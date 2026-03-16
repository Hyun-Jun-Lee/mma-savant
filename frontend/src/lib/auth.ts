import NextAuth from "next-auth"
import Google from "next-auth/providers/google"
import { env } from "@/config/env"

export const { handlers, signIn, signOut, auth } = NextAuth({
  providers: [
    Google({
      clientId: process.env.GOOGLE_CLIENT_ID!,
      clientSecret: process.env.GOOGLE_CLIENT_SECRET!,
    }),
  ],
  secret: process.env.NEXTAUTH_SECRET,
  callbacks: {
    async jwt({ token, user, account }) {
      if (user) {
        token.sub = user.id
        token.email = user.email
        token.name = user.name
        token.picture = user.image
      }

      // 최초 Google 로그인 시 서버사이드에서 백엔드 JWT 1회 교환
      if (account?.access_token) {
        try {
          const response = await fetch(
            `${env.BACKEND_URL}/api/user/google-token`,
            {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({
                google_token: account.access_token,
                email: user?.email || token.email || "",
                name: user?.name || token.name || "",
                picture: user?.image || token.picture || "",
              }),
            }
          )

          if (response.ok) {
            const data = await response.json()
            token.backendToken = data.access_token
            token.backendTokenExpiry = Date.now() + data.expires_in * 1000
          } else {
            console.error(
              "Failed to exchange Google token for backend JWT:",
              response.status
            )
          }
        } catch (error) {
          console.error("Backend token exchange error:", error)
        }
      }

      return token
    },
    async session({ session, token }) {
      if (token) {
        session.user.id = token.sub as string
        session.user.email = token.email as string
        session.user.name = token.name as string
        session.user.image = token.picture as string
        session.backendToken = token.backendToken as string
        session.backendTokenExpiry = token.backendTokenExpiry as number
      }
      return session
    },
  },
  pages: {
    signIn: "/auth/signin",
    error: "/auth/error",
  },
})
