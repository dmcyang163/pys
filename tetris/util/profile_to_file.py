import io
from line_profiler import LineProfiler

def profile_to_file(output_file='manual_output.txt'):
    def decorator(func):
        def wrapper(*args, **kwargs):
            # 创建 LineProfiler 实例
            lp = LineProfiler()
            # 对函数进行包装
            lp_wrapper = lp(func)
            # 调用被包装的函数并获取结果
            result = lp_wrapper(*args, **kwargs)

            # 捕获输出到字符串
            output = io.StringIO()
            lp.print_stats(stream=output)

            # 将输出保存到文件
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(output.getvalue())

            return result
        return wrapper
    return decorator


@profile_to_file(output_file='add_numbers_profile.txt')
def add_numbers():
    result = 0
    for i in range(1000):
        result += i
    return result


if __name__ == "__main__":
    add_numbers()