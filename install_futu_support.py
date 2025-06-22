#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
富途OpenAPI支持安装脚本
自动安装港美股交易所需的依赖包
"""

import subprocess
import sys
import os

def install_package(package_name):
    """
    安装Python包
    
    Args:
        package_name: 包名
    """
    try:
        print(f"正在安装 {package_name}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
        print(f"✓ {package_name} 安装成功")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ {package_name} 安装失败: {e}")
        return False

def check_package(package_name):
    """
    检查包是否已安装
    
    Args:
        package_name: 包名
        
    Returns:
        bool: 是否已安装
    """
    try:
        __import__(package_name)
        return True
    except ImportError:
        return False

def main():
    """
    主安装函数
    """
    print("=" * 60)
    print("Wondertrade 富途OpenAPI支持安装程序")
    print("=" * 60)
    
    # 必需的包列表
    required_packages = [
        ("futu-api", "futu"),  # (pip包名, import名)
        ("numpy", "numpy"),
        ("pandas", "pandas"),
        ("talib-binary", "talib"),  # 使用二进制版本避免编译问题
    ]
    
    # 可选的包列表
    optional_packages = [
        ("pyfolio", "pyfolio"),
        ("matplotlib", "matplotlib"),
        ("seaborn", "seaborn"),
        ("jupyter", "jupyter"),
    ]
    
    print("\n检查必需依赖...")
    missing_required = []
    for pip_name, import_name in required_packages:
        if check_package(import_name):
            print(f"✓ {import_name} 已安装")
        else:
            print(f"✗ {import_name} 未安装")
            missing_required.append(pip_name)
    
    print("\n检查可选依赖...")
    missing_optional = []
    for pip_name, import_name in optional_packages:
        if check_package(import_name):
            print(f"✓ {import_name} 已安装")
        else:
            print(f"✗ {import_name} 未安装")
            missing_optional.append(pip_name)
    
    # 安装缺失的必需包
    if missing_required:
        print(f"\n安装缺失的必需依赖: {', '.join(missing_required)}")
        for package in missing_required:
            if not install_package(package):
                print(f"错误: 无法安装必需依赖 {package}")
                return False
    
    # 询问是否安装可选包
    if missing_optional:
        print(f"\n发现缺失的可选依赖: {', '.join(missing_optional)}")
        response = input("是否安装可选依赖？(y/n): ").lower().strip()
        if response in ['y', 'yes', '是']:
            for package in missing_optional:
                install_package(package)
    
    print("\n" + "=" * 60)
    print("安装完成！")
    print("=" * 60)
    
    # 检查富途OpenD
    print("\n下一步操作:")
    print("1. 下载并安装富途牛牛客户端")
    print("2. 启动富途OpenD程序")
    print("3. 确保OpenD在 127.0.0.1:11111 端口运行")
    print("4. 运行回测演示: python demos/cta_hk_bt/runBT.py")
    print("5. 运行实盘演示: python demos/cta_hk_live/run.py")
    
    # 创建必要的目录
    dirs_to_create = [
        "demos/cta_hk_bt/logs",
        "demos/cta_hk_bt/outputs_bt",
        "demos/cta_hk_live/logs",
        "demos/storage"
    ]
    
    print("\n创建必要目录...")
    for dir_path in dirs_to_create:
        try:
            os.makedirs(dir_path, exist_ok=True)
            print(f"✓ 创建目录: {dir_path}")
        except Exception as e:
            print(f"✗ 创建目录失败 {dir_path}: {e}")
    
    print("\n富途OpenAPI支持安装完成！")
    return True

if __name__ == "__main__":
    try:
        success = main()
        if success:
            print("\n安装成功！现在可以使用港美股交易功能了。")
        else:
            print("\n安装过程中出现错误，请检查网络连接和权限设置。")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n安装被用户中断。")
        sys.exit(1)
    except Exception as e:
        print(f"\n安装过程中发生未知错误: {e}")
        sys.exit(1)