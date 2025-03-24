import numpy as np
import torch
import time
import pyopencl as cl
import reikna.cluda as cluda
from reikna.fft import FFT


# 测试参数设置
SIZE = 4096*2  # 增大测试规模
dtype = np.float32
n_trials = 5  # 多次测试取平均值

# 方案1: PyTorch (CPU)
def test_cpu():
    times = []
    for _ in range(n_trials):
        image_cpu = torch.rand(SIZE, SIZE, dtype=torch.float32)
        start = time.time()
        dft_cpu = torch.fft.fft2(image_cpu)
        times.append(time.time() - start)
    avg_time = np.mean(times)
    print(f"PyTorch (CPU) Avg Time: {avg_time:.4f} seconds")
    return avg_time

# 方案2: OpenCL (GPU)
def test_gpu_opencl():
    try:
        api = cluda.ocl_api()
        thr = api.Thread.create()
    except Exception as e:
        print("OpenCL 初始化失败:", e)
        return None

    # 生成复数数据
    image_np = np.random.rand(SIZE, SIZE).astype(dtype) + 1j * np.random.rand(SIZE, SIZE).astype(dtype)
    image_gpu = thr.to_device(image_np)
    fft = FFT(image_gpu).compile(thr)
    dft_gpu = thr.array(image_gpu.shape, dtype=np.complex64)

    times = []
    for _ in range(n_trials):
        start = time.time()
        fft(dft_gpu, image_gpu)
        thr.synchronize()
        times.append(time.time() - start)
    avg_time = np.mean(times)
    print(f"OpenCL (GPU) Avg Time: {avg_time:.4f} seconds")
    return avg_time

if __name__ == "__main__":
    print(f"Testing FFT performance on {SIZE}x{SIZE} matrix (avg of {n_trials} trials)...")
    time_cpu = test_cpu()
    time_gpu = test_gpu_opencl()
    
    if time_gpu is not None:
        speedup = time_cpu / time_gpu
        print(f"\nSpeedup (GPU vs CPU): {speedup:.2f}x")
        if speedup < 1:
            print("GPU 比 CPU 慢，可能原因：")
            print("  1. 数据规模仍不足（尝试进一步增大 SIZE）")
            print("  2. GPU 驱动或硬件性能较弱")
    else:
        print("\nGPU 测试跳过。")