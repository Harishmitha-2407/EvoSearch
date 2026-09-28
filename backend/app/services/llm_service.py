"""
Thin wrapper around LLM APIs (Anthropic or Groq) for tasks that genuinely benefit from
language understanding: claim extraction, summaries, change explanations,
Q&A synthesis, code-change explanations, improvement suggestions.

If LLM_API_KEY is not configured, `is_available()` returns False and
every caller in this codebase falls back to a deterministic heuristic
implementation instead. EVOSearch is fully functional (with reduced
sophistication) without an LLM key configured.
"""
import json
import re
from app.config import settings

_client = None
_provider = None


def is_available() -> bool:
    provider = getattr(settings, 'LLM_PROVIDER', 'anthropic').lower()
    groq_key = getattr(settings, 'GROQ_API_KEY', None)
    anthropic_key = getattr(settings, 'ANTHROPIC_API_KEY', None)
    
    if provider == 'groq':
        return bool(groq_key)
    else:
        return bool(anthropic_key)


def _get_client():
    global _client, _provider
    if _client is None:
        provider = getattr(settings, 'LLM_PROVIDER', 'anthropic').lower()
        _provider = provider
        
        if provider == 'groq':
            try:
                from groq import Groq
                import httpx
                # Create Groq client with timeout
                http_client = httpx.Client(timeout=30.0)
                _client = Groq(api_key=settings.GROQ_API_KEY, http_client=http_client)
            except Exception as e:
                print(f"[ERROR] Failed to initialize Groq client: {e}")
                raise
        else:
            import anthropic
            _client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY, timeout=30.0)
    return _client


def _extract_json(text: str):
    """LLMs sometimes wrap JSON in prose or code fences despite instructions;
    this defensively extracts the first well-formed JSON object/array."""
    text = text.strip()
    text = re.sub(r"^```(json)?", "", text).strip()
    text = re.sub(r"```$", "", text).strip()
    try:
        return json.loads(text)
    except Exception:
        pass
    match = re.search(r"(\{.*\}|\[.*\])", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except Exception:
            return None
    return None


def call_structured(system_prompt: str, user_prompt: str, max_tokens: int = 1500):
    """Calls the LLM and attempts to parse a JSON response. Returns None on
    any failure so callers can gracefully fall back to heuristics - EVOSearch
    never accepts malformed AI output without validation."""
    if not is_available():
        return None
    try:
        client = _get_client()
        provider = getattr(settings, 'LLM_PROVIDER', 'anthropic').lower()
        
        if provider == 'groq':
            combined_prompt = f"{system_prompt}\n\n{user_prompt}"
            resp = client.chat.completions.create(
                model=settings.LLM_MODEL,
                max_tokens=max_tokens,
                messages=[{"role": "user", "content": combined_prompt}],
                timeout=30.0,
            )
            text = resp.choices[0].message.content
        else:
            resp = client.messages.create(
                model=settings.LLM_MODEL,
                max_tokens=max_tokens,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
                timeout=30.0,
            )
            text = "".join(block.text for block in resp.content if block.type == "text")
        
        return _extract_json(text)
    except Exception as e:
        print(f"[ERROR] LLM call_structured error: {e}")
        import traceback
        traceback.print_exc()
        return None


def call_text(system_prompt: str, user_prompt: str, max_tokens: int = 800) -> str | None:
    if not is_available():
        return None
    try:
        client = _get_client()
        provider = getattr(settings, 'LLM_PROVIDER', 'anthropic').lower()
        
        if provider == 'groq':
            combined_prompt = f"{system_prompt}\n\n{user_prompt}"
            resp = client.chat.completions.create(
                model=settings.LLM_MODEL,
                max_tokens=max_tokens,
                messages=[{"role": "user", "content": combined_prompt}],
                timeout=30.0,
            )
            result = resp.choices[0].message.content.strip()
            return result
        else:
            resp = client.messages.create(
                model=settings.LLM_MODEL,
                max_tokens=max_tokens,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
                timeout=30.0,
            )
            return "".join(block.text for block in resp.content if block.type == "text").strip()
    except Exception as e:
        print(f"[ERROR] LLM call_text error: {e}")
        import traceback
        traceback.print_exc()
        return None
