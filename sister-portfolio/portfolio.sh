#!/bin/bash
#
# 郑大姐实盘管家 - 主脚本
# 路径: /root/.openclaw/workspace/skills/sister-portfolio/portfolio.sh
#

DATA_DIR="/root/.openclaw/workspace/memory/portfolio"
WATCHLIST_FILE="$DATA_DIR/watchlist.json"
POSITIONS_FILE="$DATA_DIR/positions.json"
TAGS_FILE="$DATA_DIR/tags.json"
HISTORY_FILE="$DATA_DIR/trade_history.json"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# 初始化数据目录
init_data_dir() {
    if [ ! -d "$DATA_DIR" ]; then
        mkdir -p "$DATA_DIR"
        echo -e "${GREEN}✅ 初始化数据目录: $DATA_DIR${NC}"
    fi
    
    # 初始化JSON文件
    [ ! -f "$WATCHLIST_FILE" ] && echo '{"stocks": []}' > "$WATCHLIST_FILE"
    [ ! -f "$POSITIONS_FILE" ] && echo '{"stocks": []}' > "$POSITIONS_FILE"
    [ ! -f "$TAGS_FILE" ] && echo '{"tags": {}}' > "$TAGS_FILE"
    [ ! -f "$HISTORY_FILE" ] && echo '{"trades": []}' > "$HISTORY_FILE"
}

# 显示帮助信息
show_help() {
    echo -e "${YELLOW}📈 郑大姐实盘管家${NC}"
    echo ""
    echo "用法: portfolio.sh [命令] [参数]"
    echo ""
    echo "${CYAN}【自选股管理】${NC}"
    echo "  add-watch [代码] [名称]      添加自选股"
    echo "  remove-watch [代码]          删除自选股"
    echo "  list-watch                   列出自选股"
    echo ""
    echo "${CYAN}【持仓股管理】${NC}"
    echo "  add-position [代码] [名称] [数量] [成本价]  添加持仓"
    echo "  remove-position [代码]       删除持仓"
    echo "  list-position                列出持仓"
    echo "  buy [代码] [数量] [价格]     买入记录"
    echo "  sell [代码] [数量] [价格]    卖出记录"
    echo ""
    echo "${CYAN}【标签管理】${NC}"
    echo "  add-tag [代码] [标签名]      给股票打标签"
    echo "  remove-tag [代码] [标签名]   删除标签"
    echo "  list-tags                    列出所有标签"
    echo "  show-tag [标签名]            显示标签下的股票"
    echo ""
    echo "${CYAN}【数据查询】${NC}"
    echo "  query [代码]                 查询股票实时数据"
    echo "  stats                        统计持仓盈亏"
    echo "  history [代码]               查询交易历史"
    echo ""
    echo "${CYAN}【推送功能】${NC}"
    echo "  push-watch                   推送自选股报告（30分钟）"
    echo "  push-position                推送持仓股报告（15分钟）"
    echo "  check-trading-hours          检查是否交易时段"
    echo ""
    echo "示例:"
    echo "  portfolio.sh add-watch 300605 恒锋信息"
    echo "  portfolio.sh add-position 002594 比亚迪 1000 85.50"
    echo "  portfolio.sh buy 002594 500 90.20"
    echo "  portfolio.sh list-tags"
    echo ""
}

# 检查是否交易时段
check_trading_hours() {
    # 获取当前时间（东八区）
    local hour=$(date +%-H)   # %-H 去掉前导零
    local minute=$(date +%-M) # %-M 去掉前导零
    local weekday=$(date +%u)  # 1-5是周一到周五
    local current_time=$((hour * 60 + minute))
    
    # 上午交易时段: 09:30 - 11:30 (570-690分钟)
    # 下午交易时段: 13:00 - 15:00 (780-900分钟)
    local morning_start=570
    local morning_end=690
    local afternoon_start=780
    local afternoon_end=900
    
    # 检查是否为工作日
    if [ "$weekday" -gt 5 ]; then
        echo -e "${YELLOW}⏰ 非交易日（周末）${NC}"
        return 1
    fi
    
    # 检查是否在交易时段
    if ([ $current_time -ge $morning_start ] && [ $current_time -le $morning_end ]) || \
       ([ $current_time -ge $afternoon_start ] && [ $current_time -le $afternoon_end ]); then
        echo -e "${GREEN}✅ 交易时段中${NC}"
        return 0
    else
        echo -e "${YELLOW}⏰ 非交易时段${NC}"
        return 1
    fi
}

# 添加自选股
add_watch() {
    local code=$1
    local name=$2
    
    if [ -z "$code" ] || [ -z "$name" ]; then
        echo -e "${RED}❌ 参数错误！用法: add-watch [代码] [名称]${NC}"
        return 1
    fi
    
    # 检查是否已存在
    if grep -q "\"code\": \"$code\"" "$WATCHLIST_FILE"; then
        echo -e "${YELLOW}⚠️  $code 已在自选股列表中${NC}"
        return 1
    fi
    
    # 自动打标签（基于股票代码）
    local tags=$(auto_tag "$code" "$name")
    
    # 添加到JSON
    local timestamp=$(date '+%Y-%m-%d %H:%M')
    local new_stock="{\"code\": \"$code\", \"name\": \"$name\", \"tags\": [$tags], \"added_time\": \"$timestamp\"}"
    
    # 使用jq或sed更新JSON
    python3 << EOF
import json
with open('$WATCHLIST_FILE', 'r', encoding='utf-8') as f:
    data = json.load(f)

data['stocks'].append($new_stock)

with open('$WATCHLIST_FILE', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
EOF
    
    echo -e "${GREEN}✅ 已添加自选股: $name ($code)${NC}"
    echo -e "${BLUE}🏷️  自动标签: $tags${NC}"
}

# 精准标签数据库文件
STOCK_TAGS_FILE="$DATA_DIR/stock_tags.txt"

# 初始化标签数据库
init_stock_tags() {
    if [ ! -f "$STOCK_TAGS_FILE" ]; then
        cat > "$STOCK_TAGS_FILE" << 'EOF'
# 格式: 代码|名称|标签1,标签2,标签3
# 新能源
002594|比亚迪|新能源汽车,动力电池,整车制造
300014|亿纬锂能|锂电池,储能,新能源
002460|赣锋锂业|锂电池,锂资源,新能源
002466|天齐锂业|锂电池,锂资源,新能源
002709|天赐材料|锂电池,电解液,新能源
300073|当升科技|锂电池,正极材料,新能源
002340|格林美|锂电池回收,镍资源,新能源
600089|特变电工|输变电设备,光伏硅料,新能源
601012|隆基绿能|光伏组件,光伏设备,新能源
600438|通威股份|光伏硅料,光伏电池,新能源
300274|阳光电源|光伏逆变器,储能,新能源
002202|金风科技|风电设备,风力发电,新能源
# AI科技
300605|恒锋信息|智慧城市,AI应用,软件服务
300010|豆神教育|AI教育,在线教育,人工智能
002230|科大讯飞|AI语音,人工智能,教育
000938|中科曙光|AI算力,服务器,信创
603019|浪潮信息|AI算力,服务器,信创
601138|工业富联|AI服务器,云计算,消费电子
002236|大华股份|AI视觉,安防监控,人工智能
002415|海康威视|AI视觉,安防监控,人工智能
# 半导体
688981|中芯国际|晶圆代工,半导体,芯片制造
603501|韦尔股份|半导体,图像传感器,芯片设计
002371|北方华创|半导体设备,芯片设备,国产替代
688012|中微公司|半导体设备,刻蚀机,国产替代
# 医药
600276|恒瑞医药|创新药,医药研发,医药龙头
300760|迈瑞医疗|医疗器械,医疗设备,医疗龙头
# 军工
600760|中航沈飞|军工,战斗机,航空装备
600893|航发动力|军工,航空发动机,航空装备
# 消费
600519|贵州茅台|白酒,大消费,食品饮料
000858|五粮液|白酒,大消费,食品饮料
000333|美的集团|家电,大消费,智能家居
EOF
    fi
}

# 从标签数据库获取股票标签
get_stock_tags_from_db() {
    local code=$1
    local name=$2
    
    # 初始化数据库
    init_stock_tags
    
    # 查询标签
    local result=$(grep "^$code|" "$STOCK_TAGS_FILE" 2>/dev/null)
    
    if [ -n "$result" ]; then
        # 提取标签部分
        echo "$result" | cut -d'|' -f3
        return 0
    else
        return 1
    fi
}

# 添加股票到标签数据库
add_stock_to_tag_db() {
    local code=$1
    local name=$2
    local tags=$3
    
    init_stock_tags
    
    # 检查是否已存在
    if grep -q "^$code|" "$STOCK_TAGS_FILE"; then
        # 更新现有条目
        sed -i "s/^$code|.*/$code|$name|$tags/" "$STOCK_TAGS_FILE"
    else
        # 添加新条目
        echo "$code|$name|$tags" >> "$STOCK_TAGS_FILE"
    fi
}

# 自动打标签函数（精准版）
auto_tag() {
    local code=$1
    local name=$2
    local tags=""
    
    # 基于代码前缀判断板块
    case ${code:0:2} in
        60) tags="\"沪主板\"" ;;
        00) tags="\"深主板\"" ;;
        30) tags="\"创业板\"" ;;
        68) tags="\"科创板\"" ;;
        8|4) tags="\"北交所\"" ;;
    esac
    
    # 优先从精准标签库获取
    local stock_tags=$(get_stock_tags_from_db "$code" "$name")
    
    if [ -n "$stock_tags" ]; then
        # 将逗号分隔的标签转换为JSON格式
        IFS=',' read -ra TAG_ARRAY <<< "$stock_tags"
        for tag in "${TAG_ARRAY[@]}"; do
            tag=$(echo "$tag" | xargs)  # 去除首尾空格
            tags="$tags, \"$tag\""
        done
    else
        # 如果精准库中没有，基于名称关键词判断（备用）
        if echo "$name" | grep -qiE "科技|信息|软件|网络|智能"; then
            tags="$tags, \"AI科技\""
        fi
        if echo "$name" | grep -qiE "新能|光伏|锂电|储|氢"; then
            tags="$tags, \"新能源\""
        fi
        if echo "$name" | grep -qiE "医药|医疗|生物|药"; then
            tags="$tags, \"医药医疗\""
        fi
        if echo "$name" | grep -qiE "银行|证券|保险|金融"; then
            tags="$tags, \"大金融\""
        fi
        if echo "$name" | grep -qiE "军工|航天|船舶|航空"; then
            tags="$tags, \"军工\""
        fi
        if echo "$name" | grep -qiE "消费|食品|饮料|家电|白酒"; then
            tags="$tags, \"大消费\""
        fi
        if echo "$name" | grep -qiE "资源|有色|稀土|煤炭|钢铁"; then
            tags="$tags, \"周期资源\""
        fi
        if echo "$name" | grep -qiE "地产|建筑|建材|基建"; then
            tags="$tags, \"地产基建\""
        fi
        if echo "$name" | grep -qiE "汽车|比亚迪|赛力斯"; then
            tags="$tags, \"新能源汽车\""
        fi
        if echo "$name" | grep -qiE "机器人|减速器|电机|自动化"; then
            tags="$tags, \"人形机器人\""
        fi
        if echo "$name" | grep -qiE "芯片|半导体|集成电路|电子"; then
            tags="$tags, \"半导体\""
        fi
    fi
    
    # 移除开头的逗号
    tags=$(echo "$tags" | sed 's/^, //')
    
    echo "$tags"
}

# 添加/更新股票标签到数据库（永久保存）
add_stock_tag() {
    local code=$1
    local name=$2
    local tag_string=$3
    
    if [ -z "$code" ] || [ -z "$name" ] || [ -z "$tag_string" ]; then
        echo -e "${RED}❌ 参数错误！用法: add-stock-tag [代码] [名称] [标签1,标签2,标签3]${NC}"
        return 1
    fi
    
    # 添加到精准标签库（永久保存到文件）
    add_stock_to_tag_db "$code" "$name" "$tag_string"
    
    echo -e "${GREEN}✅ 已添加/更新 $name ($code) 的标签: $tag_string${NC}"
    echo -e "${CYAN}💡 标签已永久保存到数据库${NC}"
}

# 刷新所有股票标签
refresh_all_tags() {
    init_data_dir
    
    echo -e "${YELLOW}🔄 刷新所有股票标签...${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    python3 << EOF
import json

try:
    # 读取watchlist
    with open('$WATCHLIST_FILE', 'r', encoding='utf-8') as f:
        watch_data = json.load(f)
    
    # 读取positions
    with open('$POSITIONS_FILE', 'r', encoding='utf-8') as f:
        pos_data = json.load(f)
    
    updated_count = 0
    
    # 更新watchlist中的标签
    for stock in watch_data['stocks']:
        code = stock['code']
        name = stock['name']
        
        # 获取新标签
        import subprocess
        result = subprocess.run(
            ['bash', '-c', f'source $0 && auto_tag "{code}" "{name}"'],
            capture_output=True,
            text=True,
            cwd='/root/.openclaw/workspace/skills/sister-portfolio'
        )
        new_tags_str = result.stdout.strip()
        
        # 解析标签
        import re
        new_tags = re.findall(r'"([^"]+)"', new_tags_str)
        
        if new_tags and new_tags != stock.get('tags', []):
            old_tags = stock.get('tags', [])
            stock['tags'] = new_tags
            updated_count += 1
            print(f"✅ {name} ({code}): {old_tags} → {new_tags}")
    
    # 更新positions中的标签
    for stock in pos_data['stocks']:
        code = stock['code']
        name = stock['name']
        
        # 获取新标签
        import subprocess
        result = subprocess.run(
            ['bash', '-c', f'source $0 && auto_tag "{code}" "{name}"'],
            capture_output=True,
            text=True,
            cwd='/root/.openclaw/workspace/skills/sister-portfolio'
        )
        new_tags_str = result.stdout.strip()
        
        # 解析标签
        import re
        new_tags = re.findall(r'"([^"]+)"', new_tags_str)
        
        if new_tags and new_tags != stock.get('tags', []):
            old_tags = stock.get('tags', [])
            stock['tags'] = new_tags
            updated_count += 1
            print(f"✅ {name} ({code}): {old_tags} → {new_tags}")
    
    # 保存更新后的数据
    with open('$WATCHLIST_FILE', 'w', encoding='utf-8') as f:
        json.dump(watch_data, f, ensure_ascii=False, indent=2)
    
    with open('$POSITIONS_FILE', 'w', encoding='utf-8') as f:
        json.dump(pos_data, f, ensure_ascii=False, indent=2)
    
    if updated_count > 0:
        print(f"\n${GREEN}✅ 共更新 {updated_count} 只股票的标签${NC}")
    else:
        print(f"${YELLOW}ℹ️ 所有标签已是最新${NC}")
        
except Exception as e:
    print(f"${RED}❌ 更新失败: {e}${NC}")
EOF
}

# 显示股票详细信息（包括业务标签）
show_stock_info() {
    local code=$1
    
    if [ -z "$code" ]; then
        echo -e "${RED}❌ 参数错误！用法: show-stock-info [代码]${NC}"
        return 1
    fi
    
    init_data_dir
    
    # 从数据库获取标签
    local stock_tags=$(get_stock_tags_from_db "$code" "")
    
    if [ -n "$stock_tags" ]; then
        # 从数据库文件获取名称
        local name=$(grep "^$code|" "$STOCK_TAGS_FILE" | cut -d'|' -f2)
        
        echo -e "${CYAN}📊 股票详细信息${NC}"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo -e "代码: ${GREEN}$code${NC}"
        echo -e "名称: ${GREEN}$name${NC}"
        echo -e "核心业务标签: ${YELLOW}$stock_tags${NC}"
        echo ""
        echo -e "${CYAN}💡 业务说明:${NC}"
        
        # 根据标签输出业务说明
        if echo "$stock_tags" | grep -q "锂电池"; then
            echo "• 主营业务: 锂电池材料/制造/回收"
            echo "• 行业地位: 新能源产业链核心环节"
            echo "• 关注要点: 原材料价格、产能利用率、客户订单"
        elif echo "$stock_tags" | grep -q "光伏"; then
            echo "• 主营业务: 光伏硅料/硅片/组件/设备"
            echo "• 行业地位: 光伏产业链关键环节"
            echo "• 关注要点: 硅料价格、装机需求、政策支持"
        elif echo "$stock_tags" | grep -q "AI"; then
            echo "• 主营业务: 人工智能软件/应用/服务"
            echo "• 行业地位: AI产业链应用层"
            echo "• 关注要点: 订单落地、技术迭代、商业化进度"
        elif echo "$stock_tags" | grep -q "半导体"; then
            echo "• 主营业务: 半导体设计/制造/设备/材料"
            echo "• 行业地位: 国产替代核心标的"
            echo "• 关注要点: 国产替代进度、下游需求、技术突破"
        elif echo "$stock_tags" | grep -q "新能源"; then
            echo "• 主营业务: 新能源相关产业"
            echo "• 行业地位: 新能源产业链"
            echo "• 关注要点: 政策变化、原材料价格、产能扩张"
        else
            echo "• 详见公司业务公告"
        fi
    else
        echo -e "${YELLOW}⚠️ 暂无 $code 的详细信息，使用名称关键词匹配${NC}"
    fi
}

# 列出自选股
list_watch() {
    init_data_dir
    
    echo -e "${YELLOW}📋 自选股列表${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    python3 << EOF
import json
try:
    with open('$WATCHLIST_FILE', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    stocks = data.get('stocks', [])
    if not stocks:
        print("${YELLOW}暂无自选股${NC}")
    else:
        print(f"${GREEN}共 {len(stocks)} 只自选股${NC}\n")
        for i, stock in enumerate(stocks, 1):
            code = stock.get('code', '')
            name = stock.get('name', '')
            tags = ', '.join(stock.get('tags', []))
            print(f"{i}. {name} ({code})")
            print(f"   🏷️ 标签: {tags}")
            print()
except Exception as e:
    print(f"${RED}读取失败: {e}${NC}")
EOF
}

# 添加持仓
add_position() {
    local code=$1
    local name=$2
    local quantity=$3
    local cost=$4
    
    if [ -z "$code" ] || [ -z "$name" ] || [ -z "$quantity" ] || [ -z "$cost" ]; then
        echo -e "${RED}❌ 参数错误！用法: add-position [代码] [名称] [数量] [成本价]${NC}"
        return 1
    fi
    
    init_data_dir
    
    # 自动打标签
    local tags=$(auto_tag "$code" "$name")
    
    local timestamp=$(date '+%Y-%m-%d %H:%M')
    local total_cost=$(echo "$quantity * $cost" | bc)
    
    local new_position="{\"code\": \"$code\", \"name\": \"$name\", \"quantity\": $quantity, \"cost_price\": $cost, \"total_cost\": $total_cost, \"tags\": [$tags], \"added_time\": \"$timestamp\"}"
    
    python3 << EOF
import json
with open('$POSITIONS_FILE', 'r', encoding='utf-8') as f:
    data = json.load(f)

data['stocks'].append($new_position)

with open('$POSITIONS_FILE', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
EOF
    
    # 记录交易
    record_trade "$code" "$name" "buy" "$quantity" "$cost" "$total_cost"
    
    echo -e "${GREEN}✅ 已添加持仓: $name ($code)${NC}"
    echo -e "   📊 数量: $quantity 股"
    echo -e "   💰 成本价: ¥$cost"
    echo -e "   💵 总成本: ¥$total_cost"
}

# 列出持仓
list_position() {
    init_data_dir
    
    echo -e "${YELLOW}💼 持仓列表${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    python3 << EOF
import json
try:
    with open('$POSITIONS_FILE', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    stocks = data.get('stocks', [])
    if not stocks:
        print("${YELLOW}暂无持仓${NC}")
    else:
        total_cost = sum(float(s.get('total_cost', 0)) for s in stocks)
        print(f"${GREEN}共 {len(stocks)} 只持仓股，总成本: ¥{total_cost:.2f}${NC}\n")
        for i, stock in enumerate(stocks, 1):
            code = stock.get('code', '')
            name = stock.get('name', '')
            quantity = stock.get('quantity', 0)
            cost = stock.get('cost_price', 0)
            tags = ', '.join(stock.get('tags', []))
            print(f"{i}. {name} ({code})")
            print(f"   📊 持仓: {quantity} 股 @ ¥{cost}")
            print(f"   🏷️ 标签: {tags}")
            print()
except Exception as e:
    print(f"${RED}读取失败: {e}${NC}")
EOF
}

# 记录交易
record_trade() {
    local code=$1
    local name=$2
    local type=$3
    local quantity=$4
    local price=$5
    local total=$6
    
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    local trade="{\"time\": \"$timestamp\", \"code\": \"$code\", \"name\": \"$name\", \"type\": \"$type\", \"quantity\": $quantity, \"price\": $price, \"total\": $total}"
    
    python3 << EOF
import json
with open('$HISTORY_FILE', 'r', encoding='utf-8') as f:
    data = json.load(f)

data['trades'].append($trade)

with open('$HISTORY_FILE', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
EOF
}

# 买入记录
buy_stock() {
    local code=$1
    local quantity=$2
    local price=$3
    
    if [ -z "$code" ] || [ -z "$quantity" ] || [ -z "$price" ]; then
        echo -e "${RED}❌ 参数错误！用法: buy [代码] [数量] [价格]${NC}"
        return 1
    fi
    
    init_data_dir
    local total=$(echo "$quantity * $price" | bc)
    
    # 获取股票名称
    local name=$(python3 << EOF
import json
try:
    with open('$POSITIONS_FILE', 'r', encoding='utf-8') as f:
        data = json.load(f)
    for s in data['stocks']:
        if s['code'] == '$code':
            print(s['name'])
            break
except:
    print('$code')
EOF
)
    
    record_trade "$code" "$name" "buy" "$quantity" "$price" "$total"
    
    echo -e "${GREEN}✅ 买入记录已保存${NC}"
    echo -e "   📊 $name ($code)"
    echo -e "   🛒 买入: $quantity 股 @ ¥$price"
    echo -e "   💵 金额: ¥$total"
}

# 卖出记录
sell_stock() {
    local code=$1
    local quantity=$2
    local price=$3
    
    if [ -z "$code" ] || [ -z "$quantity" ] || [ -z "$price" ]; then
        echo -e "${RED}❌ 参数错误！用法: sell [代码] [数量] [价格]${NC}"
        return 1
    fi
    
    init_data_dir
    local total=$(echo "$quantity * $price" | bc)
    
    # 获取股票名称
    local name=$(python3 << EOF
import json
try:
    with open('$POSITIONS_FILE', 'r', encoding='utf-8') as f:
        data = json.load(f)
    for s in data['stocks']:
        if s['code'] == '$code':
            print(s['name'])
            break
except:
    print('$code')
EOF
)
    
    record_trade "$code" "$name" "sell" "$quantity" "$price" "$total"
    
    echo -e "${GREEN}✅ 卖出记录已保存${NC}"
    echo -e "   📊 $name ($code)"
    echo -e "   💰 卖出: $quantity 股 @ ¥$price"
    echo -e "   💵 金额: ¥$total"
}

# 列标签
list_tags() {
    init_data_dir
    
    echo -e "${YELLOW}🏷️  标签列表${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    python3 << EOF
import json
from collections import defaultdict

try:
    # 收集所有标签
    all_tags = defaultdict(list)
    
    # 从自选股收集
    with open('$WATCHLIST_FILE', 'r', encoding='utf-8') as f:
        watch_data = json.load(f)
    for s in watch_data.get('stocks', []):
        for tag in s.get('tags', []):
            all_tags[tag].append(f"{s['name']}({s['code']})-自选")
    
    # 从持仓股收集
    with open('$POSITIONS_FILE', 'r', encoding='utf-8') as f:
        pos_data = json.load(f)
    for s in pos_data.get('stocks', []):
        for tag in s.get('tags', []):
            all_tags[tag].append(f"{s['name']}({s['code']})-持仓")
    
    if not all_tags:
        print("${YELLOW}暂无标签${NC}")
    else:
        print(f"${GREEN}共 {len(all_tags)} 个标签${NC}\n")
        for tag, stocks in sorted(all_tags.items()):
            print(f"📌 {tag}: {len(stocks)} 只")
            for stock in stocks:
                print(f"   • {stock}")
            print()
except Exception as e:
    print(f"${RED}读取失败: {e}${NC}")
EOF
}

# 显示标签下的股票
show_tag() {
    local tag_name=$1
    
    if [ -z "$tag_name" ]; then
        echo -e "${RED}❌ 请提供标签名${NC}"
        echo "用法: show-tag [标签名]"
        return 1
    fi
    
    echo -e "${YELLOW}🏷️  标签: $tag_name${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    python3 << EOF
import json

try:
    # 从自选股和持仓股中筛选
    result = []
    
    with open('$WATCHLIST_FILE', 'r', encoding='utf-8') as f:
        watch_data = json.load(f)
    for s in watch_data.get('stocks', []):
        if '$tag_name' in s.get('tags', []):
            result.append(f"📋 {s['name']} ({s['code']}) - 自选")
    
    with open('$POSITIONS_FILE', 'r', encoding='utf-8') as f:
        pos_data = json.load(f)
    for s in pos_data.get('stocks', []):
        if '$tag_name' in s.get('tags', []):
            result.append(f"💼 {s['name']} ({s['code']}) - 持仓 ({s['quantity']}股)")
    
    if not result:
        print("${YELLOW}该标签下暂无股票${NC}")
    else:
        print(f"${GREEN}共 {len(result)} 只股票${NC}\n")
        for item in result:
            print(item)
except Exception as e:
    print(f"${RED}读取失败: {e}${NC}")
EOF
}

# 查询实时数据（简化版）
query_stock() {
    local code=$1
    
    if [ -z "$code" ]; then
        echo -e "${RED}❌ 请提供股票代码${NC}"
        return 1
    fi
    
    echo -e "${YELLOW}📊 查询实时数据: $code${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    # 调用股票查询脚本
    if [ -f "/root/.openclaw/workspace/skills/a股实时数据/stock-query.sh" ]; then
        /root/.openclaw/workspace/skills/a股实时数据/stock-query.sh "sz$code" 2>/dev/null || \
        /root/.openclaw/workspace/skills/a股实时数据/stock-query.sh "sh$code" 2>/dev/null || \
        echo -e "${YELLOW}⚠️  无法获取实时数据，请检查代码是否正确${NC}"
    else
        echo -e "${YELLOW}⚠️  股票查询工具未安装${NC}"
    fi
}

# 统计盈亏
show_stats() {
    init_data_dir
    
    echo -e "${YELLOW}📈 持仓盈亏统计${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo -e "${YELLOW}（注：需要实时股价数据，请配合query命令使用）${NC}"
    
    python3 << EOF
import json

try:
    with open('$POSITIONS_FILE', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    stocks = data.get('stocks', [])
    if not stocks:
        print("${YELLOW}暂无持仓${NC}")
        return
    
    total_cost = sum(float(s.get('total_cost', 0)) for s in stocks)
    print(f"${GREEN}总持仓成本: ¥{total_cost:.2f}${NC}")
    print(f"${GREEN}持仓股票数: {len(stocks)} 只${NC}\n")
    
    for s in stocks:
        print(f"• {s['name']} ({s['code']}): {s['quantity']}股 @ ¥{s['cost_price']}")
    
    print(f"\n${CYAN}💡 使用 'portfolio.sh query [代码]' 查询实时盈亏${NC}")
except Exception as e:
    print(f"${RED}读取失败: {e}${NC}")
EOF
}

# 推送自选股报告
push_watch_report() {
    # 检查是否交易时段
    if ! check_trading_hours > /dev/null 2>&1; then
        echo -e "${YELLOW}⏰ 非交易时段，跳过推送${NC}"
        return 0
    fi
    
    init_data_dir
    
    echo -e "${YELLOW}📊 郑大姐自选股监控报告${NC} ($(date '+%H:%M'))"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    python3 << EOF
import json

try:
    with open('$WATCHLIST_FILE', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    stocks = data.get('stocks', [])
    if not stocks:
        print("暂无自选股")
    else:
        print(f"监控 {len(stocks)} 只自选股\n")
        for s in stocks:
            print(f"• {s['name']} ({s['code']})")
        print(f"\n${CYAN}【操作建议】${NC}")
        print("请使用 'portfolio.sh query [代码]' 查询实时数据和技术分析")
except Exception as e:
    print(f"报告生成失败: {e}")
EOF
}

# 推送持仓报告
push_position_report() {
    # 检查是否交易时段
    if ! check_trading_hours > /dev/null 2>&1; then
        echo -e "${YELLOW}⏰ 非交易时段，跳过推送${NC}"
        return 0
    fi
    
    init_data_dir
    
    echo -e "${YELLOW}💼 郑大姐持仓监控报告${NC} ($(date '+%H:%M'))"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    python3 << EOF
import json

try:
    with open('$POSITIONS_FILE', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    stocks = data.get('stocks', [])
    if not stocks:
        print("暂无持仓")
    else:
        total_cost = sum(float(s.get('total_cost', 0)) for s in stocks)
        print(f"共 {len(stocks)} 只持仓，总成本 ¥{total_cost:.2f}\n")
        for s in stocks:
            print(f"• {s['name']} ({s['code']}): {s['quantity']}股 @ ¥{s['cost_price']}")
        print(f"\n${CYAN}【盈亏监控】${NC}")
        print("请使用 'portfolio.sh query [代码]' 查询实时盈亏")
except Exception as e:
    print(f"报告生成失败: {e}")
EOF
}

# 主函数
main() {
    local command=$1
    shift
    
    init_data_dir
    
    case "$command" in
        add-watch)
            add_watch "$1" "$2"
            ;;
        remove-watch)
            echo "删除自选股功能待实现"
            ;;
        list-watch)
            list_watch
            ;;
        add-position)
            add_position "$1" "$2" "$3" "$4"
            ;;
        remove-position)
            echo "删除持仓功能待实现"
            ;;
        list-position)
            list_position
            ;;
        buy)
            buy_stock "$1" "$2" "$3"
            ;;
        sell)
            sell_stock "$1" "$2" "$3"
            ;;
        add-tag)
            echo "添加标签功能待实现"
            ;;
        remove-tag)
            echo "删除标签功能待实现"
            ;;
        list-tags)
            list_tags
            ;;
        show-tag)
            show_tag "$1"
            ;;
        show-stock-info)
            show_stock_info "$1"
            ;;
        add-stock-tag)
            add_stock_tag "$1" "$2" "$3"
            ;;
        refresh-tags)
            refresh_all_tags
            ;;
        query)
            query_stock "$1"
            ;;
        stats)
            show_stats
            ;;
        history)
            echo "交易历史查询功能待实现"
            ;;
        push-watch)
            push_watch_report
            ;;
        push-position)
            push_position_report
            ;;
        check-trading-hours)
            check_trading_hours
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
