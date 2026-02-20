#!/bin/bash
# 知乎文章发布助手
# 用于检查文章格式和内容

echo "📚 知乎文章发布助手"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 检查参数
if [ $# -eq 0 ]; then
    echo "使用方法: $0 <文章文件路径>"
    echo "示例: $0 /path/to/article.md"
    exit 1
fi

ARTICLE_FILE=$1

# 检查文件是否存在
if [ ! -f "$ARTICLE_FILE" ]; then
    echo "❌ 错误：文件不存在 - $ARTICLE_FILE"
    exit 1
fi

echo "📄 正在检查文章: $ARTICLE_FILE"
echo ""

# 读取文件内容
CONTENT=$(cat "$ARTICLE_FILE")

# 检查标题
echo "🔍 检查标题..."
TITLE=$(echo "$CONTENT" | grep -m 1 "^# ")
if [ -z "$TITLE" ]; then
    echo "  ❌ 未找到一级标题（# 标题）"
else
    TITLE_TEXT=$(echo "$TITLE" | sed 's/^# //')
    TITLE_LEN=${#TITLE_TEXT}
    if [ $TITLE_LEN -gt 100 ]; then
        echo "  ❌ 标题过长: $TITLE_LEN 字（最大100字）"
    else
        echo "  ✅ 标题: $TITLE_TEXT ($TITLE_LEN 字)"
    fi
fi

# 检查封面图
echo ""
echo "🔍 检查封面图..."
COVER_IMAGE=$(echo "$CONTENT" | grep -i "封面图" | head -1)
if [ -z "$COVER_IMAGE" ]; then
    echo "  ⚠️  未指定封面图（可选）"
else
    echo "  ✅ 封面图: $COVER_IMAGE"
fi

# 检查话题标签
echo ""
echo "🔍 检查话题标签..."
TAGS=$(echo "$CONTENT" | grep -i "话题标签" | head -1)
if [ -z "$TAGS" ]; then
    echo "  ⚠️  未指定话题标签（建议添加2-5个）"
else
    # 提取标签数量
    TAG_COUNT=$(echo "$TAGS" | tr ',' '\n' | wc -l)
    if [ $TAG_COUNT -gt 5 ]; then
        echo "  ❌ 标签过多: $TAG_COUNT 个（最多5个）"
    elif [ $TAG_COUNT -lt 2 ]; then
        echo "  ⚠️  标签过少: $TAG_COUNT 个（建议2-5个）"
    else
        echo "  ✅ 标签数量: $TAG_COUNT 个"
    fi
    echo "     标签: $TAGS"
fi

# 检查正文长度
echo ""
echo "🔍 检查正文长度..."
# 移除标题、图片等，只计算正文
BODY_TEXT=$(echo "$CONTENT" | sed '/^#/d' | sed '/^\!\[/d' | sed '/^\[.*\]:/d' | tr -d '[:space:]')
BODY_LEN=${#BODY_TEXT}
if [ $BODY_LEN -lt 100 ]; then
    echo "  ❌ 正文过短: $BODY_LEN 字（最少100字）"
else
    echo "  ✅ 正文长度: $BODY_LEN 字"
fi

# 检查图片链接
echo ""
echo "🔍 检查图片链接..."
IMAGE_URLS=$(echo "$CONTENT" | grep -oE '!\[.*\]\(.*\)' | wc -l)
if [ $IMAGE_URLS -eq 0 ]; then
    echo "  ℹ️  文中无图片"
else
    echo "  ℹ️  发现 $IMAGE_URLS 张图片"
    echo "     ⚠️  确保图片URL可访问"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ 文章格式检查完成"
echo ""
echo "💡 提示："
echo "   - 标题要吸引人，控制在100字以内"
echo "   - 话题标签2-5个，覆盖核心关键词"
echo "   - 正文至少100字，建议1000-3000字"
echo "   - 配图3-5张，提升阅读体验"
