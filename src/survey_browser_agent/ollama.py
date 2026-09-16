import httpx

from survey_browser_agent.models import OllamaCheck


def _model_names(payload: dict) -> list[str]:
    names = []
    for model in payload.get("models", []):
        if isinstance(model, dict) and isinstance(model.get("name"), str):
            names.append(model["name"])
    return sorted(names)


def check_ollama(base_url: str, model: str, timeout: float = 5.0) -> OllamaCheck:
    """Use Ollama's local `/api/tags` endpoint to check the service and model."""

    endpoint = f"{base_url.rstrip('/')}/api/tags"
    try:
        response = httpx.get(endpoint, timeout=timeout)
        response.raise_for_status()
        installed = _model_names(response.json())
    except (httpx.HTTPError, ValueError) as exc:
        return OllamaCheck(
            reachable=False,
            model=model,
            model_available=False,
            message=f"Ollama is not reachable at {base_url}: {exc}",
        )

    available = model in installed
    message = (
        f"Ollama is ready and {model} is installed."
        if available
        else f"Ollama is running, but {model} is not installed. Run: ollama pull {model}"
    )
    return OllamaCheck(
        reachable=True,
        model=model,
        model_available=available,
        installed_models=installed,
        message=message,
    )
