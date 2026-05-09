from google.adk.agents import SequentialAgent
from tools.escalation_barrier import EscalationBarrier
from .producer import get_producer
from .reviewer import get_reviewer

# TODO: Add OSCAL validation loop via LoopAgent once real jsonschema validation
# is wired up. The producer should receive an exit_loop tool and call it when
# the generated OSCAL passes validation. For now, a single sequential pass
# (producer → reviewer) is used.

def get_ssp_generator_workflow():
    producer =  get_producer()
    reviewer =  get_reviewer()

    ssp_workflow = SequentialAgent(
        name="ssp_review_loop",
        sub_agents=[producer, reviewer],
    )

    return EscalationBarrier(name="review_barrier", inner=ssp_workflow)
