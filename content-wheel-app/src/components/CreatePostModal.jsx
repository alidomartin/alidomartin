import { useState, useEffect } from 'react';
import { X, Lightbulb } from 'lucide-react';
import { POST_TYPES, PLATFORMS, ROTATION, getNextType } from '../utils/contentWheel';

const MAX_CHARS = 3000;

function toLocalDatetimeValue(iso) {
  if (!iso) return '';
  const d = new Date(iso);
  const pad = n => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

function nowPlusHour() {
  const d = new Date();
  d.setHours(d.getHours() + 1, 0, 0, 0);
  return toLocalDatetimeValue(d.toISOString());
}

const SORTED_PLATFORMS = Object.entries(PLATFORMS)
  .sort((a, b) => a[1].priority - b[1].priority);

// Unique post types for the type selector (wheel rotation has repeats)
const TYPE_OPTIONS = ['value', 'connection', 'promotional'];

export default function CreatePostModal({ posts, editingPost, onSave, onClose }) {
  const suggestedType = getNextType(posts);

  const [type, setType] = useState(editingPost?.type ?? suggestedType);
  const [caption, setCaption] = useState(editingPost?.caption ?? '');
  const [platforms, setPlatforms] = useState(editingPost?.platforms ?? ['linkedin']);
  const [scheduledAt, setScheduledAt] = useState(
    editingPost?.scheduledAt ? toLocalDatetimeValue(editingPost.scheduledAt) : nowPlusHour()
  );
  const [status, setStatus] = useState(editingPost?.status ?? 'scheduled');
  const [showStarters, setShowStarters] = useState(false);

  useEffect(() => {
    const handleKey = e => { if (e.key === 'Escape') onClose(); };
    window.addEventListener('keydown', handleKey);
    return () => window.removeEventListener('keydown', handleKey);
  }, [onClose]);

  function togglePlatform(pid) {
    setPlatforms(prev =>
      prev.includes(pid) ? prev.filter(p => p !== pid) : [...prev, pid]
    );
  }

  function useStarter(starter) {
    setCaption(starter);
    setShowStarters(false);
  }

  function handleSubmit(e) {
    e.preventDefault();
    onSave({
      type,
      caption,
      platforms,
      scheduledAt: scheduledAt ? new Date(scheduledAt).toISOString() : null,
      status,
    });
    onClose();
  }

  const typeInfo = POST_TYPES[type];
  const charsLeft = MAX_CHARS - caption.length;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/40 backdrop-blur-sm" onClick={onClose} />

      <div className="relative bg-white rounded-2xl shadow-2xl w-full max-w-xl max-h-[92vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-5 border-b border-gray-100">
          <div>
            <h2 className="text-lg font-semibold text-gray-900">
              {editingPost ? 'Edit Post' : 'New Post'}
            </h2>
            {!editingPost && (
              <p className="text-xs text-gray-400 mt-0.5">
                Wheel suggests: {POST_TYPES[suggestedType].emoji} {POST_TYPES[suggestedType].label}
              </p>
            )}
          </div>
          <button onClick={onClose} className="p-2 rounded-lg text-gray-400 hover:bg-gray-100 transition-colors">
            <X size={18} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-5 space-y-5">
          {/* Content Type */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Content Type</label>
            <div className="grid grid-cols-3 gap-2">
              {TYPE_OPTIONS.map(tid => {
                const t = POST_TYPES[tid];
                const active = type === tid;
                const isSuggested = tid === suggestedType && !editingPost;
                return (
                  <button
                    key={tid}
                    type="button"
                    onClick={() => setType(tid)}
                    className={`relative flex flex-col items-center gap-1 p-3 rounded-xl border-2 transition-all text-sm font-medium ${
                      active
                        ? 'shadow-sm'
                        : 'border-gray-200 text-gray-500 hover:border-gray-300'
                    }`}
                    style={active ? { borderColor: t.color, color: t.color, backgroundColor: `${t.color}10` } : {}}
                  >
                    {isSuggested && (
                      <span className="absolute -top-1.5 -right-1.5 text-xs bg-indigo-500 text-white px-1 py-0.5 rounded-full leading-none">
                        next
                      </span>
                    )}
                    <span className="text-xl">{t.emoji}</span>
                    <span className="text-center leading-tight">{t.shortLabel}</span>
                  </button>
                );
              })}
            </div>
            <p className="mt-1.5 text-xs text-gray-400">{typeInfo.description}</p>
          </div>

          {/* Platforms */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Platforms</label>
            <div className="flex flex-wrap gap-2">
              {SORTED_PLATFORMS.map(([pid, p]) => (
                <button
                  key={pid}
                  type="button"
                  onClick={() => togglePlatform(pid)}
                  title={p.note}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full border text-sm transition-all ${
                    platforms.includes(pid)
                      ? 'border-indigo-400 bg-indigo-50 text-indigo-700 font-medium'
                      : 'border-gray-200 text-gray-500 hover:border-gray-300'
                  }`}
                >
                  <span>{p.emoji}</span>
                  {p.label}
                  {pid === 'linkedin' && <span className="text-xs opacity-50">#1</span>}
                </button>
              ))}
            </div>
          </div>

          {/* Caption */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="block text-sm font-medium text-gray-700">Caption</label>
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => setShowStarters(s => !s)}
                  className="flex items-center gap-1 text-xs text-indigo-600 hover:text-indigo-700 font-medium"
                >
                  <Lightbulb size={12} />
                  Hook starters
                </button>
                <span className={`text-xs ${charsLeft < 200 ? 'text-red-500' : 'text-gray-400'}`}>
                  {charsLeft}
                </span>
              </div>
            </div>

            {/* Hook starters dropdown */}
            {showStarters && (
              <div className="mb-2 bg-indigo-50 border border-indigo-100 rounded-xl p-3 space-y-1.5">
                <p className="text-xs font-semibold text-indigo-600 mb-2 uppercase tracking-wide">
                  Pick a hook — edit to make it yours
                </p>
                {typeInfo.promptStarters.map((starter, i) => (
                  <button
                    key={i}
                    type="button"
                    onClick={() => useStarter(starter)}
                    className="w-full text-left text-xs text-indigo-800 hover:bg-indigo-100 px-3 py-2 rounded-lg transition-colors leading-relaxed"
                  >
                    {starter}
                  </button>
                ))}
              </div>
            )}

            <textarea
              value={caption}
              onChange={e => setCaption(e.target.value.slice(0, MAX_CHARS))}
              placeholder={`Write your ${typeInfo.shortLabel.toLowerCase()} post…\n\nTip: Start with a hook that stops the scroll.`}
              rows={6}
              className="w-full border border-gray-200 rounded-xl p-3 text-sm text-gray-700 placeholder-gray-400 resize-none focus:border-indigo-400 transition-colors leading-relaxed"
            />
          </div>

          {/* Schedule + Status */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Schedule for</label>
              <input
                type="datetime-local"
                value={scheduledAt}
                onChange={e => setScheduledAt(e.target.value)}
                className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm text-gray-700 focus:border-indigo-400 transition-colors"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Status</label>
              <select
                value={status}
                onChange={e => setStatus(e.target.value)}
                className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm text-gray-700 focus:border-indigo-400 transition-colors"
              >
                <option value="draft">Draft</option>
                <option value="scheduled">Scheduled</option>
                <option value="posted">Posted</option>
              </select>
            </div>
          </div>

          {/* Actions */}
          <div className="flex gap-3 pt-1">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-2.5 rounded-xl border border-gray-200 text-sm font-medium text-gray-600 hover:bg-gray-50 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="flex-1 px-4 py-2.5 rounded-xl text-sm font-semibold text-white transition-colors"
              style={{ backgroundColor: typeInfo.color }}
            >
              {editingPost ? 'Save changes' : 'Add to wheel'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
