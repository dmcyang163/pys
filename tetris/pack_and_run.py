import os
import subprocess
import argparse
import shutil

def package_game(script_name, packer='pyinstaller', upx_dir=None, onefile=False):
    """
    使用 pyinstaller 或 Nuitka 打包游戏脚本，并包含 sounds, fonts, textures 文件夹，并使用 UPX 压缩。

    参数:
        script_name (str): 游戏脚本的文件名。
        packer (str): 打包工具，可以是 'pyinstaller' 或 'nuitka'，默认为 'pyinstaller'。
        upx_dir (str): UPX 压缩工具的目录路径，可选。  仅用于 PyInstaller。
        onefile (bool): 是否使用 Onefile 模式，默认为 False。
    """
    base_dir = os.path.dirname(os.path.abspath(script_name))  # 脚本所在的目录
    output_dir = os.path.join(base_dir, "output") # 创建一个名为 output 的目录用于存放打包结果
    os.makedirs(output_dir, exist_ok=True) # 确保 output 目录存在

    add_data = []
    add_data.append(f"sounds{os.pathsep}sounds")
    add_data.append(f"fonts{os.pathsep}fonts")
    add_data.append(f"textures{os.pathsep}textures")

    if packer == 'pyinstaller':
        pyinstaller_output_dir = os.path.join(output_dir, "pyinstaller") # pyinstaller 的输出目录
        os.makedirs(pyinstaller_output_dir, exist_ok=True) # 确保目录存在

        command = [
            "pyinstaller",
            "--noconsole",
            f"--distpath={pyinstaller_output_dir}", # 指定输出目录
            f"--workpath={os.path.join(pyinstaller_output_dir, 'build')}", # 指定临时文件目录
            "--clean" # 添加 --clean 选项
        ]

        if onefile:
            command.append("--onefile")

        for data in add_data:
            command.append(f"--add-data={data}")

        command.append(script_name)

        if upx_dir:
            #command.append(f"--upx-dir={upx_dir}") # 暂时禁用 UPX 压缩
            pass
        try:
            subprocess.run(command, check=True)
        except subprocess.CalledProcessError as e:
            print(f"PyInstaller 打包失败: {e}")

    elif packer == 'nuitka':
        nuitka_output_dir = os.path.join(output_dir, "nuitka") # nuitka 的输出目录
        os.makedirs(nuitka_output_dir, exist_ok=True) # 确保目录存在

        # 查找虚拟环境中的 nuitka.cmd
        nuitka_executable = None
        venv_path = os.path.join(os.path.dirname(base_dir), ".venv", "Scripts", "nuitka.cmd")
        if os.path.exists(venv_path):
            nuitka_executable = venv_path
            print(f"使用虚拟环境中的 Nuitka: {nuitka_executable}")
        else:
            nuitka_executable = "nuitka"  # 假设在 PATH 中
            if shutil.which(nuitka_executable) is None:
                print("系统 PATH 中也未找到 Nuitka，请确保已安装并添加到 PATH。请检查 Nuitka 是否已安装并添加到系统环境变量 PATH 中。")
                return  # 退出函数，因为找不到 Nuitka

        command = [
            nuitka_executable,
            "--standalone",
            "--disable-console",
            "--follow-imports",
            f"--output-filename=tetris.exe", # 指定输出文件名
            f"--output-dir={nuitka_output_dir}", # 指定输出目录
        ]

        if onefile:
            command.append("--onefile")

        for data in add_data:
            source, dest = data.split(os.pathsep)
            command.append(f"--include-data-dir={source}={dest}")

        command.append(script_name)
        try:
            subprocess.run(command, check=True, cwd=base_dir)

        except subprocess.CalledProcessError as e:
            print(f"Nuitka 打包失败: {e}")
    else:
        print("无效的打包工具，请选择 'pyinstaller' 或 'nuitka'。")

def run_packaged_game(script_name, packer='pyinstaller', args_to_pass=None, onefile=False):
    """
    运行打包后的游戏。

    参数:
        script_name (str): 游戏脚本的文件名。
        packer (str): 打包工具，可以是 'pyinstaller' 或 'nuitka'，默认为 'pyinstaller'。
        args_to_pass (list): 传递给可执行文件的参数列表，默认为 None。
        onefile (bool): 是否使用 Onefile 模式，默认为 False。
    """
    base_dir = os.path.dirname(os.path.abspath(script_name))
    output_dir = os.path.join(base_dir, "output")

    if packer == 'pyinstaller':
        pyinstaller_output_dir = os.path.join(output_dir, "pyinstaller")
        exe_name = os.path.splitext(os.path.basename(script_name))[0] + ".exe"
        if onefile:
            exe_path = os.path.join(pyinstaller_output_dir, exe_name)
        else:
            # 修改为在 dist 目录中查找可执行文件
            dist_dir = os.path.join(pyinstaller_output_dir, os.path.splitext(os.path.basename(script_name))[0])
            exe_path = os.path.join(dist_dir, exe_name)
    elif packer == 'nuitka':
        nuitka_output_dir = os.path.join(output_dir, "nuitka")
        exe_name = "tetris.exe" # Nuitka output name is fixed
        if onefile:
            exe_path = os.path.join(nuitka_output_dir, exe_name)
        else:
            script_name_without_ext = os.path.splitext(os.path.basename(script_name))[0]
            dist_dir = os.path.join(nuitka_output_dir, f"{script_name_without_ext}.dist") # Nuitka 默认在 <script_name>.dist 目录生成可执行文件
            exe_path = os.path.join(dist_dir, exe_name)
    else:
        print("无效的打包工具，请选择 'pyinstaller' 或 'nuitka'。")
        return

    if os.path.exists(exe_path):
        command = [exe_path]
        if args_to_pass:
            command.extend(args_to_pass)
        try:
            subprocess.run(command, check=True)
        except subprocess.CalledProcessError as e:
            print(f"运行打包后的游戏失败: {e}")
    else:
        print(f"找不到打包后的游戏: {exe_path}，请先打包游戏。")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="使用 PyInstaller 或 Nuitka 打包 Python 游戏。")
    parser.add_argument("script_name", help="游戏脚本的文件名")
    parser.add_argument("--packer", choices=['pyinstaller', 'nuitka'], default='pyinstaller', help="选择打包工具 (pyinstaller 或 nuitka)")
    parser.add_argument("--upx_dir", help="UPX 压缩工具的目录 (可选)")
    parser.add_argument("--onefile", action="store_true", help="使用 Onefile 模式 (可选)")
    parser.add_argument("--args_to_pass", nargs='*', help="传递给可执行文件的参数 (可选)")
    #parser.add_argument("--nuitka_python_binary", help="Nuitka 特定的 Python 解释器可执行文件路径 (可选)") # 不再使用
    args = parser.parse_args()

    # 先打包游戏
    package_game(args.script_name, args.packer, args.upx_dir, onefile=args.onefile) # 不再传递 nuitka_python_binary

    # 再运行打包后的游戏
    run_packaged_game(args.script_name, args.packer, args.args_to_pass, onefile=args.onefile)
