#!/bin/bash
#
# 郑大姐股票分析日记本查阅工具
# 路径: /root/.openclaw/workspace/skills/stock-log-viewer/stock-log.sh
#

LOG_FILE="/root/.openclaw/workspace/memory/stock-analysis-log.md"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 显示帮助信息
show_help() {
    echo -e "${YELLOW}📔 郑大姐股票分析日记本查阅工具${NC}"
    echo ""
    echo "用法: stock-log.sh [命令] [参数]"
    echo ""
    echo "命令:"
    echo "  latest [n]       查看最新n条日记 (默认3条)"
    echo "  count            统计日记总数"
    echo "  date [YYYY-MM-DD] 按日期查询日记"
    echo "  stock [名称/代码] 按股票名称或代码查询"
    echo "  search [关键词]  全文搜索关键词"
    echo "  all              显示全部日记"
    echo "  help             显示帮助信息"
    echo ""
    echo "示例:"
    echo "  stock-log.sh latest 5        # 查看最新5条"
    echo "  stock-log.sh count           # 统计总数"
    echo "  stock-log.sh date 2026-02-18 # 查2月18日的分析"
    echo "  stock-log.sh stock 300605    # 查恒锋信息的分析"
    echo "  stock-log.sh search 低空经济 # 搜索含'低空经济'的日记"
}

# 检查日志文件是否存在
check_log_file() {
    if [ ! -f "$LOG_FILE" ]; then
        echo -e "${RED}❌ 日记本文件不存在: $LOG_FILE${NC}"
        echo "请确保已经完成过股票分析，日记本会自动生成。"
        exit 1
    fi
}

# 查看最新n条日记
show_latest() {
    local n=${1:-3}
    check_log_file
    
    echo -e "${YELLOW}📔 郑大姐股票分析日记本 - 最新${n}条${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    # 计算需要显示的行数 (每条记录大约15行)
    local lines=$((n * 15))
    tail -n "$lines" "$LOG_FILE" | grep -A 10 "^##" | head -n $((n * 12))
}

# 统计日记总数
show_count() {
    check_log_file
    
    local count=$(grep -c "^## " "$LOG_FILE" 2>/dev/null || echo "0")
    local total_lines=$(wc -l < "$LOG_FILE")
    local first_date=$(grep "^## " "$LOG_FILE" | head -1 | grep -oE '[0-9]{4}-[0-9]{2}-[0-9]{2}' || echo "暂无记录")
    local latest_date=$(grep "^## " "$LOG_FILE" | tail -1 | grep -oE '[0-9]{4}-[0-9]{2}-[0-9]{2}' || echo "暂无记录")
    
    echo -e "${YELLOW}📊 郑大姐日记本统计${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo -e "📁 日记本路径: ${BLUE}$LOG_FILE${NC}"
    echo -e "📝 分析记录数: ${GREEN}$count 条${NC}"
    echo -e "📄 总行数: $total_lines 行"
    echo -e "📅 最早记录: $first_date"
    echo -e "📅 最新记录: $latest_date"
    echo ""
    echo -e "${YELLOW}💡 提示: 使用 'stock-log.sh latest 5' 查看最新5条记录${NC}"
}

# 按日期查询
search_by_date() {
    local date_str=$1
    
    if [ -z "$date_str" ]; then
        echo -e "${RED}❌ 请提供日期参数，格式: YYYY-MM-DD${NC}"
        echo "示例: stock-log.sh date 2026-02-18"
        exit 1
    fi
    
    check_log_file
    
    echo -e "${YELLOW}📅 郑大姐日记本 - $date_str 的记录${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    # 搜索包含该日期的记录
    grep -B 1 -A 10 "## .*$date_str" "$LOG_FILE" || echo -e "${RED}❌ 未找到 $date_str 的记录${NC}"
}

# 按股票名称或代码查询
search_by_stock() {
    local keyword=$1
    
    if [ -z "$keyword" ]; then
        echo -e "${RED}❌ 请提供股票名称或代码${NC}"
        echo "示例: stock-log.sh stock 恒锋信息"
        echo "       stock-log.sh stock 300605"
        exit 1
    fi
    
    check_log_file
    
    echo -e "${YELLOW}🔍 郑大姐日记本 - 搜索: $keyword${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    # 搜索包含关键词的记录 (股票名称通常在 ## 行)
    local results=$(grep -n "## .*$keyword" "$LOG_FILE")
    
    if [ -z "$results" ]; then
        echo -e "${RED}❌ 未找到关于 '$keyword' 的记录${NC}"
        echo ""
        echo "💡 试试搜索相关关键词，或查看全部记录:"
        echo "   stock-log.sh all | grep -i $keyword"
    else
        echo -e "${GREEN}✅ 找到以下记录:${NC}"
        echo "$results" | while read -r line; do
            local line_num=$(echo "$line" | cut -d: -f1)
            local content=$(echo "$line" | cut -d: -f2-)
            echo ""
            echo "$content"
            # 显示该记录后续10行
            tail -n +$((line_num + 1)) "$LOG_FILE" | head -10
            echo "---"
        done
    fi
}

# 全文搜索
search_keyword() {
    local keyword=$1
    
    if [ -z "$keyword" ]; then
        echo -e "${RED}❌ 请提供搜索关键词${NC}"
        echo "示例: stock-log.sh search 低空经济"
        exit 1
    fi
    
    check_log_file
    
    echo -e "${YELLOW}🔍 郑大姐日记本 - 全文搜索: $keyword${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    # 全文搜索并显示上下文
    grep -i -B 2 -A 8 "$keyword" "$LOG_FILE" | grep -E "^## |^\*\*|$keyword" --color=auto || echo -e "${RED}❌ 未找到包含 '$keyword' 的记录${NC}"
}

# 显示全部日记
show_all() {
    check_log_file
    
    echo -e "${YELLOW}📔 郑大姐股票分析日记本 - 全部记录${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    cat "$LOG_FILE"
}

# 主函数
main() {
    local command=$1
    shift
    
    case "$command" in
        latest)
            show_latest "$1"
            ;;
        count)
            show_count
            ;;
        date)
            search_by_date "$1"
            ;;
        stock)
            search_by_stock "$1"
            ;;
        search)
            search_keyword "$1"
            ;;
        all)
            show_all
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            echo -e "${RED}❌ 未知命令: $command${NC}"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

# 如果没有参数，显示帮助信息
if [ $# -eq 0 ]; then
    show_help
    exit 0
fi

main "$@"
