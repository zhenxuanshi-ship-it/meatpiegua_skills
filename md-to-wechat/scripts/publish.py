#!/usr/bin/env python3
"""
One-click publish Markdown articles to WeChat Official Account (微信公众号).

Automates article creation via WeChat Official Account API.
Supports creating drafts, publishing, and batch operations.

Usage:
    python publish.py --setup                             # Configure AppID/AppSecret
    python publish.py input.md                            # Create draft
    python publish.py input.md --publish                  # Create draft and publish
    python publish.py input.md --title "Custom Title"     # Custom title
    python publish.py --dir ./articles                    # Batch create drafts
    python publish.py --dir ./articles --publish          # Batch create and publish

Dependencies:
    pip install requests markdown pygments beautifulsoup4
"""

import argparse
import json
import re
import sys
import time
from pathlib import Path
from urllib.parse import urlparse

SCRIPT_DIR = Path(__file__).parent
CONFIG_FILE = SCRIPT_DIR / ".wechat_config.json"
TOKEN_CACHE_FILE = SCRIPT_DIR / ".wechat_token.json"

# Add scripts dir to path for importing convert
sys.path.insert(0, str(SCRIPT_DIR))


# ──────────────────────────────────────────────
# Utilities
# ──────────────────────────────────────────────

def _print(msg: str):
    """Print with UTF-8 encoding for Windows compatibility."""
    import io
    try:
        out = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True)
        out.write(msg + "\n")
        out.flush()
        out.detach()
    except Exception:
        print(msg)


# ──────────────────────────────────────────────
# Configuration Management
# ──────────────────────────────────────────────

def save_config(config: dict):
    """Save WeChat config (AppID, AppSecret) to file."""
    CONFIG_FILE.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    _print(f"配置已保存到: {CONFIG_FILE}")


def load_config() -> dict | None:
    """Load WeChat config from file."""
    if CONFIG_FILE.exists():
        try:
            return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, IOError):
            return None
    return None


def setup_config():
    """Interactive setup for WeChat Official Account credentials."""
    _print("=" * 50)
    _print("微信公众号 API 配置向导")
    _print("=" * 50)
    _print("")
    _print("请前往微信公众平台获取以下信息：")
    _print("  公众号后台 → 设置与开发 → 基本配置")
    _print("")

    appid = input("请输入 AppID: ").strip()
    if not appid:
        _print("错误: AppID 不能为空")
        return False

    appsecret = input("请输入 AppSecret: ").strip()
    if not appsecret:
        _print("错误: AppSecret 不能为空")
        return False

    config = {"appid": appid, "appsecret": appsecret}

    # Verify credentials by fetching token
    _print("\n正在验证凭据...")
    token = _fetch_access_token(appid, appsecret)
    if token:
        save_config(config)
        _print("验证成功！配置已保存。")
        _print("")
        _print("重要提示：请确保已将本机 IP 添加到公众号 IP 白名单中")
        _print("  公众号后台 → 设置与开发 → 基本配置 → IP白名单")
        return True
    else:
        _print("验证失败，请检查 AppID 和 AppSecret 是否正确")
        return False


def _ensure_config() -> dict:
    """Ensure we have valid config, run setup if needed. Returns config dict."""
    config = load_config()
    if not config or not config.get("appid") or not config.get("appsecret"):
        _print("未找到配置信息，正在启动配置向导...")
        if not setup_config():
            sys.exit(1)
        config = load_config()
    return config


# ──────────────────────────────────────────────
# Access Token Management
# ──────────────────────────────────────────────

def _fetch_access_token(appid: str, appsecret: str) -> str | None:
    """Fetch a new access_token from WeChat API."""
    import requests

    try:
        resp = requests.get(
            "https://api.weixin.qq.com/cgi-bin/token",
            params={
                "grant_type": "client_credential",
                "appid": appid,
                "secret": appsecret,
            },
            timeout=15,
        )
        data = resp.json()
        if "access_token" in data:
            return data["access_token"]
        else:
            errcode = data.get("errcode", "unknown")
            errmsg = data.get("errmsg", "unknown")
            _print(f"获取 access_token 失败: [{errcode}] {errmsg}")
            if errcode == 40164:
                _print("提示: 请将本机 IP 添加到公众号 IP 白名单中")
            return None
    except Exception as e:
        _print(f"获取 access_token 出错: {e}")
        return None


def get_access_token(config: dict) -> str | None:
    """Get a valid access_token, using cache if not expired."""
    # Check cache
    if TOKEN_CACHE_FILE.exists():
        try:
            cache = json.loads(TOKEN_CACHE_FILE.read_text(encoding="utf-8"))
            if cache.get("expires_at", 0) > time.time() + 300:  # 5 min buffer
                return cache["access_token"]
        except (json.JSONDecodeError, IOError):
            pass

    # Fetch new token
    token = _fetch_access_token(config["appid"], config["appsecret"])
    if token:
        cache = {
            "access_token": token,
            "expires_at": time.time() + 7200,  # 2 hours
        }
        TOKEN_CACHE_FILE.write_text(json.dumps(cache), encoding="utf-8")
        return token

    return None


# ──────────────────────────────────────────────
# Image Upload
# ──────────────────────────────────────────────

def upload_image(access_token: str, image_url: str) -> str | None:
    """Upload an image to WeChat from URL and return the WeChat media URL.

    Uses the 'uploadimg' API for article inline images.
    Returns the WeChat-hosted image URL.
    """
    import requests
    import tempfile

    try:
        # Download the image first
        resp = requests.get(image_url, timeout=30)
        if resp.status_code != 200:
            _print(f"  下载图片失败: {image_url}")
            return None

        content_type = resp.headers.get("content-type", "image/png")
        ext = ".png"
        if "jpeg" in content_type or "jpg" in content_type:
            ext = ".jpg"
        elif "gif" in content_type:
            ext = ".gif"

        # Upload to WeChat
        upload_resp = requests.post(
            f"https://api.weixin.qq.com/cgi-bin/media/uploadimg?access_token={access_token}",
            files={"media": (f"image{ext}", resp.content, content_type)},
            timeout=30,
        )
        data = upload_resp.json()
        if "url" in data:
            return data["url"]
        else:
            _print(f"  上传图片失败: {data.get('errmsg', 'unknown error')}")
            return None
    except Exception as e:
        _print(f"  图片上传出错: {e}")
        return None


def upload_thumb_media(access_token: str, image_path: str | None = None) -> str | None:
    """Upload a thumb image as permanent material, return media_id.

    If no image_path provided, creates a default placeholder thumb.
    Uses the permanent material API (required for draft creation).
    """
    import requests

    try:
        if image_path and Path(image_path).exists():
            img_data = Path(image_path).read_bytes()
            filename = Path(image_path).name
        else:
            # Create a minimal 1x1 placeholder image (valid JPEG)
            # WeChat requires at least 200x200, so we create a simple colored image
            img_data = _create_default_thumb()
            filename = "thumb.jpg"

        upload_resp = requests.post(
            f"https://api.weixin.qq.com/cgi-bin/material/add_material?access_token={access_token}&type=image",
            files={"media": (filename, img_data, "image/jpeg")},
            timeout=30,
        )
        data = upload_resp.json()
        if "media_id" in data:
            _print(f"封面图已上传: media_id={data['media_id'][:20]}...")
            return data["media_id"]
        else:
            _print(f"上传封面图失败: {data.get('errmsg', 'unknown error')}")
            return None
    except Exception as e:
        _print(f"封面图上传出错: {e}")
        return None


def _create_default_thumb() -> bytes:
    """Create a simple default thumbnail image (300x200 blue gradient)."""
    try:
        # Try using PIL if available
        from PIL import Image, ImageDraw, ImageFont
        img = Image.new("RGB", (900, 500), color=(30, 111, 255))
        draw = ImageDraw.Draw(img)
        # Add a subtle gradient effect
        for y in range(500):
            r = int(30 + (y / 500) * 40)
            g = int(111 - (y / 500) * 30)
            b = int(255 - (y / 500) * 50)
            draw.line([(0, y), (900, y)], fill=(r, g, b))
        import io
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=85)
        return buf.getvalue()
    except ImportError:
        pass

    # Fallback: create a minimal valid JPEG using raw bytes
    # This is a minimal 1x1 blue JPEG - WeChat may reject it if too small
    # Better to use a proper 900x500 image
    import struct
    width, height = 300, 200
    # BMP-like approach: create raw image data and convert
    # Use a simpler approach: return a hardcoded small valid JPEG
    _print("提示: 安装 Pillow 可生成更好的默认封面 (pip install Pillow)")
    _print("建议使用 --thumb 参数指定封面图片")
    # Minimal valid JPEG (1x1 pixel, blue) - may be too small for WeChat
    return (
        b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00'
        b'\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08'
        b'\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e'
        b'\x1d\x1a\x1c\x1c $.\' ",#\x1c\x1c(7),01444\x1f\'9=82<.342\xff\xc0'
        b'\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11\x00\xff\xc4\x00\x1f\x00'
        b'\x00\x01\x05\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00'
        b'\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\xff\xc4\x00\xb5\x10'
        b'\x00\x02\x01\x03\x03\x02\x04\x03\x05\x05\x04\x04\x00\x00\x01}\x01'
        b'\x02\x03\x00\x04\x11\x05\x12!1A\x06\x13Qa\x07"q\x142\x81\x91\xa1'
        b'\x08#B\xb1\xc1\x15R\xd1\xf0$3br\x82\t\n\x16\x17\x18\x19\x1a%&\'()'
        b'*456789:CDEFGHIJSTUVWXYZcdefghijstuvwxyz\x83\x84\x85\x86\x87\x88'
        b'\x89\x8a\x92\x93\x94\x95\x96\x97\x98\x99\x9a\xa2\xa3\xa4\xa5\xa6'
        b'\xa7\xa8\xa9\xaa\xb2\xb3\xb4\xb5\xb6\xb7\xb8\xb9\xba\xc2\xc3\xc4'
        b'\xc5\xc6\xc7\xc8\xc9\xca\xd2\xd3\xd4\xd5\xd6\xd7\xd8\xd9\xda\xe1'
        b'\xe2\xe3\xe4\xe5\xe6\xe7\xe8\xe9\xea\xf1\xf2\xf3\xf4\xf5\xf6\xf7'
        b'\xf8\xf9\xfa\xff\xda\x00\x08\x01\x01\x00\x00?\x00\xfb\xd2\x8a(\x03'
        b'\xff\xd9'
    )


def replace_images_in_html(access_token: str, html_content: str) -> str:
    """Find all images in HTML content, upload them to WeChat, and replace URLs."""
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        return html_content

    soup = BeautifulSoup(html_content, "html.parser")
    img_tags = soup.find_all("img")

    if not img_tags:
        return html_content

    _print(f"发现 {len(img_tags)} 张图片，正在上传到微信...")

    for img in img_tags:
        src = img.get("src", "")
        if not src:
            continue

        # Skip data URIs and already-uploaded WeChat images
        if src.startswith("data:") or "mmbiz.qpic.cn" in src:
            continue

        # Only upload http/https images
        if src.startswith(("http://", "https://")):
            _print(f"  上传: {src[:80]}...")
            new_url = upload_image(access_token, src)
            if new_url:
                img["src"] = new_url
                _print(f"  成功: {new_url[:60]}...")
            else:
                _print(f"  跳过（上传失败）")

    return str(soup)


# ──────────────────────────────────────────────
# Draft & Publish API
# ──────────────────────────────────────────────

def _truncate_wechat_title(title: str, max_chars: int = 10) -> str:
    """Truncate title for WeChat draft API.

    WeChat has a stricter title limit for subscription accounts (订阅号):
    approximately 10 CJK characters or ~30 ASCII characters.
    For certified service accounts, the limit is 64 characters.

    This function counts CJK characters as 3 units, others as 1,
    and truncates to stay within max_chars CJK equivalents.
    """
    cost = 0
    limit = max_chars * 3  # CJK char = 3 units
    result = []
    for ch in title:
        # CJK characters cost 3 units, others cost 1
        if ord(ch) > 0x7F:
            c = 3
        else:
            c = 1
        if cost + c > limit:
            break
        cost += c
        result.append(ch)
    truncated = "".join(result)
    if len(truncated) < len(title):
        _print(f"  标题过长，已截断: {truncated}")
    return truncated


def create_draft(access_token: str, title: str, content: str,
                 thumb_media_id: str, author: str = "",
                 digest: str = "") -> str | None:
    """Create a draft article on WeChat. Returns media_id on success."""
    import requests

    # WeChat title limit: ~10 CJK chars for subscription accounts
    title = _truncate_wechat_title(title)

    # WeChat digest limit: ~54 bytes for subscription accounts
    if digest:
        # Truncate digest to safe length (18 CJK chars = 54 bytes)
        digest = _truncate_wechat_title(digest, 18)

    article = {
        "title": title,
        "author": author,
        "digest": digest,
        "content": content,
        "thumb_media_id": thumb_media_id,
        "need_open_comment": 0,
        "only_fans_can_comment": 0,
    }

    resp = requests.post(
        f"https://api.weixin.qq.com/cgi-bin/draft/add?access_token={access_token}",
        data=json.dumps({"articles": [article]}, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json; charset=utf-8"},
        timeout=30,
    )
    data = resp.json()

    if "media_id" in data:
        _print(f"草稿已创建: media_id={data['media_id'][:30]}...")
        return data["media_id"]
    else:
        errcode = data.get("errcode", "unknown")
        errmsg = data.get("errmsg", "unknown")
        _print(f"创建草稿失败: [{errcode}] {errmsg}")
        return None


def publish_draft(access_token: str, media_id: str) -> str | None:
    """Submit a draft for publishing. Returns publish_id on success.

    Note: Articles published via this API won't appear in the subscription
    messages feed. They are published as 'not notified' articles.
    Use the mass-send API if you need push notification.
    """
    import requests

    resp = requests.post(
        f"https://api.weixin.qq.com/cgi-bin/freepublish/submit?access_token={access_token}",
        data=json.dumps({"media_id": media_id}, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json; charset=utf-8"},
        timeout=30,
    )
    data = resp.json()

    if data.get("errcode", 0) == 0:
        publish_id = data.get("publish_id", "")
        _print(f"发布请求已提交: publish_id={publish_id}")
        return str(publish_id)
    else:
        errcode = data.get("errcode", "unknown")
        errmsg = data.get("errmsg", "unknown")
        _print(f"发布失败: [{errcode}] {errmsg}")
        return None


def check_publish_status(access_token: str, publish_id: str) -> dict | None:
    """Check the status of a publish request."""
    import requests

    resp = requests.post(
        f"https://api.weixin.qq.com/cgi-bin/freepublish/get?access_token={access_token}",
        data=json.dumps({"publish_id": publish_id}, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json; charset=utf-8"},
        timeout=15,
    )
    data = resp.json()
    return data


# ──────────────────────────────────────────────
# Main Publish Flow
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
            fm_text = parts[1].strip()
            for line in fm_text.split("\n"):
                line = line.strip()
                if ":" in line:
                    key, _, value = line.partition(":")
                    metadata[key.strip()] = value.strip()
            md_text = parts[2].strip()
    return md_text, metadata


def extract_title(md_text: str) -> str:
    """Extract title from first h1 heading."""
    match = re.match(r"^#\s+(.+)", md_text, re.MULTILINE)
    if match:
        return match.group(1).strip()
    for line in md_text.split("\n"):
        line = line.strip()
        if line:
            return line[:100]
    return "Untitled"


def extract_digest(md_text: str) -> str:
    """Extract a short digest from the article content."""
    lines = md_text.strip().split("\n")
    for line in lines:
        line = line.strip()
        # Skip title, empty lines, headers, images
        if not line or line.startswith("#") or line.startswith("!") or line.startswith("---"):
            continue
        # Clean markdown formatting
        clean = re.sub(r"[*_~`\[\]]", "", line)
        clean = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", clean)
        if len(clean) > 10:
            return clean[:120]
    return ""


def publish_article(
    md_file: str,
    title: str | None = None,
    publish: bool = False,
    thumb: str | None = None,
    author: str = "",
    theme: str = "blue",
) -> bool:
    """Main publish flow: convert markdown and create draft on WeChat.

    Args:
        md_file: Path to markdown file
        title: Article title (auto-extracted from h1 if None)
        publish: If True, also publish the draft (not just save as draft)
        thumb: Path to thumbnail image file
        author: Author name
        theme: WeChat theme for styling

    Returns True on success.
    """
    md_path = Path(md_file)
    if not md_path.exists():
        _print(f"错误: 文件不存在: {md_path}")
        return False

    raw_content = md_path.read_text(encoding="utf-8")

    # Strip frontmatter and extract metadata
    md_content, frontmatter = strip_frontmatter(raw_content)

    # Extract title: CLI arg > frontmatter > h1 heading
    if not title:
        title = frontmatter.get("title") or extract_title(md_content)
    _print(f"文章标题: {title}")

    # Extract author from frontmatter if not provided via CLI
    if not author and frontmatter.get("author"):
        author = frontmatter["author"]

    # Extract digest: frontmatter description > auto-extract from content
    digest = frontmatter.get("description") or extract_digest(md_content)

    # Convert markdown to WeChat HTML
    try:
        from convert import convert_to_wechat_content
        html_content = convert_to_wechat_content(md_content, theme)
    except ImportError:
        _print("错误: 无法导入 convert 模块，请确认 convert.py 存在")
        return False

    # Get config and token
    config = _ensure_config()
    access_token = get_access_token(config)
    if not access_token:
        _print("错误: 无法获取 access_token")
        return False

    # Upload images in HTML content to WeChat
    html_content = replace_images_in_html(access_token, html_content)

    # Upload thumbnail
    _print("正在上传封面图...")
    thumb_media_id = upload_thumb_media(access_token, thumb)
    if not thumb_media_id:
        _print("错误: 封面图上传失败，无法创建草稿")
        _print("提示: 可使用 --thumb 指定一张本地图片作为封面")
        return False

    # Create draft
    _print("正在创建草稿...")
    media_id = create_draft(access_token, title, html_content, thumb_media_id, author, digest)
    if not media_id:
        return False

    _print(f"草稿创建成功！")
    _print(f"  请前往公众号后台查看: https://mp.weixin.qq.com")

    # Optionally publish
    if publish:
        _print("正在发布...")
        publish_id = publish_draft(access_token, media_id)
        if publish_id:
            _print(f"文章已提交发布！")
            _print(f"  注意: 通过 API 发布的文章不会推送给粉丝")
            _print(f"  如需推送，请在公众号后台手动操作群发")
            return True
        else:
            _print("发布失败，但草稿已保存，可在公众号后台手动发布")
            return False

    return True


def batch_publish(
    dir_path: str,
    publish: bool = False,
    thumb: str | None = None,
    author: str = "",
    theme: str = "blue",
    delay: int = 60,
):
    """Batch create drafts for all .md files in a directory.

    Args:
        dir_path: Directory containing .md files
        publish: If True, also publish each draft
        thumb: Path to thumbnail image (shared for all articles)
        author: Author name for all articles
        theme: WeChat theme for styling
        delay: Seconds to wait between operations (avoid rate limiting)
    """
    folder = Path(dir_path)
    if not folder.is_dir():
        _print(f"错误: 目录不存在: {folder}")
        sys.exit(1)

    md_files = sorted(folder.glob("*.md"))
    if not md_files:
        _print(f"目录下没有找到 .md 文件: {folder}")
        sys.exit(1)

    total = len(md_files)
    mode = "创建草稿并发布" if publish else "创建草稿"
    _print(f"=" * 50)
    _print(f"批量操作: 找到 {total} 篇 Markdown 文章")
    _print(f"模式: {mode}")
    _print(f"操作间隔: {delay}s")
    _print(f"=" * 50)

    # Verify config and token once before batch
    config = _ensure_config()
    token = get_access_token(config)
    if not token:
        _print("错误: 无法获取 access_token")
        sys.exit(1)
    _print("access_token 获取成功")

    success_list = []
    fail_list = []

    for idx, md_file in enumerate(md_files, 1):
        _print(f"\n[{idx}/{total}] {md_file.name}")
        _print("-" * 40)

        try:
            ok = publish_article(
                str(md_file), title=None, publish=publish,
                thumb=thumb, author=author, theme=theme,
            )
            if ok:
                success_list.append(md_file.name)
            else:
                fail_list.append(md_file.name)
        except Exception as e:
            _print(f"操作出错: {e}")
            fail_list.append(md_file.name)

        # Delay between operations to avoid rate limiting (skip after last)
        if idx < total:
            _print(f"等待 {delay}s 后继续...")
            time.sleep(delay)

    # Summary
    _print(f"\n{'=' * 50}")
    _print(f"批量操作完成!")
    _print(f"  成功: {len(success_list)}")
    _print(f"  失败: {len(fail_list)}")
    _print(f"  共计: {total}")
    if fail_list:
        _print(f"\n失败文件:")
        for name in fail_list:
            _print(f"  - {name}")


# ──────────────────────────────────────────────
# CLI Entry Point
# ──────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="一键发布 Markdown 文章到微信公众号",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python publish.py --setup                              # 配置 AppID/AppSecret
  python publish.py article.md                           # 创建草稿
  python publish.py article.md --publish                 # 创建草稿并发布
  python publish.py article.md --title "标题"            # 指定标题
  python publish.py article.md --author "作者"           # 指定作者
  python publish.py article.md --thumb cover.jpg         # 指定封面图
  python publish.py --dir ./articles                     # 批量创建草稿
  python publish.py --dir ./articles --publish           # 批量创建草稿并发布
  python publish.py --dir ./articles --delay 30          # 批量操作，间隔 30s

注意:
  - 首次使用需要运行 --setup 配置 AppID 和 AppSecret
  - 需要将本机 IP 添加到公众号 IP 白名单
  - 通过 API 发布的文章不会推送给粉丝（不显示在历史消息中）
  - 如需推送给粉丝，请在公众号后台手动操作群发
  - 默认创建草稿模式，加 --publish 才会直接发布
        """,
    )
    parser.add_argument("input", nargs="?", help="输入 Markdown 文件路径")
    parser.add_argument("--setup", action="store_true", help="配置微信公众号 AppID/AppSecret")
    parser.add_argument("--title", help="文章标题 (默认从 Markdown 第一个 h1 提取)")
    parser.add_argument("--author", default="", help="文章作者")
    parser.add_argument("--thumb", help="封面图片文件路径 (建议 900x500 以上)")
    parser.add_argument("--publish", action="store_true", help="创建草稿后直接发布 (默认仅创建草稿)")
    parser.add_argument("--theme", default="blue", choices=["blue", "green", "dark", "warm"],
                        help="文章主题风格 (默认: blue)")
    parser.add_argument("--dir", help="批量操作：指定目录路径，处理该目录下所有 .md 文件")
    parser.add_argument("--delay", type=int, default=60,
                        help="批量操作时每篇文章间隔秒数 (默认: 60，即1分钟，避免被限流)")

    args = parser.parse_args()

    # Setup mode
    if args.setup:
        success = setup_config()
        sys.exit(0 if success else 1)

    # Batch mode
    if args.dir:
        batch_publish(
            args.dir,
            publish=args.publish,
            thumb=args.thumb,
            author=args.author,
            theme=args.theme,
            delay=args.delay,
        )
        sys.exit(0)

    # Single file mode
    if not args.input:
        parser.print_help()
        sys.exit(0)

    publish_article(
        args.input,
        title=args.title,
        publish=args.publish,
        thumb=args.thumb,
        author=args.author,
        theme=args.theme,
    )


if __name__ == "__main__":
    main()
