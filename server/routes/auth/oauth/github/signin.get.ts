defineRouteMeta({
  openAPI: {
    tags: ['OAuth'],
    summary: 'GitHub OAuth Sign In',
    description: 'Redirect to GitHub OAuth authorization page',
    responses: {
      302: {
        description: 'Redirect to GitHub OAuth',
        headers: {
          Location: {
            schema: { type: 'string', format: 'uri' },
            description: 'GitHub OAuth authorization URL',
          },
        },
      },
    },
  },
})

export default defineEventHandler((event) => {
  const { getGithubSigninUrl } = useAuthGithub()

  return sendRedirect(event, getGithubSigninUrl(), 302)
})
