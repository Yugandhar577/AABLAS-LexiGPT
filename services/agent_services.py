"""
services/agent_service.py
Planner -> Executor -> Evaluator agent service.

Depends on:
- services.ollama_services.llm_chat
- rag.retriever.Retriever
- services.docgen_service (for doc gen calls)
"""
import json
import queue
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from services.ollama_services import llm_chat
from rag.retriever import Retriever
from services.docgen_services import generate_document
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

# Agent runtime hooks for streaming logs/events
LOG_PATH = Path("data/agent_logs.jsonl")
LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

# Queue that holds JSON-serialised events (strings). Consumers (SSE) will read from this.
AGENT_EVENT_QUEUE: "queue.Queue[str]" = queue.Queue()
# Stop event to signal running agents to halt
AGENT_STOP_EVENT = threading.Event()


def emit_event(obj: Dict[str, Any]) -> None:
    """Persist an event to disk (append JSONL) and enqueue it for SSE consumers.

    The object should be JSON-serialisable.
    """
    try:
        with LOG_PATH.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(obj, ensure_ascii=False) + "\n")
    except Exception:
        pass
    try:
        AGENT_EVENT_QUEUE.put(json.dumps(obj, ensure_ascii=False))
    except Exception:
        pass


def clear_agent_events_queue() -> None:
    """Remove any pending events from the queue."""
    try:
        while not AGENT_EVENT_QUEUE.empty():
            AGENT_EVENT_QUEUE.get_nowait()
    except Exception:
        pass


def _tool_rag_search(args: Dict[str, Any]) -> Dict[str, Any]:
    q = args.get("query", "")
    session_id = args.get("session_id")
    hits = RETRIEVER.search(q, top_k=args.get("top_k", 3), session_id=session_id)
    serialised = [hit.__dict__ for hit in hits]
    return {"ok": True, "output": serialised, "logs": f"returned {len(hits)} hits"}


def _tool_doc_generate(args: Dict[str, Any]) -> Dict[str, Any]:
    try:
        with open(r"c:\Users\Yugandhar Paulbudhe\Desktop\AABLAS - Copy\debug_docgen.log", "a") as f:
            f.write(f"\n[DEBUG] _tool_doc_generate received args: {json.dumps(args, indent=2)}\n")
        
        # args is either: (1) a dict with "payload"/"doc_payload" key, or (2) the payload itself with type/content
        payload = args.get("payload") or args.get("doc_payload")
        if not payload and isinstance(args, dict) and ("type" in args or "content" in args):
            # args IS the payload itself
            payload = args
        if not payload:
            payload = {}
        
        with open(r"c:\Users\Yugandhar Paulbudhe\Desktop\AABLAS - Copy\debug_docgen.log", "a") as f:
            f.write(f"[DEBUG] Extracted payload: {json.dumps(payload, indent=2)}\n")
        
        # Backwards-compatible: if a template string was provided, attempt to map
        if isinstance(payload, str):
            payload = {"type": "pdf", "title": payload, "content": []}

        file_path = generate_document(payload)
        print(f"[DEBUG] doc_generate created file: {file_path}")

        # Emit an event for file download so SSE clients can render a link
        try:
            emit_event({
                "type": "file_download",
                "filename": Path(file_path).name,
                "url": f"/api/docgen/download/{Path(file_path).name}",
                "timestamp": int(time.time()),
            })
            print(f"[DEBUG] file_download event emitted")
        except Exception as e:
            print(f"[DEBUG] emit_event failed: {e}")

        return {"ok": True, "output": file_path, "logs": "generated document"}
    except Exception as e:
        print(f"[DEBUG] doc_generate error: {e}")
        return {"ok": False, "output": None, "logs": str(e)}


TOOL_MAP = {
    "read_file": _tool_read_file,
    "regex_extract": _tool_regex_extract,
    "rag_search": _tool_rag_search,
    "doc_generate": _tool_doc_generate,
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
    next_steps: List[str] = Field(default_factory=list)


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

AVAILABLE TOOLS:

1. "reason": For internal reasoning steps. input={}
   Example: "reason" step for thinking about the problem.

2. "read_file": Read a local text file. 
   input={path:str}
   Example input: {"path": "documents/contract.txt"}

3. "regex_extract": Apply regex to text.
   input={text:str, pattern:str}
   Example input: {"text": "some text", "pattern": "\\d+"}

4. "rag_search": Search knowledge base for information.
   input={query:str, top_k:int}
   Example input: {"query": "rental agreement clauses", "top_k": 3}

5. "doc_generate": Generate and save a PDF/DOCX/XLSX/PPTX document.
   REQUIRED input format: {type:str, title:str, content:[objects]}
   - type: "pdf", "docx", "xlsx", or "pptx"
   - title: Document title string
   - content: Array of content blocks. Each block is ONE of:
     * {"h1": "Heading text"}
     * {"h2": "Subheading text"}
     * {"p": "Paragraph text"}
     * {"bullet": ["item1", "item2", "item3"]}
     * {"table": [["Header1", "Header2"], ["Row1Col1", "Row1Col2"]]}

   COMPLETE EXAMPLE doc_generate input:
   {"type": "pdf", "title": "Rental Agreement", "content": [
       {"h1": "RENTAL AGREEMENT"},
       {"h2": "Parties"},
       {"p": "This agreement is between John Smith (Landlord) and Jane Doe (Tenant)."},
       {"h2": "Property Details"},
       {"table": [["Item", "Value"], ["Address", "123 Main St"], ["Rent", "$2000/month"]]},
       {"h2": "Terms"},
       {"p": "The lease term is from January 1, 2024 to December 31, 2024."}
   ]}

Return ONLY valid JSON matching this exact schema:
{
  "goal": string,
  "rationale": string,  
  "steps": [
    {
      "step_id": number,
      "title": string,
      "tool": string (one of: "reason", "read_file", "regex_extract", "rag_search", "doc_generate"),
      "input": object,
      "expectations": string
    }
  ],
  "success_criteria": [string],
  "max_iterations": number
}

RULES:
- Use only the 5 listed tools or 'reason'
- Prefer 2-5 steps
- step_id must start at 1 and increment
- max_iterations MUST be >= number of steps (if you have 4 steps, max_iterations must be >= 4)
- For DOCUMENT GENERATION GOALS: Include a doc_generate step with COMPLETE, non-empty content array
- Output ONLY valid JSON, no explanations or code fences
"""

# Encourage the planner to include 3 actionable next steps in the output
PLANNER_PROMPT_APPEND = (
    "\nADDITIONAL REQUIREMENT: Include a key 'next_steps' which is an array of 3 concise, actionable follow-up steps the agent should take after this plan completes. "
    "Each entry should be a short imperative sentence."
)

def draft_plan(goal: str) -> Plan:
    # Use string replace instead of .format() to avoid format placeholder interpretation errors
    prompt = PLANNER_PROMPT_TEMPLATE.replace('{goal}', goal) + PLANNER_PROMPT_APPEND
    raw = llm_chat(PLANNER_SYS_PROMPT, prompt)
    # Emit the raw planner output as an event for observability
    try:
        emit_event({"type": "planner_output", "raw": raw, "timestamp": int(time.time())})
    except Exception:
        pass
    def _extract_json_block(s: str) -> Optional[str]:
        # Try fenced code block first
        if not s or not isinstance(s, str):
            return None
        import re

        m = re.search(r"```json\s*(\{[\s\S]*?\})\s*```", s, flags=re.IGNORECASE)
        if m:
            return m.group(1)

        # Try any fenced block
        m = re.search(r"```[\s\S]*?\n(\{[\s\S]*?\})\s*```", s)
        if m:
            return m.group(1)

        # Fallback: find first { and match braces until balanced
        start = s.find('{')
        if start == -1:
            return None
        depth = 0
        for i in range(start, len(s)):
            if s[i] == '{':
                depth += 1
            elif s[i] == '}':
                depth -= 1
                if depth == 0:
                    return s[start:i+1]
        return None

    # Primary parse attempt
    try:
        data = json.loads(raw)
        return Plan(**data)
    except Exception:
        # Try extracting a JSON block from mixed text
        block = _extract_json_block(raw)
        if block:
            try:
                data = json.loads(block)
                return Plan(**data)
            except Exception:
                pass

    # Retry politely asking for ONLY JSON (short instruction)
    retry_prompt = "Return ONLY the exact same plan as valid JSON and nothing else. Do not add any explanation."
    raw2 = llm_chat(PLANNER_SYS_PROMPT, retry_prompt)
    try:
        data = json.loads(raw2)
        emit_event({"type": "planner_output", "raw": raw2, "timestamp": int(time.time())})
        return Plan(**data)
    except Exception:
        # Try extraction on second raw
        block2 = _extract_json_block(raw2)
        if block2:
            try:
                data = json.loads(block2)
                return Plan(**data)
            except Exception:
                pass

    raise RuntimeError(f"Planner failed to produce valid JSON.\nRaw1:{raw}\nRaw2:{raw2}")


def execute_plan(plan: Plan) -> RunResult:
    logs: List[StepLog] = []

    # Reset stop flag for this run
    AGENT_STOP_EVENT.clear()
    
    # DEBUG: Print full plan for inspection
    with open(r"c:\Users\Yugandhar Paulbudhe\Desktop\AABLAS - Copy\debug_docgen.log", "a") as f:
        f.write(f"\n[execute_plan] Full plan JSON:\n{json.dumps(plan.dict(), indent=2)}\n")

    for step in plan.steps[: plan.max_iterations]:
        # Check for external stop signal
        if AGENT_STOP_EVENT.is_set():
            emit_event({"type": "agent_stopped", "reason": "stop_signal_received", "timestamp": int(time.time())})
            break
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
            # Emit reasoning event
            emit_event({"type": "reason", "step_id": step.step_id, "title": step.title, "timestamp": int(time.time())})
            continue

        # If this is a doc generation step, ensure required data is present.
        if step.tool == "doc_generate":
            # Check if payload has valid content or fields
            payload = step.input or {}
            if isinstance(payload, dict):
                # New format: has 'content' array
                has_content = isinstance(payload.get('content'), list) and len(payload.get('content', [])) > 0
                # Old format: has 'fields' dict
                has_fields = isinstance(payload.get('fields'), dict) and len(payload.get('fields', {})) > 0
                
                # If we have either content or fields, proceed with execution
                # If neither, ask user for input
                if not has_content and not has_fields:
                    try:
                        # Ask LLM for required fields for this doc step
                        prompt_req = (
                            f"For the following document generation step, list the required field names as a JSON array of strings."
                            f"\n\nGOAL: {plan.goal}\nSTEP TITLE: {step.title}\nEXPECTATIONS: {step.expectations}\n"
                        )
                        raw_fields = llm_chat(PLANNER_SYS_PROMPT, prompt_req)
                        req = None
                        try:
                            req = json.loads(raw_fields)
                        except Exception:
                            # fallback: extract between first [ and last ]
                            s = raw_fields
                            a = s.find('[')
                            b = s.rfind(']')
                            if a != -1 and b != -1 and b > a:
                                try:
                                    req = json.loads(s[a:b+1])
                                except Exception:
                                    req = None
                        if isinstance(req, list) and len(req) > 0:
                            emit_event({
                                "type": "need_input",
                                "step_id": step.step_id,
                                "title": step.title,
                                "fields": req,
                                "prompt": f"Provide values for the following fields to generate the document",
                                "timestamp": int(time.time()),
                            })
                            break
                    except Exception:
                        emit_event({
                            "type": "need_input",
                            "step_id": step.step_id,
                            "title": step.title,
                            "fields": [],
                            "prompt": f"Provide document fields to generate the document",
                            "timestamp": int(time.time()),
                        })
                        break

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

        emit_event({"type": "step_started", "step_id": step.step_id, "title": step.title, "tool": step.tool, "input": step.input, "timestamp": int(time.time())})

        # Allow tools to be long-running; check stop flag before invocation
        if AGENT_STOP_EVENT.is_set():
            emit_event({"type": "agent_stopped", "reason": "stop_signal_received", "timestamp": int(time.time())})
            break

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
        # Emit step result event
        try:
            emit_event({
                "type": "step_result",
                "step_id": step.step_id,
                "title": step.title,
                "tool": step.tool,
                "ok": bool(res.get("ok", False)),
                "logs": str(res.get("logs", "")),
                "output_preview": preview,
                "timestamp": int(time.time()),
            })
        except Exception:
            pass

    # Ask evaluator LLM for structured evaluation including sources
    eval_prompt = (
        f"PLAN:\n{plan.model_dump_json(indent=2)}\n\nLOGS:\n{json.dumps([l.dict() for l in logs], indent=2)}\n\n"
        "Return compact JSON with keys: { 'success': bool, 'summary': str, 'sources': [ { 'id': int, 'title': str, 'snippet': str } ] }"
    )
    raw = llm_chat(EVALUATOR_SYS_PROMPT, eval_prompt)
    try:
        report = json.loads(raw)
    except Exception:
        report = {"success": False, "summary": f"Evaluator JSON parse failed. Raw: {raw}", "sources": []}

    # Emit a structured evaluation event for the frontend
    try:
        emit_event({
            "type": "evaluation",
            "success": bool(report.get("success", False)),
            "summary": str(report.get("summary", "")),
            "sources": report.get("sources", []),
            "timestamp": int(time.time()),
        })
    except Exception:
        pass

    return RunResult(success=bool(report.get("success", False)), plan=plan, steps=logs, summary=str(report.get("summary", "")))


# --- Public API for routes ---
def plan_and_run(goal: str) -> Dict[str, Any]:
    plan = draft_plan(goal)
    result = execute_plan(plan)
    # Emit final next_steps event for UI
    try:
        # If the planner didn't include next_steps, provide a sensible fallback
        if not getattr(plan, 'next_steps', None):
            plan.next_steps = [
                f"Review the plan and confirm inputs for goal: {plan.goal}",
                "Execute the plan steps and collect any outputs or artifacts.",
                "Summarize findings and produce the final deliverable (report or document).",
            ]

        if getattr(plan, 'next_steps', None):
            emit_event({
                "type": "next_steps",
                "next_steps": plan.next_steps,
                "timestamp": int(time.time()),
            })
        # Emit run_complete with summary and success flag
        emit_event({
            "type": "run_complete",
            "success": result.success,
            "summary": result.summary,
            "timestamp": int(time.time()),
        })
    except Exception:
        pass
    return {"plan": plan.dict(), "result": result.dict()}
