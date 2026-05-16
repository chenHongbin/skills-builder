#!/usr/bin/env python3
"""
Book Mirror - EPUB 文本提取器
纯 Python 标准库实现，不需要安装任何 pip 依赖。
支持 EPUB 2 和 EPUB 3 格式。

用法：python3 extract_epub.py <输入.epub> [输出.txt]
"""

import html.parser
import io
import json
import os
import re
import sys
import xml.etree.ElementTree as ET
import zipfile


class HTMLStripper(html.parser.HTMLParser):
    """去除 HTML 标签，保留纯文本，同时在块级元素后插入换行。"""

    # 块级元素——其后需要换行来保留段落结构
    BLOCK_TAGS = {
        'br', 'p', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
        'li', 'tr', 'blockquote', 'section', 'article', 'hr',
        'pre', 'table', 'ul', 'ol', 'dl', 'dt', 'dd',
    }

    def __init__(self):
        super().__init__()
        self.text_parts = []
        self._current_tag = None

    def handle_starttag(self, tag, attrs):
        self._current_tag = tag
        # 在标题前加标记，帮助后续的章节检测
        if tag in ('h1', 'h2', 'h3'):
            self.text_parts.append('\n')

    def handle_endtag(self, tag):
        if tag in self.BLOCK_TAGS:
            self.text_parts.append('\n')
        self._current_tag = None

    def handle_data(self, data):
        text = data.strip()
        if text:
            # 如果是标题标签内的文字，添加标题标记
            if self._current_tag in ('h1', 'h2', 'h3'):
                self.text_parts.append(f'[{self._current_tag.upper()}] {text}\n')
            else:
                self.text_parts.append(text + ' ')

    def get_text(self):
        return ''.join(self.text_parts)


def clean_text(text):
    """清理提取后的文本：合并多余空行、规范化空格。"""
    # 合并连续3个以上换行为2个
    text = re.sub(r'\n{3,}', '\n\n', text)
    # 去除行首行尾空格
    lines = [line.strip() for line in text.split('\n')]
    # 移除连续空行
    result = []
    prev_empty = False
    for line in lines:
        is_empty = not line
        if is_empty and prev_empty:
            continue
        result.append(line)
        prev_empty = is_empty
    return '\n'.join(result)


def is_photo_page(filename, content):
    """判断是否为纯图片页（照片页），应跳过分析。"""
    basename = os.path.basename(filename).lower()
    # 文件名含 photo 且内容极少 → 照片页
    if 'photo' in basename:
        stripped = HTMLStripper()
        stripped.feed(content)
        text = stripped.get_text().strip()
        if len(text) < 200:
            return True
    return False


def extract_epub(epub_path, output_path):
    """从 EPUB 文件中提取纯文本。"""
    # 打开 EPUB（本质是 ZIP 文件）
    try:
        z = zipfile.ZipFile(epub_path)
    except zipfile.BadZipFile:
        print(f'错误: 无法打开 EPUB 文件 "{epub_path}"。文件可能已损坏。', file=sys.stderr)
        sys.exit(1)

    # 步骤 1：读取 container.xml，找到 OPF 文件路径
    try:
        container_xml = z.read('META-INF/container.xml').decode('utf-8')
    except KeyError:
        print('错误: EPUB 文件中缺少 META-INF/container.xml', file=sys.stderr)
        sys.exit(1)

    # 注册命名空间
    ns_container = 'urn:oasis:names:tc:opendocument:xmlns:container'
    ET.register_namespace('', ns_container)
    container_root = ET.fromstring(container_xml)

    # 查找 rootfile 元素
    rootfile = container_root.find(f'.//{{{ns_container}}}rootfile')
    if rootfile is None:
        # 尝试不带命名空间
        for elem in container_root.iter():
            if 'rootfile' in elem.tag:
                rootfile = elem
                break
    if rootfile is None:
        print('错误: 在 container.xml 中找不到 rootfile', file=sys.stderr)
        sys.exit(1)

    opf_path = rootfile.get('full-path')
    if not opf_path:
        print('错误: rootfile 缺少 full-path 属性', file=sys.stderr)
        sys.exit(1)

    # 步骤 2：解析 OPF 文件
    opf_dir = os.path.dirname(opf_path)
    try:
        opf_xml = z.read(opf_path).decode('utf-8')
    except KeyError:
        print(f'错误: 找不到 OPF 文件 "{opf_path}"', file=sys.stderr)
        sys.exit(1)

    # 提取元数据
    opf_root = ET.fromstring(opf_xml)

    # 查找 manifest 和 spine
    manifest = {}
    spine_ids = []

    # 注册常见 EPUB 命名空间
    ns_opf = 'http://www.idpf.org/2007/opf'

    # manifest: id → href 映射
    for elem in opf_root.iter():
        tag = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
        if tag == 'manifest':
            for item in elem:
                item_id = item.get('id')
                item_href = item.get('href')
                item_type = item.get('media-type', '')
                if item_id and item_href:
                    manifest[item_id] = {
                        'href': item_href,
                        'media_type': item_type,
                    }

        # spine: reading order (idref 列表)
        if tag == 'spine':
            for itemref in elem:
                spine_ids.append(itemref.get('idref'))

    # 步骤 3：按 spine 顺序提取文本
    all_texts = []
    chapter_separator = '\n\n' + '—' * 40 + '\n\n'
    skipped_count = 0
    extracted_count = 0

    for spine_id in spine_ids:
        if spine_id not in manifest:
            continue

        info = manifest[spine_id]
        href = info['href']

        # 跳过非 XHTML 内容
        if 'xhtml' not in info['media_type'] and 'html' not in info['media_type']:
            continue

        # 构建完整路径
        if opf_dir:
            full_path = os.path.normpath(os.path.join(opf_dir, href))
        else:
            full_path = href

        # 读取文件内容
        try:
            content_bytes = z.read(full_path)
        except KeyError:
            # 路径可能在 ZIP 中使用 / 分隔
            alt_path = '/'.join(full_path.split('\\'))
            try:
                content_bytes = z.read(alt_path)
                # 如果成功，更新 full_path 为备用路径
            except KeyError:
                print(f'警告: 跳过缺失文件 "{full_path}"', file=sys.stderr)
                skipped_count += 1
                continue

        # 解码
        try:
            content = content_bytes.decode('utf-8')
        except UnicodeDecodeError:
            try:
                content = content_bytes.decode('latin-1')
            except UnicodeDecodeError:
                try:
                    content = content_bytes.decode('gbk')
                except UnicodeDecodeError:
                    content = content_bytes.decode('utf-8', errors='replace')

        # 跳过照片页
        if is_photo_page(href, content):
            skipped_count += 1
            continue

        # 跳过封面和目录页（但保留 titlePageContent，它们有实际内容）
        basename = os.path.basename(href).lower()
        if basename.startswith('cover') or basename == 'cover.xhtml':
            skipped_count += 1
            continue

        # 提取纯文本
        stripper = HTMLStripper()
        stripper.feed(content)
        text = stripper.get_text()

        # 只添加有实质内容的页面（至少 100 个字符）
        if len(text.strip()) < 100:
            skipped_count += 1
            continue

        # 添加章节标题标记
        title_match = re.search(r'<title>(.*?)</title>', content, re.DOTALL)
        page_title = title_match.group(1).strip() if title_match else ''
        if page_title:
            all_texts.append(f'## {page_title}\n\n{text}')
        else:
            all_texts.append(text)

        extracted_count += 1

    z.close()

    # 合并所有文本
    full_text = chapter_separator.join(all_texts)
    full_text = clean_text(full_text)

    # 写入输出
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(full_text)

    # 输出统计信息（JSON 格式，供调用者解析）
    stats = {
        'source': epub_path,
        'output': output_path,
        'total_chars': len(full_text),
        'sections_extracted': extracted_count,
        'sections_skipped': skipped_count,
        'total_sections': len(spine_ids),
    }
    print(json.dumps(stats))


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('用法: python3 extract_epub.py <输入.epub> [输出.txt]', file=sys.stderr)
        print('', file=sys.stderr)
        print('说明: 纯 Python 标准库实现，不需要安装任何依赖。', file=sys.stderr)
        print('支持 EPUB 2 和 EPUB 3 格式。', file=sys.stderr)
        sys.exit(1)

    input_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else '/tmp/book_mirror_full.txt'

    if not os.path.exists(input_path):
        print(f'错误: 文件不存在 "{input_path}"', file=sys.stderr)
        sys.exit(1)

    extract_epub(input_path, output_path)
