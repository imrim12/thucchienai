import { randomBytes } from 'node:crypto'
import { OAuth2Client } from 'google-auth-library'
import { withQuery } from 'ufo'

export function useAuthGoogle() {
  const event = useEvent()

  function getGoogleSigninUrl() {
    const runtimeConfig = useRuntimeConfig(event)

    const redirectUri = `${runtimeConfig.apiUrl}${runtimeConfig.googleRedirectUri}`
    const clientId = runtimeConfig.googleClientId || ''
    const scope = 'openid email profile'
    const state = randomBytes(32).toString('hex') // generate secure random state

    return withQuery('https://accounts.google.com/o/oauth2/v2/auth', {
      response_type: 'code',
      client_id: clientId,
      redirect_uri: redirectUri,
      scope,
      state,
    })
  }

  async function exchangeCodeForTokens(code: string) {
    const runtimeConfig = useRuntimeConfig(event)
    const clientId = runtimeConfig.googleClientId
    const clientSecret = runtimeConfig.googleClientSecret
    const redirectUri = `${runtimeConfig.apiUrl}${runtimeConfig.googleRedirectUri}`

    const oauth2Client = new OAuth2Client(clientId, clientSecret, redirectUri)

    const { tokens } = await oauth2Client.getToken(code)
    return tokens
  }

  async function getUserInfo(accessToken: string) {
    const response = await $fetch<{
      id: string
      email: string
      verified_email: boolean
      name: string
      given_name: string
      family_name: string
      picture: string
      locale: string
    }>('https://www.googleapis.com/oauth2/v2/userinfo', {
      headers: {
        Authorization: `Bearer ${accessToken}`,
      },
    })

    return response
  }

  return {
    getGoogleSigninUrl,
    exchangeCodeForTokens,
    getUserInfo,
  }
}
