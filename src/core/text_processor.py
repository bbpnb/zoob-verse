"""文本处理：读取、清洗、分块"""

import re
from pathlib import Path


def read_text(file_path: str | Path, encoding: str = "gbk") -> str:
    """读取文本文件，自动处理编码。"""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"文件不存在: {path}")

    try:
        return path.read_text(encoding=encoding)
    except UnicodeDecodeError:
        # Fallback to UTF-8
        return path.read_text(encoding="utf-8", errors="replace")


def clean_text(text: str) -> str:
    """清洗文本：去除头部/尾部广告、声明等噪音。"""
    # 去除常见的电子书头部噪音
    text = re.sub(r'全本全集精校小说尽在：.*?\n', '', text)
    text = re.sub(r'更多资源下载：.*?\n', '', text)
    text = re.sub(r'※声明：.*?※\n', '', text, flags=re.DOTALL)
    text = re.sub(r'-{10,}\n', '', text)

    # 去除尾部噪音
    text = re.sub(r'\n-+\s*$', '', text)

    return text.strip()


def chunk_by_paragraph(text: str, max_chunk_size: int = 2000, overlap: int = 200) -> list[str]:
    """按段落分块，保留上下文重叠。

    Args:
        text: 清洗后的文本
        max_chunk_size: 每个 chunk 的最大字符数
        overlap: 相邻 chunk 之间的重叠字符数（保留上下文）

    Returns:
        文本块列表
    """
    # 按空行分割段落
    paragraphs = re.split(r'\n\s*\n', text)
    paragraphs = [p.strip() for p in paragraphs if p.strip()]

    chunks = []
    current_chunk = []
    current_size = 0

    for para in paragraphs:
        para_len = len(para)
        if current_size + para_len > max_chunk_size and current_chunk:
            # 当前 chunk 已满，保存并开始新的
            chunk_text = '\n\n'.join(current_chunk)
            chunks.append(chunk_text)

            # 保留末尾重叠
            overlap_text = []
            overlap_size = 0
            for p in reversed(current_chunk):
                overlap_size += len(p)
                overlap_text.insert(0, p)
                if overlap_size >= overlap:
                    break
            current_chunk = overlap_text
            current_size = overlap_size

        current_chunk.append(para)
        current_size += para_len

    if current_chunk:
        chunks.append('\n\n'.join(current_chunk))

    return chunks


def process_novel(file_path: str | Path) -> list[str]:
    """处理小说文件：读取 → 清洗 → 分块"""
    text = read_text(file_path)
    text = clean_text(text)
    chunks = chunk_by_paragraph(text)
    return chunks
