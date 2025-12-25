"use client"

import { useState, useEffect, useCallback } from "react"
import { useRouter } from "next/navigation"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { ArrowLeft } from "lucide-react"
import { AdminApiService } from "@/services/adminApi"
import { UserApiService } from "@/services/userApi"
import { AdminStats } from "./AdminStats"
import { UserTable } from "./UserTable"
import { UserEditModal } from "./UserEditModal"
import type { UserAdminResponse, UserListResponse, AdminStatsResponse } from "@/types/api"

export function SettingsContainer() {
  const router = useRouter()
  const [users, setUsers] = useState<UserAdminResponse[]>([])
  const [stats, setStats] = useState<AdminStatsResponse | null>(null)
  const [currentUserId, setCurrentUserId] = useState<number>(0)
  const [totalUsers, setTotalUsers] = useState(0)
  const [currentPage, setCurrentPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const [searchQuery, setSearchQuery] = useState("")
  const [isLoading, setIsLoading] = useState(true)
  const [isStatsLoading, setIsStatsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Modal state
  const [selectedUser, setSelectedUser] = useState<UserAdminResponse | null>(null)
  const [isModalOpen, setIsModalOpen] = useState(false)

  const pageSize = 20

  // Fetch current user ID
  useEffect(() => {
    async function fetchCurrentUser() {
      try {
        const profile = await UserApiService.getCurrentUserProfile()
        setCurrentUserId(profile.id)
      } catch (err) {
        console.error("Failed to fetch current user:", err)
      }
    }
    fetchCurrentUser()
  }, [])

  // Fetch stats
  useEffect(() => {
    async function fetchStats() {
      setIsStatsLoading(true)
      try {
        const data = await AdminApiService.getAdminStats()
        setStats(data)
      } catch (err: any) {
        console.error("Failed to fetch stats:", err)
      } finally {
        setIsStatsLoading(false)
      }
    }
    fetchStats()
  }, [])

  // Fetch users
  const fetchUsers = useCallback(async () => {
    setIsLoading(true)
    setError(null)
    try {
      const data = await AdminApiService.getAllUsers(currentPage, pageSize, searchQuery || undefined)
      setUsers(data.users)
      setTotalUsers(data.total_users)
      setTotalPages(data.total_pages)
    } catch (err: any) {
      setError(err.message || "사용자 목록을 불러오는데 실패했습니다.")
    } finally {
      setIsLoading(false)
    }
  }, [currentPage, searchQuery])

  useEffect(() => {
    fetchUsers()
  }, [fetchUsers])

  // Search handler with debounce
  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    setCurrentPage(1)
    fetchUsers()
  }

  // User update handler
  const handleUserUpdate = (updatedUser: UserAdminResponse) => {
    setUsers((prev) =>
      prev.map((u) => (u.id === updatedUser.id ? updatedUser : u))
    )
    setSelectedUser(updatedUser)
  }

  // Edit modal handlers
  const openEditModal = (user: UserAdminResponse) => {
    setSelectedUser(user)
    setIsModalOpen(true)
  }

  const closeEditModal = () => {
    setIsModalOpen(false)
    setSelectedUser(null)
  }

  return (
    <div className="relative min-h-screen bg-gradient-to-br from-zinc-900 via-gray-900 to-slate-900 p-4 md:p-8">
      {/* 배경 패턴 */}
      <div className="fixed inset-0 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-gray-700/20 via-transparent to-transparent pointer-events-none" />
      <div className="fixed inset-0 bg-grid-white/[0.02] bg-[size:50px_50px] pointer-events-none" />

      <div className="relative z-10 max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Button
              variant="ghost"
              size="icon"
              onClick={() => router.push("/")}
              className="text-zinc-400 hover:text-white hover:bg-white/10"
            >
              <ArrowLeft className="h-5 w-5" />
            </Button>
            <div>
              <h1 className="text-2xl font-bold text-white">Settings</h1>
              <p className="text-zinc-400">사용자 관리 및 시스템 설정</p>
            </div>
          </div>
        </div>

        {/* Stats */}
        <AdminStats stats={stats} isLoading={isStatsLoading} />

        {/* User Management */}
        <Card className="bg-zinc-900/50 border-white/10 backdrop-blur-sm">
          <CardHeader>
            <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
              <div>
                <CardTitle className="text-white">사용자 관리</CardTitle>
                <CardDescription className="text-zinc-400">
                  총 {totalUsers}명의 사용자
                </CardDescription>
              </div>
              <form onSubmit={handleSearch} className="flex gap-2">
                <Input
                  type="text"
                  placeholder="이름 또는 이메일 검색..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-64 bg-white/5 border-white/10 text-white placeholder:text-zinc-500"
                />
                <Button type="submit" variant="outline" className="bg-transparent border-white/20 text-zinc-300 hover:bg-white/10 hover:text-white">
                  검색
                </Button>
              </form>
            </div>
          </CardHeader>
          <CardContent>
            {error && (
              <div className="mb-4 p-3 bg-red-500/10 border border-red-500/20 text-red-400 rounded-lg">
                {error}
              </div>
            )}

            {isLoading ? (
              <div className="flex justify-center py-8">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-white" />
              </div>
            ) : (
              <>
                <UserTable
                  users={users}
                  onEditUser={openEditModal}
                  currentUserId={currentUserId}
                />

                {/* Pagination */}
                {totalPages > 1 && (
                  <div className="flex items-center justify-center gap-2 mt-6">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                      disabled={currentPage === 1}
                      className="bg-transparent border-white/20 text-zinc-300 hover:bg-white/10 hover:text-white disabled:opacity-50"
                    >
                      이전
                    </Button>
                    <span className="text-sm text-zinc-400">
                      {currentPage} / {totalPages}
                    </span>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
                      disabled={currentPage === totalPages}
                      className="bg-transparent border-white/20 text-zinc-300 hover:bg-white/10 hover:text-white disabled:opacity-50"
                    >
                      다음
                    </Button>
                  </div>
                )}
              </>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Edit Modal */}
      <UserEditModal
        user={selectedUser}
        isOpen={isModalOpen}
        onClose={closeEditModal}
        onUpdate={handleUserUpdate}
        currentUserId={currentUserId}
      />
    </div>
  )
}
