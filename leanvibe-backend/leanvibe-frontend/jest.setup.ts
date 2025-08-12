import '@testing-library/jest-dom'

// Polyfill fetch for tests if not present
if (typeof (global as any).fetch === 'undefined') {
  // eslint-disable-next-line @typescript-eslint/no-var-requires
  const { Response, Request, Headers, fetch } = require('whatwg-fetch')
  ;(global as any).fetch = fetch
  ;(global as any).Response = Response
  ;(global as any).Request = Request
  ;(global as any).Headers = Headers
}

// Mock next/navigation where needed by components using app router
try {
  const { mock, fn } = require('jest-mock')
  ;(global as any).jest = { mock, fn }
  ;(global as any).jest.mock('next/navigation', () => {
    return {
      useRouter: () => ({ push: fn(), replace: fn(), back: fn() }),
      useSearchParams: () => new URLSearchParams(),
    }
  })
} catch (_) {
  // Ignore if jest-mock not available in this context
}
