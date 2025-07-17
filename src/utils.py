import dataclasses
import logging
import math
import os
import io
import sys
import time
import json
import requests
from typing import Optional, Sequence, Union

import tqdm
import copy

# 兼容新旧版本的OpenAI库
try:
    import openai
    from openai import openai_object

    OPENAI_VERSION = "old"
except ImportError:
    try:
        import openai

        # 新版本OpenAI库没有openai_object
        openai_object = None
        OPENAI_VERSION = "new"
    except ImportError:
        openai = None
        openai_object = None
        OPENAI_VERSION = "none"


# 创建兼容的mock对象
class MockOpenAIChoice:
    def __init__(self, content="", total_tokens=0):
        self.message = {"content": content}
        self.total_tokens = total_tokens
        # 支持字典式访问 - 包含所有必要的键
        self._data = {
            "total_tokens": total_tokens,
            "message": {"content": content}
        }

    def __getitem__(self, key):
        return self._data[key]

    def __setitem__(self, key, value):
        self._data[key] = value
        # 同时更新对象属性以保持一致性
        if key == "message":
            self.message = value
        elif key == "total_tokens":
            self.total_tokens = value


StrOrOpenAIObject = Union[str, MockOpenAIChoice]

openai_org = os.getenv("OPENAI_ORG")
if openai_org is not None:
    openai.organization = openai_org
    logging.warning(f"Switching to organization: {openai_org} for OAI API key.")


@dataclasses.dataclass
class OpenAIDecodingArguments(object):
    max_tokens: int = 1800
    temperature: float = 0.2
    top_p: float = 1.0
    n: int = 1
    stream: bool = False
    stop: Optional[Sequence[str]] = None
    presence_penalty: float = 0.0
    frequency_penalty: float = 0.0


@dataclasses.dataclass
class CustomAPIConfig(object):
    """Configuration for custom API endpoints like SiliconFlow"""
    api_url: str = None
    api_key: str = None
    model_name: str = None
    use_custom_api: bool = False


def custom_api_completion(
        prompts,
        decoding_args: OpenAIDecodingArguments,
        api_config: CustomAPIConfig,
        sleep_time=2,
        max_retries=3,
        **decoding_kwargs,
):
    """
    Custom API completion for SiliconFlow or other OpenAI-compatible APIs
    """
    is_single_prompt = isinstance(prompts, (str, dict))
    if is_single_prompt:
        prompts = [prompts]

    completions = []

    for prompt in prompts:
        backoff = max_retries

        while True:
            try:
                # Prepare messages for chat format
                if isinstance(prompt, str):
                    messages = [
                        {"role": "system", "content": "You are a helpful assistant."},
                        {"role": "user", "content": prompt}
                    ]
                elif isinstance(prompt, dict):
                    messages = [prompt]
                else:
                    messages = prompt

                # Prepare payload
                payload = {
                    "model": api_config.model_name,
                    "messages": messages,
                    "max_tokens": decoding_args.max_tokens,
                    "temperature": decoding_args.temperature,
                    "top_p": decoding_args.top_p,
                    "n": decoding_args.n,
                }

                # Add optional parameters
                if decoding_args.stop:
                    payload["stop"] = decoding_args.stop
                if decoding_args.presence_penalty:
                    payload["presence_penalty"] = decoding_args.presence_penalty
                if decoding_args.frequency_penalty:
                    payload["frequency_penalty"] = decoding_args.frequency_penalty

                # Add any additional kwargs
                payload.update(decoding_kwargs)

                headers = {
                    "Authorization": f"Bearer {api_config.api_key}",
                    "Content-Type": "application/json"
                }

                print(f"Making request to: {api_config.api_url}")
                print(f"Model: {api_config.model_name}")
                print(f"Payload keys: {list(payload.keys())}")

                response = requests.post(
                    api_config.api_url,
                    json=payload,
                    headers=headers,
                    timeout=120  # 增加到2分钟
                )

                response.raise_for_status()
                response_data = response.json()

                print(f"Response status: {response.status_code}")
                print(f"Response keys: {list(response_data.keys())}")

                # Convert to OpenAI-like format for compatibility
                if "choices" in response_data:
                    for choice in response_data["choices"]:
                        # Create a mock OpenAI choice object for compatibility
                        if "message" in choice:
                            content = choice["message"]["content"]
                        elif "text" in choice:
                            content = choice["text"]
                        else:
                            content = str(choice)

                        # Get usage info if available
                        total_tokens = 0
                        if "usage" in response_data:
                            total_tokens = response_data["usage"].get("total_tokens", 0)

                        # Create mock choice with proper initialization
                        mock_choice = MockOpenAIChoice(content=content, total_tokens=total_tokens)

                        completions.append(mock_choice)
                else:
                    # Fallback if response format is different
                    mock_choice = MockOpenAIChoice(content=str(response_data), total_tokens=0)
                    completions.append(mock_choice)

                break

            except requests.exceptions.RequestException as e:
                logging.warning(f"Request error: {e}")
                if not backoff:
                    logging.error("Hit too many failures, exiting")
                    raise e
                else:
                    backoff -= 1
                    logging.warning("Request failed, retrying...")
                    time.sleep(sleep_time)
            except Exception as e:
                logging.warning(f"API error: {e}")
                if not backoff:
                    logging.error("Hit too many failures, exiting")
                    raise e
                else:
                    backoff -= 1
                    logging.warning("API call failed, retrying...")
                    time.sleep(sleep_time)

    if is_single_prompt:
        return completions[0] if completions else None
    return completions


def openai_completion(
        prompts,
        decoding_args: OpenAIDecodingArguments,
        model_name="text-davinci-003",
        sleep_time=2,
        batch_size=1,
        max_instances=sys.maxsize,
        max_batches=sys.maxsize,
        return_text=False,
        custom_api_config: CustomAPIConfig = None,
        **decoding_kwargs,
) -> Union[Union[StrOrOpenAIObject], Sequence[StrOrOpenAIObject], Sequence[Sequence[StrOrOpenAIObject]],]:
    """
    Enhanced decode function supporting both OpenAI and custom APIs
    """
    # Check if using custom API
    if custom_api_config and custom_api_config.use_custom_api:
        print("Using custom API endpoint...")
        return custom_api_completion(
            prompts, decoding_args, custom_api_config, sleep_time, **decoding_kwargs
        )

    # For OpenAI API, we need to handle version differences
    if OPENAI_VERSION == "none":
        raise RuntimeError("OpenAI library not installed")

    # Original OpenAI API logic with compatibility fixes
    is_chat_model = "gpt-3.5" in model_name or "gpt-4" in model_name
    is_single_prompt = isinstance(prompts, (str, dict))
    if is_single_prompt:
        prompts = [prompts]

    if max_batches < sys.maxsize:
        logging.warning(
            "`max_batches` will be deprecated in the future, please use `max_instances` instead."
            "Setting `max_instances` to `max_batches * batch_size` for now."
        )
        max_instances = max_batches * batch_size

    prompts = prompts[:max_instances]
    num_prompts = len(prompts)
    prompt_batches = [
        prompts[batch_id * batch_size: (batch_id + 1) * batch_size]
        for batch_id in range(int(math.ceil(num_prompts / batch_size)))
    ]

    completions = []
    for batch_id, prompt_batch in tqdm.tqdm(
            enumerate(prompt_batches),
            desc="prompt_batches",
            total=len(prompt_batches),
    ):
        batch_decoding_args = copy.deepcopy(decoding_args)

        backoff = 3

        while True:
            try:
                shared_kwargs = dict(
                    model=model_name,
                    **batch_decoding_args.__dict__,
                    **decoding_kwargs,
                )

                if is_chat_model:
                    if OPENAI_VERSION == "old":
                        # 旧版本OpenAI API
                        completion_batch = openai.ChatCompletion.create(
                            messages=[
                                {"role": "system", "content": "You are a helpful assistant."},
                                {"role": "user", "content": prompt_batch[0]}
                            ],
                            **shared_kwargs
                        )
                        choices = completion_batch.choices
                        for choice in choices:
                            choice["total_tokens"] = completion_batch.usage.total_tokens
                    else:
                        # 新版本OpenAI API
                        try:
                            client = openai.OpenAI(api_key=openai.api_key)
                            completion_batch = client.chat.completions.create(
                                messages=[
                                    {"role": "system", "content": "You are a helpful assistant."},
                                    {"role": "user", "content": prompt_batch[0]}
                                ],
                                **shared_kwargs
                            )
                            choices = []
                            for choice in completion_batch.choices:
                                mock_choice = MockOpenAIChoice(
                                    content=choice.message.content,
                                    total_tokens=completion_batch.usage.total_tokens
                                )
                                choices.append(mock_choice)
                        except Exception as e:
                            print(f"新版本OpenAI API调用失败: {e}")
                            print("建议使用自定义API或降级OpenAI库")
                            raise e
                else:
                    if OPENAI_VERSION == "old":
                        completion_batch = openai.Completion.create(prompt=prompt_batch, **shared_kwargs)
                        choices = completion_batch.choices
                        for choice in choices:
                            choice["total_tokens"] = completion_batch.usage.total_tokens
                    else:
                        # 新版本的Completion API使用方式不同
                        raise RuntimeError("新版本OpenAI库不支持Completion API，请使用chat模型")

                completions.extend(choices)
                break

            except Exception as e:
                if "Please reduce your prompt" in str(e):
                    batch_decoding_args.max_tokens = int(batch_decoding_args.max_tokens * 0.8)
                    logging.warning(f"Reducing target length to {batch_decoding_args.max_tokens}, Retrying...")
                elif not backoff:
                    logging.error("Hit too many failures, exiting")
                    raise e
                else:
                    backoff -= 1
                    logging.warning("Hit request rate limit; retrying...")
                    time.sleep(sleep_time)

    if return_text:
        completions = [completion.message["content"] if hasattr(completion, 'message') else completion.text for
                       completion in completions]
    if decoding_args.n > 1:
        completions = [completions[i: i + decoding_args.n] for i in range(0, len(completions), decoding_args.n)]
    if is_single_prompt:
        (completions,) = completions
    return completions


def write_ans_to_file(ans_data, file_prefix, output_dir="./output"):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    filename = os.path.join(output_dir, file_prefix + ".txt")
    with open(filename, "w") as f:
        for ans in ans_data:
            f.write(str(ans) + "\n")