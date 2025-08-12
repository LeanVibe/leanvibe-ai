import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "@/lib/utils"

const badgeVariants = cva(
  "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2",
  {
    variants: {
      variant: {
        default:
          "border-transparent bg-primary text-primary-foreground hover:bg-primary/80",
        secondary:
          "border-transparent bg-secondary text-secondary-foreground hover:bg-secondary/80",
        destructive:
          "border-transparent bg-destructive text-destructive-foreground hover:bg-destructive/80",
        outline: "text-foreground",
        success:
          "border-transparent bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-100",
        warning:
          "border-transparent bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-100",
        info:
          "border-transparent bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-100",
        purple:
          "border-transparent bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-100",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
)

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {
  pulse?: boolean
}

function Badge({ className, variant, pulse = false, ...props }: BadgeProps) {
  return (
    <div 
      className={cn(
        badgeVariants({ variant }), 
        pulse && "animate-pulse",
        className
      )} 
      {...props} 
    />
  )
}

// Status badge for pipelines
interface StatusBadgeProps {
  status: 'queued' | 'in_progress' | 'completed' | 'failed' | 'paused'
  className?: string
}

function StatusBadge({ status, className }: StatusBadgeProps) {
  const statusConfig = {
    queued: { variant: 'outline' as const, text: 'Queued', pulse: false },
    in_progress: { variant: 'info' as const, text: 'In Progress', pulse: true },
    completed: { variant: 'success' as const, text: 'Completed', pulse: false },
    failed: { variant: 'destructive' as const, text: 'Failed', pulse: false },
    paused: { variant: 'warning' as const, text: 'Paused', pulse: false },
  }

  const config = statusConfig[status] || statusConfig.queued

  return (
    <Badge 
      variant={config.variant} 
      pulse={config.pulse}
      className={className}
    >
      {config.text}
    </Badge>
  )
}

export { Badge, StatusBadge, badgeVariants }