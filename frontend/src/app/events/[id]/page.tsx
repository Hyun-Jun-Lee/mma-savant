import { Suspense } from 'react'
import { EventDetailClient } from '@/components/event/EventDetailPage'
import { EventDetailSkeleton } from '@/components/event/EventDetailSkeleton'

export default async function EventPage({
  params,
}: {
  params: Promise<{ id: string }>
}) {
  const { id } = await params
  return (
    <Suspense fallback={<EventDetailSkeleton />}>
      <EventDetailClient eventId={Number(id)} />
    </Suspense>
  )
}
