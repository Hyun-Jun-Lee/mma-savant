'use client'

import { useRef, useState, useEffect, type ReactNode } from 'react'
import { motion, AnimatePresence } from 'framer-motion'

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
  const containerRef = useRef<HTMLDivElement>(null)
  const [indicator, setIndicator] = useState({ left: 0, width: 0 })

  useEffect(() => {
    const container = containerRef.current
    if (!container) return
    const activeBtn = container.querySelector<HTMLButtonElement>(`[data-key="${activeKey}"]`)
    if (!activeBtn) return
    setIndicator({
      left: activeBtn.offsetLeft,
      width: activeBtn.offsetWidth,
    })
  }, [activeKey])

  return (
    <div ref={containerRef} className="relative inline-flex gap-1 rounded-lg bg-white/[0.04] p-1">
      <motion.div
        className="absolute top-1 bottom-1 rounded-md bg-white/10"
        animate={{ left: indicator.left, width: indicator.width }}
        transition={{ duration: 0.3, ease: [0.23, 1, 0.32, 1] }}
      />
      {tabs.map(({ key, label }) => (
        <button
          key={key}
          data-key={key}
          onClick={() => onChange(key)}
          className={`relative z-10 rounded-md font-medium transition-colors ${padding} ${
            activeKey === key
              ? 'text-white'
              : 'text-zinc-500 hover:text-zinc-300'
          }`}
        >
          {label}
        </button>
      ))}
    </div>
  )
}

interface TabContentProps {
  activeKey: string
  children: ReactNode
}

export function TabContent({ activeKey, children }: TabContentProps) {
  return (
    <AnimatePresence mode="wait">
      <motion.div
        key={activeKey}
        initial={{ opacity: 0, x: 12 }}
        animate={{ opacity: 1, x: 0 }}
        exit={{ opacity: 0, x: -12 }}
        transition={{ duration: 0.25, ease: 'easeOut' }}
      >
        {children}
      </motion.div>
    </AnimatePresence>
  )
}
