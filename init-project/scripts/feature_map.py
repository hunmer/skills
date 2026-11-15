#!/usr/bin/env python3
"""feature_map 管线脚本（init-project skill 内置）。

用途：把「事实采集 / 数据刷新 / HTML 注入 / 校验」从模型现场发挥固化为可重跑脚本，
skill 升级（模板/管线变化）后各项目只需重跑本脚本即可同步，不依赖模型重做全流程。

语义判断仍归模型：功能归属（path → feature）以项目现有 docs/feature_map.json 为
唯一基准，脚本只做机械刷新 + 差异报告；新文件归属由模型按 `scan` 报告编辑 JSON。

子命令：
  scan    扫描代码文件事实，输出与现有 JSON 的差异报告（新增/消失/未归类），不改任何文件
  build   以现有 JSON 为归属基准，机械刷新全部 lines/gd 头注释 role/时间戳/git 提交，
          移除已消失文件，输出改动摘要（不自动收编新文件）
  render  模板 + JSON + vendor 库 → docs/feature_map.html（双占位符注入，含全部断言）
  check   覆盖率双向 diff + JSON 语法 + 产物占位符残留/seed 重解析校验
  all     build + render + check

用法：
  python3 feature_map.py scan  --root /path/to/project
  python3 feature_map.py all   --root /path/to/project
"""
import argparse
import json
import os
import re
import subprocess
import sys
from datetime import date

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_TEMPLATE = os.path.join(HERE, '..', 'templates', 'feature_map.html')
DEFAULT_VENDOR = os.path.join(HERE, '..', 'templates', 'vendor', 'vis-network.min.js')

CODE_EXTS = {'.gd', '.tscn', '.gdshader', '.mjs', '.sh', '.py'}
EXCLUDE_PREFIXES = ('addons/', '.claude/', '.godot/', '.dsh/')


# ---------- 基础事实 ----------

def git(root, *args):
    try:
        out = subprocess.run(['git', '-C', root, *args], capture_output=True, text=True)
        return out.stdout.strip() if out.returncode == 0 else None
    except Exception:
        return None


def code_files(root):
    """git 索引优先，非 git 目录回退 os.walk；返回相对路径集合（代码口径）。"""
    files = set()
    out = git(root, 'ls-files')
    if out is not None:
        files = {l.strip() for l in out.splitlines() if l.strip()}
    else:
        for dirpath, dirnames, names in os.walk(root):
            dirnames[:] = [d for d in dirnames if d not in ('.git', '.godot', 'addons', '.claude', '.dsh', 'node_modules')]
            for n in names:
                full = os.path.join(dirpath, n)
                files.add(os.path.relpath(full, root).replace(os.sep, '/'))
    return {p for p in files if os.path.splitext(p)[1] in CODE_EXTS and not p.startswith(EXCLUDE_PREFIXES)}


def head_role(root, path):
    """.gd 头部 `## xxx.gd — 职责` 注释提取（前 15 行内首个 ## 行，取 — 后文本）。"""
    full = os.path.join(root, path)
    try:
        with open(full, 'rb') as f:
            head = f.read(4096).decode('utf-8', errors='replace').splitlines()[:15]
    except OSError:
        return None
    for line in head:
        s = line.strip()
        if s.startswith('##'):
            s = s.lstrip('#').strip()
            for sep in ('—', '--', '—'):
                if sep in s:
                    s = s.split(sep, 1)[1].strip()
                    break
            return s or None
        if s and not s.startswith('#'):
            break
    return None


def line_count(root, path):
    try:
        with open(os.path.join(root, path), 'rb') as f:
            return sum(1 for _ in f)
    except OSError:
        return None


# ---------- JSON 遍历 ----------

def walk_features(doc):
    for cat in doc.get('tree', []):
        for feat in cat.get('children', []):
            yield cat, feat


def referenced_code_paths(doc):
    refs = set()
    for _, feat in walk_features(doc):
        for f in feat.get('files', []):
            if os.path.splitext(f['path'])[1] in CODE_EXTS:
                refs.add(f['path'])
        for t in feat.get('tests', []):
            refs.add(t['path'])
    for u in doc.get('unmapped', []):
        p = u.get('path') if isinstance(u, dict) else u
        if p and os.path.splitext(p)[1] in CODE_EXTS:
            refs.add(p)
    return refs


# ---------- 子命令 ----------

def cmd_scan(args):
    doc = load_doc(args)
    files = code_files(args.root)
    refs = referenced_code_paths(doc)
    new = sorted(files - refs)
    missing = sorted(p for p in refs if not os.path.exists(os.path.join(args.root, p)))
    print(f'代码文件（git/磁盘口径，排除 addons/.claude）: {len(files)}')
    print(f'JSON 已引用（含 tests/unmapped）: {len(refs)}')
    print(f'新增（未归类，需模型判断归属）: {len(new)}')
    for p in new:
        print(f'  + {p}')
    print(f'消失（JSON 引用但磁盘不存在）: {len(missing)}')
    for p in missing:
        print(f'  - {p}')
    return 0


def cmd_build(args):
    doc = load_doc(args)
    root = args.root
    n_lines = n_role = n_drop = 0
    dropped = []
    for _, feat in walk_features(doc):
        keep = []
        for f in feat.get('files', []):
            if not os.path.exists(os.path.join(root, f['path'])):
                dropped.append(f['path']); n_drop += 1
                continue
            lc = line_count(root, f['path'])
            if lc is not None and f.get('lines') != lc:
                f['lines'] = lc; n_lines += 1
            if f.get('type') == 'gd':
                r = head_role(root, f['path'])
                if r and f.get('role') != r:
                    f['role'] = r; n_role += 1
            keep.append(f)
        feat['files'] = keep
        feat['tests'] = [t for t in feat.get('tests', []) if os.path.exists(os.path.join(root, t['path']))]
    doc['unmapped'] = [u for u in doc.get('unmapped', [])
                       if os.path.exists(os.path.join(root, u['path'] if isinstance(u, dict) else '')) or not isinstance(u, dict)]
    if 'generated' in doc:
        doc['generated'] = date.today().isoformat()
    hc = git(root, 'rev-parse', '--short', 'HEAD')
    if hc:
        doc['head_commit'] = hc
    save_doc(args, doc)
    print(f'build 完成：lines 刷新 {n_lines}，gd role 刷新 {n_role}，移除消失文件 {n_drop}')
    for p in dropped:
        print(f'  - {p}')
    print('（新增文件不自动收编——跑 scan 查看未归类清单，由模型编辑 JSON 归属）')
    return 0


def cmd_render(args):
    tpl_path = args.template or DEFAULT_TEMPLATE
    vendor_path = args.vendor or DEFAULT_VENDOR
    tpl = open(tpl_path, encoding='utf-8').read()
    lib = open(vendor_path, encoding='utf-8').read()
    doc = load_doc(args)
    payload = json.dumps(doc, ensure_ascii=False, separators=(',', ':'))
    assert tpl.count('__JSON_SEED__') == 1, '模板 __JSON_SEED__ 占位符数 != 1（模板被改坏或注释混入字面量）'
    assert tpl.count('__VIS_LIB__') == 1, '模板 __VIS_LIB__ 占位符数 != 1'
    assert '</script' not in lib.lower(), 'vendor 库含 </script，不能内嵌'
    assert '</script' not in payload.lower(), 'JSON payload 含 </script，不能内嵌'
    gen = tpl.replace('__JSON_SEED__', payload).replace('__VIS_LIB__', lib)
    assert '__JSON_SEED__' not in gen and '__VIS_LIB__' not in gen, '注入后仍有占位符残留'
    m = re.search(r'<script type="application/json" id="seed">(.*?)</script>', gen, re.S)
    assert m, '产物中找不到 seed 块'
    seed = json.loads(m.group(1))
    assert seed == doc, '产物 seed 与 JSON 文件不同步'
    with open(args.html, 'w', encoding='utf-8') as f:
        f.write(gen)
    print(f'render 完成：{args.html}（{len(gen)} 字节）')
    import tempfile
    with tempfile.NamedTemporaryFile('w', suffix='.js', delete=False) as tf:
        tf.write(extract_main_js(gen))
        tmp = tf.name
    node = subprocess.run(['node', '--check', tmp], capture_output=True, text=True)
    os.unlink(tmp)
    if node.returncode == 0:
        print('主脚本 node --check 通过')
    else:
        print(f'⚠ node --check 失败（node 不可用或脚本错误）：{node.stderr[:400]}')
    return 0


def extract_main_js(gen):
    m = re.search(r"<script>\n('use strict';[\s\S]*?)\n</script>\n</body>", gen)
    return m.group(1) if m else ''


def cmd_check(args):
    doc = load_doc(args)
    files = code_files(args.root)
    refs = referenced_code_paths(doc)
    new = files - refs
    ghost = sorted(p for p in refs if not os.path.exists(os.path.join(args.root, p)))
    missing_all = sorted(p for p in iter_all_paths(doc) if not os.path.exists(os.path.join(args.root, p)))
    print(f'覆盖率：{len(refs & files)}/{len(files)} 代码文件已归类')
    ok = True
    if new:
        ok = False
        print(f'✗ 未归类 {len(new)} 个：')
        for p in sorted(new):
            print(f'    + {p}')
    if ghost:
        ok = False
        print(f'✗ 幽灵路径 {len(ghost)} 个（磁盘不存在）：')
        for p in ghost:
            print(f'    - {p}')
    if missing_all:
        print(f'⚠ 非代码条目缺失 {len(missing_all)} 个（md/config/data/dir 等）：')
        for p in missing_all:
            print(f'    - {p}')
    if os.path.exists(args.html):
        gen = open(args.html, encoding='utf-8').read()
        assert '__JSON_SEED__' not in gen and '__VIS_LIB__' not in gen, '产物有占位符残留'
        m = re.search(r'<script type="application/json" id="seed">(.*?)</script>', gen, re.S)
        assert m, '产物无 seed 块'
        seed = json.loads(m.group(1))
        assert seed == json.loads(json.dumps(doc, ensure_ascii=False)) or seed == doc, '产物 seed 与 JSON 文件不同步（重跑 render）'
        print('产物校验通过（占位符 0、seed 可解析、与 JSON 同步）')
    else:
        ok = False
        print('✗ 产物 html 不存在（先跑 render）')
    print('check ' + ('通过 ✓' if ok else '未通过 ✗'))
    return 0 if ok else 1


def iter_all_paths(doc):
    for _, feat in walk_features(doc):
        for f in feat.get('files', []):
            yield f['path']
        for t in feat.get('tests', []):
            yield t['path']


def load_doc(args):
    with open(args.json, encoding='utf-8') as f:
        return json.load(f)


def save_doc(args, doc):
    with open(args.json, 'w', encoding='utf-8') as f:
        json.dump(doc, f, ensure_ascii=False, indent=2)
        f.write('\n')


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--root', default='.', help='Godot 项目根（默认当前目录）')
    ap.add_argument('--json', default=None, help='feature_map.json 路径（默认 <root>/docs/feature_map.json）')
    ap.add_argument('--html', default=None, help='产物 html 路径（默认 <root>/docs/feature_map.html）')
    ap.add_argument('--template', default=None, help='模板路径（默认 skill 内 templates/feature_map.html）')
    ap.add_argument('--vendor', default=None, help='vendor 库路径（默认 skill 内 templates/vendor/vis-network.min.js）')
    ap.add_argument('cmd', choices=['scan', 'build', 'render', 'check', 'all'], help='子命令')
    args = ap.parse_args()
    if not args.json:
        args.json = os.path.join(args.root, 'docs', 'feature_map.json')
    if not args.html:
        args.html = os.path.join(args.root, 'docs', 'feature_map.html')
    steps = {'scan': [cmd_scan], 'build': [cmd_build], 'render': [cmd_render], 'check': [cmd_check],
             'all': [cmd_build, cmd_render, cmd_check]}[args.cmd]
    rc = 0
    for step in steps:
        rc = step(args) or rc
    sys.exit(rc)


if __name__ == '__main__':
    main()
