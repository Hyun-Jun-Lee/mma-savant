"use client"

import { AuthGuard } from "@/components/auth/AuthGuard"
import { ProfileContainer } from "@/components/profile/ProfileContainer"

export default function ProfilePage() {
  return (
    <AuthGuard>
      <ProfileContainer />
    </AuthGuard>
  )
}
