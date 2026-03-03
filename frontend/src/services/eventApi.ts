import type { EventDetailResponse } from '@/types/event'

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8002'

async function eventFetch<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`)
  if (!res.ok) throw new Error(`Event API error: ${res.status}`)
  return res.json()
}

export const eventApi = {
  getDetail: (eventId: number) =>
    eventFetch<EventDetailResponse>(`/api/events/${eventId}`),
}
