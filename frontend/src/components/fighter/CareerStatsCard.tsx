'use client'

import type { CareerStats } from '@/types/fighter'

interface Props {
  stats: CareerStats | null
}

function StatRow({
  label,
  landed,
  attempted,
}: {
  label: string
  landed: number
  attempted: number
}) {
  const pct = attempted > 0 ? Math.round((landed / attempted) * 100) : 0
  return (
    <div>
      <div className="flex items-center justify-between text-xs">
        <span className="text-zinc-400">{label}</span>
        <span className="text-zinc-200">
          {landed}/{attempted} ({pct}%)
        </span>
      </div>
      <div className="mt-1 h-1.5 w-full overflow-hidden rounded-full bg-white/[0.06]">
        <div
          className="h-full rounded-full bg-blue-500 transition-all duration-500"
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  )
}

function formatControlTime(seconds: number): string {
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  return `${m}:${s.toString().padStart(2, '0')}`
}

export function CareerStatsCard({ stats }: Props) {
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

  // Head/Body/Leg proportional bar
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

  return (
    <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
      {/* Striking */}
      <div className="rounded-xl border border-white/[0.06] bg-white/[0.03] p-5 transition-all duration-300 ease-out hover:border-white/[0.12] hover:bg-white/[0.05]">
        <h3 className="mb-4 text-sm font-semibold text-zinc-100">
          Striking ({striking.match_count} fights)
        </h3>

        <div className="space-y-3">
          <StatRow
            label="Sig. Strikes"
            landed={striking.sig_str_landed}
            attempted={striking.sig_str_attempted}
          />

          <div className="flex items-center justify-between text-xs">
            <span className="text-zinc-400">Knockdowns</span>
            <span className="font-medium text-zinc-200">
              {striking.knockdowns}
            </span>
          </div>

          {/* Target Distribution */}
          {totalTargetLanded > 0 && (
            <div>
              <p className="mb-1 text-xs text-zinc-400">Target Distribution</p>
              <div className="flex h-3 w-full overflow-hidden rounded-full">
                <div
                  className="bg-red-400 transition-all"
                  style={{ width: `${headPct}%` }}
                  title={`Head: ${headPct}%`}
                />
                <div
                  className="bg-blue-400 transition-all"
                  style={{ width: `${bodyPct}%` }}
                  title={`Body: ${bodyPct}%`}
                />
                <div
                  className="bg-green-400 transition-all"
                  style={{ width: `${legPct}%` }}
                  title={`Leg: ${legPct}%`}
                />
              </div>
              <div className="mt-1 flex gap-3 text-[10px] text-zinc-500">
                <span className="flex items-center gap-1">
                  <span className="h-1.5 w-1.5 rounded-full bg-red-400" />
                  Head {headPct}%
                </span>
                <span className="flex items-center gap-1">
                  <span className="h-1.5 w-1.5 rounded-full bg-blue-400" />
                  Body {bodyPct}%
                </span>
                <span className="flex items-center gap-1">
                  <span className="h-1.5 w-1.5 rounded-full bg-green-400" />
                  Leg {legPct}%
                </span>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Grappling */}
      <div className="rounded-xl border border-white/[0.06] bg-white/[0.03] p-5 transition-all duration-300 ease-out hover:border-white/[0.12] hover:bg-white/[0.05]">
        <h3 className="mb-4 text-sm font-semibold text-zinc-100">
          Grappling ({grappling.match_count} fights)
        </h3>

        <div className="space-y-3">
          <StatRow
            label="Takedowns"
            landed={grappling.td_landed}
            attempted={grappling.td_attempted}
          />

          <div className="flex items-center justify-between text-xs">
            <span className="text-zinc-400">Control Time (Total)</span>
            <span className="font-medium text-zinc-200">
              {formatControlTime(grappling.control_time_seconds)}
            </span>
          </div>

          <div className="flex items-center justify-between text-xs">
            <span className="text-zinc-400">Avg. Control Time</span>
            <span className="font-medium text-zinc-200">
              {formatControlTime(grappling.avg_control_time_seconds)}
            </span>
          </div>

          <div className="flex items-center justify-between text-xs">
            <span className="text-zinc-400">Submission Attempts</span>
            <span className="font-medium text-zinc-200">
              {grappling.submission_attempts}
            </span>
          </div>
        </div>
      </div>
    </div>
  )
}
