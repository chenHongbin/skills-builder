#!/usr/bin/env python3
"""
Book Mirror - 章节边界检测器
从纯文本中检测章节边界，输出 JSON 格式的章节列表。
纯 Python 标准库实现，不需要安装任何依赖。

用法：python3 detect_chapters.py <输入.txt>
"""

import json
import re
import sys


def detect_chapters(text, min_chars_per_chapter=300):
    """
    检测文本中的章节边界。
    返回章节列表，每个包含：index, title, start_char, end_char, char_count, detection_method
    """
    lines = text.split('\n')
    candidates = []

    # ============================================================
    # 策略 0：EPUB "##" 标题标记（来自 extract_epub.py 的 <title> 提取）
    # ============================================================
    for i, line in enumerate(lines):
        if line.startswith('## '):
            title = line[3:].strip()
            if title and len(title) > 1:
                candidates.append({
                    'line_idx': i,
                    'title': title,
                    'method': 'epub_title',
                    'confidence': 0.95,
                })

    # ============================================================
    # 策略 1：显式章节标记
    # ============================================================
    # 中文章节模式（匹配多字词优先）
    chinese_chapter = re.compile(
        r'^[\s　]{0,10}'
        r'('
        r'第[零一二三四五六七八九十百千\d]+[章节卷部篇回]'  # 第X章、第X节等
        r'|序言|前言|序[　\s]'  # 序言、前言、序
        r'|后记|跋$|楔子|引言|绪论'  # 后记、跋、楔子、引言
        r'|附录[一二三四五六七八九十\d]?'  # 附录、附录一
        r'|致谢|鸣谢'  # 致谢
        r'|结语|尾声|终章'  # 结语
        r')'
    )

    # 英文/中英混合章节模式
    english_chapter = re.compile(
        r'^[\s]{0,10}'
        r'((?:Chapter|CHAPTER|Part|Section|Book|Act)\s+[\dIVX]+\.?)'
    )

    # 中文章节部分（第一部分、第二部分...）
    chinese_part = re.compile(
        r'^[\s　]{0,10}'
        r'(第[零一二三四五六七八九十百千\d]+部分|Part\s+[IVX\d]+)'
    )

    # 数字编号的章节（"1 题目"、"2. 题目"、"3、题目"）
    numbered_section = re.compile(
        r'^[\s]{0,10}'
        r'(\d+)[\.\、\s]{1,3}'
        r'[A-Z一-鿿一-鿿㐀-䶿]'  # 英文大写或中文字符开头
    )

    # 罗马数字章节
    roman_numeral = re.compile(r'^[\s]{0,10}([IVX]+)\.\s+\S')

    # 扫描所有行，收集候选章节标题
    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped or len(stripped) < 2:
            continue

        # 跳过已经检查过的 ## 标题
        if stripped.startswith('## '):
            continue

        # 跳过长分隔线
        if re.match(r'^[—\-—=]{10,}$', stripped):
            continue

        # 检查英文 Part/Chapter/Section
        em = english_chapter.match(stripped)
        if em and len(stripped) < 100:
            candidates.append({
                'line_idx': i,
                'title': stripped,
                'method': 'explicit_english',
                'confidence': 0.9,
            })
            continue

        # 检查中文部分
        pm = chinese_part.match(stripped)
        if pm and len(stripped) < 100:
            candidates.append({
                'line_idx': i,
                'title': stripped,
                'method': 'chinese_part',
                'confidence': 0.9,
            })
            continue

        # 检查数字编号章节（"1 题目"、"2. 题目"、"3、题目"）
        nm = numbered_section.match(stripped)
        if nm and len(stripped) < 100 and len(stripped) > 3:
            # 验证：确保后面跟的不是页码或日期
            if not re.match(r'^\d+[\s\.、]+\d+$', stripped):  # 排除纯数字
                candidates.append({
                    'line_idx': i,
                    'title': stripped,
                    'method': 'numbered_section',
                    'confidence': 0.7,
                })
                continue

        # 检查中文章节标记
        cm = chinese_chapter.match(stripped)
        if cm and len(stripped) < 100:
            candidates.append({
                'line_idx': i,
                'title': stripped,
                'method': 'explicit_chinese',
                'confidence': 0.95,
            })
            continue

        # 检查罗马数字
        rm = roman_numeral.match(stripped)
        if rm and len(stripped) < 100 and i > 0 and not lines[i - 1].strip():
            candidates.append({
                'line_idx': i,
                'title': stripped,
                'method': 'roman_numeral',
                'confidence': 0.5,
            })
            continue

    # ============================================================
    # 策略 2：结构模式（仅在策略 0/1 候选太少时使用）
    # ============================================================
    explicit_count = sum(1 for c in candidates if c['confidence'] >= 0.7)

    if explicit_count < 3:
        for i, line in enumerate(lines):
            stripped = line.strip()
            if not stripped or len(stripped) < 3:
                continue

            # 全大写短行 → 可能是英文章节标题
            if stripped.isupper() and 3 <= len(stripped) <= 40 and stripped.replace(' ', '').isascii():
                if not re.match(r'^[A-Z\s]{1,5}$', stripped):
                    candidates.append({
                        'line_idx': i,
                        'title': stripped,
                        'method': 'all_caps',
                        'confidence': 0.35,
                    })

    # ============================================================
    # 去重：同一区域的候选行，只保留置信度最高的
    # ============================================================
    candidates.sort(key=lambda x: (x['line_idx'], -x['confidence']))
    merged = []
    last_idx = -5  # 至少间隔 5 行才算不同章节
    for c in candidates:
        if c['line_idx'] - last_idx >= 5:
            merged.append(c)
            last_idx = c['line_idx']
        elif merged and c['confidence'] > merged[-1]['confidence']:
            merged[-1] = c

    # ============================================================
    # 过滤：在高候选数时过滤低置信度
    # ============================================================
    high_conf = [c for c in merged if c['confidence'] >= 0.6]
    if len(high_conf) >= 3:
        merged = [c for c in merged if c['confidence'] >= 0.3]

    # ============================================================
    # 策略 3：如果仍然太少，用 "——" 分隔符作为章节边界
    # （来自 EPUB 提取的章节分隔符）
    # ============================================================
    if len(merged) <= 1:
        separator_pattern = re.compile(r'^[\s]*[—\-]{10,}[\s]*$')
        separator_positions = []
        for i, line in enumerate(lines):
            if separator_pattern.match(line):
                separator_positions.append(i)

        if len(separator_positions) > 1:
            merged = []
            for i, pos in enumerate(separator_positions):
                merged.append({
                    'line_idx': pos + 1,  # 分隔符之后的第一行
                    'title': f'第{i + 1}部分',
                    'method': 'separator',
                    'confidence': 0.45,
                })

    # ============================================================
    # 策略 4：最后的回退——按字符数均分
    # ============================================================
    if len(merged) <= 1:
        text_len = len(text)
        if text_len > 30000:
            chunk_size = 15000
            num_chunks = max(2, text_len // chunk_size)
            merged = []
            for i in range(num_chunks):
                char_pos = int((i * text_len) / num_chunks)
                line_idx = text[:char_pos].count('\n')
                merged.append({
                    'line_idx': line_idx,
                    'title': f'第{i + 1}部分（自动分段）',
                    'method': 'char_chunk',
                    'confidence': 0.1,
                })

    # ============================================================
    # 构建章节列表：将行索引转换为字符位置
    # ============================================================
    # 计算每行的起始字符位置
    line_starts = [0]
    for line in lines[:-1]:
        line_starts.append(line_starts[-1] + len(line) + 1)  # +1 for \n

    chapters = []
    for i, candidate in enumerate(merged):
        start_line = candidate['line_idx']
        if i < len(merged) - 1:
            end_line = merged[i + 1]['line_idx'] - 1
        else:
            end_line = len(lines) - 1

        end_line = max(end_line, start_line)

        start_char = line_starts[start_line] if start_line < len(line_starts) else 0
        end_char = line_starts[end_line] if end_line < len(line_starts) else len(text)

        if end_line < len(lines):
            end_char += len(lines[end_line])
        end_char = min(end_char, len(text))

        char_count = end_char - start_char

        chapters.append({
            'index': i,
            'title': candidate['title'],
            'start_char': start_char,
            'end_char': end_char,
            'char_count': char_count,
            'detection_method': candidate['method'],
        })

    # ============================================================
    # 合并太短的章节（有显式标记的合并到下一个同类型章节）
    # 但只在章节确实是"标题页"（非常短）时才合并
    # ============================================================
    final_chapters = []
    i = 0
    while i < len(chapters):
        ch = chapters[i]
        # 仅对极短章节（< 150 字符）且不是最后一个时进行合并
        if ch['char_count'] < 150 and i < len(chapters) - 1:
            # 合并到下一个章节
            next_ch = chapters[i + 1]
            combined = {
                'index': next_ch['index'],
                'title': f'{ch["title"]} / {next_ch["title"]}',
                'start_char': ch['start_char'],
                'end_char': next_ch['end_char'],
                'char_count': ch['char_count'] + next_ch['char_count'],
                'detection_method': f'{ch["detection_method"]}+{next_ch["detection_method"]}',
            }
            final_chapters.append(combined)
            i += 2
        else:
            final_chapters.append(ch)
            i += 1

    return final_chapters


def main():
    if len(sys.argv) < 2:
        print('用法: python3 detect_chapters.py <输入.txt>', file=sys.stderr)
        print('', file=sys.stderr)
        print('检测文本中的章节边界，输出 JSON 格式的章节列表。', file=sys.stderr)
        sys.exit(1)

    input_path = sys.argv[1]

    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            text = f.read()
    except FileNotFoundError:
        print(f'错误: 文件不存在 "{input_path}"', file=sys.stderr)
        sys.exit(1)

    chapters = detect_chapters(text)

    output = {
        'source': input_path,
        'total_chars': len(text),
        'chapter_count': len(chapters),
        'chapters': chapters,
    }

    # 始终输出 JSON
    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
