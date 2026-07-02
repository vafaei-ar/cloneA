from typing import Generator
import requests
import config


def chat(messages: list[dict], stream: bool = False) -> str | Generator[str, None, None]:
    payload = {
        "model": config.OLLAMA_MODEL,
        "messages": messages,
        "stream": stream,
    }
    resp = requests.post(
        f"{config.OLLAMA_BASE_URL}/api/chat",
        json=payload,
        stream=stream,
        timeout=120,
    )
    resp.raise_for_status()

    if stream:
        return _stream_tokens(resp)
    return resp.json()["message"]["content"]


def _stream_tokens(resp: requests.Response) -> Generator[str, None, None]:
    import json
    for line in resp.iter_lines():
        if line:
            data = json.loads(line)
            yield data["message"]["content"]
            if data.get("done"):
                break
