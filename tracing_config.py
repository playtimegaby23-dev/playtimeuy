# tracing_config.py
import logging
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor

logger = logging.getLogger("PlayTimeUY.tracing")

def configure_tracing(app):
    # Crear provider de trazas
    provider = TracerProvider()
    trace.set_tracer_provider(provider)

    # Exportar a consola (útil para debug)
    console_exporter = ConsoleSpanExporter()
    provider.add_span_processor(BatchSpanProcessor(console_exporter))

    # Exportar también vía OTLP (para collectors o Google Cloud Trace)
    otlp_exporter = OTLPSpanExporter(endpoint="http://localhost:4318/v1/traces")
    provider.add_span_processor(BatchSpanProcessor(otlp_exporter))

    # Instrumentar Flask y Requests
    FlaskInstrumentor().instrument_app(app)
    RequestsInstrumentor().instrument()

    logger.info("✅ OpenTelemetry tracing inicializado correctamente")
