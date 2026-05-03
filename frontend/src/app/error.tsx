'use client'

import { useEffect } from 'react'
import { AlertCircle } from 'lucide-react'
import { Button } from '@/components/ui/button'

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  useEffect(() => {
    console.error('Global error:', error)
  }, [error])

  return (
    <div className="flex min-h-[60vh] flex-col items-center justify-center gap-4 px-4">
      <AlertCircle className="h-12 w-12 text-red-400" />
      <h2 className="text-xl font-semibold text-zinc-100">
        문제가 발생했습니다
      </h2>
      <p className="max-w-md text-center text-sm text-zinc-400">
        예상치 못한 오류가 발생했습니다. 아래 버튼을 눌러 다시 시도해주세요.
      </p>
      <Button onClick={reset} variant="outline" className="mt-2">
        다시 시도
      </Button>
    </div>
  )
}
