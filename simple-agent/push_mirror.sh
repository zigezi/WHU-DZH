#!/usr/bin/env bash
# =============================================================================
# 手动同步推送器：/root/simple-agent  →  GitHub 镜像 zigezi/WHU-DZH:simple-agent
#
# 用法（由人工在登录 shell 里手动执行；agent 不使用）：
#     bash /root/simple-agent/push_mirror.sh            # 同步并推送
#     bash /root/simple-agent/push_mirror.sh --dry-run  # 只预览，不提交不推送
#
# 机制：镜像 = 把本仓**已提交 HEAD 树**铺进镜像仓的 `simple-agent/` 子目录，再打一个
#       sync 提交并推送（子树快照，非本仓直接 push）。
# Token：从 /root/simple-agent/github-token.txt 临时读入环境变量，**不落盘、不打印**；
#        remote URL 保持干净（不含 token）。
# 边界：本仓 /root/simple-agent 不配 remote（RL-3 结构性边界）。
# =============================================================================
set -euo pipefail

SRC="/root/simple-agent"
MIRROR="/root/WHU-DZH"
REMOTE="origin"
BRANCH="simple-agent"
SUBTREE="simple-agent"
TOKEN_FILE="$SRC/github-token.txt"
DRY=0
[ "${1:-}" = "--dry-run" ] && DRY=1

say() { printf '\033[1;36m[push_mirror]\033[0m %s\n' "$*"; }
die() { printf '\033[1;31m[push_mirror:ERROR]\033[0m %s\n' "$*" >&2; exit 1; }

# --- 0) 前置检查 -------------------------------------------------------------
[ -d "$SRC/.git" ]    || die "源仓不存在：$SRC"
[ -d "$MIRROR/.git" ] || die "镜像工作克隆不存在：$MIRROR（需先 clone zigezi/WHU-DZH）"
git -C "$MIRROR" remote get-url "$REMOTE" >/dev/null 2>&1 || die "镜像仓无 remote '$REMOTE'"

SRC_HEAD="$(git -C "$SRC" rev-parse --short HEAD)"
say "源仓 HEAD = $SRC_HEAD（镜像将反映此提交树）"

if [ -n "$(git -C "$SRC" status --porcelain | grep -vE '^\?\?')" ]; then
    say "⚠ 源仓存在未提交的 tracked 改动；镜像只反映**已提交** HEAD，改动请先 commit。"
fi

# 预检：未跟踪的裁决书/文档不会进镜像（git archive 只含 tracked）——防"镜像裁决书落后"
UNTRACKED_DOCS="$(git -C "$SRC" -c core.quotepath=false status --porcelain | grep -E '^\?\? P5a\.' | sed 's/^?? //' || true)"
if [ -n "$UNTRACKED_DOCS" ]; then
    say "⚠ 存在**未跟踪**的 P5a 裁决书（不会进镜像）："
    printf '%s\n' "$UNTRACKED_DOCS" | sed 's/^/    /'
    say "→ 先 git add 并 commit 这些裁决书，否则镜像将落后于本地。"
    [ "$DRY" = "1" ] || die "未跟踪裁决书未入库；中止（先 git add <文件> && git commit）"
fi

# --- 1) 重建子树 -------------------------------------------------------------
say "重建 $SUBTREE/ 子树 ← 本仓 HEAD 树"
rm -rf "$MIRROR/$SUBTREE" && mkdir -p "$MIRROR/$SUBTREE"
git -C "$SRC" archive HEAD | tar -x -C "$MIRROR/$SUBTREE"
git -C "$MIRROR" add -A -- "$SUBTREE"

if git -C "$MIRROR" diff --cached --quiet -- "$SUBTREE"; then
    say "无变更（镜像已是最新）——跳过提交。"
else
    say "子树变更："
    git -C "$MIRROR" diff --cached --stat -- "$SUBTREE" | tail -n 15
    if [ "$DRY" = "1" ]; then say "[dry-run] 跳过 commit/push"; exit 0; fi
    git -C "$MIRROR" commit -q -m "simple-agent: sync $SRC_HEAD (manual push)"
    say "已提交：$(git -C "$MIRROR" rev-parse --short HEAD)"
fi

# --- 2) 推送（token 临时读入，不落盘） --------------------------------------
[ "$DRY" = "1" ] && { say "[dry-run] 完成（未推送）"; exit 0; }

if [ -f "$TOKEN_FILE" ]; then
    say "使用 $TOKEN_FILE（mode $(stat -c '%a' "$TOKEN_FILE" 2>/dev/null || echo '?')) 认证"
    GIT_TOKEN="$(tr -d '\r\n' < "$TOKEN_FILE")"
    export GIT_TOKEN
    HELPER='!f(){ echo username=x-access-token; echo "password=$GIT_TOKEN"; };f'
else
    say "无 $TOKEN_FILE，使用系统现有凭据（可能交互提示）"
    HELPER=''
fi

if [ -n "$HELPER" ]; then
    git -C "$MIRROR" -c credential.helper="$HELPER" push "$REMOTE" "$BRANCH"
else
    git -C "$MIRROR" push "$REMOTE" "$BRANCH"
fi

# --- 3) 复核 -----------------------------------------------------------------
say "推送完成，远端现状："
if [ -n "$HELPER" ] && [ -n "${GIT_TOKEN:-}" ]; then
    git -C "$MIRROR" -c credential.helper="$HELPER" ls-remote --heads "$REMOTE" "$BRANCH"
else
    git -C "$MIRROR" ls-remote --heads "$REMOTE" "$BRANCH"
fi
say "OK：镜像 $REMOTE/$BRANCH 已同步（源 $SRC_HEAD）。"
