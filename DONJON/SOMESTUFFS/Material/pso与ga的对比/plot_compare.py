# plot_compare.py
import pandas as pd
import matplotlib.pyplot as plt

plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

df_ga = pd.read_csv('ga_history.csv')
df_pso = pd.read_csv('pso_history.csv')

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))

# --- 图1：Keff 收敛曲线 ---
ax1.plot(df_ga['Generation'], df_ga['Best_Keff'], marker='s', color='red', linestyle='--', label='GA 最优 Keff')
ax1.plot(df_pso['Generation'], df_pso['Global_Best_Keff'], marker='o', color='blue', linestyle='-', label='PSO 最优 Keff')
ax1.axhline(y=0.9962499, color='gray', linestyle=':', label='官方基准 (0.99625)')
ax1.set_title('GA 与 PSO 的 Keff 收敛曲线对比', fontsize=14)
ax1.set_xlabel('迭代代数', fontsize=12)
ax1.set_ylabel('最优有效增殖因数 (Keff)', fontsize=12)
ax1.legend(loc='lower right')
ax1.grid(True, alpha=0.3)

# --- 图2：综合得分收敛曲线 ---
ax2.plot(df_ga['Generation'], df_ga['Best_Score'], marker='s', color='red', linestyle='--', label='GA 综合得分')
ax2.plot(df_pso['Generation'], df_pso['Global_Best_Score'], marker='o', color='blue', linestyle='-', label='PSO 综合得分')
ax2.set_title('GA 与 PSO 的适应度综合得分对比', fontsize=14)
ax2.set_xlabel('迭代代数', fontsize=12)
ax2.set_ylabel('综合得分', fontsize=12)
ax2.legend(loc='lower right')
ax2.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('GA_vs_PSO_Comparison.png', dpi=300)
plt.show()