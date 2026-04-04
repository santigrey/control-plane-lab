_telegram_rate = []

def _check_jail(resolved, tool_name):
    jail = "/home/jes/control-plane"
    if resolved != jail and not resolved.startswith(jail + "/"):
        return {"ok": False, "tool": tool_name, "error": f"Access denied: path must be within {jail}/"}
    return None

def _summarize_handler(args):
    from ai_operator.inference.ollama import ollama_chat
    text = args.get("text", "")
    instruction = args.get("instruction")
    text = text[:8000] if text else ""
    if not text.strip():
        return {"ok": False, "tool": "summarize", "error": "text cannot be empty"}
    try:
        system_prompt = "You are a concise analytical assistant. Follow the instruction precisely."
        if instruction:
            user_prompt = f"{instruction}\n\nText to analyze:\n{text}"
        else:
            user_prompt = f"Provide a concise summary of the following text:\n\n{text}"
        result = ollama_chat(system_prompt, user_prompt)
        if not result or not result.strip():
            return {"ok": False, "tool": "summarize", "error": "No response from model"}
        return {"ok": True, "tool": "summarize", "summary": result.strip()}
    except Exception as e:
        return {"ok": False, "tool": "summarize", "error": str(e)}

def _memory_recall_handler(args):
    import os, requests, psycopg
    query = args.get("query", "")
    top_k = int(args.get("top_k", 5))
    if not query or not query.strip():
        return {"ok": False, "tool": "memory_recall", "error": "query cannot be empty"}
    try:
        db_pass = os.getenv("CONTROLPLANE_DB_PASS", "adminpass")
        db_url = f"postgresql://admin:{db_pass}@127.0.0.1:5432/controlplane"
        embed_resp = requests.post("http://192.168.1.152:11434/api/embeddings", json={"model": "nomic-embed-text", "prompt": query}, timeout=30)
        embed_resp.raise_for_status()
        embedding = embed_resp.json().get("embedding")
        if not embedding:
            return {"ok": False, "tool": "memory_recall", "error": "Failed to embed query"}
        with psycopg.connect(db_url) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT content, source, created_at, 1 - (embedding <=> %s::vector) as similarity FROM memories ORDER BY embedding <=> %s::vector LIMIT %s", (embedding, embedding, top_k))
                rows = cur.fetchall()
        if not rows:
            return {"ok": True, "tool": "memory_recall", "query": query, "results": []}
        results = [{"content": r[0], "source": r[1], "created_at": r[2].isoformat() if r[2] else None, "similarity": round(float(r[3]), 3) if r[3] else 0} for r in rows]
        return {"ok": True, "tool": "memory_recall", "query": query, "results": results, "count": len(results)}
    except Exception as e:
        return {"ok": False, "tool": "memory_recall", "error": str(e)}

def _memory_save_handler(args):
    import os, requests, psycopg
    content = args.get("content", "")
    source = args.get("source", "alexandra_chain")
    content = content[:500] if content else ""
    if not content or not content.strip():
        return {"ok": False, "tool": "memory_save", "error": "content cannot be empty"}
    try:
        db_pass = os.getenv("CONTROLPLANE_DB_PASS", "adminpass")
        db_url = f"postgresql://admin:{db_pass}@127.0.0.1:5432/controlplane"
        embed_resp = requests.post("http://192.168.1.152:11434/api/embeddings", json={"model": "nomic-embed-text", "prompt": content}, timeout=30)
        embed_resp.raise_for_status()
        embedding = embed_resp.json().get("embedding")
        if not embedding:
            return {"ok": False, "tool": "memory_save", "error": "Failed to embed content"}
        with psycopg.connect(db_url) as conn:
            with conn.cursor() as cur:
                cur.execute("INSERT INTO memories (content, source, embedding) VALUES (%s, %s, %s::vector)", (content, source, embedding))
            conn.commit()
        return {"ok": True, "tool": "memory_save", "saved": True, "chars": len(content), "source": source}
    except Exception as e:
        return {"ok": False, "tool": "memory_save", "error": str(e)}

def _send_telegram_handler(args):
    import os, requests, time
    message = args.get("message", "")
    if not message or not message.strip():
        return {"ok": False, "tool": "send_telegram", "error": "message cannot be empty"}
    try:
        now = time.time()
        _telegram_rate[:] = [t for t in _telegram_rate if now - t < 60]
        if len(_telegram_rate) >= 5:
            return {"ok": False, "tool": "send_telegram", "error": "Rate limited: max 5 messages per 60 seconds"}
        _telegram_rate.append(now)
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        chat_id = os.getenv("TELEGRAM_CHAT_ID")
        if not bot_token or not chat_id:
            return {"ok": False, "tool": "send_telegram", "error": "TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not set"}
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {"chat_id": chat_id, "text": message}
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        result = response.json()
        if result.get("ok"):
            return {"ok": True, "tool": "send_telegram", "message_id": result.get("result", {}).get("message_id"), "sent": True}
        else:
            return {"ok": False, "tool": "send_telegram", "error": result.get("description", "Unknown error")}
    except Exception as e:
        return {"ok": False, "tool": "send_telegram", "error": str(e)}

def _read_file_handler(args):
    import os
    path = args.get("path", "")
    if not path or not path.strip():
        return {"ok": False, "tool": "read_file", "error": "path cannot be empty"}
    try:
        resolved = os.path.realpath(path)
        jail_err = _check_jail(resolved, "read_file")
        if jail_err:
            return jail_err
        if not os.path.isfile(resolved):
            return {"ok": False, "tool": "read_file", "error": f"Not found or not a file: {path}"}
        size = os.path.getsize(resolved)
        if size > 50000:
            return {"ok": False, "tool": "read_file", "error": f"File too large: {size} bytes (max 50KB)"}
        with open(resolved, "r", errors="replace") as f:
            content = f.read()
        return {"ok": True, "tool": "read_file", "path": resolved, "content": content, "size": len(content)}
    except Exception as e:
        return {"ok": False, "tool": "read_file", "error": str(e)}

def _write_file_handler(args):
    import os
    path = args.get("path", "")
    content = args.get("content", "")
    if not path or not path.strip():
        return {"ok": False, "tool": "write_file", "error": "path cannot be empty"}
    try:
        resolved = os.path.realpath(path)
        jail_err = _check_jail(resolved, "write_file")
        if jail_err:
            return jail_err
        jail = "/home/jes/control-plane"
        filename = os.path.basename(resolved)
        rel_path = resolved[len(jail) + 1:]
        forbidden_names = {".env", "google_credentials.json", "google_token.json"}
        if filename in forbidden_names:
            return {"ok": False, "tool": "write_file", "error": f"Access denied: cannot write to {filename}"}
        forbidden_extensions = {".key", ".pem"}
        _, ext = os.path.splitext(filename)
        if ext in forbidden_extensions:
            return {"ok": False, "tool": "write_file", "error": f"Access denied: cannot write {ext} files"}
        if rel_path.startswith(".git/") or "/.git/" in rel_path:
            return {"ok": False, "tool": "write_file", "error": "Access denied: cannot write to .git/"}
        if len(content) > 50000:
            return {"ok": False, "tool": "write_file", "error": f"Content too large: {len(content)} bytes (max 50KB)"}
        parent_dir = os.path.dirname(resolved)
        if parent_dir and not os.path.exists(parent_dir):
            os.makedirs(parent_dir, mode=0o755, exist_ok=True)
        with open(resolved, "w") as f:
            bytes_written = f.write(content)
        return {"ok": True, "tool": "write_file", "path": resolved, "bytes_written": bytes_written}
    except Exception as e:
        return {"ok": False, "tool": "write_file", "error": str(e)}

def _list_files_handler(args):
    import os
    path = args.get("path", "/home/jes/control-plane/")
    try:
        resolved = os.path.realpath(path)
        jail_err = _check_jail(resolved, "list_files")
        if jail_err:
            return jail_err
        if not os.path.isdir(resolved):
            return {"ok": False, "tool": "list_files", "error": f"Not a directory: {path}"}
        try:
            items = os.listdir(resolved)
        except PermissionError:
            return {"ok": False, "tool": "list_files", "error": f"Permission denied: {path}"}
        entries = []
        for item in items[:100]:
            item_path = os.path.join(resolved, item)
            try:
                is_file = os.path.isfile(item_path)
                size_kb = round(os.path.getsize(item_path) / 1024, 1) if is_file else 0
                entries.append({"name": item, "type": "file" if is_file else "dir", "size_kb": size_kb})
            except OSError:
                pass
        return {"ok": True, "tool": "list_files", "path": resolved, "entries": entries, "count": len(entries)}
    except Exception as e:
        return {"ok": False, "tool": "list_files", "error": str(e)}
