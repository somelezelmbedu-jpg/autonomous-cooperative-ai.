"""
Sandbox — isolated environment for testing proposed changes.
"""

import io
import contextlib
import traceback
from typing import Any, Dict


class Sandbox:
    def __init__(self, audit_log):
        self.audit_log = audit_log

    def test_proposal(self, name: str, python_snippet: str, test_inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run a small, self-contained snippet against test inputs and capture
        the result, without letting it touch the real filesystem/network.
        """
        safe_builtins = {
            "len": len, "range": range, "min": min, "max": max, "sum": sum,
            "abs": abs, "round": round, "sorted": sorted, "enumerate": enumerate,
        }
        local_scope = dict(test_inputs)
        stdout = io.StringIO()
        result = {"name": name, "success": False, "output": None, "error": None}

        try:
            with contextlib.redirect_stdout(stdout):
                exec(python_snippet, {"__builtins__": safe_builtins}, local_scope)
            result["success"] = True
            result["output"] = local_scope.get("result")
        except Exception:
            result["error"] = traceback.format_exc(limit=2)
        finally:
            result["stdout"] = stdout.getvalue()

        self.audit_log.record(
            event_type="sandbox_test",
            detail=result,
            severity="info" if result["success"] else "warn",
        )
        return result
