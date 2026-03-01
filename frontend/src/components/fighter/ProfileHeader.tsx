'use client'

import type { FighterProfile } from '@/types/fighter'
import { Trophy, Ruler, Weight, Target, User } from 'lucide-react'

interface Props {
  profile: FighterProfile
}

export function ProfileHeader({ profile }: Props) {
  const rankingEntries = Object.entries(profile.rankings)

  return (
    <div className="rounded-xl border border-white/[0.06] bg-white/[0.03] p-5 transition-all duration-300 ease-out hover:border-white/[0.12] hover:bg-white/[0.05]">
      {/* Name & Nickname */}
      <div className="flex flex-wrap items-center gap-3">
        <h1 className="text-2xl font-bold text-zinc-100">{profile.name}</h1>
        {profile.nickname && (
          <span className="text-base text-zinc-500">
            &quot;{profile.nickname}&quot;
          </span>
        )}
        {profile.belt && (
          <span className="rounded-full bg-yellow-500/20 px-2.5 py-0.5 text-xs font-medium text-yellow-400">
            Champion
          </span>
        )}
      </div>

      {/* Nationality & Stance */}
      <div className="mt-2 flex flex-wrap items-center gap-4 text-sm text-zinc-400">
        {profile.nationality && (
          <span className="flex items-center gap-1.5">
            <User className="h-3.5 w-3.5" />
            {profile.nationality}
          </span>
        )}
        {profile.stance && (
          <span className="flex items-center gap-1.5">
            <Target className="h-3.5 w-3.5" />
            {profile.stance}
          </span>
        )}
        {profile.age != null && (
          <span>Age: {profile.age}</span>
        )}
      </div>

      {/* Physical Stats */}
      <div className="mt-3 flex flex-wrap gap-6 text-sm text-zinc-400">
        {profile.height_cm != null && (
          <span className="flex items-center gap-1.5">
            <Ruler className="h-3.5 w-3.5 text-zinc-500" />
            {profile.height_cm} cm
          </span>
        )}
        {profile.weight_kg != null && (
          <span className="flex items-center gap-1.5">
            <Weight className="h-3.5 w-3.5 text-zinc-500" />
            {profile.weight_kg} kg
          </span>
        )}
        {profile.reach_cm != null && (
          <span className="flex items-center gap-1.5">
            <Target className="h-3.5 w-3.5 text-zinc-500" />
            Reach: {profile.reach_cm} cm
          </span>
        )}
      </div>

      {/* Rankings */}
      {rankingEntries.length > 0 && (
        <div className="mt-3 flex flex-wrap gap-2">
          {rankingEntries.map(([wc, rank]) => (
            <span
              key={wc}
              className="rounded-full border border-white/[0.06] bg-white/[0.03] px-2.5 py-0.5 text-xs font-medium text-zinc-300"
            >
              {rank === 0 ? (
                <span className="flex items-center gap-1">
                  <Trophy className="h-3 w-3 text-yellow-400" />
                  {wc} Champion
                </span>
              ) : (
                `${wc}: #${rank}`
              )}
            </span>
          ))}
        </div>
      )}
    </div>
  )
}
