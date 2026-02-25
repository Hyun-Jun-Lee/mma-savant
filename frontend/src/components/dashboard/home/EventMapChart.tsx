'use client'

import { useRef, useEffect } from 'react'
import type { EventMapLocation } from '@/types/dashboard'

interface EventMapChartProps {
  data: EventMapLocation[]
}

export function EventMapChart({ data }: EventMapChartProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const mapRef = useRef<L.Map | null>(null)

  useEffect(() => {
    if (!containerRef.current) return

    let cancelled = false

    import('leaflet').then((L) => {
      if (cancelled || !containerRef.current) return

      // Cleanup previous instance
      if (mapRef.current) {
        mapRef.current.remove()
        mapRef.current = null
      }

      const map = L.map(containerRef.current, {
        center: [20, 0],
        zoom: 2,
        minZoom: 2,
        maxZoom: 10,
        scrollWheelZoom: false,
        attributionControl: false,
        zoomControl: true,
      })

      // Dark theme tiles (CartoDB Dark Matter)
      L.tileLayer(
        'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png',
        { maxZoom: 19 },
      ).addTo(map)

      // Scale marker radius by event count
      const maxCount = Math.max(...data.map((d) => d.event_count), 1)

      data.forEach((loc) => {
        const ratio = loc.event_count / maxCount
        const radius = 5 + ratio * 20

        L.circleMarker([loc.latitude, loc.longitude], {
          radius,
          fillColor: '#a855f7',
          color: '#c084fc',
          weight: 1,
          opacity: 0.9,
          fillOpacity: 0.6,
        })
          .addTo(map)
          .bindPopup(
            `<div style="font-family:sans-serif;font-size:12px;line-height:1.5">
              <strong>${loc.location}</strong><br/>
              ${loc.event_count} event${loc.event_count > 1 ? 's' : ''}
              ${loc.last_event_name ? `<br/><span style="color:#888">Latest: ${loc.last_event_name}</span>` : ''}
            </div>`,
            { className: 'leaflet-dark-popup' },
          )
      })

      mapRef.current = map
    })

    return () => {
      cancelled = true
      if (mapRef.current) {
        mapRef.current.remove()
        mapRef.current = null
      }
    }
  }, [data])

  return (
    <div
      ref={containerRef}
      className="h-[400px] w-full rounded-lg overflow-hidden"
    />
  )
}
