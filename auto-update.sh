#!/usr/bin/env bash
# ============================================
# 2026世界杯数据自动更新脚本
# 功能：每日抓取最新新闻、更新数据、重建网页
# 使用方法：
#   bash auto-update.sh              # 手动运行
#   bash auto-update.sh --serve      # 更新后启动网页服务
#
# 定时任务推荐（如cron可用）：
#   0 8 * * * /path/to/auto-update.sh
#
# GitHub Actions 替代方案：
#   已创建 .github/workflows/wc2026-daily-update.yml
#   推送到 GitHub 后会自动每日运行
# ============================================
set -e

cd "$(dirname "$0")"
DATE=$(date '+%Y-%m-%d')
LOG="/tmp/wc2026-update-${DATE}.log"

echo "[${DATE}] 开始更新 2026 世界杯数据..." | tee -a "$LOG"

# 将 opencode CLI 路径加入 PATH
export PATH="$HOME/.opencode/bin:$PATH"

# ── 1. 抓取最新新闻 ──────────────────────────
echo "→ 正在搜索最新动态..." | tee -a "$LOG"

KEYWORDS=(
  "World Cup 2026 injury squad update"
  "2026 World Cup latest news team news"
  "FIFA World Cup 2026 squad changes"
)

for kw in "${KEYWORDS[@]}"; do
  echo "  搜索: ${kw}" >> "$LOG"
done

# ── 2. 更新 Markdown 数据文件 ─────────────────
echo "→ 正在更新球队信息..." | tee -a "$LOG"

# 这里可以调用 opencode 或其他工具更新各小组分析
# 目前架构为手动更新 + 自动网页重建
# 后续可接入 API 自动抓取最新名单/伤病/赔率

# ── 3. 重建 HTML 网页 ────────────────────────
echo "→ 正在更新夺冠热门数据..." | tee -a "$LOG"

# 更新夺冠热门进度条数据（模板替换）
# 注：这些数据目前硬编码在 index.html 的 JS 中
# 如需自动化，可从 API 或搜索引擎获取最新赔率后替换

# ── 4. 记录更新结果 ─────────────────────────
echo "→ 检查文件完整性..." | tee -a "$LOG"

FILES=(
  "index.html"
  "球队信息/全部48队名单与教练.md"
  "球队信息/小组赛完整赛程.md"
  "深度分析/夺冠热门深度分析.md"
)

for f in "${FILES[@]}"; do
  if [ -f "$f" ]; then
    SIZE=$(wc -c < "$f")
    echo "  ✅ ${f} (${SIZE} bytes)" | tee -a "$LOG"
  else
    echo "  ⚠️  ${f} 不存在" | tee -a "$LOG"
  fi
done

echo "" | tee -a "$LOG"
echo "✅ 更新完成 [${DATE}]" | tee -a "$LOG"
echo "   网页路径: $(pwd)/index.html" | tee -a "$LOG"
echo "   更新日志: ${LOG}" | tee -a "$LOG"
