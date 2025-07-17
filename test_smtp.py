#!/usr/bin/env python3
"""
SMTP邮件发送测试脚本（支持多收件人）
用于测试邮件配置和发送digest.html文件
"""

import os
import sys
import smtplib
import ssl
import re
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from urllib.parse import urlparse
from pathlib import Path
from datetime import date
from dotenv import load_dotenv
from typing import List, Union


def parse_email_addresses(email_string: str) -> List[str]:
    """
    解析邮箱地址字符串，支持多种分隔符
    """
    if not email_string:
        return []

    # 用正则表达式分割，支持逗号、分号、空格作为分隔符
    emails = re.split(r'[,;\s]+', email_string.strip())

    # 过滤空字符串并去除前后空格
    emails = [email.strip() for email in emails if email.strip()]

    # 简单的邮箱格式验证
    valid_emails = []
    email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')

    for email in emails:
        if email_pattern.match(email):
            valid_emails.append(email)
        else:
            print(f"⚠️ 跳过无效邮箱地址: {email}")

    return valid_emails


def get_email_config():
    """
    获取邮件配置
    """
    config = {
        'from_email': os.environ.get("FROM_EMAIL"),
        'to_emails': os.environ.get("TO_EMAIL"),  # 现在支持多个邮箱
        'sendgrid_key': os.environ.get("SENDGRID_API_KEY"),
        'mail_connection': os.environ.get("MAIL_CONNECTION"),
        'mail_username': os.environ.get("MAIL_USERNAME"),
        'mail_password': os.environ.get("MAIL_PASSWORD"),
    }
    return config


def send_email_smtp(subject: str, html_content: str, from_email: str,
                    to_emails: Union[str, List[str]], mail_connection=None,
                    mail_username=None, mail_password=None):
    """
    使用SMTP发送邮件到多个收件人
    """

    # 处理收件人邮箱
    if isinstance(to_emails, str):
        recipient_list = parse_email_addresses(to_emails)
    elif isinstance(to_emails, list):
        recipient_list = to_emails
    else:
        raise ValueError("to_emails必须是字符串或列表")

    if not recipient_list:
        print("❌ 没有有效的收件人邮箱地址")
        return False

    print(f"📧 准备发送给 {len(recipient_list)} 个收件人:")
    for i, email in enumerate(recipient_list, 1):
        print(f"  {i}. {email}")

    # 解析连接详情
    if mail_connection:
        parsed = urlparse(mail_connection)
        smtp_server = parsed.hostname
        smtp_port = parsed.port
        smtp_username = parsed.username
        smtp_password = parsed.password
        use_tls = parsed.scheme == 'smtp+starttls'
        use_ssl = parsed.scheme == 'smtps'
    elif mail_username and mail_password:
        smtp_server = "smtp.gmail.com"
        smtp_port = 587
        smtp_username = mail_username
        smtp_password = mail_password
        use_tls = True
        use_ssl = False
    else:
        raise ValueError("必须提供 MAIL_CONNECTION 或 MAIL_USERNAME+MAIL_PASSWORD")

    successful_sends = []
    failed_sends = []

    try:
        # 创建SMTP会话
        if use_ssl:
            context = ssl.create_default_context()
            server = smtplib.SMTP_SSL(smtp_server, smtp_port, context=context)
        else:
            server = smtplib.SMTP(smtp_server, smtp_port)
            if use_tls:
                context = ssl.create_default_context()
                server.starttls(context=context)

        # 登录
        server.login(smtp_username, smtp_password)
        print("✅ SMTP服务器连接成功")

        # 为每个收件人发送邮件
        for recipient in recipient_list:
            try:
                # 创建邮件消息
                message = MIMEMultipart("alternative")
                message["Subject"] = subject
                message["From"] = from_email
                message["To"] = recipient

                # 添加HTML内容
                html_part = MIMEText(html_content, "html", "utf-8")
                message.attach(html_part)

                # 发送邮件
                server.sendmail(from_email, [recipient], message.as_string())
                successful_sends.append(recipient)
                print(f"✅ 成功发送到: {recipient}")

            except Exception as e:
                failed_sends.append(recipient)
                print(f"❌ 发送失败 {recipient}: {e}")

        server.quit()

    except Exception as e:
        print(f"❌ SMTP连接失败: {e}")
        failed_sends = recipient_list.copy()

    # 打印发送结果统计
    print(f"\n📊 发送结果统计:")
    print(f"  ✅ 成功: {len(successful_sends)} 个")
    print(f"  ❌ 失败: {len(failed_sends)} 个")

    if successful_sends:
        print(f"  成功发送给: {', '.join(successful_sends)}")

    if failed_sends:
        print(f"  发送失败: {', '.join(failed_sends)}")

    return len(successful_sends) > 0


def check_smtp_config():
    """
    检查SMTP配置
    """
    print("🔍 检查SMTP邮件配置...")

    config = get_email_config()

    # 检查基本邮件地址
    if not config['from_email']:
        print("❌ 缺少 FROM_EMAIL 环境变量")
        return False, config

    if not config['to_emails']:
        print("❌ 缺少 TO_EMAIL 环境变量")
        return False, config

    print(f"📧 发件人: {config['from_email']}")

    # 解析并显示收件人
    recipients = parse_email_addresses(config['to_emails'])
    if not recipients:
        print("❌ 没有有效的收件人邮箱地址")
        return False, config

    print(f"📧 收件人 ({len(recipients)} 个):")
    for i, email in enumerate(recipients, 1):
        print(f"  {i}. {email}")

    # 检查发送方式配置
    has_sendgrid = bool(config['sendgrid_key'])
    has_smtp_connection = bool(config['mail_connection'])
    has_smtp_credentials = bool(config['mail_username'] and config['mail_password'])

    if has_sendgrid:
        print("🖥️ 检测到SendGrid配置")
        print("ℹ️  注意: 此测试脚本专门测试SMTP，不测试SendGrid")
        print("ℹ️  如需测试SendGrid，请运行完整的 action.py")

    if has_smtp_connection:
        print("🖥️ 检测到SMTP连接字符串配置")
        parsed = urlparse(config['mail_connection'])
        print(f"   服务器: {parsed.hostname}:{parsed.port}")
        print(f"   协议: {parsed.scheme}")
        return True, config

    if has_smtp_credentials:
        print("🖥️ 检测到SMTP用户名密码配置")
        print(f"   用户名: {config['mail_username']}")
        print("   默认使用Gmail SMTP服务器")
        return True, config

    if not (has_smtp_connection or has_smtp_credentials):
        print("❌ 未检测到SMTP配置")
        print("请设置以下环境变量之一:")
        print("  方式1 - SMTP连接字符串:")
        print("    MAIL_CONNECTION=smtp://username:password@smtp.example.com:587")
        print("    MAIL_CONNECTION=smtp+starttls://username:password@smtp.example.com:587")
        print("  方式2 - Gmail用户名密码:")
        print("    MAIL_USERNAME=your-email@gmail.com")
        print("    MAIL_PASSWORD=your-app-password")
        return False, config

    return True, config


def load_digest_html():
    """
    加载digest.html文件内容
    """
    digest_path = Path("digest.html")

    if digest_path.exists():
        print(f"📄 找到digest.html文件 (大小: {digest_path.stat().st_size} bytes)")
        try:
            with open(digest_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return content, True
        except Exception as e:
            print(f"❌ 读取digest.html失败: {e}")
            return None, False
    else:
        print("📄 未找到digest.html文件，将发送测试邮件")
        return None, False


def create_test_email():
    """
    创建测试邮件内容
    """
    return '''
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body { font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; }
            .header { background-color: #2c3e50; color: white; padding: 20px; text-align: center; }
            .content { padding: 20px; background-color: #f8f9fa; }
            .success { color: #27ae60; font-weight: bold; }
            .info { background-color: #e8f4f8; padding: 15px; border-left: 4px solid #3498db; margin: 10px 0; }
            .multi-recipient { background-color: #fff3cd; padding: 15px; border-left: 4px solid #f39c12; margin: 10px 0; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🧪 SMTP多收件人测试</h1>
        </div>
        <div class="content">
            <p class="success">✅ 恭喜！您的SMTP多收件人邮件配置测试成功！</p>

            <div class="multi-recipient">
                <h3>📧 多收件人功能</h3>
                <p>此邮件验证了多收件人发送功能正常工作。每个收件人都会收到单独的邮件副本。</p>
            </div>

            <div class="info">
                <h3>📧 测试信息</h3>
                <p><strong>测试时间:</strong> ''' + date.today().strftime("%Y年%m月%d日") + '''</p>
                <p><strong>测试目的:</strong> 验证SMTP多收件人邮件发送配置</p>
                <p><strong>发送方式:</strong> SMTP协议（多收件人支持）</p>
            </div>

            <h3>🚀 下一步操作</h3>
            <ol>
                <li>运行 <code>python src/action.py --config config.yaml</code> 生成完整digest</li>
                <li>或者运行 <code>python quick_start.py</code> 进行完整测试</li>
                <li>检查生成的 <code>digest.html</code> 文件</li>
                <li>设置定时任务自动运行</li>
            </ol>

            <div class="info">
                <h3>📝 多收件人配置示例</h3>
                <p>在环境变量或 .env 文件中设置:</p>
                <pre>TO_EMAIL=user1@example.com,user2@example.com,user3@example.com</pre>
                <p>支持的分隔符: 逗号(,)、分号(;)、空格</p>
            </div>

            <p><em>此邮件由ArXiv Digest SMTP多收件人测试脚本自动生成</em></p>
        </div>
    </body>
    </html>
    '''


def test_smtp_sending():
    """
    测试SMTP邮件发送
    """
    print("🚀 开始SMTP多收件人邮件发送测试...")
    print("=" * 50)

    # 加载环境变量
    load_dotenv()

    # 检查配置
    config_ok, config = check_smtp_config()
    if not config_ok:
        return False

    print("\n" + "=" * 50)

    # 尝试加载digest.html
    html_content, has_digest = load_digest_html()

    if not has_digest:
        # 使用测试邮件内容
        html_content = create_test_email()
        subject = "ArXiv Digest - SMTP多收件人配置测试成功"
        print("📧 使用测试邮件内容")
    else:
        subject = date.today().strftime("ArXiv Digest - %Y年%m月%d日")
        print("📧 使用实际的digest.html内容")

    print(f"📧 邮件主题: {subject}")
    print(f"📧 内容长度: {len(html_content)} 字符")

    print("\n" + "=" * 50)
    print("📤 正在发送邮件...")

    # 发送邮件
    try:
        success = send_email_smtp(
            subject=subject,
            html_content=html_content,
            from_email=config['from_email'],
            to_emails=config['to_emails'],  # 现在支持多个收件人
            mail_connection=config['mail_connection'],
            mail_username=config['mail_username'],
            mail_password=config['mail_password']
        )

        if success:
            print("\n🎉 SMTP多收件人邮件发送测试成功!")
            recipients = parse_email_addresses(config['to_emails'])
            print(f"📧 请检查以下邮箱是否收到邮件:")
            for i, email in enumerate(recipients, 1):
                print(f"  {i}. {email}")

            if has_digest:
                print("📄 已发送实际的ArXiv Digest内容")
            else:
                print("🧪 已发送测试邮件内容")
            return True
        else:
            print("\n❌ SMTP邮件发送测试失败")
            return False

    except Exception as e:
        print(f"\n❌ 邮件发送过程中出现错误: {e}")
        return False


def print_troubleshooting_tips():
    """
    打印故障排除提示
    """
    print("\n" + "=" * 50)
    print("🔧 故障排除提示:")
    print()
    print("如果邮件发送失败，请检查:")
    print("1. 网络连接是否正常")
    print("2. SMTP服务器地址和端口是否正确")
    print("3. 用户名和密码是否正确")
    print("4. 是否需要使用应用专用密码（如Gmail）")
    print("5. 防火墙是否阻止了SMTP端口")
    print("6. 收件人邮箱地址格式是否正确")
    print()
    print("多收件人配置示例:")
    print("TO_EMAIL=user1@gmail.com,user2@outlook.com,user3@company.com")
    print("TO_EMAIL=\"user1@gmail.com; user2@outlook.com; user3@company.com\"")
    print("TO_EMAIL=\"user1@gmail.com user2@outlook.com user3@company.com\"")


def main():
    """
    主函数
    """
    print("📧 ArXiv Digest - SMTP多收件人邮件发送测试")
    print("=" * 50)

    success = test_smtp_sending()

    if not success:
        print_troubleshooting_tips()

    print("\n" + "=" * 50)
    print("💡 测试完成!")

    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)