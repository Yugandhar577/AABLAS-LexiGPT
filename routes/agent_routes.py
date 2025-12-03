from flask import Blueprint, Response, request, jsonify, stream_with_context
import threading
import time
import json
from pathlib import Path

bp = Blueprint("agent", __name__, url_prefix="/api/agent")

# Agent thread / instance storage
_agent_thread = None
_agent_instance = None

LOG_PATH = Path("data/agent_logs.jsonl")


@bp.route("/run", methods=["POST"])
def run_agent():
    global _agent_thread, _agent_instance
    if _agent_thread and _agent_thread.is_alive():
        return jsonify({"status": "already_running"}), 409

    # Lazy import to avoid heavy imports at startup
    from data.agent import SimpleIngestAgent

    _agent_instance = SimpleIngestAgent()
    _agent_thread = threading.Thread(target=_agent_instance.run, daemon=True)
    _agent_thread.start()
    return jsonify({"status": "started"})


@bp.route("/stop", methods=["POST"])
def stop_agent():
    global _agent_instance
    if _agent_instance:
        try:
            _agent_instance.stop()
        except Exception:
            pass
        # also set the global stop event for agent services
        try:
            from services.agent_services import AGENT_STOP_EVENT

            AGENT_STOP_EVENT.set()
        except Exception:
            pass
        return jsonify({"status": "stopping"})
    return jsonify({"status": "not_running"}), 404


@bp.route("/logs", methods=["GET"])
def agent_logs():
    if not LOG_PATH.exists():
        return jsonify([])
    try:
        lines = LOG_PATH.read_text(encoding="utf-8").splitlines()
        # return last 200 lines by default
        lines = lines[-200:]
        return jsonify([json.loads(l) for l in lines])
    except Exception as e:
        return jsonify({"error": repr(e)}), 500


def _tail_file(path: Path):
    # Generator that yields new JSON log entries as Python objects.
    # Handles file truncation/rotation by checking file stats and reopening when needed.
    last_inode = None
    last_size = 0
    f = None
    try:
        while True:
            try:
                if f is None:
                    f = path.open("r", encoding="utf-8")
                    # move to EOF for new events
                    f.seek(0, 2)
                    try:
                        st = path.stat()
                        last_inode = getattr(st, 'st_ino', None)
                        last_size = st.st_size
                    except Exception:
                        last_inode = None
                        last_size = 0

                line = f.readline()
                if not line:
                    # check for rotation/truncation
                    try:
                        st = path.stat()
                        cur_inode = getattr(st, 'st_ino', None)
                        cur_size = st.st_size
                        # file was truncated or rotated when current file pos > cur_size
                        if cur_size < f.tell() or (last_inode is not None and cur_inode != last_inode):
                            # reopen file
                            try:
                                f.close()
                            except Exception:
                                pass
                            f = None
                            last_inode = cur_inode
                            last_size = cur_size
                            time.sleep(0.2)
                            continue
                    except Exception:
                        # stat failed; just sleep and continue
                        pass
                    time.sleep(0.5)
                    continue
                try:
                    obj = json.loads(line)
                except Exception:
                    obj = {"raw": line.strip()}
                yield obj
            except Exception:
                # on any read error, close and retry opening the file
                try:
                    if f:
                        f.close()
                except Exception:
                    pass
                f = None
                time.sleep(0.5)
                continue
    finally:
        try:
            if f:
                f.close()
        except Exception:
            pass


@bp.route("/stream")
def stream_logs():
    # Server-Sent Events streaming of new log entries
    def gen():
        path = LOG_PATH
        path.parent.mkdir(parents=True, exist_ok=True)
        # create file if missing
        path.touch(exist_ok=True)
        for obj in _tail_file(path):
            data = json.dumps(obj, ensure_ascii=False)
            yield f"data: {data}\n\n"


    return Response(stream_with_context(gen()), mimetype="text/event-stream")


from services.agent_services import plan_and_run, AGENT_EVENT_QUEUE


@bp.route('/stream_events')
def stream_events():
    """Stream structured agent events (JSON) via Server-Sent Events.

    Clients should connect with EventSource to receive events like:
      {type: 'step_started'|'step_result'|'file_download'|'planner_output'|'agent_stopped', ...}
    """
    def gen():
        try:
            while True:
                try:
                    evt = AGENT_EVENT_QUEUE.get(timeout=0.5)
                except Exception:
                    # keep-alive comment
                    yield ': keep-alive\n\n'
                    continue
                yield f"data: {evt}\n\n"
        except GeneratorExit:
            return

    return Response(stream_with_context(gen()), mimetype='text/event-stream')


@bp.route("/plan-run", methods=["POST"])
def plan_run():
    """
    POST JSON: { "goal": "..." }
    Returns: { plan: {...}, result: {...} }
    """
    data = request.get_json(force=True)
    goal = data.get("goal")
    if not goal:
        return jsonify({"error": "no goal provided"}), 400
    try:
        out = plan_and_run(goal)
        return jsonify(out)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route("/generate-document", methods=["POST"])
def generate_document_route():
    """
    POST JSON: { "request": "Create a rental agreement PDF", "doc_type": "contract" (optional), "format": "pdf" (optional) }
    
    This endpoint recognizes a natural language document generation request,
    enriches it with the agent planner to fill in required fields, and generates the document.
    Returns: the full plan+run result including the file_download event and download URL.
    """
    data = request.get_json(force=True) or {}
    user_request = data.get("request")
    if not user_request:
        return jsonify({"error": "no request provided"}), 400
    
    try:
        # Transform the user request into an agent goal that includes document generation
        goal = (
            f"You are a document generation agent. The user wants: {user_request}\n\n"
            f"Plan the steps to gather any required information, ask the user for missing details if needed, "
            f"and then generate a downloadable document using the doc_generate tool."
        )
        
        # Run the agent with the enriched goal
        out = plan_and_run(goal)
        return jsonify(out)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
