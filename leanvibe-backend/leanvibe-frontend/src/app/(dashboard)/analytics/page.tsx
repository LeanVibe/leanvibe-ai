"use client"

import * as React from 'react'
import { DashboardLayout, PageWrapper } from '@/components/layout/dashboard-layout'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { AuthGuard } from '@/components/auth/auth-guard'

function Metric({ title, value, subtitle }: { title: string; value: string | number; subtitle?: string }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm text-muted-foreground">{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{value}</div>
        {subtitle && <div className="text-xs text-muted-foreground">{subtitle}</div>}
      </CardContent>
    </Card>
  )
}

export default function AnalyticsPage() {
  // Placeholder UI; can wire to /api/v1/analytics endpoints
  return (
    <AuthGuard>
      <DashboardLayout>
        <PageWrapper title="Analytics" description="Pipeline, tenant, and system analytics">
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <Metric title="Pipelines (30d)" value={42} subtitle="Success rate 96.5%" />
            <Metric title="Avg Completion (h)" value={4.2} subtitle="All projects" />
            <Metric title="Active Tenants" value={12} subtitle="System-wide" />
            <Metric title="Errors (24h)" value={3} subtitle="Critical: 0" />
          </div>

          <div className="mt-6 grid gap-6 lg:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>Pipeline Performance</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-sm text-muted-foreground">Coming soon: charts for success/failure rates and duration</div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Resource Utilization</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-sm text-muted-foreground">Coming soon: CPU, memory, storage usage charts</div>
              </CardContent>
            </Card>
          </div>
        </PageWrapper>
      </DashboardLayout>
    </AuthGuard>
  )
}
