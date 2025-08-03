import sys
import importlib.util
import os

# 待执行的脚本列表（仅需文件名，无需 .py 后缀）
scripts_to_run = ["connect_mysql", "data_downloader", "data_cleaner", "factor_calculation", "portfoliobuild"]  # 注意子目录需用点分隔

for script_name in scripts_to_run:
    try:
        sys.path.append(os.getcwd())  # 确保当前目录在搜索路径中

        # 动态加载模块
        spec = importlib.util.spec_from_file_location(script_name, f"{script_name}.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # 调用模块的 main 函数（假设每个脚本都有 main 函数）
        print(f"=== 执行 {script_name} 的 main 函数 ===")
        module.main()
    except Exception as e:
        print(f"=== 执行 {script_name} 的 main 函数时出错：{str(e)}")
    finally:
        sys.path.pop()  # 移除当前目录（根据实际情况调整）