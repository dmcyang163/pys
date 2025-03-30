import cv2
import exifread
import os
import av

class VideoProcessor:
    """Handles video file processing including metadata extraction and keyframe extraction"""
    
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
        
        # OpenCV backup info
        cap = cv2.VideoCapture(self.video_path)
        print("\nOpenCV补充信息:")
        print(f"是否可读: {cap.isOpened()}")
        print(f"CV_CAP_PROP_FOURCC: {int(cap.get(cv2.CAP_PROP_FOURCC))}")
        cap.release()
        print("=" * 40 + "\n")
    
    def extract_key_frames(self, output_folder):
        """
        Extract key frames from video and handle rotation
        Returns the number of extracted frames
        """
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
        
        keyframe_count = 0
        
        for frame in self.container.decode(video=0):
            if frame.key_frame:
                img = frame.to_ndarray(format='bgr24')
                frame_name = f"{output_folder}/frame_{keyframe_count:04d}.jpg"
                
                cv2.imwrite(frame_name, img, [int(cv2.IMWRITE_JPEG_QUALITY), 95])
                
                # Handle EXIF orientation
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
                
                # Additional rotation if needed
                img = cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)
                cv2.imwrite(frame_name, img)
                keyframe_count += 1
        
        print(f"提取了 {keyframe_count} 个关键帧")
        return keyframe_count