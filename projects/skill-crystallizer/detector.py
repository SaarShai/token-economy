def detect_task_completion(transcript_events) -> dict:
    """Detect task completion based on recent transcript events."""
    if not isinstance(transcript_events, list):
        return {"completed": False, "confidence": 0.0, "reason": "invalid_type"}
    if not transcript_events:
        return {"completed": False, "confidence": 0.0, "reason": "empty_input"}
    limit = 20
    events = transcript_events[-limit:] if len(transcript_events) > limit else transcript_events
    positive_words = {'done', 'great', 'works', 'ship', 'good', 'finished', 'complete'}
    test_patterns = ['pytest', 'npm test', 'make test', 'go test', 'mvn test']
    commit_patterns = ['git commit', 'git push', 'git push origin']
    score = 0
    reasons = []
    for event in events:
        text = event.lower() if isinstance(event, str) else str(event).lower()
        if any(word in text for word in positive_words):
            score += 1
            reasons.append('positive_close_word')
        if any(pattern in text for pattern in test_patterns):
            score += 2
            reasons.append('successful_test')
        if any(pattern in text for pattern in commit_patterns):
            score += 3
            reasons.append('commit_detected')
    completed = score >= 3
    confidence = min(1.0, score / 5.0)
    reason = '; '.join(reasons) if reasons else 'no_signals'
    result = {"completed": completed, "confidence": confidence, "reason": reason}

    return result
