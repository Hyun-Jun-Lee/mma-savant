import { Suspense } from 'react'
import { FighterDetailClient } from '@/components/fighter/FighterDetailPage'
import { FighterDetailSkeleton } from '@/components/fighter/FighterDetailSkeleton'

export default async function FighterPage({
  params,
}: {
  params: Promise<{ id: string }>
}) {
  const { id } = await params
  return (
    <Suspense fallback={<FighterDetailSkeleton />}>
      <FighterDetailClient fighterId={Number(id)} />
    </Suspense>
  )
}
