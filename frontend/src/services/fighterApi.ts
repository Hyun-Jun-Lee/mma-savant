import { api } from '@/lib/api'
import type { FighterDetailResponse } from '@/types/fighter'

export const fighterApi = {
  getDetail: async (fighterId: number): Promise<FighterDetailResponse> => {
    const response = await api.get<FighterDetailResponse>(`/api/fighters/${fighterId}`)
    return response.data!
  },
}
