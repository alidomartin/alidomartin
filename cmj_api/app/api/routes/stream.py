from __future__ import annotations
import json
import numpy as np
from collections import deque
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.config import settings
from app.core.preprocessor import preprocess
from app.core.phase_detector import detect_phases
from app.core.metrics import compute_metrics
from app.utils.validators import validate_signal

router = APIRouter(prefix="/ws", tags=["streaming"])

_MIN_BUFFER_S = 3.0


@router.websocket("/stream")
async def stream_analysis(websocket: WebSocket):
    """
    Real-time CMJ analysis over WebSocket.

    First frame: {"sample_rate": 1000, "chunk": [f1, f2, ...]}
    Subsequent frames: {"chunk": [f1, f2, ...]}
    Server responds with phase/metric events per frame received.
    """
    await websocket.accept()

    buffer: deque[float] = deque()
    sample_rate = settings.DEFAULT_SAMPLE_RATE
    initialized = False

    try:
        while True:
            raw = await websocket.receive_text()
            frame = json.loads(raw)

            if not initialized:
                sample_rate = int(frame.get("sample_rate", settings.DEFAULT_SAMPLE_RATE))
                initialized = True

            buffer.extend(frame.get("chunk", []))

            min_samples = int(_MIN_BUFFER_S * sample_rate)
            if len(buffer) < min_samples:
                await websocket.send_json({
                    "status": "buffering",
                    "samples_received": len(buffer),
                    "samples_needed": min_samples,
                })
                continue

            force = np.array(buffer, dtype=float)
            try:
                validate_signal(force, sample_rate)
                prep = preprocess(force, sample_rate)
                result = detect_phases(prep)
                metrics = compute_metrics(
                    prep.time, prep.force, result.velocity,
                    result.phases, prep.body_weight_n, prep.mass_kg,
                )
                await websocket.send_json({
                    "status": "analyzed",
                    "samples_processed": len(buffer),
                    "phases": result.phases.model_dump(),
                    "metrics": metrics.model_dump(),
                })
            except ValueError as exc:
                await websocket.send_json({"status": "insufficient_data", "detail": str(exc)})
            except Exception as exc:
                await websocket.send_json({"status": "error", "detail": str(exc)})

    except WebSocketDisconnect:
        pass
