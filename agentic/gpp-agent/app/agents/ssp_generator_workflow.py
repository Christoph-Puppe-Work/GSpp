from google.adk.agents import LoopAgent, BaseAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event, EventActions
from typing import AsyncGenerator
from .producer import get_producer
from .reviewer import get_reviewer

class EscalationChecker(BaseAgent):
    """Stops the LoopAgent when the Reviewer passes the SSP."""
    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        review_feedback = ctx.session.state.get("review_feedback")
        
        if review_feedback:
            # Assuming ReviewCriteria has an `is_approved` or similar field
            # Check if it passed
            is_approved = review_feedback.get("is_approved", False)
            if is_approved:
                # If approved, escalate out of the loop
                yield Event(
                    author=self.name,
                    content="SSP Approved. Escalating out of review loop.",
                    actions=EventActions(escalate=True)
                )
            else:
                yield Event(
                    author=self.name,
                    content=f"SSP Needs Revision. Feedback: {review_feedback.get('feedback', 'No comments provided.')}"
                )
        else:
            yield Event(author=self.name, content="Waiting for Reviewer feedback.")

def get_ssp_generator_workflow() -> LoopAgent:
    producer = get_producer()
    reviewer = get_reviewer()
    checker = EscalationChecker(name="review_escalation_checker")

    ssp_workflow = LoopAgent(
        name="ssp_review_loop",
        sub_agents=[producer, reviewer, checker],
        max_iterations=5,
        description="Coordinates the SSP generation loop (Maker-Checker) between Producer and Reviewer."
    )

    return ssp_workflow
