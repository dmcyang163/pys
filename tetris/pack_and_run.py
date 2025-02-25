import argparse
import os
import subprocess
import shutil
import platform
import sys
import logging
import shlex
import ast
import re
from concurrent.futures import ProcessPoolExecutor

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class LowercaseAction(argparse.Action):
    """自定义 Action 类，将参数值转换为小写，但排除 data_dir 和 data_dir_map。"""
    def __call__(self, parser, namespace, values, option_string=None):
        if self.dest not in ['data_dir', 'data_dir_map']:
            if isinstance(values, str):
                setattr(namespace, self.dest, values.lower())
            else:
                setattr(namespace, self.dest, [v.lower() for v in values])
        else:
            setattr(namespace, self.dest, values)


class CaseInsensitiveChoicesParser(argparse.ArgumentParser):
    """自定义 ArgumentParser 类，使其在比较 choices 时不区分大小写。"""
    def _check_value(self, action, value):
        # converted value must be one of the choices (if specified)
        if action.choices is not None and value.lower() not in action.choices:
            tup = (value, ', '.join(map(repr, action.choices)))
            msg = "invalid choice: %r (choose from %s)" % tup
            raise argparse.ArgumentError(action, msg)


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
        add_data = {}  # 使用字典存储每个脚本的数据文件
        for script_name in self.script_names:
            add_data[script_name] = []
            data_dir_to_use = self.data_dir_map.get(script_name)
            if data_dir_to_use:
                add_data[script_name].extend(self._process_data_dir(data_dir_to_use, script_name))
        return add_data

    def _process_data_dir(self, data_dir, script_name):
        """处理数据目录。"""
        add_data = []
        with ProcessPoolExecutor() as executor:
            futures = [executor.submit(self._process_item, data_dir, item) for item in os.listdir(data_dir)]
            for future in futures:
                item_data = future.result()
                add_data.append(item_data)
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

    @staticmethod
    def _compress_executable(exe_path, upx_dir):
        """使用 UPX 压缩可执行文件。"""
        if upx_dir:
            if Packer._is_already_compressed(exe_path, upx_dir):
                logging.info(f"文件已经被 UPX 压缩: {exe_path}")
                return

            if not Packer._test_upx_compression(exe_path, upx_dir):
                return

            upx_command = [os.path.join(upx_dir, "upx"), "--best", exe_path]
            try:
                subprocess.run(upx_command, check=True)
                logging.info(f"UPX 压缩成功: {exe_path}")
            except subprocess.CalledProcessError as e:
                logging.error(f"UPX 压缩失败: {e}")
            except FileNotFoundError:
                logging.error(f"未找到 UPX 工具: {upx_dir}")

    @staticmethod
    def _test_upx_compression(exe_path, upx_dir):
        """测试 UPX 压缩是否可行。"""
        test_command = [os.path.join(upx_dir, "upx"), "-t", exe_path]
        try:
            subprocess.run(test_command, check=True)
            logging.info(f"文件可以被 UPX 压缩: {exe_path}")
            return True
        except subprocess.CalledProcessError as e:
            logging.warning(f"文件无法被 UPX 压缩: {e}")
            return False

    @staticmethod
    def _is_already_compressed(exe_path, upx_dir):
        """检查文件是否已经被 UPX 压缩。"""
        info_command = [os.path.join(upx_dir, "upx"), "-l", exe_path]
        try:
            result = subprocess.run(info_command, capture_output=True, text=True, check=True)
            return "compressed" in result.stdout
        except subprocess.CalledProcessError:
            return False

    def _is_resource_used(self, script_name, resource_path):
        """检查脚本是否使用了某个资源文件。"""
        try:
            with open(script_name, 'r', encoding='utf-8') as f:
                script_content = f.read()
            resource_name = os.path.basename(resource_path)
            return resource_name in script_content
        except Exception as e:
            logging.warning(f"无法读取脚本 {script_name}: {e}")
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
        for data in self.add_data[script_name]:  # 获取当前脚本的数据文件
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
            exe_name = script_name_without_ext + exe_ext
            exe_path = os.path.join(self.output_dir, script_name_without_ext, exe_name) if not self.onefile else os.path.join(self.output_dir, exe_name)

            Packer._compress_executable(exe_path, self.upx_dir)

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

        for data in self.add_data[script_name]:  # 获取当前脚本的数据文件
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
        exe_name = script_name_without_ext + exe_ext

        command = [self.nuitka_executable] + self._build_command(script_name)
        command.extend(["--output-filename=" + exe_name, script_name])

        try:
            subprocess.run(command, check=True, cwd=os.path.dirname(os.path.abspath(script_name)))

            exe_path = os.path.join(self.output_dir, exe_name)
            Packer._compress_executable(exe_path, self.upx_dir)

            logging.info(f"Nuitka 打包成功: {script_name}")

        except subprocess.CalledProcessError as e:
            logging.error(f"Nuitka 打包失败: {e}")

    def _get_executable_extension(self):
        """根据操作系统获取可执行文件后缀。"""
        return ".exe" if platform.system() == "Windows" else ""


class ProgramRunner:
    """运行打包后的程序。"""
    def __init__(self, script_names, packer='pyinstaller', args_to_pass=None, onefile=False, run=True):
        """初始化程序运行器。"""
        self.script_names = script_names
        self.packer = packer
        self.args_to_pass = args_to_pass
        self.onefile = onefile
        self.run = run  # 新增 run 参数
        self.base_dir = os.path.dirname(os.path.abspath(script_names[0]))
        self.output_dir = os.path.join(self.base_dir, "output")

    def run_program(self):  # 修改方法名，避免与参数名冲突
        """运行打包后的程序。"""
        if not self.run:
            logging.info("跳过运行打包后的程序。")
            return

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
                    if data_dir:  # 只有当 data_dir 不为空时才进行验证
                        data_dir = os.path.normpath(data_dir)
                        if not os.path.exists(data_dir):
                            raise FileNotFoundError(f"数据目录未找到: {data_dir}")
            except ValueError as e:
                raise ValueError(f"data_dir_map 解析失败: {e}")
        if self.args.data_dir and not os.path.exists(self.args.data_dir):
            raise FileNotFoundError(f"数据目录未找到: {self.args.data_dir}")
        if self.args.upx_dir and not os.path.exists(self.args.upx_dir):
            raise FileNotFoundError(f"UPX 目录未找到: {self.args.upx_dir}")
        if self.args.upx_dir:
            upx_executable = os.path.join(self.args.upx_dir, "upx")
            if not os.path.exists(upx_executable):
                raise FileNotFoundError(f"UPX 可执行文件未找到: {upx_executable}")

    def _parse_data_dir_map(self, data_dir_map_str, script_names):
        """解析 data_dir_map 字符串。"""
        data_dir_map = {}
        # 使用正则表达式分割字符串，支持空格、逗号、分号作为分隔符
        items = re.split(r'[ ,;]+', data_dir_map_str)

        # 检查是否至少有一个键
        if not items:
            logging.warning("data_dir_map 为空，跳过。")
            return {}

        i = 0
        while i < len(items):
            key_value = items[i].strip()
            i += 1

            # 分割键和值
            parts = key_value.split(":", 1)
            key = parts[0].strip()
            data_dir = parts[1].strip() if len(parts) > 1 else None

            # 尝试将 key 解析为整数索引
            try:
                script_index = int(key) - 1
                if 0 <= script_index < len(script_names):
                    script_name = script_names[script_index]
                    data_dir_map[script_name] = data_dir  # 允许 data_dir 为 None
                else:
                    logging.warning(f"脚本序号 {key} 超出范围，跳过。")
            except ValueError:
                # 如果 key 不是整数，则尝试将其作为脚本名匹配
                matched_script = None
                for script_name in script_names:
                    if key.lower() in script_name.lower():  # 忽略大小写匹配
                        if matched_script is not None:
                            logging.warning(f"文件名 {key} 匹配到多个脚本，跳过。")
                            matched_script = None
                            break
                        matched_script = script_name
                if matched_script:
                    data_dir_map[matched_script] = data_dir  # 允许 data_dir 为 None
                else:
                    logging.warning(f"文件名 {key} 未匹配到任何脚本，跳过。")

            # 如果 data_dir 为 None，则从 data_dir_map 中移除该脚本
            # 这确保了只有明确指定了资源目录的脚本才会被添加到 data_dir_map 中
            # 其他脚本将不会包含任何资源文件
            #if data_dir is None and matched_script in data_dir_map:
            #    del data_dir_map[matched_script]

        return data_dir_map


class ArgumentParser:
    """解析命令行参数。"""
    def __init__(self):
        """初始化参数解析器。"""
        self.parser = CaseInsensitiveChoicesParser(  # 使用自定义的 ArgumentParser
            description="使用 PyInstaller 或 Nuitka 打包 Python 脚本。\n\n"
                        "示例:\n"
                        "  python your_script.py 1.py --data_dir data1\n"
                        "  python your_script.py 1.py 2.py --data_dir_map \"1:./data1 2:./data2\"\n"
                        "  python your_script.py 1.py 2.py --data_dir_map \"main.py:./data1 helper.py:./data2\"\n"
                        "  python your_script.py 1.py --run no\n"
                        "  python your_script.py 1.py --run NO\n"
                        "  python your_script.py 1.py --packer Nuitka\n"
                        "  python your_script.py 1.py 2.py --data_dir_map \"1:./data1 tetris\"\n\n"
                        "注意:\n"
                        "  - 使用 Nuitka 需要先安装 Nuitka: pip install nuitka\n"
                        "  - UPX 是一个可选的压缩工具，可以减小可执行文件的大小，需要单独下载并指定其目录。\n",
            formatter_class=argparse.RawTextHelpFormatter
        )
        self._add_arguments()
        self._convert_choices_to_lowercase()  # 添加这一行

    def _add_arguments(self):
        """添加命令行参数。"""
        self.parser.add_argument("script_names", nargs='+', help="脚本的文件名")
        self.parser.add_argument(
            "--packer",
            choices=['pyinstaller', 'nuitka'],
            default='pyinstaller',
            help="选择打包工具 (pyinstaller 或 nuitka)",
            action=LowercaseAction
        )
        self.parser.add_argument(
            "--upx_dir",
            help="UPX 压缩工具的目录 (可选)",
            action=LowercaseAction
        )
        self.parser.add_argument(
            "--onefile",
            action="store_true",
            help="使用 Onefile 模式 (可选)"
        )
        self.parser.add_argument(
            "--args_to_pass",
            help="传递给可执行文件的参数 (可选)",
            action=LowercaseAction
        )
        self.parser.add_argument(
            "--data_dir",
            help="资源文件所在的目录 (可选，用于单个脚本)",
            action=LowercaseAction
        )
        self.parser.add_argument(
            "--data_dir_map",
            help="资源文件目录的映射 (字符串，例如 \"1:./data1 2:./data2\")",
            action=LowercaseAction
        )
        self.parser.add_argument(
            "--run",
            choices=['yes', 'no'],
            default='yes',
            help="是否运行打包后的程序 (yes 或 no，默认为 yes，不区分大小写)",
            action=LowercaseAction
        )

    def _convert_choices_to_lowercase(self):
        """将 choices 中的选项转换为小写。"""
        for action in self.parser._actions:
            if isinstance(action, argparse._StoreAction) and action.choices:
                action.choices = [choice.lower() for choice in action.choices]

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
    run = args.run == 'yes'  # 获取 run 参数的值

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

    runner = ProgramRunner(script_names, packer_name, args_to_pass, onefile, run)
    runner.run_program()

    sys.exit(0)  # 运行完成后退出


if __name__ == "__main__":
    main()
