from google.adk.agents.sequential_agent import SequentialAgent
from google.adk.agents.loop_agent import LoopAgent
from google.adk.agents.parallel_agent import ParallelAgent
from google.adk.agents.llm_agent import LlmAgent

from .producer import get_producer
from .reviewer import get_reviewer
from .tools import write_policy_artifact

DOMAINS = [
    "ISMS", "ORP", "CON", "OPS", "DER", "APP", "SYS", "IND", "NET", "INF",
    "COM", "DAT", "CON_EXT", "SEC_MGMT", "RISK_MGMT", "INC_MGMT", "BCM"
]

async def get_workflow() -> SequentialAgent:
    # 17 Domains in parallel
    producers = [await get_producer(domain) for domain in DOMAINS]
    parallel_producers = ParallelAgent(
        name="parallel_policy_producers",
        sub_agents=producers
    )

    review_loop = LoopAgent(
        name="review_loop",
        sub_agents=[parallel_producers, get_reviewer()],
        max_iterations=3
    )

    artifact_writer = LlmAgent(
        name="artifact_writer",
        model="gemini-2.0-flash",
        instruction="Finalize and write all domain policies.",
        tools=[write_policy_artifact]
    )

    return SequentialAgent(
        name="policy_generator_workflow",
        sub_agents=[review_loop, artifact_writer]
    )
