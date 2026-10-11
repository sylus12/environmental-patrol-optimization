# -*- coding: utf-8 -*-
"""
第一步：构造环保举报模拟数据
============================
为什么需要这个文件？
    真实业务数据拿不到，所以我们按照"环保监督系统"的业务逻辑，
    自己造 1000 条以假乱真的举报数据。面试时可以说：
    "数据是按业务逻辑模拟的，重点在建模与求解方法。"

每条举报数据包含的字段（列）：
    id        举报编号
    region    区域（A/B/C/D 四个区）
    type      污染类型（水/气/声/固废）
    x, y      举报地点坐标（公里，相对于督查中心）
    status    处理状态（待处理 / 处理中 / 已完成）
    deadline  要求处理完毕的时限（小时，从举报时刻算起）
    workload  处理该举报所需的工作量（折算为"件"）

运行方式：
    python src/generate_data.py
运行结果：
    在 data/ 目录下生成 complaints.csv
"""

import numpy as np
import pandas as pd

# 固定随机种子：每次运行生成完全相同的数据，保证实验可复现
# （面试加分点：可复现性是算法工程的基本要求）
np.random.seed(42)

N = 1000  # 举报总数

# ---- 1. 区域与污染类型 ----
# 故意让 B 区举报更多、积压更严重，为后面的"发现问题"做铺垫
regions = np.random.choice(["A", "B", "C", "D"], size=N, p=[0.20, 0.35, 0.25, 0.20])
types = np.random.choice(
    ["水污染", "大气污染", "噪声", "固体废物"], size=N, p=[0.40, 0.30, 0.15, 0.15]
)

# ---- 2. 坐标 ----
# 每个区是以某个中心点为核心的一片区域（正态分布散布），
# B 区中心离督查中心(0,0)最远 -> 后面优化时路程矛盾更突出，故事更好看
centers = {"A": (8, 6), "B": (18, 14), "C": (6, 16), "D": (14, 4)}
xs, ys = [], []
for r in regions:
    cx, cy = centers[r]
    xs.append(np.random.normal(cx, 2.5))
    ys.append(np.random.normal(cy, 2.5))

# ---- 3. 处理状态 ----
# B 区待处理概率更高（制造"积压"这一业务痛点）
status = []
for r in regions:
    if r == "B":
        status.append(np.random.choice(["待处理", "处理中", "已完成"], p=[0.45, 0.25, 0.30]))
    else:
        status.append(np.random.choice(["待处理", "处理中", "已完成"], p=[0.20, 0.25, 0.55]))

# ---- 4. 处理时限与工作量 ----
# 水污染更紧急（时限短），工作量 1~3 件不等
deadline = [np.random.randint(8, 24) if t == "水污染" else np.random.randint(24, 72) for t in types]
workload = np.random.randint(1, 4, size=N)

df = pd.DataFrame(
    {
        "id": range(1, N + 1),
        "region": regions,
        "type": types,
        "x": np.round(xs, 2),
        "y": np.round(ys, 2),
        "status": status,
        "deadline": deadline,
        "workload": workload,
    }
)

df.to_csv("data/complaints.csv", index=False, encoding="utf-8-sig")
print(f"已生成 {len(df)} 条举报数据 -> data/complaints.csv")
print(df.head())
