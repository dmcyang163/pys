import sys
import os
import inspect

def get_resource_path(relative_path):
    """获取资源的绝对路径"""
    if getattr(sys, 'frozen', False):
        # 如果是打包后的可执行文件
        base_path = sys._MEIPASS
    else:
        # 如果是普通脚本
        # 获取调用者的文件路径
        caller_frame = inspect.stack()[1]
        own_file_path = caller_frame.filename
        base_path = os.path.dirname(os.path.abspath(own_file_path))
    return os.path.join(base_path, relative_path)