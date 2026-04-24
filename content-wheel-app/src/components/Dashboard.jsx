import { useMemo } from 'react';
import { format, isToday, isTomorrow } from 'date-fns';
import { POST_TYPES, ROTATION, getNextType } from '../utils/contentWheel';

// Unique types for balance chart (rotation has repeats)
const CHART_TYPES = ['value', 'connection', 'promotional'];

// Show what the rotation pattern looks like
const ROTATION_DISPLAY = ROTATION.map(t => POST_TYPES[t]);

function StatCard({ label, value, sub }) {
  return (
    <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-4">
      <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">{label}</p>
      <p className="text-3xl font-bold text-gray-900 mt-1">{value}</p>
      {sub && <p className="text-xs text-gray-400 mt-1">{sub}</p>}
    </div>
  );
}

export default function Dashboard({ posts, onNewPost }) {
  const stats = useMemo(() => {
    const total = posts.length;
    const scheduled = posts.filter(p => p.status === 'scheduled').length;
    const posted = posts.filter(p => p.status === 'posted').length;
    const draft = posts.filter(p => p.status === 'draft').length;
    const byType = { value: 0, connection: 0, promotional: 0 };
    posts.forEach(p => { if (byType[p.type] !== undefined) byType[p.type]++; });
    return { total, scheduled, posted, draft, byType };
  }, [posts]);

  const upcoming = useMemo(() => {
    return posts
      .filter(p => p.status === 'scheduled' && p.scheduledAt)
      .sort((a, b) => new Date(a.scheduledAt) - new Date(b.scheduledAt))
      .slice(0, 4);
  }, [posts]);

  const nextType = getNextType(posts);
  const nextTypeInfo = POST_TYPES[nextType];

  function formatWhen(iso) {
    const d = new Date(iso);
    if (isToday(d)) return `Today ${format(d, 'h:mm a')}`;
    if (isTomorrow(d)) return `Tomorrow ${format(d, 'h:mm a')}`;
    return format(d, 'EEE MMM d, h:mm a');
  }

  return (
    <div className="space-y-5">
      {/* Next post CTA */}
      <div
        className="rounded-2xl p-6 text-white"
        style={{ background: `linear-gradient(135deg, ${nextTypeInfo.color} 0%, ${nextTypeInfo.color}bb 100%)` }}
      >
        <p className="text-sm font-medium opacity-75 mb-1">Your wheel says post next…</p>
        <p className="text-2xl font-bold flex items-center gap-2">
          <span>{nextTypeInfo.emoji}</span> {nextTypeInfo.label}
        </p>
        <p className="text-sm opacity-70 mt-1 mb-4">{nextTypeInfo.description}</p>
        <button
          onClick={onNewPost}
          className="bg-white/20 hover:bg-white/30 backdrop-blur-sm px-4 py-2 rounded-xl text-sm font-semibold transition-colors"
        >
          Write it now →
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 gap-3">
        <StatCard label="Scheduled" value={stats.scheduled} sub="upcoming posts" />
        <StatCard label="Posted" value={stats.posted} sub="all time" />
        <StatCard label="Drafts" value={stats.draft} sub="in progress" />
        <StatCard label="Total" value={stats.total} sub="in the wheel" />
      </div>

      {/* Type balance */}
      <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-4">
        <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3">Content Balance</p>
        <div className="space-y-2.5">
          {CHART_TYPES.map(tid => {
            const t = POST_TYPES[tid];
            const count = stats.byType[tid];
            const pct = stats.total > 0 ? Math.round((count / stats.total) * 100) : 0;
            return (
              <div key={tid} className="flex items-center gap-3">
                <span className="text-base w-5">{t.emoji}</span>
                <div className="flex-1">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-xs font-medium text-gray-600">{t.shortLabel}</span>
                    <span className="text-xs text-gray-400">{count} posts · {pct}%</span>
                  </div>
                  <div className="bg-gray-100 rounded-full h-1.5 overflow-hidden">
                    <div
                      className="h-full rounded-full transition-all duration-500"
                      style={{ width: `${pct}%`, backgroundColor: t.color }}
                    />
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Rotation pattern */}
      <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-4">
        <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">Your Rotation Pattern</p>
        <p className="text-xs text-gray-400 mb-3">2× Insight → 1× Story → 1× Insight → 1× Offer → repeat</p>
        <div className="flex items-center gap-1.5 flex-wrap">
          {ROTATION_DISPLAY.map((t, i) => (
            <div key={i} className="flex items-center gap-1">
              <span
                className="inline-flex items-center gap-1 px-2 py-1 rounded-lg text-xs font-medium"
                style={{ backgroundColor: `${t.color}15`, color: t.color }}
              >
                {t.emoji} {t.shortLabel}
              </span>
              {i < ROTATION_DISPLAY.length - 1 && (
                <span className="text-gray-300 text-xs">→</span>
              )}
            </div>
          ))}
          <span className="text-gray-300 text-xs">→ 🔁</span>
        </div>
        <p className="text-xs text-gray-400 mt-3 leading-relaxed">
          Heavy on Insight to build authority fast in a technical niche. Story keeps it human. Offer converts without burning trust.
        </p>
      </div>

      {/* Upcoming */}
      {upcoming.length > 0 && (
        <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-4">
          <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3">Coming Up</p>
          <div className="space-y-3">
            {upcoming.map(post => {
              const type = POST_TYPES[post.type];
              return (
                <div key={post.id} className="flex items-start gap-3">
                  <div
                    className="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 text-base"
                    style={{ backgroundColor: `${type.color}15` }}
                  >
                    {type.emoji}
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="text-sm text-gray-700 line-clamp-1">
                      {post.caption || <span className="italic text-gray-400">No caption yet</span>}
                    </p>
                    <p className="text-xs text-gray-400 mt-0.5">{formatWhen(post.scheduledAt)}</p>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
