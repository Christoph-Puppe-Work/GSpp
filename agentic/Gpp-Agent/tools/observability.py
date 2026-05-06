import os
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.cloud_trace import CloudTraceSpanExporter
from google.adk.callback_context import CallbackContext

def configure_observability() -> None:
    if os.environ.get("OTEL_DISABLED") == "1": return
    provider = TracerProvider()
    try:
        exporter = CloudTraceSpanExporter(project_id=os.environ["GOOGLE_CLOUD_PROJECT"])
        provider.add_span_processor(BatchSpanProcessor(exporter))
    except Exception:
        # Fallback or ignore if GCP project not set
        pass
    trace.set_tracer_provider(provider)

def enrich_span_with_iv(callback_context: CallbackContext) -> None:
    """before_agent_callback: tag the current span with iv_id for filtering."""
    iv_id = callback_context.state.get("informationsverbund_id", "unknown")
    span = trace.get_current_span()
    span.set_attribute("gpp.iv_id", iv_id)
    span.set_attribute("gpp.agent", callback_context.agent_name)
