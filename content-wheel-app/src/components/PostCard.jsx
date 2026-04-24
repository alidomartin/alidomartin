import { format } from 'date-fns';
import { Pencil, Trash2, CheckCircle, Clock, FileText } from 'lucide-react';
import { POST_TYPES, PLATFORMS, STATUSES } from '../utils/contentWheel';

const STATUS_ICONS = {
  draft: FileText,
  scheduled: Clock,
  posted: CheckCircle,
};

export default function PostCard({ post, onEdit, onDelete, onMarkPosted }) {
  const type = POST_TYPES[post.type];
  const StatusIcon = STATUS_ICONS[post.status] || Clock;

  return (
    <div className={`bg-white rounded-xl border p-4 shadow-sm hover:shadow-md transition-shadow ${type.borderClass}`}>
      {/* Header */}
      <div className="flex items-start justify-between gap-2 mb-3">
        <div className="flex items-center gap-2 flex-wrap">
          <span className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold ${type.badgeClass}`}>
            <span>{type.emoji}</span>
            {type.label}
          </span>
          <span className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium ${STATUSES[post.status]?.class}`}>
            <StatusIcon size={10} />
            {STATUSES[post.status]?.label}
          </span>
        </div>
        <div className="flex items-center gap-1 flex-shrink-0">
          {post.status !== 'posted' && (
            <>
              <button
                onClick={() => onMarkPosted(post.id)}
                className="p-1.5 text-emerald-600 hover:bg-emerald-50 rounded-lg transition-colors"
                title="Mark as posted"
              >
                <CheckCircle size={15} />
              </button>
              <button
                onClick={() => onEdit(post)}
                className="p-1.5 text-gray-400 hover:bg-gray-50 rounded-lg transition-colors"
                title="Edit"
              >
                <Pencil size={15} />
              </button>
            </>
          )}
          <button
            onClick={() => onDelete(post.id)}
            className="p-1.5 text-gray-400 hover:bg-red-50 hover:text-red-500 rounded-lg transition-colors"
            title="Delete"
          >
            <Trash2 size={15} />
          </button>
        </div>
      </div>

      {/* Caption */}
      <p className="text-sm text-gray-700 line-clamp-3 mb-3 leading-relaxed">
        {post.caption || <span className="italic text-gray-400">No caption yet…</span>}
      </p>

      {/* Footer */}
      <div className="flex items-center justify-between gap-2">
        {/* Platforms */}
        <div className="flex items-center gap-1 flex-wrap">
          {(post.platforms || []).map(pid => {
            const p = PLATFORMS[pid];
            return p ? (
              <span key={pid} className="text-sm" title={p.label}>{p.emoji}</span>
            ) : null;
          })}
        </div>

        {/* Date */}
        <span className="text-xs text-gray-400 flex-shrink-0">
          {post.scheduledAt
            ? format(new Date(post.scheduledAt), 'MMM d, h:mm a')
            : 'No date set'}
        </span>
      </div>
    </div>
  );
}
