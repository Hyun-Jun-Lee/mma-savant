'use client'

import { motion } from 'framer-motion'
import CountUp from 'react-countup'
import type { FighterPromotionRecord, FighterRecord } from '@/types/fighter'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'

interface Props {
  record: FighterRecord
  nonUfcPromotionRecords?: FighterPromotionRecord[]
}

const tabs = [
  { key: 'ufc', label: 'UFC' },
  { key: 'another', label: 'Another' },
]

function easeOutCubic(t: number, b: number, c: number, d: number) {
  const p = t / d
  return b + c * (1 - Math.pow(1 - p, 3))
}

function RecordNumbers({
  wins,
  losses,
  draws,
  noContests,
}: {
  wins: number
  losses: number
  draws: number
  noContests?: number
}) {
  return (
    <div className="flex flex-wrap items-baseline gap-4">
      <div className="text-center">
        <span className="text-3xl font-bold text-emerald-400">
          <CountUp end={wins} duration={1.5} easingFn={easeOutCubic} />
        </span>
        <p className="text-xs text-zinc-500">Wins</p>
      </div>
      <span className="text-xl text-zinc-600">-</span>
      <div className="text-center">
        <span className="text-3xl font-bold text-red-400">
          <CountUp end={losses} duration={1.5} easingFn={easeOutCubic} />
        </span>
        <p className="text-xs text-zinc-500">Losses</p>
      </div>
      <span className="text-xl text-zinc-600">-</span>
      <div className="text-center">
        <span className="text-3xl font-bold text-amber-400">
          <CountUp end={draws} duration={1.5} easingFn={easeOutCubic} />
        </span>
        <p className="text-xs text-zinc-500">Draws</p>
      </div>
      {noContests != null && noContests > 0 && (
        <>
          <span className="text-xl text-zinc-600">-</span>
          <div className="text-center">
            <span className="text-3xl font-bold text-zinc-300">
              <CountUp end={noContests} duration={1.5} easingFn={easeOutCubic} />
            </span>
            <p className="text-xs text-zinc-500">NC</p>
          </div>
        </>
      )}
    </div>
  )
}

function EmptyRecord({ message }: { message: string }) {
  return (
    <p className="py-8 text-center text-sm text-zinc-500">
      {message}
    </p>
  )
}

export function RecordCard({ record, nonUfcPromotionRecords = [] }: Props) {
  const total = record.wins + record.losses + record.draws
  const { type, count } = record.current_streak
  const anotherTotals = nonUfcPromotionRecords.reduce(
    (acc, item) => ({
      wins: acc.wins + item.wins,
      losses: acc.losses + item.losses,
      draws: acc.draws + item.draws,
      noContests: acc.noContests + item.no_contests,
    }),
    { wins: 0, losses: 0, draws: 0, noContests: 0 }
  )
  const anotherTotal =
    anotherTotals.wins +
    anotherTotals.losses +
    anotherTotals.draws +
    anotherTotals.noContests

  return (
    <motion.div
      initial={{ opacity: 0, y: 28, filter: 'blur(4px)' }}
      animate={{ opacity: 1, y: 0, filter: 'blur(0px)' }}
      transition={{ duration: 0.7, ease: [0.23, 1, 0.32, 1] }}
      className="rounded-xl border border-white/[0.06] bg-white/[0.03] p-5 transition-all duration-300 ease-out hover:border-white/[0.12] hover:bg-white/[0.05]"
    >
      <Tabs defaultValue="ufc" className="gap-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <h3 className="text-sm font-semibold text-zinc-100">Record</h3>
          <TabsList className="h-8 rounded-lg bg-white/[0.04] p-1">
            {tabs.map((tab) => (
              <TabsTrigger
                key={tab.key}
                value={tab.key}
                className="h-6 rounded-md px-2.5 py-0 text-xs text-zinc-500 data-[state=active]:border-transparent data-[state=active]:bg-white/10 data-[state=active]:text-zinc-100"
              >
                {tab.label}
              </TabsTrigger>
            ))}
          </TabsList>
        </div>

        <TabsContent value="ufc">
          {total === 0 ? (
            <EmptyRecord message="No fights recorded" />
          ) : (
            <>
              <RecordNumbers
                wins={record.wins}
                losses={record.losses}
                draws={record.draws}
              />

              <div className="mt-4">
                <div className="flex items-center justify-between text-xs text-zinc-400">
                  <span>Win Rate</span>
                  <span className="font-medium text-zinc-200">
                    <CountUp end={record.win_rate} duration={1.5} decimals={1} easingFn={easeOutCubic} />%
                  </span>
                </div>
                <div className="mt-1 h-2 w-full overflow-hidden rounded-full bg-white/[0.06]">
                  <motion.div
                    className="h-full rounded-full bg-emerald-500"
                    initial={{ width: 0 }}
                    animate={{ width: `${record.win_rate}%` }}
                    transition={{ duration: 0.9, ease: 'easeOut', delay: 0.8 }}
                  />
                </div>
              </div>

              {type !== 'none' && count > 0 && (
                <div className="mt-3">
                  <Badge variant={type === 'win' ? 'win' : 'loss'}>
                    {count} {type === 'win' ? 'Win' : 'Loss'} Streak
                  </Badge>
                </div>
              )}
            </>
          )}
        </TabsContent>

        <TabsContent value="another">
          {anotherTotal === 0 ? (
            <EmptyRecord message="No non-UFC promotion records" />
          ) : (
            <div>
              <RecordNumbers
                wins={anotherTotals.wins}
                losses={anotherTotals.losses}
                draws={anotherTotals.draws}
                noContests={anotherTotals.noContests}
              />

              <div className="mt-4 divide-y divide-white/[0.03] rounded-lg border border-white/[0.06] bg-white/[0.02]">
                {nonUfcPromotionRecords.map((item) => (
                  <div
                    key={item.promotion_name}
                    className="grid grid-cols-[1fr_auto] items-center gap-3 px-3 py-2.5 text-xs"
                  >
                    <span className="min-w-0 truncate text-zinc-300">
                      {item.promotion_name}
                    </span>
                    <span className="shrink-0 font-semibold text-zinc-100">
                      {item.wins}-{item.losses}-{item.draws}
                      {item.no_contests > 0 ? ` (${item.no_contests} NC)` : ''}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </TabsContent>
      </Tabs>
    </motion.div>
  )
}
