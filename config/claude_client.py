import anthropic
from config.settings import settings


def get_claude_client() -> anthropic.Anthropic:
    return anthropic.Anthropic(api_key=settings.anthropic_api_key)


def call_claude(
    prompt: str,
    system: str = '',
    max_tokens: int = 4096,
    temperature: float = 0.2
) -> str:
    client = get_claude_client()

    response = client.messages.create(
        model=settings.claude_model,
        max_tokens=max_tokens,
        system=system if system else 'You are an expert software engineer.',
        messages=[{'role': 'user', 'content': prompt}]
    )

    return response.content[0].text
