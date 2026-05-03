import { api } from '@/lib/api'
import type { EventDetailResponse } from '@/types/event'

export const eventApi = {
  getDetail: async (eventId: number): Promise<EventDetailResponse> => {
    const response = await api.get<EventDetailResponse>(`/api/events/${eventId}`)
    return response.data!
  },
}
