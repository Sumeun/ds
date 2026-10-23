#!/usr/bin/env python3
"""Build saved, editable public HTML without depending on the old WordPress host."""
import argparse
from html.parser import HTMLParser
from pathlib import Path
import shutil


class Robots(HTMLParser):
    def __init__(self, preview):
        super().__init__(convert_charrefs=False)
        self.preview = preview
        self.output = []
        self.head_closed = False
    def handle_starttag(self, tag, attrs):
        if tag == 'meta' and dict(attrs).get('name', '').lower() == 'robots':
            return
        self.output.append(self.get_starttag_text())
    def handle_startendtag(self, tag, attrs): self.handle_starttag(tag, attrs)
    def handle_endtag(self, tag):
        if tag == 'head' and not self.head_closed:
            self.head_closed = True
            content = 'noindex,nofollow,max-image-preview:large' if self.preview else 'max-image-preview:large'
            self.output.append('<meta name="robots" content="'+content+'">')
        self.output.append('</' + tag + '>')
    def handle_data(self, data): self.output.append(data)
    def handle_entityref(self, name): self.output.append('&' + name + ';')
    def handle_charref(self, name): self.output.append('&#' + name + ';')
    def handle_comment(self, data): self.output.append('<!--' + data + '-->')
    def handle_decl(self, data): self.output.append('<!' + data + '>')


def build(source, output, mode):
    source = source.resolve(strict=True)
    output = output.resolve()
    if source == output or source in output.parents or output in source.parents:
        raise ValueError('Source and output must be separate directories')
    if output.exists():
        raise ValueError('Output already exists; use a fresh build directory')
    if any(p.is_symlink() for p in source.rglob('*')):
        raise ValueError('Source must not contain symlinks')
    shutil.copytree(source, output)
    for path in output.rglob('*.html'):
        # Missing pages and search-result URLs should never enter the index.
        parser = Robots(mode == 'preview' or path.name == '404.html')
        parser.feed(path.read_text(encoding='utf-8'))
        path.write_text(''.join(parser.output), encoding='utf-8')
    (output / 'robots.txt').write_text('User-agent: *\n' +
        ('Allow: /\n' if mode == 'preview' else 'Allow: /\nSitemap: https://ds.sumeun.org/sitemap.xml\n'))
    (output / '.nojekyll').touch()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--mode', choices=['preview', 'production'], default='preview')
    args = parser.parse_args()
    build(args.source, args.output, args.mode)


if __name__ == '__main__': main()
