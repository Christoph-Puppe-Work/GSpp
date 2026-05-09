from typing import AsyncGenerator
from google.adk.agents import BaseAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event


class EscalationBarrier(BaseAgent):
    inner: BaseAgent

    def __init__(self, *, name: str, inner: BaseAgent, **kwargs):
        super().__init__(
            name=name,
            inner=inner,           # ← Pydantic-Feld muss in super() rein
            sub_agents=[inner],    # ← weiterhin als sub_agent registriert für ADK-Tree
            **kwargs,
        )

    async def _run_async_impl(
        self, ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        async for event in self.inner.run_async(ctx):
            # escalate aus Events absorbieren, damit parent SequentialAgent weiterläuft
            if event.actions and event.actions.escalate:
                event.actions.escalate = False
            yield event