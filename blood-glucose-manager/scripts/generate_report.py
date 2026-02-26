#!/usr/bin/env python3
"""
血糖报告生成脚本
生成周报、月报统计
"""

import json
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict
import statistics

DATA_FILE = Path("/root/.openclaw/workspace/blood-glucose/data.jsonl")

def load_data(days=30):
    """加载最近N天的血糖数据"""
    if not DATA_FILE.exists():
        return []
    
    records = []
    cutoff = datetime.now() - timedelta(days=days)
    
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
                record_time = datetime.fromisoformat(record["timestamp"])
                if record_time >= cutoff:
                    record["_datetime"] = record_time
                    records.append(record)
            except:
                continue
    
    return records

def analyze_by_type(records):
    """按血糖类型分组统计"""
    groups = defaultdict(list)
    for r in records:
        groups[r["type"]].append(r["value"])
    
    stats = {}
    for type_name, values in groups.items():
        if not values:
            continue
        stats[type_name] = {
            "count": len(values),
            "avg": round(statistics.mean(values), 2),
            "min": round(min(values), 2),
            "max": round(max(values), 2),
            "values": values
        }
    
    return stats

def count_by_status(records):
    """按状态统计"""
    counts = defaultdict(int)
    for r in records:
        counts[r.get("status", "unknown")] += 1
    return counts

def generate_weekly_report():
    """生成周报"""
    records = load_data(days=7)
    
    if not records:
        print("本周暂无血糖记录")
        return
    
    # 基础统计
    total = len(records)
    type_stats = analyze_by_type(records)
    status_counts = count_by_status(records)
    
    # 计算达标率
    normal_count = status_counts.get("normal", 0)
    normal_rate = round(normal_count / total * 100, 1) if total > 0 else 0
    
    # 获取本周日期范围
    today = datetime.now()
    week_start = today - timedelta(days=6)
    date_range = f"{week_start.strftime('%Y-%m-%d')} ~ {today.strftime('%Y-%m-%d')}"
    
    # 输出报告
    print("=" * 60)
    print(f"📈 血糖周报 ({date_range})")
    print("=" * 60)
    
    print("\n📊 测量概况")
    print(f"  测量次数：{total}次")
    print(f"  达标次数：{normal_count}次 ({normal_rate}%)")
    
    # 空腹血糖
    if "fasting" in type_stats:
        fasting = type_stats["fasting"]
        fasting_normal = sum(1 for v in fasting["values"] if v < 6.1)
        print(f"\n📉 空腹血糖（{fasting['count']}次）")
        print(f"  平均：{fasting['avg']} mmol/L")
        print(f"  范围：{fasting['min']} ~ {fasting['max']} mmol/L")
        print(f"  达标率：{fasting_normal}/{fasting['count']} ({round(fasting_normal/fastin['count']*100,1)}%)")
    
    # 餐后血糖
    if "post_meal" in type_stats:
        post = type_stats["post_meal"]
        post_normal = sum(1 for v in post["values"] if v < 7.8)
        print(f"\n📈 餐后血糖（{post['count']}次）")
        print(f"  平均：{post['avg']} mmol/L")
        print(f"  范围：{post['min']} ~ {post['max']} mmol/L")
        print(f"  达标率：{post_normal}/{post['count']} ({round(post_normal/post['count']*100,1)}%)")
    
    # 其他类型
    for type_name, stats in type_stats.items():
        if type_name in ["fasting", "post_meal"]:
            continue
        type_cn = {"pre_meal": "餐前", "random": "随机"}.get(type_name, type_name)
        print(f"\n📋 {type_cn}血糖（{stats['count']}次）")
        print(f"  平均：{stats['avg']} mmol/L")
        print(f"  范围：{stats['min']} ~ {stats['max']} mmol/L")
    
    # 建议
    print("\n💡 本周建议")
    if "fasting" in type_stats and type_stats["fasting"]["avg"] > 6.1:
        print("  • 空腹血糖偏高，建议晚餐减少主食，睡前避免加餐")
    if "post_meal" in type_stats and type_stats["post_meal"]["avg"] > 7.8:
        print("  • 餐后血糖偏高，建议调整进餐顺序（先蔬菜后主食）")
    if normal_rate >= 80:
        print("  • 整体控制良好，继续保持！")
    elif normal_rate >= 60:
        print("  • 控制尚可，注意监测异常时段")
    else:
        print("  • 控制不理想，建议咨询医生调整方案")
    
    print("=" * 60)

def generate_monthly_report():
    """生成月报"""
    records = load_data(days=30)
    
    if not records:
        print("本月暂无血糖记录")
        return
    
    total = len(records)
    type_stats = analyze_by_type(records)
    status_counts = count_by_status(records)
    
    normal_count = status_counts.get("normal", 0)
    warning_count = status_counts.get("warning", 0)
    danger_count = status_counts.get("danger", 0)
    normal_rate = round(normal_count / total * 100, 1) if total > 0 else 0
    
    today = datetime.now()
    month_start = today - timedelta(days=29)
    date_range = f"{month_start.strftime('%Y-%m-%d')} ~ {today.strftime('%Y-%m-%d')}"
    
    print("=" * 60)
    print(f"📊 血糖月报 ({date_range})")
    print("=" * 60)
    
    print("\n📈 月度概况")
    print(f"  总测量次数：{total}次")
    print(f"  日均测量：{round(total/30, 1)}次")
    print(f"  达标率：{normal_rate}%")
    print(f"  偏高次数：{warning_count}次")
    print(f"  高血糖次数：{danger_count}次")
    
    # 详细统计
    for type_name, stats in type_stats.items():
        type_cn = {
            "fasting": "空腹",
            "post_meal": "餐后",
            "pre_meal": "餐前",
            "random": "随机"
        }.get(type_name, type_name)
        
        print(f"\n📉 {type_cn}血糖（{stats['count']}次）")
        print(f"  平均：{stats['avg']} mmol/L")
        print(f"  最高：{stats['max']} mmol/L")
        print(f"  最低：{stats['min']} mmol/L")
        
        # 计算标准差
        if len(stats["values"]) > 1:
            std = statistics.stdev(stats["values"])
            print(f"  波动：±{round(std, 2)} mmol/L")
    
    # 控制评价
    print("\n📋 控制评价")
    if normal_rate >= 80:
        print("  ✅ 血糖控制优秀")
    elif normal_rate >= 60:
        print("  ⚠️ 血糖控制一般，需加强监测")
    else:
        print("  🚨 血糖控制不佳，建议就医调整治疗方案")
    
    print("\n💡 下月建议")
    print("  • 继续保持规律监测习惯")
    if "fasting" in type_stats:
        avg = type_stats["fasting"]["avg"]
        if avg > 7.0:
            print("  • 空腹血糖控制不理想，重点关注夜间和晨起血糖")
    if "post_meal" in type_stats:
        avg = type_stats["post_meal"]["avg"]
        if avg > 10.0:
            print("  • 餐后血糖偏高，建议调整饮食结构和运动量")
    
    print("=" * 60)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="生成血糖报告")
    parser.add_argument("--period", "-p", choices=["weekly", "monthly"], 
                       default="weekly", help="报告周期")
    
    args = parser.parse_args()
    
    if args.period == "weekly":
        generate_weekly_report()
    else:
        generate_monthly_report()
