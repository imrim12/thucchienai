import { template } from "es-toolkit/compat";
import { withQuery } from "ufo";
import { authSignUpSchema } from "@/schemas/auth/signup.schema";

import {
  authSignUpJsonSchema,
  errorResponseJsonSchema,
  successResponseJsonSchema,
} from "@/utils/schema";

defineRouteMeta({
  openAPI: {
    tags: ["Auth"],
    summary: "Sign Up",
    description: "Register a new user account and send email verification",
    security: [{ csrfToken: [] }],
    requestBody: {
      required: true,
      content: {
        "application/json": {
          schema: authSignUpJsonSchema,
          example: {
            name: "John Doe",
            email: "user@example.com",
            password: "password123",
          },
        },
      },
    },
    responses: {
      200: {
        description: "User registered successfully",
        content: {
          "application/json": {
            schema: successResponseJsonSchema,
            example: {
              message:
                "User registered successfully. Please check your email to verify your account.",
            },
          },
        },
      },
      400: {
        description: "Validation error or user already exists",
        content: {
          "application/json": {
            schema: errorResponseJsonSchema,
          },
        },
      },
      500: {
        description: "Internal server error",
        content: {
          "application/json": {
            schema: errorResponseJsonSchema,
          },
        },
      },
    },
  },
});

export default defineEventHandler(async (event) => {
  const runtimeConfig = useRuntimeConfig();
  const body = await readValidatedBody(event, authSignUpSchema.parse);

  const { registerUser, createVerificationToken } = useAuthCredentials();
  const { sendMail } = useEmail();

  try {
    // Register user
    const { email } = await registerUser(body.email, body.password, body.name);

    // Create verification token (1 hour expiry)
    const verificationToken = await createVerificationToken(
      email,
      "email-verification",
      1
    );

    // Send verification email
    const setPasswordEmailTemplate = await useStorage("assets:server").getItem(
      "templates/verify.ejs"
    );

    await sendMail(
      "Verify your email",
      template(setPasswordEmailTemplate.toString())({
        appName: "THECODEORIGIN",
        verificationLink: withQuery(`${runtimeConfig.appUrl}/auth/verify`, {
          code: verificationToken,
        }),
      }),
      email
    );

    return {
      message:
        "User registered successfully. Please check your email to verify your account.",
    };
  } catch (error: any) {
    if (error.statusCode) {
      throw error;
    }
    throw createError({
      statusCode: 500,
      statusMessage: "Registration failed",
    });
  }
});
