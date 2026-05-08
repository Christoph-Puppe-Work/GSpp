import { NextRequest } from "next/server";
import { CopilotRuntime, copilotRuntimeNextJSAppRouterEndpoint } from "@copilotkit/runtime";
const { ErrorReporting } = require("@google-cloud/error-reporting");

// Initialize Google Cloud Error Reporting
let errors: any = null;
try {
  errors = new ErrorReporting();
  console.log("[Frontend] Google Cloud Error Reporting initialized.");
} catch (e) {
  console.warn("[Frontend] Could not initialize Error Reporting:", e);
}

// Fetches a Google Cloud identity token for Cloud Run-to-Cloud Run authentication.
// Returns null when running locally (no metadata server available).
async function getGcpIdentityToken(audience: string): Promise<string | null> {
  try {
    const metadataUrl =
      `http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/identity` +
      `?audience=${encodeURIComponent(audience)}`;
    const res = await fetch(metadataUrl, {
      headers: { "Metadata-Flavor": "Google" },
      signal: AbortSignal.timeout(1000),
      cache: "no-store",
    });
    if (res.ok) {
      return await res.text();
    }
  } catch (e) {
    // Not running on GCP (local dev) or metadata server unreachable
  }
  return null;
}

export const POST = async (req: NextRequest) => {
  const agentUrl = process.env.AGENT_URL || "http://127.0.0.1:8000/copilotkit";
  
  console.log(`\n=== COPILOTKIT CONNECTION ===`);
  console.log(`[Frontend] Target Agent URL: ${agentUrl}`);

  try {
    const reqClone = req.clone();
    const reqBody = await reqClone.json();
    console.log(`[Frontend] Request payload sent to agent:\n`, JSON.stringify(reqBody, null, 2));
  } catch (e) {
    console.log(`[Frontend] Request payload (unparseable):`, e);
  }

  // The Cloud Run identity token audience must be the service base URL (no path).
  const serviceBaseUrl = new URL(agentUrl).origin;
  const identityToken = await getGcpIdentityToken(serviceBaseUrl);

  if (identityToken) {
    console.log(`[Frontend] Using identity token for audience: ${serviceBaseUrl}`);
  } else {
    console.log(`[Frontend] No identity token available (Local Dev or Metadata server unreachable).`);
  }

  const { handleRequest } = copilotRuntimeNextJSAppRouterEndpoint({
    runtime: new CopilotRuntime({
      remoteEndpoints: [
        {
          url: agentUrl,
          ...(identityToken && {
            onBeforeRequest: (options: any) => {
              return {
                headers: { Authorization: `Bearer ${identityToken}` },
              };
            },
          }),
        },
      ],
    }),
    endpoint: "/api/copilotkit",
  });

  try {
    const response = await handleRequest(req);
    
    // Log the answer content
    // We clone the response so we don't consume the stream needed by the client
    const responseClone = response.clone();
    
    console.log(`[Frontend] Agent response status: ${response.status}`);
    console.log(`[Frontend] Agent response headers:`, JSON.stringify(Object.fromEntries(response.headers.entries()), null, 2));

    responseClone.text().then((text: string) => {
      console.log(`\n[Frontend] Agent Answer Content:\n${text}\n=============================\n`);
    }).catch((e: any) => {
      console.log(`\n[Frontend] Failed to read agent answer content:`, e);
    });

    return response;
  } catch (error: any) {
    console.error(`\n[Frontend] Error calling Agent:`, error);
    if (errors) {
      errors.report(error);
    }
    throw error;
  }
};
