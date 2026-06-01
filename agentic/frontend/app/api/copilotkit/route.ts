import { NextRequest } from "next/server";
import { CopilotRuntime, copilotRuntimeNextJSAppRouterEndpoint } from "@copilotkit/runtime";
import { ErrorReporting } from "@google-cloud/error-reporting";

// Initialize Google Cloud Error Reporting
let errors: ErrorReporting | null = null;
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
    
    console.log(`[Frontend] Agent response status: ${response.status}`);
    
    return response;
  } catch (error: any) {
    console.error(`\n[Frontend] Error calling Agent:`, error);
    if (errors) {
      errors.report(error);
    }
    throw error;
  }
};
