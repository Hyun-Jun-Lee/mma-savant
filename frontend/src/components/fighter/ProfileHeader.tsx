'use client'

import { motion } from 'framer-motion'
import type { FighterProfile } from '@/types/fighter'
import { Building2, Calendar, Crown, Dumbbell, MapPin, Ruler, Weight, Target, User } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { toTitleCase } from '@/lib/utils'

interface Props {
  profile: FighterProfile
}

export function ProfileHeader({ profile }: Props) {
  const rankingEntries = Object.entries(profile.rankings)

  return (
    <motion.div
      initial={{ opacity: 0, y: 28, filter: 'blur(4px)' }}
      animate={{ opacity: 1, y: 0, filter: 'blur(0px)' }}
      transition={{ duration: 0.7, ease: [0.23, 1, 0.32, 1] }}
      className="rounded-xl border border-white/[0.06] bg-white/[0.03] p-5 transition-all duration-300 ease-out hover:border-white/[0.12] hover:bg-white/[0.05]"
    >
      {/* Name & Nickname */}
      <div className="flex flex-wrap items-center gap-3">
        <h1 className="text-2xl font-bold text-zinc-100">{toTitleCase(profile.name)}</h1>
        {profile.nickname && (
          <span className="text-base text-zinc-500">
            &quot;{profile.nickname}&quot;
          </span>
        )}
        {profile.belt && (
          <Badge variant="champion">Champion</Badge>
        )}
      </div>

      {/* Nationality & Stance */}
      <div className="mt-2 flex flex-wrap items-center gap-x-4 gap-y-2 text-sm text-zinc-400">
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
        {profile.born && (
          <span className="flex min-w-0 max-w-full items-center gap-1.5">
            <Calendar className="h-3.5 w-3.5 shrink-0 text-zinc-500" />
            <span className="truncate">Born: {profile.born}</span>
          </span>
        )}
        {profile.fighting_out_of && (
          <span className="flex min-w-0 max-w-full items-center gap-1.5">
            <MapPin className="h-3.5 w-3.5 shrink-0 text-zinc-500" />
            <span className="truncate">Fighting out of: {profile.fighting_out_of}</span>
          </span>
        )}
        {profile.affiliation && (
          <span className="flex min-w-0 max-w-full items-center gap-1.5">
            <Building2 className="h-3.5 w-3.5 shrink-0 text-zinc-500" />
            <span className="truncate">Affiliation: {profile.affiliation}</span>
          </span>
        )}
        {profile.gym && (
          <span className="flex min-w-0 max-w-full items-center gap-1.5">
            <Dumbbell className="h-3.5 w-3.5 shrink-0 text-zinc-500" />
            <span className="truncate">Gym: {profile.gym}</span>
          </span>
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

      {/* Rankings / Weight Class */}
      <div className="mt-3 flex flex-wrap gap-2">
        {rankingEntries.length > 0 ? (
          rankingEntries.map(([wc, rank]) => (
            <Badge
              key={wc}
              variant={rank === 0 ? 'champion' : 'ranking'}
            >
              {rank === 0 ? (
                <span className="flex items-center gap-1">
                  <Crown className="h-3 w-3 text-yellow-400" />
                  {toTitleCase(wc)} Champion
                </span>
              ) : (
                `${toTitleCase(wc)} #${rank}`
              )}
            </Badge>
          ))
        ) : profile.weight_class ? (
          <Badge variant="ranking">
            {toTitleCase(profile.weight_class)}
          </Badge>
        ) : null}
      </div>
    </motion.div>
  )
}
