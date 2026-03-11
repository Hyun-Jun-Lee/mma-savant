'use client'

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'

const WEIGHT_CLASSES = [
  { id: 1, name: 'Flyweight' },
  { id: 2, name: 'Bantamweight' },
  { id: 3, name: 'Featherweight' },
  { id: 4, name: 'Lightweight' },
  { id: 5, name: 'Welterweight' },
  { id: 6, name: 'Middleweight' },
  { id: 7, name: 'Light Heavyweight' },
  { id: 8, name: 'Heavyweight' },
  { id: 9, name: "Women's Strawweight" },
  { id: 10, name: "Women's Flyweight" },
  { id: 11, name: "Women's Bantamweight" },
  { id: 12, name: "Women's Featherweight" },
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
