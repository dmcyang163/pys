import ast
import inspect
import warnings
from typing import Set, List, Type
import textwrap


def auto_slots(*extra_attrs):
    """自动为类添加 __slots__ 属性的装饰器
    
    Args:
        *extra_attrs: 额外需要添加的属性名
    """
    # 缓存已处理的类
    if not hasattr(auto_slots, '_cache'):
        auto_slots._cache = {}

    def get_attributes(node: ast.AST) -> Set[str]:
        """从 AST 中提取所有属性访问"""
        attrs = set()
        for child in ast.walk(node):
            # 检查普通的属性访问 (self.xxx)
            if isinstance(child, ast.Attribute) and \
            isinstance(child.value, ast.Name) and \
            child.value.id == 'self':
                print(f"Found attribute: {child.attr}")
                attrs.add(child.attr)
                
            # 检查 setattr 调用
            if isinstance(child, ast.Call) and \
            isinstance(child.func, ast.Name) and \
            child.func.id == 'setattr' and \
            len(child.args) >= 2:
                print(f"Found setattr call: {child.args[1]}")
                if isinstance(child.args[1], ast.Constant):
                    print(f"Adding setattr attribute: {child.args[1].value}")
                    attrs.add(child.args[1].value)
                
            # 检查 vars/dict 赋值
            if isinstance(child, ast.Subscript) and \
            isinstance(child.value, ast.Call) and \
            isinstance(child.value.func, ast.Name) and \
            child.value.func.id in ('vars', 'dict'):
                print(f"Found vars/dict access: {child.slice}")
                if isinstance(child.slice, ast.Constant):
                    print(f"Adding vars/dict attribute: {child.slice.value}")
                    attrs.add(child.slice.value)
            
            # 检查直接操作 __dict__ 的赋值
            if isinstance(child, ast.Assign) and \
            isinstance(child.targets[0], ast.Attribute) and \
            isinstance(child.targets[0].value, ast.Name) and \
            child.targets[0].value.id == 'self' and \
            child.targets[0].attr == '__dict__':
                print(f"Found direct __dict__ assignment")
                if isinstance(child.value, ast.Dict):
                    for key in child.value.keys:
                        if isinstance(key, ast.Constant):
                            print(f"Adding __dict__ attribute: {key.value}")
                            attrs.add(key.value)
        return attrs
    
    def get_class_attributes(cls: Type) -> Set[str]:
        """获取类中定义的所有属性"""
        attrs = set()
        
        try:
            print(f"\nProcessing class: {cls.__name__}")
            # 获取类的源代码
            source = inspect.getsource(cls)
            print(f"Source code:\n{source}")
            # 处理缩进问题
            source = textwrap.dedent(source)
            # 解析为 AST
            tree = ast.parse(source)
            # 提取静态定义的属性
            attrs.update(get_attributes(tree))
            print(f"Found attributes: {attrs}")
            
            # 处理继承
            for base in cls.__bases__:
                if hasattr(base, '__slots__'):
                    print(f"Adding base class slots: {base.__slots__}")
                    attrs.update(base.__slots__)
            
            # 获取运行时添加的方法中的属性
            for name, method in inspect.getmembers(cls, predicate=inspect.ismethod):
                if method.__module__ is None:  # 动态添加的方法
                    try:
                        print(f"Processing dynamic method: {name}")
                        source = inspect.getsource(method)
                        tree = ast.parse(source)
                        method_attrs = get_attributes(tree)
                        print(f"Found attributes in method: {method_attrs}")
                        attrs.update(method_attrs)
                    except:
                        print(f"Failed to process method: {name}")
            
            # 检查类的 __dict__ 中的属性
            for name, value in cls.__dict__.items():
                if not name.startswith('__'):
                    if callable(value):
                        try:
                            print(f"Processing callable: {name}")
                            source = inspect.getsource(value)
                            tree = ast.parse(source)
                            callable_attrs = get_attributes(tree)
                            print(f"Found attributes in callable: {callable_attrs}")
                            attrs.update(callable_attrs)
                        except:
                            print(f"Failed to process callable: {name}")
                    else:
                        print(f"Adding direct attribute: {name}")
                        attrs.add(name)
            
            # 添加额外属性
            print(f"Adding extra attributes: {extra_attrs}")
            attrs.update(extra_attrs)
            
            return attrs
                
        except (IOError, TypeError, IndentationError) as e:
            warnings.warn(f"Could not parse source for class {cls.__name__}: {e}")
            return set()
    def decorator(cls: Type) -> Type:
        """实际的装饰器函数"""
        # 如果类已经处理过，直接返回缓存的结果
        if cls in auto_slots._cache:
            return auto_slots._cache[cls]

        # 获取所有属性
        attrs = get_class_attributes(cls)
        
        # 设置 __slots__
        cls.__slots__ = list(attrs)

        # 添加一个方法来查看所有可用属性
        def get_available_attrs(self) -> List[str]:
            return self.__slots__
        cls.get_available_attrs = get_available_attrs

        # 缓存结果
        auto_slots._cache[cls] = cls
        
        return cls

    # 如果没有传入额外参数，直接返回装饰器
    if len(extra_attrs) == 1 and isinstance(extra_attrs[0], type):
        return decorator(extra_attrs[0])
    
    return decorator


# 使用示例:

def test_decorator(cls):
    """测试装饰器添加属性"""
    cls.decorator_attr = 'test'
    return cls

def test_metaclass(name, bases, dict):
    """测试元类添加属性"""
    dict['metaclass_attr'] = 'test'
    return type(name, bases, dict)

# 测试用例
if __name__ == "__main__":
    # 1. 测试动态属性赋值
    @auto_slots
    class TestDynamic:
        def __init__(self):
            self.normal = 1
            setattr(self, 'dynamic_attr', 2)
            vars(self)['dict_attr'] = 3

    # 2. 测试运行时方法
    @auto_slots
    class TestRuntime:
        def __init__(self):
            self.normal = 1

    def dynamic_method(self):
        self.runtime_attr = 2
    TestRuntime.new_method = dynamic_method

    # 3. 测试装饰器和元类
    @auto_slots
    @test_decorator
    class TestDecorator:
        def __init__(self):
            self.normal = 1

    class TestMeta(metaclass=test_metaclass):
        def __init__(self):
            self.normal = 1