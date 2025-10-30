"""
services/agent_service.py
Planner -> Executor -> Evaluator agent service.

Depends on:
- services.ollama_services.llm_chat
- rag.retriever.Retriever
- services.docgen_service (for doc gen calls)
"""
import json
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from services.ollama_services import llm_chat
from rag.retriever import Retriever
# from services.docgen_service import generate_document
from utils.prompts import PLANNER_SYS_PROMPT, EVALUATOR_SYS_PROMPT

# Tool registry: name -> callable
# Each tool receives a dict input and returns {"ok": bool, "output": Any, "logs": str}
def _tool_read_file(args: Dict[str, Any]) -> Dict[str, Any]:
    path = args.get("path")
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            txt = f.read()
        return {"ok": True, "output": txt, "logs": f"read {len(txt)} chars"}
    except Exception as e:
        return {"ok": False, "output": None, "logs": str(e)}


def _tool_regex_extract(args: Dict[str, Any]) -> Dict[str, Any]:
    import re

    text = args.get("text", "")
    pattern = args.get("pattern", "")
    try:
        matches = re.findall(pattern, text, flags=re.MULTILINE)
        return {"ok": True, "output": matches, "logs": f"{len(matches)} matches"}
    except re.error as e:
        return {"ok": False, "output": None, "logs": f"regex error: {e}"}


RETRIEVER = Retriever()  # local retriever; uses vector DB if configured


def _tool_rag_search(args: Dict[str, Any]) -> Dict[str, Any]:
    q = args.get("query", "")
    hits = RETRIEVER.search(q, top_k=args.get("top_k", 3))
    return {"ok": True, "output": hits, "logs": f"returned {len(hits)} hits"}


# def _tool_doc_generate(args: Dict[str, Any]) -> Dict[str, Any]:
#     # generate_document returns text or dict
#     try:
#         doc = generate_document(args.get("template"), args.get("fields", {}))
#         return {"ok": True, "output": doc, "logs": "generated document"}
#     except Exception as e:
#         return {"ok": False, "output": None, "logs": str(e)}


TOOL_MAP = {
    "read_file": _tool_read_file,
    "regex_extract": _tool_regex_extract,
    "rag_search": _tool_rag_search,
    # "doc_generate": _tool_doc_generate,
}


# --- Plan schema ---
class PlanStep(BaseModel):
    step_id: int
    title: str
    tool: str
    input: Dict[str, Any] = Field(default_factory=dict)
    expectations: Optional[str] = ""


class Plan(BaseModel):
    goal: str
    rationale: str
    steps: List[PlanStep]
    success_criteria: List[str] = Field(default_factory=list)
    max_iterations: int = 6


# --- Execution schema ---
class StepLog(BaseModel):
    step_id: int
    title: str
    tool: str
    ok: bool
    logs: str
    output_preview: str


class RunResult(BaseModel):
    success: bool
    plan: Plan
    steps: List[StepLog]
    summary: str


# --- Planner: ask LLM to produce JSON plan ---
PLANNER_PROMPT_TEMPLATE = """
GOAL:
{goal}

TOOL INVENTORY:
- read_file: Read a local text file. input={{path:str}}
- regex_extract: Apply regex. input={{text:str, pattern:str}}
- rag_search: Search knowledge base. input={{query:str, top_k:int}}
- doc_generate: Generate a document. input={{template:str, fields:dict}}

Return ONLY valid JSON matching the schema:
{{ "goal": str, "rationale": str, "steps": [{{"step_id": int, "title": str, "tool": str, "input": dict, "expectations": str}}], "success_criteria": [str], "max_iterations": int }}
Rules: Use only listed tools or 'reason'. Prefer 2-5 steps. step_id starts at 1.
"""

def draft_plan(goal: str) -> Plan:
    prompt = PLANNER_PROMPT_TEMPLATE.format(goal=goal)
    raw = llm_chat(PLANNER_SYS_PROMPT, prompt)
    try:
        data = json.loads(raw)
        return Plan(**data)
    except Exception as e:
        # Try a quick fallback: ask for JSON again (simple retry)
        raw2 = llm_chat(PLANNER_SYS_PROMPT, "Please return the same plan as valid JSON only.\n\n" + raw)
        try:
            data = json.loads(raw2)
            return Plan(**data)
        except Exception as e2:
            raise RuntimeError(f"Planner failed to produce valid JSON.\nFirst:{e}\nRaw1:{raw}\nRaw2:{raw2}")


def execute_plan(plan: Plan) -> RunResult:
    logs: List[StepLog] = []

    for step in plan.steps[: plan.max_iterations]:
        if step.tool == "reason":
            logs.append(
                StepLog(
                    step_id=step.step_id,
                    title=step.title,
                    tool="reason",
                    ok=True,
                    logs="internal reasoning",
                    output_preview="(no external action)",
                )
            )
            continue

        tool_fn = TOOL_MAP.get(step.tool)
        if not tool_fn:
            logs.append(
                StepLog(
                    step_id=step.step_id,
                    title=step.title,
                    tool=step.tool,
                    ok=False,
                    logs=f"unknown tool {step.tool}",
                    output_preview="",
                )
            )
            continue

        res = tool_fn(step.input)
        preview = str(res.get("output", ""))[:400]
        logs.append(
            StepLog(
                step_id=step.step_id,
                title=step.title,
                tool=step.tool,
                ok=bool(res.get("ok", False)),
                logs=str(res.get("logs", "")),
                output_preview=preview,
            )
        )

    # Ask evaluator LLM
    eval_prompt = f"PLAN:\n{plan.model_dump_json(indent=2)}\n\nLOGS:\n{json.dumps([l.dict() for l in logs], indent=2)}\n\nReturn compact JSON: {{'success': bool, 'summary': str}}"
    raw = llm_chat(EVALUATOR_SYS_PROMPT, eval_prompt)
    try:
        report = json.loads(raw)
    except Exception:
        report = {"success": False, "summary": f"Evaluator JSON parse failed. Raw: {raw}"}

    return RunResult(success=bool(report.get("success", False)), plan=plan, steps=logs, summary=str(report.get("summary", "")))


# --- Public API for routes ---
def plan_and_run(goal: str) -> Dict[str, Any]:
    plan = draft_plan(goal)
    result = execute_plan(plan)
    return {"plan": plan.dict(), "result": result.dict()}
