from __future__ import annotations

import codecs
import re
import zipfile
from pathlib import Path
from typing import Callable

# Match markup without parsing/serializing it: resource paths, entities, namespace
# prefixes, comments and original formatting remain untouched.
TOKEN = re.compile(r'<!--.*?-->|<!\[CDATA\[.*?\]\]>|<\?.*?\?>|<!DOCTYPE(?:[^>\[]|\[[\s\S]*?\])*>|</?[A-Za-z_][\w:.-]*(?:[^>"\']|"[^"]*"|\'[^\']*\')*>', re.S | re.I)
NAME = re.compile(r'<\s*(/?)\s*([\w:.-]+)')
ENCODING = re.compile(br'<\?xml\s+[^>]*encoding\s*=\s*["\']([^"\']+)', re.I)
TEXT_EXTENSIONS = {'.xhtml', '.html', '.htm', '.ncx', '.opf'}
SKIP_TAGS = {'script', 'style', 'code', 'pre', 'identifier'}
OPF_TEXT = {'title', 'creator', 'contributor', 'publisher', 'description', 'subject', 'rights'}


def _decode(data: bytes) -> tuple[str, str]:
    if data.startswith((codecs.BOM_UTF16_LE, codecs.BOM_UTF16_BE)):
        return data.decode('utf-16'), 'utf-16-le-bom' if data.startswith(codecs.BOM_UTF16_LE) else 'utf-16-be-bom'
    if data.startswith(codecs.BOM_UTF8):
        return data.decode('utf-8-sig'), 'utf-8-sig'
    match = ENCODING.search(data[:512])
    encoding = match.group(1).decode('ascii') if match else 'utf-8'
    return data.decode(encoding), encoding


def _encode(text: str, encoding: str) -> bytes:
    if encoding == 'utf-16-le-bom':
        return codecs.BOM_UTF16_LE + text.encode('utf-16-le')
    if encoding == 'utf-16-be-bom':
        return codecs.BOM_UTF16_BE + text.encode('utf-16-be')
    return text.encode(encoding)


def convert_markup(data: bytes, convert: Callable[[str], str], *, opf: bool = False) -> bytes:
    text, encoding = _decode(data)
    stack: list[str] = []
    chunks: list[str] = []
    last = 0
    for match in TOKEN.finditer(text):
        segment = text[last:match.start()]
        permitted = not any(tag in SKIP_TAGS for tag in stack)
        if opf:
            permitted = permitted and bool(stack) and stack[-1] in OPF_TEXT and 'metadata' in stack
        chunks.append(convert(segment) if permitted else segment)
        token = match.group()
        chunks.append(token)
        tag = NAME.match(token)
        if tag:
            closing, name = tag.groups()
            name = name.lower().split(':')[-1]
            if closing:
                # Malformed documents remain structurally unchanged, but avoid
                # inferring context beyond the nearest matching opening tag.
                if name in stack:
                    del stack[len(stack) - 1 - stack[::-1].index(name):]
            elif not token.rstrip().endswith('/>') and name not in {'br', 'hr', 'img', 'meta', 'link', 'input', 'wbr', 'source', 'area', 'embed', 'param', 'col', 'base'}:
                stack.append(name)
        last = match.end()
    tail = text[last:]
    permitted = not any(tag in SKIP_TAGS for tag in stack)
    if opf:
        permitted = permitted and bool(stack) and stack[-1] in OPF_TEXT and 'metadata' in stack
    chunks.append(convert(tail) if permitted else tail)
    return _encode(''.join(chunks), encoding)


def convert_epub(source: Path, destination: Path, convert: Callable[[str], str]) -> None:
    source, destination = source.resolve(), destination.resolve()
    if source == destination:
        raise ValueError('输入和输出不能是同一个文件')
    with zipfile.ZipFile(source, 'r') as zin:
        entries = zin.infolist()
        names = [entry.filename for entry in entries]
        if len(names) != len(set(names)):
            raise ValueError('EPUB 包含重复文件名，无法安全转换')
        if 'mimetype' not in names or zin.read('mimetype') != b'application/epub+zip':
            raise ValueError('不是有效的 EPUB：缺少正确的 mimetype')
        if any(entry.flag_bits & 1 for entry in entries):
            raise ValueError('不支持加密的 ZIP 条目')
        if 'META-INF/encryption.xml' in names:
            raise ValueError('检测到 EPUB 加密信息；本工具不支持加密或混淆资源')
        converted: list[tuple[zipfile.ZipInfo, bytes]] = []
        for info in entries:
            if info.filename == 'mimetype':
                continue
            data = zin.read(info)
            suffix = Path(info.filename).suffix.lower()
            if suffix in TEXT_EXTENSIONS:
                data = convert_markup(data, convert, opf=suffix == '.opf')
            converted.append((info, data))
        # Exclusive creation prevents overwriting an existing book.
        with destination.open('xb') as output, zipfile.ZipFile(output, 'w') as zout:
            zout.writestr('mimetype', b'application/epub+zip', compress_type=zipfile.ZIP_STORED)
            for info, data in converted:
                zout.writestr(info, data)
