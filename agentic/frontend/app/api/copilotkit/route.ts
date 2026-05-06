import { NextRequest } from "next/server";
import { CopilotRuntime, copilotRuntimeNextJSAppRouterEndpoint } from "@copilotkit/runtime";

export const POST = async (req: NextRequest) => {
  // Verbindet das Next.js Frontend mit dem ADK Agenten über das AG-UI Protokoll
  const { handleRequest } = copilotRuntimeNextJSAppRouterEndpoint({
    runtime: new CopilotRuntime({
      remoteEndpoints: [
        {
          // ADK API Server (läuft normalerweise auf Port 8000)
          url: process.env.AGENT_URL || "http://127.0.0.1:8000/copilotkit",
        },
      ],
    }),
    endpoint: "/api/copilotkit",
  });

  return handleRequest(req);
};
