import { useMemo } from 'react';
import { POST_TYPES, ROTATION, getNextType, getWheelAngle } from '../utils/contentWheel';

// SVG wheel: 3 equal sectors, center (100,100), radius 90
// Sector angles (starting from top, -90°):
//   0: -90° → 30°  (top)
//   1:  30° → 150° (bottom-right)
//   2: 150° → 270° (bottom-left)
const SECTOR_PATHS = [
  'M 100 100 L 100 10 A 90 90 0 0 1 177.94 145 Z',
  'M 100 100 L 177.94 145 A 90 90 0 0 1 22.06 145 Z',
  'M 100 100 L 22.06 145 A 90 90 0 0 1 100 10 Z',
];

// Label positions (centroid of each sector, ~60% of radius from center)
const LABEL_POSITIONS = [
  { x: 100, y: 52 },     // top sector
  { x: 152, y: 136 },    // bottom-right sector
  { x: 48, y: 136 },     // bottom-left sector
];

// The wheel always shows the 3 physical sectors regardless of rotation pattern
const WHEEL_SECTORS = ['value', 'connection', 'promotional'];

export default function ContentWheel({ posts }) {
  const nextType = getNextType(posts);
  const angle = getWheelAngle(posts);
  const nextIdx = WHEEL_SECTORS.indexOf(nextType);

  const stats = useMemo(() => {
    const counts = { value: 0, connection: 0, promotional: 0 };
    posts.forEach(p => { if (counts[p.type] !== undefined) counts[p.type]++; });
    return counts;
  }, [posts]);

  return (
    <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
      <div className="flex items-start justify-between mb-4">
        <div>
          <h2 className="text-lg font-semibold text-gray-900">Content Wheel</h2>
          <p className="text-sm text-gray-500 mt-0.5">Your posting rotation</p>
        </div>
        <div className="flex items-center gap-2 bg-indigo-50 px-3 py-1.5 rounded-full">
          <span className="text-lg">{POST_TYPES[nextType].emoji}</span>
          <span className="text-sm font-medium text-indigo-700">
            Next: {POST_TYPES[nextType].label}
          </span>
        </div>
      </div>

      <div className="flex items-center justify-center gap-8">
        {/* SVG Wheel */}
        <div className="relative flex-shrink-0">
          {/* Pointer arrow at top */}
          <div className="absolute top-0 left-1/2 -translate-x-1/2 -translate-y-1 z-10">
            <svg width="16" height="16" viewBox="0 0 16 16">
              <polygon points="8,14 0,2 16,2" fill="#1e293b" />
            </svg>
          </div>

          <svg
            width="200"
            height="200"
            viewBox="0 0 200 200"
            style={{
              transform: `rotate(${angle}deg)`,
              transition: 'transform 0.6s cubic-bezier(0.34, 1.56, 0.64, 1)',
            }}
          >
            {WHEEL_SECTORS.map((typeId, i) => {
              const type = POST_TYPES[typeId];
              const isActive = i === nextIdx;
              return (
                <g key={typeId}>
                  <path
                    d={SECTOR_PATHS[i]}
                    fill={type.color}
                    opacity={isActive ? 1 : 0.35}
                    stroke="white"
                    strokeWidth="3"
                  />
                  <text
                    x={LABEL_POSITIONS[i].x}
                    y={LABEL_POSITIONS[i].y}
                    textAnchor="middle"
                    dominantBaseline="middle"
                    fill="white"
                    fontSize="9"
                    fontWeight="700"
                    fontFamily="system-ui, sans-serif"
                    style={{ transform: `rotate(${-angle}deg)`, transformOrigin: `${LABEL_POSITIONS[i].x}px ${LABEL_POSITIONS[i].y}px` }}
                  >
                    {type.emoji}
                  </text>
                </g>
              );
            })}
            {/* Center circle */}
            <circle cx="100" cy="100" r="22" fill="white" />
            <text x="100" y="97" textAnchor="middle" fontSize="9" fontWeight="600" fill="#374151" fontFamily="system-ui, sans-serif">POST</text>
            <text x="100" y="107" textAnchor="middle" fontSize="9" fontWeight="600" fill="#374151" fontFamily="system-ui, sans-serif">NEXT</text>
          </svg>
        </div>

        {/* Legend + stats */}
        <div className="flex flex-col gap-3">
          {WHEEL_SECTORS.map(typeId => {
            const type = POST_TYPES[typeId];
            const isNext = typeId === nextType;
            return (
              <div
                key={typeId}
                className={`flex items-center gap-3 px-3 py-2 rounded-lg transition-all ${
                  isNext ? 'bg-gray-50 ring-1 ring-gray-200' : ''
                }`}
              >
                <div
                  className="w-3 h-3 rounded-full flex-shrink-0"
                  style={{ backgroundColor: type.color }}
                />
                <div className="min-w-0">
                  <div className="flex items-center gap-1.5">
                    <span className="text-sm font-medium text-gray-800">{type.label}</span>
                    {isNext && (
                      <span className="text-xs bg-indigo-100 text-indigo-600 px-1.5 py-0.5 rounded-full font-medium">
                        Next
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-gray-400 truncate">{type.description}</p>
                </div>
                <span className="text-xs font-semibold text-gray-400 ml-auto">
                  {stats[typeId]}
                </span>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
