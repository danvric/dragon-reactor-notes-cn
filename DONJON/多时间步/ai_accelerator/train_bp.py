# train_bp.py (在本地电脑运行)
import pandas as pd
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
import os

print("加载数据集...")
df = pd.read_csv('dataset.csv')
# 假设你的通道总数是 380
NUM_CHANNELS = 380 
INPUT_DIM = 4 * NUM_CHANNELS
OUTPUT_DIM = 2 # Keff 和 PPF

# 构造 One-hot 输入特征
X = np.zeros((len(df), INPUT_DIM), dtype=np.float32)
for i in range(len(df)):
    for j in range(4):
        ch_idx = int(df.iloc[i, j])
        X[i, j * NUM_CHANNELS + ch_idx] = 1.0

# 标签
y = df[['Keff', 'PPF']].values.astype(np.float32)

# 转换为 PyTorch Tensor
X_tensor = torch.tensor(X)
y_tensor = torch.tensor(y)
dataloader = DataLoader(TensorDataset(X_tensor, y_tensor), batch_size=32, shuffle=True)

# 定义 BP 神经网络 (参考王端论文的结构：输入 -> 隐层 -> 隐层 -> 输出)
class BPModel(nn.Module):
    def __init__(self):
        super(BPModel, self).__init__()
        self.net = nn.Sequential(
            nn.Linear(INPUT_DIM, 256),
            nn.ReLU(),
            nn.Linear(256, 128),
            nn.ReLU(),
            nn.Linear(128, OUTPUT_DIM)
        )
    def forward(self, x):
        return self.net(x)

model = BPModel()
criterion = nn.MSELoss() 
optimizer = optim.Adam(model.parameters(), lr=0.001)

print("开始训练...")
epochs = 200 # 数据量较小时可以多训练几次
for epoch in range(epochs):
    epoch_loss = 0.0
    for batch_X, batch_y in dataloader:
        optimizer.zero_grad()
        outputs = model(batch_X)
        loss = criterion(outputs, batch_y)
        loss.backward()
        optimizer.step()
        epoch_loss += loss.item()
    
    if (epoch + 1) % 20 == 0:
        print(f"Epoch {epoch+1}/{epochs}, Loss: {epoch_loss/len(dataloader):.6f}")

# 导出权重为 numpy 格式，方便 Ubuntu 上的纯 numpy 推理
weights_dict = {
    'W1': model.net[0].weight.detach().numpy().T, 'b1': model.net[0].bias.detach().numpy(),
    'W2': model.net[2].weight.detach().numpy().T, 'b2': model.net[2].bias.detach().numpy(),
    'W3': model.net[4].weight.detach().numpy().T, 'b3': model.net[4].bias.detach().numpy()
}
np.savez('weights.npz', **weights_dict)
print("权重已保存至 weights.npz！")