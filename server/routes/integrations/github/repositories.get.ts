import { errorResponseJsonSchema, githubRepositoriesResponseJsonSchema } from '@/utils/schema'

defineRouteMeta({
  openAPI: {
    tags: ['Integrations'],
    summary: 'Get GitHub Repositories',
    description: 'Fetch user\'s private GitHub repositories using stored OAuth token',
    security: [{ cookieAuth: [] }],
    responses: {
      200: {
        description: 'Successfully retrieved repositories',
        content: {
          'application/json': {
            schema: githubRepositoriesResponseJsonSchema,
            example: {
              success: true,
              repositories: [
                {
                  id: 123456,
                  name: 'my-repo',
                  fullName: 'username/my-repo',
                  isPrivate: true,
                  description: 'My private repository',
                  url: 'https://github.com/username/my-repo',
                  lastUpdated: '2023-01-01T12:00:00Z',
                },
              ],
              scopes: ['user:email', 'repo'],
            },
          },
        },
      },
      400: {
        description: 'GitHub integration not found',
        content: {
          'application/json': {
            schema: errorResponseJsonSchema,
            example: {
              statusCode: 400,
              statusMessage: 'GitHub integration not found - Please connect your GitHub account',
            },
          },
        },
      },
      401: {
        description: 'Unauthorized - no valid session',
        content: {
          'application/json': {
            schema: errorResponseJsonSchema,
            example: {
              statusCode: 401,
              statusMessage: 'Unauthorized - No valid session found',
            },
          },
        },
      },
      500: {
        description: 'Internal server error or GitHub API error',
        content: {
          'application/json': {
            schema: errorResponseJsonSchema,
          },
        },
      },
    },
  },
})

export default defineEventHandler(async (event) => {
  try {
    const { getSession, getOAuthTokens } = useAuth()

    // Get current user session
    const session = await getSession(event)

    if (!session) {
      throw createError({
        statusCode: 401,
        statusMessage: 'Unauthorized - No valid session found',
      })
    }

    // Get GitHub OAuth tokens for the user
    const githubTokens = await getOAuthTokens(session.userId, 'github')

    if (!githubTokens?.accessToken) {
      throw createError({
        statusCode: 400,
        statusMessage: 'GitHub integration not found - Please connect your GitHub account',
      })
    }

    // Use the stored access token to fetch user's repositories
    const repositories = await $fetch<Array<{
      id: number
      name: string
      full_name: string
      private: boolean
      description: string | null
      html_url: string
      updated_at: string
    }>>('https://api.github.com/user/repos', {
      headers: {
        'Authorization': `Bearer ${githubTokens.accessToken}`,
        'User-Agent': 'DirectusHostingAPI',
      },
      query: {
        visibility: 'private', // Focus on private repos for integration
        sort: 'updated',
        per_page: 10,
      },
    })

    return {
      success: true,
      repositories: repositories.map(repo => ({
        id: repo.id,
        name: repo.name,
        fullName: repo.full_name,
        isPrivate: repo.private,
        description: repo.description,
        url: repo.html_url,
        lastUpdated: repo.updated_at,
      })),
      scopes: githubTokens.scopes,
    }
  }
  catch (error: any) {
    console.error('GitHub integration error:', error)

    if (error.statusCode) {
      throw error
    }

    // Handle GitHub API errors
    if (error.data?.message) {
      throw createError({
        statusCode: error.status || 500,
        statusMessage: `GitHub API Error: ${error.data.message}`,
      })
    }

    throw createError({
      statusCode: 500,
      statusMessage: 'Failed to fetch GitHub repositories',
    })
  }
})
