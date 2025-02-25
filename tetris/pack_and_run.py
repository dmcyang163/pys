import argparse
import os
import subprocess
import shutil
import sys

def create_output_dir(base_dir, packer):
    """创建输出目录"""
    output_dir = os.path.join(base_dir, "output")
    packer_output_dir = os.path.join(output_dir, packer)
    os.makedirs(packer_output_dir, exist_ok=True)
    return packer_output_dir

def get_virtual_env_path():
    """
    获取当前虚拟环境的路径，如果不在虚拟环境中则返回 None。
    结合使用 VIRTUAL_ENV 环境变量和 sys.prefix/sys.base_prefix。
    """
    # 1. 检查 VIRTUAL_ENV 环境变量
    venv_path = os.environ.get("VIRTUAL_ENV")
    if venv_path and os.path.isdir(venv_path):  # 确保路径存在
        return venv_path

    # 2. 如果 VIRTUAL_ENV 不存在或无效，则使用 sys.prefix/sys.base_prefix
    if sys.prefix != sys.base_prefix:
        return sys.prefix

    # 3. 如果以上两种方法都失败，则返回 None
    return None

def get_nuitka_executable(base_dir):
    """获取 Nuitka 可执行文件路径"""
    venv_path = get_virtual_env_path()  # 使用 get_virtual_env_path() 获取虚拟环境路径
    if venv_path:
        venv_nuitka_path = os.path.join(venv_path, "Scripts", "nuitka.cmd")  # 构建虚拟环境中的 Nuitka 路径
        if os.path.exists(venv_nuitka_path):
            print(f"使用虚拟环境中的 Nuitka: {venv_nuitka_path}")
            return venv_nuitka_path
        else:
            print("虚拟环境中未找到 Nuitka，尝试使用系统 PATH 中的 Nuitka。")

    nuitka_executable = "nuitka"
    if shutil.which(nuitka_executable) is None:
        print("系统 PATH 中也未找到 Nuitka，请确保已安装并添加到 PATH。")
        return None
    return nuitka_executable

def build_pyinstaller_command(script_name, output_dir, add_data, onefile, upx_dir):
    """构建 PyInstaller 打包命令"""
    command = [
        "pyinstaller",
        "--noconsole",
        f"--distpath={output_dir}",
        f"--workpath={os.path.join(output_dir, 'build')}",
        "--clean"
    ]

    if onefile:
        command.append("--onefile")

    for data in add_data:
        command.append(f"--add-data={data}")

    if upx_dir:
        command.append(f"--upx-dir={upx_dir}")

    command.append(script_name)
    return command

def build_nuitka_command(script_name, output_dir, add_data, onefile):
    """构建 Nuitka 打包命令"""
    script_name_without_ext = os.path.splitext(os.path.basename(script_name))[0]
    exe_name = script_name_without_ext + ".exe"
    command = [
        "--standalone",
        "--windows-console-mode=disable",  # 使用新选项
        "--follow-imports",
        f"--output-filename={exe_name}",
        f"--output-dir={output_dir}",
    ]

    if onefile:
        command.append("--onefile")

    for data in add_data:
        source, dest = data.split(os.pathsep)
        command.append(f"--include-data-dir={source}={dest}")

    command.append(script_name)
    return command

def test_upx_compression(upx_dir, exe_path):
    """测试文件是否可以被 UPX 压缩"""
    test_command = [os.path.join(upx_dir, "upx"), "-t", exe_path]
    try:
        subprocess.run(test_command, check=True)
        print(f"文件可以被 UPX 压缩: {exe_path}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"文件无法被 UPX 压缩: {e}")
        return False

def is_already_compressed(upx_dir, exe_path):
    """检查文件是否已经被 UPX 压缩"""
    info_command = [os.path.join(upx_dir, "upx"), "-l", exe_path]
    try:
        result = subprocess.run(info_command, capture_output=True, text=True, check=True)
        return "compressed" in result.stdout
    except subprocess.CalledProcessError:
        return False

def compress_with_upx(upx_dir, exe_path):
    """使用 UPX 压缩可执行文件"""
    if is_already_compressed(upx_dir, exe_path):
        print(f"文件已经被 UPX 压缩: {exe_path}")
        return  # 如果文件已经被压缩，直接返回

    if not test_upx_compression(upx_dir, exe_path):
        return  # 如果文件无法被压缩，直接返回

    upx_command = [os.path.join(upx_dir, "upx"), "--best", exe_path]
    try:
        subprocess.run(upx_command, check=True)
        print(f"UPX 压缩成功: {exe_path}")
    except subprocess.CalledProcessError as e:
        print(f"UPX 压缩失败: {e}")
    except FileNotFoundError:
        print(f"未找到 UPX 工具，请确保 UPX 已安装并路径正确: {upx_dir}")

def _package_with_pyinstaller(script_name, output_dir, add_data, onefile, upx_dir):
    """使用 PyInstaller 打包"""
    command = build_pyinstaller_command(script_name, output_dir, add_data, onefile, upx_dir)
    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as e:
        print(f"PyInstaller 打包失败: {e}")
        return False
    return True

def _package_with_nuitka(script_name, output_dir, add_data, onefile, upx_dir):
    """使用 Nuitka 打包"""
    nuitka_executable = get_nuitka_executable(os.path.dirname(os.path.abspath(script_name)))
    if not nuitka_executable:
        return False  # 如果找不到 Nuitka，退出函数

    command = [nuitka_executable] + build_nuitka_command(script_name, output_dir, add_data, onefile)
    try:
        subprocess.run(command, check=True, cwd=os.path.dirname(os.path.abspath(script_name)))

        # Nuitka 打包完成后，调用 UPX 压缩
        if upx_dir:
            script_name_without_ext = os.path.splitext(os.path.basename(script_name))[0]
            exe_name = script_name_without_ext + ".exe"
            exe_path = os.path.join(output_dir, exe_name)
            compress_with_upx(upx_dir, exe_path)

    except subprocess.CalledProcessError as e:
        print(f"Nuitka 打包失败: {e}")
        return False
    return True

def package_game(script_name, packer='pyinstaller', upx_dir=None, onefile=False, data_dir=None):
    """
    使用 pyinstaller 或 Nuitka 打包游戏脚本，并包含 data_dir 目录下的文件，并使用 UPX 压缩。

    参数:
        script_name (str): 游戏脚本的文件名。
        packer (str): 打包工具，可以是 'pyinstaller' 或 'nuitka'，默认为 'pyinstaller'。
        upx_dir (str): UPX 压缩工具的目录路径，可选。  仅用于 PyInstaller。
        onefile (bool): 是否使用 Onefile 模式，默认为 False。
        data_dir (str): 资源文件所在的目录，可选。
    """
    base_dir = os.path.dirname(os.path.abspath(script_name))  # 脚本所在的目录
    add_data = []

    if data_dir:
        # 遍历 data_dir 目录下的所有文件和子目录
        for item in os.listdir(data_dir):
            source_path = os.path.join(data_dir, item)
            dest_path = item  # 打包后的目标路径为 item，保持目录结构
            add_data.append(f"{source_path}{os.pathsep}{dest_path}")

    if packer == 'pyinstaller':
        output_dir = create_output_dir(base_dir, "pyinstaller")
        _package_with_pyinstaller(script_name, output_dir, add_data, onefile, upx_dir)

    elif packer == 'nuitka':
        output_dir = create_output_dir(base_dir, "nuitka")
        if onefile:
            if not _package_with_nuitka(script_name, output_dir, add_data, True, upx_dir):
                print("Nuitka Onefile 打包失败，尝试不用 Onefile 模式重新打包...")
                _package_with_nuitka(script_name, output_dir, add_data, False, upx_dir)
        else:
            _package_with_nuitka(script_name, output_dir, add_data, False, upx_dir)

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

    script_name_without_ext = os.path.splitext(os.path.basename(script_name))[0]
    exe_name = script_name_without_ext + ".exe"

    if packer == 'pyinstaller':
        pyinstaller_output_dir = os.path.join(output_dir, "pyinstaller")
        if onefile:
            exe_path = os.path.join(pyinstaller_output_dir, exe_name)
        else:
            # 修改为在 dist 目录中查找可执行文件
            dist_dir = os.path.join(pyinstaller_output_dir, script_name_without_ext)
            exe_path = os.path.join(dist_dir, exe_name)
    elif packer == 'nuitka':
        nuitka_output_dir = os.path.join(output_dir, "nuitka")
        # 优先查找 onefile 模式的 exe，如果不存在，则查找非 onefile 模式的 exe
        if onefile:
            exe_path = os.path.join(nuitka_output_dir, exe_name)
            if not os.path.exists(exe_path):
                print("Onefile 模式打包的可执行文件不存在，尝试查找非 Onefile 模式的可执行文件...")
                onefile = False # 切换到非 onefile 模式
        if not onefile:
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

def parse_arguments():
    """
    解析命令行参数。

    返回:
        argparse.Namespace: 包含解析后的参数的对象。
    """
    parser = argparse.ArgumentParser(description="使用 PyInstaller 或 Nuitka 打包 Python 游戏。")
    parser.add_argument("script_name", help="游戏脚本的文件名")
    parser.add_argument(
        "--packer",
        choices=['pyinstaller', 'nuitka'],
        default='pyinstaller',
        help="选择打包工具 (pyinstaller 或 nuitka)"
    )
    parser.add_argument(
        "--upx_dir",
        help="UPX 压缩工具的目录 (可选)"
    )
    parser.add_argument(
        "--onefile",
        action="store_true",
        help="使用 Onefile 模式 (可选)"
    )
    parser.add_argument(
        "--args_to_pass",
        nargs='*',
        help="传递给可执行文件的参数 (可选)"
    )
    parser.add_argument(
        "--data_dir",
        help="资源文件所在的目录 (可选)"
    )
    return parser.parse_args()

if __name__ == "__main__":
    # 解析命令行参数
    args = parse_arguments()

    # 提取参数值并传递给函数
    script_name = args.script_name
    packer = args.packer
    upx_dir = args.upx_dir
    onefile = args.onefile
    args_to_pass = args.args_to_pass
    data_dir = args.data_dir

    # 先打包游戏
    package_game(script_name, packer, upx_dir, onefile=onefile, data_dir=data_dir)

    # 再运行打包后的游戏
    run_packaged_game(script_name, packer, args_to_pass, onefile=onefile)
