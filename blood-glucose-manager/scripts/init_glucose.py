#!/usr/bin/env python3
"""
血糖管理技能初始化脚本
创建数据目录和初始配置
"""

import os
from pathlib import Path

# 基础路径
BASE_DIR = Path("/root/.openclaw/workspace/blood-glucose")
DATA_FILE = BASE_DIR / "data.jsonl"
CONFIG_FILE = BASE_DIR / "config.json"

def init_glucose_manager():
    """初始化血糖管理系统"""
    
    print("=" * 60)
    print("🩸 血糖管理助手 - 初始化")
    print("=" * 60)
    
    # 创建数据目录
    if not BASE_DIR.exists():
        BASE_DIR.mkdir(parents=True, exist_ok=True)
        print(f"\n✅ 创建数据目录: {BASE_DIR}")
    else:
        print(f"\n✓ 数据目录已存在: {BASE_DIR}")
    
    # 创建空数据文件
    if not DATA_FILE.exists():
        DATA_FILE.touch()
        print(f"✅ 创建数据文件: {DATA_FILE}")
    else:
        print(f"✓ 数据文件已存在: {DATA_FILE}")
    
    # 默认配置
    default_config = {
        "units": "mmol/L",
        "target_fasting": {"min": 4.4, "max": 6.1},
        "target_post_meal": {"min": 4.4, "max": 7.8},
        "reminders": {
            "fasting": True,
            "breakfast_post": True,
            "lunch_post": True,
            "dinner_post": True,
            "weekly_report": True,
            "monthly_report": True
        },
        "created_at": str(__import__('datetime').datetime.now())
    }
    
    import json
    if not CONFIG_FILE.exists():
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(default_config, f, ensure_ascii=False, indent=2)
        print(f"✅ 创建配置文件: {CONFIG_FILE}")
    else:
        print(f"✓ 配置文件已存在: {CONFIG_FILE}")
    
    # 检查脚本可执行权限
    scripts_dir = Path(__file__).parent
    scripts = ["record_glucose.py", "generate_report.py", "query_stats.py", "set_reminders.py"]
    
    print("\n📋 脚本状态：")
    for script in scripts:
        script_path = scripts_dir / script
        if script_path.exists():
            print(f"  ✓ {script}")
        else:
            print(f"  ⚠️ {script} (未找到)")
    
    print("\n" + "=" * 60)
    print("✅ 初始化完成！")
    print("=" * 60)
    
    print("\n📝 使用指南：")
    print("  1. 记录血糖: python scripts/record_glucose.py --value 6.5")
    print("  2. 查看统计: python scripts/query_stats.py --days 7")
    print("  3. 生成报告: python scripts/generate_report.py --period weekly")
    print("  4. 设置提醒: python scripts/set_reminders.py --list")
    
    print("\n💡 或者直接对话：")
    print('  "血糖7.2"')
    print('  "查看本周血糖"')
    print('  "生成血糖周报"')
    
    print("=" * 60)

if __name__ == "__main__":
    init_glucose_manager()
