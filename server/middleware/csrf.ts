import micromatch from 'micromatch'
import { importEncryptSecret, verify } from 'uncsrf'
import {
  CSRF_ALLOWED_METHODS,
  CSRF_ALLOWED_PATHS,
  CSRF_COOKIE_NAME,
  CSRF_HEADER_NAME,
} from '@/constants/csrf'

export default defineEventHandler(async (event) => {
  const runtimeConfig = useRuntimeConfig(event)
  const secret = runtimeConfig.csrfSecret

  if (!secret) {
    console.warn('CSRF secret not configured; skipping CSRF validation')
    return
  }

  const method = event.method.toUpperCase()
  if (CSRF_ALLOWED_METHODS.includes(method)) {
    return
  }

  const url = getRequestURL(event)
  if (micromatch.isMatch(url.pathname, CSRF_ALLOWED_PATHS)) {
    return
  }

  // Get token from header first, then fall back to cookie
  let token = getHeader(event, CSRF_HEADER_NAME)

  if (!token) {
    token = getCookie(event, CSRF_COOKIE_NAME)
  }

  if (!token) {
    throw createError({
      statusCode: 403,
      statusMessage: 'CSRF token missing',
    })
  }

  try {
    const importedSecret = await importEncryptSecret(secret)

    // Verify the token with the secret
    verify(secret, token, importedSecret)
  }
  catch {
    throw createError({
      statusCode: 403,
      statusMessage: 'Invalid CSRF token',
    })
  }
})
