import { withQuery } from 'ufo'

defineRouteMeta({
  openAPI: {
    tags: ['OAuth'],
    summary: 'Google OAuth Callback',
    description: 'Handle Google OAuth callback and create user session',
    parameters: [
      {
        name: 'code',
        in: 'query',
        required: false,
        schema: { type: 'string' },
        description: 'OAuth authorization code',
      },
      {
        name: 'error',
        in: 'query',
        required: false,
        schema: { type: 'string' },
        description: 'OAuth error code',
      },
    ],
    responses: {
      302: {
        description: 'Redirect to application',
        headers: {
          Location: {
            schema: { type: 'string', format: 'uri' },
            description: 'Application URL with success or error parameters',
          },
        },
      },
    },
  },
})

export default defineEventHandler(async (event) => {
  try {
    const runtimeConfig = useRuntimeConfig(event)
    const { exchangeCodeForTokens, getUserInfo } = useAuthGoogle()
    const { findOrCreateUser, createSession } = useAuth()

    const { code, error } = getQuery(event)

    // Handle OAuth errors
    if (error) {
      console.error('OAuth error:', error)
      const appUrl = runtimeConfig.appUrl || 'http://localhost:5173'
      return sendRedirect(
        event,
        withQuery(appUrl, { error: 'oauth_error' }),
        302,
      )
    }

    // Validate required parameters
    if (!code || typeof code !== 'string') {
      const appUrl = runtimeConfig.appUrl || 'http://localhost:5173'
      return sendRedirect(
        event,
        withQuery(appUrl, { error: 'missing_code' }),
        302,
      )
    }

    // Exchange authorization code for tokens
    const tokens = await exchangeCodeForTokens(code)

    if (!tokens.access_token) {
      throw createError({
        statusCode: 500,
        statusMessage: 'Failed to obtain access token',
      })
    }

    // Get user information from Google
    const userInfo = await getUserInfo(tokens.access_token)

    if (!userInfo.email || !userInfo.verified_email) {
      throw createError({
        statusCode: 400,
        statusMessage: 'Google account must have a verified email address',
      })
    }

    // Find or create user in database
    const user = await findOrCreateUser(
      userInfo.email,
      userInfo.name,
      userInfo.picture,
      'google',
      userInfo.id,
      {
        accessToken: tokens.access_token || undefined,
        refreshToken: tokens.refresh_token || undefined,
        expiresAt: tokens.expiry_date ? new Date(tokens.expiry_date) : undefined,
        scopes: tokens.scope ? tokens.scope.split(' ') : ['openid', 'email', 'profile'],
      },
    )

    // Create session with user data
    await createSession(event, user, 'google', {
      accessToken: tokens.access_token,
      refreshToken: tokens.refresh_token || undefined,
    })

    // Redirect to frontend dashboard
    const appUrl = runtimeConfig.appUrl || 'http://localhost:5173'
    return sendRedirect(event, appUrl, 302)
  }
  catch (error) {
    console.error('Google OAuth callback error:', error)

    // Redirect to frontend with error
    const runtimeConfig = useRuntimeConfig(event)
    const appUrl = runtimeConfig.appUrl || 'http://localhost:5173'
    return sendRedirect(
      event,
      withQuery(appUrl, { error: 'authentication_failed' }),
      302,
    )
  }
})
