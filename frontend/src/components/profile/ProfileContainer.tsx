"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import { useAuth } from "@/hooks/useAuth"
import { useUser } from "@/hooks/useUser"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Badge } from "@/components/ui/badge"
import { Separator } from "@/components/ui/separator"
import {
  ArrowLeft,
  Mail,
  Calendar,
  Activity,
  TrendingUp,
  Clock,
  Edit2,
  Check,
  X,
  Loader2
} from "lucide-react"
import { Input } from "@/components/ui/input"
import { UserProfileResponse } from "@/types/api"

export function ProfileContainer() {
  const router = useRouter()
  const { user } = useAuth()
  const {
    userProfile,
    isLoading,
    isUpdating,
    loadUserProfile,
    updateUserProfile
  } = useUser()

  const [isEditing, setIsEditing] = useState(false)
  const [editName, setEditName] = useState("")

  useEffect(() => {
    loadUserProfile()
  }, [loadUserProfile])

  useEffect(() => {
    if (userProfile?.name) {
      setEditName(userProfile.name)
    }
  }, [userProfile])

  const handleSave = async () => {
    if (editName.trim() && editName !== userProfile?.name) {
      const success = await updateUserProfile({ name: editName.trim() })
      if (success) {
        setIsEditing(false)
      }
    } else {
      setIsEditing(false)
    }
  }

  const handleCancel = () => {
    setEditName(userProfile?.name || "")
    setIsEditing(false)
  }

  const getInitials = (name?: string | null, email?: string | null) => {
    if (name) {
      return name
        .split(" ")
        .map((n) => n[0])
        .join("")
        .toUpperCase()
        .slice(0, 2)
    }
    if (email) {
      return email[0].toUpperCase()
    }
    return "U"
  }

  const formatDate = (dateString?: string) => {
    if (!dateString) return "-"
    return new Date(dateString).toLocaleDateString("ko-KR", {
      year: "numeric",
      month: "long",
      day: "numeric"
    })
  }

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-zinc-900 via-gray-900 to-slate-900 flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-white" />
      </div>
    )
  }

  const profile = userProfile || {
    id: 0,
    name: user?.name || "",
    email: user?.email || "",
    picture: user?.image || "",
    total_requests: 0,
    daily_requests: 0,
    remaining_requests: 100,
    is_active: true,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString()
  } as UserProfileResponse

  return (
    <div className="min-h-screen bg-gradient-to-br from-zinc-900 via-gray-900 to-slate-900">
      {/* 배경 패턴 */}
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-gray-700/20 via-transparent to-transparent" />
      <div className="absolute inset-0 bg-grid-white/[0.02] bg-[size:50px_50px]" />

      <div className="relative max-w-4xl mx-auto px-4 py-8">
        {/* 헤더 */}
        <div className="flex items-center justify-between mb-8">
          <Button
            variant="ghost"
            className="text-zinc-400 hover:text-white hover:bg-white/10"
            onClick={() => router.back()}
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back
          </Button>

          <div className="flex items-center space-x-2">
            <div className="w-8 h-8 bg-white rounded-lg flex items-center justify-center">
              <span className="text-zinc-900 font-bold text-sm">MS</span>
            </div>
            <span className="text-white font-semibold">MMA Savant</span>
          </div>
        </div>

        {/* 프로필 카드 */}
        <Card className="bg-white/5 backdrop-blur-sm border-white/10 mb-6">
          <CardHeader className="pb-4">
            <div className="flex items-start justify-between">
              <div className="flex items-center space-x-4">
                <Avatar className="w-20 h-20 border-2 border-white/20">
                  <AvatarImage
                    src={profile.picture || user?.image || ""}
                    alt={profile.name || ""}
                  />
                  <AvatarFallback className="bg-zinc-700 text-white text-xl">
                    {getInitials(profile.name, profile.email)}
                  </AvatarFallback>
                </Avatar>
                <div className="space-y-1">
                  {isEditing ? (
                    <div className="flex items-center space-x-2">
                      <Input
                        value={editName}
                        onChange={(e) => setEditName(e.target.value)}
                        className="h-8 w-48 bg-white/10 border-white/20 text-white"
                        placeholder="Enter name"
                        autoFocus
                      />
                      <Button
                        size="sm"
                        variant="ghost"
                        className="h-8 w-8 p-0 text-emerald-400 hover:text-emerald-300 hover:bg-emerald-400/10"
                        onClick={handleSave}
                        disabled={isUpdating}
                      >
                        {isUpdating ? (
                          <Loader2 className="w-4 h-4 animate-spin" />
                        ) : (
                          <Check className="w-4 h-4" />
                        )}
                      </Button>
                      <Button
                        size="sm"
                        variant="ghost"
                        className="h-8 w-8 p-0 text-red-400 hover:text-red-300 hover:bg-red-400/10"
                        onClick={handleCancel}
                        disabled={isUpdating}
                      >
                        <X className="w-4 h-4" />
                      </Button>
                    </div>
                  ) : (
                    <div className="flex items-center space-x-2">
                      <CardTitle className="text-2xl text-white">
                        {profile.name || "User"}
                      </CardTitle>
                      <Button
                        size="sm"
                        variant="ghost"
                        className="h-8 w-8 p-0 text-zinc-400 hover:text-white hover:bg-white/10"
                        onClick={() => setIsEditing(true)}
                      >
                        <Edit2 className="w-4 h-4" />
                      </Button>
                    </div>
                  )}
                  <CardDescription className="text-zinc-400 flex items-center">
                    <Mail className="w-4 h-4 mr-2" />
                    {profile.email}
                  </CardDescription>
                </div>
              </div>
              <Badge
                variant="outline"
                className="border-emerald-500/50 text-emerald-400 bg-emerald-500/10"
              >
                Active
              </Badge>
            </div>
          </CardHeader>
          <Separator className="bg-white/10" />
          <CardContent className="pt-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="flex items-center space-x-3 text-zinc-300">
                <Calendar className="w-5 h-5 text-zinc-500" />
                <div>
                  <p className="text-sm text-zinc-500">Member since</p>
                  <p className="font-medium">{formatDate(profile.created_at)}</p>
                </div>
              </div>
              <div className="flex items-center space-x-3 text-zinc-300">
                <Clock className="w-5 h-5 text-zinc-500" />
                <div>
                  <p className="text-sm text-zinc-500">Last updated</p>
                  <p className="font-medium">{formatDate(profile.updated_at)}</p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* 사용량 통계 카드 */}
        <Card className="bg-white/5 backdrop-blur-sm border-white/10 mb-6">
          <CardHeader>
            <CardTitle className="text-lg text-white flex items-center">
              <Activity className="w-5 h-5 mr-2 text-zinc-400" />
              Usage Statistics
            </CardTitle>
            <CardDescription className="text-zinc-500">
              Your API usage and remaining quota
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {/* 총 요청 수 */}
              <div className="bg-white/5 rounded-lg p-4 border border-white/10">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-zinc-500 text-sm">Total Requests</span>
                  <TrendingUp className="w-4 h-4 text-blue-400" />
                </div>
                <p className="text-3xl font-bold text-white">
                  {profile.total_requests?.toLocaleString() || 0}
                </p>
                <p className="text-xs text-zinc-500 mt-1">All time</p>
              </div>

              {/* 오늘 요청 수 */}
              <div className="bg-white/5 rounded-lg p-4 border border-white/10">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-zinc-500 text-sm">Today's Requests</span>
                  <Activity className="w-4 h-4 text-amber-400" />
                </div>
                <p className="text-3xl font-bold text-white">
                  {profile.daily_requests?.toLocaleString() || 0}
                </p>
                <p className="text-xs text-zinc-500 mt-1">Since midnight</p>
              </div>

              {/* 남은 요청 수 */}
              <div className="bg-white/5 rounded-lg p-4 border border-white/10">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-zinc-500 text-sm">Remaining Today</span>
                  <div className={`w-2 h-2 rounded-full ${
                    (profile.remaining_requests || 0) > 50
                      ? "bg-emerald-400"
                      : (profile.remaining_requests || 0) > 20
                        ? "bg-amber-400"
                        : "bg-red-400"
                  }`} />
                </div>
                <p className="text-3xl font-bold text-white">
                  {profile.remaining_requests?.toLocaleString() || 0}
                </p>
                <p className="text-xs text-zinc-500 mt-1">Daily limit: 100</p>
              </div>
            </div>

            {/* 사용량 프로그레스 바 */}
            <div className="mt-6">
              <div className="flex justify-between text-sm mb-2">
                <span className="text-zinc-500">Daily Usage</span>
                <span className="text-zinc-400">
                  {profile.daily_requests || 0} / 100
                </span>
              </div>
              <div className="h-2 bg-white/10 rounded-full overflow-hidden">
                <div
                  className={`h-full rounded-full transition-all duration-300 ${
                    (profile.daily_requests || 0) > 80
                      ? "bg-red-500"
                      : (profile.daily_requests || 0) > 50
                        ? "bg-amber-500"
                        : "bg-emerald-500"
                  }`}
                  style={{ width: `${Math.min((profile.daily_requests || 0), 100)}%` }}
                />
              </div>
            </div>
          </CardContent>
        </Card>

      </div>
    </div>
  )
}
