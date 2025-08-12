import '@testing-library/jest-dom'

// Polyfill fetch for tests if not present
if (typeof global.fetch === 'undefined') {
  // eslint-disable-next-line @typescript-eslint/no-var-requires
  const { Response, Request, Headers, fetch } = require('whatwg-fetch')
  // @ts-expect-error attaching to global
  global.fetch = fetch
  // @ts-expect-error attaching to global
  global.Response = Response
  // @ts-expect-error attaching to global
  global.Request = Request
  // @ts-expect-error attaching to global
  global.Headers = Headers
}

// Mock next/navigation where needed by components using app router
jest.mock('next/navigation', () => {
  return {
    useRouter: () => ({ push: jest.fn(), replace: jest.fn(), back: jest.fn() }),
    useSearchParams: () => new URLSearchParams(),
  }
})
