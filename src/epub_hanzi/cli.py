from __future__ import annotations

import argparse
import sys
from pathlib import Path
from zipfile import BadZipFile

from opencc import OpenCC
from .converter import convert_epub


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='将 EPUB 繁体中文转换为简体中文，全部在本机处理。')
    parser.add_argument('inputs', nargs='+', type=Path, help='一个或多个 EPUB 文件')
    parser.add_argument('-o', '--output-dir', type=Path, help='输出目录；默认与原文件相同')
    parser.add_argument('--mode', choices=('t2s', 'tw2sp', 'hk2s'), default='t2s', help='转换模式：t2s（默认）、tw2sp（台湾用语）、hk2s（香港字形）')
    args = parser.parse_args(argv)
    if args.output_dir and not args.output_dir.is_dir():
        parser.error('输出目录不存在：' + str(args.output_dir))
    converter = OpenCC(args.mode)
    failures = 0
    for source in args.inputs:
        target = (args.output_dir or source.parent) / (source.stem + '.简体.epub')
        try:
            if source.suffix.lower() != '.epub' or not source.is_file():
                raise ValueError('输入必须是存在的 EPUB 文件')
            convert_epub(source, target, converter.convert)
            print(f'完成：{source} → {target}')
        except (OSError, ValueError, UnicodeError, LookupError, BadZipFile, RuntimeError) as exc:
            failures += 1
            print(f'失败：{source}：{exc}', file=sys.stderr)
    return 1 if failures else 0


if __name__ == '__main__':
    raise SystemExit(main())
