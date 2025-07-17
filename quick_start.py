#!/usr/bin/env python3
"""
快速启动脚本 - ArXiv Digest with SiliconFlow API
自动化设置和测试流程
"""

import os
import sys
import subprocess
from pathlib import Path


def print_banner():
    """打印横幅"""
    banner = """
    ╔══════════════════════════════════════════════════════════════╗
    ║                   ArXiv Digest Enhanced                     ║
    ║              Analog Circuit Design & Optimization           ║
    ║                  with SiliconFlow API                       ║
    ╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)


def check_environment():
    """检查环境配置"""
    print("🔍 检查环境配置...")

    required_env_vars = ["CUSTOM_API_KEY"]
    missing_vars = []

    for var in required_env_vars:
        if not os.environ.get(var):
            missing_vars.append(var)

    if missing_vars:
        print(f"❌ 缺少环境变量: {', '.join(missing_vars)}")
        print("\n请设置以下环境变量：")
        for var in missing_vars:
            if var == "CUSTOM_API_KEY":
                print(f"  export {var}='your-siliconflow-api-key'")
        print("\n或者创建 .env 文件：")
        print("  CUSTOM_API_KEY=your-siliconflow-api-key")
        return False

    print("✅ API环境变量检查通过")

    # 检查邮件配置（可选）
    mail_connection = os.environ.get("MAIL_CONNECTION")
    mail_username = os.environ.get("MAIL_USERNAME")
    mail_password = os.environ.get("MAIL_PASSWORD")
    from_email = os.environ.get("FROM_EMAIL")
    to_email = os.environ.get("TO_EMAIL")
    sendgrid_key = os.environ.get("SENDGRID_API_KEY")

    has_email_config = bool(sendgrid_key or mail_connection or (mail_username and mail_password))
    has_email_addresses = bool(from_email and to_email)

    if has_email_config and has_email_addresses:
        if sendgrid_key:
            print("✅ SendGrid邮件配置检查通过")
        elif mail_connection:
            print("✅ SMTP连接字符串配置检查通过")
        elif mail_username and mail_password:
            print("✅ SMTP用户密码配置检查通过")
    else:
        print("⚠️  未检测到邮件配置（可选功能）")
        print("   如需邮件功能，请参考SMTP配置指南")

    return True


def check_files():
    """检查必要文件"""
    print("📁 检查必要文件...")

    required_files = [
        "config.yaml",
        "src/action.py",
        "src/relevancy.py",
        "src/utils.py",
        "src/relevancy_prompt.txt",
        "test_api.py",
        "test_smtp.py"
    ]

    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)

    if missing_files:
        print(f"❌ 缺少文件: {', '.join(missing_files)}")
        return False

    print("✅ 文件检查通过")
    return True


def install_dependencies():
    """安装依赖"""
    print("📦 检查并安装依赖...")

    try:
        import yaml
        import requests
        import tqdm
        import openai
        print("✅ 核心依赖已安装")
        return True
    except ImportError as e:
        print(f"❌ 缺少依赖: {e}")
        print("正在安装依赖...")

        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
            print("✅ 依赖安装完成")
            return True
        except subprocess.CalledProcessError:
            print("❌ 依赖安装失败")
            return False


def run_api_test():
    """运行API测试"""
    print("🧪 运行API测试...")

    try:
        result = subprocess.run([sys.executable, "test_api.py"],
                                capture_output=True, text=True, timeout=120)

        if result.returncode == 0:
            print("✅ API测试通过")
            # 显示测试输出的关键信息
            lines = result.stdout.split('\n')
            for line in lines:
                if any(keyword in line for keyword in ['✅', '❌', '🤖', '📊']):
                    print(f"  {line}")
            return True
        else:
            print("❌ API测试失败")
            print("错误输出:")
            print(result.stderr)
            return False

    except subprocess.TimeoutExpired:
        print("❌ API测试超时")
        return False
    except Exception as e:
        print(f"❌ API测试错误: {e}")
        return False


def run_full_digest():
    """运行完整的digest生成"""
    print("🚀 运行完整的ArXiv Digest生成...")

    try:
        result = subprocess.run([sys.executable, "src/action.py", "--config", "config.yaml"],
                                capture_output=True, text=True, timeout=600)  # 10分钟超时

        if result.returncode == 0:
            print("✅ Digest生成成功!")

            # 检查输出文件
            if Path("digest.html").exists():
                file_size = Path("digest.html").stat().st_size
                print(f"📄 生成的HTML文件大小: {file_size} bytes")
                print("📍 文件位置: digest.html")

                # 显示一些运行统计
                lines = result.stdout.split('\n')
                for line in lines:
                    if any(keyword in line for keyword in ['Total papers', 'Found', 'Request']):
                        print(f"  {line}")

                return True
            else:
                print("❌ HTML文件未生成")
                return False
        else:
            print("❌ Digest生成失败")
            print("错误输出:")
            print(result.stderr[:1000])  # 只显示前1000个字符
            return False

    except subprocess.TimeoutExpired:
        print("❌ Digest生成超时（可能论文太多或API响应慢）")
        return False
    except Exception as e:
        print(f"❌ Digest生成错误: {e}")
        return False


def test_smtp_if_configured():
    """如果配置了SMTP，进行测试"""
    mail_connection = os.environ.get("MAIL_CONNECTION")
    mail_username = os.environ.get("MAIL_USERNAME")
    mail_password = os.environ.get("MAIL_PASSWORD")
    from_email = os.environ.get("FROM_EMAIL")
    to_email = os.environ.get("TO_EMAIL")

    has_smtp_config = bool(mail_connection or (mail_username and mail_password))
    has_email_addresses = bool(from_email and to_email)

    if not has_smtp_config or not has_email_addresses:
        return True  # 如果没配置SMTP，跳过测试

    print("📧 检测到SMTP配置，进行邮件测试...")

    try:
        result = subprocess.run([sys.executable, "test_smtp.py"],
                                capture_output=True, text=True, timeout=60)

        if result.returncode == 0:
            print("✅ SMTP配置测试通过")
            # 显示关键信息
            lines = result.stdout.split('\n')
            for line in lines:
                if any(keyword in line for keyword in ['✅', '❌', '📧', '🖥️']):
                    print(f"  {line}")
            return True
        else:
            print("⚠️ SMTP配置测试失败，但可以继续运行（邮件功能不可用）")
            print("如需邮件功能，请检查SMTP配置")
            return True  # 不阻止主要功能

    except subprocess.TimeoutExpired:
        print("⚠️ SMTP测试超时，跳过邮件功能")
        return True
    except Exception as e:
        print(f"⚠️ SMTP测试错误: {e}")
        return True


def main():
    """主函数"""
    print_banner()

    # 步骤1: 检查环境
    if not check_environment():
        return False

    # 步骤2: 检查文件
    if not check_files():
        print("\n💡 请确保已经替换了所有增强版本的文件")
        return False

    # 步骤3: 安装依赖
    if not install_dependencies():
        return False

    print("\n" + "=" * 60)

    # 步骤4: API测试
    if not run_api_test():
        print("\n💡 API测试失败，请检查:")
        print("  1. API密钥是否正确")
        print("  2. 网络连接是否正常")
        print("  3. SiliconFlow服务是否可用")
        return False

    print("\n" + "=" * 60)

    # 步骤5: SMTP测试（如果配置了）
    test_smtp_if_configured()

    print("\n" + "=" * 60)

    # 步骤6: 询问是否运行完整digest
    response = input("\n🤔 测试通过！是否运行完整的ArXiv Digest? (y/n): ").lower().strip()

    if response in ['y', 'yes', '是', '好']:
        if run_full_digest():
            print("\n🎉 恭喜！ArXiv Digest设置和测试完成！")
            print("\n📋 接下来您可以:")
            print("  1. 打开 digest.html 查看结果")
            print("  2. 检查邮箱是否收到邮件（如果配置了）")
            print("  3. 修改 config.yaml 调整配置")
            print("  4. 设置定时任务自动运行")
            print("\n📧 邮件功能配置:")
            print("  - 参考 'SMTP邮件配置指南' 设置邮件发送")
            print("  - 运行 'python test_smtp.py' 测试邮件配置")
            return True
        else:
            print("\n⚠️ 完整运行失败，但API配置正确")
            print("建议检查论文数据或调整配置参数")
            return False
    else:
        print("\n✅ 设置完成！您可以稍后手动运行:")
        print("  python src/action.py --config config.yaml")
        print("\n📧 如需配置邮件功能:")
        print("  python test_smtp.py  # 测试SMTP配置")
        return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)