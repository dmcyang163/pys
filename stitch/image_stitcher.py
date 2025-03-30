import cv2
import os

class ImageStitcher:
    """Handles stitching of images into panoramas"""
    
    def __init__(self, batch_size=5):
        self.batch_size = batch_size
    
    def stitch_images(self, image_folder):
        """Stitch images in batches from the specified folder"""
        image_paths = sorted([os.path.join(image_folder, f) for f in os.listdir(image_folder)])
        batch_results = []
        
        for i in range(0, len(image_paths), self.batch_size):
            batch_images = [cv2.imread(p) for p in image_paths[i:i+self.batch_size]]
            stitcher = cv2.Stitcher.create()
            status, result = stitcher.stitch(batch_images)
            
            if status == cv2.STITCHER_OK:
                batch_results.append(result)
            else:
                print(f"警告：批次 {i//self.batch_size+1} 拼接失败，已跳过")
        
        if not batch_results:
            return None
        
        if len(batch_results) == 1:
            return batch_results[0]
        
        final_stitcher = cv2.Stitcher.create()
        status, panorama = final_stitcher.stitch(batch_results)
        return panorama if status == cv2.STITCHER_OK else batch_results[-1]