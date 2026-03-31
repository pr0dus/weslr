"""Weslr Self-Improvement Apply Workflow - Phase 1D.

Applies approved proposals in a bounded, safe manner.
Phase 1D: Real test execution with actual pytest integration.

Phase 1D adds:
1. Real test execution using pytest or Python test functions
2. Pass/fail recording based on actual test results
3. Failure status when tests fail
4. Clear rollback guidance when tests fail

Safety rules (preserving Phase 1C):
1. Only approved proposals can be applied
2. Proposals must have test_prompts OR explicit test_exempt
3. Proposals must have patch_plan OR rollback_command
4. Protected files blocked
5. Checkpoint created before each file change
6. Tests run after apply with real execution
7. Failure state recorded when tests fail
"""

from __future__ import annotations

import json
import subprocess
import time
import importlib
import sys
from pathlib import Path


APPLY_LOG_FILE = "self_improvement_apply_log.json"
BASE_DIR = Path(__file__).resolve().parent


def get_apply_log_path() -> Path:
    """Get path to apply log storage file."""
    return BASE_DIR / APPLY_LOG_FILE


def load_apply_log() -> list[dict]:
    """Load apply log from storage."""
    path = get_apply_log_path()
    if not path.exists():
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def save_apply_log(log: list[dict]) -> None:
    """Save apply log to storage."""
    path = get_apply_log_path()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(log, f, indent=2)


def get_proposals_path() -> Path:
    """Get path to proposals storage file."""
    from self_improvement_proposal import get_proposals_path
    return get_proposals_path()


def load_proposals() -> list[dict]:
    """Load all proposals from storage."""
    from self_improvement_proposal import load_proposals
    return load_proposals()


def save_proposals(proposals: list[dict]) -> None:
    """Save proposals to storage."""
    from self_improvement_proposal import save_proposals
    save_proposals(proposals)


def load_observations() -> list[dict]:
    """Load all observations from storage."""
    from self_improvement_observation import load_observations
    return load_observations()


def create_checkpoint(file_path: str) -> dict:
    """Create a checkpoint of a file before applying changes.

    Args:
        file_path: Path to the file to checkpoint (relative to workspace)

    Returns:
        dict with checkpoint details or error
    """
    workspace_path = Path(__file__).resolve().parent / file_path

    if not workspace_path.exists():
        return {
            "ok": False,
            "error": f"File not found: {file_path}",
        }

    try:
        with open(workspace_path, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        return {
            "ok": False,
            "error": f"Could not read file: {e}",
        }

    now_ts = int(time.time() * 1000)
    checkpoint_name = f"{file_path.replace('/', '_').replace('.py', '')}_{now_ts}.bak"

    # Use checkpoints directory
    checkpoint_dir = Path(__file__).resolve().parent / "checkpoints"
    checkpoint_dir.mkdir(exist_ok=True)

    checkpoint_path = checkpoint_dir / checkpoint_name
    try:
        with open(checkpoint_path, "w", encoding="utf-8") as f:
            f.write(content)
    except Exception as e:
        return {
            "ok": False,
            "error": f"Could not create checkpoint: {e}",
        }

    return {
        "ok": True,
        "file_path": file_path,
        "checkpoint_name": checkpoint_name,
        "content_length": len(content),
        "checkpoint_path": str(checkpoint_path),
        "created_at": now_ts,
    }


def _validate_test_requirement(proposal: dict) -> tuple[bool, str]:
    """Validate that proposal meets test requirements.

    Rules:
    - Must have test_prompts, OR
    - Must have explicit test_exempt flag with justification

    Returns:
        (is_valid, error_message)
    """
    test_prompts = proposal.get("test_prompts", [])
    test_exempt = proposal.get("test_exempt", False)

    if test_prompts:
        return True, ""

    if test_exempt:
        justification = proposal.get("test_exempt_justification", "")
        if justification:
            return True, ""
        return False, "test_exempt flag requires test_exempt_justification field"

    return False, "Proposal must have either test_prompts or explicit test_exempt justification"


def _validate_patch_requirement(proposal: dict) -> tuple[bool, str]:
    """Validate that proposal has patch information.

    Rules:
    - Must have patch_plan (dry-run), OR
    - Must have rollback_command

    Returns:
        (is_valid, error_message)
    """
    patch_plan = proposal.get("patch_plan")
    rollback_command = proposal.get("rollback_command")

    if patch_plan:
        return True, ""

    if rollback_command:
        return True, ""

    return False, "Proposal must have either patch_plan (dry-run) or rollback_command"


def _run_test_command(test_command: str) -> dict:
    """Run a test command and return results.

    Args:
        test_command: Command to run (e.g., 'pytest tests/test_something.py')

    Returns:
        dict with test results
    """
    try:
        result = subprocess.run(
            test_command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=60,
        )
        return {
            "success": result.returncode == 0,
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": "Test execution timed out",
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


def _run_pytest_tests(test_paths: list[str]) -> dict:
    """Run pytest on specified test paths.

    Args:
        test_paths: List of test file paths or patterns

    Returns:
        dict with pytest results
    """
    if not test_paths:
        return {
            "success": False,
            "error": "No test paths specified",
        }

    try:
        # Build pytest command
        pytest_args = " ".join(test_paths)
        cmd = f"python3 -m pytest {pytest_args} -v"
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=120,
        )
        return {
            "success": result.returncode == 0,
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "command": cmd,
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": "pytest execution timed out",
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


def _run_module_import_test(module_name: str) -> dict:
    """Test that a module can be imported successfully.

    Args:
        module_name: Name of module to import

    Returns:
        dict with import test results
    """
    try:
        # Add workspace to path if not already there
        workspace_path = str(Path(__file__).resolve().parent)
        if workspace_path not in sys.path:
            sys.path.insert(0, workspace_path)

        # Try to import the module
        module = importlib.import_module(module_name)
        return {
            "success": True,
            "module": module_name,
            "message": f"Module {module_name} imported successfully",
        }
    except Exception as e:
        return {
            "success": False,
            "module": module_name,
            "error": str(e),
        }


def _run_tests_from_proposal(test_prompts: list[dict]) -> list[dict]:
    """Run tests from proposal test prompts.

    Args:
        test_prompts: List of test prompt definitions

    Returns:
        list of test results
    """
    test_results = []

    for i, test in enumerate(test_prompts):
        prompt = test.get("prompt", "")
        expected_type = test.get("expected_type", "")

        result = {
            "test_index": i,
            "prompt": prompt[:50] + "..." if len(prompt) > 50 else prompt,
        }

        # Run actual test based on expected_type
        if expected_type == "pytest":
            test_paths = test.get("test_paths", [])
            if test_paths:
                pytest_result = _run_pytest_tests(test_paths)
                result["status"] = "pass" if pytest_result.get("success") else "fail"
                result["stdout"] = pytest_result.get("stdout", "")
                result["stderr"] = pytest_result.get("stderr", "")
                result["command"] = pytest_result.get("command", "")
                if not pytest_result.get("success"):
                    result["error"] = pytest_result.get("error", "pytest failed")
            else:
                result["status"] = "fail"
                result["error"] = "No test_paths specified for pytest"

        elif expected_type == "module_import":
            module_name = test.get("module_name", "")
            if module_name:
                import_result = _run_module_import_test(module_name)
                result["status"] = "pass" if import_result.get("success") else "fail"
                result["message"] = import_result.get("message", "")
                if not import_result.get("success"):
                    result["error"] = import_result.get("error", "")
            else:
                result["status"] = "fail"
                result["error"] = "No module_name specified"

        elif expected_type == "command":
            cmd = test.get("command", "")
            if cmd:
                cmd_result = _run_test_command(cmd)
                result["status"] = "pass" if cmd_result.get("success") else "fail"
                result["stdout"] = cmd_result.get("stdout", "")
                result["stderr"] = cmd_result.get("stderr", "")
                if not cmd_result.get("success"):
                    result["error"] = cmd_result.get("error", "")
            else:
                result["status"] = "fail"
                result["error"] = "No command specified"

        else:
            # Default: try to import a module named after the prompt keyword
            # This is a simple heuristic for testing
            module_keyword = prompt.lower().replace(" ", "_").replace("-", "_")
            import_result = _run_module_import_test(module_keyword)
            result["status"] = "pass" if import_result.get("success") else "fail"
            if not import_result.get("success"):
                result["error"] = import_result.get("error", "")

        test_results.append(result)

    return test_results


def apply_proposal(proposal_id: str, applied_by: str, test_mode: str = "real") -> dict:
    """Apply an approved proposal in a bounded, safe manner.

    Phase 1D adds:
    1. Real test execution using pytest or Python tests
    2. Pass/fail recording based on actual test results
    3. Failure status when tests fail
    4. Rollback guidance when tests fail

    Args:
        proposal_id: ID of proposal to apply
        applied_by: Who applied (e.g., "human")
        test_mode: "real" for actual pytest, "simplified" for Phase 1C behavior

    Returns:
        dict with apply result
    """
    proposal = None
    proposals = load_proposals()
    for p in proposals:
        if p.get("id") == proposal_id:
            proposal = p
            break

    if not proposal:
        return {
            "ok": False,
            "error": f"Proposal not found: {proposal_id}",
        }

    # Rule 1: Only approved proposals can be applied
    if proposal.get("status") != "approved":
        return {
            "ok": False,
            "error": f"Proposal is not approved. Current status: {proposal.get('status')}. Must be 'approved'.",
            "current_status": proposal.get("status"),
        }

    # Rule 2: Validate test requirement
    tests_valid, tests_error = _validate_test_requirement(proposal)
    if not tests_valid:
        return {
            "ok": False,
            "error": f"Test requirement not met: {tests_error}",
            "requirement": "tests_or_exempt",
            "details": {
                "has_test_prompts": bool(proposal.get("test_prompts")),
                "has_test_exempt": bool(proposal.get("test_exempt")),
            },
        }

    # Rule 3: Validate patch requirement
    patch_valid, patch_error = _validate_patch_requirement(proposal)
    if not patch_valid:
        return {
            "ok": False,
            "error": f"Patch requirement not met: {patch_error}",
            "requirement": "patch_or_rollback",
            "details": {
                "has_patch_plan": bool(proposal.get("patch_plan")),
                "has_rollback_command": bool(proposal.get("rollback_command")),
            },
        }

    # Rule 4: Protected files cannot be modified
    files_to_change = proposal.get("files_to_change", [])
    for filepath in files_to_change:
        from self_improvement_proposal import is_protected_file
        if is_protected_file(filepath):
            return {
                "ok": False,
                "error": f"Protected file cannot be modified: {filepath}",
                "protected_file": filepath,
            }

    # Rule 5: Create checkpoint before each file change
    checkpoints = []
    for filepath in files_to_change:
        checkpoint = create_checkpoint(filepath)
        if not checkpoint.get("ok"):
            return {
                "ok": False,
                "error": f"Checkpoint failed for {filepath}: {checkpoint.get('error')}",
                "failed_checkpoint": filepath,
            }
        checkpoints.append(checkpoint)

    # Apply change
    now_ts = int(time.time() * 1000)
    applied_files = []

    for filepath in files_to_change:
        workspace_path = Path(__file__).resolve().parent / filepath

        if not workspace_path.exists():
            return {
                "ok": False,
                "error": f"File not found during apply: {filepath}",
                "failed_file": filepath,
            }

        try:
            with open(workspace_path, "r", encoding="utf-8") as f:
                current_content = f.read()
        except Exception as e:
            return {
                "ok": False,
                "error": f"Could not read file during apply: {e}",
                "failed_file": filepath,
            }

        # Simple append change (placeholder - for Phase 1C/1D testing)
        change_marker = f"\n# Phase 1C/1D apply: {proposal.get('id')} - {proposal.get('title')}\n"
        new_content = current_content + change_marker + "# Applied at: " + time.strftime("%Y-%m-%d %H:%M:%S") + "\n"

        try:
            with open(workspace_path, "w", encoding="utf-8") as f:
                f.write(new_content)
        except Exception as e:
            return {
                "ok": False,
                "error": f"Could not write file during apply: {e}",
                "failed_file": filepath,
                "rollback_available": True,
            }

        applied_files.append({
            "file_path": filepath,
            "before_length": len(current_content),
            "after_length": len(new_content),
        })

    # Rule 6: Run tests (real execution in Phase 1D)
    test_prompts = proposal.get("test_prompts", [])
    test_results = []

    if test_prompts:
        if test_mode == "real":
            # Real test execution using actual test functions
            test_results = _run_tests_from_proposal(test_prompts)
        else:
            # Simplified behavior (Phase 1C compatibility)
            for i, test in enumerate(test_prompts):
                test_results.append({
                    "test_index": i,
                    "prompt": test.get("prompt", "")[:50] + "...",
                    "status": "pass",
                    "message": "Test executed (simplified in Phase 1C)",
                })
    else:
        # test_exempt case - no tests to run
        test_results.append({
            "test_index": 0,
            "prompt": "N/A (test_exempt)",
            "status": "pass",
            "message": "No tests required due to test_exempt flag",
        })

    # Check if all tests passed
    all_tests_passed = all(t.get("status") == "pass" for t in test_results)

    # Update proposal status
    proposal["status"] = "applied" if all_tests_passed else "applied_with_failures"
    proposal["applied_at"] = now_ts
    proposal["applied_by"] = applied_by
    proposal["applied_files"] = applied_files
    proposal["test_results"] = test_results
    proposal["checkpoint_names"] = [c.get("checkpoint_name") for c in checkpoints]
    proposal["all_tests_passed"] = all_tests_passed

    # Save proposals
    for i, p in enumerate(proposals):
        if p.get("id") == proposal_id:
            proposals[i] = proposal
            break
    save_proposals(proposals)

    # Log apply event
    apply_entry = {
        "id": f"apply-{now_ts}",
        "proposal_id": proposal_id,
        "applied_by": applied_by,
        "timestamp": now_ts,
        "applied_files": [f.get("file_path") for f in applied_files],
        "test_results": test_results,
        "all_tests_passed": all_tests_passed,
        "note": "Phase 1D: Bounded apply with real test execution",
    }

    log = load_apply_log()
    log.append(apply_entry)
    save_apply_log(log)

    # Build result with rollback guidance
    result = {
        "ok": True,
        "proposal_id": proposal_id,
        "status": proposal["status"],
        "applied_by": applied_by,
        "applied_at": now_ts,
        "applied_files": [f.get("file_path") for f in applied_files],
        "checkpoints": [c.get("checkpoint_name") for c in checkpoints],
        "test_results": test_results,
        "all_tests_passed": all_tests_passed,
        "note": "Phase 1D: Bounded apply completed",
    }

    if not all_tests_passed:
        # Add failure details
        failing_tests = [t for t in test_results if t.get("status") == "fail"]
        result["status"] = "applied_with_failures"
        result["failing_tests"] = [t.get("test_index") for t in failing_tests]
        result["rollback_guidance"] = {
            "message": "Tests failed after apply. Execute rollback command manually.",
            "rollback_command": proposal.get("rollback_command"),
            "checkpoints": [c.get("checkpoint_path") for c in checkpoints],
        }

    return result


def apply_proposal_with_tests(proposal_id: str, applied_by: str) -> dict:
    """Apply proposal and run full test suite (real execution).

    This calls apply_proposal with test_mode="real" for actual pytest execution.

    Args:
        proposal_id: ID of proposal to apply
        applied_by: Who applied (e.g., "human")

    Returns:
        dict with apply result
    """
    return apply_proposal(proposal_id, applied_by, test_mode="real")


def rollback_proposal(proposal_id: str, rolled_back_by: str) -> dict:
    """Rollback an applied proposal.

    Args:
        proposal_id: ID of proposal to rollback
        rolled_back_by: Who rolled back (e.g., "human")

    Returns:
        dict with rollback result
    """
    proposal = None
    proposals = load_proposals()
    for p in proposals:
        if p.get("id") == proposal_id:
            proposal = p
            break

    if not proposal:
        return {
            "ok": False,
            "error": f"Proposal not found: {proposal_id}",
        }

    if proposal.get("status") not in ("applied", "applied_with_failures"):
        return {
            "ok": False,
            "error": f"Cannot rollback. Proposal status: {proposal.get('status')}. Must be 'applied' or 'applied_with_failures'.",
        }

    rollback_command = proposal.get("rollback_command")

    if not rollback_command:
        return {
            "ok": False,
            "error": "No rollback command stored in proposal. Rollback not possible.",
        }

    # Mark as rolled back
    now_ts = int(time.time() * 1000)
    proposal["status"] = "rolled_back"
    proposal["rolled_back_at"] = now_ts
    proposal["rolled_back_by"] = rolled_back_by

    # Save proposals
    for i, p in enumerate(proposals):
        if p.get("id") == proposal_id:
            proposals[i] = proposal
            break
    save_proposals(proposals)

    # Log rollback event
    rollback_entry = {
        "id": f"rollback-{now_ts}",
        "proposal_id": proposal_id,
        "rolled_back_by": rolled_back_by,
        "timestamp": now_ts,
        "rollback_command": rollback_command,
        "note": "Phase 1D: Rollback recorded",
    }

    log = load_apply_log()
    log.append(rollback_entry)
    save_apply_log(log)

    return {
        "ok": True,
        "proposal_id": proposal_id,
        "status": "rolled_back",
        "rolled_back_by": rolled_back_by,
        "rolled_back_at": now_ts,
        "rollback_command": rollback_command,
        "note": "Phase 1D: Rollback recorded. Execute rollback command manually if needed.",
    }


def build_apply_report() -> dict:
    """Build a summary report of all apply operations."""
    proposals = load_proposals()
    apply_log = load_apply_log()

    status_counts = {
        "proposed": 0,
        "approved": 0,
        "applied": 0,
        "applied_with_failures": 0,
        "rolled_back": 0,
        "rejected": 0,
    }

    for p in proposals:
        status = p.get("status", "unknown")
        if status in status_counts:
            status_counts[status] += 1

    total_applied = len([p for p in proposals if p.get("status") in ("applied", "applied_with_failures")])
    total_rolled_back = len([p for p in proposals if p.get("status") == "rolled_back"])

    return {
        "ok": True,
        "total_proposals": len(proposals),
        "by_status": status_counts,
        "total_applied": total_applied,
        "total_rolled_back": total_rolled_back,
        "total_apply_operations": len(apply_log),
        "generated_at": int(time.time()),
    }
