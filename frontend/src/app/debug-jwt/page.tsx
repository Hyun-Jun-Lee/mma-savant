'use client'

import { useSession } from 'next-auth/react'
import jwt from 'jsonwebtoken'

export default function DebugJwtPage() {
  const { data: session } = useSession()

  const testJwtCreation = () => {
    const secret = process.env.NEXTAUTH_SECRET || 'fallback-secret'
    console.log('Client-side NEXTAUTH_SECRET:', secret)
    
    const payload = {
      sub: 'test-user',
      email: 'test@example.com',
      name: 'Test User',
      iat: Math.floor(Date.now() / 1000),
      exp: Math.floor(Date.now() / 1000) + 3600,
    }
    
    try {
      const token = jwt.sign(payload, secret, { algorithm: 'HS256' })
      console.log('Test JWT created:', token)
      
      const decoded = jwt.verify(token, secret)
      console.log('Test JWT verified:', decoded)
    } catch (error) {
      console.error('JWT test failed:', error)
    }
  }

  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold mb-4">JWT Debug Page</h1>
      
      <div className="space-y-4">
        <div>
          <h2 className="text-lg font-semibold">Session Info:</h2>
          <pre className="bg-gray-100 p-4 rounded overflow-auto">
            {JSON.stringify(session, null, 2)}
          </pre>
        </div>
        
        <div>
          <h2 className="text-lg font-semibold">Environment Variables:</h2>
          <pre className="bg-gray-100 p-4 rounded">
            NEXTAUTH_SECRET: {process.env.NEXTAUTH_SECRET || 'undefined'}
          </pre>
        </div>
        
        <button 
          onClick={testJwtCreation}
          className="bg-blue-500 text-white px-4 py-2 rounded"
        >
          Test JWT Creation
        </button>
      </div>
    </div>
  )
}