"""Phase 4 output sanitizer -- strips spec section 5 patterns from LLM responses before client return.

Per paco_response_phase4_sanitizer.md: output-only, last gate before client, memory
write happens BEFORE sanitize (raw lives in memory.content).

Strip order matters: tool_json patterns FIRST (nested patterns may contain other
targets). Markdown residue LAST (cleanup pass).
"""
import re
from dataclasses import dataclass


@dataclass
class SanitizeResult:
    text: str
    raw_length: int
    sanitized_length: int
    strips: dict
    applied: bool


# Canonical strip patterns. Order matters.
_TOOL_JSON_NESTED    = re.compile(r'\{[^{}]*\{[^{}]*\}[^{}]*\}')
_TOOL_JSON_FIELD     = re.compile(r'\{[^{}]*"tool"[^{}]*\}')
_TOOL_JSON_LEAD      = re.compile(r'^\s*\}\s*')
_TOOL_CALLS_OLLAMA   = re.compile(r'"tool_calls"\s*:\s*\[.*?\]', re.DOTALL)
_CONTEXT_ENVELOPE    = re.compile(r'\[CONTEXT\].*?\[/CONTEXT\]', re.DOTALL)
_KNOWLEDGE_ENVELOPE  = re.compile(r'\[KNOWLEDGE\].*?\[/KNOWLEDGE\]', re.DOTALL)
_JUDGMENT_SENTINEL   = re.compile(r'\[\[JUDGMENT:[^\]]*\]\]')
_ESCALATION_SENTINEL = re.compile(r'\[\[ESCALATE:(sonnet|opus)\]\]')
_MARKDOWN_BOLD       = re.compile(r'\*\*([^*]+)\*\*')
_MARKDOWN_ITALIC     = re.compile(r'\*([^*]+)\*')
_MARKDOWN_LEAD       = re.compile(r'^\s*\*+\s*', re.MULTILINE)

def sanitize_output(raw: str) -> SanitizeResult:
    """Apply spec section 5 strips in canonical order. Returns result + provenance counters."""
    strips = {
        'tool_json': 0,
        'context_envelope': 0,
        'judgment_sentinel': 0,
        'escalation_sentinel': 0,
        'markdown_residue': 0,
    }
    text = raw

    # 1. Tool JSON (Claude inline + Ollama) -- FIRST because nested patterns may embed others
    for pat in (_TOOL_JSON_NESTED, _TOOL_JSON_FIELD, _TOOL_CALLS_OLLAMA):
        n = len(pat.findall(text))
        if n:
            strips['tool_json'] += n
            text = pat.sub('', text)
    if _TOOL_JSON_LEAD.search(text):
        strips['tool_json'] += 1
        text = _TOOL_JSON_LEAD.sub('', text)

    # 2. Context / knowledge envelopes
    for pat in (_CONTEXT_ENVELOPE, _KNOWLEDGE_ENVELOPE):
        n = len(pat.findall(text))
        if n:
            strips['context_envelope'] += n
            text = pat.sub('', text)

    # 3. Judgment sentinel (forward-compat for Phase 5)
    n = len(_JUDGMENT_SENTINEL.findall(text))
    if n:
        strips['judgment_sentinel'] += n
        text = _JUDGMENT_SENTINEL.sub('', text)

    # 4. Escalation sentinel (consolidates two inline strip sites)
    n = len(_ESCALATION_SENTINEL.findall(text))
    if n:
        strips['escalation_sentinel'] += n
        text = _ESCALATION_SENTINEL.sub('', text)

    # 5. Markdown residue -- LAST (cleanup pass for what prior strips left behind)
    for pat, repl in ((_MARKDOWN_BOLD, r'\1'), (_MARKDOWN_ITALIC, r'\1')):
        n = len(pat.findall(text))
        if n:
            strips['markdown_residue'] += n
            text = pat.sub(repl, text)
    lead_hits = len(_MARKDOWN_LEAD.findall(text))
    if lead_hits:
        strips['markdown_residue'] += lead_hits
        text = _MARKDOWN_LEAD.sub('', text)

    text = text.strip()
    applied = any(v > 0 for v in strips.values())

    return SanitizeResult(
        text=text,
        raw_length=len(raw),
        sanitized_length=len(text),
        strips=strips,
        applied=applied,
    )


def sanitize_to_provenance(raw: str):
    """Convenience: returns (sanitized_text, provenance_dict for 'sanitized' key)."""
    r = sanitize_output(raw)
    return r.text, {
        'applied': r.applied,
        'strips': r.strips,
        'raw_length': r.raw_length,
        'sanitized_length': r.sanitized_length,
    }
