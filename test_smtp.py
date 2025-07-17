#!/usr/bin/env python3
"""
SMTP邮件发送测试脚本
用于测试邮件配置和发送digest.html文件
"""

import os
import sys
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from urllib.parse import urlparse
from pathlib import Path
from datetime import date
from dotenv import load_dotenv


def get_email_config():
    """
    获取邮件配置
    """
    config = {
        'from_email': os.environ.get("FROM_EMAIL"),
        'to_email': os.environ.get("TO_EMAIL"),
        'sendgrid_key': os.environ.get("SENDGRID_API_KEY"),
        'mail_connection': os.environ.get("MAIL_CONNECTION"),
        'mail_username': os.environ.get("MAIL_USERNAME"),
        'mail_password': os.environ.get("MAIL_PASSWORD"),
    }
    return config


def send_email_smtp(subject, html_content, from_email, to_email, mail_connection=None, mail_username=None,
                    mail_password=None):
    """
    使用SMTP发送邮件
    """
    # 解析连接详情
    if mail_connection:
        # 解析连接字符串如 smtp://user:pass@server:port
        parsed = urlparse(mail_connection)
        smtp_server = parsed.hostname
        smtp_port = parsed.port
        smtp_username = parsed.username
        smtp_password = parsed.password
        use_tls = parsed.scheme == 'smtp+starttls'
        use_ssl = parsed.scheme == 'smtps'
    elif mail_username and mail_password:
        # Gmail默认配置或手动配置
        smtp_server = "smtp.gmail.com"
        smtp_port = 587
        smtp_username = mail_username
        smtp_password = mail_password
        use_tls = True
        use_ssl = False
    else:
        raise ValueError("必须提供 MAIL_CONNECTION 或 MAIL_USERNAME+MAIL_PASSWORD")

    # 创建消息
    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = from_email
    message["To"] = to_email

    # 添加HTML内容
    html_part = MIMEText(html_content, "html", "utf-8")
    message.attach(html_part)

    try:
        # 创建SMTP会话
        if use_ssl:
            # SSL (通常端口465)
            context = ssl.create_default_context()
            server = smtplib.SMTP_SSL(smtp_server, smtp_port, context=context)
        else:
            # STARTTLS (通常端口587) 或普通 (端口25)
            server = smtplib.SMTP(smtp_server, smtp_port)
            if use_tls:
                context = ssl.create_default_context()
                server.starttls(context=context)

        # 登录并发送
        server.login(smtp_username, smtp_password)
        server.sendmail(from_email, to_email, message.as_string())
        server.quit()

        print(f"✅ SMTP邮件发送成功: {from_email} -> {to_email}")
        return True

    except Exception as e:
        print(f"❌ SMTP邮件发送失败: {e}")
        return False


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

    if not config['to_email']:
        print("❌ 缺少 TO_EMAIL 环境变量")
        return False, config

    print(f"📧 发件人: {config['from_email']}")
    print(f"📧 收件人: {config['to_email']}")

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
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🧪 SMTP邮件配置测试</h1>
        </div>
        <div class="content">
            <p class="success">✅ 恭喜！您的SMTP邮件配置测试成功！</p>

            <div class="info">
                <h3>📧 测试信息</h3>
                <p><strong>测试时间:</strong> ''' + date.today().strftime("%Y年%m月%d日") + '''</p>
                <p><strong>测试目的:</strong> 验证SMTP邮件发送配置</p>
                <p><strong>发送方式:</strong> SMTP协议</p>
            </div>

            <h3>🚀 下一步操作</h3>
            <ol>
                <li>运行 <code>python src/action.py --config config.yaml</code> 生成完整digest</li>
                <li>或者运行 <code>python quick_start.py</code> 进行完整测试</li>
                <li>检查生成的 <code>digest.html</code> 文件</li>
                <li>设置定时任务自动运行</li>
            </ol>

            <div class="info">
                <h3>⚙️ ArXiv Digest配置</h3>
                <p>如需调整论文推荐的配置，请编辑 <code>config.yaml</code> 文件：</p>
                <ul>
                    <li>修改 <code>topics</code> 选择感兴趣的研究领域</li>
                    <li>调整 <code>categories</code> 细化分类</li>
                    <li>更新 <code>interest</code> 描述您的具体研究兴趣</li>
                    <li>调整 <code>threshold</code> 控制相关性阈值</li>
                </ul>
            </div>

            <p><em>此邮件由ArXiv Digest SMTP测试脚本自动生成</em></p>
        </div>
    </body>
    </html>
    '''


def test_smtp_sending():
    """
    测试SMTP邮件发送
    """
    print("🚀 开始SMTP邮件发送测试...")
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
        subject = "ArXiv Digest - SMTP配置测试成功"
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
            to_email=config['to_email'],
            mail_connection=config['mail_connection'],
            mail_username=config['mail_username'],
            mail_password=config['mail_password']
        )

        if success:
            print("\n🎉 SMTP邮件发送测试成功!")
            print(f"📧 请检查邮箱 {config['to_email']} 是否收到邮件")
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
    print()
    print("常用SMTP配置示例:")
    print("Gmail:")
    print("  MAIL_CONNECTION=smtp+starttls://user:pass@smtp.gmail.com:587")
    print("  或使用 MAIL_USERNAME + MAIL_PASSWORD")
    print()
    print("Outlook/Hotmail:")
    print("  MAIL_CONNECTION=smtp+starttls://user:pass@smtp-mail.outlook.com:587")
    print()
    print("QQ邮箱:")
    print("  MAIL_CONNECTION=smtp+starttls://user:pass@smtp.qq.com:587")
    print()
    print("163邮箱:")
    print("  MAIL_CONNECTION=smtp+starttls://user:pass@smtp.163.com:587")


def main():
    """
    主函数
    """
    print("📧 ArXiv Digest - SMTP邮件发送测试")
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