import os
import subprocess
import argparse

def package_game(script_name):
    """
    使用pyinstaller打包游戏脚本，不显示控制台窗口，并包含 sounds, fonts, textures 文件夹
    :param script_name: 游戏脚本的文件名 (例如: my_game.py)
    """
    try:
        base_name, ext = os.path.splitext(script_name)  # 分离文件名和扩展名
        
        # 构建 add-data 参数
        add_data = []
        add_data.append("sounds:sounds")
        add_data.append("fonts:fonts")
        add_data.append("textures:textures")

        # 构建 pyinstaller 命令
        if os.name == 'nt':  # Windows系统
            command = ['pyinstaller', '--onefile', '--noconsole']
        else:  # 类Unix系统（如Linux、macOS）
            command = ['pyinstaller', '--onefile', '--windowed']

        for data in add_data:
            command.extend(['--add-data', data])

        command.append(script_name)

        subprocess.run(command)
        print(f"{script_name} 打包成功！")
    except Exception as e:
        print(f"打包 {script_name} 过程中出现错误: {e}")

def run_packaged_game(script_name):
    """
    运行打包后的游戏
    :param script_name: 游戏脚本的文件名 (例如: my_game.py)
    """
    base_name, ext = os.path.splitext(script_name)  # 分离文件名和扩展名
    if os.name == 'nt':  # Windows系统
        executable_path = os.path.join('dist', base_name + '.exe')
    else:  # 类Unix系统（如Linux、macOS）
        executable_path = os.path.join('dist', base_name)

    if os.path.exists(executable_path):
        try:
            subprocess.run([executable_path])
        except Exception as e:
            print(f"运行 {executable_path} 时出现错误: {e}")
    else:
        print(f"打包后的可执行文件 {executable_path} 不存在，请先打包游戏。")

if __name__ == "__main__":
    # 创建 ArgumentParser 对象
    parser = argparse.ArgumentParser(description="打包和运行游戏脚本")

    # 添加 script_name 参数
    parser.add_argument("script_name", help="游戏脚本的文件名 (例如: my_game.py)")

    # 解析命令行参数
    args = parser.parse_args()

    # 获取游戏脚本的文件名
    game_script = args.script_name

    # 先打包游戏
    package_game(game_script)
    # 再运行打包后的游戏
    run_packaged_game(game_script)
