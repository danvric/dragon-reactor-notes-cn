# predict_numpy.py (在 Ubuntu 上跑)
import numpy as np
import os
import time

current_dir = os.path.dirname(os.path.abspath(__file__))
weights_file = os.path.join(current_dir, 'weights.npz')

if not os.path.exists(weights_file):
    raise FileNotFoundError(f"找不到权重文件: {weights_file}，请从本地电脑拷过来！")

weights = np.load(weights_file)
NUM_CHANNELS = 380

def predict(chosen_indices):
    x = np.zeros((1, 4 * NUM_CHANNELS), dtype=np.float32)
    for j, idx in enumerate(chosen_indices):
        x[0, j * NUM_CHANNELS + idx] = 1.0
        
    z1 = np.dot(x, weights['W1']) + weights['b1']
    a1 = np.maximum(z1, 0)
    z2 = np.dot(a1, weights['W2']) + weights['b2']
    a2 = np.maximum(z2, 0)
    z3 = np.dot(a2, weights['W3']) + weights['b3']
    
    return float(z3[0, 0]), float(z3[0, 1])

if __name__ == "__main__":
    # 拿 dataset.csv 里的第一条数据来测试
    test_idx = [354, 313, 260, 152] # 对应 ['U11', 'R20', 'P06', 'K07']
    
    start_time = time.time()
    keff, ppf = predict(test_idx)
    end_time = time.time()
    
    print(f"测试输入: {test_idx}")
    print(f"预测结果: Keff={keff:.5f}, PPF={ppf:.4f}")
    print(f"真实结果: Keff=0.9961516, PPF=1.2999")
    print(f"单次推理耗时: {(end_time - start_time) * 1000:.2f} 毫秒")
    print("看到这行字，说明环境彻底打通了！")