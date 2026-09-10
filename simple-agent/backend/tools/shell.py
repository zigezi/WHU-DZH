import subprocess
import os

# Security: only allow safe commands, extend as needed
ALLOWED_COMMANDS = {
    "ls", "cat", "head", "tail", "wc", "grep", "find",
    "python", "python3", "node", "npm", "pip", "pip3",
    "mkdir", "touch", "cp", "mv", "rm", "chmod",
    "git", "docker", "curl", "wget", "echo", "pwd"
}

def run_command(work_dir: str, command: str, timeout: int = 30, **kwargs) -> str:
    # Basic security check
    cmd_base = command.strip().split()[0] if command.strip() else ""
    if cmd_base not in ALLOWED_COMMANDS:
        raise PermissionError(f"Command not allowed: {cmd_base}. Add to whitelist if needed.")
    
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=work_dir,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        output = f"$ {command}\n"
        output += f"Exit code: {result.returncode}\n"
        if result.stdout:
            output += f"--- STDOUT ---\n{result.stdout[:3000]}\n"
        if result.stderr:
            output += f"--- STDERR ---\n{result.stderr[:2000]}\n"
        return output
    except subprocess.TimeoutExpired:
        return f"Command timed out after {timeout}s: {command}"

