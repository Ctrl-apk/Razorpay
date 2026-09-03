from .base import AIProvider
from ..config import settings


def get_provider() -> AIProvider:
    """Return the configured AI provider, falling back to deterministic stub."""
    provider_name = settings.ai_provider.lower()

    if provider_name == "openai":
        try:
            from .openai_provider import OpenAIInvestigator
            return OpenAIInvestigator()
        except Exception as e:
            print(f"[WARN] OpenAI provider unavailable ({e}), falling back to stub")

    if provider_name == "anthropic":
        try:
            from .anthropic_provider import AnthropicInvestigator
            return AnthropicInvestigator()
        except Exception as e:
            print(f"[WARN] Anthropic provider unavailable ({e}), falling back to stub")

    # Default: deterministic stub
    from .deterministic import DeterministicInvestigator
    return DeterministicInvestigator()
