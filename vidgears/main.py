import cv2
from vidgear.gears import CamGear

# 定义RTSP视频流地址
# rtsp_url = "rtsp://stream.strba.sk:1935/strba/VYHLAD_JAZERO.stream"
rtsp_url = "https://wdl.wallstreetcn.com/41aae4d2-390a-48ff-9230-ee865552e72d"

# 设置选项，尝试调整缓冲区大小
options = {"CAP_PROP_BUFFERSIZE": 3}  # 可以根据实际情况调整这个值

# 使用CamGear打开RTSP视频流
stream = CamGear(source=rtsp_url, **options).start()

while True:
    # 读取视频帧
    frame = stream.read()
    if frame is None:
        break

    # 使用OpenCV显示视频帧
    cv2.imshow("RTSP Stream", frame)

    # 按下 'q' 键退出循环
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# 释放资源
cv2.destroyAllWindows()
stream.stop()