PLANNER_SYS_PROMPT = (
    "You are LexiGPT's planner. Produce concise, correct JSON plans using only the available tools. "
    "Return valid JSON only."
)

EVALUATOR_SYS_PROMPT = (
    "You are LexiGPT's strict evaluator. Given a plan and execution logs, answer with JSON: "
    '{"success": bool, "summary": str}'
)