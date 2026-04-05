"""Weslr Tool Adapter: OpenClaw Reference Implementation (v1)

OpenClaw tool/capability bridge adapter for Weslr platform.
This adapter provides OpenClaw-specific tools while maintaining
compatibility with the platform contract.

Architecture: Layer 3 of 3-layer adapter architecture
Purpose: Provider-agnostic tool access (files, commands, Python execution)

Adapter Pattern:
  - ToolAdapter base class defines interface
  - OpenClawTools implements OpenClaw-specific tools
  - Weslr core uses adapter, never calls tools directly
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..contracts import RunResult
from . import ToolAdapter


class OpenClawTools(ToolAdapter):
    """OpenClaw tool/capability bridge adapter.
    
    Provides access to OpenClaw workspace tools and capabilities.
    This is the reference implementation for the ToolAdapter interface.
    
    Tools provided:
    - file_read: Read files from workspace
    - file_write: Write files to workspace
    - directory_list: List directory contents
    - command_execute: Execute shell commands
    - python_execute: Execute Python scripts
    """
    
    def __init__(self, base_dir: str = None):
        """Initialize with optional base directory override."""
        self._base_dir = base_dir or self._detect_base_dir()
    
    def _detect_base_dir(self) -> str:
        """Detect OpenClaw workspace base directory."""
        # Try environment variable first
        env_dir = os.getenv("WESLR_BASE_DIR")
        if env_dir:
            return env_dir
        
        # Default to OpenClaw workspace
        return "/data/data/com.termux/files/home/.openclaw/workspace"
    
    # ===== ToolAdapter Interface =====
    
    def list_tools(self) -> List[Dict[str, Any]]:
        """List all available tools/capabilities."""
        return [
            {
                "name": "file_read",
                "description": "Read the contents of a file from the workspace",
                "schema": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Path to the file relative to base_dir"
                        }
                    },
                    "required": ["path"]
                },
                "category": "file"
            },
            {
                "name": "file_write",
                "description": "Write contents to a file in the workspace",
                "schema": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Path to the file relative to base_dir"
                        },
                        "content": {
                            "type": "string",
                            "description": "Content to write to the file"
                        }
                    },
                    "required": ["path", "content"]
                },
                "category": "file"
            },
            {
                "name": "directory_list",
                "description": "List contents of a directory in the workspace",
                "schema": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Path to the directory relative to base_dir",
                            "default": "."
                        }
                    },
                    "required": []
                },
                "category": "file"
            },
            {
                "name": "command_execute",
                "description": "Execute a shell command in the workspace",
                "schema": {
                    "type": "object",
                    "properties": {
                        "command": {
                            "type": "string",
                            "description": "Shell command to execute"
                        },
                        "args": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Command arguments",
                            "default": []
                        }
                    },
                    "required": ["command"]
                },
                "category": "system"
            },
            {
                "name": "python_execute",
                "description": "Execute a Python script in the workspace",
                "schema": {
                    "type": "object",
                    "properties": {
                        "script": {
                            "type": "string",
                            "description": "Python script to execute"
                        },
                        "args": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Script arguments",
                            "default": []
                        }
                    },
                    "required": ["script"]
                },
                "category": "system"
            }
        ]
    
    def get_tool_schema(self, name: str) -> Dict[str, Any]:
        """Get the JSON schema for a specific tool."""
        tools = self.list_tools()
        for tool in tools:
            if tool.get("name") == name:
                return tool.get("schema", {})
        raise ValueError(f"Tool not found: {name}")
    
    def execute_tool(self, name: str, arguments: Dict[str, Any]) -> Any:
        """Execute a tool with the given arguments."""
        if name == "file_read":
            return self._execute_file_read(arguments)
        elif name == "file_write":
            return self._execute_file_write(arguments)
        elif name == "directory_list":
            return self._execute_directory_list(arguments)
        elif name == "command_execute":
            return self._execute_command_execute(arguments)
        elif name == "python_execute":
            return self._execute_python_execute(arguments)
        else:
            raise ValueError(f"Unknown tool: {name}")
    
    def tool_result_to_message(self, tool_call_id: str, content: Any) -> Dict[str, Any]:
        """Convert a tool result to a normalized Weslr message/result shape."""
        # Convert content to string for message
        if isinstance(content, (dict, list)):
            content_str = str(content)
        else:
            content_str = str(content) if content is not None else ""
        
        return {
            "role": "tool",
            "tool_call_id": tool_call_id,
            "content": content_str,
            "is_error": False
        }
    
    # ===== Tool Implementations =====
    
    def _execute_file_read(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Read a file from the workspace."""
        path = arguments.get("path")
        if not path:
            return {"error": "path is required", "is_error": True}
        
        full_path = os.path.join(self._base_dir, path)
        
        try:
            with open(full_path, "r", encoding="utf-8") as f:
                content = f.read()
            return {
                "path": path,
                "content": content,
                "size": len(content),
                "is_error": False
            }
        except FileNotFoundError:
            return {"error": f"File not found: {full_path}", "is_error": True}
        except Exception as e:
            return {"error": str(e), "is_error": True}
    
    def _execute_file_write(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Write to a file in the workspace."""
        path = arguments.get("path")
        content = arguments.get("content")
        
        if not path:
            return {"error": "path is required", "is_error": True}
        if content is None:
            return {"error": "content is required", "is_error": True}
        
        full_path = os.path.join(self._base_dir, path)
        
        try:
            # Ensure parent directory exists
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(content)
            
            return {
                "path": path,
                "size": len(content),
                "is_error": False
            }
        except Exception as e:
            return {"error": str(e), "is_error": True}
    
    def _execute_directory_list(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """List contents of a directory."""
        path = arguments.get("path", ".")
        full_path = os.path.join(self._base_dir, path)
        
        try:
            if not os.path.exists(full_path):
                return {"error": f"Directory not found: {full_path}", "is_error": True}
            
            entries = []
            for entry in os.listdir(full_path):
                entry_path = os.path.join(full_path, entry)
                entries.append({
                    "name": entry,
                    "type": "directory" if os.path.isdir(entry_path) else "file",
                    "size": os.path.getsize(entry_path) if os.path.isfile(entry_path) else None
                })
            
            return {
                "path": path,
                "entries": entries,
                "count": len(entries),
                "is_error": False
            }
        except Exception as e:
            return {"error": str(e), "is_error": True}
    
    def _execute_command_execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a shell command."""
        command = arguments.get("command")
        args = arguments.get("args", [])
        
        if not command:
            return {"error": "command is required", "is_error": True}
        
        try:
            result = subprocess.run(
                [command] + args,
                cwd=self._base_dir,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            return {
                "command": command,
                "args": args,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "return_code": result.returncode,
                "is_error": result.returncode != 0
            }
        except subprocess.TimeoutExpired:
            return {
                "command": command,
                "args": args,
                "error": "Command timed out after 300 seconds",
                "is_error": True
            }
        except Exception as e:
            return {"error": str(e), "is_error": True}
    
    def _execute_python_execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a Python script."""
        script = arguments.get("script")
        args = arguments.get("args", [])
        
        if not script:
            return {"error": "script is required", "is_error": True}
        
        try:
            # Write script to temp file and execute
            import tempfile
            with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
                f.write(script)
                script_path = f.name
            
            try:
                result = subprocess.run(
                    ["python3", script_path] + args,
                    cwd=self._base_dir,
                    capture_output=True,
                    text=True,
                    timeout=300
                )
                
                return {
                    "script": script,
                    "args": args,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "return_code": result.returncode,
                    "is_error": result.returncode != 0
                }
            finally:
                os.unlink(script_path)
                
        except subprocess.TimeoutExpired:
            return {
                "script": script,
                "args": args,
                "error": "Script execution timed out after 300 seconds",
                "is_error": True
            }
        except Exception as e:
            return {"error": str(e), "is_error": True}


# Convenience factory function
def create_tools(base_dir: str = None) -> ToolAdapter:
    """Create an OpenClawTools adapter instance.
    
    This is a convenience function for getting a tool adapter.
    """
    return OpenClawTools(base_dir)
