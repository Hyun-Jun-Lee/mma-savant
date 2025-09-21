"use client"

interface TableVisualizationProps {
  data: Record<string, string | number>[]
  xAxis?: string
  yAxis?: string
}

export function TableVisualization({ data }: TableVisualizationProps) {
  if (!data || data.length === 0) {
    return (
      <div className="p-8 text-center text-zinc-400">
        표시할 데이터가 없습니다.
      </div>
    )
  }

  // 첫 번째 행에서 컬럼 헤더 추출
  const columns = Object.keys(data[0])

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-zinc-600">
            {columns.map((column) => (
              <th
                key={column}
                className="px-4 py-3 text-left text-zinc-300 font-medium uppercase tracking-wider"
              >
                {column}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.map((row, index) => (
            <tr
              key={index}
              className="border-b border-zinc-700/50 hover:bg-zinc-700/20 transition-colors"
            >
              {columns.map((column) => (
                <td
                  key={column}
                  className="px-4 py-3 text-zinc-200"
                >
                  {typeof row[column] === 'number'
                    ? row[column].toLocaleString()
                    : String(row[column])
                  }
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>

      {/* 데이터 요약 정보 */}
      <div className="mt-4 text-xs text-zinc-500 flex justify-between">
        <span>총 {data.length}개 행</span>
        <span>{columns.length}개 컬럼</span>
      </div>
    </div>
  )
}