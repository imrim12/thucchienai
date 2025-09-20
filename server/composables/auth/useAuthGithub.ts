import { randomBytes } from 'node:crypto'
import { withQuery } from 'ufo'

export function useAuthGithub() {
  const event = useEvent()

  function getGithubSigninUrl() {
    const runtimeConfig = useRuntimeConfig(event)

    const redirectUri = `${runtimeConfig.apiUrl}${runtimeConfig.githubRedirectUri}`
    const clientId = runtimeConfig.githubClientId || ''
    const scope = 'user:email'
    const state = randomBytes(32).toString('hex') // generate secure random state

    return withQuery('https://github.com/login/oauth/authorize', {
      client_id: clientId,
      redirect_uri: encodeURIComponent(redirectUri),
      scope: encodeURIComponent(scope),
      state,
    })
  }

  async function exchangeCodeForToken(code: string) {
    const runtimeConfig = useRuntimeConfig(event)
    const clientId = runtimeConfig.githubClientId
    const clientSecret = runtimeConfig.githubClientSecret

    const response = await $fetch<{
      access_token: string
      scope: string
      token_type: string
    }>('https://github.com/login/oauth/access_token', {
      method: 'POST',
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: new URLSearchParams({
        client_id: clientId,
        client_secret: clientSecret,
        code,
      }).toString(),
    })

    return response
  }

  async function getUserInfo(accessToken: string) {
    const user = await $fetch<{
      id: number
      login: string
      name: string
      email: string
      avatar_url: string
      bio: string
    }>('https://api.github.com/user', {
      headers: {
        'Authorization': `Bearer ${accessToken}`,
        'User-Agent': 'DirectusHostingAPI',
      },
    })

    // GitHub API might not return email in the user object if it's private
    // Fetch primary email separately
    if (!user.email) {
      const emails = await $fetch<Array<{
        email: string
        primary: boolean
        verified: boolean
        visibility: string
      }>>('https://api.github.com/user/emails', {
        headers: {
          'Authorization': `Bearer ${accessToken}`,
          'User-Agent': 'DirectusHostingAPI',
        },
      })

      const primaryEmail = emails.find(email => email.primary && email.verified)
      if (primaryEmail) {
        user.email = primaryEmail.email
      }
    }

    return user
  }

  return {
    getGithubSigninUrl,
    exchangeCodeForToken,
    getUserInfo,
  }
}
