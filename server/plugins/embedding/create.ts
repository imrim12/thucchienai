export default defineNitroPlugin(() => {
  const nitroApp = useNitroApp()
  const runtimeConfig = useRuntimeConfig()

  nitroApp.hooks.hook('embedding:create', () => {
    //
  })
})
