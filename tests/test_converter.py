import tempfile
import unittest
import zipfile
from pathlib import Path
from opencc import OpenCC
from epub_hanzi.converter import convert_epub, convert_markup


class ConverterTests(unittest.TestCase):
    def setUp(self):
        self.convert = OpenCC('t2s').convert

    def test_markup_preserves_identifiers_paths_and_scripts(self):
        raw = '<html><body><a href="書籍.xhtml" title="書名">繁體書籍</a><script>var 名稱="繁體";</script><style>.繁體{}</style><!-- 繁體 --></body></html>'.encode()
        result = convert_markup(raw, self.convert).decode()
        self.assertIn('href="書籍.xhtml" title="書名">繁体书籍', result)
        self.assertIn('<script>var 名稱="繁體";</script>', result)
        self.assertIn('<style>.繁體{}</style><!-- 繁體 -->', result)

    def test_metadata_and_utf16(self):
        raw = '<?xml version="1.0" encoding="UTF-16"?><package><metadata><dc:title>繁體書</dc:title><dc:identifier>書號</dc:identifier></metadata></package>'.encode('utf-16')
        result = convert_markup(raw, self.convert, opf=True).decode('utf-16')
        self.assertIn('<dc:title>繁体书</dc:title>', result)
        self.assertIn('<dc:identifier>書號</dc:identifier>', result)

    def test_epub_layout_resources_and_no_overwrite(self):
        root = Path(tempfile.mkdtemp(prefix='epub-hanzi-test-'))
        source = root / 'source.epub'; output = root / 'out.epub'
        with zipfile.ZipFile(source, 'w') as archive:
            archive.writestr('mimetype', b'application/epub+zip')
            archive.writestr('OEBPS/book.xhtml', '<p>繁體書</p>')
            archive.writestr('OEBPS/書籍.png', b'\x89PNG\x00\xff')
        convert_epub(source, output, self.convert)
        with zipfile.ZipFile(output) as archive:
            self.assertEqual(archive.infolist()[0].filename, 'mimetype')
            self.assertEqual(archive.infolist()[0].compress_type, zipfile.ZIP_STORED)
            self.assertIn('繁体书', archive.read('OEBPS/book.xhtml').decode())
            self.assertEqual(archive.read('OEBPS/書籍.png'), b'\x89PNG\x00\xff')
        with self.assertRaises(FileExistsError):
            convert_epub(source, output, self.convert)

    def test_encryption_is_rejected(self):
        root = Path(tempfile.mkdtemp(prefix='epub-hanzi-test-'))
        source = root / 'source.epub'; output = root / 'out.epub'
        with zipfile.ZipFile(source, 'w') as archive:
            archive.writestr('mimetype', b'application/epub+zip')
            archive.writestr('META-INF/encryption.xml', '<encryption/>')
        with self.assertRaisesRegex(ValueError, '加密'):
            convert_epub(source, output, self.convert)
        self.assertFalse(output.exists())

if __name__ == '__main__':
    unittest.main()
