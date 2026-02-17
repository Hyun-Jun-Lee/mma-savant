'use client'

import Link from 'next/link'
import { usePathname, useRouter } from 'next/navigation'
import { useAuth } from '@/hooks/useAuth'
import { UserProfile } from '@/components/auth/UserProfile'
import { Button } from '@/components/ui/button'
import { BarChart3, MessageSquare } from 'lucide-react'

const NAV_ITEMS = [
  { href: '/', label: 'Dashboard', icon: BarChart3 },
  { href: '/chat', label: 'AI Chat', icon: MessageSquare },
] as const

export function GlobalNav() {
  const pathname = usePathname()
  const router = useRouter()
  const { isAuthenticated, isLoading } = useAuth()

  return (
    <nav className="sticky top-0 z-50 border-b border-white/[0.06] bg-[#050507]/80 backdrop-blur-md">
      <div className="mx-auto flex h-14 max-w-7xl items-center justify-between px-4">
        {/* Logo */}
        <Link href="/" className="flex items-center gap-2">
          <div className="flex h-7 w-7 items-center justify-center rounded-md bg-white">
            <span className="text-xs font-bold text-zinc-900">MS</span>
          </div>
          <span className="text-sm font-semibold text-white">MMA Savant</span>
        </Link>

        {/* Nav Links */}
        <div className="flex items-center gap-1">
          {NAV_ITEMS.map(({ href, label, icon: Icon }) => {
            const isActive =
              href === '/' ? pathname === '/' : pathname.startsWith(href)

            return (
              <Link
                key={href}
                href={href}
                className={`flex items-center gap-1.5 rounded-md px-3 py-1.5 text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-white/10 text-white'
                    : 'text-zinc-400 hover:bg-white/[0.06] hover:text-zinc-200'
                }`}
              >
                <Icon className="h-4 w-4" />
                {label}
              </Link>
            )
          })}
        </div>

        {/* User Area */}
        <div className="flex items-center">
          {isAuthenticated ? (
            <UserProfile />
          ) : (
            !isLoading && (
              <Button
                size="sm"
                variant="ghost"
                className="text-sm text-zinc-400 hover:text-white"
                onClick={() => router.push('/auth/signin')}
              >
                Sign in
              </Button>
            )
          )}
        </div>
      </div>
    </nav>
  )
}
