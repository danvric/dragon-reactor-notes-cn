加入dbo算法，与ga、pso算法进行对比

结果是完全水土不服，完全比不上ga和pso一根

[dbo的python代码](../DBO/dbo_optimizer.py)

结果可视化

![1](./Material/pso与ga的对比/Three_Algorithms_Comparison.png)

[GA数据](./Material/pso与ga的对比/dbo_history.csv)

原因

DBO 因为连续空间机制和离散通道取整的冲突，很快陷入了阶梯式停滞