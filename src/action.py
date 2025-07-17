from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from urllib.parse import urlparse

from datetime import date

import argparse
import yaml
import os
from dotenv import load_dotenv
import openai
from relevancy import generate_relevance_score, process_subject_fields
from download_new_papers import get_papers

import re
from typing import List, Union

# Hackathon quality code. Don't judge too harshly.
# Feel free to submit pull requests to improve the code.

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


topics = {
    "Physics": "",
    "Mathematics": "math",
    "Computer Science": "cs",
    "Quantitative Biology": "q-bio",
    "Quantitative Finance": "q-fin",
    "Statistics": "stat",
    "Electrical Engineering and Systems Science": "eess",
    "Economics": "econ",
}

physics_topics = {
    "Astrophysics": "astro-ph",
    "Condensed Matter": "cond-mat",
    "General Relativity and Quantum Cosmology": "gr-qc",
    "High Energy Physics - Experiment": "hep-ex",
    "High Energy Physics - Lattice": "hep-lat",
    "High Energy Physics - Phenomenology": "hep-ph",
    "High Energy Physics - Theory": "hep-th",
    "Mathematical Physics": "math-ph",
    "Nonlinear Sciences": "nlin",
    "Nuclear Experiment": "nucl-ex",
    "Nuclear Theory": "nucl-th",
    "Physics": "physics",
    "Quantum Physics": "quant-ph",
}

# TODO: surely theres a better way
category_map = {
    "Astrophysics": [
        "Astrophysics of Galaxies",
        "Cosmology and Nongalactic Astrophysics",
        "Earth and Planetary Astrophysics",
        "High Energy Astrophysical Phenomena",
        "Instrumentation and Methods for Astrophysics",
        "Solar and Stellar Astrophysics",
    ],
    "Condensed Matter": [
        "Disordered Systems and Neural Networks",
        "Materials Science",
        "Mesoscale and Nanoscale Physics",
        "Other Condensed Matter",
        "Quantum Gases",
        "Soft Condensed Matter",
        "Statistical Mechanics",
        "Strongly Correlated Electrons",
        "Superconductivity",
    ],
    "General Relativity and Quantum Cosmology": ["None"],
    "High Energy Physics - Experiment": ["None"],
    "High Energy Physics - Lattice": ["None"],
    "High Energy Physics - Phenomenology": ["None"],
    "High Energy Physics - Theory": ["None"],
    "Mathematical Physics": ["None"],
    "Nonlinear Sciences": [
        "Adaptation and Self-Organizing Systems",
        "Cellular Automata and Lattice Gases",
        "Chaotic Dynamics",
        "Exactly Solvable and Integrable Systems",
        "Pattern Formation and Solitons",
    ],
    "Nuclear Experiment": ["None"],
    "Nuclear Theory": ["None"],
    "Physics": [
        "Accelerator Physics",
        "Applied Physics",
        "Atmospheric and Oceanic Physics",
        "Atomic and Molecular Clusters",
        "Atomic Physics",
        "Biological Physics",
        "Chemical Physics",
        "Classical Physics",
        "Computational Physics",
        "Data Analysis, Statistics and Probability",
        "Fluid Dynamics",
        "General Physics",
        "Geophysics",
        "History and Philosophy of Physics",
        "Instrumentation and Detectors",
        "Medical Physics",
        "Optics",
        "Physics and Society",
        "Physics Education",
        "Plasma Physics",
        "Popular Physics",
        "Space Physics",
    ],
    "Quantum Physics": ["None"],
    "Mathematics": [
        "Algebraic Geometry",
        "Algebraic Topology",
        "Analysis of PDEs",
        "Category Theory",
        "Classical Analysis and ODEs",
        "Combinatorics",
        "Commutative Algebra",
        "Complex Variables",
        "Differential Geometry",
        "Dynamical Systems",
        "Functional Analysis",
        "General Mathematics",
        "General Topology",
        "Geometric Topology",
        "Group Theory",
        "History and Overview",
        "Information Theory",
        "K-Theory and Homology",
        "Logic",
        "Mathematical Physics",
        "Metric Geometry",
        "Number Theory",
        "Numerical Analysis",
        "Operator Algebras",
        "Optimization and Control",
        "Probability",
        "Quantum Algebra",
        "Representation Theory",
        "Rings and Algebras",
        "Spectral Theory",
        "Statistics Theory",
        "Symplectic Geometry",
    ],
    "Computer Science": [
        "Artificial Intelligence",
        "Computation and Language",
        "Computational Complexity",
        "Computational Engineering, Finance, and Science",
        "Computational Geometry",
        "Computer Science and Game Theory",
        "Computer Vision and Pattern Recognition",
        "Computers and Society",
        "Cryptography and Security",
        "Data Structures and Algorithms",
        "Databases",
        "Digital Libraries",
        "Discrete Mathematics",
        "Distributed, Parallel, and Cluster Computing",
        "Emerging Technologies",
        "Formal Languages and Automata Theory",
        "General Literature",
        "Graphics",
        "Hardware Architecture",
        "Human-Computer Interaction",
        "Information Retrieval",
        "Information Theory",
        "Logic in Computer Science",
        "Machine Learning",
        "Mathematical Software",
        "Multiagent Systems",
        "Multimedia",
        "Networking and Internet Architecture",
        "Neural and Evolutionary Computing",
        "Numerical Analysis",
        "Operating Systems",
        "Other Computer Science",
        "Performance",
        "Programming Languages",
        "Robotics",
        "Social and Information Networks",
        "Software Engineering",
        "Sound",
        "Symbolic Computation",
        "Systems and Control",
    ],
    "Quantitative Biology": [
        "Biomolecules",
        "Cell Behavior",
        "Genomics",
        "Molecular Networks",
        "Neurons and Cognition",
        "Other Quantitative Biology",
        "Populations and Evolution",
        "Quantitative Methods",
        "Subcellular Processes",
        "Tissues and Organs",
    ],
    "Quantitative Finance": [
        "Computational Finance",
        "Economics",
        "General Finance",
        "Mathematical Finance",
        "Portfolio Management",
        "Pricing of Securities",
        "Risk Management",
        "Statistical Finance",
        "Trading and Market Microstructure",
    ],
    "Statistics": [
        "Applications",
        "Computation",
        "Machine Learning",
        "Methodology",
        "Other Statistics",
        "Statistics Theory",
    ],
    "Electrical Engineering and Systems Science": [
        "Audio and Speech Processing",
        "Image and Video Processing",
        "Signal Processing",
        "Systems and Control",
    ],
    "Economics": ["Econometrics", "General Economics", "Theoretical Economics"],
}


def get_papers_from_multiple_topics(topics_config, categories_config, test_mode=False):
    """
    Enhanced function to get papers from multiple topics
    topics_config: list of topic names or single topic name
    categories_config: list of categories or single category
    test_mode: if True, limit to 1 paper for testing
    """
    all_papers = []

    # If single topic provided, convert to list
    if isinstance(topics_config, str):
        topics_config = [topics_config]

    # If single category provided, convert to list
    if isinstance(categories_config, str):
        categories_config = [categories_config]

    for topic in topics_config:
        print(f"Fetching papers from topic: {topic}")

        if topic == "Physics":
            raise RuntimeError("You must choose a physics subtopic.")
        elif topic in physics_topics:
            abbr = physics_topics[topic]
        elif topic in topics:
            abbr = topics[topic]
        else:
            raise RuntimeError(f"Invalid topic {topic}")

        # Get papers for this topic with limit if in test mode
        limit = 1 if test_mode else None
        topic_papers = get_papers(abbr, limit=limit)

        # Filter by categories if specified
        if categories_config:
            # Get valid categories for this topic
            valid_categories = category_map.get(topic, [])
            # Find intersection of requested categories and valid categories
            relevant_categories = [cat for cat in categories_config if cat in valid_categories]

            if relevant_categories:
                filtered_papers = [
                    paper for paper in topic_papers
                    if bool(set(process_subject_fields(paper["subjects"])) & set(relevant_categories))
                ]
                print(f"  Found {len(filtered_papers)} papers in categories {relevant_categories}")
                all_papers.extend(filtered_papers)
            else:
                print(f"  No matching categories found for topic {topic}")
        else:
            print(f"  Found {len(topic_papers)} papers (no category filter)")
            all_papers.extend(topic_papers)

        # In test mode, break after getting first paper
        if test_mode and all_papers:
            print(f"🧪 Test mode: Limited to {len(all_papers)} paper(s)")
            break

    print(f"Total papers collected: {len(all_papers)}")
    return all_papers


def generate_body_enhanced(config, test_mode=False):
    """
    Enhanced function to generate body supporting multiple topics and bilingual output
    test_mode: if True, limit to 1 paper for testing
    """
    # Support both single topic and multiple topics
    topics_to_search = config.get("topics", config.get("topic"))
    if isinstance(topics_to_search, str):
        topics_to_search = [topics_to_search]

    # Add EESS as secondary topic for analog circuit papers
    if "Computer Science" in topics_to_search and "Electrical Engineering and Systems Science" not in topics_to_search:
        topics_to_search.append("Electrical Engineering and Systems Science")
        print("Added 'Electrical Engineering and Systems Science' for comprehensive circuit design coverage")

    categories = config["categories"] if config["categories"] else []
    threshold = config["threshold"]
    interest = config["interest"]

    # Get API configuration
    api_config_dict = config.get("api_config", {})
    custom_api_config = None

    if api_config_dict.get("use_custom_api", False):
        from utils import CustomAPIConfig
        custom_api_config = CustomAPIConfig(
            api_url=api_config_dict.get("api_url"),
            api_key=os.environ.get("CUSTOM_API_KEY"),  # Get from environment
            model_name=api_config_dict.get("model_name"),
            use_custom_api=True
        )
        print(f"Using custom API: {custom_api_config.api_url}")
        print(f"Model: {custom_api_config.model_name}")

        if not custom_api_config.api_key:
            raise RuntimeError("CUSTOM_API_KEY environment variable not set")

    # Get papers from multiple topics with test mode support
    papers = get_papers_from_multiple_topics(topics_to_search, categories, test_mode=test_mode)

    if not papers:
        return "No papers found matching the specified criteria."

    # In test mode, add a notice
    test_notice = ""
    if test_mode:
        test_notice = f'''
        <div style="background-color: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; margin-bottom: 20px; border-radius: 5px;">
            <strong>🧪 测试模式</strong><br>
            此邮件为ArXiv Digest测试模式生成，仅包含 {len(papers)} 篇论文用于验证功能。<br>
            <strong>🧪 Test Mode</strong><br>
            This email is generated in ArXiv Digest test mode, containing only {len(papers)} paper(s) for verification.
        </div>
        '''

    if interest:
        # Determine model name based on API configuration
        model_name = api_config_dict.get("model_name",
                                         "gpt-3.5-turbo-16k") if custom_api_config else "gpt-3.5-turbo-16k"

        # In test mode, reduce num_paper_in_prompt to 1
        num_papers_in_prompt = 1 if test_mode else 8

        relevancy, hallucination = generate_relevance_score(
            papers,
            query={"interest": interest},
            threshold_score=threshold,
            num_paper_in_prompt=num_papers_in_prompt,
            model_name=model_name,
            custom_api_config=custom_api_config
        )

        # Enhanced HTML generation with bilingual support
        body_parts = []
        for paper in relevancy:
            paper_html = f'<div style="margin-bottom: 20px; border-bottom: 1px solid #eee; padding-bottom: 15px;">'
            paper_html += f'<h3><a href="{paper["main_page"]}" target="_blank">{paper["title"]}</a></h3>'
            paper_html += f'<p><strong>Authors:</strong> {paper["authors"]}</p>'
            paper_html += f'<p><strong>Relevancy Score:</strong> {paper["Relevancy score"]}/10</p>'

            # English reason
            if "Reasons for match" in paper:
                paper_html += f'<p><strong>Relevance (EN):</strong> {paper["Reasons for match"]}</p>'

            # Chinese reason
            if "中文原因" in paper:
                paper_html += f'<p><strong>相关性 (中文):</strong> {paper["中文原因"]}</p>'

            # Detailed English summary
            if "Detailed Summary" in paper:
                paper_html += f'<p><strong>Detailed Summary (EN):</strong> {paper["Detailed Summary"]}</p>'

            # Detailed Chinese summary
            if "详细总结" in paper:
                paper_html += f'<p><strong>详细总结 (中文):</strong> {paper["详细总结"]}</p>'

            paper_html += '</div>'
            body_parts.append(paper_html)

        body = "".join(body_parts)

        if hallucination:
            warning = '<div style="background-color: #fff3cd; border: 1px solid #ffeaa7; padding: 10px; margin-bottom: 20px; border-radius: 5px;">'
            warning += '<strong>Warning:</strong> The model may have hallucinated some papers. We have tried to remove them, but the scores may not be accurate.'
            warning += '</div>'
            body = warning + body
    else:
        # Simple listing without relevancy scoring
        body_parts = []
        for paper in papers:
            paper_html = f'<div style="margin-bottom: 15px;">'
            paper_html += f'<h4><a href="{paper["main_page"]}" target="_blank">{paper["title"]}</a></h4>'
            paper_html += f'<p><strong>Authors:</strong> {paper["authors"]}</p>'
            paper_html += '</div>'
            body_parts.append(paper_html)
        body = "".join(body_parts)

    # Add test notice if in test mode
    return test_notice + body


def send_email_smtp(subject, html_content, from_email, to_emails, mail_connection=None, mail_username=None,
                    mail_password=None):
    """
    Send email using SMTP to multiple recipients

    Args:
        subject: Email subject
        html_content: HTML content of the email
        from_email: Sender email address
        to_emails: Recipient email addresses (string or list)
        mail_connection: SMTP connection string
        mail_username: SMTP username
        mail_password: SMTP password
    """

    # 处理收件人邮箱
    if isinstance(to_emails, str):
        recipient_list = parse_email_addresses(to_emails)
    elif isinstance(to_emails, list):
        recipient_list = to_emails
    else:
        raise ValueError("to_emails must be string or list")

    if not recipient_list:
        print("❌ 没有有效的收件人邮箱地址")
        return False

    print(f"📧 准备发送给 {len(recipient_list)} 个收件人:")
    for i, email in enumerate(recipient_list, 1):
        print(f"  {i}. {email}")

    # Parse connection details
    if mail_connection:
        # Parse connection string like smtp://user:pass@server:port
        parsed = urlparse(mail_connection)
        smtp_server = parsed.hostname
        smtp_port = parsed.port
        smtp_username = parsed.username
        smtp_password = parsed.password
        use_tls = parsed.scheme == 'smtp+starttls'
        use_ssl = parsed.scheme == 'smtps'
    elif mail_username and mail_password:
        # Gmail defaults or manual configuration
        smtp_server = "smtp.gmail.com"
        smtp_port = 587
        smtp_username = mail_username
        smtp_password = mail_password
        use_tls = True
        use_ssl = False
    else:
        raise ValueError("Either MAIL_CONNECTION or MAIL_USERNAME+MAIL_PASSWORD must be provided")

    successful_sends = []
    failed_sends = []

    try:
        # Create SMTP session
        if use_ssl:
            # For SSL (usually port 465)
            context = ssl.create_default_context()
            server = smtplib.SMTP_SSL(smtp_server, smtp_port, context=context)
        else:
            # For STARTTLS (usually port 587) or plain (port 25)
            server = smtplib.SMTP(smtp_server, smtp_port)
            if use_tls:
                context = ssl.create_default_context()
                server.starttls(context=context)

        # Login
        server.login(smtp_username, smtp_password)
        print("✅ SMTP服务器连接成功")

        # Send to each recipient
        for recipient in recipient_list:
            try:
                # Create message
                message = MIMEMultipart("alternative")
                message["Subject"] = subject
                message["From"] = from_email
                message["To"] = recipient

                # Add HTML content
                html_part = MIMEText(html_content, "html", "utf-8")
                message.attach(html_part)

                # Send email
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

    # Print results
    print(f"\n📊 发送结果统计:")
    print(f"  ✅ 成功: {len(successful_sends)} 个")
    print(f"  ❌ 失败: {len(failed_sends)} 个")

    if successful_sends:
        print(f"  成功发送给: {', '.join(successful_sends)}")

    if failed_sends:
        print(f"  发送失败: {', '.join(failed_sends)}")

    return len(successful_sends) > 0


def get_email_config():
    """
    Get email configuration from environment variables

    Returns:
        dict: Email configuration
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


if __name__ == "__main__":
    # Load the .env file.
    load_dotenv()
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config", help="yaml config file to use", default="config.yaml"
    )
    parser.add_argument(
        "--test-mode", action="store_true", help="Test mode - process only 1 paper"
    )
    args = parser.parse_args()

    # Check for test mode from environment variable as well
    test_mode = args.test_mode or os.environ.get("ARXIV_DIGEST_TEST_MODE", "false").lower() == "true"

    if test_mode:
        print("🧪 测试模式已启用 - 只处理1篇论文")
        print("🧪 Test mode enabled - processing only 1 paper")

    with open(args.config, "r") as f:
        config = yaml.safe_load(f)

    # Check API configuration
    api_config = config.get("api_config", {})
    if api_config.get("use_custom_api", False):
        if "CUSTOM_API_KEY" not in os.environ:
            raise RuntimeError("CUSTOM_API_KEY environment variable not set for custom API")
        print(f"Using custom API: {api_config.get('api_url')}")
        print(f"Model: {api_config.get('model_name')}")
    else:
        if "OPENAI_API_KEY" not in os.environ:
            raise RuntimeError("OPENAI_API_KEY environment variable not set")
        openai.api_key = os.environ.get("OPENAI_API_KEY")
        print("Using OpenAI API")

    # Get email configuration
    email_config = get_email_config()

    # Use enhanced body generation with test mode support
    body = generate_body_enhanced(config, test_mode=test_mode)

    # Add CSS styling for better presentation
    mode_title = "测试模式 Test Mode" if test_mode else "Analog Circuit Design & Optimization"
    html_header = f'''
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: Arial, sans-serif; max-width: 1200px; margin: 0 auto; padding: 20px; }}
            h1 {{ color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }}
            h3 {{ color: #2980b9; }}
            a {{ color: #3498db; text-decoration: none; }}
            a:hover {{ text-decoration: underline; }}
            .paper {{ margin-bottom: 20px; border-bottom: 1px solid #eee; padding-bottom: 15px; }}
        </style>
    </head>
    <body>
        <h1>Personalized arXiv Digest - {mode_title}</h1>
        <h1>个性化arXiv文献摘要 - {mode_title}</h1>
    '''
    html_footer = '</body></html>'

    full_html = html_header + body + html_footer

    with open("digest.html", "w", encoding='utf-8') as f:
        f.write(full_html)

    # Email sending logic
    email_sent = False
    subject_suffix = " [测试模式 Test Mode]" if test_mode else ""
    subject = date.today().strftime(
        "Personalized arXiv Digest (Analog Circuit Design & Optimization), %d %b %Y") + subject_suffix

    if not email_config['from_email'] or not email_config['to_email']:
        print("📧 未配置发件人或收件人邮箱，跳过邮件发送")
    elif email_config['sendgrid_key']:
        # Use SendGrid
        print("📧 使用SendGrid发送邮件...")
        try:
            sg = SendGridAPIClient(api_key=email_config['sendgrid_key'])
            from_email_obj = Email(email_config['from_email'])
            to_email_obj = To(email_config['to_email'])
            content = Content("text/html", full_html)
            mail = Mail(from_email_obj, to_email_obj, subject, content)
            mail_json = mail.get()

            response = sg.client.mail.send.post(request_body=mail_json)
            if response.status_code >= 200 and response.status_code <= 300:
                mode_msg = "测试邮件" if test_mode else "邮件"
                print(f"✅ SendGrid{mode_msg}发送成功!")
                email_sent = True
            else:
                print(f"❌ SendGrid邮件发送失败: ({response.status_code}, {response.text})")
        except Exception as e:
            print(f"❌ SendGrid发送错误: {e}")

    elif email_config['mail_connection'] or (email_config['mail_username'] and email_config['mail_password']):
        # Use SMTP
        print("📧 使用SMTP发送邮件...")
        email_sent = send_email_smtp(
            subject=subject,
            html_content=full_html,
            from_email=email_config['from_email'],
            to_emails=email_config['to_email'],
            mail_connection=email_config['mail_connection'],
            mail_username=email_config['mail_username'],
            mail_password=email_config['mail_password']
        )
    else:
        print("📧 未配置邮件发送方式（SendGrid或SMTP），跳过邮件发送")

    # Summary
    print("\n" + "=" * 60)
    mode_text = "测试模式" if test_mode else "正常模式"
    print(f"📊 {mode_text}运行总结:")
    print(f"📄 HTML文件: digest.html (已生成)")
    if email_sent:
        mode_email_text = "测试邮件" if test_mode else "邮件"
        print(f"📧 {mode_email_text}发送: ✅ 成功发送到 {email_config['to_email']}")
    else:
        print("📧 邮件发送: ❌ 未发送或发送失败")

    if test_mode:
        print("🧪 测试模式完成 - 仅处理了1篇论文用于功能验证")
        print("🧪 Test mode completed - processed only 1 paper for functionality verification")

    print("=" * 60)