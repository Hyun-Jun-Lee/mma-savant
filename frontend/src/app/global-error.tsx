'use client'

export default function GlobalError({
  error: _error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  console.error('Global layout error:', _error)

  return (
    <html lang="en" className="dark">
      <body className="bg-[#050507] text-zinc-100 antialiased">
        <div className="flex min-h-screen flex-col items-center justify-center gap-4 px-4">
          <h2 className="text-xl font-semibold">문제가 발생했습니다</h2>
          <p className="max-w-md text-center text-sm text-zinc-400">
            페이지를 불러오는 중 오류가 발생했습니다.
          </p>
          <button
            onClick={reset}
            className="mt-2 rounded-md border border-zinc-700 bg-zinc-800 px-4 py-2 text-sm text-zinc-100 hover:bg-zinc-700"
          >
            다시 시도
          </button>
        </div>
      </body>
    </html>
  )
}
