import { render, screen } from '@testing-library/react'
import { Progress } from '@/components/ui/progress'

describe('Progress', () => {
  it('renders with default value 0', () => {
    render(<Progress />)
    // The indicator translates based on value; ensure it exists
    expect(document.querySelector('[data-state]')).toBeInTheDocument()
  })

  it('shows value text when showValue is true', () => {
    render(<Progress value={42} showValue />)
    expect(screen.getByText('42%')).toBeInTheDocument()
  })
})
