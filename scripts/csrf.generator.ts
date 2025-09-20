/* eslint-disable no-console */
/**
 * @fileoverview This script generates a cryptographically secure random string
 * that can be used as a secret for libraries like `uncsrf`.
 *
 * `uncsrf` uses AES-256-CBC, which requires a 256-bit (32-byte) key.
 * The library expects this key to be provided as a 32-character string.
 * This script generates the necessary bytes and encodes them using 'base64url'
 * to produce a URL-safe, 32-character string suitable for this purpose.
 */

import crypto from 'node:crypto'

/**
 * The desired length of the final secret string in characters.
 * `uncsrf` requires a 32-character string to derive its 32-byte key.
 */
const SECRET_LENGTH_CHARS = 32

/**
 * The number of random bytes to generate.
 * Base64 encoding represents 3 bytes of binary data as 4 characters.
 * To get the required number of bytes, we reverse this calculation.
 * (32 characters / 4) * 3 = 24 bytes
 */
const BYTES_TO_GENERATE = (SECRET_LENGTH_CHARS / 4) * 3

/**
 * Generates a cryptographically secure secret.
 * @returns {string} A 32-character URL-safe random string.
 */
function generateSecret() {
  // crypto.randomBytes generates a Buffer containing cryptographically secure random data.
  const buffer = crypto.randomBytes(BYTES_TO_GENERATE)

  // We encode the random bytes into a 'base64url' string. This is different
  // from standard base64 as it uses URL-safe characters ('-' and '_').
  // 24 bytes of random data reliably converts to a 32-character string without padding.
  return buffer.toString('base64url')
}

// --- Main Execution ---
try {
  const secret = generateSecret()

  // Verify the generated secret has the correct length.
  if (secret.length !== SECRET_LENGTH_CHARS) {
    throw new Error(
      `Failed to generate a secret of the correct length. Expected ${SECRET_LENGTH_CHARS}, but got ${secret.length}.`,
    )
  }

  console.log('✅ Secure Secret Generated Successfully!')
  console.log('------------------------------------')
  console.log(secret)
  console.log('------------------------------------')
  console.log(`\nLength: ${secret.length} characters`)
  console.log(`\n💡 Copy this 32-character value and set it as your CSRF_SECRET environment variable.`)
  console.log(`   For example, in a .env file:\n`)
  console.log(`   NITRO_CSRF_SECRET="${secret}"`)
  console.log('\n')
}
catch (error) {
  console.error('❌ Failed to generate secret:')
  console.error(error)
  process.exit(1) // Exit with an error code
}
