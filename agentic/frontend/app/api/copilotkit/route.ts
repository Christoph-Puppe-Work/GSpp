import { NextRequest } from "next/server";
import { CopilotRuntime, copilotRuntimeNextJSAppRouterEndpoint } from "@copilotkit/runtime";

// Fetches a Google Cloud identity token for Cloud Run-to-Cloud Run authentication.
// Returns null when running locally (no metadata server available).
async function getGcpIdentityToken(audience: string): Promise<string | null> {
  console.log(`[DEBUG] Attempting to fetch GCP Identity Token for audience: ${audience}`);
  try {
    const metadataUrl =
      `http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/identity` +
      `?audience=${encodeURIComponent(audience)}`;
    const res = await fetch(metadataUrl, {
      headers: { "Metadata-Flavor": "Google" },
      signal: AbortSignal.timeout(1000),
      cache: "no-store",
    });
    console.log(`[DEBUG] GCP Metadata fetch status: ${res.status} ${res.statusText}`);
    if (res.ok) {
      const token = await res.text();
      console.log(`[DEBUG] GCP Identity Token fetched successfully. Length: ${token.length}`);
      return token;
    }
    console.warn(`[DEBUG] GCP Identity Token fetch failed: ${res.status} ${res.statusText}`);
  } catch (e) {
    // Not running on GCP (local dev) or metadata server unreachable
    console.info("[DEBUG] GCP Metadata server not reachable, skipping identity token fetch. Error:", e);
  }
  return null;
}

export const POST = async (req: NextRequest) => {
  console.log("================================================");
  console.log(`[DEBUG] Incoming POST request to /api/copilotkit`);
  console.log(`[DEBUG] Request headers:`, Object.fromEntries(req.headers));

  const agentUrl = process.env.AGENT_URL || "http://127.0.0.1:8000/copilotkit";
  console.log(`[DEBUG] Configured AGENT_URL: ${agentUrl}`);

  // The Cloud Run identity token audience must be the service base URL (no path).
  const serviceBaseUrl = new URL(agentUrl).origin;
  console.log(`[DEBUG] Derived serviceBaseUrl for token audience: ${serviceBaseUrl}`);
  const identityToken = await getGcpIdentityToken(serviceBaseUrl);
  if (identityToken) {
    console.log("[DEBUG] Proceeding with GCP Identity Token.");
  } else {
    console.log("[DEBUG] Proceeding without GCP Identity Token.");
  }

  console.log("[DEBUG] Initializing CopilotRuntime NextJS endpoint...");
  const { handleRequest } = copilotRuntimeNextJSAppRouterEndpoint({
    runtime: new CopilotRuntime({
      remoteEndpoints: [
        {
          url: agentUrl,
          ...(identityToken && {
            onBeforeRequest: (options: any) => {
              console.log(`[DEBUG] onBeforeRequest hook triggered. Adding Authorization header`);
              // Note: the SDK's onBeforeRequest should return the options object that is merged with defaults
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

  console.log("[DEBUG] Invoking handleRequest...");
  try {
    const response = await handleRequest(req);
    console.log(`[DEBUG] handleRequest returned successfully. Response status: ${response.status}`);
    console.log(`[DEBUG] Response headers:`, Object.fromEntries(response.headers));
    console.log("================================================");
    return response;
  } catch (error) {
    console.error(`[DEBUG] handleRequest threw an error:`, error);
    console.log("================================================");
    throw error;
  }
};
