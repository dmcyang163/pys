from video_processor import VideoProcessor
from image_stitcher import ImageStitcher
from utils import show_resized
import cv2

if __name__ == "__main__":
    VIDEO_PATH = "IMG_7891.MOV"
    FRAME_FOLDER = "extracted_frames"
    OUTPUT_PANO = "panorama_result.jpg"
    
    # Process video
    video_processor = VideoProcessor(VIDEO_PATH)
    video_processor.print_metadata()
    video_processor.extract_key_frames(FRAME_FOLDER)
    
    # Stitch images
    stitcher = ImageStitcher(batch_size=5)
    panorama = stitcher.stitch_images(FRAME_FOLDER)
    
    if panorama is not None:
        cv2.imwrite(OUTPUT_PANO, panorama)
        print(f"全景图已保存至 {OUTPUT_PANO}")
        show_resized(panorama)
    else:
        print("拼接失败：请检查视频内容或调整批次大小")