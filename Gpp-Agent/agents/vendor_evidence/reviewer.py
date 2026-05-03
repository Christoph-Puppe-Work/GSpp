from google.adk.agents.llm_agent import LlmAgent
from tools.exit_loop import exit_loop
from shared.review_criteria import VendorEvidenceReviewCriteria

def get_reviewer() -> LlmAgent:
    return LlmAgent(
        name="vendor_evidence_reviewer",
        model="gemini-2.0-flash",
        instruction=f"""Review extracted evidence and mappings.
        Criteria: {VendorEvidenceReviewCriteria.model_json_schema()}
        Call 'exit_loop' if approved.""",
        tools=[exit_loop]
    )
