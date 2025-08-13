import { render, screen } from '@testing-library/react'
import { PipelineLogsPanel } from '@/components/pipelines/PipelineLogsPanel'

jest.mock('@/hooks/use-pipelines', () => ({
  useLogsTail: () => ({
    events: [{ timestamp: new Date().toISOString(), level: 'INFO', message: 'Test log' }],
    isConnected: true,
    error: null,
    clear: () => {},
  }),
}))

test('renders logs', () => {
  render(<PipelineLogsPanel pipelineId="123" />)
  expect(screen.getByText(/Test log/)).toBeInTheDocument()
})
