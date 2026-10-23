#!/usr/bin/env python3
"""Generate an inactive, validated books -> GitHub Pages routing bundle.

Run against a reviewed public static export, on a trusted machine. This program
does not connect to servers, publish content, or modify installed Nginx files.
"""

import argparse
import hashlib
import json
import re
import zipfile
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit, quote as urlquote


PUBLIC_ORIGIN = "https://ds.sumeun.org"
REMOTE_ROOT = "/srv/ds-static"
QUERY_FIELDS = ('p', 'page_id', 'cat', 'tag', 'm', 'author', 'paged', 'feed', 'page', 'attachment_id')


class CanonicalParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.canonicals = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "link" and "canonical" in attrs.get("rel", "").lower().split():
            self.canonicals.append(attrs.get("href"))


def safe_path(value):
    if not isinstance(value, str) or not re.fullmatch(r"/[A-Za-z0-9/_.~%+\-]*", value):
        raise ValueError("Paths must be absolute URL paths, percent-encoded if necessary")
    decoded = unquote(value, errors="strict")
    if ("//" in decoded or any(p in (".", "..") for p in decoded.split("/"))
            or re.search(r'[\x00-\x20\x7f$"\\;{}?#%]', decoded)):
        raise ValueError("Unsafe or ambiguous URL path")
    return decoded


def check_export(site, public_archives=()):
    """Catch accidental backups/config inclusion before preparing deployment."""
    total = 0
    archives={safe_path(row['path']).lstrip('/'):row['sha256'] for row in public_archives}
    for path in site.rglob("*"):
        relative = path.relative_to(site)
        if path.is_symlink():
            raise ValueError("Static export contains a symlink: " + str(relative))
        if any(part.startswith(".") and part not in (".nojekyll", ".well-known")
               for part in relative.parts):
            raise ValueError("Hidden file/directory in export: " + str(relative))
        if path.is_file():
            if path.name == "CNAME":
                raise ValueError("Use the github.io origin behind books; do not set a ds CNAME")
            if path.suffix.lower() in (".php", ".sql", ".sqlite", ".db", ".pem", ".key", ".ini", ".gz", ".tar", ".bak"):
                raise ValueError("Review non-public/backup file: " + str(relative))
            if path.suffix.lower()=='.zip':
                if archives.get(str(relative))!=hashlib.sha256(path.read_bytes()).hexdigest():
                    raise ValueError('Archive needs a verified public-download manifest: '+str(relative))
                with zipfile.ZipFile(path) as archive:
                    for member in archive.infolist():
                        name=member.filename.lower()
                        if name.startswith('/') or '..' in Path(name).parts or any(v in name for v in ('wp-config','.env','.sql','.pem','.key','.git/')):
                            raise ValueError('Archive contains an unsafe or private configuration filename')
            size = path.stat().st_size
            if size >= 100 * 1024 * 1024:
                raise ValueError("File needs a separate large-file hosting decision: " + str(relative))
            total += size
    if total >= 1_000_000_000:
        raise ValueError("Export reaches the conservative 1 GB Pages size gate")
    if not (site / "index.html").is_file():
        raise ValueError("Export is missing index.html")
    return total


def prepare(manifest, site, upstream, permanent=False):
    site = Path(site).resolve(strict=True)
    total = check_export(site, manifest.get('public_archives', []))
    parsed = urlsplit(upstream)
    if (parsed.scheme != "https" or parsed.query or parsed.fragment
            or not re.fullmatch(r"[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?\.github\.io", parsed.netloc)):
        raise ValueError("Origin must be https://OWNER.github.io/ or /REPOSITORY/")
    if not re.fullmatch(r"/(?:[A-Za-z0-9_-][A-Za-z0-9_.-]*/)?", parsed.path):
        raise ValueError("Origin must have a trailing slash and at most one repository path")
    entries = manifest.get("posts")
    if not isinstance(entries, list) or not entries:
        raise ValueError("A nonempty reviewed public posts manifest is required")
    ids, aliases = {}, {}
    for entry in entries:
        post_id = entry.get("id")
        if type(post_id) is not int or post_id <= 0 or post_id in ids:
            raise ValueError("Post IDs must be unique positive integers")
        if entry.get("public") is not True:
            raise ValueError("Every mapped item must be explicitly reviewed as public")
        target = entry.get("target")
        safe_path(target)
        if target not in (f"/posts/{post_id}/", f"/pages/{post_id}/"):
            raise ValueError("Target must match its post/page ID")
        html = (site / target.lstrip("/") / "index.html").resolve(strict=True)
        if site not in html.parents:
            raise ValueError("Target escapes the export directory")
        parser = CanonicalParser()
        parser.feed(html.read_text(encoding="utf-8"))
        if parser.canonicals != [PUBLIC_ORIGIN + target]:
            raise ValueError("Target must have exactly one matching public canonical: " + target)
        ids[post_id] = target
        for alias in entry.get("aliases", []):
            normalized = safe_path(alias)
            if normalized in ("/", "/index.php"):
                raise ValueError("The homepage cannot be a post alias")
            if normalized == target:
                continue
            if normalized in aliases and aliases[normalized] != target:
                raise ValueError("Conflicting alias: " + normalized)
            aliases[normalized] = target
    if set(aliases).intersection(ids.values()):
        raise ValueError("An alias shadows an exported canonical URL")

    query_routes = {}
    for post_id, target in sorted(ids.items()):
        for key in ('p', 'page_id'):
            values = {key: str(post_id)}
            signature = ':'.join(values.get(field, '') for field in QUERY_FIELDS)
            query_routes[signature] = target
    for entry in manifest.get('queries', []):
        args = entry.get('args')
        target = entry.get('target')
        if not isinstance(args, dict) or not args or set(args) - set(QUERY_FIELDS):
            raise ValueError('Unsupported query mapping')
        for key, value in args.items():
            if not isinstance(value, str) or (key == 'feed' and value not in ('rss2','rss','atom','rdf','comments-rss2')) or (key == 'tag' and not re.fullmatch(r'[\w.-]+',value)) or (key not in ('feed','tag') and not re.fullmatch(r'[0-9]+', value)):
                raise ValueError('Invalid query mapping value')
            if key in ('p', 'page_id') and int(value) not in ids:
                raise ValueError('Query mapping references a non-public ID')
        decoded_target = safe_path(target)
        path = site / decoded_target.lstrip('/')
        if target.endswith('/'): path /= 'index.html'
        path = path.resolve(strict=True)
        if site not in path.parents or not path.is_file():
            raise ValueError('Query target must be an exported file')
        signature = ':'.join(urlquote(args.get(field, ''),safe='-._~') for field in QUERY_FIELDS)
        if signature in query_routes and query_routes[signature] != target:
            raise ValueError('Conflicting query route')
        query_routes[signature] = target

    quote = lambda s: json.dumps(s, ensure_ascii=False)
    maps = ['# Included in the nginx http context.',
            'map_hash_bucket_size 128;', 'map_hash_max_size 8192;',
            'map "$arg_p:$arg_page_id" $ds_static_query_target {', '    default "";']
    for post_id, target in sorted(ids.items()):
        maps.extend([f'    "{post_id}:" {quote(target)};', f'    ":{post_id}" {quote(target)};'])
    maps.extend(['}', 'map $uri $ds_static_alias_target {', '    default "";'])
    maps.extend(f'    {quote(alias)} {quote(target)};' for alias, target in sorted(aliases.items()))
    maps.extend(['}', ''])
    expression = ':'.join('$arg_' + field for field in QUERY_FIELDS)
    maps.extend([f'map "{expression}" $ds_static_route_target {{', '    default "";'])
    maps.extend(f'    {quote(signature)} {quote(target)};' for signature, target in sorted(query_routes.items()))
    maps.extend(['}', 'map "' + ''.join('$arg_' + field for field in QUERY_FIELDS) + '" $ds_static_has_selector {',
                 '    default 1;', '    "" 0;', '}', ''])
    maps.extend(['map "$uri:$arg_day" $ds_static_date_target {', '    default "";'])
    for entry in manifest.get('dated_aliases', []):
        alias = entry.get('path'); day = entry.get('day'); target = entry.get('target')
        safe_path(alias); safe_path(target)
        if not re.fullmatch(r'/[0-9]{4}/[0-9]{1,2}/?', alias) or not re.fullmatch(r'[0-9]{0,2}', day):
            raise ValueError('Invalid date archive alias')
        path=(site/target.lstrip('/')/'index.html').resolve(strict=True)
        if site not in path.parents: raise ValueError('Date target escapes export')
        maps.append(f'    {quote(alias + ":" + day)} {quote(target)};')
    maps.extend(['}', ''])
    code = 301 if permanent else 302
    noindex = '' if permanent else '    add_header X-Robots-Tag "noindex, nofollow" always;\n'
    proxy = f'''# Included only inside the two static-content locations.
proxy_pass {upstream};
proxy_set_header Host {parsed.netloc};
proxy_ssl_server_name on;
proxy_ssl_name {parsed.netloc};
proxy_ssl_verify on;
proxy_ssl_trusted_certificate /etc/ssl/certs/ca-certificates.crt;
proxy_ssl_verify_depth 3;
proxy_set_header Cookie "";
proxy_set_header Authorization "";
proxy_set_header Referer "";
proxy_set_header X-Forwarded-For "";
proxy_set_header X-Real-IP "";
proxy_hide_header Set-Cookie;
proxy_connect_timeout 10s;
proxy_read_timeout 30s;
proxy_redirect {upstream} {PUBLIC_ORIGIN}/;
'''
    if parsed.path != '/':
        proxy += f'proxy_redirect {parsed.path} /;\n'
    config = f'''# INACTIVE TEMPLATE. Install only after TLS, baseline and live nginx -t checks.
# Included in the nginx http context. Never replace books server blocks.
include {REMOTE_ROOT}/routing/maps.conf;
server {{
    listen 80;
    listen [::]:80;
    server_name ds.sumeun.org;
    location ^~ /.well-known/acme-challenge/ {{
        root {REMOTE_ROOT}/acme;
        try_files $uri =404;
    }}
    location / {{ return {code} https://ds.sumeun.org$request_uri; }}
}}
server {{
    listen 443 ssl;
    listen [::]:443 ssl;
    server_name ds.sumeun.org;
    ssl_certificate /etc/letsencrypt/live/ds.sumeun.org/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/ds.sumeun.org/privkey.pem;
    access_log {REMOTE_ROOT}/logs/access.log combined;
    error_log {REMOTE_ROOT}/logs/error.log;
{noindex}    if ($request_method !~ ^(GET|HEAD)$) {{ return 405; }}
    if ($arg_preview != "") {{ return 404; }}
    if ($arg_sitemap != "") {{ return {code} https://ds.sumeun.org/sitemap.xml; }}
    if ($ds_static_date_target != "") {{
        return {code} https://ds.sumeun.org$ds_static_date_target;
    }}
    if ($ds_static_alias_target != "") {{
        return {code} https://ds.sumeun.org$ds_static_alias_target;
    }}
    location = / {{
        if ($ds_static_route_target != "") {{
            return {code} https://ds.sumeun.org$ds_static_route_target;
        }}
        if ($ds_static_has_selector) {{ return 404; }}
        if ($arg_s != "") {{ return 302 https://ds.sumeun.org/search/?q=$arg_s; }}
        include {REMOTE_ROOT}/routing/proxy.conf;
    }}
    location = /index.php {{
        if ($ds_static_route_target != "") {{
            return {code} https://ds.sumeun.org$ds_static_route_target;
        }}
        return 404;
    }}
    location ~* (?:\\.php(?:/|$)|^/(?:wp-admin|wp-json|mysqladmin|xhprof)(?:/|$)) {{
        return 404;
    }}
    location = /wp-sitemap.xml {{ return {code} https://ds.sumeun.org/sitemap.xml; }}
    location = /sitemap_index.xml {{ return {code} https://ds.sumeun.org/sitemap.xml; }}
    location ~ ^/wp-sitemap-[A-Za-z0-9_-]+\\.xml$ {{ return {code} https://ds.sumeun.org/sitemap.xml; }}
    # Already forbidden on the source; do not expose the underlying text file.
    location = /wp-content/uploads/2019/02/UTF-8test.txt {{ return 403; }}
    location / {{ include {REMOTE_ROOT}/routing/proxy.conf; }}
}}
'''
    return {'maps.conf': '\n'.join(maps), 'proxy.conf': proxy,
            'ds-static.conf': config,
            'summary.json': json.dumps({'public_origin': PUBLIC_ORIGIN, 'upstream': upstream,
                'posts': len(ids), 'aliases': len(aliases), 'query_routes': len(query_routes), 'export_bytes': total,
                'mode': 'permanent' if permanent else 'rehearsal'}, indent=2) + '\n'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', required=True, type=Path)
    parser.add_argument('--site', required=True, type=Path)
    parser.add_argument('--upstream', required=True)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--permanent', action='store_true', help='301 redirects; remove rehearsal noindex')
    args = parser.parse_args()
    result = prepare(json.loads(args.manifest.read_text()), args.site, args.upstream, args.permanent)
    args.output.mkdir(parents=True, exist_ok=False)
    for name, content in result.items():
        (args.output / name).write_text(content, encoding='utf-8')
    print(result['summary.json'], end='')


if __name__ == '__main__':
    main()
