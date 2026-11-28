import logging

import litellm

logger = logging.getLogger(__name__)


def generate_completion(
    *,
    model,
    api_key,
    messages,
    api_base=None,
    timeout=45,
):
    """
    Provider-independent LLM completion through LiteLLM.

    model must be a valid LiteLLM model identifier.
    """

    if not model or not api_key:
        raise ValueError("Model and API key are required.")

    kwargs = {
        "model": model,
        "api_key": api_key,
        "messages": messages,
        "temperature": 0.2,
        "timeout": timeout,
    }

    if api_base:
        kwargs["api_base"] = api_base

    response = litellm.completion(**kwargs)

    content = response.choices[0].message.content

    if not isinstance(content, str) or not content.strip():
        raise ValueError("AI provider returned an empty response.")

    return content