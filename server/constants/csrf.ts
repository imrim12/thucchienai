export const CSRF_COOKIE_NAME = 'csrf-token'

export const CSRF_HEADER_NAME = 'x-csrf-token'

export const CSRF_ALLOWED_PATHS = [
  '/auth/csrf',
  '/auth/verify',
  '/auth/signout',
  '/_scalar',
  '/_swagger',
  '/_openapi.json',
]

export const CSRF_ALLOWED_METHODS = [
  'HEAD',
  'OPTIONS',
]
