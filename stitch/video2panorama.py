import cv2
import exifread
import os
import av
from pprint import pprint
try:
    import pyautogui
    SCREEN_WIDTH, SCREEN_HEIGHT = pyautogui.size()
except:
    SCREEN_WIDTH, SCREEN_HEIGHT = 1920, 1080

def print_video_metadata(video_path):
    """打印视频的主要元数据"""
    print("\n视频元数据信息:")
    print("=" * 40)
    
    # 方法1：使用PyAV获取详细元数据
    container = av.open(video_path)
    stream = container.streams.video[0]
    
    print(f"文件格式: {container.format.name.upper()}")
    print(f"视频编码: {stream.codec_context.codec.long_name}")
    print(f"分辨率: {stream.width}x{stream.height}")
    print(f"帧率: {stream.average_rate:.2f} fps")
    print(f"时长: {stream.duration * stream.time_base:.2f} 秒")
    print(f"总帧数: {stream.frames}")
    print(f"像素格式: {stream.codec_context.pix_fmt}")
    
    # 方法2：使用OpenCV获取基础信息（备用）
    cap = cv2.VideoCapture(video_path)
    print("\nOpenCV补充信息:")
    print(f"是否可读: {cap.isOpened()}")
    print(f"CV_CAP_PROP_FOURCC: {int(cap.get(cv2.CAP_PROP_FOURCC))}")
    cap.release()
    print("=" * 40 + "\n")

def extract_key_frames(video_path, frame_folder):
    """提取关键帧并处理旋转"""
    if not os.path.exists(frame_folder):
        os.makedirs(frame_folder)
    
    container = av.open(video_path)
    keyframe_count = 0
    
    for frame in container.decode(video=0):
        if frame.key_frame:
            img = frame.to_ndarray(format='bgr24')
            frame_name = f"{frame_folder}/frame_{keyframe_count:04d}.jpg"
            
            cv2.imwrite(frame_name, img, [int(cv2.IMWRITE_JPEG_QUALITY), 95])
            
            with open(frame_name, 'rb') as f:
                tags = exifread.process_file(f)
                if 'Image Orientation' in tags:
                    orientation = tags['Image Orientation'].values[0]
                    if orientation == 3:
                        img = cv2.rotate(img, cv2.ROTATE_180)
                    elif orientation == 6:
                        img = cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)
                    elif orientation == 8:
                        img = cv2.rotate(img, cv2.ROTATE_90_COUNTERCLOCKWISE)
            
            img = cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)
            cv2.imwrite(frame_name, img)
            keyframe_count += 1
    
    print(f"提取了 {keyframe_count} 个关键帧")

def stitch_frames_in_batches(image_folder, batch_size=5):
    """分批次拼接图像"""
    image_paths = sorted([os.path.join(image_folder, f) for f in os.listdir(image_folder)])
    batch_results = []
    
    for i in range(0, len(image_paths), batch_size):
        batch_images = [cv2.imread(p) for p in image_paths[i:i+batch_size]]
        stitcher = cv2.Stitcher.create()
        status, result = stitcher.stitch(batch_images)
        
        if status == cv2.STITCHER_OK:
            batch_results.append(result)
        else:
            print(f"警告：批次 {i//batch_size+1} 拼接失败，已跳过")
    
    if not batch_results:
        return None
    
    if len(batch_results) == 1:
        return batch_results[0]
    
    final_stitcher = cv2.Stitcher.create()
    status, panorama = final_stitcher.stitch(batch_results)
    return panorama if status == cv2.STITCHER_OK else batch_results[-1]

def show_resized(image, window_name="Panorama", max_ratio=0.8):
    """自适应屏幕大小的图像显示"""
    h, w = image.shape[:2]
    max_w = int(SCREEN_WIDTH * max_ratio)
    max_h = int(SCREEN_HEIGHT * max_ratio)
    
    scale = min(max_w/w, max_h/h)
    if scale < 1:
        image = cv2.resize(image, (int(w*scale), int(h*scale)))
    
    cv2.imshow(window_name, image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

if __name__ == "__main__":
    VIDEO_PATH = "IMG_7891.MOV"
    FRAME_FOLDER = "extracted_frames"
    OUTPUT_PANO = "panorama_result.jpg"
    
    # 打印视频元数据
    print_video_metadata(VIDEO_PATH)
    
    # 处理流程
    extract_key_frames(VIDEO_PATH, FRAME_FOLDER)
    panorama = stitch_frames_in_batches(FRAME_FOLDER)
    
    if panorama is not None:
        cv2.imwrite(OUTPUT_PANO, panorama)
        print(f"全景图已保存至 {OUTPUT_PANO}")
        show_resized(panorama)
    else:
        print("拼接失败：请检查视频内容或调整批次大小")