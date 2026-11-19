from promptguard.auditor import _matches


def test_substring_any_still_works():
    rule = {"any": ["write code"]}
    assert _matches(rule, "please write code now", "please write code now")


def test_word_any_requires_boundary():
    rule = {"word_any": ["fix"]}
    assert _matches(rule, "please fix the bug", "please fix the bug")
    assert not _matches(rule, "prefix the suffix", "prefix the suffix")


def test_regex_any():
    rule = {"regex_any": [r"\bPG0\d{2}\b"]}
    assert _matches(rule, "see PG012 here", "see PG012 here")
    assert not _matches(rule, "see PG here", "see PG here")


def test_invalid_regex_fail_closed_for_positive_key():
    rule = {"regex_any": ["[unterminated"]}
    assert not _matches(rule, "anything", "anything")


def test_word_missing_any_blocks_when_present():
    rule = {"word_any": ["deploy"], "word_missing_any": ["rollback"]}
    assert _matches(rule, "deploy to prod", "deploy to prod")
    assert not _matches(rule, "deploy with rollback", "deploy with rollback")


def test_word_also_any_requires_both_words():
    rule = {"word_any": ["deploy"], "word_also_any": ["production"]}
    assert _matches(rule, "deploy to production", "deploy to production")
    assert not _matches(rule, "deploy the docs", "deploy the docs")


def test_regex_also_any_requires_both_patterns():
    rule = {"regex_any": [r"deploy"], "regex_also_any": [r"prod(uction)?"]}
    assert _matches(rule, "deploy to prod", "deploy to prod")
    assert not _matches(rule, "deploy the docs", "deploy the docs")


def test_regex_missing_any_blocks_when_present():
    rule = {"regex_any": [r"deploy"], "regex_missing_any": [r"roll\s?back"]}
    assert _matches(rule, "deploy to prod", "deploy to prod")
    assert not _matches(rule, "deploy with a roll back plan", "deploy with a roll back plan")
