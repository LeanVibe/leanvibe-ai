import { render, screen } from '@testing-library/react'
import { PipelineLogsPanel } from '@/components/pipelines/PipelineLogsPanel'

jest.mock('@/hooks/use-pipelines', () => ({
  usePipelineLogs: () => ({ data: { data: [{ timestamp: new Date().toISOString(), level: 'INFO', message: 'Test log' }] }, isLoading: false })
}))

test('renders logs', () => {
  render(<PipelineLogsPanel pipelineId="123" />)
  expect(screen.getByText(/Test log/)).toBeInTheDocument()
})
