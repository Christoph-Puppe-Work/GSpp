import { NextRequest } from "next/server";
import { CopilotRuntime, copilotRuntimeNextJSAppRouterEndpoint } from "@copilotkit/runtime";
import { GoogleAuth } from "google-auth-library";

const auth = new GoogleAuth();

export const POST = async (req: NextRequest) => {
  const agentUrl = process.env.AGENT_URL || "http://127.0.0.1:8000/copilotkit";

  const serviceBaseUrl = new URL(agentUrl).origin;
  let authHeaders = {};

  try {
    const client = await auth.getIdTokenClient(serviceBaseUrl);
    authHeaders = await client.getRequestHeaders(serviceBaseUrl);
  } catch (e) {
    console.log("Not using GCP Auth (local dev without ADC or localhost agent)");
  }

  const { handleRequest } = copilotRuntimeNextJSAppRouterEndpoint({
    runtime: new CopilotRuntime({
      remoteEndpoints: [
        {
          url: agentUrl,
          onBeforeRequest: () => ({
            headers: authHeaders,
          }),
        },
      ],
    }),
    endpoint: "/api/copilotkit",
  });

  return handleRequest(req);
};
