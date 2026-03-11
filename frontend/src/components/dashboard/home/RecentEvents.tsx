'use client'

import { useState, useRef } from 'react'
import Link from 'next/link'
import { Calendar, ChevronLeft, ChevronRight, Loader2, Search, X } from 'lucide-react'
import { ChartCard } from '../ChartCard'
import { dashboardApi } from '@/services/dashboardApi'
import type { RecentEvent } from '@/types/dashboard'

const PAGE_SIZE = 5

interface RecentEventsProps {
  events: RecentEvent[]
  totalEvents: number
  index?: number
}

type DisplayEvent = {
  id: number
  name: string
  location: string | null
  event_date: string | null
}

export function RecentEvents({ events, totalEvents, index }: RecentEventsProps) {
  const [page, setPage] = useState(0) // 0 = initial (props data)
  const [displayEvents, setDisplayEvents] = useState<DisplayEvent[]>(events)
  const [loading, setLoading] = useState(false)
  const [total, setTotal] = useState(totalEvents)

  // search state
  const [searchQuery, setSearchQuery] = useState('')
  const [isSearchMode, setIsSearchMode] = useState(false)
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  const currentPage = page === 0 ? 1 : page
  const totalPages = isSearchMode ? 1 : Math.ceil(total / PAGE_SIZE)

  async function goToPage(targetPage: number) {
    if (targetPage < 1 || targetPage > totalPages || loading) return
    setLoading(true)
    try {
      const data = await dashboardApi.getEvents(targetPage, PAGE_SIZE)
      setDisplayEvents(data.events)
      setTotal(data.total)
      setPage(targetPage)
    } catch {
      // stay on current page
    } finally {
      setLoading(false)
    }
  }

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
        const data = await dashboardApi.searchEvents(value.trim())
        setDisplayEvents(data.results.map((r) => r.event))
        setTotal(data.total)
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
    setDisplayEvents(events)
    setTotal(totalEvents)
    setPage(0)
  }

  function buildPageNumbers(): (number | '...')[] {
    if (totalPages <= 7) return Array.from({ length: totalPages }, (_, i) => i + 1)
    const pages: (number | '...')[] = [1]
    if (currentPage > 3) pages.push('...')
    for (let i = Math.max(2, currentPage - 1); i <= Math.min(totalPages - 1, currentPage + 1); i++) {
      pages.push(i)
    }
    if (currentPage < totalPages - 2) pages.push('...')
    pages.push(totalPages)
    return pages
  }

  return (
    <ChartCard title="Events" description="All UFC events" tooltip="Browse and search all UFC events." index={index}>
      {/* Search Input */}
      <div className="relative mb-3">
        <Search className="absolute left-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-zinc-500" />
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => handleSearchInput(e.target.value)}
          placeholder="Search events..."
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

      {/* Event List */}
      <div className="space-y-2">
        {loading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="h-5 w-5 animate-spin text-zinc-500" />
          </div>
        ) : (
          displayEvents.map((event) => (
            <Link
              key={event.id}
              href={`/events/${event.id}`}
              className="flex items-start justify-between gap-3 rounded-lg border border-white/[0.04] bg-white/[0.02] p-3 transition-colors hover:border-white/[0.08] hover:bg-white/[0.04]"
            >
              <div className="min-w-0">
                <p className="truncate text-sm font-medium text-zinc-200">
                  {event.name}
                </p>
                {event.location && (
                  <p className="mt-0.5 text-xs text-zinc-500">{event.location}</p>
                )}
              </div>
              <div className="shrink-0 text-right">
                {event.event_date && (
                  <div className="flex items-center gap-1 text-xs text-zinc-500">
                    <Calendar className="h-3 w-3" />
                    {new Date(event.event_date).toLocaleDateString('en-US', {
                      month: 'short',
                      day: 'numeric',
                      year: 'numeric',
                    })}
                  </div>
                )}
              </div>
            </Link>
          ))
        )}
        {!loading && displayEvents.length === 0 && (
          <p className="py-8 text-center text-sm text-zinc-600">
            {isSearchMode ? `No events matching "${searchQuery}"` : 'No events found'}
          </p>
        )}
      </div>

      {/* Pagination — hidden in search mode */}
      {!isSearchMode && totalPages > 1 && (
        <div className="mt-4 flex items-center justify-center gap-1">
          <button
            onClick={() => goToPage(currentPage - 1)}
            disabled={currentPage <= 1 || loading}
            className="rounded p-1 text-zinc-500 transition-colors hover:bg-white/[0.06] hover:text-zinc-300 disabled:opacity-30 disabled:hover:bg-transparent"
          >
            <ChevronLeft className="h-4 w-4" />
          </button>
          {buildPageNumbers().map((p, i) =>
            p === '...' ? (
              <span key={`dots-${i}`} className="px-1 text-xs text-zinc-600">
                ...
              </span>
            ) : (
              <button
                key={p}
                onClick={() => goToPage(p)}
                disabled={loading}
                className={`min-w-[28px] rounded px-1.5 py-0.5 text-xs transition-colors ${
                  p === currentPage
                    ? 'bg-white/[0.1] font-medium text-zinc-200'
                    : 'text-zinc-500 hover:bg-white/[0.06] hover:text-zinc-300'
                }`}
              >
                {p}
              </button>
            )
          )}
          <button
            onClick={() => goToPage(currentPage + 1)}
            disabled={currentPage >= totalPages || loading}
            className="rounded p-1 text-zinc-500 transition-colors hover:bg-white/[0.06] hover:text-zinc-300 disabled:opacity-30 disabled:hover:bg-transparent"
          >
            <ChevronRight className="h-4 w-4" />
          </button>
        </div>
      )}

      {/* Search result count */}
      {isSearchMode && !loading && displayEvents.length > 0 && (
        <p className="mt-3 text-center text-xs text-zinc-600">
          {total} result{total !== 1 ? 's' : ''} found
        </p>
      )}
    </ChartCard>
  )
}
