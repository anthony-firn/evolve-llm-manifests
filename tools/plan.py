#!/usr/bin/env python3
"""Plan manifest jobs: every part of each requested Hugging Face GGUF, with its SHA-256 and the
commit to read it at, skipping files whose manifest already exists in v1/.

Reads "owner/repo path/to/file.gguf" lines from $FILES (any part of a split model stands for
every part) and prints a JSON list for a GitHub Actions matrix.
"""
import json
import os
import re
import sys
import urllib.parse
import urllib.request

SPLIT = re.compile(r'^(.*)-(\d{5})-of-(\d{5})\.gguf$')


def get(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'evolve-llm-manifest-plan'})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def main():
    jobs, seen = [], set()
    for line in os.environ.get('FILES', '').splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        repo, path = line.split(None, 1)
        if not re.fullmatch(r'[\w.-]+/[\w.-]+', repo):
            sys.exit(f'not a repository name: {repo!r}')
        info = get(f'https://huggingface.co/api/models/{repo}')
        revision = info['sha']
        tree = get(f'https://huggingface.co/api/models/{repo}/tree/{revision}?recursive=1')
        files = {f['path']: f for f in tree if f.get('type') == 'file'}
        m = SPLIT.match(path)
        names = [f'{m.group(1)}-{i:05d}-of-{m.group(3)}.gguf' for i in range(1, int(m.group(3)) + 1)] if m else [path]
        for name in names:
            f = files.get(name)
            if not f or not f.get('lfs'):
                sys.exit(f'{repo}: {name} is not an LFS file in the repository')
            sha = f['lfs']['oid']
            if sha in seen or os.path.exists(f'v1/{sha}/index.json'):
                continue
            seen.add(sha)
            jobs.append({'repo': repo, 'path': name, 'sha256': sha, 'size': f['lfs']['size'], 'revision': revision})
    print(json.dumps(jobs))


if __name__ == '__main__':
    main()
