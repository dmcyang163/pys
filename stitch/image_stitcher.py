import cv2
import os
import numpy as np
from multiprocessing import Pool, cpu_count
from functools import partial
import time

class ImageStitcher:
    """优化后的图像拼接器，支持并行处理和预处理"""
    
    def __init__(self, batch_size=5, workers=None, enable_preprocess=True):
        """
        参数:
            batch_size: 每批处理图像数量
            workers: 并行进程数（默认CPU核心数-1）
            enable_preprocess: 是否启用图像预处理
        """
        self.batch_size = batch_size
        self.workers = workers or max(1, cpu_count() - 1)
        self.enable_preprocess = enable_preprocess

    def stitch_images(self, image_folder):
        """并行分批次拼接图像"""
        image_paths = self._get_sorted_images(image_folder)
        if not image_paths:
            return None

        # 第一阶段：并行处理小批次
        with Pool(self.workers) as pool:
            batch_results = pool.map(
                partial(self._stitch_batch, enable_preprocess=self.enable_preprocess),
                [image_paths[i:i + self.batch_size] 
                 for i in range(0, len(image_paths), self.batch_size)]
            )
        
        # 过滤失败批次
        valid_results = [r for r in batch_results if r is not None]
        if not valid_results:
            return None

        # 第二阶段：合并批次结果
        if len(valid_results) == 1:
            return valid_results[0]
        
        final_result = self._stitch_batch(valid_results, enable_preprocess=False)
        return final_result

    def _stitch_batch(self, image_paths_or_imgs, enable_preprocess=True):
        """处理单个批次（内部方法）"""
        try:
            # 输入可能是路径列表或图像数组
            if isinstance(image_paths_or_imgs[0], str):
                images = [self._preprocess_image(cv2.imread(p)) 
                         for p in image_paths_or_imgs] if enable_preprocess else \
                        [cv2.imread(p) for p in image_paths_or_imgs]
            else:
                images = image_paths_or_imgs

            # 移除加载失败的图像
            images = [img for img in images if img is not None]
            if len(images) < 2:
                return None

            stitcher = cv2.Stitcher.create(cv2.Stitcher_PANORAMA)
            status, panorama = stitcher.stitch(images)
            
            if status == cv2.STITCHER_OK:
                return panorama
            else:
                print(f"拼接失败，错误码: {status}")
                return None
        except Exception as e:
            print(f"批次处理异常: {str(e)}")
            return None

    def _preprocess_image(self, img):
        """图像预处理加速拼接"""
        if img is None:
            return None
            
        # 1. 降分辨率（保持宽高比）
        h, w = img.shape[:2]
        scale = min(1.0, 2000 / max(h, w))  # 限制长边不超过2000px
        if scale < 1.0:
            img = cv2.resize(img, (int(w * scale), int(h * scale)))
        
        # 2. 增强对比度（CLAHE）
        lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        l = clahe.apply(l)
        img = cv2.cvtColor(cv2.merge((l, a, b)), cv2.COLOR_LAB2BGR)
        
        return img

    def _get_sorted_images(self, folder):
        """获取排序后的图像路径列表"""
        valid_exts = {'.jpg', '.jpeg', '.png', '.bmp'}
        paths = []
        for f in sorted(os.listdir(folder)):
            ext = os.path.splitext(f)[1].lower()
            if ext in valid_exts:
                paths.append(os.path.join(folder, f))
        return paths