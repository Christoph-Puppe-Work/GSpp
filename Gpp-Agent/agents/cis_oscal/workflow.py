from google.adk.agents.sequential_agent import SequentialAgent
from google.adk.agents.loop_agent import LoopAgent
from google.adk.agents.llm_agent import LlmAgent

from .producer import get_producer
from .reviewer import get_reviewer
from .tools import load_cis_input, write_oscal_artifact

async def get_workflow() -> SequentialAgent:
    # 1. Input Loader
    input_loader = LlmAgent(
        name="input_loader",
        model="gemini-2.0-flash",
        instruction="Load the CIS input from GCS using the provided tool.",
        tools=[load_cis_input]
    )

    # 2. Review Loop
    producer = await get_producer()
    review_loop = LoopAgent(
        name="review_loop",
        sub_agents=[producer, get_reviewer()],
        max_iterations=3
    )

    # 3. Artifact Writer
    artifact_writer = LlmAgent(
        name="artifact_writer",
        model="gemini-2.0-flash",
        instruction="Take the 'draft_artifact' and write it to GCS as a final OSCAL component definition.",
        tools=[write_oscal_artifact]
    )

    return SequentialAgent(
        name="cis_oscal_workflow",
        sub_agents=[input_loader, review_loop, artifact_writer]
    )
