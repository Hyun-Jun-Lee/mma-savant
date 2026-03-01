import type { FighterDetailResponse } from '@/types/fighter'

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8002'

async function fighterFetch<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`)
  if (!res.ok) throw new Error(`Fighter API error: ${res.status}`)
  return res.json()
}

export const fighterApi = {
  getDetail: (fighterId: number) =>
    fighterFetch<FighterDetailResponse>(`/api/fighters/${fighterId}`),
}
