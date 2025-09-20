import { fileURLToPath } from 'node:url'
import { defineNitroConfig } from 'nitropack/config'

// https://nitro.build/config
export default defineNitroConfig({
  compatibilityDate: 'latest',

  srcDir: 'server',

  alias: {
    '@': fileURLToPath(new URL('./server', import.meta.url)),
  },

  // Works with prefixed with NITRO_
  // These are just for type generation
  runtimeConfig: {
    // This Nitro app URL
    apiUrl: '',
    // Frontend URL for redirects
    appUrl: '',

    // Encryption
    authSecret: '',

    // CSRF Secret
    csrfSecret: '',

    // Google OAuth
    googleClientId: '',
    googleClientSecret: '',
    googleRedirectUri: '',

    // GitHub OAuth
    githubClientId: '',
    githubClientSecret: '',
    githubRedirectUri: '',

    // Database configuration
    databaseUrl: '',

    // Redis configuration
    redisUrl: '',

    // Upstash Redis configuration
    upstashRedisRestUrl: '',
    upstashRedisRestToken: '',

    // SMTP credentials
    smtpHost: '',
    smtpPort: '',
    smtpUser: '',
    smtpPassword: '',
    smtpPlaceholder: '',
    smtpFrom: '',
  },

  experimental: {
    tasks: true,
    asyncContext: true,
    openAPI: true,
  },

  openAPI: {
    meta: {
      title: 'Directus Hosting API',
      description: 'API for Directus Hosting platform',
      version: '1.0.0',
    },
  },

  imports: {
    dirs: [
      './server/composables/**',
      './server/utils/**',
    ],
  },
})
