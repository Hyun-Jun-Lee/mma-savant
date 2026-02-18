'use client'

import { useState, type ReactNode } from 'react'
import { ChevronDown, ChevronUp } from 'lucide-react'

interface ExpandableListProps {
  initialCount?: number
  expandedCount?: number
  children: (count: number) => ReactNode
}

export function ExpandableList({
  initialCount = 5,
  expandedCount = 10,
  children,
}: ExpandableListProps) {
  const [expanded, setExpanded] = useState(false)
  const count = expanded ? expandedCount : initialCount

  return (
    <div>
      {children(count)}
      <button
        onClick={() => setExpanded(!expanded)}
        className="mt-3 flex w-full items-center justify-center gap-1 rounded-md py-1.5 text-xs font-medium text-zinc-500 transition-colors hover:bg-white/[0.04] hover:text-zinc-300"
      >
        {expanded ? (
          <>
            접기 <ChevronUp className="h-3 w-3" />
          </>
        ) : (
          <>
            더보기 <ChevronDown className="h-3 w-3" />
          </>
        )}
      </button>
    </div>
  )
}
