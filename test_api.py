#!/usr/bin/env python3
"""
SiliconFlow API测试脚本
用于验证API配置和连接
"""

import os
import sys
import requests
import json
from dotenv import load_dotenv


def test_siliconflow_api():
    """测试SiliconFlow API连接"""

    # 加载环境变量
    load_dotenv()

    api_key = os.environ.get("CUSTOM_API_KEY")
    if not api_key:
        print("❌ 错误: 未设置CUSTOM_API_KEY环境变量")
        print("请设置: export CUSTOM_API_KEY='your-api-key'")
        return False

    url = "https://api.siliconflow.cn/v1/chat/completions"

    # 简单测试消息
    payload = {
        "model": "Pro/deepseek-ai/DeepSeek-R1",
        "messages": [
            {
                "role": "user",
                "content": "Hello! Please respond with 'API test successful' if you can see this message."
            }
        ],
        "max_tokens": 100,
        "temperature": 0.1
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    print("🔄 测试SiliconFlow API连接...")
    print(f"URL: {url}")
    print(f"Model: {payload['model']}")
    print(f"API Key: {api_key[:10]}...{api_key[-5:]}")

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)

        print(f"📊 HTTP状态码: {response.status_code}")

        if response.status_code == 200:
            response_data = response.json()
            print("✅ API连接成功!")

            if "choices" in response_data and len(response_data["choices"]) > 0:
                content = response_data["choices"][0]["message"]["content"]
                print(f"🤖 模型响应: {content}")

                if "usage" in response_data:
                    usage = response_data["usage"]
                    print(f"📈 Token使用: {usage}")

                return True
            else:
                print("⚠️ 响应格式异常")
                print(f"响应内容: {response_data}")
                return False

        else:
            print(f"❌ API调用失败: {response.status_code}")
            print(f"错误响应: {response.text}")
            return False

    except requests.exceptions.Timeout:
        print("❌ 请求超时")
        return False
    except requests.exceptions.ConnectionError:
        print("❌ 网络连接错误")
        return False
    except Exception as e:
        print(f"❌ 未知错误: {e}")
        return False


def test_paper_analysis():
    """测试论文分析功能"""

    load_dotenv()
    api_key = os.environ.get("CUSTOM_API_KEY")
    if not api_key:
        print("❌ 错误: 未设置CUSTOM_API_KEY环境变量")
        return False

    url = "https://api.siliconflow.cn/v1/chat/completions"

    # 模拟论文分析任务
    test_prompt = """
    You have been asked to read a list of arxiv papers, each with title, authors and abstract.
    Based on my specific research interests, provide a relevancy score out of 10 for each paper, with a higher score indicating greater relevance.

    Additionally, please generate explanations in BOTH Chinese and English according to the following rules:

    **For Analog Circuit Design Papers (involving ML/AI methods):**
    - Provide a concise summary of the methodology and results
    - Focus on the ML/AI techniques used and their application to circuit design

    **For Pure Algorithmic Papers (RL, Bayesian Optimization, Evolutionary Algorithms):**
    - Provide detailed explanation of key concepts and comprehensive summary
    - Explain the algorithmic contributions and theoretical insights

    Please keep the paper order the same as in the input list, with one json format per line. Example format:
    {"Relevancy score": "an integer score out of 10", "Reasons for match": "1-2 sentence short reasoning in English", "中文原因": "1-2句中文简要原因"}

    My research interests are:
    1. Machine learning methods for analog circuit design
    2. Reinforcement learning algorithms

    ###
    1. Title: Deep Reinforcement Learning for Analog Circuit Sizing
    1. Authors: John Smith, Alice Chen
    1. Abstract: This paper presents a novel deep reinforcement learning approach for automatic sizing of analog circuits. We propose a policy gradient method that can optimize circuit parameters to meet performance specifications while minimizing power consumption.

    Generate response:
    1.
    """

    payload = {
        "model": "Pro/deepseek-ai/DeepSeek-R1",
        "messages": [
            {
                "role": "user",
                "content": test_prompt
            }
        ],
        "max_tokens": 500,
        "temperature": 0.4
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    print("\n🔄 测试论文分析功能...")

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=60)

        if response.status_code == 200:
            response_data = response.json()
            print("✅ 论文分析测试成功!")

            if "choices" in response_data and len(response_data["choices"]) > 0:
                content = response_data["choices"][0]["message"]["content"]
                print(f"🤖 分析结果:\n{content}")

                # 尝试解析JSON响应
                try:
                    # 提取JSON部分
                    import re
                    json_match = re.search(r'\{.*\}', content, re.DOTALL)
                    if json_match:
                        json_str = json_match.group()
                        parsed_json = json.loads(json_str)
                        print("✅ JSON解析成功!")
                        print(f"相关性评分: {parsed_json.get('Relevancy score', 'N/A')}")
                        print(f"英文原因: {parsed_json.get('Reasons for match', 'N/A')}")
                        print(f"中文原因: {parsed_json.get('中文原因', 'N/A')}")
                    else:
                        print("⚠️ 未找到有效的JSON格式")
                except json.JSONDecodeError:
                    print("⚠️ JSON解析失败，但响应正常")

                return True
            else:
                print("⚠️ 响应格式异常")
                return False

        else:
            print(f"❌ 论文分析测试失败: {response.status_code}")
            print(f"错误响应: {response.text}")
            return False

    except Exception as e:
        print(f"❌ 论文分析测试错误: {e}")
        return False


def main():
    """主测试函数"""
    print("🚀 开始API测试...")
    print("=" * 50)

    # 基础连接测试
    basic_test = test_siliconflow_api()

    if basic_test:
        print("\n" + "=" * 50)
        # 论文分析测试
        analysis_test = test_paper_analysis()

        if analysis_test:
            print("\n🎉 所有测试通过!")
            print("✅ API配置正确，可以运行完整的arxiv digest")
        else:
            print("\n⚠️ 基础连接正常，但论文分析可能需要调整")
    else:
        print("\n❌ 基础连接失败，请检查API配置")

    print("\n" + "=" * 50)
    print("💡 测试完成!")


if __name__ == "__main__":
    main()