from __future__ import annotations
from ai_operator.iot_security import enforce_tier, classify_tier

import os
import time
import requests
from ai_operator.tools.chains import CHAIN_TEMPLATES

_telegram_rate = []
from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional


@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    # Minimal schema: {"type":"object","properties":{...},"required":[...],"additionalProperties":False}
    schema: Dict[str, Any]
    handler: Callable[[Dict[str, Any]], Dict[str, Any]]


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: Dict[str, ToolSpec] = {}

    def register(self, tool: ToolSpec) -> None:
        if tool.name in self._tools:
            raise ValueError(f"Tool already registered: {tool.name}")
        self._tools[tool.name] = tool

    def get(self, name: str) -> Optional[ToolSpec]:
        return self._tools.get(name)

    def list(self) -> Dict[str, ToolSpec]:
        return dict(self._tools)

    def validate_args(self, schema: Dict[str, Any], args: Dict[str, Any]) -> None:
        # Lightweight validation (no jsonschema dependency)
        if schema.get("type") != "object":
            raise ValueError("Tool schema must be type=object")

        required = schema.get("required") or []
        props = schema.get("properties") or {}
        additional_ok = schema.get("additionalProperties", True)

        for k in required:
            if k not in args:
                raise ValueError(f"Missing required arg: {k}")

        if not additional_ok:
            for k in args.keys():
                if k not in props:
                    raise ValueError(f"Unexpected arg: {k}")

        for k, v in args.items():
            if k not in props:
                continue
            expected_type = props[k].get("type")
            if expected_type == "string" and not isinstance(v, str):
                raise ValueError(f"Arg '{k}' must be string")
            if expected_type == "integer" and not isinstance(v, int):
                raise ValueError(f"Arg '{k}' must be integer")
            if expected_type == "number" and not isinstance(v, (int, float)):
                raise ValueError(f"Arg '{k}' must be number")
            if expected_type == "boolean" and not isinstance(v, bool):
                raise ValueError(f"Arg '{k}' must be boolean")

    def run(self, name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        tool = self.get(name)
        if not tool:
            raise ValueError(f"Unknown tool: {name}")
        self.validate_args(tool.schema, args)
        return tool.handler(args)


# ---- built-in tools ----

def _ping_handler(args: Dict[str, Any]) -> Dict[str, Any]:
    message = args.get("message", "pong")
    return {"ok": True, "tool": "ping", "echo": message}


def _sleep_handler(args: Dict[str, Any]) -> Dict[str, Any]:
    seconds = int(args.get("seconds", 1))
    if seconds < 0 or seconds > 60:
        raise ValueError("seconds must be between 0 and 60")
    time.sleep(seconds)
    return {"ok": True, "tool": "sleep", "slept": seconds}


def _web_search_handler(args: Dict[str, Any]) -> Dict[str, Any]:
    query = args["query"]
    n = int(args.get("n", 5))
    try:
        from ddgs import DDGS as DDGS2
        raw = list(DDGS2().text(query, max_results=n))
        results = [
            {"title": r.get("title", ""), "url": r.get("href", ""), "snippet": r.get("body", "")}
            for r in raw
        ]
        return {"ok": True, "tool": "web_search", "query": query, "results": results}
    except Exception as e:
        return {"ok": False, "tool": "web_search", "error": str(e)}

def _job_search_handler(args: Dict[str, Any]) -> Dict[str, Any]:
    app_id = os.environ.get("ADZUNA_APP_ID", "")
    app_key = os.environ.get("ADZUNA_APP_KEY", "")
    if not app_id or not app_key:
        return {"ok": False, "tool": "job_search", "error": "ADZUNA_APP_ID or ADZUNA_APP_KEY not set"}
    what = args["what"]
    where = args.get("where", "Denver")
    n = int(args.get("n", 5))
    try:
        r = requests.get(
            "https://api.adzuna.com/v1/api/jobs/us/search/1",
            params={
                "app_id": app_id,
                "app_key": app_key,
                "what": what,
                "where": where,
                "results_per_page": n,
                "content-type": "application/json",
            },
            timeout=10,
        )
        r.raise_for_status()
        data = r.json()
        results = [
            {
                "title": job.get("title", ""),
                "company": job.get("company", {}).get("display_name", ""),
                "location": job.get("location", {}).get("display_name", ""),
                "description": job.get("description", "")[:300],
                "url": job.get("redirect_url", ""),
                "salary_min": job.get("salary_min"),
                "salary_max": job.get("salary_max"),
            }
            for job in data.get("results", [])
        ]
        return {"ok": True, "tool": "job_search", "query": what, "location": where, "results": results}
    except Exception as e:
        return {"ok": False, "tool": "job_search", "error": str(e)}

def _jsearch_handler(args: Dict[str, Any]) -> Dict[str, Any]:
    api_key = os.environ.get("JSEARCH_API_KEY", "")
    if not api_key:
        return {"ok": False, "tool": "job_search_jsearch", "error": "JSEARCH_API_KEY not set"}
    what = args["what"]
    where = args.get("where", "Denver")
    remote_only = args.get("remote_only", False)
    n = int(args.get("n", 10))
    query = f"{what} in {where}"
    try:
        params = {
            "query": query,
            "page": "1",
            "num_pages": "1",
            "country": "us",
            "date_posted": "month",
        }
        if remote_only:
            params["work_from_home"] = "true"
        r = requests.get(
            "https://jsearch.p.rapidapi.com/search",
            headers={
                "x-rapidapi-key": api_key,
                "x-rapidapi-host": "jsearch.p.rapidapi.com",
                "Content-Type": "application/json",
            },
            params=params,
            timeout=15,
        )
        r.raise_for_status()
        data = r.json()
        jobs = data.get("data", [])[:n]
        results = [
            {
                "title": j.get("job_title", ""),
                "company": j.get("employer_name", ""),
                "location": f"{j.get('job_city','')}, {j.get('job_state','')}".strip(", "),
                "description": (j.get("job_description") or "")[:300],
                "url": j.get("job_apply_link") or j.get("job_google_link", ""),
                "remote": j.get("job_is_remote", False),
                "posted": j.get("job_posted_at_datetime_utc", ""),
                "salary_min": j.get("job_min_salary"),
                "salary_max": j.get("job_max_salary"),
            }
            for j in jobs
        ]
        return {"ok": True, "tool": "job_search_jsearch", "query": query, "results": results}
    except Exception as e:
        return {"ok": False, "tool": "job_search_jsearch", "error": str(e)}
def _draft_message_handler(args):
    from ai_operator.inference.ollama import ollama_chat
    role = args["role"]
    company = args["company"]
    context = args.get("context", "")
    prompt = (
        f"Write a concise, direct outreach message for this role:\n"
        f"Role: {role}\nCompany: {company}\nContext: {context}\n\n"
        f"Keep it under 150 words. Professional but not stiff. "
        f"Mention the candidate's background in AI infrastructure and systems engineering. "
        f"Output only the message text."
    )
    draft = ollama_chat(
        system_prompt="You are a professional outreach writer. Output only the message.",
        user_prompt=prompt,
    )
    return {"ok": True, "tool": "draft_message", "draft": draft}


def _web_fetch_handler(args):
    url = args["url"]
    try:
        from bs4 import BeautifulSoup
        headers = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
            tag.decompose()
        text = soup.get_text(separator=" ", strip=True)
        import re; text = re.sub(r"\s+", " ", text).strip()
        return {"ok": True, "tool": "web_fetch", "url": url, "text": text[:3000]}
    except Exception as e:
        return {"ok": False, "tool": "web_fetch", "url": url, "error": str(e)}

def _research_topic_handler(args):
    topic = args["topic"]
    max_results = int(args.get("max_results", 3))
    try:
        search_result = _web_search_handler({"query": topic, "n": max_results})
        results = search_result.get("results", [])
        sources = []
        for r in results:
            url = r.get("url", "")
            if not url:
                continue
            fetch = _web_fetch_handler({"url": url})
            page_text = fetch.get("text", r.get("snippet", "")) if fetch.get("ok") else r.get("snippet", "")
            sources.append({"url": url, "title": r.get("title", ""), "summary": page_text[:500]})
        # Fallback: if search returned nothing, try fetching the topic URL directly
        if not sources:
            slug = topic.lower().replace(" ", "")
            for candidate_url in [f"https://www.{slug}.com", f"https://{slug}.com", f"https://www.{slug}.space"]:
                fetch = _web_fetch_handler({"url": candidate_url})
                if fetch.get("ok"):
                    sources.append({"url": candidate_url, "title": topic, "summary": fetch.get("text", "")[:500]})
                    break
        parts = ["[" + s["title"] + "] " + s["summary"][:200] for s in sources]
        synthesis = "Research on " + repr(topic) + ": " + " | ".join(parts)
        return {"ok": True, "tool": "research_topic", "topic": topic, "sources": sources, "synthesis": synthesis[:3000]}
    except Exception as e:
        return {"ok": False, "tool": "research_topic", "topic": topic, "error": str(e)}

def _get_emails_handler(args: Dict[str, Any]) -> Dict[str, Any]:
    import subprocess, json as _json
    r = subprocess.run(
        ['/usr/bin/python3', '-c',
         'import sys, json; sys.path.insert(0,"/home/jes/control-plane"); '
         'from google_readers import get_recent_emails; '
         'print(json.dumps(get_recent_emails(10)))'],
        capture_output=True, text=True, timeout=20)
    if r.returncode != 0:
        return {"ok": False, "error": r.stderr.strip()}
    return _json.loads(r.stdout.strip())


def _get_calendar_handler(args: Dict[str, Any]) -> Dict[str, Any]:
    import subprocess, json as _json
    r = subprocess.run(
        ['/usr/bin/python3', '-c',
         'import sys, json; sys.path.insert(0,"/home/jes/control-plane"); '
         'from google_readers import get_todays_calendar; '
         'print(json.dumps(get_todays_calendar()))'],
        capture_output=True, text=True, timeout=20)
    if r.returncode != 0:
        return {"ok": False, "error": r.stderr.strip()}
    return _json.loads(r.stdout.strip())



def _get_upcoming_calendar_handler(args):
    import subprocess, json as _json
    days = args.get('days', 7)
    r = subprocess.run(
        ['/usr/bin/python3', '-c',
         f'import sys, json; sys.path.insert(0,"/home/jes/control-plane"); '
         f'from google_readers import get_upcoming_calendar; '
         f'print(json.dumps(get_upcoming_calendar(days={int(days)})))'],
        capture_output=True, text=True, timeout=20)
    if r.returncode != 0:
        return {"ok": False, "error": r.stderr.strip()}
    return _json.loads(r.stdout.strip())

def _create_calendar_event_handler(args: Dict[str, Any]) -> Dict[str, Any]:
    import subprocess, json as _json
    snippet = (
        'import sys, json; sys.path.insert(0,"/home/jes/control-plane"); '
        'from google_readers import create_calendar_event; '
        'print(json.dumps(create_calendar_event(**json.loads(sys.stdin.read()))))'
    )
    r = subprocess.run(
        ['/usr/bin/python3', '-c', snippet],
        input=_json.dumps(args), capture_output=True, text=True, timeout=20)
    if r.returncode != 0:
        return {"ok": False, "error": r.stderr.strip()}
    result = _json.loads(r.stdout.strip())
    result["ok"] = True
    return result

def _get_system_status_handler(args):
    import subprocess as _sp, urllib.request as _ur, json as _jj
    r = {}
    try:
        with _ur.urlopen("http://localhost:8000/healthz", timeout=5) as _resp:
            h = _jj.loads(_resp.read())
        r["orchestrator"] = h.get("status", "unknown")
        d = h.get("details", {})
        r["api"] = d.get("api", "?")
        r["postgres"] = d.get("postgres", "?")
        r["ollama"] = d.get("ollama", "?")
        r["worker"] = d.get("worker", {}).get("status", "?")
    except Exception as e:
        r["orchestrator"] = str(e)
    r["services"] = {}
    for s in ["orchestrator", "alexandra-telegram", "recruiter-watcher"]:
        try:
            r["services"][s] = _sp.check_output(["systemctl","is-active",s], text=True, timeout=5).strip()
        except:
            r["services"][s] = "unknown"
    try:
        disk = _sp.check_output(["df","-h","/"], text=True, timeout=5).split("\n")[1].split()
        r["disk"] = {"size":disk[1],"used":disk[2],"avail":disk[3],"pct":disk[4]}
    except:
        r["disk"] = "unavailable"
    try:
        mem = _sp.check_output(["free","-h"], text=True, timeout=5).split("\n")[1].split()
        r["memory"] = {"total":mem[1],"used":mem[2],"free":mem[3]}
    except:
        r["memory"] = "unavailable"
    try:
        ts = _jj.loads(_sp.check_output(["tailscale","status","--json"], text=True, timeout=5))
        peers = ts.get("Peer", {})
        r["tailscale"] = {
            "ip": ts.get("Self",{}).get("TailscaleIPs",["?"])[0],
            "peers_online": sum(1 for p in peers.values() if not p.get("Offline",True)),
            "peers_total": len(peers)
        }
    except:
        r["tailscale"] = "unavailable"
    r["ok"] = True

def _get_linkedin_profile_handler(args: Dict[str, Any]) -> Dict[str, Any]:
    import json as _json
    profile_path = '/home/jes/control-plane/data/linkedin_profile.json'
    section = args.get('section', 'all')
    try:
        with open(profile_path, 'r') as f:
            data = _json.load(f)
        if section == 'all':
            return {"ok": True, "tool": "get_linkedin_profile", "profile": data}
        elif section in data:
            return {"ok": True, "tool": "get_linkedin_profile", "section": section, "data": data[section]}
        else:
            return {"ok": True, "tool": "get_linkedin_profile", "profile": data, "note": f"section '{section}' not found, returning all"}
    except Exception as e:
        return {"ok": False, "tool": "get_linkedin_profile", "error": str(e)}

    return r


def _get_live_context_handler(args: Dict[str, Any]) -> Dict[str, Any]:
    from concurrent.futures import ThreadPoolExecutor, as_completed
    from datetime import datetime as _dt
    import xml.etree.ElementTree as _ET
    from dotenv import dotenv_values as _dv
    _env = _dv('/home/jes/control-plane/.env')

    def _get_time():
        import pytz
        denver = pytz.timezone('America/Denver')
        now = _dt.now(denver)
        return now.strftime('%A %B %d, %Y at %I:%M %p MST')

    def _get_weather():
        key = _env.get('OPENWEATHER_API_KEY', '')
        if not key:
            return 'weather unavailable (no API key)'
        try:
            r = requests.get(
                f'https://api.openweathermap.org/data/2.5/weather?q=Denver,CO,US&appid={key}&units=imperial',
                timeout=5)
            r.raise_for_status()
            d = r.json()
            temp = round(d['main']['temp'])
            feels = round(d['main']['feels_like'])
            desc = d['weather'][0]['description']
            humidity = d['main']['humidity']
            wind = round(d['wind']['speed'])
            return f'Denver: {temp}F (feels {feels}F), {desc}, humidity {humidity}%, wind {wind}mph'
        except Exception as e:
            return f'weather error: {e}'

    def _get_market():
        tickers = [
            ('S&P 500', 'https://stooq.com/q/l/?s=^spx&f=o,c'),
            ('NASDAQ', 'https://stooq.com/q/l/?s=^ndq&f=o,c'),
            ('BTC', 'https://stooq.com/q/l/?s=btc.v&f=o,c'),
        ]
        parts = []
        for name, url in tickers:
            try:
                r = requests.get(url, timeout=5)
                r.raise_for_status()
                vals = r.text.strip().split(',')
                open_p, close_p = float(vals[0]), float(vals[1])
                chg = ((close_p - open_p) / open_p) * 100
                sign = '+' if chg >= 0 else ''
                if name == 'BTC':
                    parts.append(f'BTC: ${close_p:,.0f} ({sign}{chg:.1f}%)')
                else:
                    parts.append(f'{name}: {close_p:,.0f} ({sign}{chg:.1f}%)')
            except Exception:
                parts.append(f'{name}: unavailable')
        return ' | '.join(parts)

    def _get_news():
        for url in [
            'https://feeds.feedburner.com/reuters/topNews',
            'https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml',
        ]:
            try:
                r = requests.get(url, timeout=5)
                r.raise_for_status()
                root = _ET.fromstring(r.content)
                headlines = []
                for item in root.iter('item'):
                    t = item.find('title')
                    if t is not None and t.text:
                        headlines.append(t.text.strip())
                    if len(headlines) >= 5:
                        break
                if headlines:
                    return headlines
            except Exception:
                continue
        return ['news unavailable']

    res = {}
    with ThreadPoolExecutor(max_workers=4) as ex:
        futs = {
            ex.submit(_get_time): 'time',
            ex.submit(_get_weather): 'weather',
            ex.submit(_get_market): 'market',
            ex.submit(_get_news): 'headlines',
        }
        for fut in as_completed(futs, timeout=10):
            k = futs[fut]
            try:
                res[k] = fut.result()
            except Exception as e:
                res[k] = f'{k} error: {e}'

    return {
        'ok': True,
        'time': res.get('time', 'unknown'),
        'weather': res.get('weather', 'unknown'),
        'market': res.get('market', 'unknown'),
        'headlines': res.get('headlines', []),
    }




def _read_course_material_handler(args):
    import os, subprocess
    BASE = '/home/jes/control-plane/course_materials'
    action = args.get('action', 'list')
    if action == 'list':
        files = []
        for f in sorted(os.listdir(BASE)):
            fp = os.path.join(BASE, f)
            if os.path.isfile(fp):
                files.append({'name': f, 'size_kb': round(os.path.getsize(fp)/1024,1)})
        return {'ok': True, 'action': 'list', 'files': files, 'count': len(files)}
    elif action == 'read':
        fn = os.path.basename(args.get('filename',''))
        if not fn: return {'ok': False, 'error': 'filename required'}
        fp = os.path.join(BASE, fn)
        if not os.path.exists(fp): return {'ok': False, 'error': f'Not found: {fn}'}
        ext = os.path.splitext(fn)[1].lower()
        if ext in ('.md','.txt','.csv','.json','.py','.js','.html'):
            c = open(fp,'r',errors='replace').read()
            if len(c)>8000: c = c[:8000]+'\n[TRUNCATED]'
            return {'ok':True,'action':'read','filename':fn,'content':c}
        elif ext == '.pdf':
            r = subprocess.run(['pdftotext',fp,'-'],capture_output=True,text=True,timeout=15)
            if r.returncode==0 and r.stdout.strip():
                return {'ok':True,'action':'read','filename':fn,'content':r.stdout.strip()[:8000]}
            return {'ok':False,'error':'PDF extract failed'}
        elif ext in ('.png','.jpg','.jpeg'):
            return {'ok':True,'action':'read','filename':fn,'content':'[IMAGE]','type':'image'}
        return {'ok':False,'error':f'Unsupported: {ext}'}
    elif action == 'search':
        query = args.get('query','').lower()
        if not query: return {'ok':False,'error':'query required'}
        matches = []
        for f in os.listdir(BASE):
            fp = os.path.join(BASE, f)
            ext = os.path.splitext(f)[1].lower()
            if ext in ('.md','.txt','.csv','.json','.py','.js','.html'):
                try:
                    content = open(fp,'r',errors='replace').read()
                    if query in content.lower() or query in f.lower():
                        lines = [l.strip() for l in content.split('\n') if query in l.lower()][:5]
                        matches.append({'filename':f,'matching_lines':lines})
                except: pass
            elif query in f.lower():
                matches.append({'filename':f,'matching_lines':['(filename match)']})
        return {'ok':True,'action':'search','query':query,'matches':matches}
    return {'ok':False,'error':f'Unknown action: {action}. Use list, read, or search.'}


def _plan_and_execute_handler(args):
    from ai_operator.tools.chains import CHAIN_TEMPLATES, build_dynamic_plan, execute_chain
    chain_name = args.get('chain', '')
    goal = args.get('goal', '')
    params = args.get('params', {})
    registry = default_registry()
    # Fast path: static chain by name
    if chain_name and chain_name in CHAIN_TEMPLATES:
        template = CHAIN_TEMPLATES[chain_name]
        return execute_chain(template['steps'], registry, params)
    # Dynamic path: goal-based planning
    if goal:
        plan = build_dynamic_plan(goal, registry)
        if not plan:
            return {'ok': False, 'error': 'Planner could not generate a valid plan for this goal.'}
        return execute_chain(plan, registry, params)
    # No chain or goal
    avail = list(CHAIN_TEMPLATES.keys())
    return {'ok': False, 'error': f'Provide chain (static) or goal (dynamic). Static chains: {avail}'}


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
    if path and not os.path.isabs(path):
        path = os.path.join("/home/jes/control-plane", path)
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
    if path and not os.path.isabs(path):
        path = os.path.join("/home/jes/control-plane", path)
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
    if path and not os.path.isabs(path):
        path = os.path.join("/home/jes/control-plane", path)
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



# ---- Home Assistant tools ----

def _ha_request(method, path, json_body=None):
    from dotenv import dotenv_values
    env = dotenv_values('/home/jes/control-plane/.env')
    token = env.get('HA_TOKEN') or os.getenv('HA_TOKEN', '')
    url = env.get('HA_URL', 'http://localhost:8123')
    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    if method == 'GET':
        resp = requests.get(f'{url}{path}', headers=headers, timeout=10)
    else:
        resp = requests.post(f'{url}{path}', headers=headers, json=json_body or {}, timeout=10)
    resp.raise_for_status()
    return resp.json() if resp.text else {"ok": True}


def _home_status_handler(args):
    try:
        states = _ha_request('GET', '/api/states')
        df = args.get('domain', '')
        result = {}
        for s in states:
            eid = s['entity_id']
            d = eid.split('.')[0]
            if df and d != df:
                continue
            if d in ('light','switch','climate','camera','media_player','alarm_control_panel','sensor','binary_sensor','siren'):
                if d not in result:
                    result[d] = []
                e = {'entity_id': eid, 'state': s['state'], 'name': s.get('attributes',{}).get('friendly_name', eid)}
                a = s.get('attributes', {})
                if d == 'light' and 'brightness' in a:
                    e['brightness'] = a['brightness']
                if d == 'climate':
                    e['current_temp'] = a.get('current_temperature')
                    e['target_temp'] = a.get('temperature')
                if d == 'sensor' and 'temperature' in eid:
                    e['unit'] = a.get('unit_of_measurement','')
                if d == 'media_player':
                    e['source'] = a.get('source')
                result[d].append(e)
        return {"ok": True, "tool": "home_status", "devices": result}
    except Exception as ex:
        return {"ok": False, "tool": "home_status", "error": str(ex)}


def _home_control_handler(args):
    try:
        eid = args['entity_id']
        act = args['action']
        ext = args.get('extras', {})
        # --- IoT Security: Tier Enforcement ---
        allowed, reason = enforce_tier(eid, act, ext)
        if not allowed:
            return {"ok": False, "tool": "home_control", "blocked": True, "tier": classify_tier(eid, act), "reason": reason}
        # --- End Tier Enforcement ---
        # Validate entity exists first
        try:
            _ha_request('GET', f'/api/states/{eid}')
        except Exception:
            return {"ok": False, "tool": "home_control", "error": f"Entity '{eid}' not found in Home Assistant. Call home_status first to get valid entity IDs."}
        dom = eid.split('.')[0]
        smap = {
            'turn_on': f'{dom}/turn_on', 'turn_off': f'{dom}/turn_off', 'toggle': f'{dom}/toggle',
            'set_temperature': 'climate/set_temperature', 'set_hvac_mode': 'climate/set_hvac_mode',
            'media_play': 'media_player/media_play', 'media_pause': 'media_player/media_pause',
            'media_next': 'media_player/media_next_track', 'volume_set': 'media_player/volume_set',
            'arm_away': 'alarm_control_panel/alarm_arm_away', 'disarm': 'alarm_control_panel/alarm_disarm',
            'select_source': 'media_player/select_source',
        }
        svc = smap.get(act)
        if not svc:
            return {"ok": False, "tool": "home_control", "error": f"Unknown action: {act}"}
        body = {'entity_id': eid}
        ext = args.get('extras', {})
        if isinstance(ext, dict):
            body.update(ext)
        _ha_request("POST", f"/api/services/{svc}", body)
        time.sleep(1.2)  # allow local IoT devices (WiZ UDP) to update state
        new_state = _ha_request('GET', f'/api/states/{eid}')
        return {"ok": True, "tool": "home_control", "entity_id": eid, "action": act, "new_state": new_state.get('state', 'unknown'), "friendly_name": new_state.get('attributes', {}).get('friendly_name', eid)}
    except Exception as ex:
        return {"ok": False, "tool": "home_control", "error": str(ex)}


def _home_cameras_handler(args):
    # TIER 3 HARD BLOCK: Camera access always requires explicit approval.
    # Do NOT remove without Sloan's approval.
    return {
        "ok": False,
        "tool": "home_cameras",
        "blocked": True,
        "tier": 3,
        "reason": "This command requires the security approval system which is not yet deployed. Blocked for safety. Ask Sloan to approve manually."
    }

def default_registry() -> ToolRegistry:
    r = ToolRegistry()

    r.register(
        ToolSpec(
            name="ping",
            description="Connectivity sanity tool: echoes a message.",
            schema={
                "type": "object",
                "properties": {"message": {"type": "string"}},
                "required": [],
                "additionalProperties": False,
            },
            handler=_ping_handler,
        )
    )

    r.register(
        ToolSpec(
            name="sleep",
            description="Sleep for N seconds (testing lock visibility).",
            schema={
                "type": "object",
                "properties": {"seconds": {"type": "integer"}},
                "required": ["seconds"],
                "additionalProperties": False,
            },
            handler=_sleep_handler,
        )
    )

    r.register(ToolSpec(
        name="web_search",
        description="Search the web for current information. Use for job listings, company research, or news.",
        schema={
            "type": "object",
            "properties": {"query": {"type": "string"}},
            "required": ["query"],
            "additionalProperties": False,
        },
        handler=_web_search_handler,
    ))

    r.register(ToolSpec(
        name="draft_message",
        description="Draft a professional outreach message for a job role at a company.",
        schema={
            "type": "object",
            "properties": {
                "role": {"type": "string"},
                "company": {"type": "string"},
                "context": {"type": "string"},
            },
            "required": ["role", "company"],
            "additionalProperties": False,
        },
        handler=_draft_message_handler,
    ))

    r.register(ToolSpec(
        name="job_search",
        description="Search for real job listings by title and location using Adzuna. Use this for any career or job-finding task.",
        schema={
            "type": "object",
            "properties": {
                "what": {"type": "string"},
                "where": {"type": "string"},
            },
            "required": ["what"],
            "additionalProperties": False,
        },
        handler=_job_search_handler,
    ))

    r.register(ToolSpec(
        name="job_search_jsearch",
        description="Search for real job listings using JSearch (LinkedIn, Indeed, Glassdoor). Use this for job searches. Args: what (job title, required), where (location, default Denver), remote_only (boolean, default false).",
        schema={
            "type": "object",
            "properties": {
                "what": {"type": "string"},
                "where": {"type": "string"},
                "remote_only": {"type": "boolean"},
            },
            "required": ["what"],
            "additionalProperties": False,
        },
        handler=_jsearch_handler,
    ))

    r.register(ToolSpec(
        name="web_fetch",
        description="Fetch and extract readable text from a URL. Use to read company sites, articles, or job pages.",
        schema={"type": "object", "properties": {"url": {"type": "string"}},
                "required": ["url"], "additionalProperties": False},
        handler=_web_fetch_handler,
    ))

    r.register(ToolSpec(
        name="research_topic",
        description="Research a topic: searches the web and fetches top pages. Returns sources and synthesis. Use for company research, tech stack analysis, or deep-dive queries.",
        schema={"type": "object", "properties": {"topic": {"type": "string"}, "max_results": {"type": "integer"}},
                "required": ["topic"], "additionalProperties": False},
        handler=_research_topic_handler,
    ))

    r.register(ToolSpec(
        name="get_emails",
        description="Get James's recent emails from Gmail. Use this when asked about emails, inbox, or messages. Returns sender, subject, snippet and date for last 24 hours.",
        schema={"type": "object", "properties": {}, "required": [], "additionalProperties": True},
        handler=_get_emails_handler,
    ))

    r.register(ToolSpec(
        name="get_calendar",
        description="Get James's calendar events for today. Use this when asked about schedule, meetings, or calendar. Returns event summary, start time, end time and location.",
        schema={"type": "object", "properties": {}, "required": [], "additionalProperties": True},
        handler=_get_calendar_handler,
    ))


    r.register(ToolSpec(
        name="get_upcoming_calendar",
        description="Get James's calendar events for the next N days. Use this to verify appointments, check upcoming schedule, or look beyond today. Args: days (int, default 14).",
        schema={"type": "object", "properties": {"days": {"type": "integer", "default": 14}}, "required": [], "additionalProperties": False},
        handler=_get_upcoming_calendar_handler,
    ))
    r.register(ToolSpec(
        name="create_calendar_event",
        description="Create a Google Calendar event. Args: summary (required), start_time (ISO, required), end_time (ISO, required), description, location, timezone (default America/Denver), recurrence (RFC5545 RRULE).",
        schema={
            "type": "object",
            "properties": {
                "summary": {"type": "string"},
                "start_time": {"type": "string"},
                "end_time": {"type": "string"},
                "description": {"type": "string"},
                "location": {"type": "string"},
                "timezone": {"type": "string"},
                "recurrence": {"type": "string"},
            },
            "required": ["summary", "start_time", "end_time"],
            "additionalProperties": False,
        },
        handler=_create_calendar_event_handler,
    ))

    r.register(ToolSpec(
        name="get_live_context",
        description="Get current time, weather in Denver, top news headlines, and stock market prices. Use this when James asks about time, weather, news, stocks, or wants a situational awareness update.",
        schema={"type": "object", "properties": {}, "required": [], "additionalProperties": False},
        handler=_get_live_context_handler,
    ))

    r.register(ToolSpec(
        name="get_system_status",
        description="Get live health of the Alexandra homelab stack: orchestrator status, API, postgres, ollama, worker, systemd services (orchestrator, alexandra-telegram, recruiter-watcher), disk usage, memory, and Tailscale network. Use when James asks about system status, stack health, server check, services, or how things are running.",
        schema={"type":"object","properties":{},"required":[],"additionalProperties":True},
        handler=_get_system_status_handler,
    ))


    def _get_job_pipeline_handler(args):
        import psycopg2 as _pg2
        from datetime import datetime as _dt, timezone as _tz
        conn = _pg2.connect('postgresql://admin:adminpass@127.0.0.1:5432/controlplane')
        cur = conn.cursor()
        cur.execute('SELECT status, COUNT(*) FROM job_applications GROUP BY status ORDER BY COUNT(*) DESC')
        counts = {r[0]: r[1] for r in cur.fetchall()}
        cur.execute('''SELECT company, role, status, last_updated FROM job_applications
                       ORDER BY last_updated DESC LIMIT 10''')
        recent = [{'company': r[0], 'role': r[1], 'status': r[2],
                   'days_ago': (_dt.now(_tz.utc) - r[3]).days} for r in cur.fetchall()]
        cur.execute('''SELECT company, role, last_updated FROM job_applications
                       WHERE status='applied'
                       ORDER BY last_updated ASC LIMIT 5''')
        pending_followup = [{'company': r[0], 'role': r[1],
                              'days_since_apply': (_dt.now(_tz.utc) - r[2]).days}
                             for r in cur.fetchall()]
        conn.close()
        return {'ok': True, 'counts': counts, 'recent': recent, 'pending_followup': pending_followup}

    r.register(ToolSpec(
        name='get_job_pipeline',
        description='Get James job search pipeline status: application counts by status, 10 most recent applications, and applications pending follow-up. Use when James asks about job applications, interview status, pipeline, follow-ups, or how the job search is going.',
        schema={'type':'object','properties':{},'required':[],'additionalProperties':True},
        handler=_get_job_pipeline_handler,
    ))


    r.register(ToolSpec(
        name='read_course_material',
        description='Access Per Scholas course materials. Actions: list (show files), read (read file by filename), search (search keyword). Use for homework, study, class questions.',
        schema={'type':'object','properties':{'action':{'type':'string'},'filename':{'type':'string'},'query':{'type':'string'}},'required':['action'],'additionalProperties':False},
        handler=_read_course_material_handler,
    ))

    r.register(ToolSpec(
        name='plan_and_execute',
        description='Execute multi-step tool chains. Use chain for static shortcuts (morning_briefing, full_status_report, class_prep, weekly_review, application_followup, company_deep_dive, research_and_draft, job_search_deep) OR goal for dynamic planning (any natural language goal). Args: chain OR goal (at least one required), params (optional).',
        schema={'type': 'object', 'properties': {'chain': {'type': 'string'}, 'goal': {'type': 'string'}, 'params': {'type': 'object'}}, 'required': [], 'additionalProperties': False},
        handler=_plan_and_execute_handler,
    ))


    r.register(ToolSpec(name="summarize", description="Summarize text with optional analysis instruction. Args: text (required, max 8000 chars), instruction (optional). Uses ollama.", schema={"type": "object", "properties": {"text": {"type": "string"}, "instruction": {"type": "string"}}, "required": ["text"], "additionalProperties": False}, handler=_summarize_handler))
    r.register(ToolSpec(name="memory_recall", description="Search semantic memory via pgvector. Args: query (required), top_k (optional, default 5).", schema={"type": "object", "properties": {"query": {"type": "string"}, "top_k": {"type": "integer"}}, "required": ["query"], "additionalProperties": False}, handler=_memory_recall_handler))
    r.register(ToolSpec(name="memory_save", description="Save content to semantic memory. Args: content (required, max 500 chars), source (optional).", schema={"type": "object", "properties": {"content": {"type": "string"}, "source": {"type": "string"}}, "required": ["content"], "additionalProperties": False}, handler=_memory_save_handler))
    r.register(ToolSpec(name="send_telegram", description="Send a message via Telegram bot. Args: message (required). Rate limited 5/60s.", schema={"type": "object", "properties": {"message": {"type": "string"}}, "required": ["message"], "additionalProperties": False}, handler=_send_telegram_handler))
    r.register(ToolSpec(name="read_file", description="Read a file from /home/jes/control-plane/ (jailed). Args: path (required). Max 50KB.", schema={"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"], "additionalProperties": False}, handler=_read_file_handler))
    r.register(ToolSpec(name="write_file", description="Write to /home/jes/control-plane/ (jailed). Args: path, content (max 50KB). Rejects .env, .key, .pem, .git/.", schema={"type": "object", "properties": {"path": {"type": "string"}, "content": {"type": "string"}}, "required": ["path", "content"], "additionalProperties": False}, handler=_write_file_handler))
    r.register(ToolSpec(name="get_linkedin_profile", description="Get James's LinkedIn profile data. Args: section (optional: 'experience', 'education', 'certifications', 'projects', 'recent_activity', or 'all'). Returns structured profile data.", schema={"type": "object", "properties": {"section": {"type": "string"}}, "required": [], "additionalProperties": False}, handler=_get_linkedin_profile_handler))
    r.register(ToolSpec(name="list_files", description="List files in /home/jes/control-plane/ (jailed). Args: path (optional). Max 100 entries.", schema={"type": "object", "properties": {"path": {"type": "string"}}, "required": [], "additionalProperties": False}, handler=_list_files_handler))
    r.register(ToolSpec(name="home_status", description="Get status of all smart home devices. Optional: domain filter.", schema={"type": "object", "properties": {"domain": {"type": "string"}}, "required": [], "additionalProperties": False}, handler=_home_status_handler))
    r.register(ToolSpec(name="home_control", description="Control a smart home device. Args: entity_id, action (turn_on/off/toggle/set_temperature/media_play/pause/volume_set/arm_away/disarm), extras (optional dict).", schema={"type": "object", "properties": {"entity_id": {"type": "string"}, "action": {"type": "string"}, "extras": {"type": "object"}}, "required": ["entity_id", "action"], "additionalProperties": False}, handler=_home_control_handler))
    r.register(ToolSpec(name="home_cameras", description="Get status of all cameras (Blink, Tapo).", schema={"type": "object", "properties": {}, "required": [], "additionalProperties": False}, handler=_home_cameras_handler))


    return r


def run_tool_call(task_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compatibility entrypoint for worker runner "tool.call" tasks.
    Expected payload shape: {"tool": "<name>", "args": {...}}.
    """
    tool_name = payload.get("tool")
    if not isinstance(tool_name, str) or not tool_name.strip():
        raise ValueError("tool.call payload.tool must be a non-empty string")

    args = payload.get("args") or {}
    if not isinstance(args, dict):
        raise ValueError("tool.call payload.args must be an object")

    result = default_registry().run(tool_name, args)
    return {
        "ok": True,
        "kind": "tool.call",
        "task_id": task_id,
        "tool": tool_name,
        "args": args,
        "result": result,
    }


def execute_tool(name: str, args: Dict[str, Any]) -> Dict[str, Any]:
    return default_registry().run(name, args)
