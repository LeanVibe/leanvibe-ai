import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Input } from '@/components/ui/input'

describe('Input', () => {
  it('renders label and associates it with input', () => {
    render(<Input label="Email" placeholder="email@example.com" />)
    const input = screen.getByPlaceholderText(/email@example.com/i)
    const label = screen.getByText(/email/i)
    expect(label).toHaveAttribute('for', input.getAttribute('id'))
  })

  it('renders helper text', () => {
    render(<Input helper="We will never share your email" />)
    expect(screen.getByText(/never share/i)).toBeInTheDocument()
  })

  it('renders error text and red styles', () => {
    render(<Input error="Required" />)
    expect(screen.getByText(/required/i)).toBeInTheDocument()
  })

  it('accepts user typing', async () => {
    const user = userEvent.setup()
    render(<Input />)
    const input = screen.getByRole('textbox')
    await user.type(input, 'hello')
    expect(input).toHaveValue('hello')
  })
})
