from freshness import assess_answer, significant_tokens


def test_significant_tokens_removes_common_stop_words():
    tokens = significant_tokens("The latest stable Python release is Python 3.13")
    assert "python" in tokens
    assert "latest" in tokens
    assert "the" not in tokens


def test_no_sources_returns_unable_to_verify():
    result = assess_answer("Python 3.13 is the latest release.", "", [])
    assert result["verdict"] == "Unable to verify"
    assert result["overlap_score"] == 0.0


def test_high_overlap_is_not_labelled_as_proof():
    answer = "Python 3.13 is the latest stable Python release available today."
    summary = "Python 3.13 is the latest stable Python release available today."
    results = [{"content": "Python 3.13 is the latest stable release."}]
    result = assess_answer(answer, summary, results)
    assert result["verdict"] == "No obvious mismatch"
    assert 0.0 <= result["overlap_score"] <= 1.0
    assert "does not prove" in result["reason"]


def test_low_overlap_requests_review():
    answer = "The Acme cloud database version 7.4 supports encrypted backups and multi-region failover."
    summary = "The company announced a new mobile photography feature for its consumer application."
    results = [{"content": "New smartphone camera features and photo sharing updates."}]
    result = assess_answer(answer, summary, results)
    assert result["verdict"] == "Potential mismatch"
