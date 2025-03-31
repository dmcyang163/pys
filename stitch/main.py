from video_processor import VideoProcessor
from image_stitcher import ImageStitcher
from utils import show_resized
from ttools.timer import timer, timing  # 始终可行
import cv2
import click

@click.command()
@click.option("--video", "-v", default="IMG_7891.MOV", help="输入视频路径")
@click.option("--frames", "-f", default="extracted_frames", help="帧输出文件夹")
@click.option("--output", "-o", default="panorama_result.jpg", help="全景图输出路径")
@timer  # 使用默认计时器
def main(video, frames, output):
    """从视频生成全景图的工具"""
    try:
        with timing("视频初始化"):
            processor = VideoProcessor(video)
            processor.print_metadata()
        
        with timing("关键帧提取"):
            processor.extract_key_frames(frames)
        
        with timing("图像拼接"):
            stitcher = ImageStitcher(batch_size=5)
            panorama = stitcher.stitch_images(frames)
        
        if panorama is not None:
            cv2.imwrite(output, panorama)
            print(f"结果已保存至 {output}")  # 普通print仍可用
            show_resized(panorama)
    except Exception as e:
        logging.error(f"错误: {e}")  # 错误日志会自动通过timer模块配置输出

if __name__ == "__main__":
    main()