"""Shared model settings and strict request validation (no ML imports)."""
BASE_MODEL = "Qwen/Qwen2.5-Coder-1.5B-Instruct"
SYSTEM = "You are Forge, a coding assistant. Give a concise explanation, then correct code in a fenced code block. Mention important edge cases. Never claim you ran code."
MODES = {
    "build": "Write a small, clear implementation for the user's request.",
    "explain": "Explain the supplied code clearly, including edge cases.",
    "debug": "Identify likely bugs and provide corrected code. Ask for missing details when needed.",
}

def validate_chat(payload):
    if not isinstance(payload, dict):
        raise ValueError("Expected a JSON object.")
    mode = payload.get("mode", "build")
    if mode not in MODES:
        raise ValueError("Unknown mode.")
    messages = payload.get("messages")
    if not isinstance(messages, list) or not 1 <= len(messages) <= 12:
        raise ValueError("Send between 1 and 12 messages.")
    clean = []
    for i, message in enumerate(messages):
        if not isinstance(message, dict):
            raise ValueError("Invalid message.")
        role, content = message.get("role"), message.get("content")
        if role != ("user" if i % 2 == 0 else "assistant"):
            raise ValueError("Messages must alternate, starting with user.")
        if not isinstance(content, str) or not content.strip() or len(content) > 6000:
            raise ValueError("Each message must contain 1–6000 characters.")
        clean.append({"role": role, "content": content})
    if clean[-1]["role"] != "user" or sum(len(x["content"]) for x in clean) > 16000:
        raise ValueError("End with a user message; keep the conversation under 16000 characters.")
    return [{"role": "system", "content": SYSTEM + " " + MODES[mode]}] + clean

