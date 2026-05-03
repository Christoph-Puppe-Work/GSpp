from google.adk.agents.llm_agent import LlmAgent
from tools.exit_loop import exit_loop
from shared.review_criteria import PolicyReviewCriteria

def get_reviewer() -> LlmAgent:
    return LlmAgent(
        name="policy_reviewer",
        model="gemini-2.0-flash",
        instruction=f"""Review generated policies for consistency and completeness.
        Criteria: {PolicyReviewCriteria.model_json_schema()}
        Call 'exit_loop' if approved.""",
        tools=[exit_loop]
    )
