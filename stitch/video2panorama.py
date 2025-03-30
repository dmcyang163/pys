import cv2
import exifread
import os
import av
import pyautogui  # 用于获取屏幕尺寸

def extract_key_frames(video_path, frame_folder):
    """（与原有代码保持一致）"""
    if not os.path.exists(frame_folder):
        os.makedirs(frame_folder)
    container = av.open(video_path)
    keyframe_count = 0
    for frame in container.decode(video=0):
        if frame.key_frame:
            img = frame.to_ndarray(format='bgr24')
            frame_name = f"{frame_folder}/frame_{keyframe_count:04d}.jpg"
            cv2.imwrite(frame_name, img)
            with open(frame_name, 'rb') as f:
                tags = exifread.process_file(f)
                orientation = tags.get('Image Orientation')
                if orientation:
                    orientation = int(str(orientation.values[0]))
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
    """（与原有代码保持一致）"""
    image_files = sorted(os.listdir(image_folder))
    image_paths = [os.path.join(image_folder, f) for f in image_files]
    batch_results = []
    for i in range(0, len(image_paths), batch_size):
        batch_paths = image_paths[i:i + batch_size]
        batch_images = [cv2.imread(path) for path in batch_paths]
        stitcher = cv2.Stitcher.create()
        status, batch_result = stitcher.stitch(batch_images)
        if status == cv2.STITCHER_OK:
            batch_results.append(batch_result)
        else:
            print(f'Error: 第 {i // batch_size + 1} 批图像拼接失败！跳过当前批次。')
            continue
    if len(batch_results) > 1:
        stitcher = cv2.Stitcher.create()
        status, final_result = stitcher.stitch(batch_results)
        if status == cv2.STITCHER_OK:
            return final_result
        else:
            print('Error: 最终拼接失败！返回最后一个成功批次。')
            return batch_results[-1]
    elif len(batch_results) == 1:
        return batch_results[0]
    else:
        return None

def show_image_resized(img, window_name='Image', max_screen_ratio=0.8):
    """
    调整图像窗口大小，使其不超过屏幕的80%
    :param img: 要显示的图像
    :param window_name: 窗口名称
    :param max_screen_ratio: 最大屏幕占比（0.8表示80%）
    """
    try:
        # 使用pyautogui获取屏幕尺寸
        screen_width, screen_height = pyautogui.size()
    except:
        # 如果pyautogui不可用，使用默认值
        screen_width, screen_height = 1920, 1080
    
    # 计算最大允许尺寸
    max_width = int(screen_width * max_screen_ratio)
    max_height = int(screen_height * max_screen_ratio)
    
    # 获取图像尺寸
    img_height, img_width = img.shape[:2]
    
    # 计算缩放比例
    scale = min(max_width / img_width, max_height / img_height)
    if scale < 1:  # 仅在需要缩小时调整
        new_width = int(img_width * scale)
        new_height = int(img_height * scale)
        img = cv2.resize(img, (new_width, new_height))
    
    # 显示图像
    cv2.imshow(window_name, img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

if __name__ == "__main__":
    video_path = "IMG_7891.MOV"
    frame_folder = "keyframes"

    # 1. 提取关键帧
    extract_key_frames(video_path, frame_folder)

    # 2. 分批次拼接
    panorama = stitch_frames_in_batches(frame_folder)

    if panorama is not None:
        cv2.imwrite("panorama_keyframes.jpg", panorama)
        # 显示图像（限制为屏幕的80%大小）
        show_image_resized(panorama, 'Panorama (Keyframes)')
    else:
        print("拼接失败：请检查关键帧是否足够或重叠区域是否明显。")