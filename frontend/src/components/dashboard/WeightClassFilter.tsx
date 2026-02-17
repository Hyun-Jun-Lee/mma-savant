'use client'

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'

const WEIGHT_CLASSES = [
  { id: 1, name: 'Strawweight' },
  { id: 2, name: 'Flyweight' },
  { id: 3, name: 'Bantamweight' },
  { id: 4, name: 'Featherweight' },
  { id: 5, name: 'Lightweight' },
  { id: 6, name: 'Welterweight' },
  { id: 7, name: 'Middleweight' },
  { id: 8, name: 'Light Heavyweight' },
  { id: 9, name: 'Heavyweight' },
  { id: 10, name: "Women's Strawweight" },
  { id: 11, name: "Women's Flyweight" },
  { id: 12, name: "Women's Bantamweight" },
] as const

interface WeightClassFilterProps {
  value?: number
  onChange: (value?: number) => void
}

export function WeightClassFilter({ value, onChange }: WeightClassFilterProps) {
  return (
    <Select
      value={value?.toString() ?? 'all'}
      onValueChange={(v) => onChange(v === 'all' ? undefined : Number(v))}
    >
      <SelectTrigger className="h-8 w-[180px] border-white/[0.06] bg-white/[0.04] text-xs text-zinc-300">
        <SelectValue placeholder="All Weight Classes" />
      </SelectTrigger>
      <SelectContent className="border-white/[0.06] bg-zinc-900">
        <SelectItem value="all" className="text-xs">
          All Weight Classes
        </SelectItem>
        {WEIGHT_CLASSES.map(({ id, name }) => (
          <SelectItem key={id} value={id.toString()} className="text-xs">
            {name}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  )
}
