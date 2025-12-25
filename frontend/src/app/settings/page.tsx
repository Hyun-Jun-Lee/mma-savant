"use client"

import { AdminGuard } from "@/components/admin/AdminGuard"
import { SettingsContainer } from "@/components/admin/SettingsContainer"

export default function SettingsPage() {
  return (
    <AdminGuard>
      <SettingsContainer />
    </AdminGuard>
  )
}
