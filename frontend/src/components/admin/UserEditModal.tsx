"use client"

import { useState } from "react"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { AdminApiService } from "@/services/adminApi"
import type { UserAdminResponse } from "@/types/api"

interface UserEditModalProps {
  user: UserAdminResponse | null
  isOpen: boolean
  onClose: () => void
  onUpdate: (user: UserAdminResponse) => void
  currentUserId: number
}

export function UserEditModal({
  user,
  isOpen,
  onClose,
  onUpdate,
  currentUserId,
}: UserEditModalProps) {
  const [dailyLimit, setDailyLimit] = useState<number>(user?.daily_request_limit ?? 100)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const isSelf = user?.id === currentUserId

  // user가 변경될 때 dailyLimit 업데이트
  useState(() => {
    if (user) {
      setDailyLimit(user.daily_request_limit)
    }
  })

  const handleLimitUpdate = async () => {
    if (!user) return
    setIsLoading(true)
    setError(null)

    try {
      const updated = await AdminApiService.updateUserLimit(user.id, {
        daily_request_limit: dailyLimit,
      })
      onUpdate(updated)
    } catch (err: any) {
      setError(err.message || "요청 제한 업데이트에 실패했습니다.")
    } finally {
      setIsLoading(false)
    }
  }

  const handleAdminToggle = async () => {
    if (!user || isSelf) return
    setIsLoading(true)
    setError(null)

    try {
      const updated = await AdminApiService.updateUserAdminStatus(user.id, {
        is_admin: !user.is_admin,
      })
      onUpdate(updated)
    } catch (err: any) {
      setError(err.message || "관리자 권한 변경에 실패했습니다.")
    } finally {
      setIsLoading(false)
    }
  }

  const handleActiveToggle = async () => {
    if (!user || isSelf) return
    setIsLoading(true)
    setError(null)

    try {
      const updated = await AdminApiService.updateUserActiveStatus(user.id, {
        is_active: !user.is_active,
      })
      onUpdate(updated)
    } catch (err: any) {
      setError(err.message || "활성화 상태 변경에 실패했습니다.")
    } finally {
      setIsLoading(false)
    }
  }

  if (!user) return null

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>사용자 설정</DialogTitle>
          <DialogDescription>
            사용자의 권한 및 요청 제한을 관리합니다.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          {/* User Info */}
          <div className="flex items-center gap-4 p-4 bg-gray-50 rounded-lg">
            <Avatar className="h-12 w-12">
              <AvatarImage src={user.picture} alt={user.name || "User"} />
              <AvatarFallback>
                {user.name?.charAt(0) || user.email?.charAt(0) || "U"}
              </AvatarFallback>
            </Avatar>
            <div className="flex-1 min-w-0">
              <p className="font-medium truncate">{user.name || "Unknown"}</p>
              <p className="text-sm text-gray-500 truncate">{user.email}</p>
            </div>
            <div className="flex gap-1">
              {user.is_admin && (
                <Badge variant="default" className="bg-red-600">Admin</Badge>
              )}
              {!user.is_active && (
                <Badge variant="secondary">Inactive</Badge>
              )}
              {isSelf && (
                <Badge variant="outline">You</Badge>
              )}
            </div>
          </div>

          {/* Daily Limit */}
          <div className="space-y-2">
            <label className="text-sm font-medium">일일 요청 제한</label>
            <div className="flex gap-2">
              <Input
                type="number"
                min={0}
                max={10000}
                value={dailyLimit}
                onChange={(e) => setDailyLimit(Number(e.target.value))}
                className="flex-1"
              />
              <Button
                onClick={handleLimitUpdate}
                disabled={isLoading || dailyLimit === user.daily_request_limit}
              >
                저장
              </Button>
            </div>
            <p className="text-xs text-gray-500">
              현재 사용량: {user.daily_requests} / {user.daily_request_limit}
            </p>
          </div>

          {/* Admin Toggle */}
          <div className="flex items-center justify-between p-3 border rounded-lg">
            <div>
              <p className="font-medium">관리자 권한</p>
              <p className="text-sm text-gray-500">
                {user.is_admin ? "관리자입니다" : "일반 사용자입니다"}
              </p>
            </div>
            <Button
              variant={user.is_admin ? "destructive" : "default"}
              size="sm"
              onClick={handleAdminToggle}
              disabled={isLoading || isSelf}
            >
              {user.is_admin ? "권한 해제" : "권한 부여"}
            </Button>
          </div>

          {/* Active Toggle */}
          <div className="flex items-center justify-between p-3 border rounded-lg">
            <div>
              <p className="font-medium">계정 상태</p>
              <p className="text-sm text-gray-500">
                {user.is_active ? "활성 상태" : "비활성 상태"}
              </p>
            </div>
            <Button
              variant={user.is_active ? "destructive" : "default"}
              size="sm"
              onClick={handleActiveToggle}
              disabled={isLoading || isSelf}
            >
              {user.is_active ? "비활성화" : "활성화"}
            </Button>
          </div>

          {/* Error Message */}
          {error && (
            <p className="text-sm text-red-500 bg-red-50 p-2 rounded">{error}</p>
          )}

          {/* Self Warning */}
          {isSelf && (
            <p className="text-sm text-amber-600 bg-amber-50 p-2 rounded">
              자신의 관리자 권한이나 계정 상태는 변경할 수 없습니다.
            </p>
          )}
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={onClose}>
            닫기
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
