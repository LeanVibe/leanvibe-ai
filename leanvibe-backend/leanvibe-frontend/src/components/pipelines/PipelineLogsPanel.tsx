"use client"

import * as React from 'react'
import { usePipelineLogs } from '@/hooks/use-pipelines'

export function PipelineLogsPanel({ pipelineId }: { pipelineId: string }) {
  const { data, isLoading } = usePipelineLogs(pipelineId, true)
  const logs = (data as any)?.data ?? []
  return (
    <div className="mt-2 max-h-64 overflow-auto rounded bg-muted/30 p-2 text-xs">
      {isLoading && <div className="text-muted-foreground">Loading logs…</div>}
      {!isLoading && logs.length === 0 && (
        <div className="text-muted-foreground">No logs yet.</div>
      )}
      {logs.map((log: any, idx: number) => (
        <div key={idx} className="grid grid-cols-[auto_1fr] gap-2 whitespace-pre-wrap">
          <span className="text-muted-foreground">[{new Date(log.timestamp).toLocaleTimeString()}]</span>
          <span>
            <span className="font-medium">{log.level}</span> {log.message}
          </span>
        </div>
      ))}
    </div>
  )
}
