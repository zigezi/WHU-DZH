from tools.registry import ToolRegistry
from tools.file_ops import read_file, write_file, list_files
from tools.shell import run_command

def init_tool_registry(work_dir: str) -> ToolRegistry:
    registry = ToolRegistry(work_dir)
    
    # Register file operations
    registry.register(
        name="read_file",
        schema={
            "type": "function",
            "function": {
                "name": "read_file",
                "description": "Read a file from the workspace",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "Relative path to file"}
                    },
                    "required": ["path"]
                }
            }
        },
        func=read_file
    )
    
    registry.register(
        name="write_file",
        schema={
            "type": "function",
            "function": {
                "name": "write_file",
                "description": "Write content to a file in the workspace",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "Relative path to file"},
                        "content": {"type": "string", "description": "Content to write"}
                    },
                    "required": ["path", "content"]
                }
            }
        },
        func=write_file
    )
    
    registry.register(
        name="list_files",
        schema={
            "type": "function",
            "function": {
                "name": "list_files",
                "description": "List files in a directory",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "Relative directory path", "default": "."}
                    }
                }
            }
        },
        func=list_files
    )
    
    registry.register(
        name="run_command",
        schema={
            "type": "function",
            "function": {
                "name": "run_command",
                "description": "Execute a shell command in the workspace",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "command": {"type": "string", "description": "Command to execute"},
                        "timeout": {"type": "integer", "description": "Timeout in seconds", "default": 30}
                    },
                    "required": ["command"]
                }
            }
        },
        func=run_command
    )
    
    return registry

