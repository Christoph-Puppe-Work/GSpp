from google.adk.tools import ToolContext


def exit_loop(reason: str, tool_context: ToolContext) -> dict:
    """
    Signal that the reviewed artifact is approved and the review loop
    can exit. Set reason to a short human-readable approval rationale.
    """
    tool_context.actions.escalate = True
    return {"status": "approved", "reason": reason}
