defineRouteMeta({
  openAPI: {
    tags: ['OAuth'],
    summary: 'Google OAuth Sign In',
    description: 'Redirect to Google OAuth authorization page',
    responses: {
      302: {
        description: 'Redirect to Google OAuth',
        headers: {
          Location: {
            schema: { type: 'string', format: 'uri' },
            description: 'Google OAuth authorization URL',
          },
        },
      },
    },
  },
})

export default defineEventHandler((event) => {
  const { getGoogleSigninUrl } = useAuthGoogle()

  return sendRedirect(event, getGoogleSigninUrl(), 302)
})
