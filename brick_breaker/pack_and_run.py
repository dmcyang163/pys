import os
import subprocess

def package_game():
    """
    使用pyinstaller打包游戏脚本，不显示控制台窗口
    """
    try:
        if os.name == 'nt':  # Windows系统
            subprocess.run(['pyinstaller', '--onefile', '--noconsole', 'brick_breaker.py'])
        else:  # 类Unix系统（如Linux、macOS）
            subprocess.run(['pyinstaller', '--onefile', '--windowed', 'brick_breaker.py'])
        print("游戏打包成功！")
    except Exception as e:
        print(f"打包过程中出现错误: {e}")

def run_packaged_game():
    """
    运行打包后的游戏
    """
    if os.name == 'nt':  # Windows系统
        executable_path = os.path.join('dist', 'brick_breaker.exe')
    else:  # 类Unix系统（如Linux、macOS）
        executable_path = os.path.join('dist', 'brick_breaker')

    if os.path.exists(executable_path):
        try:
            subprocess.run([executable_path])
        except Exception as e:
            print(f"运行游戏时出现错误: {e}")
    else:
        print("打包后的可执行文件不存在，请先打包游戏。")

if __name__ == "__main__":
    # 先打包游戏
    package_game()
    # 再运行打包后的游戏
    run_packaged_game()