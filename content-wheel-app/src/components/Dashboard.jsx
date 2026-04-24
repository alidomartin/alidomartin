import { useMemo } from 'react';
import { format, isToday, isTomorrow } from 'date-fns';
import { POST_TYPES, ROTATION, getNextType } from '../utils/contentWheel';

function StatCard({ label, value, sub, color }) {
  return (
    <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-4">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">{label}</p>
          <p className="text-3xl font-bold text-gray-900 mt-1">{value}</p>
          {sub && <p className="text-xs text-gray-400 mt-1">{sub}</p>}
        </div>
        {color && (
          <div className="w-3 h-3 rounded-full mt-1" style={{ backgroundColor: color }} />
        )}
      </div>
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
      .slice(0, 3);
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
    <div className="space-y-6">
      {/* Next post CTA */}
      <div
        className="rounded-2xl p-6 text-white flex items-center justify-between"
        style={{ background: `linear-gradient(135deg, ${nextTypeInfo.color}, ${nextTypeInfo.color}cc)` }}
      >
        <div>
          <p className="text-sm font-medium opacity-80 mb-1">Your wheel says…</p>
          <p className="text-2xl font-bold flex items-center gap-2">
            <span>{nextTypeInfo.emoji}</span> Post {nextTypeInfo.label} next
          </p>
          <p className="text-sm opacity-75 mt-1">{nextTypeInfo.description}</p>
        </div>
        <button
          onClick={onNewPost}
          className="flex-shrink-0 bg-white/20 hover:bg-white/30 backdrop-blur-sm px-4 py-2.5 rounded-xl text-sm font-semibold transition-colors"
        >
          Create post →
        </button>
      </div>

      {/* Stats grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard label="Total Posts" value={stats.total} sub={`${stats.draft} draft`} />
        <StatCard label="Scheduled" value={stats.scheduled} sub="upcoming" />
        <StatCard label="Posted" value={stats.posted} sub="all time" />
        <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-4">
          <p className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-2">Type Balance</p>
          <div className="space-y-1.5">
            {ROTATION.map(tid => {
              const t = POST_TYPES[tid];
              const count = stats.byType[tid];
              const pct = stats.total > 0 ? Math.round((count / stats.total) * 100) : 0;
              return (
                <div key={tid} className="flex items-center gap-2">
                  <div className="w-2 h-2 rounded-full flex-shrink-0" style={{ backgroundColor: t.color }} />
                  <div className="flex-1 bg-gray-100 rounded-full h-1.5 overflow-hidden">
                    <div
                      className="h-full rounded-full transition-all"
                      style={{ width: `${pct}%`, backgroundColor: t.color }}
                    />
                  </div>
                  <span className="text-xs text-gray-500 w-5 text-right">{count}</span>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Upcoming posts */}
      {upcoming.length > 0 && (
        <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-5">
          <h3 className="text-sm font-semibold text-gray-700 mb-3">Coming up</h3>
          <div className="space-y-3">
            {upcoming.map(post => {
              const type = POST_TYPES[post.type];
              return (
                <div key={post.id} className="flex items-start gap-3">
                  <div className="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 text-base"
                    style={{ backgroundColor: `${type.color}15` }}>
                    {type.emoji}
                  </div>
                  <div className="min-w-0">
                    <p className="text-sm text-gray-700 line-clamp-1">
                      {post.caption || <span className="italic text-gray-400">No caption</span>}
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
