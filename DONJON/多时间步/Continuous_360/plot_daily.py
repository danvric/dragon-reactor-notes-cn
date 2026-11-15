import csv
import matplotlib.pyplot as plt

def plot_daily_history(csv_file):
    days, keffs, ppfs = [], [], []
    
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            days.append(int(row["Day"]))
            keffs.append(float(row["Keff"]))
            ppfs.append(float(row["PPF"]))

    fig, ax1 = plt.subplots(figsize=(12, 6), dpi=120)
    ax2 = ax1.twinx()

    # 左轴画 Keff
    ax1.plot(days, keffs, marker='o', color='tab:blue', linewidth=2.5, markersize=8, label='Keff (有效增殖因数)')
    ax1.set_xlabel('Operating Time (Days)', fontsize=12, fontweight='bold')
    ax1.set_ylabel('Keff', fontsize=12, fontweight='bold', color='tab:blue')
    ax1.tick_params(axis='y', labelcolor='tab:blue')
    
    # 动态调整 Keff 的 Y 轴范围，让波动更明显
    ax1.set_ylim(min(keffs) - 0.0002, max(keffs) + 0.0002)
    
    # 画 Keff 的官方基准线 (0.9962499)
    ax1.axhline(y=0.9962499, color='tab:blue', linestyle='-.', alpha=0.5, label='Official Baseline (0.99625)')

    # 右轴画 PPF
    ax2.plot(days, ppfs, marker='s', color='tab:green', linewidth=2, linestyle='--', markersize=6, label='PPF (功率峰因子)')
    ax2.set_ylabel('PPF', fontsize=12, fontweight='bold', color='tab:green')
    ax2.tick_params(axis='y', labelcolor='tab:green')
    
    # 动态调整 PPF 的 Y 轴范围
    ax2.set_ylim(1.1, 1.5)
    
    # 画安全红线 (1.4)
    ax2.axhline(y=1.4, color='red', linestyle=':', linewidth=2, label='PPF Safety Limit (1.4)')

    # 合并图例
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='lower center', fontsize=10)

    plt.title('CANDU-6 Continuous Refueling Optimization (PSO Driven)', fontsize=14, fontweight='bold')
    ax1.grid(True, linestyle='--', alpha=0.4)
    
    plt.tight_layout()
    out_fig = 'daily_optimization_30days.png'
    plt.savefig(out_fig, dpi=300)
    print(f"✅ 绘图完成！图片已保存为: {out_fig}")
    plt.show()

if __name__ == "__main__":
    plot_daily_history('daily_optimization_history.csv')