import os

def _safe_path(work_dir: str, target_path: str) -> str:
    """Prevent path traversal outside work_dir"""
    full_path = os.path.abspath(os.path.join(work_dir, target_path))
    if not full_path.startswith(os.path.abspath(work_dir)):
        raise PermissionError(f"Access denied: path outside work directory")
    return full_path

def read_file(work_dir: str, path: str, **kwargs) -> str:
    full_path = _safe_path(work_dir, path)
    if not os.path.exists(full_path):
        raise FileNotFoundError(f"File not found: {path}")
    with open(full_path, "r", encoding="utf-8") as f:
        content = f.read()
    return f"File: {path}\nSize: {len(content)} chars\n---\n{content[:5000]}"

def write_file(work_dir: str, path: str, content: str, **kwargs) -> str:
    full_path = _safe_path(work_dir, path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)
    return f"Successfully wrote {len(content)} chars to {path}"

def list_files(work_dir: str, path: str = ".", **kwargs) -> str:
    full_path = _safe_path(work_dir, path)
    if not os.path.isdir(full_path):
        raise NotADirectoryError(f"Not a directory: {path}")
    items = os.listdir(full_path)
    result = f"Directory: {path}\n"
    for item in sorted(items):
        item_path = os.path.join(full_path, item)
        item_type = "DIR" if os.path.isdir(item_path) else "FILE"
        size = os.path.getsize(item_path) if os.path.isfile(item_path) else 0
        result += f"  [{item_type}] {item} ({size} bytes)\n"
    return result

