---
name: blood-glucose-manager
description: 个人血糖管理技能，用于记录、分析、监控血糖数据。支持自动判断血糖类型（空腹/餐前/餐后/随机），根据医学标准给出健康评估，生成周报月报统计，设置定时测量提醒。当用户需要记录血糖、查看血糖趋势、获取血糖分析报告或设置测量提醒时触发。
---

# 血糖管理助手

## 核心功能

1. **血糖数据录入** - 智能识别血糖类型，自动存储
2. **医学标准评估** - 根据WHO/ADA标准判断血糖水平
3. **统计报告生成** - 周报、月报、自定义时段分析
4. **可视化图表** - 血糖趋势曲线图
5. **定时提醒** - 测量提醒（空腹、三餐餐后）

## 血糖数据存储

数据存储在 `~/.openclaw/workspace/blood-glucose/data.jsonl`，每行一条记录：

```json
{
  "timestamp": "2026-02-26T07:30:00+08:00",
  "value": 6.2,
  "type": "fasting",
  "type_name": "空腹血糖",
  "meal": null,
  "notes": "晨起测量"
}
```

**血糖类型判定逻辑**：
1. **空腹血糖 (fasting)** - 时间 5:00-9:00，且无进食记录超过8小时
2. **餐前血糖 (pre_meal)** - 时间 6:00-9:00、11:00-13:00、17:00-20:00
3. **餐后血糖 (post_meal)** - 用户明确说"餐后"或距离上一餐1-2小时
4. **随机血糖 (random)** - 其他时间或用户明确说"随机"

**meal字段**：当type为post_meal时，记录是哪一餐（breakfast/lunch/dinner）

## 医学评估标准

参考 `references/glucose-standards.md` 获取详细的血糖判断标准。

**核心指标**（单位：mmol/L）：

| 类型 | 正常 | 空腹血糖受损/糖耐量异常 | 糖尿病 |
|------|------|------------------------|--------|
| 空腹 | <6.1 | 6.1-7.0 | ≥7.0 |
| 餐后2h | <7.8 | 7.8-11.1 | ≥11.1 |
| 随机 | <11.1 | - | ≥11.1 |

**妊娠期标准更严格**：
| 类型 | 正常 | 异常 |
|------|------|------|
| 空腹 | <5.1 | ≥5.1 |
| 餐后1h | <10.0 | ≥10.0 |
| 餐后2h | <8.5 | ≥8.5 |

## 使用流程

### 1. 录入血糖

用户说："血糖6.5"、"空腹血糖7.2"、"晚餐后两小时8.8"

**执行步骤**：
1. 解析血糖值和时间
2. 根据时间或描述判断血糖类型
3. 对照医学标准给出评估
4. 保存到数据文件
5. 返回录入结果和健康建议

**示例代码**：
```python
# 使用 scripts/record_glucose.py
exec: python /root/.openclaw/workspace/skills/blood-glucose-manager/scripts/record_glucose.py --value 6.5 --time "07:30" --notes "晨起"
```

### 2. 生成报告

**周报**：每周日晚上自动生成，包含：
- 本周测量次数统计
- 各类型血糖平均值、最高/最低值
- 正常/异常比例
- 趋势分析（与上周对比）

**月报**：每月最后一天生成，包含：
- 月度统计摘要
- 血糖控制达标率
- 趋势图表
- 建议

**手动生成**：
```python
exec: python /root/.openglucose/scripts/generate_report.py --period weekly
exec: python /root/.openclaw/workspace/skills/blood-glucose-manager/scripts/generate_report.py --period monthly
```

### 3. 查询统计

用户说："查看本周血糖"、"最近7天血糖趋势"、"血糖统计图"

**执行步骤**：
1. 确定查询时间段
2. 读取数据文件，筛选记录
3. 生成统计摘要
4. 生成可视化图表（ASCII图表或matplotlib）
5. 返回结果

### 4. 设置提醒

使用 cron 工具设置定时提醒：

```python
# 空腹血糖提醒（每天早上7:00）
cron.add {
  "name": "空腹血糖提醒",
  "schedule": {"kind": "cron", "expr": "0 7 * * *", "tz": "Asia/Shanghai"},
  "payload": {"kind": "systemEvent", "text": "⏰ 该测空腹血糖了！记得在起床后、吃早餐前测量。"},
  "sessionTarget": "main"
}

# 早餐后2小时（假设早餐8:00）
cron.add {
  "name": "早餐后血糖提醒",
  "schedule": {"kind": "cron", "expr": "0 10 * * *", "tz": "Asia/Shanghai"},
  "payload": {"kind": "systemEvent", "text": "⏰ 该测早餐后血糖了！距离早餐约2小时。"},
  "sessionTarget": "main"
}

# 午餐后2小时（假设午餐12:00）
cron.add {
  "name": "午餐后血糖提醒",
  "schedule": {"kind": "cron", "expr": "0 14 * * *", "tz": "Asia/Shanghai"},
  "payload": {"kind": "systemEvent", "text": "⏰ 该测午餐后血糖了！距离午餐约2小时。"},
  "sessionTarget": "main"
}

# 晚餐后2小时（假设晚餐18:00）
cron.add {
  "name": "晚餐后血糖提醒",
  "schedule": {"kind": "cron", "expr": "0 20 * * *", "tz": "Asia/Shanghai"},
  "payload": {"kind": "systemEvent", "text": "⏰ 该测晚餐后血糖了！距离晚餐约2小时。"},
  "sessionTarget": "main"
}
```

## 输出格式

### 单次测量结果

```
📊 血糖记录已保存
━━━━━━━━━━━━━━━━━━━━━━━━━
时间：2026-02-26 07:30
类型：空腹血糖
数值：6.2 mmol/L

📋 评估结果：正常范围
━━━━━━━━━━━━━━━━━━━━━━━━━
参考标准：空腹血糖 < 6.1 mmol/L 为正常
您的结果：6.2 mmol/L（略高于正常值）

💡 建议：
• 注意控制饮食，减少高糖食物摄入
• 建议定期监测，关注趋势变化
• 如持续偏高，请咨询医生
```

### 统计报告

```
📈 血糖周报（2026-02-20 ~ 2026-02-26）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 测量概况
测量次数：21次
达标次数：18次（85.7%）

📉 空腹血糖
平均：6.1 mmol/L
最高：7.2 mmol/L（2026-02-22）
最低：5.4 mmol/L（2026-02-24）
达标率：5/7（71.4%）

📊 餐后血糖
早餐：平均 7.8 mmol/L
午餐：平均 8.2 mmol/L  
晚餐：平均 7.5 mmol/L

📈 趋势分析
与上周相比：空腹血糖平均下降 0.3 mmol/L ✅
餐后控制：整体平稳，午餐后略高

💡 本周建议
• 空腹血糖控制较好，继续保持
• 午餐后血糖偏高，建议减少午餐主食量
• 建议增加餐后适量运动
```

## 关键脚本

- `scripts/record_glucose.py` - 记录血糖数据
- `scripts/generate_report.py` - 生成周报/月报
- `scripts/query_stats.py` - 查询统计和图表
- `scripts/set_reminders.py` - 设置定时提醒

## 注意事项

1. **数据备份**：定期备份 `data.jsonl` 文件
2. **单位统一**：所有记录使用 mmol/L（中国标准）
3. **个人差异**：医学标准仅供参考，具体诊断请咨询医生
4. **隐私保护**：血糖数据属于个人健康信息，注意保密
