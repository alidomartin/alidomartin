import { LayoutDashboard, CalendarDays, Plus } from 'lucide-react';

const NAV = [
  { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { id: 'schedule', label: 'Schedule', icon: CalendarDays },
];

export default function Sidebar({ activeView, onViewChange, onNewPost }) {
  return (
    <aside className="w-56 bg-slate-900 min-h-screen flex flex-col flex-shrink-0">
      {/* Logo */}
      <div className="px-5 py-5 border-b border-slate-700">
        <div className="flex items-center gap-2">
          <span className="text-2xl">🎡</span>
          <div>
            <p className="text-white font-bold text-sm leading-tight">Content Wheel</p>
            <p className="text-slate-400 text-xs">Scheduler</p>
          </div>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 p-3 space-y-1">
        {NAV.map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            onClick={() => onViewChange(id)}
            className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all ${
              activeView === id
                ? 'bg-indigo-600 text-white'
                : 'text-slate-400 hover:text-white hover:bg-slate-800'
            }`}
          >
            <Icon size={16} />
            {label}
          </button>
        ))}
      </nav>

      {/* New post button */}
      <div className="p-3 border-t border-slate-700">
        <button
          onClick={onNewPost}
          className="w-full flex items-center justify-center gap-2 bg-indigo-600 hover:bg-indigo-500 text-white px-4 py-2.5 rounded-xl text-sm font-semibold transition-colors"
        >
          <Plus size={16} />
          New Post
        </button>
      </div>
    </aside>
  );
}
