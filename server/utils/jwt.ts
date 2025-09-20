import { jwtVerify, SignJWT } from 'jose'

export async function createJwt(payload: Record<string, any>, expiresIn: string = '1d') {
  const runtimeConfig = useRuntimeConfig()
  const secret = new TextEncoder().encode(runtimeConfig.authSecret)

  return await new SignJWT(payload)
    .setProtectedHeader({ alg: 'HS256' })
    .setIssuedAt()
    .setExpirationTime(expiresIn)
    .sign(secret)
}

export async function verifyJwt(token: string) {
  const runtimeConfig = useRuntimeConfig()
  const secret = new TextEncoder().encode(runtimeConfig.authSecret)

  try {
    const { payload } = await jwtVerify(token, secret)
    return payload
  }
  catch {
    return null
  }
}
