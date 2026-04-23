"""Phase 4 sanitizer unit tests -- spec section 5, 12 cases.

Each test pins one of: a strip category, a counter, or a contract.
"""
from ai_operator.sanitize.output import sanitize_output, sanitize_to_provenance


def test_01_clean_prose_is_passthrough():
    r = sanitize_output("The weather in Denver today is mild.")
    assert r.applied is False
    assert r.text == "The weather in Denver today is mild."
    assert all(v == 0 for v in r.strips.values())


def test_02_tool_json_nested_brace():
    raw = 'Preamble {"args": {"q": "x"}} trailing prose.'
    r = sanitize_output(raw)
    assert r.applied is True
    assert r.strips['tool_json'] >= 1
    assert '{"args"' not in r.text


def test_03_tool_json_with_tool_field():
    raw = 'intro {"tool": "search"} outro'
    r = sanitize_output(raw)
    assert r.strips['tool_json'] >= 1
    assert '"tool"' not in r.text


def test_04_tool_json_leading_orphan_brace():
    raw = '}  Here is the real answer.'
    r = sanitize_output(raw)
    assert r.strips['tool_json'] >= 1
    assert r.text.startswith('Here')


def test_05_ollama_tool_calls_multiline():
    raw = 'prefix "tool_calls": [\n  {"name": "x"}\n] suffix'
    r = sanitize_output(raw)
    assert r.strips['tool_json'] >= 1
    assert 'tool_calls' not in r.text


def test_06_context_envelope_stripped():
    raw = 'before [CONTEXT]retrieved memory blob\nmulti line[/CONTEXT] after'
    r = sanitize_output(raw)
    assert r.strips['context_envelope'] == 1
    assert '[CONTEXT]' not in r.text
    assert 'retrieved memory' not in r.text


def test_07_knowledge_envelope_stripped():
    raw = 'intro [KNOWLEDGE]fact A\nfact B[/KNOWLEDGE] outro'
    r = sanitize_output(raw)
    assert r.strips['context_envelope'] == 1
    assert '[KNOWLEDGE]' not in r.text
    assert 'fact A' not in r.text


def test_08_judgment_sentinel_stripped():
    raw = 'answer [[JUDGMENT:low_confidence]] body continues.'
    r = sanitize_output(raw)
    assert r.strips['judgment_sentinel'] == 1
    assert '[[JUDGMENT' not in r.text


def test_09_escalation_sentinel_sonnet_and_opus():
    raw1 = 'needs help [[ESCALATE:sonnet]] end'
    r1 = sanitize_output(raw1)
    assert r1.strips['escalation_sentinel'] == 1
    assert '[[ESCALATE' not in r1.text

    raw2 = 'deeper [[ESCALATE:opus]] end'
    r2 = sanitize_output(raw2)
    assert r2.strips['escalation_sentinel'] == 1
    assert '[[ESCALATE' not in r2.text


def test_10_markdown_bold_and_italic_unwrapped():
    raw = 'This is **bold** and this is *italic* text.'
    r = sanitize_output(raw)
    assert r.strips['markdown_residue'] >= 2
    assert '**' not in r.text
    assert 'bold' in r.text
    assert 'italic' in r.text


def test_11_markdown_leading_stars_removed():
    raw = '* one\n* two\n* three'
    r = sanitize_output(raw)
    # Italic regex pair-eats some stars; lead-stars catches what's left.
    # Both count into markdown_residue. Counter varies by input shape.
    assert r.strips['markdown_residue'] >= 1
    assert '*' not in r.text
    for line in r.text.splitlines():
        assert not line.lstrip().startswith('*')


def test_12_counter_shape_and_provenance_contract():
    raw = '[CONTEXT]x[/CONTEXT] body [[ESCALATE:sonnet]] **b**'
    r = sanitize_output(raw)
    # counter shape: exactly the 5 spec keys, all int
    expected_keys = {'tool_json', 'context_envelope', 'judgment_sentinel',
                     'escalation_sentinel', 'markdown_residue'}
    assert set(r.strips.keys()) == expected_keys
    for v in r.strips.values():
        assert isinstance(v, int)
    assert r.raw_length == len(raw)
    assert r.sanitized_length == len(r.text)
    assert r.applied is True

    # sanitize_to_provenance contract: 4-key dict, matches result
    text, prov = sanitize_to_provenance(raw)
    assert text == r.text
    assert set(prov.keys()) == {'applied', 'strips', 'raw_length', 'sanitized_length'}
    assert prov['applied'] is True
    assert prov['strips'] == r.strips
    assert prov['raw_length'] == r.raw_length
    assert prov['sanitized_length'] == r.sanitized_length
