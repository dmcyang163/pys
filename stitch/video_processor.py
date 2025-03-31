import cv2
import exifread
import os
import shutil
import av
import logging
from typing import List

class VideoProcessor:
    """Handles video file processing including metadata extraction and frame extraction"""
    
    def __init__(self, video_path):
        self.video_path = video_path
        self.container = av.open(video_path)
        self.video_stream = self.container.streams.video[0]
    
    def print_metadata(self):
        """Print detailed video metadata"""
        print("\n视频元数据信息:")
        print("=" * 40)
        
        print(f"文件格式: {self.container.format.name.upper()}")
        print(f"视频编码: {self.video_stream.codec_context.codec.long_name}")
        print(f"分辨率: {self.video_stream.width}x{self.video_stream.height}")
        print(f"帧率: {self.video_stream.average_rate:.2f} fps")
        print(f"时长: {self.video_stream.duration * self.video_stream.time_base:.2f} 秒")
        print(f"总帧数: {self.video_stream.frames}")
        print(f"像素格式: {self.video_stream.codec_context.pix_fmt}")
        
        cap = cv2.VideoCapture(self.video_path)
        print("\nOpenCV补充信息:")
        print(f"是否可读: {cap.isOpened()}")
        print(f"CV_CAP_PROP_FOURCC: {int(cap.get(cv2.CAP_PROP_FOURCC))}")
        cap.release()
        print("=" * 40 + "\n")
    
    def extract_frames(self, output_folder: str, frame_types: List[str] = ['I']) -> int:
        """
        提取指定类型的视频帧（I帧/P帧）并按解码顺序保存
        
        参数:
            output_folder: 输出文件夹路径
            frame_types: 要提取的帧类型列表，可选 'I' 和 'P'
        
        返回:
            提取的帧总数
        """
        # 检查文件夹是否存在
        if os.path.exists(output_folder):
            # 如果存在，删除整个文件夹，创建新的文件夹
            shutil.rmtree(output_folder)
            os.makedirs(output_folder)
        
        frame_count = 0
        
        try:
            for packet in self.container.demux(video=0):
                for frame in packet.decode():
                    frame_type = self._get_frame_type(frame)
                    
                    if frame_type in frame_types:
                        img = frame.to_ndarray(format='bgr24')
                        frame_name = f"{output_folder}/frame_{frame_count:04d}_{frame_type}.jpg"
                        
                        cv2.imwrite(frame_name, img, [int(cv2.IMWRITE_JPEG_QUALITY), 95])
                        img = self._process_image_rotation(frame_name, img)
                        
                        # 额外旋转（根据需求调整）
                        img = cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)
                        cv2.imwrite(frame_name, img)
                        
                        frame_count += 1
                        logging.info(f"已提取 {frame_type}帧: {frame_name}")
        
        except Exception as e:
            logging.error(f"提取帧时发生错误: {str(e)}")
            raise
        
        logging.info(f"\n共提取 {frame_count} 帧（{'、'.join(frame_types)}帧）")
        return frame_count

    def _get_frame_type(self, frame) -> str:
        """获取帧类型（兼容所有PyAV版本）"""
        try:
            # 方法1: 检查整数类型的pict_type (PyAV 10.0.0+)
            if hasattr(frame, 'pict_type') and isinstance(frame.pict_type, int):
                if frame.key_frame:
                    return 'I'
                elif frame.pict_type == 2:  # P帧
                    return 'P'
                elif frame.pict_type == 3:  # B帧
                    return 'B'
                return 'U'
            
            # 方法2: 检查旧版PyAV的pict_type.name
            if hasattr(frame, 'pict_type') and hasattr(frame.pict_type, 'name'):
                if frame.key_frame:
                    return 'I'
                elif frame.pict_type.name == 'P':
                    return 'P'
                elif frame.pict_type.name == 'B':
                    return 'B'
                return 'U'
            
            # 方法3: 仅使用key_frame判断
            if frame.key_frame:
                return 'I'
            return 'P'  # 默认非关键帧视为P帧
            
        except Exception as e:
            logging.warning(f"帧类型判断失败: {str(e)}")
            return 'U'

    def _process_image_rotation(self, frame_path: str, img):
        """处理EXIF旋转信息"""
        try:
            with open(frame_path, 'rb') as f:
                tags = exifread.process_file(f)
                if 'Image Orientation' in tags:
                    orientation = tags['Image Orientation'].values[0]
                    if orientation == 3:
                        img = cv2.rotate(img, cv2.ROTATE_180)
                    elif orientation == 6:
                        img = cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)
                    elif orientation == 8:
                        img = cv2.rotate(img, cv2.ROTATE_90_COUNTERCLOCKWISE)
        except Exception as e:
            logging.warning(f"旋转处理失败: {str(e)}")
        return img