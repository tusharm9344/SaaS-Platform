import os

from runtime_rca import RuntimeRCA

rca = RuntimeRCA(
    api_key=os.environ["RCA_API_KEY"],
    service_name="sdk-integration-test",
    environment="development",
    base_url="http://127.0.0.1:8000",
)

try:
    raise ValueError("Async SDK test: payment processing failed")

except Exception as error:
    result = rca.capture_exception(error)
    print("Event queued:", result)

print("Flushing events...")
print("Delivered:", rca.flush(timeout=10))

rca.close()