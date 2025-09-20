/* eslint-disable no-console */
/**
 * @fileoverview This script generates a cryptographically secure random string
 * that can be used as an authentication secret for AES-256-GCM encryption.
 *
 * The authentication system uses AES-256-GCM, which requires a 256-bit (32-byte) key.
 * This script generates 32 random bytes and encodes them as a 64-character hex string
 * suitable for the NITRO_AUTH_SECRET environment variable.
 */

import crypto from 'node:crypto'

/**
 * The number of random bytes to generate for AES-256 encryption.
 * AES-256 requires a 32-byte (256-bit) key.
 */
const BYTES_TO_GENERATE = 32

/**
 * The expected length of the final hex-encoded secret string.
 * 32 bytes encoded as hex = 64 characters
 */
const SECRET_LENGTH_CHARS = 64

/**
 * Generates a cryptographically secure authentication secret.
 * @returns {string} A 64-character hex string representing 32 random bytes.
 */
function generateAuthSecret() {
  // Generate 32 cryptographically secure random bytes
  const buffer = crypto.randomBytes(BYTES_TO_GENERATE)

  // Encode as hex string (each byte becomes 2 hex characters)
  return buffer.toString('hex')
}

// --- Main Execution ---
try {
  const authSecret = generateAuthSecret()

  // Verify the generated secret has the correct length
  if (authSecret.length !== SECRET_LENGTH_CHARS) {
    throw new Error(
      `Failed to generate a secret of the correct length. Expected ${SECRET_LENGTH_CHARS}, but got ${authSecret.length}.`,
    )
  }

  console.log('✅ Auth Secret Generated Successfully!')
  console.log('------------------------------------')
  console.log(authSecret)
  console.log('------------------------------------')
  console.log(`\nLength: ${authSecret.length} characters (${BYTES_TO_GENERATE} bytes)`)
  console.log(`\n💡 Copy this 64-character hex value and set it as your NITRO_AUTH_SECRET environment variable.`)
  console.log(`   For example, in a .env file:\n`)
  console.log(`   NITRO_AUTH_SECRET="${authSecret}"`)
  console.log('\n')
}
catch (error) {
  console.error('❌ Failed to generate auth secret:')
  console.error(error)
  process.exit(1) // Exit with an error code
}
