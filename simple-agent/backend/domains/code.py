"""代码域包（E3 基板，stub；待落地）。"""
from domains import DomainPack, register  # noqa: E402

CODE = register(DomainPack(
    name="code",
    mutating_tools={"write_file", "edit_file", "apply_patch", "run_command", "delete_path"},
    transfer_tool="",
    read_prefixes=("read_", "list_", "grep", "glob", "search", "stat"),
    entity_field_class={"path": "III", "file_id": "I", "repo_id": "I",
                        "commit_sha": "I", "symbol": "IV"},
    interceptor_rules=[],           # E3 首个死因谓词待普查后立法
    lock_scope_key="path",
    description="代码域（E3 基板）；harness 复用 τ 已建成设施",
))
