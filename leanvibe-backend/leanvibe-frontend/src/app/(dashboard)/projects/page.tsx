'use client'

import * as React from 'react'
import Link from 'next/link'
import { useProjects } from '@/hooks/use-projects'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

export default function ProjectsPage() {
  const { data } = useProjects()
  const projects = (data as any)?.data ?? []

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold">Projects</h1>
      <div className="grid gap-4 md:grid-cols-2">
        {projects.map((p: any) => (
          <Card key={p.id}>
            <CardHeader>
              <CardTitle>{p.project_name}</CardTitle>
            </CardHeader>
            <CardContent className="flex items-center justify-between">
              <div className="text-sm text-muted-foreground">Status: {p.status}</div>
              <Link href={`/projects/${p.id}`}>
                <Button size="sm">Open</Button>
              </Link>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )
}
