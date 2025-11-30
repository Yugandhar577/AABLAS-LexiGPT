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
        _agent_instance.stop()
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


from services.agent_services import plan_and_run


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