# plot_three_algorithms.py
import pandas as pd
import matplotlib.pyplot as plt

plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

df_ga = pd.read_csv('ga_history.csv')
df_pso = pd.read_csv('pso_history.csv')
df_dbo = pd.read_csv('dbo_history.csv')

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))

# 图1：Keff 收敛对比
ax1.plot(df_ga['Generation'], df_ga['Best_Keff'],
         marker='s', color='red', linestyle='--', label='GA (遗传算法)')
ax1.plot(df_pso['Generation'], df_pso['Global_Best_Keff'],
         marker='o', color='blue', linestyle='-', label='PSO (粒子群)')
ax1.plot(df_dbo['Generation'], df_dbo['Best_Keff'],
         marker='^', color='green', linestyle='-.', label='DBO (蜣螂优化)')
ax1.axhline(y=0.9962499, color='gray', linestyle=':', label='官方基准 (0.99625)')
ax1.set_title('GA vs PSO vs DBO：Keff 收敛对比', fontsize=14, fontweight='bold')
ax1.set_xlabel('迭代代数', fontsize=12)
ax1.set_ylabel('最优有效增殖因数 (Keff)', fontsize=12)
ax1.legend(loc='lower right')
ax1.grid(True, alpha=0.3)

# 图2：综合得分对比
ax2.plot(df_ga['Generation'], df_ga['Best_Score'],
         marker='s', color='red', linestyle='--', label='GA (遗传算法)')
ax2.plot(df_pso['Generation'], df_pso['Global_Best_Score'],
         marker='o', color='blue', linestyle='-', label='PSO (粒子群)')
ax2.plot(df_dbo['Generation'], df_dbo['Best_Score'],
         marker='^', color='green', linestyle='-.', label='DBO (蜣螂优化)')
ax2.set_title('GA vs PSO vs DBO：适应度综合得分对比', fontsize=14, fontweight='bold')
ax2.set_xlabel('迭代代数', fontsize=12)
ax2.set_ylabel('综合得分', fontsize=12)
ax2.legend(loc='lower right')
ax2.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('Three_Algorithms_Comparison.png', dpi=300)
plt.show()