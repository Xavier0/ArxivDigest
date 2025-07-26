# encoding: utf-8
import os
import tqdm
from bs4 import BeautifulSoup as bs
import urllib.request
import json
import datetime
import pytz
import re


def _download_new_papers(field_abbr):
    NEW_SUB_URL = f'https://arxiv.org/list/{field_abbr}/new'  # https://arxiv.org/list/cs/new
    page = urllib.request.urlopen(NEW_SUB_URL)
    soup = bs(page)
    content = soup.body.find("div", {'id': 'content'})

    # find the first h3 element in content
    h3 = content.find("h3").text  # e.g: New submissions for Wed, 10 May 23
    date = h3.replace("New submissions for", "").strip()

    dt_list = content.dl.find_all("dt")
    dd_list = content.dl.find_all("dd")
    arxiv_base = "https://arxiv.org/abs/"

    assert len(dt_list) == len(dd_list)
    new_paper_list = []
    for i in tqdm.tqdm(range(len(dt_list))):
        paper = {}

        # 改进的论文编号提取逻辑
        paper_number = None

        # 方法1: 从HTML链接中提取 (最可靠)
        link_element = dt_list[i].find("a", href=True)
        if link_element:
            href = link_element.get('href')
            if href and href.startswith('/abs/'):
                paper_number = href[5:]  # 去掉 "/abs/" 前缀
                print(f"从链接提取论文编号: {paper_number}")

        # 方法2: 从链接文本中提取
        if not paper_number and link_element:
            link_text = link_element.text.strip()
            # 匹配 arXiv:XXXX.XXXXX 格式
            arxiv_match = re.search(r'arXiv:(\d{4}\.\d{4,5})', link_text)
            if arxiv_match:
                paper_number = arxiv_match.group(1)
                print(f"从链接文本提取论文编号: {paper_number}")

        # 方法3: 从整个dt元素文本中提取 (备用方法)
        if not paper_number:
            dt_text = dt_list[i].text.strip()
            # 使用正则表达式匹配 arXiv:XXXX.XXXXX 格式
            arxiv_match = re.search(r'arXiv:(\d{4}\.\d{4,5})', dt_text)
            if arxiv_match:
                paper_number = arxiv_match.group(1)
                print(f"从dt文本提取论文编号: {paper_number}")
            else:
                # 最后的备用方法：尝试原始的分割逻辑
                try:
                    parts = dt_text.split()
                    for part in parts:
                        if ':' in part and ('arXiv:' in part or re.match(r'\d{4}\.\d{4,5}', part.split(':')[-1])):
                            paper_number = part.split(":")[-1]
                            print(f"从分割文本提取论文编号: {paper_number}")
                            break
                except:
                    pass

        # 如果仍然没有找到论文编号，使用一个默认值并记录错误
        if not paper_number:
            print(f"警告: 无法提取第 {i + 1} 篇论文的编号，dt文本: {dt_list[i].text.strip()}")
            paper_number = f"unknown_{i}"  # 临时编号，避免程序崩溃

        # 构建链接
        paper['main_page'] = arxiv_base + paper_number
        paper['pdf'] = arxiv_base.replace('abs', 'pdf') + paper_number

        # 提取其他信息
        paper['title'] = dd_list[i].find("div", {"class": "list-title mathjax"}).text.replace("Title: ", "").strip()
        paper['authors'] = dd_list[i].find("div", {"class": "list-authors"}).text \
            .replace("Authors:\n", "").replace("\n", "").strip()
        paper['subjects'] = dd_list[i].find("div", {"class": "list-subjects"}).text.replace("Subjects: ", "").strip()
        paper['abstract'] = dd_list[i].find("p", {"class": "mathjax"}).text.replace("\n", " ").strip()

        new_paper_list.append(paper)

    #  check if ./data exist, if not, create it
    if not os.path.exists("./data"):
        os.makedirs("./data")

    # save new_paper_list to a jsonl file, with each line as the element of a dictionary
    date = datetime.date.fromtimestamp(datetime.datetime.now(tz=pytz.timezone("America/New_York")).timestamp())
    date = date.strftime("%a, %d %b %y")
    with open(f"./data/{field_abbr}_{date}.jsonl", "w") as f:
        for paper in new_paper_list:
            f.write(json.dumps(paper) + "\n")


def get_papers(field_abbr, limit=None):
    date = datetime.date.fromtimestamp(datetime.datetime.now(tz=pytz.timezone("America/New_York")).timestamp())
    date = date.strftime("%a, %d %b %y")
    if not os.path.exists(f"./data/{field_abbr}_{date}.jsonl"):
        _download_new_papers(field_abbr)
    results = []
    with open(f"./data/{field_abbr}_{date}.jsonl", "r") as f:
        for i, line in enumerate(f.readlines()):
            if limit and i == limit:
                return results
            results.append(json.loads(line))
    return results


def test_paper_extraction():
    """
    测试论文提取功能的辅助函数
    """
    print("🧪 测试论文链接提取功能...")

    # 测试一个简单的CS领域
    try:
        papers = get_papers("cs", limit=3)
        print(f"✅ 成功提取 {len(papers)} 篇论文")

        for i, paper in enumerate(papers, 1):
            print(f"\n📄 论文 {i}:")
            print(f"  标题: {paper.get('title', 'N/A')[:80]}...")
            print(f"  链接: {paper.get('main_page', 'N/A')}")
            print(f"  PDF: {paper.get('pdf', 'N/A')}")

            # 验证链接格式
            main_page = paper.get('main_page', '')
            if main_page and main_page != 'https://arxiv.org/abs/':
                if re.match(r'https://arxiv\.org/abs/\d{4}\.\d{4,5}', main_page):
                    print(f"  ✅ 链接格式正确")
                else:
                    print(f"  ❌ 链接格式异常: {main_page}")
            else:
                print(f"  ❌ 空链接或格式错误")

        return True

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False


if __name__ == "__main__":
    # 运行测试
    test_paper_extraction()