# EPUB 汉字转换器

在本机将 EPUB 电子书从繁体中文转换为简体中文。支持一次处理多本书，不修改原文件，不上传书籍。

项目受 [神奇海螺 ePub 繁简转换](https://v.magiconch.com/epub-transform) 的功能启发，代码独立编写；文字转换使用 [OpenCC](https://github.com/BYVoid/OpenCC) 的 Python 实现，未复制该网站的代码或字表。

## 安装

需要 Python 3.10 或更高版本。在项目目录打开 PowerShell 或终端：

```powershell
py -m pip install .
```

macOS / Linux 使用：

```sh
python3 -m pip install .
```

安装后使用 `epub-hanzi` 命令。也可以用 `python -m epub_hanzi.cli` 替代该命令。

## 使用

```powershell
epub-hanzi "D:\书籍\繁體書.epub"
epub-hanzi "D:\书籍\第一本.epub" "D:\书籍\第二本.epub"
epub-hanzi --mode tw2sp --output-dir "D:\转换结果" "D:\书籍\繁體書.epub"
```

输出目录必须已存在。默认在原书旁生成 `原文件名.简体.epub`；若输出文件已存在，工具会报错，不会覆盖。可以通过 PowerShell 传入目录里的 EPUB 文件：

```powershell
Get-ChildItem "D:\书籍\*.epub" | ForEach-Object { epub-hanzi $_.FullName }
```

模式：`t2s`（默认，繁体字转简体）、`tw2sp`（台湾字形及词汇转大陆用语）、`hk2s`（香港字形转简体）。转换准确性取决于 OpenCC 词典，建议检查专有名词和少见字。

## 处理范围与限制

- 转换 XHTML、HTML、NCX 中的普通文本，以及 OPF 中常见书籍元数据的文本；保留标签、属性、链接路径、标识符、注释和 CDATA。`script`、`style`、`code`、`pre` 不转换；CSS、图片、字体等不处理。
- 为尽量保留原始排版，程序使用标记扫描而非完整 HTML/XML 解析器。格式不规范的文档、复杂 DOCTYPE、少见标记结构、内嵌 SVG 文本、属性中的可见文字、图片里的文字以及被标签拆开的词语可能无法正确处理。建议用 EPUB 阅读器检查结果并保留原书。
- `META-INF/encryption.xml` 或 ZIP 加密条目会被拒绝；这也会拒绝仅对字体做混淆的 EPUB。不绕过 DRM。
- 程序把条目读入内存，不适合超大文件。转换过程中若写入失败，可能留下不完整的输出文件；请检查后手动删除，再重试。
- EPUB 的 `mimetype` 写在首项且不压缩，其余 ZIP 条目与资源文件名保持原样。并非 EPUB 标准完整校验器。

## 开发与测试

```powershell
py -m pip install -e .
py -m unittest discover -s tests -v
```

测试会在系统临时目录创建带 `epub-hanzi-test-` 前缀的测试文件夹并保留，供手动检查和删除。

## 许可

本项目采用 [MIT 许可证](LICENSE)。依赖 `opencc-python-reimplemented` 单独采用 Apache-2.0 许可，使用及分发依赖时请查看其 [许可证与声明](https://github.com/yichen0831/opencc-python/tree/master/opencc)。本仓库不包含其代码或词典。发布到 GitHub 前，请确认仓库名称及许可符合你的意愿。
