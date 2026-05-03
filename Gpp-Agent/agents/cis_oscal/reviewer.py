from google.adk.agents.llm_agent import LlmAgent
from tools.exit_loop import exit_loop
from shared.review_criteria import CisOscalReviewCriteria

def get_reviewer() -> LlmAgent:
    return LlmAgent(
        name="cis_oscal_reviewer",
        model="gemini-2.0-flash",
        instruction=f"""You are a Peer Reviewer for CIS to OSCAL mappings.
        Check the 'draft_artifact' in the state against the original input.
        Use these criteria: {CisOscalReviewCriteria.model_json_schema()}
        If the artifact is excellent and meets all criteria, call the 'exit_loop' tool.
        Otherwise, provide detailed feedback in 'review_feedback' so the producer can improve it.""",
        tools=[exit_loop]
    )
