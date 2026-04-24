export const POST_TYPES = {
  value: {
    id: 'value',
    label: 'Value',
    emoji: '💡',
    description: 'Educational tips, how-tos, insights',
    color: '#3b82f6',
    bgClass: 'bg-blue-500',
    lightClass: 'bg-blue-50',
    textClass: 'text-blue-700',
    borderClass: 'border-blue-200',
    badgeClass: 'bg-blue-100 text-blue-700',
  },
  connection: {
    id: 'connection',
    label: 'Connection',
    emoji: '💚',
    description: 'Stories, personal, behind-the-scenes',
    color: '#22c55e',
    bgClass: 'bg-green-500',
    lightClass: 'bg-green-50',
    textClass: 'text-green-700',
    borderClass: 'border-green-200',
    badgeClass: 'bg-green-100 text-green-700',
  },
  promotional: {
    id: 'promotional',
    label: 'Promotional',
    emoji: '🚀',
    description: 'Offers, CTA, sales, announcements',
    color: '#a855f7',
    bgClass: 'bg-purple-500',
    lightClass: 'bg-purple-50',
    textClass: 'text-purple-700',
    borderClass: 'border-purple-200',
    badgeClass: 'bg-purple-100 text-purple-700',
  },
};

export const ROTATION = ['value', 'connection', 'promotional'];

export const PLATFORMS = {
  instagram: { label: 'Instagram', emoji: '📸', color: '#E1306C' },
  twitter: { label: 'Twitter/X', emoji: '🐦', color: '#1DA1F2' },
  linkedin: { label: 'LinkedIn', emoji: '💼', color: '#0077B5' },
  tiktok: { label: 'TikTok', emoji: '🎵', color: '#010101' },
  facebook: { label: 'Facebook', emoji: '👥', color: '#1877F2' },
  youtube: { label: 'YouTube', emoji: '▶️', color: '#FF0000' },
};

export const STATUSES = {
  draft: { label: 'Draft', class: 'bg-gray-100 text-gray-600' },
  scheduled: { label: 'Scheduled', class: 'bg-indigo-100 text-indigo-700' },
  posted: { label: 'Posted', class: 'bg-emerald-100 text-emerald-700' },
};

export function getNextType(posts) {
  const posted = posts
    .filter(p => p.status === 'posted')
    .sort((a, b) => new Date(b.scheduledAt) - new Date(a.scheduledAt));

  if (posted.length === 0) return 'value';

  const lastType = posted[0].type;
  const idx = ROTATION.indexOf(lastType);
  return ROTATION[(idx + 1) % ROTATION.length];
}

export function getWheelAngle(posts) {
  const nextType = getNextType(posts);
  const idx = ROTATION.indexOf(nextType);
  return -(idx * 120);
}

export function groupPostsByTime(posts) {
  const now = new Date();
  const todayEnd = new Date(now); todayEnd.setHours(23, 59, 59, 999);
  const tomorrowEnd = new Date(now); tomorrowEnd.setDate(tomorrowEnd.getDate() + 1); tomorrowEnd.setHours(23, 59, 59, 999);
  const weekEnd = new Date(now); weekEnd.setDate(weekEnd.getDate() + 7);

  const groups = { today: [], tomorrow: [], thisWeek: [], later: [], past: [] };

  for (const post of posts) {
    if (post.status === 'posted') {
      groups.past.push(post);
      continue;
    }
    const d = new Date(post.scheduledAt);
    if (d <= todayEnd) groups.today.push(post);
    else if (d <= tomorrowEnd) groups.tomorrow.push(post);
    else if (d <= weekEnd) groups.thisWeek.push(post);
    else groups.later.push(post);
  }

  for (const key of Object.keys(groups)) {
    groups[key].sort((a, b) => new Date(a.scheduledAt) - new Date(b.scheduledAt));
  }

  return groups;
}
