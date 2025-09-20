export default defineEventHandler((event) => {
  const runtimeConfig = useRuntimeConfig()

  handleCors(event, {
    credentials: true,
    origin: [
      runtimeConfig.appUrl || '*',
    ],
    preflight: {
      statusCode: 204,
    },
  })
})
