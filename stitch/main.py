from video_processor import VideoProcessor
from image_stitcher import ImageStitcher
from utils import show_resized
import cv2
import click

@click.command()
@click.option(
    "--video", "-v",
    default="IMG_7891.MOV",
    type=click.Path(exists=True),
    help="输入视频文件路径（默认：IMG_7891.MOV）"
)
@click.option(
    "--frames", "-f",
    default="extracted_frames",
    type=click.Path(),
    help="提取帧的输出文件夹（默认：extracted_frames）"
)
@click.option(
    "--output", "-o",
    default="panorama_result.jpg",
    type=click.Path(),
    help="全景图输出路径（默认：panorama_result.jpg）"
)
@click.option(
    "--batch-size", "-b",
    default=5,
    type=int,
    help="图像拼接的批次大小（默认：5）"
)
def main(video, frames, output, batch_size):
    """从视频生成全景图的工具"""
    
    # 处理视频
    try:
        video_processor = VideoProcessor(video)
        video_processor.print_metadata()
        video_processor.extract_key_frames(frames)
        
        # 拼接图像
        stitcher = ImageStitcher(batch_size=batch_size)
        panorama = stitcher.stitch_images(frames)
        
        if panorama is not None:
            cv2.imwrite(output, panorama)
            click.echo(f"全景图已保存至 {click.style(output, fg='green')}")
            show_resized(panorama)
        else:
            click.echo(click.style("拼接失败：请检查视频内容或调整批次大小", fg="red"))
    except Exception as e:
        click.echo(click.style(f"错误发生：{str(e)}", fg="red"), err=True)

if __name__ == "__main__":
    main()