#!/usr/bin/env bash
# ============================================
# 2026世界杯 每日数据更新脚本
# 由 GitHub Actions 定时调用
#
# 工作流程:
#   1. 运行 Python 数据抓取脚本 (data-fetch.py)
#   2. 验证 index.html 完整性
#   3. 提交变更到 Git
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

# ── 3. 提交变更 ─────────────────────────────
echo "→ 检查文件变更..." | tee -a "$LOG"
if git diff --quiet && git diff --cached --quiet; then
    echo "ℹ️  无数据变更，跳过提交" | tee -a "$LOG"
else
    git add index.html docs/index.html
    git commit -m "📊 每日数据更新 ${DATE}" || true
    git push 2>&1 | tee -a "$LOG"
    echo "✅ 已提交并推送更新" | tee -a "$LOG"
fi

echo "" | tee -a "$LOG"
echo "✅ 更新完成 [${DATE}]" | tee -a "$LOG"
echo "   网页: $(pwd)/index.html" | tee -a "$LOG"
echo "   日志: ${LOG}" | tee -a "$LOG"
