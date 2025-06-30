import os
import requests
import logging
import json
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import List, Dict, Optional

# 配置日志记录
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

# 定义规则类型的排序优先级
RULE_ORDER = [
    "DOMAIN",
    "DOMAIN-SUFFIX",
    "DOMAIN-KEYWORD",
    "PROCESS-NAME",
    "IP-CIDR",
    "IP-CIDR6",
    "IP-SUFFIX"
]

def get_time() -> str:
    """
    获取工作流执行时的时间段
    :return: 当前时间
    """
    beijing_time = ZoneInfo("Asia/Shanghai")
    now_time = datetime.now(beijing_time)
    return now_time.strftime("%Y年%m月%d日 %H:%M")

def calculate_rule_number(content: List[str]) -> Dict[str, int]:
    """
    统计每种规则类型的数量
    :param content: 内容列表
    :return: 统计后的数据字典
    """
    rule_number_dict = {prefix: 0 for prefix in RULE_ORDER}
    for line in content:
        parts = line.split(",")
        if parts[0] in RULE_ORDER:
            rule_number_dict[parts[0]] += 1
    return rule_number_dict

def download_file(file_url: str) -> Optional[str]:
    """
    下载指定文件
    :param file_url: 文件的 URL
    :return: 文件内容（字符串），失败时返回 None
    """
    try:
        response = requests.get(file_url, timeout=10)
        response.raise_for_status() # 抛出 HTTP 错误
        logging.info(f"文件下载成功: {file_url}")
        return response.text # 返回文件内容
    except requests.RequestException as e:
        logging.error(f"文件下载失败: {file_url} - {e}")
        return None

def merge_file_contents(file_contents: List[str]) -> List[str]:
    """
    合并文件内容，去除重复项和注释行
    :param file_contents: 内容列表
    :return: 合并后的内容列表
    """
    merged_lines = []
    seen_lines = set()
    for content in file_contents:
        if content:
            for line in content.splitlines():
                line = line.strip()
                if line and not line.startswith("#") and line not in seen_lines:
                    seen_lines.add(line)
                    merged_lines.append(line)
    return merged_lines

def sort_rules(rules: List[str]) -> List[str]:
    """
    根据规则类型和字母顺序对规则进行排序
    :param rules: 规则列表
    :return: 排序后的规则列表
    """
    def rule_key(line: str) -> tuple:
        parts = line.split(",")
        if parts[0] in RULE_ORDER:
            return (RULE_ORDER.index(parts[0]), parts[1])
        return (len(RULE_ORDER), line)
    return sorted(rules, key=rule_key)

def write_md_file(urls: List[str], content: List[str], folder_name: str, folder_path: str) -> None:
    """
    生成 .md 说明文件
    :param urls: 文件的 URL 列表
    :param content: 内容列表
    :param folder_name: 文件夹名称
    :param folder_path: 生成路径
    """
    rule_count = len(content)
    rule_number_dict = calculate_rule_number(content)
    now_time = get_time()

    md_content = f"""# {folder_name}

## 规则统计
最后同步时间: {now_time}

| 类型        | 数量(条) |
| ----------- | -------- |
"""
    for prefix, count in rule_number_dict.items():
        md_content += f"| {prefix:<12} | {count:<8} |\n"
    md_content += f"| **TOTAL**   | **{rule_count}** |\n"

    md_content += f"## 订阅链接（每日更新）\n"
    md_content += f"https://raw.githubusercontent.com/kirito12827/kk_zawuku/clash/rule/{folder_name}/{folder_name}.yaml\n"
    md_content += f"### 使用说明 \n"
    md_content += f"{folder_name}.yaml，请使用 behavior: 'classical' \n"
    md_content += f"### 规则来源\n"
    for url in urls:
        md_content += f"- {url}\n"

    os.makedirs(folder_path, exist_ok=True)
    md_file_path = os.path.join(folder_path, "README.md")
    try:
        with open(md_file_path, "w", encoding="utf-8") as md_file:
            md_file.write(md_content)
        logging.info(f".md 文件保存成功: {md_file_path}")
    except IOError as e:
        logging.error(f".md 文件保存失败: {md_file_path} - {e}")

def write_list_file(file_name: str, content: List[str], folder_name: str, folder_path: str) -> None:
    """
    将内容写入 .list 文件，并添加标题注释
    :param file_name: 文件名称
    :param content: 内容列表
    :param folder_name: 文件夹名称
    :param folder_path: 生成路径
    """
    rule_count = len(content)
    rule_name = os.path.splitext(file_name)[0]
    rule_number_dict = calculate_rule_number(content)
    now_time = get_time()

    formatted_content = [
        f"# 规则名称: {rule_name}",
        f"# 规则数量: {rule_count}",
        f"# 同步时间: {now_time}",
    ]
    for prefix, count in rule_number_dict.items():
        formatted_content.append(f"# {prefix}: {count}")
    formatted_content.append("")
    formatted_content.extend(content)

    os.makedirs(folder_path, exist_ok=True)
    list_file_path = os.path.join(folder_path, file_name)
    try:
        with open(list_file_path, "w", encoding="utf-8") as list_file:
            list_file.write("\n".join(formatted_content))
        logging.info(f".list 文件保存成功: {list_file_path}")
    except IOError as e:
        logging.error(f".list 文件保存失败: {list_file_path} - {e}")

def write_yaml_file(file_name: str, content: List[str], folder_name: str, folder_path: str) -> None:
    """
    将内容写入 .yaml 文件，并添加 payload 格式
    :param file_name: 文件名称
    :param content: 内容列表
    :param folder_name: 文件夹名称
    :param folder_path: 生成路径
    """
    rule_count = len(content)
    rule_name = os.path.splitext(file_name)[0]
    rule_number_dict = calculate_rule_number(content)
    now_time = get_time()

    formatted_content = [
        f"# 规则名称: {rule_name}",
        f"# 规则数量: {rule_count}",
        f"# 同步时间: {now_time}",
    ]
    for prefix, count in rule_number_dict.items():
        formatted_content.append(f"# {prefix}: {count}")
    formatted_content.append("")
    formatted_content.append("payload:")
    for line in content:
        formatted_content.append(f"  - {line}")

    os.makedirs(folder_path, exist_ok=True)
    yaml_file_path = os.path.join(folder_path, f"{rule_name}.yaml")
    try:
        with open(yaml_file_path, "w", encoding="utf-8") as yaml_file:
            yaml_file.write("\n".join(formatted_content))
        logging.info(f".yaml 文件保存成功: {yaml_file_path}")
    except IOError as e:
        logging.error(f".yaml 文件保存失败: {yaml_file_path} - {e}")

def process_file(file_name: str, urls: List[str], folder_name: str, folder_path: str) -> None:
    """
    下载文件、合并内容、排序规则并生成 .list 和 .yaml 文件
    :param file_name: 文件名称
    :param urls: 文件的 URL 列表
    :param folder_name: 文件夹名称
    :param folder_path: 生成路径
    """
    file_contents = []
    for url in urls:
        content = download_file(url)
        if content is not None:
            file_contents.append(content)

    # 合并内容
    merged_content = merge_file_contents(file_contents)

    # 排序规则
    sorted_content = sort_rules(merged_content)

    # 在 rule 目录下创建同名文件夹
    rule_folder_path = os.path.join(folder_path, folder_name)
    os.makedirs(rule_folder_path, exist_ok=True)

    # 写入 .list 和 .yaml 文件
    write_list_file(file_name, sorted_content, folder_name, rule_folder_path)
    write_yaml_file(file_name, sorted_content, folder_name, rule_folder_path)

    # 写入 .md 文件
    write_md_file(urls, sorted_content, folder_name, rule_folder_path)

def write_total_md_file(folder_path: str, rule_list_data: Dict[str, List[str]], width: int = 5) -> None:
    """
    生成一个总的 .md 文件
    :param folder_path: 生成路径
    :param rule_list_data: 列表数据
    :param width: 表格宽度
    """
    now_time = get_time()
    total_list_data_number = len(rule_list_data)

    md_content = f"""## 前言
本文件由脚本自动生成

## 规则列表
处理的规则总计: {total_list_data_number} 

最后同步时间: {now_time} \n
"""
    folder_names = [os.path.splitext(item)[0] for item in list(rule_list_data.keys())]

    rows = []
    for i in range(0, len(folder_names), width):
        row = folder_names[i:i + width]
        rows.append(row)

    for row in rows:
        while len(row) < width:
            row.append(" " * 10)

    markdown_table = []
    markdown_table.append("| 规则名称 |" + " | ".join(["   "] * (width - 1)) + " |")
    markdown_table.append("|" + "----------|" * width)
    for row in rows:
        formatted_row = [f"[{cell:<10}](https://github.com/kirito12827/kk_zawuku/tree/clash/rule/{cell:<10})" for cell in row]
        markdown_table.append("| " + "|".join(formatted_row) + " |")

    md_content += "\n".join(markdown_table)

    os.makedirs(folder_path, exist_ok=True)
    md_file_path = os.path.join(folder_path, "README.md")
    try:
        with open(md_file_path, "w", encoding="utf-8") as md_file:
            md_file.write(md_content)
        logging.info(f"总 .md 文件保存成功: {md_file_path}")
    except IOError as e:
        logging.error(f"总 .md 文件保存失败: {md_file_path} - {e}")

if __name__ == "__main__":
    # 自定义 rule 文件夹总路径
    folder_path = "rule"

    # 获取 rule_list.json 的路径
    json_file_path = os.path.join(os.path.dirname(__file__), "rule_list.json")

    # 读取 rule_list.json 文件
    try:
        with open(json_file_path, "r", encoding="utf-8") as json_file:
            rule_list_data = json.load(json_file)
    except FileNotFoundError:
        logging.error(f"文件未找到: {json_file_path}")
        exit(1)
    except json.JSONDecodeError:
        logging.error(f"JSON 文件格式错误: {json_file_path}")
        exit(1)

    # 批量处理
    for file_name, urls in rule_list_data.items():
        folder_name = os.path.splitext(file_name)[0]
        process_file(file_name, urls, folder_name, folder_path)

    # 生成总的 MD 文件
    write_total_md_file(folder_path, rule_list_data)