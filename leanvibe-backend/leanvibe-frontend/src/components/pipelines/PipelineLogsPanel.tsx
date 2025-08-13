"use client"

import * as React from 'react'
import { useLogsTail, type TailLogEvent } from '@/hooks/use-pipelines'

export function PipelineLogsPanel({ pipelineId }: { pipelineId: string }) {
  const [level, setLevel] = React.useState<string | undefined>()
  const [stage, setStage] = React.useState<string | undefined>()
  const [search, setSearch] = React.useState('')
  const { events, isConnected, error, clear } = useLogsTail(pipelineId, {
    level,
    stage,
    search,
  })

  const containerRef = React.useRef<HTMLDivElement | null>(null)
  React.useEffect(() => {
    const el = containerRef.current
    if (!el) return
    el.scrollTop = el.scrollHeight
  }, [events.length])

  const filtered = React.useMemo(() => {
    return events
  }, [events])

  return (
    <div className="mt-2">
      <div className="mb-2 flex items-center gap-2 text-xs">
        <select
          className="rounded border px-2 py-1"
          value={level || ''}
          onChange={(e) => setLevel(e.target.value || undefined)}
        >
          <option value="">Level</option>
          <option value="INFO">INFO</option>
          <option value="WARNING">WARNING</option>
          <option value="ERROR">ERROR</option>
        </select>
        <input
          className="flex-1 rounded border px-2 py-1"
          placeholder="Search message…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        {/* optional stage filter input for now */}
        <input
          className="w-40 rounded border px-2 py-1"
          placeholder="Stage (e.g. backend_development)"
          value={stage || ''}
          onChange={(e) => setStage(e.target.value || undefined)}
        />
        <button className="rounded border px-2 py-1" onClick={() => clear()}>Clear</button>
        <span className="text-muted-foreground">
          {isConnected ? 'live' : 'disconnected'}{error ? ` – ${error}` : ''}
        </span>
      </div>
      <div ref={containerRef} className="max-h-64 overflow-auto rounded bg-muted/30 p-2 text-xs">
        {filtered.length === 0 && (
          <div className="text-muted-foreground">No logs yet.</div>
        )}
        {filtered.map((log: TailLogEvent, idx: number) => (
          <div key={idx} className="grid grid-cols-[auto_1fr] gap-2 whitespace-pre-wrap">
            <span className="text-muted-foreground">[{log.timestamp ? new Date(log.timestamp).toLocaleTimeString() : ''}]</span>
            <span>
              <span className="font-medium">{log.level}</span> {log.message}
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}
