import type { Arrayable } from 'type-fest'
import nodemailer from 'nodemailer'

export function useEmail() {
  const runtimeConfig = useRuntimeConfig()

  const sender = nodemailer.createTransport({
    host: runtimeConfig.smtpHost,
    port: Number(runtimeConfig.smtpPort),
    secure: Boolean(runtimeConfig.smtpSecure),
    auth: runtimeConfig.smtpUser && runtimeConfig.smtpPassword
      ? {
          user: runtimeConfig.smtpUser,
          pass: runtimeConfig.smtpPassword,
        }
      : undefined,
  })

  function sendMail(subject: string, html: string, to: Arrayable<string>) {
    if (Array.isArray(to)) {
      return sender.sendMail({
        from: runtimeConfig.smtpFrom,
        to: runtimeConfig.smtpPlaceholder,
        bcc: to,
        subject,
        html,
      })
    }

    return sender.sendMail({
      from: runtimeConfig.smtpFrom,
      to,
      subject,
      html,
    })
  }

  return { sendMail }
}
