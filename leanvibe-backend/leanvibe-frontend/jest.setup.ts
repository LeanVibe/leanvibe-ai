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
;(global as any).jest = (global as any).jest || require('jest-mock')
;(global as any).jest.mock('next/navigation', () => {
  const j = (global as any).jest
  return {
    useRouter: () => ({ push: j.fn(), replace: j.fn(), back: j.fn() }),
    useSearchParams: () => new URLSearchParams(),
  }
})
