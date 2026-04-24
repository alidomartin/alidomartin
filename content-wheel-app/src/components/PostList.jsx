import { useMemo, useState } from 'react';
import { groupPostsByTime } from '../utils/contentWheel';
import PostCard from './PostCard';

const FILTERS = [
  { id: 'all', label: 'All' },
  { id: 'scheduled', label: 'Scheduled' },
  { id: 'draft', label: 'Drafts' },
  { id: 'posted', label: 'Posted' },
];

const GROUP_LABELS = {
  today: 'Today',
  tomorrow: 'Tomorrow',
  thisWeek: 'This Week',
  later: 'Later',
  past: 'Already Posted',
};

export default function PostList({ posts, onEdit, onDelete, onMarkPosted }) {
  const [filter, setFilter] = useState('all');

  const filtered = useMemo(() => {
    if (filter === 'all') return posts;
    return posts.filter(p => p.status === filter);
  }, [posts, filter]);

  const groups = useMemo(() => groupPostsByTime(filtered), [filtered]);

  const hasAny = Object.values(groups).some(g => g.length > 0);

  return (
    <div className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
      {/* Header + filter */}
      <div className="flex items-center justify-between px-5 py-4 border-b border-gray-100">
        <h2 className="text-lg font-semibold text-gray-900">Posts</h2>
        <div className="flex gap-1 bg-gray-100 rounded-lg p-1">
          {FILTERS.map(f => (
            <button
              key={f.id}
              onClick={() => setFilter(f.id)}
              className={`px-3 py-1 rounded-md text-xs font-medium transition-all ${
                filter === f.id
                  ? 'bg-white text-gray-800 shadow-sm'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              {f.label}
            </button>
          ))}
        </div>
      </div>

      <div className="p-5 space-y-6 max-h-[calc(100vh-280px)] overflow-y-auto">
        {!hasAny && (
          <div className="text-center py-12">
            <p className="text-4xl mb-3">🎡</p>
            <p className="text-gray-500 text-sm">No posts yet. Add your first post to start the wheel!</p>
          </div>
        )}

        {Object.entries(GROUP_LABELS).map(([key, label]) => {
          const group = groups[key];
          if (!group || group.length === 0) return null;
          return (
            <div key={key}>
              <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-3">
                {label} · {group.length}
              </h3>
              <div className="space-y-3">
                {group.map(post => (
                  <PostCard
                    key={post.id}
                    post={post}
                    onEdit={onEdit}
                    onDelete={onDelete}
                    onMarkPosted={onMarkPosted}
                  />
                ))}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
