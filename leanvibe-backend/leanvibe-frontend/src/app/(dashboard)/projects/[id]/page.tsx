'use client'

import * as React from 'react'
import Link from 'next/link'
import { useParams } from 'next/navigation'
import { useProject, useProjectFiles, downloadProjectFile, useDownloadArchive } from '@/hooks/use-projects'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

export default function ProjectDetailPage() {
  const params = useParams<{ id: string }>()
  const id = params?.id as string
  const { data: projectResp } = useProject(id)
  const { data: files } = useProjectFiles(id)
  const downloadArchive = useDownloadArchive()

  const project = (projectResp as any)?.data ?? projectResp

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">{project?.project_name || 'Project'}</h1>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => downloadArchive.mutate(id)}>Download Archive</Button>
          <Link href="/projects">
            <Button variant="ghost">Back</Button>
          </Link>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Files</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {(files || []).map((f: any) => (
              <div key={f.path} className="flex items-center justify-between rounded border p-2">
                <div className="truncate">
                  <div className="text-sm font-medium">{f.name}</div>
                  <div className="text-xs text-muted-foreground">{f.path}</div>
                </div>
                <div className="flex gap-2">
                  <Button size="sm" variant="outline" onClick={() => downloadProjectFile(id, f.path)}>Download</Button>
                </div>
              </div>
            ))}
            {(!files || files.length === 0) && (
              <div className="text-sm text-muted-foreground">No files found.</div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
