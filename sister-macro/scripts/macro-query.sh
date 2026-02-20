#!/bin/bash
# 郑大姐宏观金融数据查询脚本
# 获取九大资产实时行情

echo "🌍 郑大姐宏观金融数据查询"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 获取实时数据的函数（使用web_search工具由主程序调用）
# 这里只是输出提示信息

echo "📊 请使用以下关键词进行搜索获取实时数据："
echo ""
echo "💵 美元体系："
echo "  - 美元指数 DXY 实时行情"
echo "  - 美债收益率 10年 2年 实时"
echo ""
echo "🪙 加密货币："
echo "  - 比特币 BTC 价格 实时"
echo "  - 以太坊 ETH 价格 实时"
echo ""
echo "🛢️ 大宗商品："
echo "  - 原油价格 WTI Brent 实时"
echo "  - 黄金价格 XAU 实时"
echo "  - 白银价格 XAG 实时"
echo ""
echo "🇯🇵 日本市场："
echo "  - 日元汇率 USD JPY 实时"
echo "  - 日债收益率 10年 实时"
echo ""
echo "🇨🇳 人民币资产："
echo "  - 人民币汇率 USD CNY 实时"
echo "  - 中国10年国债收益率 实时"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "建议使用 web_search 工具逐个查询"
