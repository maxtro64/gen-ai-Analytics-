import os
import time
from typing import Optional, List, Dict, Any, cast
from dotenv import load_dotenv
from openai import OpenAI
from google import genai
from google.genai import types

load_dotenv()


def generate_with_openai(
    system_prompt: str,
    user_prompt: str,
    api_key: str,
    model: str,
    base_url: Optional[str] = None,
) -> str:
    """Calls any OpenAI-compatible API (OpenAI, NVIDIA NIM, etc.)."""
    if base_url:
        client = OpenAI(api_key=api_key, base_url=base_url)
    else:
        client = OpenAI(api_key=api_key)

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.3,
        max_tokens=5000,
    )
    return response.choices[0].message.content or ""


def generate_with_gemini(system_prompt: str, user_prompt: str, api_key: str, model: str) -> str:
    """Calls the Google Gemini API with automatic candidate fallback on temporary 503 load spikes."""
    client = genai.Client(api_key=api_key)

    candidates = [model]
    for alt in ["gemini-3.5-flash-lite", "gemini-3.8-flash", "gemini-3.5-flash"]:
        if alt not in candidates:
            candidates.append(alt)

    last_exc = None
    for mdl in candidates:
        try:
            response = client.models.generate_content(
                model=mdl,
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=0.3,
                    max_output_tokens=6000,
                    automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
                ),
            )
            return response.text or ""
        except Exception as e:
            last_exc = e
            err_str = str(e).lower()
            if any(kw in err_str for kw in ["503", "demand", "404", "disconnect", "connection", "remote", "429", "quota", "exhausted", "rate_limit"]):
                time.sleep(1)
                continue
            raise e

    if last_exc:
        raise last_exc
    raise RuntimeError("No candidate Gemini models succeeded.")


def generate_report(
    system_prompt: str,
    user_prompt: str,
    provider: str,
    api_key: Optional[str] = None,
    model: Optional[str] = None,
) -> str:
    """Main entry point for report generation. Routes to the correct LLM backend."""

    if provider == "openai":
        key = api_key or os.getenv("OPENAI_API_KEY", "")
        mdl = model or "gpt-4o-mini"
        if not key:
            raise ValueError("OpenAI API key is missing")
        return generate_with_openai(system_prompt, user_prompt, key, mdl)

    elif provider == "nvidia":
        key = api_key or os.getenv("NVIDIA_API_KEY", "")
        mdl = model or os.getenv("NVIDIA_MODEL", "meta/llama-3.1-70b-instruct")
        if not key:
            raise ValueError("NVIDIA API key is missing")
        return generate_with_openai(
            system_prompt, user_prompt, key, mdl,
            base_url="https://integrate.api.nvidia.com/v1",
        )

    elif provider == "gemini":
        key = api_key or os.getenv("GEMINI_API_KEY", "")
        mdl = model or "gemini-3.5-flash-lite"
        if not key:
            raise ValueError("Gemini API key is missing")
        return generate_with_gemini(system_prompt, user_prompt, key, mdl)

    else:
        raise ValueError(f"Unknown provider: {provider}. Use 'openai', 'nvidia', or 'gemini'.")


def generate_chat_response(
    messages: List[Dict[str, str]],
    system_prompt: str,
    provider: str,
    api_key: Optional[str] = None,
    model: Optional[str] = None,
) -> str:
    """
    Handles conversational multi-turn chat interactions with full data and report context.
    messages is a list of {'role': 'user' | 'assistant', 'content': '...'}
    """
    if provider == "openai":
        key = api_key or os.getenv("OPENAI_API_KEY", "")
        mdl = model or "gpt-4o-mini"
        if not key:
            raise ValueError("OpenAI API key is missing")
        client = OpenAI(api_key=key)
        chat_messages = [{"role": "system", "content": system_prompt}] + messages
        response = client.chat.completions.create(
            model=mdl,
            messages=cast(Any, chat_messages),
            temperature=0.3,
            max_tokens=2048,
        )
        return response.choices[0].message.content or ""

    elif provider == "nvidia":
        key = api_key or os.getenv("NVIDIA_API_KEY", "")
        mdl = model or os.getenv("NVIDIA_MODEL", "meta/llama-3.1-70b-instruct")
        if not key:
            raise ValueError("NVIDIA API key is missing")
        client = OpenAI(api_key=key, base_url="https://integrate.api.nvidia.com/v1")
        chat_messages = [{"role": "system", "content": system_prompt}] + messages
        response = client.chat.completions.create(
            model=mdl,
            messages=cast(Any, chat_messages),
            temperature=0.3,
            max_tokens=2048,
        )
        return response.choices[0].message.content or ""

    elif provider == "gemini":
        key = api_key or os.getenv("GEMINI_API_KEY", "")
        mdl = model or "gemini-3.5-flash"
        if not key:
            raise ValueError("Gemini API key is missing")

        client = genai.Client(api_key=key)

        gemini_contents = []
        for msg in messages:
            role = "user" if msg["role"] == "user" else "model"
            gemini_contents.append(
                types.Content(
                    role=role,
                    parts=[types.Part.from_text(text=msg["content"])],
                )
            )

        candidates = [mdl]
        for alt in ["gemini-3.5-flash-lite", "gemini-3.8-flash", "gemini-3.5-flash"]:
            if alt not in candidates:
                candidates.append(alt)

        last_exc = None
        for candidate in candidates:
            try:
                response = client.models.generate_content(
                    model=candidate,
                    contents=gemini_contents,
                    config=types.GenerateContentConfig(
                        system_instruction=system_prompt,
                        temperature=0.3,
                        max_output_tokens=3500,
                        automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
                    ),
                )
                return response.text or ""
            except Exception as e:
                last_exc = e
                err_str = str(e).lower()
                if any(kw in err_str for kw in ["503", "demand", "404", "disconnect", "connection", "remote", "429", "quota", "exhausted", "rate_limit"]):
                    time.sleep(1)
                    continue
                raise e

        if last_exc:
            raise last_exc
        raise RuntimeError("No candidate Gemini models succeeded.")

    else:
        raise ValueError(f"Unknown provider: {provider}. Use 'openai', 'nvidia', or 'gemini'.")
