"""Pre-defined multi-step tool chain templates."""

CHAIN_TEMPLATES = {
    'research_and_draft': {
        'description': 'Research a company then draft an outreach message',
        'steps': [
            {'tool': 'research_topic', 'args_template': {'topic': '{company}'}},
            {'tool': 'draft_message', 'args_template': {'role': '{role}', 'company': '{company}', 'context': '{research_result}'}},
        ]
    },
    'job_search_deep': {
        'description': 'Search for jobs using both engines then research top match',
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
}
