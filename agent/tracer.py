import os
from dotenv import load_dotenv

load_dotenv()


def setup_tracing():
    phoenix_api_key = os.getenv("PHOENIX_API_KEY")
    phoenix_space = os.getenv("PHOENIX_SPACE_NAME")

    if not phoenix_api_key:
        return None

    os.environ["PHOENIX_API_KEY"] = phoenix_api_key
    os.environ["PHOENIX_COLLECTOR_ENDPOINT"] = (
        f"https://app.phoenix.arize.com/s/{phoenix_space}/v1/traces"
    )

    from phoenix.otel import register
    from openinference.instrumentation.groq import GroqInstrumentor

    tracer_provider = register(
        project_name="loanguard",
        batch=False,
    )

    GroqInstrumentor().instrument(tracer_provider=tracer_provider)

    print("✅ Arize Phoenix tracing initialized")
    print(f"📊 View traces: https://app.phoenix.arize.com/s/{phoenix_space}")

    return tracer_provider