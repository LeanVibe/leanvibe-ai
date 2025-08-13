'use client'

import * as React from 'react'
import Link from 'next/link'
import { useParams } from 'next/navigation'
import { useProject, useDirectoryEntries, downloadProjectFile, useDownloadArchive } from '@/hooks/use-projects'
import apiClient from '@/lib/api-client'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

export default function ProjectDetailPage() {
  const params = useParams<{ id: string }>()
  const id = params?.id as string
  const { data: projectResp } = useProject(id)
  const [path, setPath] = React.useState<string>('')
  const [sort, setSort] = React.useState<'name' | 'size' | 'modified'>('name')
  const { data: entries } = useDirectoryEntries(id, { path, sort })
  const downloadArchive = useDownloadArchive()
  const [preview, setPreview] = React.useState<{ url: string; type: string } | null>(null)

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
          <div className="mb-2 flex items-center gap-2 text-sm">
            <button className="underline" onClick={() => setPath('')}>root</button>
            {path && path.split('/').map((seg, idx, arr) => {
              const p = arr.slice(0, idx + 1).join('/')
              return (
                <span key={p} className="flex items-center gap-2">
                  <span>/</span>
                  <button className="underline" onClick={() => setPath(p)}>{seg}</button>
                </span>
              )
            })}
            <div className="ml-auto flex items-center gap-2">
              <label className="text-xs text-muted-foreground">Sort</label>
              <select className="rounded border px-2 py-1" value={sort} onChange={(e) => setSort(e.target.value as any)}>
                <option value="name">Name</option>
                <option value="size">Size</option>
                <option value="modified">Modified</option>
              </select>
            </div>
          </div>
          <div className="space-y-2">
            {(entries || []).map((f: any) => (
              <div key={f.path} className="flex items-center justify-between rounded border p-2">
                <div className="truncate">
                  <div className="text-sm font-medium">{f.name}</div>
                  <div className="text-xs text-muted-foreground">{f.path}</div>
                </div>
                <div className="flex gap-2">
                  {f.is_dir ? (
                    <Button size="sm" variant="ghost" onClick={() => setPath(f.path)}>Open</Button>
                  ) : (
                    <>
                      <Button size="sm" variant="ghost" onClick={async () => {
                        const res = await apiClient.previewProjectFile(id, f.path)
                        const url = URL.createObjectURL(res.blob)
                        setPreview({ url, type: res.contentType || 'text/plain' })
                      }}>Preview</Button>
                      <Button size="sm" variant="outline" onClick={() => downloadProjectFile(id, f.path)}>Download</Button>
                    </>
                  )}
                </div>
              </div>
            ))}
            {(!entries || entries.length === 0) && (
              <div className="text-sm text-muted-foreground">No files found.</div>
            )}
          </div>
        </CardContent>
      </Card>

      {preview && (
        <Card>
          <CardHeader>
            <CardTitle>Preview</CardTitle>
          </CardHeader>
          <CardContent>
            {preview.type.startsWith('image/') ? (
              <img src={preview.url} alt="preview" className="max-h-96" />
            ) : (
              <iframe src={preview.url} className="h-96 w-full rounded border" />
            )}
            <div className="mt-2">
              <Button size="sm" variant="ghost" onClick={() => { URL.revokeObjectURL(preview.url); setPreview(null) }}>Close</Button>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
