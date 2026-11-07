import csv
import matplotlib.pyplot as plt

# 读取刚才生成的 csv
generations = []
keffs = []
mbps = []

with open('pso_history.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        generations.append(int(row["Generation"]))
        keffs.append(float(row["Keff"]))
        mbps.append(float(row["MBP"]))

# 计算每一代的最优（最大值）Keff 和 对应的 MBP
best_keff_per_gen = []
best_mbp_per_gen = []

for gen in range(1, max(generations) + 1):
    gen_keffs = [k for g, k in zip(generations, keffs) if g == gen]
    gen_mbps = [m for g, m in zip(generations, mbps) if g == gen]
    
    if gen_keffs:
        best_k = max(gen_keffs)
        best_m = gen_mbps[gen_keffs.index(best_k)]
        best_keff_per_gen.append(best_k)
        best_mbp_per_gen.append(best_m)

# === 开始画图 ===
fig, ax1 = plt.subplots(figsize=(10, 6))

# 画 Keff (左轴，蓝色)
color = 'tab:blue'
ax1.set_xlabel('PSO Generation (迭代代数)', fontsize=12)
ax1.set_ylabel('Best Keff (最优有效增殖因数)', color=color, fontsize=12)
ax1.plot(range(1, len(best_keff_per_gen) + 1), best_keff_per_gen, marker='o', color=color, linewidth=2, label='Best Keff')
ax1.tick_params(axis='y', labelcolor=color)
ax1.grid(True, linestyle='--', alpha=0.6)

# 画 MBP (右轴，红色)
ax2 = ax1.twinx()  
color = 'tab:red'
ax2.set_ylabel('Max Bundle Power (最大棒束功率 kW)', color=color, fontsize=12)
ax2.plot(range(1, len(best_mbp_per_gen) + 1), best_mbp_per_gen, marker='s', color=color, linewidth=2, linestyle='--', label='MBP')
ax2.tick_params(axis='y', labelcolor=color)

# 画出 950kW 的安全限值红线
ax2.axhline(y=950, color='black', linestyle=':', linewidth=2, label='Safety Limit (950 kW)')

# 合并图例
lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc='lower right')

plt.title('PSO Optimization Progress for CANDU-6 Refueling', fontsize=14, fontweight='bold')
plt.tight_layout()
plt.savefig('pso_convergence.png', dpi=300)
plt.show()