#!/usr/bin/env python3
"""
血糖管理技能初始化脚本
创建必要的数据目录和文件
"""

from pathlib import Path
import json

def init_blood_glucose_manager():
    """初始化血糖管理环境"""
    
    # 创建数据目录
    data_dir = Path("/root/.openclaw/workspace/blood-glucose")
    data_dir.mkdir(parents=True, exist_ok=True)
    
    # 创建数据文件（如果不存在）
    data_file = data_dir / "data.jsonl"
    if not data_file.exists():
        data_file.touch()
        print(f"✅ 创建数据文件: {data_file}")
    
    # 创建设置文件
    config_file = data_dir / "config.json"
    if not config_file.exists():
        default_config = {
            "user_name": "",
            "diabetes_type": "",  # type1, type2, gestational, none
            "target_fasting": 6.1,
            "target_post_meal": 7.8,
            "reminders_enabled": False,
            "created_at": ""
        }
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(default_config, f, ensure_ascii=False, indent=2)
        print(f"✅ 创建配置文件: {config_file}")
    
    print("\n✅ 血糖管理技能初始化完成！")
    print(f"数据目录: {data_dir}")
    print("\n您可以开始记录血糖数据了。")
    print("示例: 血糖6.5、空腹血糖7.2、餐后血糖8.8")

if __name__ == "__main__":
    init_blood_glucose_manager()
