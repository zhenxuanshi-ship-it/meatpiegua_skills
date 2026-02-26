#!/usr/bin/env python3
"""
设置血糖测量提醒
使用 cron 定时任务
"""

import argparse
import json

REMINDERS = {
    "fasting": {
        "name": "空腹血糖提醒",
        "schedule": {"kind": "cron", "expr": "0 7 * * *", "tz": "Asia/Shanghai"},
        "message": "⏰ 该测空腹血糖了！记得在起床后、吃早餐前测量。"
    },
    "breakfast_post": {
        "name": "早餐后血糖提醒",
        "schedule": {"kind": "cron", "expr": "0 10 * * *", "tz": "Asia/Shanghai"},
        "message": "⏰ 该测早餐后血糖了！距离早餐约2小时。"
    },
    "lunch_post": {
        "name": "午餐后血糖提醒",
        "schedule": {"kind": "cron", "expr": "0 14 * * *", "tz": "Asia/Shanghai"},
        "message": "⏰ 该测午餐后血糖了！距离午餐约2小时。"
    },
    "dinner_post": {
        "name": "晚餐后血糖提醒",
        "schedule": {"kind": "cron", "expr": "0 20 * * *", "tz": "Asia/Shanghai"},
        "message": "⏰ 该测晚餐后血糖了！距离晚餐约2小时。"
    },
    "weekly_report": {
        "name": "血糖周报生成",
        "schedule": {"kind": "cron", "expr": "0 21 * * 0", "tz": "Asia/Shanghai"},
        "message": "📊 正在生成本周血糖报告..."
    },
    "monthly_report": {
        "name": "血糖月报生成",
        "schedule": {"kind": "cron", "expr": "0 9 1 * *", "tz": "Asia/Shanghai"},
        "message": "📊 正在生成本月血糖报告..."
    }
}

def print_setup_guide():
    """打印设置指南"""
    print("=" * 60)
    print("🔔 血糖测量提醒设置指南")
    print("=" * 60)
    
    print("\n📋 可设置的提醒类型：")
    print("  1. fasting         - 空腹血糖 (每天 7:00)")
    print("  2. breakfast_post  - 早餐后 (每天 10:00)")
    print("  3. lunch_post      - 午餐后 (每天 14:00)")
    print("  4. dinner_post     - 晚餐后 (每天 20:00)")
    print("  5. weekly_report   - 周报 (每周日 21:00)")
    print("  6. monthly_report  - 月报 (每月1日 9:00)")
    print("  7. all             - 设置所有提醒")
    
    print("\n💡 设置方法：")
    print("  使用 OpenClaw 的 cron 工具添加定时任务")
    
    print("\n📝 示例命令：")
    print("-" * 60)
    
    # 空腹血糖提醒
    print("\n# 空腹血糖提醒")
    reminder = REMINDERS["fasting"]
    cron_job = {
        "name": reminder["name"],
        "schedule": reminder["schedule"],
        "payload": {"kind": "systemEvent", "text": reminder["message"]},
        "sessionTarget": "main"
    }
    print(f'cron.add {json.dumps(cron_job, ensure_ascii=False, indent=2)}')
    
    print("\n" + "=" * 60)

def get_all_cron_commands():
    """获取所有cron命令"""
    commands = []
    
    for key, reminder in REMINDERS.items():
        cron_job = {
            "name": reminder["name"],
            "schedule": reminder["schedule"],
            "payload": {"kind": "systemEvent", "text": reminder["message"]},
            "sessionTarget": "main"
        }
        commands.append((key, cron_job))
    
    return commands

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="设置血糖测量提醒")
    parser.add_argument("--list", "-l", action="store_true", help="列出所有提醒设置")
    parser.add_argument("--type", "-t", type=str, help="设置特定提醒类型")
    
    args = parser.parse_args()
    
    if args.list or not args.type:
        print_setup_guide()
    else:
        if args.type in REMINDERS:
            reminder = REMINDERS[args.type]
            print(f"\n设置提醒: {reminder['name']}")
            print(f"时间: {reminder['schedule']['expr']}")
            print(f"内容: {reminder['message']}")
            print("\n请使用上面的 cron.add 命令手动添加")
        elif args.type == "all":
            print("\n所有提醒设置：")
            for key, reminder in REMINDERS.items():
                print(f"\n{key}:")
                print(f"  名称: {reminder['name']}")
                print(f"  时间: {reminder['schedule']['expr']}")
        else:
            print(f"未知的提醒类型: {args.type}")
            print("使用 --list 查看可用类型")
