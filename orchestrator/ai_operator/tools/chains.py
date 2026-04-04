"""Dynamic chain composition engine + static chain shortcuts."""

import json
import time
import logging

log = logging.getLogger('chains')

MAX_STEPS = 10
STEP_TIMEOUT = 30
TOTAL_TIMEOUT = 120

CHAIN_TEMPLATES = {
    'research_and_draft': {
        'description': 'Research a company then draft an outreach message',
        'steps': [
            {'tool': 'research_topic', 'args_template': {'topic': '{company}'}},
            {'tool': 'draft_message', 'args_template': {'role': '{role}', 'company': '{company}', 'context': '{research_result}'}},
        ]
    },
    'job_search_deep': {
        'description': 'Search for jobs then research top match',
        'steps': [
            {'tool': 'job_search_jsearch', 'args_template': {'what': '{query}', 'where': '{location}'}},
            {'tool': 'research_topic', 'args_template': {'topic': '{top_company} company culture engineering team'}},
        ]
    },
    'full_status_report': {
        'description': 'Get complete situational awareness',
        'steps': [
            {'tool': 'get_live_context', 'args_template': {}},
            {'tool': 'get_emails', 'args_template': {}},
            {'tool': 'get_calendar', 'args_template': {}},
            {'tool': 'get_job_pipeline', 'args_template': {}},
            {'tool': 'get_system_status', 'args_template': {}},
        ]
    },
    'morning_briefing': {
        'description': 'Morning briefing: context, calendar, emails, pipeline, then summarize',
        'steps': [
            {'tool': 'get_live_context', 'args_template': {}},
            {'tool': 'get_calendar', 'args_template': {}},
            {'tool': 'get_emails', 'args_template': {}},
            {'tool': 'get_job_pipeline', 'args_template': {}},
            {'tool': 'summarize', 'args_template': {'text': '{chain_results}', 'instruction': 'Create a concise morning briefing. Lead with schedule, then urgent emails, then pipeline status. 2-3 paragraphs max.'}},
        ]
    },
    'class_prep': {
        'description': 'Prepare for Per Scholas class: list materials, read lesson, summarize key points',
        'steps': [
            {'tool': 'read_course_material', 'args_template': {'action': 'list'}},
            {'tool': 'read_course_material', 'args_template': {'action': 'read', 'filename': '{filename}'}},
            {'tool': 'summarize', 'args_template': {'text': '{chain_results}', 'instruction': 'Extract the key concepts, vocabulary, and likely discussion points from this lesson. Format as a study guide.'}},
        ]
    },
    'weekly_review': {
        'description': 'Weekly review: pipeline stats, context, recent wins, summarize week',
        'steps': [
            {'tool': 'get_job_pipeline', 'args_template': {}},
            {'tool': 'get_live_context', 'args_template': {}},
            {'tool': 'memory_recall', 'args_template': {'query': 'recent accomplishments wins completed', 'top_k': 5}},
            {'tool': 'summarize', 'args_template': {'text': '{chain_results}', 'instruction': 'Write a weekly review: what was accomplished, pipeline progress, and top 3 priorities for next week.'}},
        ]
    },
    'application_followup': {
        'description': 'Check pipeline for stale applications and draft followup strategy',
        'steps': [
            {'tool': 'get_job_pipeline', 'args_template': {}},
            {'tool': 'summarize', 'args_template': {'text': '{chain_results}', 'instruction': 'Identify applications older than 7 days with no response. For each, suggest whether to follow up, move on, or escalate. Be specific.'}},
        ]
    },
    'company_deep_dive': {
        'description': 'Deep research on a company: web research, careers page, fit analysis',
        'steps': [
            {'tool': 'research_topic', 'args_template': {'topic': '{company}'}},
            {'tool': 'web_fetch', 'args_template': {'url': '{careers_url}'}},
            {'tool': 'summarize', 'args_template': {'text': '{chain_results}', 'instruction': 'Analyze this company as a potential employer for an AI Platform Engineer. Assess: culture, tech stack, team size, growth signals, and fit with infrastructure + AI background.'}},
        ]
    },
}


def _build_tool_inventory(registry):
    """Build a compact tool inventory string for the planner prompt."""
    lines = []
    for name, spec in sorted(registry.list().items()):
        if name == 'plan_and_execute':
            continue
        props = spec.schema.get('properties', {})
        req = spec.schema.get('required', [])
        args_desc = ', '.join(
            f"{k} ({'required' if k in req else 'optional'})"
            for k in props
        )
        lines.append(f"- {name}: {spec.description[:100]}. Args: [{args_desc}]")
    return '\n'.join(lines)


def _extract_json_array(text):
    """Extract a JSON array from LLM output, tolerant of surrounding text."""
    import re
    text = text.strip()
    m = re.search(r'\[\s*\{', text)
    if not m:
        return None
    start = m.start()
    depth = 0
    for i in range(start, len(text)):
        if text[i] == '[':
            depth += 1
        elif text[i] == ']':
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(text[start:i+1])
                except json.JSONDecodeError:
                    return None
    return None


PLANNER_SYSTEM = """You are a task planner for an AI assistant named Alexandra. Given a goal, output a JSON array of steps to accomplish it.

Each step must be: {"tool": "<tool_name>", "args": {<args>}, "label": "<what this step does>"}

Rules:
- Use ONLY tools from the Available Tools list below
- Maximum 10 steps. Prefer fewer steps when possible.
- Output ONLY the JSON array. No explanation, no markdown, no commentary.
- Args must match the tool's required/optional parameters exactly.
- If a step needs output from a previous step, use the placeholder {step_N_result} where N is the 0-based step index.
- Use {chain_results} to reference all accumulated results.
- Always end multi-step chains with a summarize step to synthesize results.
- If the goal is simple and needs only 1 tool, use 1 step."""


def build_dynamic_plan(goal, registry, live_context=''):
    """Use Ollama to generate a step-by-step plan from a goal."""
    from ai_operator.inference.ollama import ollama_chat

    inventory = _build_tool_inventory(registry)
    user_prompt = f"Available Tools:\n{inventory}\n"
    if live_context:
        user_prompt += f"\nCurrent Context:\n{live_context}\n"
    user_prompt += f"\nGoal: {goal}"

    try:
        raw = ollama_chat(PLANNER_SYSTEM, user_prompt)
        plan = _extract_json_array(raw)
        if not plan:
            log.warning(f"Planner returned unparseable output: {raw[:200]}")
            return None
        if len(plan) > MAX_STEPS:
            plan = plan[:MAX_STEPS]
        for step in plan:
            if 'tool' not in step or 'args' not in step:
                log.warning(f"Invalid step in plan: {step}")
                return None
        return plan
    except Exception as e:
        log.error(f"Planner failed: {e}")
        return None


def _fill_template_args(args, context):
    """Replace {placeholder} references in args with context values."""
    filled = {}
    for k, v in args.items():
        if isinstance(v, str) and '{' in v and '}' in v:
            for ck, cv in context.items():
                placeholder = '{' + ck + '}'
                if placeholder in v:
                    if isinstance(cv, str):
                        v = v.replace(placeholder, cv)
                    else:
                        v = v.replace(placeholder, json.dumps(cv, default=str)[:3000])
            filled[k] = v
        else:
            filled[k] = v
    return filled


def execute_chain(plan, registry, params=None):
    """Execute a plan (list of steps). Returns results dict."""
    context = dict(params or {})
    results = []
    chain_start = time.time()

    for i, step in enumerate(plan):
        if time.time() - chain_start > TOTAL_TIMEOUT:
            results.append({'step': i, 'tool': step.get('tool', '?'), 'error': 'Chain timeout exceeded'})
            break

        tool_name = step['tool']
        raw_args = step.get('args', step.get('args_template', {}))
        label = step.get('label', f'Step {i}: {tool_name}')

        filled_args = _fill_template_args(raw_args, context)

        log.info(f"Chain step {i}: {tool_name} args={list(filled_args.keys())}")

        try:
            step_start = time.time()
            result = registry.run(tool_name, filled_args)
            elapsed = round(time.time() - step_start, 2)
            results.append({'step': i, 'tool': tool_name, 'label': label, 'result': result, 'elapsed_s': elapsed})

            # Feed result into context for next steps
            if isinstance(result, dict):
                for rk, rv in result.items():
                    if isinstance(rv, str) and len(rv) < 2000:
                        context[f'step_{i}_{rk}'] = rv
                if 'synthesis' in result:
                    context['research_result'] = result['synthesis'][:2000]
                if 'summary' in result:
                    context['last_summary'] = result['summary'][:2000]
                if 'results' in result and isinstance(result['results'], list) and result['results']:
                    first = result['results'][0]
                    if isinstance(first, dict) and 'company' in first:
                        context['top_company'] = first['company']

            # Build accumulated chain_results
            context[f'step_{i}_result'] = json.dumps(result, default=str)[:3000]

        except Exception as e:
            results.append({'step': i, 'tool': tool_name, 'label': label, 'error': str(e)})
            context[f'step_{i}_result'] = f'ERROR: {e}'

    # Build final chain_results summary
    parts = []
    for r in results:
        if 'error' in r:
            parts.append(f"[{r['tool']}] ERROR: {r['error']}")
        else:
            parts.append(f"[{r['tool']}] {json.dumps(r.get('result', {}), default=str)[:1500]}")
    context['chain_results'] = '\n---\n'.join(parts)

    total_time = round(time.time() - chain_start, 2)
    return {
        'ok': True,
        'steps_executed': len(results),
        'total_time_s': total_time,
        'results': results,
        'chain_results_summary': context.get('chain_results', '')[:5000]
    }
