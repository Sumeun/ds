# 숨은원리 데이터사이언스

Public static blog migrated from https://ds.sumeun.org.

The initial export preserves 140 public posts, one public page and 40 approved
public comments/pingbacks. Password-protected/private posts and hidden comments
are excluded. Existing comments are read-only; new commenting is not enabled.

## Hosting

Public address: https://ds.sumeun.org (the original WordPress server remains
active until the migration DNS cutover).
GitHub Pages origin: https://sumeun.github.io/ds/.
Books Nginx handles legacy query URLs and proxies the static origin. Do not set
a Pages CNAME for ds.sumeun.org in this repository.

## Editing and publishing

The site directory contains editable, saved HTML plus its static assets. This is
an HTML snapshot blog, not a running WordPress installation or a Markdown/Jekyll
theme. The initial snapshot keeps the existing theme and rendered math/tools.
Edit an existing article at site/posts/ID/index.html. Keep its public canonical
URL and comment IDs. The old WordPress server is not needed to build or publish
this repository. New articles also need homepage/archive/search-index/sitemap
and public-manifest updates; an authoring generator can be added separately.

Actions -> Publish reviewed static blog -> Run workflow:
- Leave production false for a preview with noindex metadata.
- Use production true only when the domain routing and migration checks pass.

Only the built _site artifact is published. The workflow validates every mapped
public post target and canonical URL before deploying. It does not upload raw
WordPress databases, users, statistics or server credentials.

For an offline build with Python 3:

~~~bash
python3 tools/build_site.py --source site --output _site --mode preview
python3 tools/prepare_routing.py --manifest public-manifest.json --site _site --upstream https://sumeun.github.io/ds/ --output _validated-routing
~~~

The public-manifest.json file also records known archive/feed/calendar query
mappings. The text-file URL returning 403 and missing inner.jpg already failed
on the original site; no underlying forbidden source file is included here.
