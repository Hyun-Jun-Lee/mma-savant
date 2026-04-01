/**
 * Long-format → Wide-format pivot for Recharts multi-series charts.
 *
 * SQL often returns long format:
 *   [{round: 1, fighter_name: "A", value: 10}, {round: 1, fighter_name: "B", value: 20}, ...]
 *
 * Recharts needs wide format:
 *   [{round: 1, "A": 10, "B": 20}, ...]
 */

export type Row = Record<string, string | number>

/** SQL 결과의 문자열 숫자("19.09")를 실제 number로 변환 */
export function normalizeData(data: Row[]): Row[] {
  if (!data || data.length === 0) return data
  return data.map(row => {
    const out: Row = {}
    for (const [key, val] of Object.entries(row)) {
      if (typeof val === "string" && val.trim() !== "") {
        const num = Number(val)
        out[key] = isNaN(num) ? val : num
      } else {
        out[key] = val
      }
    }
    return out
  })
}

interface PivotResult {
  data: Row[]
  seriesKeys: string[]
  valueColumn: string
}

/** Column name이 초 단위 시간 데이터인지 판별 */
export function isSecondsField(key: string): boolean {
  const lower = key.toLowerCase()
  return lower.includes("second") || lower.includes("_sec") || lower.endsWith("_s")
}

/** 초 → "X분 Y초" 변환 (60초 미만이면 "X초") */
export function formatSeconds(value: number): string {
  if (typeof value !== "number" || isNaN(value)) return String(value)
  const abs = Math.abs(value)
  if (abs < 60) return `${Math.round(value)}초`
  const min = Math.floor(abs / 60)
  const sec = Math.round(abs % 60)
  const sign = value < 0 ? "-" : ""
  return sec === 0 ? `${sign}${min}분` : `${sign}${min}분 ${sec}초`
}

export function pivotLongToWide(
  data: Row[],
  xAxisKey: string,
  yAxis?: string,
): PivotResult | null {
  if (!data || data.length === 0) return null

  const sampleRow = data[0]

  // Find string columns that are NOT the xAxis → candidate group columns
  const groupCandidates = Object.keys(sampleRow).filter(
    key => typeof sampleRow[key] === "string" && key !== xAxisKey,
  )
  if (groupCandidates.length === 0) return null

  // Check for duplicate xAxis values (long-format indicator)
  const xValues = data.map(row => row[xAxisKey])
  const uniqueX = new Set(xValues)
  if (uniqueX.size === xValues.length) return null // all unique → already wide

  const groupCol = groupCandidates[0]

  const numericFields = Object.keys(sampleRow).filter(
    key => typeof sampleRow[key] === "number",
  )
  const valueCol = yAxis || numericFields[0]
  if (!valueCol) return null

  // Collect unique series names
  const seriesSet = new Set<string>()
  for (const row of data) {
    seriesSet.add(String(row[groupCol]))
  }
  const seriesKeys = Array.from(seriesSet)

  // Pivot: group by xAxisKey, spread group values into columns
  const pivotMap = new Map<string | number, Row>()
  for (const row of data) {
    const xVal = row[xAxisKey]
    if (!pivotMap.has(xVal)) {
      pivotMap.set(xVal, { [xAxisKey]: xVal })
    }
    const pivotRow = pivotMap.get(xVal)!
    pivotRow[String(row[groupCol])] = row[valueCol]
  }

  return {
    data: Array.from(pivotMap.values()),
    seriesKeys,
    valueColumn: valueCol,
  }
}

/**
 * Radar 차트용 전치(transpose) + 0-100 정규화.
 *
 * 입력: 소수 행(선수) x 다수 수치 열(스탯)
 *   [{name:"A", accuracy:60, wins:28}, {name:"B", accuracy:55, wins:25}]
 *
 * 출력: 행=스탯, 열=선수 (정규화 값 + 원본 값)
 *   [{stat:"accuracy", "A":100, "B":91.7, "_raw_A":60, "_raw_B":55}, ...]
 */
interface RadarTransposeResult {
  data: Row[]
  seriesKeys: string[]
}

export function transposeForRadar(
  data: Row[],
  nameKey: string,
): RadarTransposeResult | null {
  if (!data || data.length < 2) return null

  const numericFields = Object.keys(data[0]).filter(
    key => key !== nameKey && typeof data[0][key] === "number",
  )
  // 소수 행 + 다수 수치 열일 때만 전치 (행 수 < 수치 열 수)
  if (numericFields.length < 3 || data.length >= numericFields.length) return null

  const seriesKeys = data.map(row => String(row[nameKey]))

  // 스탯별 max값 (정규화 기준)
  const maxByField: Record<string, number> = {}
  for (const field of numericFields) {
    maxByField[field] = Math.max(...data.map(r => Math.abs(Number(r[field]) || 0)), 1)
  }

  const transposed: Row[] = numericFields.map(field => {
    const row: Row = { stat: field }
    for (const item of data) {
      const name = String(item[nameKey])
      const raw = Number(item[field]) || 0
      row[name] = Math.round((raw / maxByField[field]) * 100 * 10) / 10
      row[`_raw_${name}`] = raw
    }
    return row
  })

  return { data: transposed, seriesKeys }
}
