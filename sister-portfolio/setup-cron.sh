#!/bin/bash
#
# 郑大姐实盘管家 - 自动推送Cron配置脚本
# 路径: /root/.openclaw/workspace/skills/sister-portfolio/setup-cron.sh
#

echo "📈 郑大姐实盘管家 - 自动推送配置"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 获取脚本路径
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PUSH_WATCH_CMD="cd $SCRIPT_DIR && ./portfolio.sh push-watch"
PUSH_POSITION_CMD="cd $SCRIPT_DIR && ./portfolio.sh push-position"

echo "📝 即将添加以下定时任务:"
echo ""
echo "1️⃣  自选股推送 (每30分钟)"
echo "   时间: 交易时段 9:30-11:30, 13:00-15:00"
echo "   频率: 每30分钟"
echo "   命令: $PUSH_WATCH_CMD"
echo ""
echo "2️⃣  持仓股推送 (每15分钟)"
echo "   时间: 交易时段 9:30-11:30, 13:00-15:00"
echo "   频率: 每15分钟"
echo "   命令: $PUSH_POSITION_CMD"
echo ""

read -p "确认添加这些定时任务? (y/n): " confirm

if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
    echo "❌ 已取消"
    exit 0
fi

# 创建临时crontab文件
TEMP_CRON=$(mktemp)

# 导出当前crontab
crontab -l > "$TEMP_CRON" 2>/dev/null || echo "# 新建crontab" > "$TEMP_CRON"

# 检查是否已存在相关任务
if grep -q "sister-portfolio" "$TEMP_CRON"; then
    echo ""
    echo "⚠️  检测到已存在相关定时任务"
    read -p "是否重新配置? (y/n): " reconfig
    if [ "$reconfig" != "y" ] && [ "$reconfig" != "Y" ]; then
        echo "❌ 已取消"
        rm "$TEMP_CRON"
        exit 0
    fi
    # 删除旧的任务
    grep -v "sister-portfolio" "$TEMP_CRON" > "${TEMP_CRON}.new"
    mv "${TEMP_CRON}.new" "$TEMP_CRON"
fi

# 添加新任务
cat >> "$TEMP_CRON" << EOF

# 郑大姐实盘管家 - 自动推送 (交易时段)
# 自选股推送 - 每30分钟
*/30 9-11,13-15 * * 1-5 $PUSH_WATCH_CMD >> /tmp/sister_portfolio_watch.log 2>&1
# 持仓股推送 - 每15分钟
*/15 9-11,13-15 * * 1-5 $PUSH_POSITION_CMD >> /tmp/sister_portfolio_position.log 2>&1
EOF

# 安装新的crontab
crontab "$TEMP_CRON"
rm "$TEMP_CRON"

echo ""
echo "✅ 定时任务已添加!"
echo ""
echo "📋 当前定时任务:"
crontab -l | grep -A 5 "郑大姐实盘管家"
echo ""
echo "💡 查看推送日志:"
echo "   tail -f /tmp/sister_portfolio_watch.log"
echo "   tail -f /tmp/sister_portfolio_position.log"
echo ""
echo "⚠️  注意:"
echo "   • 推送只在A股交易时段生效 (周一至周五 9:30-11:30, 13:00-15:00)"
echo "   • 非交易时段自动跳过"
echo "   • 如需取消，运行: crontab -e 删除相关行"
