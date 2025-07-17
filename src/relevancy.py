"""
Enhanced relevancy module for bilingual output and cross-domain paper analysis
"""
import time
import json
import os
import random
import re
import string
from datetime import datetime

import numpy as np
import tqdm
import utils


def encode_prompt(query, prompt_papers):
    """Encode multiple prompt instructions into a single string."""
    prompt = open("src/relevancy_prompt.txt").read() + "\n"
    prompt += query['interest']

    for idx, task_dict in enumerate(prompt_papers):
        (title, authors, abstract) = task_dict["title"], task_dict["authors"], task_dict["abstract"]
        if not title:
            raise ValueError(f"Empty title for paper {idx}")
        prompt += f"###\n"
        prompt += f"{idx + 1}. Title: {title}\n"
        prompt += f"{idx + 1}. Authors: {authors}\n"
        prompt += f"{idx + 1}. Abstract: {abstract}\n"
    prompt += f"\n Generate response:\n1."
    print("Generated prompt length:", len(prompt))
    return prompt


def post_process_chat_gpt_response(paper_data, response, threshold_score=6):
    """
    Enhanced post-processing for bilingual responses with multiple fields
    """
    selected_data = []
    if response is None:
        return [], True

    response_content = response['message']['content'].replace("\n\n", "\n")
    json_items = response_content.split("\n")

    # Pattern to remove numbering and quotes
    pattern = r"^\d+\. |\\"

    import pprint
    try:
        # Extract lines that look like JSON
        json_lines = [line for line in json_items if any(key in line.lower() for key in
                     ["relevancy score", "reasons for match", "中文原因", "detailed summary", "详细总结"])]

        score_items = []
        for line in json_lines:
            cleaned_line = re.sub(pattern, "", line).strip()
            if cleaned_line and (cleaned_line.startswith('{') or '"relevancy score"' in cleaned_line.lower()):
                try:
                    # Handle cases where line might not be complete JSON
                    if not cleaned_line.endswith('}'):
                        # Try to find the next part
                        continue
                    score_items.append(json.loads(cleaned_line))
                except json.JSONDecodeError as e:
                    print(f"JSON decode error for line: {cleaned_line}")
                    print(f"Error: {e}")
                    continue

    except Exception as e:
        print("Error processing response:")
        pprint.pprint(json_lines)
        raise RuntimeError(f"Failed to parse response: {e}")

    print(f"Successfully parsed {len(score_items)} items from response")
    pprint.pprint(score_items[:2])  # Show first 2 items for debugging

    # Extract scores
    scores = []
    for item in score_items:
        temp = item.get("Relevancy score", item.get("relevancy score", 0))
        if isinstance(temp, str):
            if "/" in temp:
                scores.append(int(temp.split("/")[0]))
            else:
                try:
                    scores.append(int(temp))
                except ValueError:
                    scores.append(0)
        else:
            scores.append(int(temp))

    # Handle hallucination (more items returned than input papers)
    if len(score_items) > len(paper_data):
        print(f"Warning: Model returned {len(score_items)} items but only {len(paper_data)} papers provided")
        score_items = score_items[:len(paper_data)]
        scores = scores[:len(paper_data)]
        hallucination = True
    elif len(score_items) < len(paper_data):
        print(f"Warning: Model returned {len(score_items)} items but {len(paper_data)} papers provided")
        hallucination = True
    else:
        hallucination = False

    # Process each item
    for idx, inst in enumerate(score_items):
        if idx >= len(paper_data) or idx >= len(scores):
            break

        # Filter by threshold
        if scores[idx] < threshold_score:
            continue

        # Build output string for display
        output_str = "Title: " + paper_data[idx]["title"] + "\n"
        output_str += "Authors: " + paper_data[idx]["authors"] + "\n"
        output_str += "Link: " + paper_data[idx]["main_page"] + "\n"

        # Add all fields from the response to the paper data
        for key, value in inst.items():
            paper_data[idx][key] = value
            output_str += str(key) + ": " + str(value) + "\n"

        paper_data[idx]['summarized_text'] = output_str
        selected_data.append(paper_data[idx])

    return selected_data, hallucination


def find_word_in_string(w, s):
    return re.compile(r"\b({0})\b".format(w), flags=re.IGNORECASE).search(s)


def process_subject_fields(subjects):
    all_subjects = subjects.split(";")
    all_subjects = [s.split(" (")[0] for s in all_subjects]
    return all_subjects


def generate_relevance_score(
    all_papers,
    query,
    model_name="gpt-3.5-turbo-16k",
    threshold_score=6,
    num_paper_in_prompt=8,  # Reduced for longer bilingual responses
    temperature=0.4,
    top_p=1.0,
    sorting=True,
    custom_api_config=None
):
    """
    Enhanced relevance scoring with bilingual support and custom API
    """
    ans_data = []
    request_idx = 1
    hallucination = False

    print(f"Processing {len(all_papers)} papers in batches of {num_paper_in_prompt}")
    if custom_api_config and custom_api_config.use_custom_api:
        print(f"Using custom API: {custom_api_config.api_url}")
        print(f"Model: {custom_api_config.model_name}")

    for id in tqdm.tqdm(range(0, len(all_papers), num_paper_in_prompt)):
        prompt_papers = all_papers[id:id+num_paper_in_prompt]
        prompt = encode_prompt(query, prompt_papers)

        # Increased max_tokens for bilingual responses
        decoding_args = utils.OpenAIDecodingArguments(
            temperature=temperature,
            n=1,
            max_tokens=256*num_paper_in_prompt,  # Increased for bilingual content
            top_p=top_p,
        )

        request_start = time.time()
        response = utils.openai_completion(
            prompts=prompt,
            model_name=model_name,
            batch_size=1,
            decoding_args=decoding_args,
            logit_bias={"100257": -100},  # prevent the <|endoftext|> from being generated
            custom_api_config=custom_api_config
        )

        print(f"Response for batch {request_idx}:")
        if hasattr(response, 'message') and 'content' in response.message:
            content = response.message['content']
            print(content[:500] + "..." if len(content) > 500 else content)
        else:
            print("Unexpected response format:", str(response)[:200])

        request_duration = time.time() - request_start

        process_start = time.time()
        batch_data, hallu = post_process_chat_gpt_response(
            prompt_papers, response, threshold_score=threshold_score
        )
        hallucination = hallucination or hallu
        ans_data.extend(batch_data)

        print(f"Request {request_idx} took {request_duration:.2f}s")
        print(f"Post-processing took {time.time() - process_start:.2f}s")
        print(f"Found {len(batch_data)} relevant papers in this batch")

        request_idx += 1

    if sorting and ans_data:
        ans_data = sorted(ans_data, key=lambda x: int(x.get("Relevancy score", 0)), reverse=True)

    print(f"Total relevant papers found: {len(ans_data)}")
    return ans_data, hallucination


def run_all_day_paper(
    query={"interest":"", "subjects":["Computation and Language", "Artificial Intelligence"]},
    date=None,
    data_dir="../data",
    model_name="gpt-3.5-turbo-16k",
    threshold_score=6,
    num_paper_in_prompt=6,  # Reduced for bilingual processing
    temperature=0.4,
    top_p=1.0
):
    """
    Enhanced function to process daily papers with bilingual support
    """
    if date is None:
        date = datetime.today().strftime('%a, %d %b %y')
    print("The date for the arxiv data is:", date)

    try:
        all_papers = [json.loads(l) for l in open(f"{data_dir}/{date}.jsonl", "r")]
        print(f"Found {len(all_papers)} total papers.")
    except FileNotFoundError:
        print(f"No data file found for {date}")
        return [], False

    all_papers_in_subjects = [
        t for t in all_papers
        if bool(set(process_subject_fields(t['subjects'])) & set(query['subjects']))
    ]
    print(f"After filtering subjects, we have {len(all_papers_in_subjects)} papers left.")

    if not all_papers_in_subjects:
        print("No papers found matching the subject criteria.")
        return [], False

    ans_data, hallucination = generate_relevance_score(
        all_papers_in_subjects, query, model_name, threshold_score,
        num_paper_in_prompt, temperature, top_p
    )

    # Save results
    utils.write_ans_to_file(ans_data, date, output_dir="../outputs")
    return ans_data, hallucination


if __name__ == "__main__":
    # Test query for analog circuit design and optimization algorithms
    query = {
        "interest": """
        I am interested in the following research areas:
        
        **Primary Focus - Analog Circuit Design with ML/AI:**
        1. Machine learning methods for analog circuit design, including layout generation and sizing optimization
        2. Large language models (LLMs) applied to circuit design automation
        3. AI-driven electronic design automation (EDA) tools
        
        **Secondary Focus - Optimization Algorithms:**
        1. Reinforcement learning algorithms and novel RL techniques
        2. Bayesian optimization methods and Gaussian processes
        3. Evolutionary algorithms, genetic algorithms, and nature-inspired optimization
        """,
        "subjects": ["Artificial Intelligence", "Machine Learning", "Systems and Control"]
    }

    ans_data, hallucination = run_all_day_paper(query)