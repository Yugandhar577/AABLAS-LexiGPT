def draft_plan(goal: str) -> Plan:
    # Escape any braces in goal to prevent format() interpretation errors
    safe_goal = goal.replace('{', '{{').replace('}', '}}')
    try:
        prompt = PLANNER_PROMPT_TEMPLATE.format(goal=safe_goal) + PLANNER_PROMPT_APPEND
    except Exception as e:
        print(f"[ERROR] Format failed: {e}")
        print(f"[ERROR] Template snippet: {PLANNER_PROMPT_TEMPLATE[:200]}")
        print(f"[ERROR] safe_goal: {safe_goal[:100]}")
        raise
    raw = llm_chat(PLANNER_SYS_PROMPT, prompt)
    # Emit the raw planner output as an event for observability
    try:
        emit_event({"type": "planner_output", "raw": raw, "timestamp": int(time.time())})
    except Exception:
        pass
    def _extract_json_block(s: str) -> Optional[str]:
