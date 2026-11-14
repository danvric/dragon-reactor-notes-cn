import sys
import os
import csv
import matplotlib.pyplot as plt

def read_csv_data(file_path):
    gens, g_keffs, g_ppfs = [], [], []
    gen_keffs, gen_ppfs = [], []
    is_pso = False
    
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        # 检查是不是新版 PSO 的数据结构
        if "Global_Best_Keff" in reader.fieldnames:
            is_pso = True
            
        for row in reader:
            gens.append(int(row["Generation"]))
            
            if is_pso:
                g_keffs.append(float(row["Global_Best_Keff"]))
                g_ppfs.append(float(row["Global_Best_PPF"]))
                gen_keffs.append(float(row["Gen_Best_Keff"]))
                gen_ppfs.append(float(row["Gen_Best_PPF"]))
            else:
                # GA 的旧结构
                g_keffs.append(float(row["Best_Keff"]))
                g_ppfs.append(float(row["Best_PPF"]))
                
    return gens, g_keffs, g_ppfs, gen_keffs, gen_ppfs, is_pso

def main():
    if len(sys.argv) > 1:
        file_paths = sys.argv[1:]
    else:
        user_input = input("请把 CSV 文件拖拽到这里（支持多个文件对比），然后按回车：\n").strip(" '\"\n")
        file_paths = [p.strip(" '\"\n") for p in user_input.split() if p]

    fig, ax1 = plt.subplots(figsize=(10, 6), dpi=120)
    ax2 = ax1.twinx()  
    
    colors = ['tab:blue', 'tab:green', 'tab:purple']
    
    for idx, file_path in enumerate(file_paths):
        if not os.path.exists(file_path):
            print(f"❌ 找不到文件：{file_path}")
            continue
            
        label_name = os.path.basename(file_path).split('.')[0].upper()
        gens, g_keffs, g_ppfs, gen_keffs, gen_ppfs, is_pso = read_csv_data(file_path)
        
        color = colors[idx % len(colors)]
        
        # 1. 画历史全局最优 (实线，带圆点)
        ax1.plot(gens, g_keffs, marker='o', color=color, linewidth=2.5, label=f'{label_name} Global Best Keff')
        ax2.plot(gens, g_ppfs, marker='s', color=color, linestyle='--', linewidth=1.5, alpha=0.8, label=f'{label_name} Global Best PPF')
        
        # 2. 如果是 PSO，额外把每一代的探索轨迹画出来 (点线，透明度高)
        if is_pso and len(gen_keffs) > 0:
            ax1.plot(gens, gen_keffs, linestyle=':', color=color, marker='x', alpha=0.4, label=f'{label_name} Gen Best Keff')
            ax2.plot(gens, gen_ppfs, linestyle=':', color=color, marker='x', alpha=0.3, label=f'{label_name} Gen Best PPF')

    # --- 核心标注 ---
    # 画官方基准线 (Keff = 0.9962499)
    official_keff = 0.9962499
    ax1.axhline(y=official_keff, color='orange', linestyle='-.', linewidth=2, label=f'Official Baseline ({official_keff})')
    
    # 画安全红线 (PPF=1.4)
    ax2.axhline(y=1.4, color='red', linestyle=':', linewidth=2, label='PPF Safety Limit (1.4)')
    
    # 设置轴和标签
    ax1.set_xlabel('Generation (迭代代数)', fontsize=12, fontweight='bold')
    ax1.set_ylabel('Keff (有效增殖因数)', fontsize=12, fontweight='bold')
    ax2.set_ylabel('PPF (功率峰因子)', fontsize=12, fontweight='bold')
    
    # 动态调整 Y 轴范围，让差距更明显
    min_k = min([min(read_csv_data(fp)[1]) for fp in file_paths if os.path.exists(fp)] + [official_keff])
    max_k = max([max(read_csv_data(fp)[1]) for fp in file_paths if os.path.exists(fp)] + [official_keff])
    ax1.set_ylim(min_k - 0.0005, max_k + 0.0005)
    
    ax1.grid(True, linestyle='--', alpha=0.4)
    
    # 合并图例，放在左下角避免遮挡曲线
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='lower right', fontsize=9)
    
    plt.title('PSO vs GA: Optimization Progress (Surpassing Official Baseline)', fontsize=14, fontweight='bold')
    plt.tight_layout()
    
    out_fig = 'optimization_comparison.png'
    plt.savefig(out_fig, dpi=300)
    print(f"\n✅ 绘图完成！图片已保存为: {os.path.abspath(out_fig)}")
    plt.show()

if __name__ == "__main__":
    main()