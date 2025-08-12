'use client'

import * as React from 'react'
import { Sidebar } from './sidebar'
import { Header } from './header'
import { cn } from '@/lib/utils'

interface DashboardLayoutProps {
  children: React.ReactNode
  className?: string
}

export function DashboardLayout({ children, className }: DashboardLayoutProps) {
  const [showMobileSidebar, setShowMobileSidebar] = React.useState(false)

  const toggleMobileSidebar = () => {
    setShowMobileSidebar(!showMobileSidebar)
  }

  return (
    <div className="flex h-screen overflow-hidden">
      {/* Desktop Sidebar */}
      <div className="hidden lg:block">
        <Sidebar />
      </div>

      {/* Mobile Sidebar Overlay */}
      {showMobileSidebar && (
        <div className="fixed inset-0 z-50 lg:hidden">
          <div 
            className="absolute inset-0 bg-black/50"
            onClick={() => setShowMobileSidebar(false)}
          />
          <div className="relative">
            <Sidebar />
          </div>
        </div>
      )}

      {/* Main Content Area */}
      <div className="flex flex-1 flex-col overflow-hidden">
        <Header 
          onMenuClick={toggleMobileSidebar}
          showMobileMenu={showMobileSidebar}
        />
        
        <main className={cn(
          "flex-1 overflow-y-auto bg-muted/10 p-4 lg:p-6",
          className
        )}>
          <div className="mx-auto max-w-7xl">
            {children}
          </div>
        </main>
      </div>
    </div>
  )
}

// Page wrapper component for consistent page styling
interface PageWrapperProps {
  children: React.ReactNode
  title?: string
  description?: string
  actions?: React.ReactNode
  className?: string
}

export function PageWrapper({ 
  children, 
  title, 
  description, 
  actions,
  className 
}: PageWrapperProps) {
  return (
    <div className={cn("space-y-6", className)}>
      {(title || description || actions) && (
        <div className="flex flex-col space-y-2 sm:flex-row sm:items-center sm:justify-between sm:space-y-0">
          <div>
            {title && (
              <h1 className="text-2xl font-bold tracking-tight lg:text-3xl">
                {title}
              </h1>
            )}
            {description && (
              <p className="text-muted-foreground">
                {description}
              </p>
            )}
          </div>
          {actions && (
            <div className="flex items-center space-x-2">
              {actions}
            </div>
          )}
        </div>
      )}
      {children}
    </div>
  )
}

// Loading component for pages
export function PageLoading() {
  return (
    <div className="flex h-64 items-center justify-center">
      <div className="flex items-center space-x-2">
        <div className="h-4 w-4 animate-spin rounded-full border-2 border-primary border-t-transparent" />
        <span className="text-muted-foreground">Loading...</span>
      </div>
    </div>
  )
}

// Error component for pages
interface PageErrorProps {
  title?: string
  description?: string
  action?: React.ReactNode
}

export function PageError({ 
  title = "Something went wrong", 
  description = "We encountered an error while loading this page.",
  action
}: PageErrorProps) {
  return (
    <div className="flex h-64 flex-col items-center justify-center space-y-4">
      <div className="text-center">
        <h2 className="text-lg font-semibold">{title}</h2>
        <p className="text-muted-foreground">{description}</p>
      </div>
      {action && action}
    </div>
  )
}

// Empty state component
interface EmptyStateProps {
  icon?: React.ComponentType<{ className?: string }>
  title: string
  description?: string
  action?: React.ReactNode
}

export function EmptyState({ 
  icon: Icon, 
  title, 
  description, 
  action 
}: EmptyStateProps) {
  return (
    <div className="flex h-64 flex-col items-center justify-center space-y-4 text-center">
      {Icon && (
        <div className="rounded-full bg-muted p-4">
          <Icon className="h-8 w-8 text-muted-foreground" />
        </div>
      )}
      <div className="space-y-2">
        <h3 className="text-lg font-semibold">{title}</h3>
        {description && (
          <p className="text-sm text-muted-foreground max-w-md">
            {description}
          </p>
        )}
      </div>
      {action && action}
    </div>
  )
}