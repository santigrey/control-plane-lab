from fastapi import FastAPI
from pydantic import BaseModel
import httpx

from db import insert_memory

OLLAMA_URL = "http://192.168.1.152:11434"
MODEL = "llama3.1:8b"

app = FastAPI(title="Control Plane Orchestrator", version="0.3.0")


class AskRequest(BaseModel):
    prompt: str
    use_tool: bool = False  # if true, call a tool and include the output


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/tool/ollama_tags")
async def tool_ollama_tags():
    """
    A simple "tool": fetch available models from the inference node.
    """
    async with httpx.AsyncClient(timeout=15.0) as client:
        r = await client.get(f"{OLLAMA_URL}/api/tags")
        r.raise_for_status()
        return r.json()


@app.post("/ask")
async def ask(req: AskRequest):
    tool_result = None

    # Optional tool call (proof of tool-use wiring)
    if req.use_tool:
        async with httpx.AsyncClient(timeout=15.0) as client:
            tr = await client.get(f"{OLLAMA_URL}/api/tags")
            tr.raise_for_status()
            tool_result = tr.json()

    payload = {
        "model": MODEL,
        "prompt": req.prompt,
        "stream": False,
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        r = await client.post(f"{OLLAMA_URL}/api/generate", json=payload)
        r.raise_for_status()
        data = r.json()

    response_text = data.get("response", "")

    # Persist to control-plane memory (embedding added next)
    memory_content = f"PROMPT: {req.prompt}\nRESPONSE: {response_text}"
    if tool_result is not None:
        memory_content += f"\nTOOL: ollama_tags\nTOOL_RESULT: {tool_result}"

    memory_id = insert_memory(source="orchestrator", content=memory_content)

    return {"model": MODEL, "response": response_text, "memory_id": memory_id, "tool_result": tool_result}
