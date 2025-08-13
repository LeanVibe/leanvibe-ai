'use client'

import * as React from 'react'
import { DashboardLayout, PageWrapper, EmptyState } from '@/components/layout/dashboard-layout'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Progress } from '@/components/ui/progress'
import { Badge, StatusBadge } from '@/components/ui/badge'
import { 
  Workflow, 
  FolderOpen, 
  TrendingUp, 
  Clock, 
  Users, 
  Activity,
  Plus,
  ArrowRight,
  BarChart3,
  CheckCircle,
  AlertCircle
} from 'lucide-react'
import { AuthGuard } from '@/components/auth/auth-guard'
import { usePipelines, usePausePipeline, useResumePipeline } from '@/hooks/use-pipelines'
import { formatDate, formatDuration } from '@/lib/utils'
import Link from 'next/link'
import { PipelineLogsPanel } from '@/components/pipelines/PipelineLogsPanel'

// Mock data for demonstration
const mockStats = {
  totalPipelines: 12,
  activePipelines: 3,
  completedProjects: 8,
  successRate: 92,
  avgCompletionTime: 2.5, // hours
  totalUsers: 5
}

const mockRecentPipelines = [
  {
    id: '1',
    project_name: 'E-commerce Platform',
    status: 'in_progress' as const,
    progress_percentage: 75,
    current_step: 'Implementing payment system',
    created_at: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
    estimated_completion: new Date(Date.now() + 30 * 60 * 1000).toISOString()
  },
  {
    id: '2',
    project_name: 'Task Management App',
    status: 'completed' as const,
    progress_percentage: 100,
    current_step: 'Deployment complete',
    created_at: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
    estimated_completion: new Date(Date.now() - 1 * 60 * 60 * 1000).toISOString()
  },
  {
    id: '3',
    project_name: 'Social Media Dashboard',
    status: 'queued' as const,
    progress_percentage: 0,
    current_step: 'Waiting to start',
    created_at: new Date(Date.now() - 10 * 60 * 1000).toISOString(),
    estimated_completion: new Date(Date.now() + 4 * 60 * 60 * 1000).toISOString()
  }
]

function DashboardStats() {
  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Total Pipelines</CardTitle>
          <Workflow className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{mockStats.totalPipelines}</div>
          <p className="text-xs text-muted-foreground">
            {mockStats.activePipelines} currently active
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Completed Projects</CardTitle>
          <FolderOpen className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{mockStats.completedProjects}</div>
          <p className="text-xs text-muted-foreground">
            {mockStats.successRate}% success rate
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Avg. Completion</CardTitle>
          <Clock className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{mockStats.avgCompletionTime}h</div>
          <p className="text-xs text-muted-foreground">
            Average time to MVP
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Team Members</CardTitle>
          <Users className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{mockStats.totalUsers}</div>
          <p className="text-xs text-muted-foreground">
            Active this month
          </p>
        </CardContent>
      </Card>
    </div>
  )
}

function RecentPipelines() {
  const { data: pipelinesResp } = usePipelines()
  const pause = usePausePipeline()
  const resume = useResumePipeline()
  const pipelines = pipelinesResp?.data ?? []

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle>Recent Pipelines</CardTitle>
        <Link href="/pipelines">
          <Button variant="ghost" size="sm">
            View all
            <ArrowRight className="ml-2 h-4 w-4" />
          </Button>
        </Link>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {pipelines.map((pipeline) => (
            <div key={pipeline.id} className="rounded-lg border p-4">
              <div className="flex items-center justify-between space-x-4">
              <div className="flex-1 space-y-2">
                <div className="flex items-center justify-between">
                  <h3 className="font-medium">{pipeline.project_name}</h3>
                  <StatusBadge status={pipeline.status as any} />
                </div>
                <div className="space-y-1">
                  {pipeline.progress && (
                    <Progress 
                      value={pipeline.progress.overall_progress || 0} 
                      showValue 
                      size="sm" 
                    />
                  )}
                  <div className="text-xs text-muted-foreground">
                    Created {formatDate(new Date(pipeline.created_at))}
                  </div>
                </div>
              </div>
                <Link href={`/pipelines/${pipeline.id}`}>
                  <Button variant="ghost" size="sm">
                    View
                  </Button>
                </Link>
              </div>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  disabled={pause.isPending || (pipeline.status as any) !== 'generating'}
                  onClick={() => pause.mutate(pipeline.id)}
                >
                  Pause
                </Button>
                <Button
                  size="sm"
                  disabled={resume.isPending || (pipeline.status as any) !== 'paused'}
                  onClick={() => resume.mutate(pipeline.id)}
                >
                  Resume
                </Button>
              </div>
              <div className="mt-2 w-full">
                <PipelineLogsPanel pipelineId={pipeline.id} />
              </div>
            </div>
          ))}
        </div>
        
        {pipelines.length === 0 && (
          <EmptyState
            icon={Workflow}
            title="No pipelines yet"
            description="Create your first autonomous development pipeline to get started."
            action={
              <Link href="/pipelines/new">
                <Button>
                  <Plus className="mr-2 h-4 w-4" />
                  Create Pipeline
                </Button>
              </Link>
            }
          />
        )}
      </CardContent>
    </Card>
  )
}

function QuickActions() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Quick Actions</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid gap-3">
          <Link href="/pipelines/new">
            <Button className="w-full justify-start" size="lg">
              <Plus className="mr-2 h-4 w-4" />
              Create New Pipeline
            </Button>
          </Link>
          
          <Link href="/interviews/new">
            <Button variant="outline" className="w-full justify-start" size="lg">
              <Activity className="mr-2 h-4 w-4" />
              Start Founder Interview
            </Button>
          </Link>
          
          <Link href="/projects">
            <Button variant="outline" className="w-full justify-start" size="lg">
              <FolderOpen className="mr-2 h-4 w-4" />
              Browse Projects
            </Button>
          </Link>
          
          <Link href="/analytics">
            <Button variant="outline" className="w-full justify-start" size="lg">
              <BarChart3 className="mr-2 h-4 w-4" />
              View Analytics
            </Button>
          </Link>
        </div>
      </CardContent>
    </Card>
  )
}

function SystemStatus() {
  const systemHealth = [
    { name: 'API Service', status: 'healthy', uptime: '99.9%' },
    { name: 'AI Pipeline', status: 'healthy', uptime: '99.7%' },
    { name: 'Database', status: 'healthy', uptime: '100%' },
    { name: 'File Storage', status: 'warning', uptime: '98.5%' },
  ]

  return (
    <Card>
      <CardHeader>
        <CardTitle>System Status</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {systemHealth.map((service) => (
            <div key={service.name} className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                {service.status === 'healthy' ? (
                  <CheckCircle className="h-4 w-4 text-green-500" />
                ) : (
                  <AlertCircle className="h-4 w-4 text-yellow-500" />
                )}
                <span className="text-sm font-medium">{service.name}</span>
              </div>
              <div className="text-right">
                <div className="text-sm">{service.uptime}</div>
                <div className="text-xs text-muted-foreground">uptime</div>
              </div>
            </div>
          ))}
        </div>
        <div className="mt-4 pt-4 border-t">
          <div className="flex items-center justify-between text-sm">
            <span>Overall System Health</span>
            <Badge variant="success">Operational</Badge>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

export default function DashboardPage() {
  return (
    <AuthGuard>
      <DashboardLayout>
        <PageWrapper
          title="Dashboard"
          description="Overview of your autonomous development pipelines and projects"
          actions={
            <Link href="/pipelines/new">
              <Button>
                <Plus className="mr-2 h-4 w-4" />
                New Pipeline
              </Button>
            </Link>
          }
        >
          {/* Stats Overview */}
          <DashboardStats />

          {/* Main Content Grid */}
          <div className="grid gap-6 lg:grid-cols-3">
            {/* Recent Pipelines - Takes up 2 columns */}
            <div className="lg:col-span-2">
              <RecentPipelines />
            </div>

            {/* Sidebar Content */}
            <div className="space-y-6">
              <QuickActions />
              <SystemStatus />
            </div>
          </div>
        </PageWrapper>
      </DashboardLayout>
    </AuthGuard>
  )
}