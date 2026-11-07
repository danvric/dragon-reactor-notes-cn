# pso_optimizer.py
import random
import math
from auto_run import evaluate

# 1. 加载所有合法通道
with open("channels_list.txt", "r") as f:
    valid_channels = [line.strip() for line in f if line.strip()]

NUM_CHANNELS = len(valid_channels)
print(f"PSO 启动，合法通道池大小: {NUM_CHANNELS}")

# ================= 适应度函数 =================
def fitness(particle):
    """
    输入：particle 是一个列表，包含 4 个在 valid_channels 里的索引。
    输出：得分。我们要最大化这个得分。
    """
    # 将索引转换为通道名
    chosen = [valid_channels[i] for i in particle]
    
    # 调用计算引擎
    keff, mbp, mcp = evaluate(chosen)
    
    if keff is None or mbp is None:
        return -999.0  # 如果计算失败，直接给最低分
    
    # 约束条件：参考霍小东，最大棒束功率不能超过 950 kW
    MBP_LIMIT = 950.0
    if mbp > MBP_LIMIT:
        penalty = (mbp - MBP_LIMIT) * 0.1  # 超限越多，惩罚越重
        score = keff - penalty
    else:
        score = keff
    
    # 打印当前评估结果（方便追踪）
    print(f"  评估: {chosen} -> Keff={keff:.5f}, MBP={mbp:.1f}, MCP={mcp:.1f}, Score={score:.5f}")
    return score

# ================= PSO 算法核心 =================
class Particle:
    def __init__(self):
        # 随机初始化位置（4个不重复的通道索引）
        self.position = random.sample(range(NUM_CHANNELS), 4)
        self.velocity = [random.uniform(-1, 1) for _ in range(4)]
        self.best_position = list(self.position)
        self.best_score = -999.0

class PSO:
    def __init__(self, num_particles=10, max_iter=5):
        self.particles = [Particle() for _ in range(num_particles)]
        self.global_best_position = None
        self.global_best_score = -999.0
        self.max_iter = max_iter
        self.w = 0.5  # 惯性权重
        self.c1 = 1.5 # 个体认知
        self.c2 = 1.5 # 社会认知

    def optimize(self):
        for iteration in range(self.max_iter):
            print(f"\n========== PSO 迭代第 {iteration+1} 代 ==========")
            for idx, p in enumerate(self.particles):
                print(f"粒子 {idx+1}:")
                score = fitness(p.position)
                
                # 更新个体最优
                if score > p.best_score:
                    p.best_score = score
                    p.best_position = list(p.position)
                
                # 更新全局最优
                if score > self.global_best_score:
                    self.global_best_score = score
                    self.global_best_position = list(p.position)
            
            # 更新速度和位置
            for p in self.particles:
                for i in range(4):
                    r1, r2 = random.random(), random.random()
                    # 更新速度
                    p.velocity[i] = (self.w * p.velocity[i] + 
                                     self.c1 * r1 * (p.best_position[i] - p.position[i]) +
                                     self.c2 * r2 * (self.global_best_position[i] - p.position[i]))
                    # 更新位置
                    p.position[i] = int(p.position[i] + p.velocity[i])
                    
                # 修复越界和重复问题
                p.position = self.fix_position(p.position)
                
    def fix_position(self, pos):
        # 边界限制
        pos = [max(0, min(NUM_CHANNELS - 1, p)) for p in pos]
        # 去重修复（如果两个位置一样，随机挪动一个）
        while len(set(pos)) < 4:
            for i in range(4):
                if pos.count(pos[i]) > 1:
                    pos[i] = random.randint(0, NUM_CHANNELS - 1)
        return pos

if __name__ == "__main__":
    # 初始化 PSO：10 个粒子，迭代 5 代
    pso = PSO(num_particles=10, max_iter=5)
    pso.optimize()
    
    print("\n====================================")
    print("PSO 寻优结束！")
    best_channels = [valid_channels[i] for i in pso.global_best_position]
    print(f"全局最优换料序列: {best_channels}")
    print(f"全局最优适应度: {pso.global_best_score:.5f}")