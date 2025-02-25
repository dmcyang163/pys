import argparse
import os
import subprocess
import shutil
import platform
import sys
import logging
import shlex
from concurrent.futures import ProcessPoolExecutor

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def create_output_dir(base_dir, packer):
    """创建输出目录."""
    output_dir = os.path.join(base_dir, "output")
    packer_output_dir = os.path.join(output_dir, packer)
    os.makedirs(packer_output_dir, exist_ok=True)
    return packer_output_dir


def get_virtual_env_path():
    """获取虚拟环境路径，如果不在虚拟环境中则返回 None."""
    venv_path = os.environ.get("VIRTUAL_ENV")
    if venv_path and os.path.isdir(venv_path):
        return venv_path
    if getattr(sys, 'base_prefix', sys.prefix) != sys.prefix:
        return sys.prefix
    return None


def get_nuitka_executable(base_dir):
    """获取 Nuitka 可执行文件路径."""
    venv_path = get_virtual_env_path()
    if venv_path:
        nuitka_cmd = "nuitka.cmd" if platform.system() == "Windows" else "nuitka"
        venv_nuitka_path = os.path.join(venv_path, "Scripts", nuitka_cmd)
        if os.path.exists(venv_nuitka_path):
            logging.info(f"使用虚拟环境中的 Nuitka: {venv_nuitka_path}")
            return venv_nuitka_path
        else:
            logging.warning("虚拟环境中未找到 Nuitka，尝试使用系统 PATH 中的 Nuitka。")

    nuitka_executable = "nuitka"
    if shutil.which(nuitka_executable) is None:
        logging.error("系统 PATH 中也未找到 Nuitka，请确保已安装并添加到 PATH。")
        return None
    return nuitka_executable


def get_executable_extension():
    """根据操作系统获取可执行文件后缀."""
    return ".exe" if platform.system() == "Windows" else ""


def build_pyinstaller_command(script_names, output_dir, add_data, onefile, upx_dir):
    """构建 PyInstaller 打包命令."""
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
    command.extend(script_names)
    return command


def build_nuitka_command(script_names, output_dir, add_data, onefile):
    """构建 Nuitka 打包命令."""
    # Nuitka 不支持直接指定多个 --output-filename，需要为每个脚本单独打包
    if len(script_names) > 1:
        logging.warning("Nuitka 不支持一次性打包多个脚本，将为每个脚本单独打包。")

    command = [
        "--standalone",
        "--windows-console-mode=disable",
        "--follow-imports",
        f"--output-dir={output_dir}",
    ]
    if onefile:
        command.append("--onefile")

    for data in add_data:
        source, dest = data.split(os.pathsep)
        command.append(f"--include-data-dir={source}={dest}")

    return command


def test_upx_compression(upx_dir, exe_path):
    """测试文件是否可以被 UPX 压缩."""
    test_command = [os.path.join(upx_dir, "upx"), "-t", exe_path]
    try:
        subprocess.run(test_command, check=True)
        logging.info(f"文件可以被 UPX 压缩: {exe_path}")
        return True
    except subprocess.CalledProcessError as e:
        logging.warning(f"文件无法被 UPX 压缩: {e}")
        return False


def is_already_compressed(upx_dir, exe_path):
    """检查文件是否已经被 UPX 压缩."""
    info_command = [os.path.join(upx_dir, "upx"), "-l", exe_path]
    try:
        result = subprocess.run(info_command, capture_output=True, text=True, check=True)
        return "compressed" in result.stdout
    except subprocess.CalledProcessError:
        return False


def compress_with_upx(upx_dir, exe_path):
    """使用 UPX 压缩可执行文件."""
    if is_already_compressed(upx_dir, exe_path):
        logging.info(f"文件已经被 UPX 压缩: {exe_path}")
        return

    if not test_upx_compression(upx_dir, exe_path):
        return

    upx_command = [os.path.join(upx_dir, "upx"), "--best", exe_path]
    try:
        subprocess.run(upx_command, check=True)
        logging.info(f"UPX 压缩成功: {exe_path}")
    except subprocess.CalledProcessError as e:
        logging.error(f"UPX 压缩失败: {e}")
    except FileNotFoundError:
        logging.error(f"未找到 UPX 工具，请确保 UPX 已安装并路径正确: {upx_dir}")


def package(script_names, packer='pyinstaller', upx_dir=None, onefile=False, data_dir=None):
    """使用 pyinstaller 或 Nuitka 打包脚本，并包含资源文件，并使用 UPX 压缩."""
    base_dir = os.path.dirname(os.path.abspath(script_names[0]))
    add_data = prepare_data_files(data_dir)

    output_dir = create_output_dir(base_dir, packer)

    if packer == 'nuitka' and len(script_names) > 1:
        # Nuitka 不支持一次性打包多个脚本，需要为每个脚本单独打包
        for script_name in script_names:
            script_name_without_ext = os.path.splitext(os.path.basename(script_name))[0]
            exe_ext = get_executable_extension()
            exe_name = script_name_without_ext + exe_ext

            nuitka_executable = get_nuitka_executable(os.path.dirname(os.path.abspath(script_name)))
            if not nuitka_executable:
                logging.error("获取 Nuitka 可执行文件失败。")
                return

            command = [nuitka_executable] + build_nuitka_command([script_name], output_dir, add_data, onefile)
            command.extend(["--output-filename", exe_name, script_name])

            try:
                subprocess.run(command, check=True, cwd=os.path.dirname(os.path.abspath(script_name)))

                if upx_dir:
                    exe_path = os.path.join(output_dir, script_name_without_ext + exe_ext)
                    compress_with_upx(upx_dir, exe_path)

                logging.info(f"Nuitka 打包成功: {script_name}")

            except subprocess.CalledProcessError as e:
                logging.error(f"Nuitka 打包失败: {e}")
    else:
        # PyInstaller 或 Nuitka 单个脚本
        if packer == 'pyinstaller':
            command = build_pyinstaller_command(script_names, output_dir, add_data, onefile, upx_dir)
        else:  # packer == 'nuitka'
            nuitka_executable = get_nuitka_executable(os.path.dirname(os.path.abspath(script_names[0])))
            if not nuitka_executable:
                logging.error("获取 Nuitka 可执行文件失败。")
                return
            command = [nuitka_executable] + build_nuitka_command(script_names, output_dir, add_data, onefile)
            command.extend(script_names)

        try:
            subprocess.run(command, check=True, cwd=os.path.dirname(os.path.abspath(script_names[0])))

            if upx_dir:
                for script_name in script_names:
                    script_name_without_ext = os.path.splitext(os.path.basename(script_name))[0]
                    exe_ext = get_executable_extension()
                    exe_path = os.path.join(output_dir, script_name_without_ext + exe_ext)
                    compress_with_upx(upx_dir, exe_path)

            logging.info(f"{packer} 打包成功: {script_names}")

        except subprocess.CalledProcessError as e:
            logging.error(f"{packer} 打包失败: {e}")


def _process_item(data_dir, item):
    """处理单个文件，格式化为 PyInstaller/Nuitka 所需的格式."""
    source_path = os.path.join(data_dir, item)
    dest_path = item
    return f"{source_path}{os.pathsep}{dest_path}"


def prepare_data_files(data_dir):
    """准备要添加到打包文件中的数据文件."""
    add_data = []
    if data_dir:
        with ProcessPoolExecutor() as executor:
            futures = [executor.submit(_process_item, data_dir, item) for item in os.listdir(data_dir)]
            for future in futures:
                add_data.append(future.result())
    return add_data


def run_packaged_program(script_names, packer='pyinstaller', args_to_pass=None, onefile=False):
    """运行打包后的程序."""
    base_dir = os.path.dirname(os.path.abspath(script_names[0]))
    output_dir = os.path.join(base_dir, "output")

    for script_name in script_names:
        script_name_without_ext = os.path.splitext(os.path.basename(script_name))[0]
        exe_ext = get_executable_extension()
        exe_name = script_name_without_ext + exe_ext

        if packer == 'pyinstaller':
            pyinstaller_output_dir = os.path.join(output_dir, "pyinstaller")
            exe_path = os.path.join(pyinstaller_output_dir, script_name_without_ext, exe_name) if not onefile else os.path.join(pyinstaller_output_dir, exe_name)

        elif packer == 'nuitka':
            nuitka_output_dir = os.path.join(output_dir, "nuitka")
            if onefile:
                exe_path = os.path.join(nuitka_output_dir, exe_name)
                if not os.path.exists(exe_path):
                    logging.warning("Onefile 模式打包的可执行文件不存在，尝试查找非 Onefile 模式的可执行文件...")
                    onefile = False
            exe_path = os.path.join(nuitka_output_dir, f"{script_name_without_ext}.dist", exe_name) if not onefile else exe_path
        else:
            logging.error("无效的打包工具，请选择 'pyinstaller' 或 'nuitka'。")
            return

        if os.path.exists(exe_path):
            command = [exe_path]
            if args_to_pass:
                command.extend(shlex.split(args_to_pass))
            try:
                subprocess.run(command, check=True)
                logging.info(f"运行打包后的程序成功: {exe_path}")
            except subprocess.CalledProcessError as e:
                logging.error(f"运行打包后的程序失败: {e}")
        else:
            logging.error(f"找不到打包后的程序: {exe_path}，请先打包程序。")


def validate_arguments(args):
    """验证命令行参数是否有效."""
    for script_name in args.script_names:
        if not os.path.exists(script_name):
            raise FileNotFoundError(f"脚本文件不存在: {script_name}")
    if args.data_dir and not os.path.exists(args.data_dir):
        raise FileNotFoundError(f"资源目录不存在: {args.data_dir}")
    if args.upx_dir:
        upx_executable = os.path.join(args.upx_dir, "upx")
        if not os.path.exists(upx_executable):
            raise FileNotFoundError(f"UPX 可执行文件未找到: {upx_executable}")


def parse_arguments():
    """解析命令行参数，并验证参数的有效性."""
    parser = argparse.ArgumentParser(
        description="使用 PyInstaller 或 Nuitka 打包 Python 脚本。\n\n"
                    "示例:\n"
                    "  python your_script.py main.py script2.py --packer nuitka --onefile --data_dir data\n\n"
                    "注意:\n"
                    "  - 使用 Nuitka 需要先安装 Nuitka: pip install nuitka\n"
                    "  - UPX 是一个可选的压缩工具，可以减小可执行文件的大小，需要单独下载并指定其目录。\n",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("script_names", nargs='+', help="脚本的文件名")
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
        help="传递给可执行文件的参数 (可选)"
    )
    parser.add_argument(
        "--data_dir",
        help="资源文件所在的目录 (可选)"
    )

    args = parser.parse_args()

    try:
        validate_arguments(args)
    except FileNotFoundError as e:
        print(f"参数验证失败: {e}")
        sys.exit(1)

    return args


if __name__ == "__main__":
    args = parse_arguments()

    script_names = args.script_names
    packer = args.packer
    upx_dir = args.upx_dir
    onefile = args.onefile
    args_to_pass = args.args_to_pass
    data_dir = args.data_dir

    package(script_names, packer, upx_dir, onefile=onefile, data_dir=data_dir)
    run_packaged_program(script_names, packer, args_to_pass, onefile=onefile)
