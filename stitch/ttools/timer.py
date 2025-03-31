import time
from functools import wraps
import logging
from typing import Optional, Callable, Literal

# 时间单位类型
TimeUnit = Literal["ns", "μs", "ms", "s"]

# 默认日志配置
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class timer:
    """可配置单位的计时器装饰器"""
    def __init__(
        self,
        unit: TimeUnit = "ms",  # 默认毫秒
        logger: Optional[logging.Logger] = None,
        format_str: str = "{function} 耗时: {time:.2f}{unit}"
    ):
        self.unit = unit
        self.logger = logger or logging.getLogger("timer")
        self.format_str = format_str
        self._unit_factors = {
            "ns": 1e9,
            "μs": 1e6,
            "ms": 1e3,
            "s": 1
        }

    def __call__(self, func: Callable) -> Callable:
        @wraps(func)
        def wrapped(*args, **kwargs):
            start_time = time.perf_counter()
            result = func(*args, **kwargs)
            elapsed = self._convert_time(time.perf_counter() - start_time)
            
            self.logger.info(
                self.format_str.format(
                    function=f"{func.__module__}.{func.__qualname__}",
                    time=elapsed,
                    unit=self.unit
                )
            )
            return result
        return wrapped

    def _convert_time(self, seconds: float) -> float:
        """将秒转换为目标单位"""
        return seconds * self._unit_factors[self.unit]

# 默认实例（毫秒单位）
_default_timer = timer(unit="ms")
timer = _default_timer  # 导出模块级装饰器

class timing:
    """可配置单位的上下文计时器"""
    def __init__(
        self,
        name: str = "代码块",
        unit: TimeUnit = "ms",  # 默认毫秒
        logger: Optional[logging.Logger] = None
    ):
        self.name = name
        self.unit = unit
        self.logger = logger or logging.getLogger("timer")
        self._unit_factors = {
            "ns": 1e9,
            "μs": 1e6,
            "ms": 1e3,
            "s": 1
        }

    def __enter__(self):
        self.start = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        elapsed = (time.perf_counter() - self.start) * self._unit_factors[self.unit]
        self.logger.info(f"⏳ {self.name} 耗时: {elapsed:.2f}{self.unit}")

if __name__ == "__main__":
    # 测试代码
    @timer(unit="ms")  # 默认毫秒（可省略）
    def test_func(n):
        return sum(range(n))
    
    with timing("纳秒测试", unit="ns"):
        test_func(1000000)
    
    with timing("微秒测试", unit="μs"):
        test_func(1000000)
    
    with timing("秒测试", unit="s"):
        test_func(1000000)