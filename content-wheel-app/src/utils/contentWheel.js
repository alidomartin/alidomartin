// Brand: Alido Martin — Sports Performance / S&C
// Target Avatar: Club-level S&C coach who uses force plate data and needs
// science-to-practice content they can trust and act on immediately.

export const BRAND = {
  name: 'Alido Martin',
  tagline: 'Sports Performance · Force Plate Data · S&C Coaching',
  avatar: 'Club-level S&C coach / performance analyst (semi-pro → pro)',
  niche: 'CMJ & force-time curve analysis → practical coaching decisions',
};

// The 3 spokes of the content wheel, mapped to the brand
export const POST_TYPES = {
  value: {
    id: 'value',
    label: 'Performance Insight',
    shortLabel: 'Insight',
    emoji: '📊',
    description: 'Break down a metric, phase, or concept. Teach coaches to read their data.',
    promptStarters: [
      'What your [metric] actually tells you (and what it doesn\'t)…',
      'Most coaches misread their braking phase. Here\'s why…',
      'One CMJ number that predicts injury risk before the athlete feels it…',
      'The difference between peak force and impulse — and why it matters for programming…',
      'How to use mRSI to decide training load today…',
      '3 things that change your propulsive phase overnight (that aren\'t strength)…',
    ],
    color: '#2563eb',
    bgClass: 'bg-blue-600',
    lightClass: 'bg-blue-50',
    textClass: 'text-blue-700',
    borderClass: 'border-blue-200',
    badgeClass: 'bg-blue-100 text-blue-700',
  },
  connection: {
    id: 'connection',
    label: 'Behind the Data',
    shortLabel: 'Story',
    emoji: '🔬',
    description: 'Real cases, coaching stories, lessons learned. Build trust through your process.',
    promptStarters: [
      'An athlete\'s RSI dropped 18% before they felt any soreness. Here\'s what I did…',
      'The time I over-relied on force plate data and got it wrong…',
      'What coaching [athlete type] taught me about loading the braking phase…',
      'A week in my monitoring workflow (real numbers, real decisions)…',
      'Why I stopped chasing peak force and what I chase now…',
      'The question every coach asks me after seeing a CMJ report for the first time…',
    ],
    color: '#059669',
    bgClass: 'bg-emerald-600',
    lightClass: 'bg-emerald-50',
    textClass: 'text-emerald-700',
    borderClass: 'border-emerald-200',
    badgeClass: 'bg-emerald-100 text-emerald-700',
  },
  promotional: {
    id: 'promotional',
    label: 'Work With Me',
    shortLabel: 'Offer',
    emoji: '🎯',
    description: 'Clear CTA. Your services, tools, assessments, or consultations.',
    promptStarters: [
      'I help [S&C coaches / performance teams] turn force plate data into daily decisions. Here\'s how to work with me…',
      'CMJ assessment + full force-time report — now open for [month]…',
      'If your team has force plates and nobody knows what to do with the numbers, this is for you…',
      'I\'m taking [X] coaches this quarter for 1:1 performance analytics mentoring…',
      'Free: the CMJ phase guide I use with every athlete. Link in bio…',
      '[Workshop / Webinar] — Reading the CMJ curve in under 5 minutes. Register below…',
    ],
    color: '#7c3aed',
    bgClass: 'bg-violet-600',
    lightClass: 'bg-violet-50',
    textClass: 'text-violet-700',
    borderClass: 'border-violet-200',
    badgeClass: 'bg-violet-100 text-violet-700',
  },
};

// Rotation: 2 Value → 1 Connection → 1 Value → 1 Promotional (repeat)
// Rationale: heavy on insight (builds authority fast in a technical niche),
// story keeps it human, promo converts without burning trust.
export const ROTATION = ['value', 'value', 'connection', 'value', 'promotional'];

// Platform priority for this niche — S&C coaches live on LinkedIn + Instagram
export const PLATFORMS = {
  linkedin: {
    label: 'LinkedIn',
    emoji: '💼',
    color: '#0077B5',
    priority: 1,
    note: 'Primary. Long-form text + carousels dominate here for S&C professionals.',
  },
  instagram: {
    label: 'Instagram',
    emoji: '📸',
    color: '#E1306C',
    priority: 2,
    note: 'Infographics, force curve visuals, short reels. Strong reach for coaching content.',
  },
  twitter: {
    label: 'Twitter/X',
    emoji: '🐦',
    color: '#1DA1F2',
    priority: 3,
    note: 'Sports science community is active here. Good for quick insights + threads.',
  },
  tiktok: {
    label: 'TikTok',
    emoji: '🎵',
    color: '#010101',
    priority: 4,
    note: 'Growing S&C audience. Short explainers of force-time curves perform well.',
  },
  youtube: {
    label: 'YouTube',
    emoji: '▶️',
    color: '#FF0000',
    priority: 5,
    note: 'Long-form deep dives. Build once, traffic forever.',
  },
  facebook: {
    label: 'Facebook',
    emoji: '👥',
    color: '#1877F2',
    priority: 6,
    note: 'Groups can work. Lower priority for this avatar.',
  },
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

  if (posted.length === 0) return ROTATION[0];

  const lastType = posted[0].type;
  // Find the last occurrence of this type in the rotation to step forward correctly
  const lastIdx = [...ROTATION].lastIndexOf(lastType);
  return ROTATION[(lastIdx + 1) % ROTATION.length];
}

export function getWheelAngle(posts) {
  const nextType = getNextType(posts);
  // Wheel has 3 physical sectors (value/connection/promotional), map shortLabel
  const sectors = ['value', 'connection', 'promotional'];
  const idx = sectors.indexOf(nextType);
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
