import os
from google.adk.agents import LoopAgent, SequentialAgent
from tools.escalation_barrier import EscalationBarrier
from .producer import get_producer
from .reviewer import get_reviewer

async def get_ssp_generator_workflow() -> SequentialAgent:
    producer = await get_producer()
    reviewer = await get_reviewer()

    review_loop = LoopAgent(
        name="ssp_review_loop",
        sub_agents=[producer, reviewer],
        max_iterations=int(os.environ.get("MAX_REVIEW_ITERATIONS", "3")),
    )

    return SequentialAgent(
        name="ssp_generator_workflow",
        sub_agents=[
            EscalationBarrier(name="review_barrier", inner=review_loop),
            # In a full implementation, we'd add HITL and GCS Writer here
        ],
    )
