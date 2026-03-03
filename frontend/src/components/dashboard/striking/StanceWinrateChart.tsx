'use client'

import type { StanceWinrate } from '@/types/dashboard'

interface StanceWinrateChartProps {
  data: StanceWinrate[]
}

const STANCES = ['Orthodox', 'Southpaw', 'Switch']

function getColor(rate: number): string {
  if (rate >= 60) return 'bg-emerald-500/30 text-emerald-300'
  if (rate >= 50) return 'bg-amber-500/20 text-amber-300'
  return 'bg-red-500/20 text-red-300'
}

export function StanceWinrateChart({ data }: StanceWinrateChartProps) {
  const matrix: Record<string, Record<string, { wins: number; win_rate: number }>> = {}
  for (const stance of STANCES) {
    matrix[stance] = {}
    for (const opp of STANCES) {
      matrix[stance][opp] = { wins: 0, win_rate: 0 }
    }
  }
  for (const row of data) {
    const w = row.winner_stance
    const l = row.loser_stance
    if (matrix[w]?.[l]) {
      matrix[w][l] = { wins: row.wins, win_rate: row.win_rate }
    }
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-xs">
        <thead>
          <tr>
            <th className="px-2 py-2 text-left text-zinc-500 font-medium">Winner \ Loser</th>
            {STANCES.map((s) => (
              <th key={s} className="px-2 py-2 text-center text-zinc-400 font-medium">
                {s}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {STANCES.map((winner) => (
            <tr key={winner} className="border-t border-white/[0.03]">
              <td className="px-2 py-2.5 font-medium text-zinc-300">{winner}</td>
              {STANCES.map((loser) => {
                const cell = matrix[winner][loser]
                if (winner === loser) {
                  return (
                    <td key={loser} className="px-2 py-2.5 text-center">
                      <span className="text-zinc-600">-</span>
                    </td>
                  )
                }
                return (
                  <td key={loser} className="px-2 py-2.5 text-center">
                    <span
                      className={`inline-block rounded-md px-2 py-1 font-medium ${getColor(cell.win_rate)}`}
                    >
                      {cell.win_rate.toFixed(1)}%
                    </span>
                    <span className="ml-1 text-zinc-600">({cell.wins})</span>
                  </td>
                )
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
