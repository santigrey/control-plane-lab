from __future__ import annotations

import os
import time
import requests
from ai_operator.tools.chains import CHAIN_TEMPLATES
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




def _plan_and_execute_handler(args):
    chain_name = args.get('chain', '')
    params = args.get('params', {})
    if chain_name not in CHAIN_TEMPLATES:
        return {'ok': False, 'error': f'Unknown chain: {chain_name}. Available: {list(CHAIN_TEMPLATES.keys())}'}
    template = CHAIN_TEMPLATES[chain_name]
    results = []
    context = dict(params)
    registry = default_registry()
    for i, step in enumerate(template['steps']):
        tool_name = step['tool']
        filled_args = {}
        for k, v in step.get('args_template', {}).items():
            if isinstance(v, str) and v.startswith('{') and v.endswith('}'):
                filled_args[k] = context.get(v[1:-1], v)
            else:
                filled_args[k] = v
        try:
            result = registry.run(tool_name, filled_args)
            results.append({'step': i, 'tool': tool_name, 'result': result})
            if isinstance(result, dict):
                for rk, rv in result.items():
                    if isinstance(rv, str) and len(rv) < 500:
                        context[f'step_{i}_{rk}'] = rv
                if 'synthesis' in result:
                    context['research_result'] = result['synthesis'][:500]
                if 'results' in result and isinstance(result['results'], list) and result['results']:
                    first = result['results'][0]
                    if isinstance(first, dict) and 'company' in first:
                        context['top_company'] = first['company']
        except Exception as e:
            results.append({'step': i, 'tool': tool_name, 'error': str(e)})
    return {'ok': True, 'chain': chain_name, 'steps_executed': len(results), 'results': results}

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
        name='plan_and_execute',
        description='Execute a pre-defined multi-step tool chain. Chains: research_and_draft (params: company, role), job_search_deep (params: query, location), full_status_report (no params). Use for complex requests needing multiple tools.',
        schema={'type': 'object', 'properties': {'chain': {'type': 'string'}, 'params': {'type': 'object'}}, 'required': ['chain'], 'additionalProperties': False},
        handler=_plan_and_execute_handler,
    ))

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
