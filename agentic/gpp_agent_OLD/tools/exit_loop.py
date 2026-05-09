from google.adk.tools.tool_context import ToolContext

def exit_loop(reason: str, tool_context: ToolContext) -> dict:
    tool_context.actions.escalate = True
    tool_context.actions.skip_summarization = True   # avoids extra LLM call
    return {"status": "approved", "reason": reason}
