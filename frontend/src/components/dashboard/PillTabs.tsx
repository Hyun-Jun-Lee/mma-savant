'use client'

interface PillTabsProps {
  tabs: { key: string; label: string }[]
  activeKey: string
  onChange: (key: string) => void
  size?: 'sm' | 'md'
}

export function PillTabs({
  tabs,
  activeKey,
  onChange,
  size = 'md',
}: PillTabsProps) {
  const padding = size === 'sm' ? 'px-2.5 py-1 text-xs' : 'px-3 py-1.5 text-sm'

  return (
    <div className="inline-flex gap-1 rounded-lg bg-white/[0.04] p-1">
      {tabs.map(({ key, label }) => (
        <button
          key={key}
          onClick={() => onChange(key)}
          className={`rounded-md font-medium transition-colors ${padding} ${
            activeKey === key
              ? 'bg-white/10 text-white'
              : 'text-zinc-500 hover:text-zinc-300'
          }`}
        >
          {label}
        </button>
      ))}
    </div>
  )
}
