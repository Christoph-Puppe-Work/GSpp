from google.adk.agents.sequential_agent import SequentialAgent
from google.adk.agents.loop_agent import LoopAgent
from google.adk.agents.llm_agent import LlmAgent

from .producer import get_producer
from .reviewer import get_reviewer
from .tools import load_vendor_docs, write_evidence_artifact

async def get_workflow() -> SequentialAgent:
    input_loader = LlmAgent(
        name="input_loader",
        model="gemini-2.0-flash",
        instruction="Load vendor documents.",
        tools=[load_vendor_docs]
    )

    producer = await get_producer()
    review_loop = LoopAgent(
        name="review_loop",
        sub_agents=[producer, get_reviewer()],
        max_iterations=3
    )

    artifact_writer = LlmAgent(
        name="artifact_writer",
        model="gemini-2.0-flash",
        instruction="Write final evidence artifacts.",
        tools=[write_evidence_artifact]
    )

    return SequentialAgent(
        name="vendor_evidence_workflow",
        sub_agents=[input_loader, review_loop, artifact_writer]
    )
