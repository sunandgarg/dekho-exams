export const STUDENT_INTEGRATIONS = {
  google: {
    name: "Google sign-in",
    note: "Register the website callback and separate iOS/Android clients in Google Cloud.",
    fields: [
      { key: "clientId", label: "Web client ID", secret: false },
      { key: "clientSecret", label: "Web client secret", secret: true },
    ],
    help: "https://developers.google.com/identity/protocols/oauth2/web-server",
  },
  sms: {
    name: "Mobile OTP · MSG91",
    note: "Your approved OTP template and Indian sender/DLT setup must be active. Apply daily spend and resend limits.",
    fields: [
      { key: "authKey", label: "Auth key", secret: true },
      { key: "templateId", label: "Approved OTP template ID", secret: false },
    ],
    help: "https://msg91.com/help/sendotp/step-by-step-process-to-configure-otp",
  },
  razorpay: {
    name: "Razorpay",
    note: "Connect test keys first. Live keys need an activated merchant account and a signed webhook endpoint.",
    fields: [
      { key: "keyId", label: "Key ID", secret: false },
      { key: "keySecret", label: "Key secret", secret: true },
      { key: "webhookSecret", label: "Webhook signing secret", secret: true },
    ],
    help: "https://razorpay.com/docs/payments/payment-gateway/web-integration/standard/integration-steps/",
  },
  ses: {
    name: "Amazon SES",
    note: "Verify the sender domain, request production access and connect a sender-only IAM identity. Email delivery is queued.",
    fields: [
      { key: "region", label: "AWS region", secret: false },
      { key: "fromEmail", label: "Verified sender email", secret: false },
      { key: "accessKeyId", label: "Sender-only access key ID", secret: false },
      { key: "secretAccessKey", label: "Sender-only secret access key", secret: true },
    ],
    help: "https://docs.aws.amazon.com/ses/latest/dg/request-production-access.html",
  },
} as const;
export type IntegrationName = keyof typeof STUDENT_INTEGRATIONS;
