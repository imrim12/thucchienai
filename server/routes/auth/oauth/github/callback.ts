import { withQuery } from 'ufo'

defineRouteMeta({
  openAPI: {
    tags: ['OAuth'],
    summary: 'GitHub OAuth Callback',
    description: 'Handle GitHub OAuth callback and create user session',
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
    const { exchangeCodeForToken, getUserInfo } = useAuthGithub()
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

    // Exchange authorization code for access token
    const tokenResponse = await exchangeCodeForToken(code)

    if (!tokenResponse.access_token) {
      throw createError({
        statusCode: 500,
        statusMessage: 'Failed to obtain access token',
      })
    }

    // Get user information from GitHub
    const userInfo = await getUserInfo(tokenResponse.access_token)

    if (!userInfo.email) {
      throw createError({
        statusCode: 400,
        statusMessage: 'GitHub account must have a public email address',
      })
    }

    // Find or create user in database
    const user = await findOrCreateUser(
      userInfo.email,
      userInfo.name || userInfo.login,
      userInfo.avatar_url,
      'github',
      userInfo.id.toString(),
      {
        accessToken: tokenResponse.access_token,
        scopes: tokenResponse.scope ? tokenResponse.scope.split(' ') : ['user:email'],
      },
    )

    // Create session with user data
    await createSession(event, user, 'github', {
      accessToken: tokenResponse.access_token,
    })

    // Redirect to frontend dashboard
    const appUrl = runtimeConfig.appUrl || 'http://localhost:5173'
    return sendRedirect(event, appUrl, 302)
  }
  catch (error) {
    console.error('GitHub OAuth callback error:', error)

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
