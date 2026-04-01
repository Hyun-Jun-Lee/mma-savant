"use client"

import { useMemo } from "react"
import { motion } from "framer-motion"
import { VisualizationData } from "@/types/chat"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { normalizeData } from "./pivotData"
import { BarChartVisualization } from "./BarChartVisualization"
import { PieChartVisualization } from "./PieChartVisualization"
import { LineChartVisualization } from "./LineChartVisualization"
import { AreaChartVisualization } from "./AreaChartVisualization"
import { RadarChartVisualization } from "./RadarChartVisualization"
import { ScatterPlotVisualization } from "./ScatterPlotVisualization"
import { HorizontalBarVisualization } from "./HorizontalBarVisualization"
import { StackedBarVisualization } from "./StackedBarVisualization"
import { RingListVisualization } from "./RingListVisualization"
import { LollipopVisualization } from "./LollipopVisualization"
import { InsightsSummary } from "./InsightsSummary"
import { BarChart3, PieChart, TrendingUp, Activity, Radar, ScatterChart, MessageSquare, AlignLeft, Layers, Target, Minus } from "lucide-react"

interface ChartRendererProps {
  data: VisualizationData
}

export function ChartRenderer({ data }: ChartRendererProps) {
  const { selected_visualization, visualization_data, insights } = data

  // SQL 결과의 문자열 숫자("19.09")를 실제 number로 정규화
  const normalizedData = useMemo(
    () => normalizeData(visualization_data.data),
    [visualization_data.data],
  )

  const getIcon = () => {
    switch (selected_visualization) {
      case "bar_chart":
        return <BarChart3 className="w-5 h-5" />
      case "pie_chart":
        return <PieChart className="w-5 h-5" />
      case "line_chart":
        return <TrendingUp className="w-5 h-5" />
      case "area_chart":
        return <Activity className="w-5 h-5" />
      case "radar_chart":
        return <Radar className="w-5 h-5" />
      case "scatter_plot":
        return <ScatterChart className="w-5 h-5" />
      case "text_summary":
        return <MessageSquare className="w-5 h-5" />
      case "horizontal_bar":
        return <AlignLeft className="w-5 h-5" />
      case "stacked_bar":
        return <Layers className="w-5 h-5" />
      case "ring_list":
        return <Target className="w-5 h-5" />
      case "lollipop_chart":
        return <Minus className="w-5 h-5" />
      default:
        return <BarChart3 className="w-5 h-5" />
    }
  }

  const renderVisualization = () => {
    const commonProps = {
      data: normalizedData,
      xAxis: visualization_data.x_axis,
      yAxis: visualization_data.y_axis,
    }

    switch (selected_visualization) {
      case "bar_chart":
        return <BarChartVisualization {...commonProps} />
      case "pie_chart":
        return <PieChartVisualization {...commonProps} />
      case "line_chart":
        return <LineChartVisualization {...commonProps} />
      case "area_chart":
        return <AreaChartVisualization {...commonProps} />
      case "radar_chart":
        return <RadarChartVisualization {...commonProps} />
      case "scatter_plot":
        return <ScatterPlotVisualization {...commonProps} />
      case "horizontal_bar":
        return <HorizontalBarVisualization {...commonProps} />
      case "stacked_bar":
        return <StackedBarVisualization {...commonProps} />
      case "ring_list":
        return <RingListVisualization {...commonProps} />
      case "lollipop_chart":
        return <LollipopVisualization {...commonProps} />
      case "text_summary":
        return <InsightsSummary insights={insights} />
      default:
        return <BarChartVisualization {...commonProps} />
    }
  }

  return (
    <motion.div
      className="w-full max-w-4xl space-y-4"
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, ease: "easeOut" }}
    >
      <Card className="bg-white/[0.03] backdrop-blur-sm border-white/[0.06]">
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center gap-2 text-white text-lg">
            {getIcon()}
            {visualization_data.title}
          </CardTitle>
        </CardHeader>
        <CardContent>
          {renderVisualization()}
        </CardContent>
      </Card>

      {selected_visualization !== "text_summary" && insights.length > 0 && (
        <Card className="bg-white/[0.02] backdrop-blur-sm border-white/[0.06]">
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2 text-white text-base">
              <MessageSquare className="w-4 h-4" />
              Key Insights
            </CardTitle>
          </CardHeader>
          <CardContent>
            <InsightsSummary insights={insights} />
          </CardContent>
        </Card>
      )}
    </motion.div>
  )
}
