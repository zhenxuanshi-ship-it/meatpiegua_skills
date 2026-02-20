---
name: auto-feishu-drive-upload
description: 自动将生成的文章/文件上传到飞书云盘。当用户要求"写文章并上传到飞书云盘"、"写完文章后发到我飞书云盘"、"保存到飞书"等类似请求时触发。支持配置目标文件夹，自动完成文件上传到飞书云盘的操作。
license: MIT
---

# 自动上传文件到飞书云盘

这个技能让你能够在完成文章/文件创作后，自动将其上传到你的飞书云盘指定位置。

## 使用场景

当用户有以下请求时触发此技能：
- "帮我写一篇文章，写完后发到飞书云盘"
- "把这个文件保存到我的飞书"
- "写完直接上传到我飞书云盘"
- "创作完成后自动上传到飞书"

## 前置条件

使用此技能需要以下信息：

1. **飞书访问令牌 (Access Token)**
   - 需要在飞书开放平台创建应用并获取
   - 或使用现有应用的访问令牌
   - 可通过环境变量 `FEISHU_ACCESS_TOKEN` 设置

2. **目标文件夹 Token** (可选)
   - 默认为 `root` (云盘根目录)
   - 如需上传到特定文件夹，需要提供该文件夹的 token

## 工作流程

当用户要求"写文章并上传到飞书云盘"时：

1. **创作内容** - 按照用户要求完成文章/文件创作
2. **保存文件** - 将内容保存到本地文件系统
3. **获取上传配置** - 从以下位置获取飞书配置：
   - 用户当前对话中提供的配置
   - 环境变量 `FEISHU_ACCESS_TOKEN`
   - 如果未配置，询问用户提供
4. **执行上传** - 调用 feishu_doc 工具将文档创建到飞书云盘
5. **添加协作者** - 使用 message 工具向用户发送文档链接和协作邀请
6. **确认完成** - 向用户报告上传结果和协作方式

## 文档所有权说明

由于飞书 API 限制，通过应用创建的文档所有者是应用本身（`openclawchannel`）。但我们会自动将用户添加为协作者：

- 用户获得 **可编辑** 权限
- 用户可以随时将文档 **转移所有权** 给自己
- 用户拥有完全的内容控制权

## 使用方法

### 基础用法

用户请求：
> "帮我写一篇商业航天分析文章，写完后发到飞书云盘"

执行步骤：
1. 完成文章创作并保存到 `/root/.openclaw/workspace/essays/xxx.md`
2. 检查是否有 `FEISHU_ACCESS_TOKEN` 环境变量
3. 如有，执行上传脚本
4. 向用户确认上传完成

### 使用脚本上传

```bash
# 使用环境变量中的 token
python3 scripts/upload_to_feishu_drive.py /path/to/file.md

# 显式指定 token 和文件夹
python3 scripts/upload_to_feishu_drive.py /path/to/file.md \
  --token "your-access-token" \
  --folder-token "folder-xxx"
```

### 如何获取飞书访问令牌

1. 访问 [飞书开放平台](https://open.feishu.cn/)
2. 创建企业自建应用
3. 开通 "云文档" 权限（需要 `drive:drive:readonly` 和 `drive:file:write` 权限）
4. 获取应用的 App ID 和 App Secret
5. 使用以下方式获取 Access Token：

```bash
curl -X POST https://open.feishu.cn/open-apis/auth/v3/app_access_token/internal \
  -H "Content-Type: application/json" \
  -d '{
    "app_id": "your-app-id",
    "app_secret": "your-app-secret"
  }'
```

### 如何获取文件夹 Token

1. 在飞书云盘中打开目标文件夹
2. 从浏览器地址栏复制 URL，类似：`https://example.feishu.cn/drive/folder/fldxxx`
3. `fldxxx` 部分即为文件夹 token

## 完整示例流程

### 基础流程

```
用户: 帮我写一篇关于AI的文章，写完后发到飞书云盘

Claude: 
1. 创作文章并保存到本地
2. 使用 feishu_doc 创建文档到飞书云盘
3. 向用户发送协作邀请消息
4. 返回文档链接和协作说明
```

### 协作邀请消息模板

上传完成后，自动发送以下消息给用户：

```
📄 文档已创建：《文档标题》
🔗 https://feishu.cn/docx/xxx

✅ 你已被添加为协作者（可编辑权限）

操作选项：
• 点击链接直接编辑文档
• 在文档右上角「...」→「文档设置」→「转移所有权」
• 分享链接给他人协作
```

## 注意事项

1. **文件大小限制** - 飞书云盘对单个文件有大小限制（通常为 20GB）
2. **权限要求** - 确保应用有足够的权限访问和操作云盘文件
3. **Token 有效期** - Access Token 有过期时间，需要定期刷新
4. **文件名冲突** - 如果目标位置已有同名文件，飞书会自动重命名

## 故障排除

如果遇到上传失败：
1. 检查 Access Token 是否有效
2. 确认文件夹 Token 正确且应用有访问权限
3. 检查文件是否存在且可读
4. 查看错误信息中的具体错误码

## 配置存储 (可选)

为了方便使用，可以在工作区创建配置文件：

```bash
# ~/.openclaw/workspace/config/feishu_drive.conf
FEISHU_ACCESS_TOKEN=your-token-here
DEFAULT_FOLDER_TOKEN=root
```