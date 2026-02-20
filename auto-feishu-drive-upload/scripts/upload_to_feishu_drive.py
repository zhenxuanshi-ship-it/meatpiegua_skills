#!/usr/bin/env python3
"""
上传文件到飞书云盘
用法: python3 upload_to_feishu_drive.py <file_path> [--folder-token <folder_token>] [--token <access_token>]
"""

import sys
import os
import argparse
import base64
import json
import urllib.request
import urllib.error

FEISHU_UPLOAD_URL = "https://open.feishu.cn/open-apis/drive/v1/files/upload_all"

def get_upload_token(access_token):
    """获取文件上传凭证"""
    url = "https://open.feishu.cn/open-apis/drive/v1/files/upload_prepare"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    data = json.dumps({"file_name": "temp", "parent_type": "explorer", "parent_node": "root"}).encode()
    
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode())
            if result.get("code") == 0:
                return result["data"]["upload_ticket"]
            else:
                print(f"获取上传凭证失败: {result.get('msg')}", file=sys.stderr)
                return None
    except urllib.error.HTTPError as e:
        print(f"HTTP错误: {e.code} - {e.read().decode()}", file=sys.stderr)
        return None

def upload_file(file_path, folder_token, access_token):
    """上传文件到飞书云盘"""
    if not os.path.exists(file_path):
        print(f"错误: 文件不存在 {file_path}", file=sys.stderr)
        return False
    
    file_name = os.path.basename(file_path)
    file_size = os.path.getsize(file_path)
    
    # 读取文件内容
    with open(file_path, "rb") as f:
        file_content = f.read()
    
    # 构建 multipart/form-data 请求
    boundary = "----FormBoundary7MA4YWxkTrZu0gW"
    
    # 构建请求体
    body_parts = []
    
    # parent_node (文件夹token)
    body_parts.append(f"--{boundary}\r\n".encode())
    body_parts.append(f'Content-Disposition: form-data; name="parent_node"\r\n\r\n'.encode())
    body_parts.append(f"{folder_token}\r\n".encode())
    
    # parent_type
    body_parts.append(f"--{boundary}\r\n".encode())
    body_parts.append(f'Content-Disposition: form-data; name="parent_type"\r\n\r\n'.encode())
    body_parts.append(b"explorer\r\n")
    
    # size
    body_parts.append(f"--{boundary}\r\n".encode())
    body_parts.append(f'Content-Disposition: form-data; name="size"\r\n\r\n'.encode())
    body_parts.append(f"{file_size}\r\n".encode())
    
    # file_name
    body_parts.append(f"--{boundary}\r\n".encode())
    body_parts.append(f'Content-Disposition: form-data; name="file_name"\r\n\r\n'.encode())
    body_parts.append(f"{file_name}\r\n".encode())
    
    # file 内容
    body_parts.append(f"--{boundary}\r\n".encode())
    body_parts.append(f'Content-Disposition: form-data; name="file"; filename="{file_name}"\r\n'.encode())
    body_parts.append(b"Content-Type: application/octet-stream\r\n\r\n")
    body_parts.append(file_content)
    body_parts.append(b"\r\n")
    
    # 结束boundary
    body_parts.append(f"--{boundary}--\r\n".encode())
    
    body = b"".join(body_parts)
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": f"multipart/form-data; boundary={boundary}",
        "Content-Length": str(len(body))
    }
    
    req = urllib.request.Request(FEISHU_UPLOAD_URL, data=body, headers=headers, method="POST")
    
    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode())
            if result.get("code") == 0:
                file_token = result["data"]["file_token"]
                print(f"✅ 上传成功!")
                print(f"   文件名: {file_name}")
                print(f"   文件Token: {file_token}")
                return True
            else:
                print(f"❌ 上传失败: {result.get('msg')}", file=sys.stderr)
                return False
    except urllib.error.HTTPError as e:
        error_body = e.read().decode()
        print(f"❌ HTTP错误 {e.code}: {error_body}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"❌ 错误: {str(e)}", file=sys.stderr)
        return False

def main():
    parser = argparse.ArgumentParser(description="上传文件到飞书云盘")
    parser.add_argument("file_path", help="要上传的文件路径")
    parser.add_argument("--folder-token", default="root", help="目标文件夹的token (默认为root)")
    parser.add_argument("--token", help="飞书访问令牌 (Access Token)")
    
    args = parser.parse_args()
    
    # 优先使用命令行参数，其次使用环境变量
    access_token = args.token or os.environ.get("FEISHU_ACCESS_TOKEN")
    
    if not access_token:
        print("❌ 错误: 未提供飞书访问令牌", file=sys.stderr)
        print("   请通过 --token 参数提供，或设置 FEISHU_ACCESS_TOKEN 环境变量", file=sys.stderr)
        return 1
    
    if upload_file(args.file_path, args.folder_token, access_token):
        return 0
    else:
        return 1

if __name__ == "__main__":
    sys.exit(main())