"use client";

import { CopilotSidebar } from "@copilotkit/react-ui";
import { useCopilotAction } from "@copilotkit/react-core";

export default function Home() {

  // Hier registrieren wir unsere Generative UI für HITL (Human-In-The-Loop)
  (useCopilotAction as any)({
    name: "approve_artifact",
    handler: async (args: any) => {
      console.log("Artifact approved:", args);
      return "Artifact approved";
    },
    render: ({ args, status, handler }: any) => {

      // Wenn der Agent ein Artefakt vorlegt, rendern wir ein benutzerfreundliches Review-Formular
      return (
        <div className="p-4 bg-gray-100 rounded-lg shadow mt-2">
          <h3 className="font-bold text-lg text-blue-800 mb-2">Freigabe erforderlich (HITL)</h3>
          <p className="text-sm mb-4">Der Agent bittet um Prüfung des OSCAL Artefakts.</p>

          <div className="bg-white p-2 rounded mb-4 overflow-auto max-h-48 text-xs border border-gray-300">
            <pre>{JSON.stringify(args, null, 2)}</pre>
          </div>

          {status === "executing" && (
            <div className="flex gap-2">
              <button
                className="bg-green-600 text-white px-4 py-2 rounded font-medium hover:bg-green-700 transition"
                onClick={() => handler?.("approved")}
              >
                Freigeben
              </button>
              <button
                className="bg-red-600 text-white px-4 py-2 rounded font-medium hover:bg-red-700 transition"
                onClick={() => handler?.("rejected")}
              >
                Ablehnen
              </button>
            </div>
          )}
        </div>
      );
    },
  });

  return (
    <main className="flex h-screen flex-col items-center justify-center bg-gray-50">
      <div className="z-10 w-full max-w-5xl items-center justify-between font-mono text-sm p-4">
        <h1 className="text-4xl font-bold text-center text-blue-900 mb-8">
          G++ Compliance Management
        </h1>
        <p className="text-center text-gray-600 max-w-2xl mx-auto text-lg">
          Willkommen beim gpp_agenten. Öffnen Sie die Chat-Sidebar auf der rechten Seite, um den Workflow für Ihren Informationsverbund zu starten.
        </p>
      </div>

      <CopilotSidebar 
        defaultOpen={true} 
        labels={{
          title: "gpp_agent",
          initial: "Hallo! Ich bin dein G++ Compliance Agent. Wie kann ich beim System Security Plan helfen?",
        }}
      />
    </main>
  );
}
