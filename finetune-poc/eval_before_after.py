"""Before/after LoRA comparison for Llama 3.1 8B + SQuAD POC."""
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel
import time

BASE_MODEL = "meta-llama/Llama-3.1-8B"
ADAPTER_PATH = "/workspace/Automodel/checkpoints/epoch_0_step_19/model"

SQUAD_PROMPTS = [
    {
        "context": "The Apollo 11 mission, launched on July 16, 1969, was the first crewed mission to land on the Moon. Commander Neil Armstrong and lunar module pilot Buzz Aldrin landed the Apollo Lunar Module Eagle on July 20, 1969. Armstrong became the first person to step onto the lunar surface six hours and 39 minutes later.",
        "question": "Who was the first person to walk on the moon?"
    },
    {
        "context": "The Great Barrier Reef is the world's largest coral reef system, composed of over 2,900 individual reefs and 900 islands stretching for over 2,300 kilometres over an area of approximately 344,400 square kilometres. The reef is located in the Coral Sea, off the coast of Queensland, Australia.",
        "question": "How many individual reefs make up the Great Barrier Reef?"
    },
    {
        "context": "Python is a high-level programming language created by Guido van Rossum and first released in 1991. It emphasizes code readability with its notable use of significant indentation. Python is dynamically typed and garbage-collected. It supports multiple programming paradigms, including structured, object-oriented, and functional programming.",
        "question": "Who created the Python programming language?"
    }
]

OPEN_PROMPTS = [
    "Write a haiku about machine learning.",
    "Explain quantum entanglement in one sentence.",
    "What's the best way to learn a new language?"
]

def format_squad(ctx, q):
    return f"Context: {ctx}\n\nQuestion: {q}\n\nAnswer:"

def load_base():
    print("Loading BASE Llama 3.1 8B...", flush=True)
    tok = AutoTokenizer.from_pretrained(BASE_MODEL)
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
    model = AutoModelForCausalLM.from_pretrained(BASE_MODEL, dtype=torch.bfloat16, device_map="cuda")
    model.eval()
    return tok, model

def load_lora(base_tok, base_model):
    print("Attaching LoRA adapter from checkpoint...", flush=True)
    model = PeftModel.from_pretrained(base_model, ADAPTER_PATH)
    model.eval()
    return model

def generate(tok, model, prompt, max_new=80):
    inputs = tok(prompt, return_tensors="pt").to("cuda")
    t0 = time.time()
    with torch.no_grad():
        out = model.generate(**inputs, max_new_tokens=max_new, do_sample=False, pad_token_id=tok.eos_token_id)
    elapsed = time.time() - t0
    full = tok.decode(out[0], skip_special_tokens=True)
    generated = full[len(prompt):].strip()
    return generated, elapsed

def main():
    tok, base = load_base()
    print("\n" + "="*80, flush=True)
    print("BASE MODEL --- Llama 3.1 8B (no fine-tuning)", flush=True)
    print("="*80, flush=True)
    for i, p in enumerate(SQUAD_PROMPTS):
        prompt = format_squad(p["context"], p["question"])
        out, t = generate(tok, base, prompt, max_new=60)
        print(f"\n[SQuAD {i+1}] Q: {p['question']}", flush=True)
        print(f"Base ({t:.1f}s): {out}", flush=True)
    for i, p in enumerate(OPEN_PROMPTS):
        out, t = generate(tok, base, p, max_new=80)
        print(f"\n[Open {i+1}] {p}", flush=True)
        print(f"Base ({t:.1f}s): {out}", flush=True)
    lora_model = load_lora(tok, base)
    print("\n" + "="*80, flush=True)
    print("LoRA MODEL --- Llama 3.1 8B + SQuAD LoRA adapter (20 steps)", flush=True)
    print("="*80, flush=True)
    for i, p in enumerate(SQUAD_PROMPTS):
        prompt = format_squad(p["context"], p["question"])
        out, t = generate(tok, lora_model, prompt, max_new=60)
        print(f"\n[SQuAD {i+1}] Q: {p['question']}", flush=True)
        print(f"LoRA ({t:.1f}s): {out}", flush=True)
    for i, p in enumerate(OPEN_PROMPTS):
        out, t = generate(tok, lora_model, p, max_new=80)
        print(f"\n[Open {i+1}] {p}", flush=True)
        print(f"LoRA ({t:.1f}s): {out}", flush=True)
    print("\n" + "="*80, flush=True)
    print("COMPARISON COMPLETE", flush=True)
    print("="*80, flush=True)

if __name__ == "__main__":
    main()
