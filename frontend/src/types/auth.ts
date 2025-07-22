import { DefaultSession } from "next-auth"

declare module "next-auth" {
  interface Session {
    user: {
      id: string
    } & DefaultSession["user"]
    accessToken?: string
    googleAccessToken?: string
  }

  interface User {
    id: string
  }
}

export interface AuthUser {
  id: string
  name?: string | null
  email?: string | null
  image?: string | null
}

export interface AuthState {
  user: AuthUser | null
  isLoading: boolean
  isAuthenticated: boolean
}