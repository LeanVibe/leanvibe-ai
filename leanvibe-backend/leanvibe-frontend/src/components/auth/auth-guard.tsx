'use client'

import * as React from 'react'
import { useRouter } from 'next/navigation'
import { useAuthStore } from '@/stores/auth-store'
import { PageLoading } from '@/components/layout/dashboard-layout'

interface AuthGuardProps {
  children: React.ReactNode
  requireAuth?: boolean
  redirectTo?: string
}

export function AuthGuard({ 
  children, 
  requireAuth = true, 
  redirectTo = '/login' 
}: AuthGuardProps) {
  const router = useRouter()
  const { isAuthenticated, isLoading, getCurrentUser } = useAuthStore()
  const [isInitialized, setIsInitialized] = React.useState(false)

  React.useEffect(() => {
    const initializeAuth = async () => {
      // Check if we have a token stored
      const token = typeof window !== 'undefined' 
        ? localStorage.getItem('access_token') 
        : null

      if (token && !isAuthenticated) {
        try {
          await getCurrentUser()
        } catch (error) {
          console.error('Failed to get current user:', error)
          // Token might be invalid, clear it
          localStorage.removeItem('access_token')
          localStorage.removeItem('refresh_token')
        }
      }
      
      setIsInitialized(true)
    }

    if (!isInitialized) {
      initializeAuth()
    }
  }, [isAuthenticated, getCurrentUser, isInitialized])

  React.useEffect(() => {
    if (isInitialized && !isLoading) {
      if (requireAuth && !isAuthenticated) {
        router.push(redirectTo)
      } else if (!requireAuth && isAuthenticated) {
        router.push('/dashboard')
      }
    }
  }, [isAuthenticated, isLoading, requireAuth, router, redirectTo, isInitialized])

  // Show loading while initializing or redirecting
  if (!isInitialized || isLoading) {
    return <PageLoading />
  }

  // If requiring auth and not authenticated, don't render children
  if (requireAuth && !isAuthenticated) {
    return <PageLoading />
  }

  // If not requiring auth and authenticated, don't render children
  if (!requireAuth && isAuthenticated) {
    return <PageLoading />
  }

  return <>{children}</>
}

// Higher-order component for protecting pages
export function withAuth<P extends object>(
  Component: React.ComponentType<P>,
  options: { requireAuth?: boolean; redirectTo?: string } = {}
) {
  const { requireAuth = true, redirectTo = '/login' } = options

  return function AuthenticatedComponent(props: P) {
    return (
      <AuthGuard requireAuth={requireAuth} redirectTo={redirectTo}>
        <Component {...props} />
      </AuthGuard>
    )
  }
}