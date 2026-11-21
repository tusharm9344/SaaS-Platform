# Runtime RCA — Python SDK

Runtime RCA is a Python SDK for collecting application errors, grouping similar errors into incidents, and performing automated root-cause analysis.

It connects Python applications to the Runtime RCA backend.

## Features

- Capture Python exceptions.
- Capture custom error messages.
- Automatically capture uncaught main-thread exceptions.
- Automatically capture uncaught background-thread exceptions.
- Asynchronous event delivery using a background worker.
- Configurable request timeout and retry settings.
- Configurable service name and environment.

## Requirements

- Python 3.10+
- Runtime RCA backend running and accessible.
- A valid Runtime RCA application API key.

## Installation

### Install from the Runtime RCA repository

Clone the repository:

```bash
git clone <YOUR_REPOSITORY_URL>
cd SaaS-Platform
```

Install the SDK:

```bash
pip install -e ./sdk/python
```

The editable installation is intended for local development.

## Configuration

Create an application in Runtime RCA and generate an API key.

Set the API key as an environment variable:

```bash
export RCA_API_KEY="your-api-key"
```

Avoid hardcoding API keys in application source code.

## Basic Usage

```python
import os

from runtime_rca import RuntimeRCA

rca = RuntimeRCA(
    api_key=os.environ["RCA_API_KEY"],
    service_name="payment-service",
    environment="development",
    base_url="http://127.0.0.1:8000",
)

try:
    process_payment()

except Exception as error:
    rca.capture_exception(error)

finally:
    rca.close()
```

## Capture Custom Messages

You can also report errors without an exception object.

```python
rca.capture_message(
    "Payment gateway connection failed",
    severity="error",
)
```

## Automatic Exception Monitoring

Runtime RCA can automatically capture uncaught exceptions.

```python
import os

from runtime_rca import RuntimeRCA

rca = RuntimeRCA(
    api_key=os.environ["RCA_API_KEY"],
    service_name="payment-service",
    environment="production",
)

rca.install_exception_hooks()

def process_payment():
    raise ValueError("Payment processing failed")

process_payment()
```

The SDK captures uncaught exceptions in:

- The main Python thread.
- Background Python threads.

The original Python exception behavior is preserved.

**Important:** Automatic hooks capture uncaught exceptions. Exceptions handled internally by your application must be explicitly reported using `capture_exception()`.

## Configuration Options

| Parameter | Default | Description |
|---|---|---|
| api_key | Required | Application API key |
| service_name | Required | Name of the monitored service |
| environment | production | Environment name |
| base_url | localhost:8000 | Runtime RCA backend URL |
| timeout | 5 | HTTP request timeout in seconds |
| max_retries | 3 | Maximum transport retries |
| max_queue_size | 1000 | Maximum background queue size |

## SDK Lifecycle

Runtime RCA provides three lifecycle methods.

### flush()

```python
rca.flush(timeout=10)
```

Waits for pending events in the background queue to be processed.

Note: Queue completion does not currently guarantee successful backend delivery.

### close()

```python
rca.close()
```

Stops exception monitoring and shuts down the background worker.

### uninstall_exception_hooks()

```python
rca.uninstall_exception_hooks()
```

Restores the previously registered Python exception hooks.

## Running Tests

From the SDK directory:

```bash
python -m unittest discover -s tests -v
```

## Architecture

```text
Python Application
       |
       v
Runtime RCA SDK
       |
       +--> Exception Capture
       |
       +--> Event Payload Creation
       |
       +--> Background Queue
                  |
                  v
             Event Worker
                  |
                  v
             HTTP Transport
                  |
                  v
          Django Ingestion API
                  |
                  v
           Error Event Storage
                  |
                  v
           Incident Grouping
                  |
                  v
          Celery + Redis
                  |
                  v
             RCA Engine
```

## Current Limitations

- Background delivery uses an in-memory queue.
- Events can be lost if the process terminates unexpectedly.
- Delivery confirmation is not yet exposed through the SDK.
- Automatic hooks do not capture handled exceptions.
- The SDK currently supports Python applications.

## Project Status

Runtime RCA is under active development. The SDK and backend are currently being developed and tested as part of the Runtime RCA project.