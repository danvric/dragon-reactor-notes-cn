# plot_final.py
import pandas as pd
import matplotlib.pyplot as plt

plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

df = pd.read_csv('optimization_history_closedloop.csv')

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 9), sharex=True)

# 图 1：Keff 波浪图
ax1.plot(df['Day'], df['Real_Keff'], marker='.', linestyle='-', color='b', linewidth=1.5, label='真实 Keff (DD)')
ax1.axhline(y=0.996, color='r', linestyle='--', alpha=0.6, label='官方基准 0.9962')
ax1.fill_between(df['Day'], 0.995, 0.999, color='blue', alpha=0.05) # 添加辅助背景
ax1.set_ylabel('有效增殖因数 (Keff)', fontsize=14)
ax1.set_title('CANDU 堆 360 天连续换料模拟：基于闭环 PSO 的 Keff 稳定控制', fontsize=16, fontweight='bold')
ax1.legend(loc='lower left')
ax1.grid(True, alpha=0.3)

# 图 2：PPF 红线压制图
ax2.plot(df['Day'], df['Real_PPF'], marker='o', markersize=3, linestyle='-', color='g', linewidth=1.5, label='真实 PPF (DD)')
ax2.axhline(y=1.4, color='r', linestyle='-', linewidth=2, label='安全限值 1.4')

# 把超标的区域涂红
ax2.fill_between(df['Day'], 1.4, df['Real_PPF'], where=(df['Real_PPF'] > 1.4), 
                 color='red', alpha=0.3, label='极少数局部超限 (物理极限博弈)')

ax2.set_xlabel('天数 (Day)', fontsize=14)
ax2.set_ylabel('通道功率峰因子 (PPF)', fontsize=14)
ax2.set_title('CANDU 堆 360 天连续换料模拟：PPF 安全红线控制', fontsize=16, fontweight='bold')
ax2.legend(loc='upper right')
ax2.grid(True, alpha=0.3)
ax2.set_ylim(1.2, 1.5) # 把纵轴范围缩放到 1.2~1.5，看得更清楚

plt.tight_layout()
plt.savefig('final_360_days_result.png', dpi=300)
plt.show()