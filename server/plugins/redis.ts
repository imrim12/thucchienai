import redisDriver from 'unstorage/drivers/redis'
import upstashDriver from 'unstorage/drivers/upstash'

export default defineNitroPlugin(() => {
  const storage = useStorage()
  const runtimeConfig = useRuntimeConfig()

  if (runtimeConfig.upstashRedisRestUrl && runtimeConfig.upstashRedisRestToken) {
    const driver = upstashDriver({
      base: 'redis',
      url: runtimeConfig.upstashRedisRestUrl,
      token: runtimeConfig.upstashRedisRestToken,
      agent: {
        keepAlive: false,
      },
    })

    storage.mount('redis', driver)
  }
  else if (runtimeConfig.redisUrl) {
    const driver = redisDriver({
      base: 'redis',
      url: runtimeConfig.redisUrl,
      maxRetriesPerRequest: 20,
      // tls: {
      //   rejectUnauthorized: false, // Upstash uses valid certificates, but this helps with some connection issues
      // },
    })

    storage.mount('redis', driver)
  }
})
