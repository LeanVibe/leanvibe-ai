import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Button } from '@/components/ui/button'

describe('Button', () => {
  it('renders children', () => {
    render(<Button>Click me</Button>)
    expect(screen.getByRole('button', { name: /click me/i })).toBeInTheDocument()
  })

  it('disables when loading', async () => {
    render(<Button loading>Submit</Button>)
    const btn = screen.getByRole('button', { name: /loading/i })
    expect(btn).toBeDisabled()
  })

  it('supports variants and sizes via class names', () => {
    const { rerender } = render(<Button variant="destructive">X</Button>)
    expect(screen.getByRole('button')).toHaveClass('bg-destructive')
    rerender(<Button size="xl">X</Button>)
    expect(screen.getByRole('button')).toHaveClass('h-12')
  })

  it('respects disabled prop and prevents clicks', async () => {
    const onClick = jest.fn()
    const user = userEvent.setup()
    render(
      <Button disabled onClick={onClick}>
        Submit
      </Button>
    )
    const btn = screen.getByRole('button', { name: /submit/i })
    expect(btn).toBeDisabled()
    await user.click(btn)
    expect(onClick).not.toHaveBeenCalled()
  })
})
