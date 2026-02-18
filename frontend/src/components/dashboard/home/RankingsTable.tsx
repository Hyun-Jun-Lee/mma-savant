'use client'

import { useState } from 'react'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { ChartCard } from '../ChartCard'
import { Trophy } from 'lucide-react'
import type { WeightClassRanking } from '@/types/dashboard'

interface RankingsTableProps {
  rankings: WeightClassRanking[]
}

const P4P_NAME = "Men's Pound-for-Pound"

export function RankingsTable({ rankings }: RankingsTableProps) {
  const defaultId =
    rankings.find(
      (r) => r.weight_class.toLowerCase() === P4P_NAME.toLowerCase()
    )?.weight_class_id ?? rankings[0]?.weight_class_id ?? 0

  const [selectedClassId, setSelectedClassId] = useState<number>(defaultId)

  const selected = rankings.find((r) => r.weight_class_id === selectedClassId)
  const fighters = selected?.fighters ?? []

  const dropdown = (
    <Select
      value={selectedClassId.toString()}
      onValueChange={(v) => setSelectedClassId(Number(v))}
    >
      <SelectTrigger className="h-7 w-[160px] border-white/[0.06] bg-white/[0.04] text-xs text-zinc-300">
        <SelectValue />
      </SelectTrigger>
      <SelectContent className="border-white/[0.06] bg-zinc-900">
        {rankings.map((r) => (
          <SelectItem
            key={r.weight_class_id}
            value={r.weight_class_id.toString()}
            className="text-xs"
          >
            {r.weight_class}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  )

  return (
    <ChartCard
      title="Rankings"
      description="Current UFC rankings by weight class"
      tooltip="UFC 공식 랭킹입니다. 드롭다운으로 체급을 선택하세요. 트로피 아이콘은 현 챔피언입니다."
      headerRight={dropdown}
    >
      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead>
            <tr className="border-b border-white/[0.06] text-xs text-zinc-500">
              <th className="pb-2 pr-4 font-medium">Rank</th>
              <th className="pb-2 pr-4 font-medium">Fighter</th>
              <th className="pb-2 pr-4 text-right font-medium">W</th>
              <th className="pb-2 pr-4 text-right font-medium">L</th>
              <th className="pb-2 text-right font-medium">D</th>
            </tr>
          </thead>
          <tbody>
            {fighters.map((f) => (
              <tr
                key={f.ranking}
                className="border-b border-white/[0.03] last:border-0"
              >
                <td className="py-2 pr-4">
                  {f.ranking === 0 ? (
                    <Trophy className="h-4 w-4 text-amber-500" />
                  ) : (
                    <span className="text-xs text-zinc-500">#{f.ranking}</span>
                  )}
                </td>
                <td className="py-2 pr-4 font-medium text-zinc-200">
                  {f.fighter_name}
                </td>
                <td className="py-2 pr-4 text-right text-zinc-300">{f.wins}</td>
                <td className="py-2 pr-4 text-right text-zinc-400">{f.losses}</td>
                <td className="py-2 text-right text-zinc-500">{f.draws}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {fighters.length === 0 && (
          <p className="py-8 text-center text-sm text-zinc-600">
            No ranking data available
          </p>
        )}
      </div>
    </ChartCard>
  )
}
