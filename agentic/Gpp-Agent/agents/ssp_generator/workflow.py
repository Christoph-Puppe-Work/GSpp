import os
from google.adk import Workflow, Event
from tools.escalation_barrier import EscalationBarrier
from .producer import get_producer
from .reviewer import get_reviewer

def validate_oscal(node_input):
    # Deterministic validation using your GS_backend_MCP tools or local jsonschema
    # Placeholder for actual validation logic
    errors = [] # perform_oscal_validation(node_input)
    if errors:
        return Event(route="invalid", message={"errors": errors, "draft": node_input})
    return Event(route="valid", message=node_input)

async def get_ssp_generator_workflow():
    producer = await get_producer()
    reviewer = await get_reviewer()

    ssp_workflow = Workflow(
        name="ssp_review_loop",
        edges=[
            ("START", producer),
            (producer, validate_oscal),
            (validate_oscal, {
                "invalid": producer, # Automatically loops back
                "valid": reviewer    # Proceeds to reviewer
            }),
        ],
    )

    return EscalationBarrier(name="review_barrier", inner=ssp_workflow)
