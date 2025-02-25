import argparse
import os
import subprocess
import shutil
import platform
import sys
import logging
import shlex
import ast
from concurrent.futures import ProcessPoolExecutor

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class Packer:
    """打包工具的基类。"""
    def __init__(self, script_names, output_dir, upx_dir=None, onefile=False, data_dir=None, data_dir_map=None):
        """初始化打包器。"""
        self.script_names = script_names
        self.output_dir = output_dir
        self.upx_dir = upx_dir
        self.onefile = onefile
        self.data_dir = data_dir
        self.data_dir_map = data_dir_map or {}
        self.add_data = self._prepare_data_files()

    def _prepare_data_files(self):
        """准备要打包的数据文件。"""
        add_data = []
        for script_name in self.script_names:
            data_dir_to_use = self.data_dir_map.get(script_name) if script_name in self.data_dir_map else self.data_dir
            if data_dir_to_use:
                add_data.extend(self._process_data_dir(data_dir_to_use))
        return add_data

    def _process_data_dir(self, data_dir):
        """处理数据目录。"""
        add_data = []
        with ProcessPoolExecutor() as executor:
            futures = [executor.submit(self._process_item, data_dir, item) for item in os.listdir(data_dir)]
            for future in futures:
                add_data.append(future.result())
        return add_data

    def _process_item(self, data_dir, item):
        """处理单个文件项。"""
        source_path = os.path.join(data_dir, item)
        dest_path = item
        return f"{source_path}{os.pathsep}{dest_path}"

    def package(self):
        """打包脚本。"""
        with ProcessPoolExecutor() as executor:
            futures = []
            for script_name in self.script_names:
                futures.append(executor.submit(self._package_single_script, script_name))

            for future in futures:
                future.result()

    def _package_single_script(self, script_name):
        """打包单个脚本。子类必须实现此方法。"""
        raise NotImplementedError("子类必须实现 _package_single_script")

    def _compress_executable(self, exe_path):
        """使用 UPX 压缩可执行文件。"""
        if self.upx_dir:
            if self._is_already_compressed(exe_path):
                logging.info(f"文件已经被 UPX 压缩: {exe_path}")
                return

            if not self._test_upx_compression(exe_path):
                return

            upx_command = [os.path.join(self.upx_dir, "upx"), "--best", exe_path]
            try:
                subprocess.run(upx_command, check=True)
                logging.info(f"UPX 压缩成功: {exe_path}")
            except subprocess.CalledProcessError as e:
                logging.error(f"UPX 压缩失败: {e}")
            except FileNotFoundError:
                logging.error(f"未找到 UPX 工具: {self.upx_dir}")

    def _test_upx_compression(self, exe_path):
        """测试 UPX 压缩是否可行。"""
        test_command = [os.path.join(self.upx_dir, "upx"), "-t", exe_path]
        try:
            subprocess.run(test_command, check=True)
            logging.info(f"文件可以被 UPX 压缩: {exe_path}")
            return True
        except subprocess.CalledProcessError as e:
            logging.warning(f"文件无法被 UPX 压缩: {e}")
            return False

    def _is_already_compressed(self, exe_path):
        """检查文件是否已经被 UPX 压缩。"""
        info_command = [os.path.join(self.upx_dir, "upx"), "-l", exe_path]
        try:
            result = subprocess.run(info_command, capture_output=True, text=True, check=True)
            return "compressed" in result.stdout
        except subprocess.CalledProcessError:
            return False


class PyInstallerPacker(Packer):
    """使用 PyInstaller 打包脚本。"""
    def __init__(self, script_names, output_dir, upx_dir=None, onefile=False, data_dir=None, data_dir_map=None):
        """初始化 PyInstaller 打包器。"""
        super().__init__(script_names, output_dir, upx_dir, onefile, data_dir, data_dir_map)

    def _build_command(self, script_name):
        """构建 PyInstaller 命令。"""
        command = [
            "pyinstaller",
            "--noconsole",
            f"--distpath={self.output_dir}",
            f"--workpath={os.path.join(self.output_dir, 'build')}",
            "--clean"
        ]
        if self.onefile:
            command.append("--onefile")
        for data in self.add_data:
            command.append(f"--add-data={data}")
        if self.upx_dir:
            command.append(f"--upx-dir={self.upx_dir}")
        command.append(script_name)
        return command

    def _package_single_script(self, script_name):
        """使用 PyInstaller 打包单个脚本。"""
        command = self._build_command(script_name)
        try:
            subprocess.run(command, check=True, cwd=os.path.dirname(os.path.abspath(script_name)))

            script_name_without_ext = os.path.splitext(os.path.basename(script_name))[0]
            exe_ext = self._get_executable_extension()
            exe_name = script_name_without_ext + exe_ext  # 定义 exe_name
            exe_path = os.path.join(self.output_dir, script_name_without_ext, exe_name) if not self.onefile else os.path.join(self.output_dir, exe_name)

            self._compress_executable(exe_path)

            logging.info(f"PyInstaller 打包成功: {script_name}")

        except subprocess.CalledProcessError as e:
            logging.error(f"PyInstaller 打包失败: {e}")

    def _get_executable_extension(self):
        """根据操作系统获取可执行文件后缀。"""
        return ".exe" if platform.system() == "Windows" else ""


class NuitkaPacker(Packer):
    """使用 Nuitka 打包脚本。"""
    def __init__(self, script_names, output_dir, upx_dir=None, onefile=False, data_dir=None, data_dir_map=None):
        """初始化 Nuitka 打包器。"""
        super().__init__(script_names, output_dir, upx_dir, onefile, data_dir, data_dir_map)
        self.nuitka_executable = self._get_nuitka_executable(os.path.dirname(os.path.abspath(script_names[0])))

    def _get_nuitka_executable(self, base_dir):
        """获取 Nuitka 可执行文件路径。"""
        venv_path = self._get_virtual_env_path()
        if venv_path:
            nuitka_cmd = "nuitka.cmd" if platform.system() == "Windows" else "nuitka"
            venv_nuitka_path = os.path.join(venv_path, "Scripts", nuitka_cmd)
            if os.path.exists(venv_nuitka_path):
                logging.info(f"使用虚拟环境中的 Nuitka: {venv_nuitka_path}")
                return venv_nuitka_path
            else:
                logging.warning("虚拟环境中未找到 Nuitka，尝试使用系统 PATH。")

        nuitka_executable = "nuitka"
        if shutil.which(nuitka_executable) is None:
            logging.error("系统 PATH 中未找到 Nuitka。请确保已安装并添加到 PATH。")
            return None
        return nuitka_executable

    def _get_virtual_env_path(self):
        """获取虚拟环境路径。"""
        venv_path = os.environ.get("VIRTUAL_ENV")
        if venv_path and os.path.isdir(venv_path):
            return venv_path
        if getattr(sys, 'base_prefix', sys.prefix) != sys.prefix:
            return sys.prefix
        return None

    def _build_command(self, script_name):
        """构建 Nuitka 命令。"""
        command = [
            "--standalone",
            "--windows-console-mode=disable",
            "--follow-imports",
            f"--output-dir={self.output_dir}",
        ]
        if self.onefile:
            command.append("--onefile")

        for data in self.add_data:
            source, dest = data.split(os.pathsep)
            command.append(f"--include-data-dir={source}={dest}")

        return command

    def _package_single_script(self, script_name):
        """使用 Nuitka 打包单个脚本。"""
        if not self.nuitka_executable:
            logging.error("获取 Nuitka 可执行文件失败。")
            return

        script_name_without_ext = os.path.splitext(os.path.basename(script_name))[0]
        exe_ext = self._get_executable_extension()
        exe_name = script_name_without_ext + exe_ext  # 定义 exe_name

        command = [self.nuitka_executable] + self._build_command(script_name)
        command.extend(["--output-filename=" + exe_name, script_name])

        try:
            subprocess.run(command, check=True, cwd=os.path.dirname(os.path.abspath(script_name)))

            exe_path = os.path.join(self.output_dir, exe_name)
            self._compress_executable(exe_path)

            logging.info(f"Nuitka 打包成功: {script_name}")

        except subprocess.CalledProcessError as e:
            logging.error(f"Nuitka 打包失败: {e}")

    def _get_executable_extension(self):
        """根据操作系统获取可执行文件后缀。"""
        return ".exe" if platform.system() == "Windows" else ""


class ProgramRunner:
    """运行打包后的程序。"""
    def __init__(self, script_names, packer='pyinstaller', args_to_pass=None, onefile=False):
        """初始化程序运行器。"""
        self.script_names = script_names
        self.packer = packer
        self.args_to_pass = args_to_pass
        self.onefile = onefile
        self.base_dir = os.path.dirname(os.path.abspath(script_names[0]))
        self.output_dir = os.path.join(self.base_dir, "output")

    def run(self):
        """运行打包后的程序。"""
        for script_name in self.script_names:
            script_name_without_ext = os.path.splitext(os.path.basename(script_name))[0]
            exe_ext = self._get_executable_extension()
            exe_name = script_name_without_ext + exe_ext

            if self.packer == 'pyinstaller':
                pyinstaller_output_dir = os.path.join(self.output_dir, "pyinstaller")
                exe_path = os.path.join(pyinstaller_output_dir, script_name_without_ext, exe_name) if not self.onefile else os.path.join(pyinstaller_output_dir, exe_name)

            elif self.packer == 'nuitka':
                nuitka_output_dir = os.path.join(self.output_dir, "nuitka")
                if self.onefile:
                    exe_path = os.path.join(nuitka_output_dir, exe_name)
                    if not os.path.exists(exe_path):
                        logging.warning("Onefile 可执行文件未找到，尝试查找非 Onefile 版本。")
                        self.onefile = False
                exe_path = os.path.join(nuitka_output_dir, f"{script_name_without_ext}.dist", exe_name) if not self.onefile else exe_path
            else:
                logging.error("无效的打包工具。请选择 'pyinstaller' 或 'nuitka'。")
                return

            if os.path.exists(exe_path):
                command = [exe_path]
                if self.args_to_pass:
                    command.extend(shlex.split(self.args_to_pass))
                try:
                    subprocess.run(command, check=True)
                    logging.info(f"打包后的程序运行成功: {exe_path}")
                except subprocess.CalledProcessError as e:
                    logging.error(f"打包后的程序运行失败: {e}")
            else:
                logging.error(f"打包后的程序未找到: {exe_path}。请先打包。")

    def _get_executable_extension(self):
        """根据操作系统获取可执行文件后缀。"""
        return ".exe" if platform.system() == "Windows" else ""


class ArgumentValidator:
    """验证命令行参数。"""
    def __init__(self, args):
        """初始化参数验证器。"""
        self.args = args

    def validate(self):
        """验证参数。"""
        for script_name in self.args.script_names:
            if not os.path.exists(script_name):
                raise FileNotFoundError(f"脚本文件未找到: {script_name}")
        if self.args.data_dir_map:
            try:
                data_dir_map = self._parse_data_dir_map(self.args.data_dir_map, self.args.script_names)
                for script_name, data_dir in data_dir_map.items():
                    data_dir = os.path.normpath(data_dir)
                    if not os.path.exists(data_dir):
                        raise FileNotFoundError(f"数据目录未找到: {data_dir}")
            except ValueError as e:
                raise ValueError(f"data_dir_map 解析失败: {e}")
        if self.args.data_dir and not os.path.exists(self.args.data_dir):
            raise FileNotFoundError(f"数据目录未找到: {self.args.data_dir}")
        if self.args.upx_dir:
            upx_executable = os.path.join(self.args.upx_dir, "upx")
            if not os.path.exists(upx_executable):
                raise FileNotFoundError(f"UPX 可执行文件未找到: {upx_executable}")

    def _parse_data_dir_map(self, data_dir_map_str, script_names):
        """解析 data_dir_map 字符串。

        data_dir_map 允许你为每个脚本指定不同的资源目录。
        它是一个字符串，格式为 "脚本标识:资源目录:脚本标识:资源目录..."。
        脚本标识可以是脚本的序号（从 1 开始），也可以是脚本的文件名（可以不完整，但要能唯一匹配一个脚本）。
        例如: "1:./data1:2:./data2" 或 "main.py:./data1:helper.py:./data2"。
        """
        data_dir_map = {}
        items = data_dir_map_str.split(':')
        if len(items) % 2 != 0:
            logging.warning("data_dir_map 格式不正确，跳过。")
            return {}

        for i in range(0, len(items), 2):
            key = items[i].strip()
            data_dir = items[i + 1].strip()

            try:
                script_index = int(key) - 1
                if 0 <= script_index < len(script_names):
                    script_name = script_names[script_index]
                    data_dir_map[script_name] = data_dir
                else:
                    logging.warning(f"脚本序号 {key} 超出范围，跳过。")
            except ValueError:
                matched_script = None
                for script_name in script_names:
                    if key in script_name:
                        if matched_script is not None:
                            logging.warning(f"文件名 {key} 匹配到多个脚本，跳过。")
                            matched_script = None
                            break
                        matched_script = script_name
                if matched_script:
                    data_dir_map[matched_script] = data_dir
                else:
                    logging.warning(f"文件名 {key} 未匹配到任何脚本，跳过。")
        return data_dir_map


class ArgumentParser:
    """解析命令行参数。"""
    def __init__(self):
        """初始化参数解析器。"""
        self.parser = argparse.ArgumentParser(
            description="使用 PyInstaller 或 Nuitka 打包 Python 脚本。\n\n"
                        "示例:\n"
                        "  python your_script.py 1.py --data_dir data1\n"
                        "  python your_script.py 1.py 2.py --data_dir_map \"1:./data1:2:./data2\"\n"
                        "  python your_script.py 1.py 2.py --data_dir_map \"main.py:./data1:helper.py:./data2\"\n\n"
                        "注意:\n"
                        "  - 使用 Nuitka 需要先安装 Nuitka: pip install nuitka\n"
                        "  - UPX 是一个可选的压缩工具，可以减小可执行文件的大小，需要单独下载并指定其目录。\n",
            formatter_class=argparse.RawTextHelpFormatter
        )
        self._add_arguments()

    def _add_arguments(self):
        """添加命令行参数。"""
        self.parser.add_argument("script_names", nargs='+', help="脚本的文件名")
        self.parser.add_argument(
            "--packer",
            choices=['pyinstaller', 'nuitka'],
            default='pyinstaller',
            help="选择打包工具 (pyinstaller 或 nuitka)"
        )
        self.parser.add_argument(
            "--upx_dir",
            help="UPX 压缩工具的目录 (可选)"
        )
        self.parser.add_argument(
            "--onefile",
            action="store_true",
            help="使用 Onefile 模式 (可选)"
        )
        self.parser.add_argument(
            "--args_to_pass",
            help="传递给可执行文件的参数 (可选)"
        )
        self.parser.add_argument(
            "--data_dir",
            help="资源文件所在的目录 (可选，用于单个脚本)"
        )
        self.parser.add_argument(
            "--data_dir_map",
            help="资源文件目录的映射 (字符串，例如 \"1:./data1:2:./data2\")"
        )

    def parse_args(self):
        """解析命令行参数。"""
        args = self.parser.parse_args()
        try:
            ArgumentValidator(args).validate()
        except FileNotFoundError as e:
            print(f"参数验证失败: {e}")
            sys.exit(1)
        except ValueError as e:
            print(f"参数验证失败: {e}")
            sys.exit(1)
        return args


class OutputDirectoryManager:
    """管理输出目录。"""
    def __init__(self, base_dir):
        """初始化输出目录管理器。"""
        self.base_dir = base_dir

    def create_output_dir(self, packer):
        """创建输出目录。"""
        output_dir = os.path.join(self.base_dir, "output")
        packer_output_dir = os.path.join(output_dir, packer)
        os.makedirs(packer_output_dir, exist_ok=True)
        return packer_output_dir


def main():
    """主函数。"""
    args = ArgumentParser().parse_args()

    script_names = args.script_names
    packer_name = args.packer
    upx_dir = args.upx_dir
    onefile = args.onefile
    args_to_pass = args.args_to_pass
    data_dir = args.data_dir
    data_dir_map_str = args.data_dir_map

    base_dir = os.path.dirname(os.path.abspath(script_names[0]))
    output_dir = OutputDirectoryManager(base_dir).create_output_dir(packer_name)

    data_dir_map = {}
    if data_dir_map_str:
        data_dir_map = ArgumentValidator(args)._parse_data_dir_map(data_dir_map_str, script_names)

    if packer_name == 'pyinstaller':
        packer = PyInstallerPacker(script_names, output_dir, upx_dir, onefile, data_dir, data_dir_map)
    elif packer_name == 'nuitka':
        packer = NuitkaPacker(script_names, output_dir, upx_dir, onefile, data_dir, data_dir_map)
    else:
        print("无效的打包工具。请选择 'pyinstaller' 或 'nuitka'。")
        sys.exit(1)

    packer.package()

    ProgramRunner(script_names, packer_name, args_to_pass, onefile).run()


if __name__ == "__main__":
    main()
