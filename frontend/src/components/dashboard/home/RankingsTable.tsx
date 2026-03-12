'use client'

import { useState, useRef } from 'react'
import Link from 'next/link'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { ChartCard } from '../ChartCard'
import { Crown, Loader2, Search, X } from 'lucide-react'
import { toTitleCase } from '@/lib/utils'
import { dashboardApi } from '@/services/dashboardApi'
import type { WeightClassRanking, FighterSearchItem } from '@/types/dashboard'

interface RankingsTableProps {
  rankings: WeightClassRanking[]
  index?: number
}

const P4P_NAME = "Men's Pound-for-Pound"

export function RankingsTable({ rankings, index }: RankingsTableProps) {
  const defaultId =
    rankings.find(
      (r) => r.weight_class.toLowerCase() === P4P_NAME.toLowerCase()
    )?.weight_class_id ?? rankings[0]?.weight_class_id ?? 0

  const [selectedClassId, setSelectedClassId] = useState<number>(defaultId)

  // search state
  const [searchQuery, setSearchQuery] = useState('')
  const [isSearchMode, setIsSearchMode] = useState(false)
  const [searchResults, setSearchResults] = useState<FighterSearchItem[]>([])
  const [loading, setLoading] = useState(false)
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  const selected = rankings.find((r) => r.weight_class_id === selectedClassId)
  const fighters = selected?.fighters ?? []

  function handleSearchInput(value: string) {
    setSearchQuery(value)
    if (debounceRef.current) clearTimeout(debounceRef.current)

    if (!value.trim()) {
      clearSearch()
      return
    }

    debounceRef.current = setTimeout(async () => {
      setLoading(true)
      setIsSearchMode(true)
      try {
        const data = await dashboardApi.searchFighters(value.trim())
        setSearchResults(data)
      } catch {
        // keep current state
      } finally {
        setLoading(false)
      }
    }, 300)
  }

  function clearSearch() {
    setSearchQuery('')
    setIsSearchMode(false)
    setSearchResults([])
  }

  function formatRankings(r: Record<string, number>): string {
    const entries = Object.entries(r)
    if (entries.length === 0) return '-'
    return entries.map(([wc, rank]) => `${wc} #${rank}`).join(', ')
  }

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
      tooltip="Official UFC rankings. Select a weight class from the dropdown. Use the search box to find any fighter by name. Crown icon indicates the current champion."
      headerRight={isSearchMode ? undefined : dropdown}
      index={index}
    >
      {/* Search Input */}
      <div className="relative mb-3">
        <Search className="absolute left-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-zinc-500" />
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => handleSearchInput(e.target.value)}
          placeholder="Search fighters..."
          className="w-full rounded-md border border-white/[0.06] bg-white/[0.03] py-1.5 pl-8 pr-8 text-sm text-zinc-200 placeholder-zinc-600 outline-none transition-colors focus:border-white/[0.12] focus:bg-white/[0.05]"
        />
        {searchQuery && (
          <button
            onClick={clearSearch}
            className="absolute right-2 top-1/2 -translate-y-1/2 rounded p-0.5 text-zinc-500 hover:text-zinc-300"
          >
            <X className="h-3.5 w-3.5" />
          </button>
        )}
      </div>

      <div className="overflow-x-auto">
        {loading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="h-5 w-5 animate-spin text-zinc-500" />
          </div>
        ) : isSearchMode ? (
          /* Search Results Table */
          <>
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-white/[0.06] text-xs text-zinc-500">
                  <th className="pb-2 pr-4 font-medium">Fighter</th>
                  <th className="pb-2 pr-4 text-right font-medium">Record</th>
                  <th className="pb-2 text-right font-medium">Rankings</th>
                </tr>
              </thead>
              <tbody>
                {searchResults.map((item) => (
                  <tr
                    key={item.fighter.id}
                    className="border-b border-white/[0.03] last:border-0"
                  >
                    <td className="py-2 pr-4">
                      <Link
                        href={`/fighters/${item.fighter.id}`}
                        className="font-medium text-zinc-200 hover:text-blue-400 hover:underline transition-colors"
                      >
                        {toTitleCase(item.fighter.name)}
                      </Link>
                      {item.fighter.nickname && (
                        <span className="ml-1.5 text-xs text-zinc-500">
                          &quot;{item.fighter.nickname}&quot;
                        </span>
                      )}
                    </td>
                    <td className="py-2 pr-4 text-right text-xs text-zinc-300">
                      {item.fighter.wins}-{item.fighter.losses}-{item.fighter.draws}
                    </td>
                    <td className="py-2 text-right text-xs text-zinc-500">
                      {formatRankings(item.rankings)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {searchResults.length === 0 && (
              <p className="py-8 text-center text-sm text-zinc-600">
                No fighters matching &quot;{searchQuery}&quot;
              </p>
            )}
            {searchResults.length > 0 && (
              <p className="mt-3 text-center text-xs text-zinc-600">
                {searchResults.length} result{searchResults.length !== 1 ? 's' : ''} found
              </p>
            )}
          </>
        ) : (
          /* Default Rankings Table */
          <>
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
                        <Crown className="h-4 w-4 text-amber-500" />
                      ) : (
                        <span className="text-xs text-zinc-500">#{f.ranking}</span>
                      )}
                    </td>
                    <td className="py-2 pr-4 font-medium text-zinc-200">
                      <Link
                        href={`/fighters/${f.fighter_id}`}
                        className="hover:text-blue-400 hover:underline transition-colors"
                      >
                        {toTitleCase(f.fighter_name)}
                      </Link>
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
          </>
        )}
      </div>
    </ChartCard>
  )
}
