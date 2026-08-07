#!/usr/bin/env bash
# =============================================================================
# NL2EARS 构建子系统环境准备脚本（幂等，可重复执行）
# 用法：sudo bash setup-build-env.sh <后端运行用户>，如 sudo bash setup-build-env.sh admin
# 说明：仅做环境准备，不启动服务；node:20-alpine 为沙箱基础镜像，必须在部署前预拉。
# =============================================================================
set -euo pipefail

RUN_USER="${1:-admin}"
RUNNING_USER="$(id -un)"

echo "==> 1/6 检查 / 添加 2G swap（幂等）"
if ! swapon --show | grep -q '/swapfile'; then
  if [ ! -f /swapfile ]; then
    fallocate -l 2G /swapfile
    chmod 600 /swapfile
    mkswap /swapfile >/dev/null
  fi
  swapon /swapfile
  if ! grep -q '/swapfile' /etc/fstab; then
    echo '/swapfile none swap sw 0 0' >> /etc/fstab
  fi
  echo "    2G swap 已启用"
else
  echo "    swap 已存在，跳过"
fi

echo "==> 2/6 将运行用户加入 docker 组"
if id -nG "$RUN_USER" | grep -qw docker; then
  echo "    ${RUN_USER} 已在 docker 组"
else
  usermod -aG docker "$RUN_USER"
  echo "    已添加。注意：${RUN_USER} 需重新登录（或重新 ssh）后 docker 组权限才生效"
fi

echo "==> 3/6 预拉沙箱基础镜像 node:20-alpine"
if docker image inspect node:20-alpine >/dev/null 2>&1; then
  echo "    镜像已存在"
else
  docker pull node:20-alpine
fi

echo "==> 4/6 PostgreSQL 降配建议（2 核 2G 机器，按需修改 postgresql.conf 后重启）"
echo "    shared_buffers = 128MB"
echo "    work_mem = 4MB"
echo "    max_connections = 20"
if [ "$RUNNING_USER" = "root" ]; then
  CONF=$(docker inspect userdb --format '{{range .Mounts}}{{.Source}}{{end}}' 2>/dev/null || true)
  if [ -n "$CONF" ] && [ -f "$CONF/postgresql.conf" ]; then
    sed -i 's/^#\?shared_buffers = .*/shared_buffers = 128MB/' "$CONF/postgresql.conf"
    sed -i 's/^#\?work_mem = .*/work_mem = 4MB/' "$CONF/postgresql.conf"
    sed -i 's/^#\?max_connections = .*/max_connections = 20/' "$CONF/postgresql.conf"
    echo "    已写入降配参数，请重启容器生效：docker restart userdb"
  else
    echo "    未找到 userdb 容器数据卷，请手动修改 postgresql.conf"
  fi
fi

echo "==> 5/6 每日自动清理 Docker（crontab）"
if crontab -l 2>/dev/null | grep -q 'docker system prune'; then
  echo "    已存在清理任务"
else
  (crontab -l 2>/dev/null; echo "0 4 * * * docker system prune -f >/dev/null 2>&1") | crontab -
  echo "    已添加每日 04:00 docker system prune -f"
fi

echo "==> 6/6 后端启动建议"
echo "    node --max-old-space-size=400 src/index.js"

echo ""
echo "环境准备完成。请确保："
echo "  1. 后端运行用户可访问 /var/run/docker.sock（本脚本已处理 docker 组，需重新登录）"
echo "  2. node:20-alpine 镜像已存在（docker image inspect node:20-alpine）"
echo "  3. 后端以最小内存启动：node --max-old-space-size=400 src/index.js"