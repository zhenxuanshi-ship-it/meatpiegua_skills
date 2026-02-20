#!/bin/bash

# A股实时数据查询脚本
# 使用腾讯财经接口

if [ $# -eq 0 ]; then
    echo "Usage: $0 <股票代码1,股票代码2,...>"
    echo "Example: $0 002340"
    echo "Example: $0 002340,601857,300102"
    exit 1
fi

CODES=$1
URL="http://qt.gtimg.cn/q=${CODES}"

# 获取数据并转换编码
data=$(curl -s "$URL" | iconv -f GBK -t UTF-8 2>/dev/null)

if [ -z "$data" ]; then
    echo "获取数据失败"
    exit 1
fi

# 解析并输出
IFS=';' read -ra STOCKS <<< "$data"

for stock in "${STOCKS[@]}"; do
    if [[ ! $stock =~ v_ ]]; then
        continue
    fi
    
    # 提取数据部分
    data_str=$(echo "$stock" | grep -o '"[^"]*"' | head -1 | tr -d '"')
    
    if [ -z "$data_str" ]; then
        continue
    fi
    
    # 分割字段
    IFS='~' read -ra FIELDS <<< "$data_str"
    
    if [ ${#FIELDS[@]} -lt 45 ]; then
        continue
    fi
    
    name=${FIELDS[1]}
    code=${FIELDS[2]}
    current=${FIELDS[3]}
    close=${FIELDS[4]}
    open=${FIELDS[5]}
    high=${FIELDS[33]}
    low=${FIELDS[34]}
    volume=${FIELDS[6]}
    amount=${FIELDS[37]}
    change_percent=${FIELDS[32]}
    buy1_price=${FIELDS[9]}
    buy1_vol=${FIELDS[10]}
    sell1_price=${FIELDS[19]}
    sell1_vol=${FIELDS[20]}
    
    # 计算涨跌
    change=$(echo "$current - $close" | bc)
    
    # 格式化
    if (( $(echo "$change >= 0" | bc -l) )); then
        emoji="📈"
        change_str="+${change}"
    else
        emoji="📉"
        change_str="${change}"
    fi
    
    # 转换成交量（手->万手）
    volume_wan=$(echo "scale=2; $volume / 100" | bc)
    
    # 输出
    echo "📊 ${name} (${code}) ${emoji}"
    echo "━━━━━━━━━━━━━━━━━━━━━━"
    echo "现价：${current}元"
    echo "涨跌：${change_str} (${change_percent}%)"
    echo "今开：${open}元"
    echo "最高：${high}元"
    echo "最低：${low}元"
    echo "昨收：${close}元"
    echo "━━━━━━━━━━━━━━━━━━━━━━"
    echo "成交量：${volume_wan}万手"
    echo "成交额：${amount}万"
    echo "━━━━━━━━━━━━━━━━━━━━━━"
    echo "买一：${buy1_price} (${buy1_vol}手)"
    echo "卖一：${sell1_price} (${sell1_vol}手)"
    echo "━━━━━━━━━━━━━━━━━━━━━━"
    echo "数据来源：腾讯财经 | 延迟约15分钟"
    echo ""
done
