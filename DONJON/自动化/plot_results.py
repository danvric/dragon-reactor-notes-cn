import sys
import os
import csv
import matplotlib.pyplot as plt

def read_csv_data(file_path):
    gens, keffs, ppfs = [], [], []
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            gens.append(int(row["Generation"]))
            keffs.append(float(row["Best_Keff"]))
            ppfs.append(float(row["Best_PPF"]))
    return gens, keffs, ppfs

def main():
    # 支持拖拽一个或多个文件，或者直接运行
    if len(sys.argv) > 1:
        file_paths = sys.argv[1:]
    else:
        user_input = input("请把 CSV 文件拖拽到这里（支持多个文件对比），然后按回车：\n").strip(" '\"\n")
        file_paths = [p.strip(" '\"\n") for p in user_input.split() if p]

    fig, ax1 = plt.subplots(figsize=(10, 6))
    ax2 = ax1.twinx()  
    
    colors = ['tab:blue', 'tab:green', 'tab:purple']
    
    for idx, file_path in enumerate(file_paths):
        if not os.path.exists(file_path):
            print(f"❌ 找不到文件：{file_path}")
            continue
            
        label_name = os.path.basename(file_path).split('.')[0].upper()
        gens, keffs, ppfs = read_csv_data(file_path)
        
        color = colors[idx % len(colors)]
        
        # 左轴画 Keff (实线)
        ax1.plot(gens, keffs, marker='o', color=color, linewidth=2, label=f'{label_name} Keff')
        
        # 右轴画 PPF (虚线)
        ax2.plot(gens, ppfs, marker='s', color=color, linestyle='--', alpha=0.6, label=f'{label_name} PPF')

    # 设置轴和标签
    ax1.set_xlabel('Generation (迭代代数)', fontsize=12)
    ax1.set_ylabel('Best Keff (最优有效增殖因数)', fontsize=12)
    ax2.set_ylabel('Best PPF (最优功率峰因子)', fontsize=12)
    
    # 画安全红线 (PPF=1.4)
    ax2.axhline(y=1.4, color='red', linestyle=':', linewidth=2, label='PPF Safety Limit (1.4)')
    
    ax1.grid(True, linestyle='--', alpha=0.5)
    
    # 合并图例
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='center right')
    
    plt.title('PSO vs GA Optimization Progress for CANDU-6', fontsize=14, fontweight='bold')
    plt.tight_layout()
    
    out_fig = 'optimization_comparison.png'
    plt.savefig(out_fig, dpi=300)
    print(f"\n✅ 绘图完成！图片已保存为: {os.path.abspath(out_fig)}")
    plt.show()

if __name__ == "__main__":
    main()