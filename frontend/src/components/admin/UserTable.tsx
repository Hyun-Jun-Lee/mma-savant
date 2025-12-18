"use client"

import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import type { UserAdminResponse } from "@/types/api"

interface UserTableProps {
  users: UserAdminResponse[]
  onEditUser: (user: UserAdminResponse) => void
  currentUserId: number
}

export function UserTable({ users, onEditUser, currentUserId }: UserTableProps) {
  const formatDate = (dateString?: string) => {
    if (!dateString) return "-"
    return new Date(dateString).toLocaleDateString("ko-KR", {
      year: "numeric",
      month: "short",
      day: "numeric",
    })
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full border-collapse">
        <thead>
          <tr className="border-b border-white/10 bg-white/5">
            <th className="text-left p-3 font-medium text-zinc-300">사용자</th>
            <th className="text-left p-3 font-medium text-zinc-300">상태</th>
            <th className="text-center p-3 font-medium text-zinc-300">일일 사용량</th>
            <th className="text-center p-3 font-medium text-zinc-300">총 요청</th>
            <th className="text-left p-3 font-medium text-zinc-300">가입일</th>
            <th className="text-center p-3 font-medium text-zinc-300">관리</th>
          </tr>
        </thead>
        <tbody>
          {users.map((user) => (
            <tr
              key={user.id}
              className="border-b border-white/10 hover:bg-white/5 transition-colors"
            >
              {/* User Info */}
              <td className="p-3">
                <div className="flex items-center gap-3">
                  <Avatar className="h-10 w-10">
                    <AvatarImage src={user.picture} alt={user.name || "User"} />
                    <AvatarFallback className="bg-white/10 text-white">
                      {user.name?.charAt(0) || user.email?.charAt(0) || "U"}
                    </AvatarFallback>
                  </Avatar>
                  <div className="min-w-0">
                    <p className="font-medium truncate max-w-[200px] text-white">
                      {user.name || "Unknown"}
                      {user.id === currentUserId && (
                        <span className="ml-2 text-xs text-zinc-500">(You)</span>
                      )}
                    </p>
                    <p className="text-sm text-zinc-400 truncate max-w-[200px]">
                      {user.email}
                    </p>
                  </div>
                </div>
              </td>

              {/* Status Badges */}
              <td className="p-3">
                <div className="flex gap-1 flex-wrap">
                  {user.is_admin && (
                    <Badge variant="default" className="bg-red-600">
                      Admin
                    </Badge>
                  )}
                  {user.is_active ? (
                    <Badge variant="outline" className="text-green-600 border-green-600">
                      Active
                    </Badge>
                  ) : (
                    <Badge variant="secondary">Inactive</Badge>
                  )}
                </div>
              </td>

              {/* Daily Usage */}
              <td className="p-3 text-center">
                <div className="flex flex-col items-center">
                  <span className="font-medium text-zinc-300">
                    {user.daily_requests} / {user.daily_request_limit}
                  </span>
                  <div className="w-20 h-1.5 bg-white/10 rounded-full mt-1">
                    <div
                      className="h-full bg-red-500 rounded-full transition-all"
                      style={{
                        width: `${Math.min(
                          (user.daily_requests / user.daily_request_limit) * 100,
                          100
                        )}%`,
                      }}
                    />
                  </div>
                </div>
              </td>

              {/* Total Requests */}
              <td className="p-3 text-center font-medium text-white">
                {user.total_requests.toLocaleString()}
              </td>

              {/* Created Date */}
              <td className="p-3 text-sm text-zinc-400">
                {formatDate(user.created_at)}
              </td>

              {/* Actions */}
              <td className="p-3 text-center">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => onEditUser(user)}
                  className="bg-transparent border-white/20 text-zinc-300 hover:bg-white/10 hover:text-white"
                >
                  설정
                </Button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {users.length === 0 && (
        <div className="text-center py-8 text-zinc-500">
          사용자가 없습니다.
        </div>
      )}
    </div>
  )
}
