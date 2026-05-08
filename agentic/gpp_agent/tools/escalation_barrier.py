from typing import AsyncGenerator
from google.adk.agents import BaseAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event

class EscalationBarrier(BaseAgent):
    inner: BaseAgent

    def __init__(self, *, name: str, inner: LoopAgent, **kwargs):
        super().__init__(name=name, sub_agents=[inner], **kwargs)
        self.inner = inner

    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        async for event in self.inner.run_async(ctx):
            # Strip escalate from events leaving this barrier so the parent
            # SequentialAgent continues with the next sub-agent.
            if event.actions and event.actions.escalate:
                event.actions.escalate = False
            yield event
