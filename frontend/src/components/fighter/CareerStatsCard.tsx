'use client'

import { motion } from 'framer-motion'
import type { CareerStats } from '@/types/fighter'

/** SVG Repo human silhouette (CC0) – single path, clipped into Head / Body / Leg zones */
const SILHOUETTE_PATH =
  'M104.265,117.959c-0.304,3.58,2.126,22.529,3.38,29.959c0.597,3.52,2.234,9.255,1.645,12.3' +
  'c-0.841,4.244-1.084,9.736-0.621,12.934c0.292,1.942,1.211,10.899-0.104,14.175c-0.688,1.718-1.949,10.522-1.949,10.522' +
  'c-3.285,8.294-1.431,7.886-1.431,7.886c1.017,1.248,2.759,0.098,2.759,0.098c1.327,0.846,2.246-0.201,2.246-0.201' +
  'c1.139,0.943,2.467-0.116,2.467-0.116c1.431,0.743,2.758-0.627,2.758-0.627c0.822,0.414,1.023-0.109,1.023-0.109' +
  'c2.466-0.158-1.376-8.05-1.376-8.05c-0.92-7.088,0.913-11.033,0.913-11.033c6.004-17.805,6.309-22.53,3.909-29.24' +
  'c-0.676-1.937-0.847-2.704-0.536-3.545c0.719-1.941,0.195-9.748,1.072-12.848c1.692-5.979,3.361-21.142,4.231-28.217' +
  'c1.169-9.53-4.141-22.308-4.141-22.308c-1.163-5.2,0.542-23.727,0.542-23.727c2.381,3.705,2.29,10.245,2.29,10.245' +
  'c-0.378,6.859,5.541,17.342,5.541,17.342c2.844,4.332,3.921,8.442,3.921,8.747c0,1.248-0.273,4.269-0.273,4.269l0.109,2.631' +
  'c0.049,0.67,0.426,2.977,0.365,4.092c-0.444,6.862,0.646,5.571,0.646,5.571c0.92,0,1.931-5.522,1.931-5.522' +
  'c0,1.424-0.348,5.687,0.42,7.295c0.919,1.918,1.595-0.329,1.607-0.78c0.243-8.737,0.768-6.448,0.768-6.448' +
  'c0.511,7.088,1.139,8.689,2.265,8.135c0.853-0.407,0.073-8.506,0.073-8.506c1.461,4.811,2.569,5.577,2.569,5.577' +
  'c2.411,1.693,0.92-2.983,0.585-3.909c-1.784-4.92-1.839-6.625-1.839-6.625c2.229,4.421,3.909,4.257,3.909,4.257' +
  'c2.174-0.694-1.9-6.954-4.287-9.953c-1.218-1.528-2.789-3.574-3.245-4.789c-0.743-2.058-1.304-8.674-1.304-8.674' +
  'c-0.225-7.807-2.155-11.198-2.155-11.198c-3.3-5.282-3.921-15.135-3.921-15.135l-0.146-16.635' +
  'c-1.157-11.347-9.518-11.429-9.518-11.429c-8.451-1.258-9.627-3.988-9.627-3.988c-1.79-2.576-0.767-7.514-0.767-7.514' +
  'c1.485-1.208,2.058-4.415,2.058-4.415c2.466-1.891,2.345-4.658,1.206-4.628c-0.914,0.024-0.707-0.733-0.707-0.733' +
  'C115.068,0.636,104.01,0,104.01,0h-1.688c0,0-11.063,0.636-9.523,13.089c0,0,0.207,0.758-0.715,0.733' +
  'c-1.136-0.03-1.242,2.737,1.215,4.628c0,0,0.572,3.206,2.058,4.415c0,0,1.023,4.938-0.767,7.514c0,0-1.172,2.73-9.627,3.988' +
  'c0,0-8.375,0.082-9.514,11.429l-0.158,16.635c0,0-0.609,9.853-3.922,15.135c0,0-1.921,3.392-2.143,11.198' +
  'c0,0-0.563,6.616-1.303,8.674c-0.451,1.209-2.021,3.255-3.249,4.789c-2.408,2.993-6.455,9.24-4.29,9.953' +
  'c0,0,1.689,0.164,3.909-4.257c0,0-0.046,1.693-1.827,6.625c-0.35,0.914-1.839,5.59,0.573,3.909c0,0,1.117-0.767,2.569-5.577' +
  'c0,0-0.779,8.099,0.088,8.506c1.133,0.555,1.751-1.047,2.262-8.135c0,0,0.524-2.289,0.767,6.448' +
  'c0.012,0.451,0.673,2.698,1.596,0.78c0.779-1.608,0.429-5.864,0.429-7.295c0,0,0.999,5.522,1.933,5.522' +
  'c0,0,1.099,1.291,0.648-5.571c-0.073-1.121,0.32-3.422,0.369-4.092l0.106-2.631c0,0-0.274-3.014-0.274-4.269' +
  'c0-0.311,1.078-4.415,3.921-8.747c0,0,5.913-10.488,5.532-17.342c0,0-0.082-6.54,2.299-10.245' +
  'c0,0,1.69,18.526,0.545,23.727c0,0-5.319,12.778-4.146,22.308c0.864,7.094,2.53,22.237,4.226,28.217' +
  'c0.886,3.094,0.362,10.899,1.072,12.848c0.32,0.847,0.152,1.627-0.536,3.545c-2.387,6.71-2.083,11.436,3.921,29.24' +
  'c0,0,1.848,3.945,0.914,11.033c0,0-3.836,7.892-1.379,8.05c0,0,0.192,0.523,1.023,0.109c0,0,1.327,1.37,2.761,0.627' +
  'c0,0,1.328,1.06,2.463,0.116c0,0,0.91,1.047,2.237,0.201c0,0,1.742,1.175,2.777-0.098c0,0,1.839,0.408-1.435-7.886' +
  'c0,0-1.254-8.793-1.945-10.522c-1.318-3.275-0.387-12.251-0.106-14.175c0.453-3.216,0.21-8.695-0.618-12.934' +
  'c-0.606-3.038,1.035-8.774,1.641-12.3c1.245-7.423,3.685-26.373,3.38-29.959l1.008,0.354' +
  'C103.809,118.312,104.265,117.959,104.265,117.959z'

interface Props {
  stats: CareerStats | null
  submissionWins?: number
}

function HalfDonutGauge({
  label,
  value,
  total,
  color,
  delay = 0,
}: {
  label: string
  value: number
  total: number
  color: string
  delay?: number
}) {
  const pct = total > 0 ? Math.round((value / total) * 100) : 0
  const r = 38
  const cx = 60
  const cy = 46
  const arcLength = Math.PI * r
  const dashOffset = arcLength * (1 - pct / 100)

  const bgArc = `M ${cx - r},${cy} A ${r},${r} 0 1 1 ${cx + r},${cy}`

  return (
    <div className="flex flex-col items-center">
      <svg viewBox="0 0 120 68" className="w-full max-w-[140px]">
        <path
          d={bgArc}
          fill="none"
          stroke="rgba(255,255,255,0.08)"
          strokeWidth="7"
          strokeLinecap="round"
        />
        {pct > 0 && (
          <motion.path
            d={bgArc}
            fill="none"
            stroke={color}
            strokeWidth="7"
            strokeLinecap="round"
            strokeDasharray={arcLength}
            initial={{ strokeDashoffset: arcLength }}
            animate={{ strokeDashoffset: dashOffset }}
            transition={{ duration: 1.2, ease: 'easeOut', delay }}
          />
        )}
        <text x={cx} y="42" textAnchor="middle" fill="#e4e4e7" fontSize="12" fontWeight="600">
          {value}/{total}
        </text>
        <text x={cx} y="54" textAnchor="middle" fill="#a1a1aa" fontSize="9">
          ({pct}%)
        </text>
      </svg>
      <span className="mt-0.5 text-[11px] text-zinc-400">{label}</span>
    </div>
  )
}

function formatControlTime(seconds: number): string {
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  return `${m}:${s.toString().padStart(2, '0')}`
}

export function CareerStatsCard({ stats, submissionWins = 0 }: Props) {
  if (!stats) {
    return (
      <div className="rounded-xl border border-white/[0.06] bg-white/[0.03] p-5 transition-all duration-300 ease-out hover:border-white/[0.12] hover:bg-white/[0.05]">
        <h3 className="text-sm font-semibold text-zinc-100">Career Stats</h3>
        <p className="mt-4 text-center text-sm text-zinc-500">
          No stats available
        </p>
      </div>
    )
  }

  const { striking, grappling } = stats

  // Target distribution
  const totalTargetLanded =
    striking.head_landed + striking.body_landed + striking.leg_landed
  const headPct =
    totalTargetLanded > 0
      ? Math.round((striking.head_landed / totalTargetLanded) * 100)
      : 0
  const bodyPct =
    totalTargetLanded > 0
      ? Math.round((striking.body_landed / totalTargetLanded) * 100)
      : 0
  const legPct = totalTargetLanded > 0 ? 100 - headPct - bodyPct : 0

  // Knockdowns comparison
  const kdDiff = striking.knockdowns - striking.opp_knockdowns

  // Grappling gauges
  const tdDefenseVal =
    grappling.opp_td_attempted > 0
      ? grappling.opp_td_attempted - grappling.opp_td_landed
      : 0

  return (
    <motion.div
      initial={{ opacity: 0, y: 28, filter: 'blur(4px)' }}
      animate={{ opacity: 1, y: 0, filter: 'blur(0px)' }}
      transition={{ duration: 0.7, ease: [0.23, 1, 0.32, 1] }}
      className="rounded-xl border border-white/[0.06] bg-white/[0.03] p-5 transition-all duration-300 ease-out hover:border-white/[0.12] hover:bg-white/[0.05]"
    >
      <h3 className="mb-5 text-sm font-semibold text-zinc-100">Fighting Stats</h3>

      {/* ── Main 3-column area ── */}
      <div className="grid grid-cols-[2fr_1fr_1.5fr] gap-5">
        {/* Col 1: 2×2 Half-Donut Gauges */}
        <div className="grid grid-cols-2 gap-x-3 gap-y-3">
          <HalfDonutGauge
            label="Sig. Strikes"
            value={striking.sig_str_landed}
            total={striking.sig_str_attempted}
            color="#f59e0b"
            delay={0.3}
          />
          <HalfDonutGauge
            label="TD Offense"
            value={grappling.td_landed}
            total={grappling.td_attempted}
            color="#10b981"
            delay={0.5}
          />
          <HalfDonutGauge
            label="TD Defense"
            value={tdDefenseVal}
            total={grappling.opp_td_attempted}
            color="#06b6d4"
            delay={0.7}
          />
          <HalfDonutGauge
            label="Submissions"
            value={submissionWins}
            total={grappling.submission_attempts}
            color="#a855f7"
            delay={0.9}
          />
        </div>

        {/* Col 2: Knockdowns Stat Comparison */}
        <div className="flex flex-col items-center justify-center rounded-lg border border-white/[0.06] bg-white/[0.02] px-3 py-4">
          <span className="text-[10px] font-medium uppercase tracking-wider text-zinc-500">
            Knockdowns
          </span>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-2xl font-bold text-amber-400">{striking.knockdowns}</span>
            <span className="text-xs text-zinc-500">vs</span>
            <span className="text-2xl font-bold text-red-400">{striking.opp_knockdowns}</span>
          </div>
          <div className="mt-1 flex items-center gap-1 text-[10px] text-zinc-500">
            <span>Landed</span>
            <span>/</span>
            <span>Knocked Down</span>
          </div>
          <div className={`mt-2.5 rounded-full px-2.5 py-0.5 text-xs font-semibold ${
            kdDiff > 0
              ? 'bg-emerald-500/10 text-emerald-400'
              : kdDiff < 0
                ? 'bg-red-500/10 text-red-400'
                : 'bg-zinc-500/10 text-zinc-400'
          }`}>
            {kdDiff > 0 ? '+' : ''}{kdDiff}
          </div>
        </div>

        {/* Col 3: Target Distribution */}
        {totalTargetLanded > 0 && (
          <div className="flex flex-col items-center justify-center">
            <p className="mb-1 text-[10px] font-medium uppercase tracking-wider text-zinc-500">
              Target Distribution
            </p>
            <svg viewBox="0 0 206.326 206.326" className="h-[190px] w-auto">
              <defs>
                <clipPath id="target-dist-clip">
                  <path d={SILHOUETTE_PATH} />
                </clipPath>
              </defs>

              <rect
                x="0" y="0" width="206.326" height="30"
                clipPath="url(#target-dist-clip)"
                fill={headPct > 0 ? '#ef4444' : '#3f3f46'}
                opacity={headPct > 0 ? 0.85 : 0.3}
              />
              <rect
                x="0" y="30" width="206.326" height="100"
                clipPath="url(#target-dist-clip)"
                fill={bodyPct > 0 ? '#f59e0b' : '#3f3f46'}
                opacity={bodyPct > 0 ? 0.85 : 0.3}
              />
              <rect
                x="0" y="130" width="206.326" height="76.326"
                clipPath="url(#target-dist-clip)"
                fill={legPct > 0 ? '#06b6d4' : '#3f3f46'}
                opacity={legPct > 0 ? 0.85 : 0.3}
              />

              <line
                x1="0" y1="30" x2="206.326" y2="30"
                stroke="rgba(0,0,0,0.4)" strokeWidth="1"
                clipPath="url(#target-dist-clip)"
              />
              <line
                x1="0" y1="130" x2="206.326" y2="130"
                stroke="rgba(0,0,0,0.4)" strokeWidth="1"
                clipPath="url(#target-dist-clip)"
              />

              {/* Head: % + (count) */}
              <text x="103" y="16" textAnchor="middle" fill="white" fontSize="13" fontWeight="600">
                {headPct}%
              </text>
              <text x="103" y="27" textAnchor="middle" fill="rgba(255,255,255,0.6)" fontSize="9">
                ({striking.head_landed})
              </text>

              {/* Body: % + (count) */}
              <text x="103" y="74" textAnchor="middle" fill="white" fontSize="15" fontWeight="600">
                {bodyPct}%
              </text>
              <text x="103" y="88" textAnchor="middle" fill="rgba(255,255,255,0.6)" fontSize="10">
                ({striking.body_landed})
              </text>

              {/* Leg: % + (count) */}
              <text x="103" y="155" textAnchor="middle" fill="white" fontSize="13" fontWeight="600">
                {legPct}%
              </text>
              <text x="103" y="167" textAnchor="middle" fill="rgba(255,255,255,0.6)" fontSize="9">
                ({striking.leg_landed})
              </text>
            </svg>
          </div>
        )}
      </div>

      {/* ── Mini Stat Row ── */}
      <div className="mt-5 border-t border-white/[0.06] pt-4">
        <div className="grid grid-cols-3 gap-4">
          <div className="flex flex-col items-center">
            <span className="text-[10px] text-zinc-500">Control Time</span>
            <span className="mt-1 text-sm font-semibold text-zinc-100">
              {formatControlTime(grappling.control_time_seconds)}
            </span>
            <span className="text-[10px] text-zinc-500">total</span>
          </div>
          <div className="flex flex-col items-center">
            <span className="text-[10px] text-zinc-500">Avg. Control</span>
            <span className="mt-1 text-sm font-semibold text-zinc-100">
              {formatControlTime(grappling.avg_control_time_seconds)}
            </span>
            <span className="text-[10px] text-zinc-500">per fight</span>
          </div>
          <div className="flex flex-col items-center">
            <span className="text-[10px] text-zinc-500">Best Submission</span>
            <span className="mt-1 text-sm font-semibold text-zinc-100">
              {grappling.top_submission || '—'}
            </span>
          </div>
        </div>
      </div>
    </motion.div>
  )
}
