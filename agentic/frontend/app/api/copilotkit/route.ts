import { NextRequest } from "next/server";
import { CopilotRuntime, copilotRuntimeNextJSAppRouterEndpoint } from "@copilotkit/runtime";

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
    if (res.ok) return res.text();
  } catch {
    // Not running on GCP (local dev) — skip auth
  }
  return null;
}

export const POST = async (req: NextRequest) => {
  const agentUrl = process.env.AGENT_URL || "http://127.0.0.1:8000/copilotkit";

  // The Cloud Run identity token audience must be the service base URL (no path).
  const serviceBaseUrl = new URL(agentUrl).origin;
  const identityToken = await getGcpIdentityToken(serviceBaseUrl);

  const { handleRequest } = copilotRuntimeNextJSAppRouterEndpoint({
    runtime: new CopilotRuntime({
      remoteEndpoints: [
        {
          url: agentUrl,
          ...(identityToken && {
            onBeforeRequest: () => ({
              headers: { Authorization: `Bearer ${identityToken}` },
            }),
          }),
        },
      ],
    }),
    endpoint: "/api/copilotkit",
  });

  return handleRequest(req);
};
