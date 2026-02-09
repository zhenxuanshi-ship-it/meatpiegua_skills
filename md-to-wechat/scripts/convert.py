#!/usr/bin/env python3
"""
Markdown to WeChat Official Account HTML converter.

Converts markdown files into beautifully styled HTML with inline CSS,
optimized for direct paste into the WeChat Official Account editor.

Usage:
    python convert.py input.md [-o output.html] [--theme blue|green|dark|warm]

Dependencies:
    pip install markdown pygments beautifulsoup4
"""

import argparse
import re
import sys
from pathlib import Path

try:
    import markdown
    from markdown.extensions.codehilite import CodeHiliteExtension
    from markdown.extensions.fenced_code import FencedCodeExtension
    from markdown.extensions.tables import TableExtension
    from markdown.extensions.toc import TocExtension
    from markdown.extensions.footnotes import FootnoteExtension
except ImportError:
    print("Error: 'markdown' package not installed. Run: pip install markdown")
    sys.exit(1)

try:
    from pygments.formatters import HtmlFormatter
except ImportError:
    print("Error: 'pygments' package not installed. Run: pip install pygments")
    sys.exit(1)

try:
    from bs4 import BeautifulSoup, Tag
except ImportError:
    print("Error: 'beautifulsoup4' package not installed. Run: pip install beautifulsoup4")
    sys.exit(1)


# ──────────────────────────────────────────────
# Theme Definitions
# ──────────────────────────────────────────────

THEMES = {
    "blue": {
        "name": "优雅蓝",
        "primary": "#1e6fff",
        "primary_light": "#eef4ff",
        "primary_dark": "#1557cc",
        "primary_gradient": "linear-gradient(135deg, #1e6fff 0%, #5b9aff 100%)",
        "text": "#2b2b2b",
        "text_secondary": "#5f6368",
        "text_light": "#999999",
        "bg": "#ffffff",
        "bg_code": "#1e1e2e",
        "bg_code_text": "#d4d4d4",
        "bg_code_inline": "#eef4ff",
        "bg_blockquote": "#f7f9fc",
        "border": "#e0e0e0",
        "border_light": "#f0f0f0",
        "font_body": "-apple-system, BlinkMacSystemFont, 'PingFang SC', 'Microsoft YaHei', 'Segoe UI', Roboto, sans-serif",
        "font_size": "15px",
        "line_height": "1.8",
        "font_code": "'Fira Code', 'JetBrains Mono', Consolas, Monaco, 'Courier New', monospace",
        "pygments_style": "monokai",
    },
    "green": {
        "name": "清新绿",
        "primary": "#07a35a",
        "primary_light": "#edfaf3",
        "primary_dark": "#058c4c",
        "primary_gradient": "linear-gradient(135deg, #07a35a 0%, #4ac78e 100%)",
        "text": "#2d3436",
        "text_secondary": "#636e72",
        "text_light": "#999999",
        "bg": "#ffffff",
        "bg_code": "#1e272e",
        "bg_code_text": "#d4d4d4",
        "bg_code_inline": "#edfaf3",
        "bg_blockquote": "#f5fbf8",
        "border": "#dfe6e9",
        "border_light": "#f0f0f0",
        "font_body": "-apple-system, BlinkMacSystemFont, 'PingFang SC', 'Microsoft YaHei', sans-serif",
        "font_size": "15px",
        "line_height": "1.8",
        "font_code": "Consolas, Monaco, 'Courier New', monospace",
        "pygments_style": "monokai",
    },
    "dark": {
        "name": "经典黑",
        "primary": "#2c3e50",
        "primary_light": "#f4f6f7",
        "primary_dark": "#1a252f",
        "primary_gradient": "linear-gradient(135deg, #2c3e50 0%, #4a6b8a 100%)",
        "text": "#2c3e50",
        "text_secondary": "#7f8c8d",
        "text_light": "#999999",
        "bg": "#ffffff",
        "bg_code": "#282c34",
        "bg_code_text": "#abb2bf",
        "bg_code_inline": "#f4f6f7",
        "bg_blockquote": "#f8f9fa",
        "border": "#dce1e4",
        "border_light": "#f0f0f0",
        "font_body": "'Georgia', 'Songti SC', 'SimSun', -apple-system, serif",
        "font_size": "16px",
        "line_height": "2.0",
        "font_code": "Consolas, Monaco, 'Courier New', monospace",
        "pygments_style": "one-dark",
    },
    "warm": {
        "name": "温暖橙",
        "primary": "#e67e22",
        "primary_light": "#fef5ec",
        "primary_dark": "#d35400",
        "primary_gradient": "linear-gradient(135deg, #e67e22 0%, #f0a653 100%)",
        "text": "#34495e",
        "text_secondary": "#7f8c8d",
        "text_light": "#999999",
        "bg": "#ffffff",
        "bg_code": "#2d2d2d",
        "bg_code_text": "#d4d4d4",
        "bg_code_inline": "#fef5ec",
        "bg_blockquote": "#fffaf5",
        "border": "#f0d0b0",
        "border_light": "#f5ead8",
        "font_body": "-apple-system, BlinkMacSystemFont, 'PingFang SC', 'Microsoft YaHei', sans-serif",
        "font_size": "15px",
        "line_height": "1.8",
        "font_code": "Consolas, Monaco, 'Courier New', monospace",
        "pygments_style": "monokai",
    },
}


# ──────────────────────────────────────────────
# Style Generator
# ──────────────────────────────────────────────

def build_styles(theme_name: str = "blue") -> dict:
    """Build a complete inline-styles dictionary from a theme."""
    t = THEMES.get(theme_name, THEMES["blue"])
    return {
        "container": (
            f"max-width: 100%;"
            f"font-family: {t['font_body']};"
            f"font-size: {t['font_size']};"
            f"line-height: {t['line_height']};"
            f"color: {t['text']};"
            f"word-wrap: break-word;"
            f"overflow-wrap: break-word;"
        ),
        "h1": (
            f"font-size: 22px;"
            f"font-weight: bold;"
            f"color: {t['primary']};"
            f"text-align: center;"
            f"margin: 30px 0 20px 0;"
            f"padding-bottom: 12px;"
            f"border-bottom: 2px solid {t['primary']};"
            f"line-height: 1.4;"
        ),
        "h2": (
            f"font-size: 19px;"
            f"font-weight: bold;"
            f"color: {t['primary']};"
            f"margin: 28px 0 15px 0;"
            f"padding: 4px 0 4px 12px;"
            f"border-left: 4px solid {t['primary']};"
            f"line-height: 1.4;"
        ),
        "h3": (
            f"font-size: 17px;"
            f"font-weight: bold;"
            f"color: {t['text']};"
            f"margin: 22px 0 10px 0;"
            f"padding-left: 8px;"
            f"line-height: 1.4;"
        ),
        "h4": (
            f"font-size: 15px;"
            f"font-weight: bold;"
            f"color: {t['text_secondary']};"
            f"margin: 18px 0 8px 0;"
            f"line-height: 1.4;"
        ),
        "p": (
            f"margin: 0 0 15px 0;"
            f"text-align: justify;"
            f"line-height: {t['line_height']};"
            f"color: {t['text']};"
        ),
        "strong": f"font-weight: bold; color: {t['primary_dark']};",
        "em": f"font-style: italic;",
        "del": f"text-decoration: line-through; color: {t['text_light']};",
        "a": (
            f"color: {t['primary']};"
            f"text-decoration: none;"
            f"border-bottom: 1px dashed {t['primary']};"
            f"word-break: break-all;"
        ),
        "ul": f"margin: 5px 0 15px 0; padding-left: 2em; list-style-type: disc;",
        "ol": f"margin: 5px 0 15px 0; padding-left: 2em;",
        "li": f"margin: 4px 0; line-height: {t['line_height']};",
        "blockquote": (
            f"margin: 15px 0;"
            f"padding: 15px 18px;"
            f"background: {t['bg_blockquote']};"
            f"border-left: 4px solid {t['primary']};"
            f"color: {t['text_secondary']};"
            f"font-size: 14px;"
            f"line-height: 1.75;"
            f"border-radius: 0 6px 6px 0;"
        ),
        "blockquote_p": (
            f"margin: 0 0 8px 0;"
            f"text-align: justify;"
            f"line-height: 1.75;"
            f"color: {t['text_secondary']};"
        ),
        "code_inline": (
            f"background: {t['bg_code_inline']};"
            f"color: {t['primary']};"
            f"padding: 2px 6px;"
            f"border-radius: 3px;"
            f"font-family: {t['font_code']};"
            f"font-size: 90%;"
            f"word-break: break-all;"
        ),
        "code_block_wrapper": (
            f"background: {t['bg_code']};"
            f"border-radius: 8px;"
            f"margin: 15px 0;"
            f"overflow: hidden;"
        ),
        "code_block_header": (
            f"display: flex;"
            f"justify-content: space-between;"
            f"align-items: center;"
            f"padding: 8px 16px;"
            f"background: rgba(255,255,255,0.05);"
            f"border-bottom: 1px solid rgba(255,255,255,0.08);"
        ),
        "code_block_lang": (
            f"font-size: 12px;"
            f"color: rgba(255,255,255,0.5);"
            f"font-family: {t['font_code']};"
            f"text-transform: uppercase;"
            f"letter-spacing: 0.5px;"
        ),
        "code_block_dots": (
            f"display: flex; gap: 6px;"
        ),
        "code_block_dot": (
            f"width: 10px; height: 10px; border-radius: 50%;"
        ),
        "code_block_body": (
            f"padding: 16px;"
            f"overflow-x: auto;"
            f"font-family: {t['font_code']};"
            f"font-size: 13px;"
            f"line-height: 1.6;"
            f"color: {t['bg_code_text']};"
            f"-webkit-overflow-scrolling: touch;"
        ),
        "table_wrapper": (
            f"overflow-x: auto;"
            f"margin: 15px 0;"
            f"-webkit-overflow-scrolling: touch;"
        ),
        "table": (
            f"width: 100%;"
            f"border-collapse: collapse;"
            f"font-size: 14px;"
            f"border: 1px solid {t['border']};"
        ),
        "th": (
            f"background: {t['primary']};"
            f"color: #ffffff;"
            f"font-weight: bold;"
            f"padding: 10px 14px;"
            f"text-align: left;"
            f"border: 1px solid {t['primary_dark']};"
            f"font-size: 14px;"
            f"white-space: nowrap;"
        ),
        "td": (
            f"padding: 9px 14px;"
            f"border: 1px solid {t['border']};"
            f"line-height: 1.6;"
            f"font-size: 14px;"
        ),
        "td_even": (
            f"padding: 9px 14px;"
            f"border: 1px solid {t['border']};"
            f"line-height: 1.6;"
            f"font-size: 14px;"
            f"background: {t['primary_light']};"
        ),
        "hr": (
            f"border: none;"
            f"height: 1px;"
            f"background: {t['border']};"
            f"margin: 30px 0;"
        ),
        "img": (
            f"max-width: 100%;"
            f"height: auto;"
            f"border-radius: 6px;"
            f"margin: 10px auto;"
            f"display: block;"
        ),
        "img_caption": (
            f"text-align: center;"
            f"font-size: 13px;"
            f"color: {t['text_light']};"
            f"margin: 6px 0 15px 0;"
            f"line-height: 1.5;"
        ),
        "task_done": (
            f"color: {t['text_light']};"
            f"text-decoration: line-through;"
        ),
        "footnote_section": (
            f"margin-top: 30px;"
            f"padding-top: 15px;"
            f"border-top: 1px solid {t['border']};"
            f"font-size: 13px;"
            f"color: {t['text_secondary']};"
        ),
        "footnote_ref": (
            f"color: {t['primary']};"
            f"font-size: 12px;"
            f"vertical-align: super;"
            f"text-decoration: none;"
            f"font-weight: bold;"
        ),
    }


# ──────────────────────────────────────────────
# Markdown Pre-processing
# ──────────────────────────────────────────────

def strip_frontmatter(md_text: str) -> tuple[str, dict]:
    """Remove YAML frontmatter from markdown and return (content, metadata).

    Frontmatter is enclosed by '---' at the start of the file.
    Returns the markdown without frontmatter and a dict of parsed metadata.
    """
    metadata = {}
    if md_text.startswith("---"):
        parts = md_text.split("---", 2)
        if len(parts) >= 3:
            # parts[0] is empty (before first ---), parts[1] is frontmatter, parts[2] is content
            fm_text = parts[1].strip()
            for line in fm_text.split("\n"):
                line = line.strip()
                if ":" in line:
                    key, _, value = line.partition(":")
                    metadata[key.strip()] = value.strip()
            md_text = parts[2].strip()
    return md_text, metadata


def preprocess_markdown(md_text: str) -> str:
    """Pre-process markdown for better compatibility."""
    # Strip frontmatter if present
    md_text, _ = strip_frontmatter(md_text)

    # Convert task lists: - [ ] and - [x]
    md_text = re.sub(
        r"^(\s*[-*])\s*\[x\]\s+(.+)$",
        r'\1 <span class="task-done">✅ \2</span>',
        md_text, flags=re.MULTILINE
    )
    md_text = re.sub(
        r"^(\s*[-*])\s*\[ \]\s+(.+)$",
        r"\1 ⬜ \2",
        md_text, flags=re.MULTILINE
    )
    return md_text


# ──────────────────────────────────────────────
# HTML Post-processing with BeautifulSoup
# ──────────────────────────────────────────────

def apply_styles(html: str, styles: dict, theme: dict) -> str:
    """Apply inline styles to all HTML elements using BeautifulSoup."""
    soup = BeautifulSoup(html, "html.parser")

    # --- Headings ---
    for tag_name in ["h1", "h2", "h3", "h4"]:
        for tag in soup.find_all(tag_name):
            tag["style"] = styles[tag_name]

    # --- Paragraphs ---
    for p in soup.find_all("p"):
        # Paragraphs inside blockquotes get different styles
        if p.parent and p.parent.name == "blockquote":
            p["style"] = styles["blockquote_p"]
        else:
            p["style"] = styles["p"]

    # --- Inline formatting ---
    for strong in soup.find_all("strong"):
        strong["style"] = styles["strong"]
    for em in soup.find_all("em"):
        em["style"] = styles["em"]
    for del_tag in soup.find_all("del"):
        del_tag["style"] = styles["del"]

    # --- Links ---
    for a in soup.find_all("a"):
        # Skip footnote back-references
        cls = a.get("class", [])
        if "footnote-backref" in cls:
            a["style"] = styles["footnote_ref"]
        elif "footnote-ref" in cls:
            a["style"] = styles["footnote_ref"]
        else:
            a["style"] = styles["a"]

    # --- Lists ---
    for ul in soup.find_all("ul"):
        ul["style"] = styles["ul"]
    for ol in soup.find_all("ol"):
        ol["style"] = styles["ol"]
    for li in soup.find_all("li"):
        li["style"] = styles["li"]

    # --- Blockquotes ---
    for bq in soup.find_all("blockquote"):
        bq["style"] = styles["blockquote"]

    # --- Code blocks (codehilite) ---
    for div in soup.find_all("div", class_="codehilite"):
        # Extract language from class if present
        lang = ""
        pre = div.find("pre")
        if pre:
            # Try to detect language from span classes
            first_span = pre.find("span")
            # Try to get lang from codehilite metadata
            classes = div.get("class", [])
            for cls in classes:
                if cls.startswith("language-"):
                    lang = cls.replace("language-", "")

        # If no language found, try to detect from code tag
        if not lang:
            code_tag = div.find("code")
            if code_tag:
                code_classes = code_tag.get("class", [])
                for cls in code_classes:
                    if cls.startswith("language-"):
                        lang = cls.replace("language-", "")

        # Build styled code block with header
        inner_html = div.decode_contents()

        # Create new wrapper structure
        new_div = soup.new_tag("div")
        new_div["style"] = styles["code_block_wrapper"]

        # Header with dots + language label
        header = soup.new_tag("div")
        header["style"] = styles["code_block_header"]

        dots_div = soup.new_tag("div")
        dots_div["style"] = styles["code_block_dots"]
        for color in ["#ff5f57", "#febc2e", "#28c840"]:
            dot = soup.new_tag("span")
            dot["style"] = styles["code_block_dot"] + f" background: {color};"
            dots_div.append(dot)
        header.append(dots_div)

        if lang:
            lang_span = soup.new_tag("span")
            lang_span["style"] = styles["code_block_lang"]
            lang_span.string = lang.upper()
            header.append(lang_span)

        new_div.append(header)

        # Code body
        body_div = soup.new_tag("div")
        body_div["style"] = styles["code_block_body"]
        # Keep original Pygments-highlighted HTML
        body_div.append(BeautifulSoup(inner_html, "html.parser"))
        new_div.append(body_div)

        # Remove style from inner pre (it's wrapped now)
        inner_pre = new_div.find("pre")
        if inner_pre:
            inner_pre["style"] = "margin: 0; padding: 0; background: transparent; overflow: visible;"

        div.replace_with(new_div)

    # --- Bare <pre> blocks (non-highlighted) ---
    for pre in soup.find_all("pre"):
        # Skip if already inside our styled wrapper
        if pre.parent and pre.parent.get("style", "").startswith("padding:"):
            continue
        # Only style top-level pre blocks
        wrapper = soup.new_tag("div")
        wrapper["style"] = styles["code_block_wrapper"]

        body = soup.new_tag("div")
        body["style"] = styles["code_block_body"]
        pre_copy = pre.extract()
        pre_copy["style"] = "margin: 0; padding: 0; background: transparent; overflow: visible;"
        body.append(pre_copy)
        wrapper.append(body)

        pre.insert_after(wrapper) if pre.parent else None

    # --- Inline code (not inside pre/code blocks) ---
    for code in soup.find_all("code"):
        # Skip code inside pre (those are code blocks)
        if code.parent and code.parent.name == "pre":
            continue
        # Skip code inside our code block body divs
        if code.parent and code.parent.name == "div":
            parent_style = code.parent.get("style", "")
            if "overflow-x" in parent_style or "font-family" in parent_style:
                continue
        code["style"] = styles["code_inline"]

    # --- Tables ---
    for table in soup.find_all("table"):
        # Wrap table in scrollable div
        wrapper = soup.new_tag("div")
        wrapper["style"] = styles["table_wrapper"]

        table["style"] = styles["table"]

        # Style headers
        for th in table.find_all("th"):
            th["style"] = styles["th"]

        # Style body rows with zebra stripes
        tbody = table.find("tbody")
        if tbody:
            for i, tr in enumerate(tbody.find_all("tr")):
                for td in tr.find_all("td"):
                    td["style"] = styles["td_even"] if i % 2 == 1 else styles["td"]

        table.wrap(wrapper)

    # --- Horizontal rules ---
    for hr in soup.find_all("hr"):
        hr["style"] = styles["hr"]

    # --- Images ---
    for img in soup.find_all("img"):
        img["style"] = styles["img"]
        # If the image has alt text, add a caption
        alt = img.get("alt", "").strip()
        if alt and alt != "image":
            caption = soup.new_tag("p")
            caption["style"] = styles["img_caption"]
            caption.string = alt
            img.insert_after(caption)

    # --- Task list done items ---
    for span in soup.find_all("span", class_="task-done"):
        span["style"] = styles["task_done"]

    # --- Footnote section ---
    for div in soup.find_all("div", class_="footnote"):
        div["style"] = styles["footnote_section"]
        # Remove the redundant <hr> inside footnote (we use border-top instead)
        for hr_in_fn in div.find_all("hr"):
            hr_in_fn.decompose()

    for sup in soup.find_all("sup"):
        if sup.find("a", class_="footnote-ref"):
            pass  # Already styled above

    return str(soup)


# ──────────────────────────────────────────────
# Fenced Code Language Extraction
# ──────────────────────────────────────────────

class LanguageTracker:
    """Track language hints from fenced code blocks before markdown processing."""

    def __init__(self):
        self.languages = []

    def extract_languages(self, md_text: str) -> str:
        """Extract language from fenced code blocks and add class markers."""
        def replacer(match):
            lang = match.group(1).strip()
            self.languages.append(lang)
            return f"```{lang}"

        return re.sub(r"^```(\w+)\s*$", replacer, md_text, flags=re.MULTILINE)


# ──────────────────────────────────────────────
# Main Converter
# ──────────────────────────────────────────────

def convert(md_content: str, theme_name: str = "blue") -> str:
    """Convert markdown content to WeChat-compatible HTML with inline styles."""
    t = THEMES.get(theme_name, THEMES["blue"])
    styles = build_styles(theme_name)

    # Pre-process markdown
    md_content = preprocess_markdown(md_content)

    # Configure markdown extensions
    extensions = [
        TableExtension(),
        FencedCodeExtension(),
        FootnoteExtension(),
        TocExtension(permalink=False),
        CodeHiliteExtension(
            pygments_style=t["pygments_style"],
            noclasses=True,
            linenums=False,
            guess_lang=True,
        ),
    ]

    # Convert markdown to raw HTML
    md_parser = markdown.Markdown(extensions=extensions)
    raw_html = md_parser.convert(md_content)

    # Apply inline styles with BeautifulSoup
    styled_html = apply_styles(raw_html, styles, t)

    # Build full HTML document with preview shell
    return build_document(styled_html, styles, t)


def build_document(body_html: str, styles: dict, theme: dict) -> str:
    """Generate a complete HTML document with copy-to-clipboard and preview."""
    primary = theme["primary"]
    font = theme["font_body"]
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>微信公众号文章预览 - {theme['name']}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            background: #f0f2f5;
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 20px;
            font-family: {font};
        }}
        .toolbar {{
            position: sticky;
            top: 0;
            z-index: 100;
            background: #fff;
            padding: 14px 24px;
            border-radius: 10px;
            box-shadow: 0 2px 12px rgba(0,0,0,0.08);
            margin-bottom: 24px;
            display: flex;
            gap: 16px;
            align-items: center;
            flex-wrap: wrap;
        }}
        .toolbar button {{
            background: {primary};
            color: #fff;
            border: none;
            padding: 10px 24px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 500;
            transition: all 0.2s;
            box-shadow: 0 2px 6px rgba(0,0,0,0.12);
        }}
        .toolbar button:hover {{
            opacity: 0.9;
            transform: translateY(-1px);
            box-shadow: 0 4px 10px rgba(0,0,0,0.15);
        }}
        .toolbar button:active {{ transform: translateY(0); }}
        .toolbar .hint {{
            color: #888;
            font-size: 13px;
        }}
        .toolbar .status {{
            font-size: 13px;
            font-weight: 500;
            transition: opacity 0.3s;
        }}
        .phone-frame {{
            background: #fff;
            max-width: 420px;
            width: 100%;
            border-radius: 40px;
            box-shadow: 0 8px 40px rgba(0,0,0,0.12);
            overflow: hidden;
            border: 8px solid #1a1a1a;
        }}
        .phone-header {{
            background: #1a1a1a;
            padding: 10px 20px 8px;
            display: flex;
            justify-content: center;
            align-items: center;
        }}
        .phone-notch {{
            width: 120px;
            height: 24px;
            background: #000;
            border-radius: 12px;
        }}
        .phone-content {{
            padding: 20px 16px 30px;
            max-height: 80vh;
            overflow-y: auto;
        }}
        #content {{
            font-family: {font};
        }}
        /* Clean up Pygments pre inside our wrapper */
        #content pre {{ background: transparent !important; }}
    </style>
</head>
<body>
    <div class="toolbar">
        <button onclick="copyContent()">复制内容到剪贴板</button>
        <span class="hint">复制后直接粘贴到微信公众号编辑器</span>
        <span class="status" id="status"></span>
    </div>
    <div class="phone-frame">
        <div class="phone-header">
            <div class="phone-notch"></div>
        </div>
        <div class="phone-content">
            <div id="content" style="{styles['container']}">
{body_html}
            </div>
        </div>
    </div>
    <script>
        function copyContent() {{
            const content = document.getElementById('content');
            const range = document.createRange();
            range.selectNodeContents(content);
            const sel = window.getSelection();
            sel.removeAllRanges();
            sel.addRange(range);
            try {{
                document.execCommand('copy');
                showStatus('已复制！可直接粘贴到公众号编辑器', '#52c41a');
            }} catch (e) {{
                showStatus('复制失败，请手动 Ctrl+A 全选后复制', '#f5222d');
            }}
            sel.removeAllRanges();
        }}
        function showStatus(msg, color) {{
            const el = document.getElementById('status');
            el.textContent = msg;
            el.style.color = color;
            setTimeout(() => {{ el.style.opacity = '0'; setTimeout(() => {{ el.textContent = ''; el.style.opacity = '1'; }}, 300); }}, 3000);
        }}
    </script>
</body>
</html>"""


# ──────────────────────────────────────────────
# CLI Entry Point
# ──────────────────────────────────────────────

def _out(msg: str):
    """Print with UTF-8 encoding for Windows compatibility."""
    import io
    try:
        out = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True)
        out.write(msg + "\n")
        out.flush()
        out.detach()
    except Exception:
        print(msg)


def convert_single(input_path: Path, output_path: Path | None, theme: str) -> Path | None:
    """Convert a single markdown file. Returns output path on success."""
    if not input_path.exists():
        _out(f"错误: 文件不存在: {input_path}")
        return None

    if not output_path:
        output_path = input_path.with_name(f"{input_path.stem}_wechat.html")

    md_content = input_path.read_text(encoding="utf-8")
    html_content = convert(md_content, theme)
    output_path.write_text(html_content, encoding="utf-8")
    return output_path


def main():
    parser = argparse.ArgumentParser(
        description="Markdown → 微信公众号 HTML 转换器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python convert.py article.md                     # 默认优雅蓝主题
  python convert.py article.md --theme green       # 清新绿主题
  python convert.py article.md -o output.html      # 指定输出文件
  python convert.py --dir ./articles               # 批量转换目录下所有 .md
  python convert.py --dir ./articles --theme warm  # 批量转换，温暖橙主题
        """,
    )
    parser.add_argument("input", nargs="?", help="输入 Markdown 文件路径")
    parser.add_argument("-o", "--output", help="输出 HTML 文件路径 (默认: {input}_wechat.html)")
    parser.add_argument(
        "--theme",
        choices=list(THEMES.keys()),
        default="blue",
        help="主题风格 (默认: blue)",
    )
    parser.add_argument(
        "--dir",
        help="批量转换：指定目录路径，转换该目录下所有 .md 文件",
    )

    args = parser.parse_args()

    theme = THEMES[args.theme]

    # ── Batch mode ──
    if args.dir:
        dir_path = Path(args.dir)
        if not dir_path.is_dir():
            _out(f"错误: 目录不存在: {dir_path}")
            sys.exit(1)

        md_files = sorted(dir_path.glob("*.md"))
        if not md_files:
            _out(f"目录下没有找到 .md 文件: {dir_path}")
            sys.exit(1)

        _out(f"批量转换: 找到 {len(md_files)} 个 Markdown 文件")
        _out(f"主题: {theme['name']}")
        _out("-" * 50)

        success = 0
        failed = 0
        for md_file in md_files:
            out_path = convert_single(md_file, None, args.theme)
            if out_path:
                _out(f"  [OK] {md_file.name} -> {out_path.name}")
                success += 1
            else:
                _out(f"  [FAIL] {md_file.name}")
                failed += 1

        _out("-" * 50)
        _out(f"批量转换完成: 成功 {success}, 失败 {failed}, 共 {len(md_files)}")
        _out(f"\n使用方法:")
        _out(f"  1. 浏览器打开生成的 HTML 文件")
        _out(f"  2. 点击「复制内容到剪贴板」")
        _out(f"  3. 在微信公众号编辑器中粘贴")
        sys.exit(0)

    # ── Single file mode ──
    if not args.input:
        parser.print_help()
        sys.exit(0)

    input_path = Path(args.input)
    output_path = Path(args.output) if args.output else None
    result = convert_single(input_path, output_path, args.theme)

    if not result:
        sys.exit(1)

    _out(f"[OK] 转换完成!")
    _out(f"  输入:  {input_path}")
    _out(f"  输出:  {result}")
    _out(f"  主题:  {theme['name']}")
    _out(f"\n使用方法:")
    _out(f"  1. 浏览器打开 {result}")
    _out(f"  2. 点击「复制内容到剪贴板」")
    _out(f"  3. 在微信公众号编辑器中粘贴")


def convert_to_wechat_content(md_content: str, theme_name: str = "blue") -> str:
    """Convert markdown to clean styled HTML suitable for WeChat article content.

    Returns HTML with inline styles (no document wrapper), used by the publisher
    for API-based article creation via WeChat Official Account API.
    """
    t = THEMES.get(theme_name, THEMES["blue"])
    styles = build_styles(theme_name)

    # Pre-process markdown
    md_content = preprocess_markdown(md_content)

    # Configure markdown extensions
    extensions = [
        TableExtension(),
        FencedCodeExtension(),
        FootnoteExtension(),
        TocExtension(permalink=False),
        CodeHiliteExtension(
            pygments_style=t["pygments_style"],
            noclasses=True,
            linenums=False,
            guess_lang=True,
        ),
    ]

    # Convert markdown to raw HTML
    md_parser = markdown.Markdown(extensions=extensions)
    raw_html = md_parser.convert(md_content)

    # Apply inline styles with BeautifulSoup
    styled_html = apply_styles(raw_html, styles, t)
    return styled_html


if __name__ == "__main__":
    main()
