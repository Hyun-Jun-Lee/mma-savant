'use client'

import { motion } from 'framer-motion'
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Label } from 'recharts'
import type { FighterMethodRecord, FinishBreakdown } from '@/types/fighter'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { getSemanticColor } from '@/lib/chartTheme'
import { FINISH_COLORS } from '@/lib/utils'

interface Props {
  breakdown: FinishBreakdown
  nonUfcMethodRecords?: FighterMethodRecord[]
}

const tabs = [
  { key: 'ufc', label: 'UFC' },
  { key: 'another', label: 'Another' },
]

interface FinishDataItem {
  [key: string]: string | number
  key: string
  name: string
  value: number
  color: string
}

function getMethodLabel(method: string): string {
  const normalized = method.toUpperCase()
  if (normalized === 'SUB') return 'Submission'
  if (normalized === 'DEC') return 'Decision'
  return method
}

function EmptyBreakdown({ message }: { message: string }) {
  return (
    <p className="py-8 text-center text-sm text-zinc-500">
      {message}
    </p>
  )
}

function FinishPie({ data, total }: { data: FinishDataItem[]; total: number }) {
  if (total === 0) {
    return <EmptyBreakdown message="No wins to display" />
  }

  return (
    <div className="flex flex-col items-center justify-center gap-4 sm:flex-row sm:gap-6">
      <div className="h-[160px] w-[160px] shrink-0">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="50%"
              innerRadius={45}
              outerRadius={70}
              paddingAngle={2}
              dataKey="value"
              stroke="none"
              animationBegin={400}
              animationDuration={1400}
              animationEasing="ease-out"
              startAngle={90}
              endAngle={-270}
            >
              {data.map((entry) => (
                <Cell key={entry.key} fill={entry.color} />
              ))}
              <Label
                value={`${total} Wins`}
                position="center"
                style={{ fill: '#e4e4e7', fontSize: '13px', fontWeight: 600 }}
              />
            </Pie>
            <Tooltip
              contentStyle={{
                backgroundColor: '#27272a',
                border: '1px solid rgba(255,255,255,0.06)',
                borderRadius: '8px',
                fontSize: '12px',
                color: '#e4e4e7',
              }}
            />
          </PieChart>
        </ResponsiveContainer>
      </div>

      <div className="flex flex-col gap-2">
        {data.map((item) => {
          const pct = Math.round((item.value / total) * 100)
          return (
            <div key={item.key} className="flex items-center gap-2 text-sm">
              <div
                className="h-2.5 w-2.5 rounded-full"
                style={{ backgroundColor: item.color }}
              />
              <span className="text-zinc-400">{item.name}</span>
              <span className="font-medium text-zinc-200">
                {item.value} ({pct}%)
              </span>
            </div>
          )
        })}
      </div>
    </div>
  )
}

export function FinishBreakdownChart({ breakdown, nonUfcMethodRecords = [] }: Props) {
  const ufcTotal = breakdown.ko_tko + breakdown.submission + breakdown.decision
  const ufcData: FinishDataItem[] = [
    { key: 'ko_tko', name: 'KO/TKO', value: breakdown.ko_tko, color: FINISH_COLORS.ko_tko },
    {
      key: 'submission',
      name: 'Submission',
      value: breakdown.submission,
      color: FINISH_COLORS.submission,
    },
    { key: 'decision', name: 'Decision', value: breakdown.decision, color: FINISH_COLORS.decision },
  ].filter((d) => d.value > 0)
  const anotherData: FinishDataItem[] = nonUfcMethodRecords
    .filter((item) => item.result.toLowerCase() === 'win' && item.count > 0)
    .map((item, index) => ({
      key: item.method_category,
      name: getMethodLabel(item.method_category),
      value: item.count,
      color: getSemanticColor(item.method_category, index),
    }))
  const anotherTotal = anotherData.reduce((sum, item) => sum + item.value, 0)

  return (
    <motion.div
      initial={{ opacity: 0, y: 28, filter: 'blur(4px)' }}
      animate={{ opacity: 1, y: 0, filter: 'blur(0px)' }}
      transition={{ duration: 0.7, ease: [0.23, 1, 0.32, 1] }}
      className="rounded-xl border border-white/[0.06] bg-white/[0.03] p-5 transition-all duration-300 ease-out hover:border-white/[0.12] hover:bg-white/[0.05]"
    >
      <Tabs defaultValue="ufc" className="gap-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <h3 className="text-sm font-semibold text-zinc-100">
            Finish Breakdown
          </h3>
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
          <FinishPie data={ufcData} total={ufcTotal} />
        </TabsContent>

        <TabsContent value="another">
          <FinishPie data={anotherData} total={anotherTotal} />
        </TabsContent>
      </Tabs>
    </motion.div>
  )
}
