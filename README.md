# 环保举报数据分析与督查路线优化

从「发现问题」到「优化决策」的完整闭环：先对环保举报数据做统计分析定位积压痛点，
再将督查队伍的巡查调度抽象为**带容量与时间窗约束的车辆路径问题（CVRPTW）**，
用 Google OR-Tools 建模求解，相比经验派车（贪心最近邻）**总里程降低 20.6%**。

## 项目结构

```
├── data/                       # 生成的数据
│   ├── complaints.csv          # 1000 条举报数据
│   └── b_pending_tasks.csv     # 全市最紧急的 14 个待处理点
├── src/
│   ├── generate_data.py        # 第一步：按业务逻辑构造模拟数据
│   ├── analysis.py             # 第二步：Pandas 统计分析，定位积压痛点
│   ├── vrp_optimization.py     # 第三步（核心）：CVRPTW 建模 + OR-Tools 求解 + 贪心基准对比
│   └── visualize.py            # 第四步：优化前后路线对比可视化
├── output/                     # 运行产物（图表、路线结果）
└── requirements.txt
```

## 快速开始

```bash
pip install -r requirements.txt
python src/generate_data.py
python src/analysis.py
python src/vrp_optimization.py
python src/visualize.py
```

## 核心结果

| 方案 | 总里程 | 说明 |
|---|---|---|
| 贪心最近邻（模拟人工派车） | 160 km | 每辆车反复前往"最近且装得下"的点 |
| OR-Tools 优化求解 | **127 km** | 引导式局部搜索（GLS），限时 10s |
| **里程降低** | **20.6%** | |

![路线对比](https://raw.githubusercontent.com/sylus12/environmental-patrol-optimization/main/output/route_comparison.png)

## 技术栈

- 数据处理：Pandas / NumPy
- 可视化：Matplotlib
- 优化求解：Google OR-Tools（CP-SAT 路由库）
- 模型：CVRPTW（容量约束 + 时间窗约束的车辆路径问题）

## 说明

数据为按环保监督业务逻辑模拟生成（固定随机种子，可复现），重点在于
「业务问题 → 数学模型 → 求解 → 效果评估」的完整方法论。
