#!/usr/bin/env bash
# ============================================
# 2026世界杯 每日数据更新脚本
# 由 GitHub Actions 定时调用
#
# 工作流程:
#   1. 运行 Python 数据抓取脚本 (data-fetch.py)
#   2. 同步 index.html → docs/index.html
#   3. 列出待提交的变更（由 workflow 统一提交）
# ============================================
set -e

cd "$(dirname "$0")"
DATE=$(date '+%Y-%m-%d')
LOG="/tmp/wc2026-update-${DATE}.log"

echo "[${DATE}] 开始更新 2026 世界杯数据..." | tee -a "$LOG"

# ── 1. 运行数据抓取 ──────────────────────────
echo "→ 运行 data-fetch.py..." | tee -a "$LOG"
python3 data-fetch.py 2>&1 | tee -a "$LOG"

# ── 2. 重建 docs 目录 ─────────────────────────
echo "→ 同步到 docs 目录..." | tee -a "$LOG"
cp index.html docs/index.html

echo "" | tee -a "$LOG"
echo "✅ 更新完成 [${DATE}]" | tee -a "$LOG"
echo "   网页: $(pwd)/index.html" | tee -a "$LOG"
echo "   日志: ${LOG}" | tee -a "$LOG"
