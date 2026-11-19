# -*- coding: utf-8 -*-
"""
软件站生成器 —— 读取 data/apps.json，生成整站静态页面。

用法：双击「更新网站.bat」，或者命令行 python build.py
每次改了 apps.json 之后都要重新跑一次，改动才会出现在网页上。
"""

import json
import os
import shutil
import sys
from datetime import datetime

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "data", "apps.json")
TPL = os.path.join(BASE, "templates")

STATUS_LABEL = {
    "released": "已发布",
    "beta": "测试版",
    "coming": "即将上线",
}


def esc(text):
    if text is None:
        return ""
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def render(tpl, mapping):
    out = tpl
    for key, val in mapping.items():
        out = out.replace("{{" + key + "}}", str(val))
    return out


def icon_html(app, size_class=""):
    icon = (app.get("icon") or "").strip()
    cls = "app-icon " + size_class
    if icon:
        name = app.get("name", "?")
        return '<img class="%s" src="{{ASSETS}}%s" alt="%s">' % (
            cls.strip(),
            esc(icon),
            esc(name),
        )
    letter = (app.get("name") or "?")[:1].upper()
    return '<div class="%s ph">%s</div>' % (cls.strip(), esc(letter))


def pills_html(app, with_status=True):
    parts = []
    if with_status:
        st = app.get("status", "released")
        label = STATUS_LABEL.get(st, st)
        cls = "pill accent" if st == "released" else ("pill warn" if st == "beta" else "pill")
        parts.append('<span class="%s">%s</span>' % (cls, esc(label)))
    for p in app.get("platforms", []):
        parts.append('<span class="pill">%s</span>' % esc(p))
    ver = (app.get("version") or "").strip()
    if ver:
        parts.append('<span class="pill">v%s</span>' % esc(ver))
    return "".join(parts)


def download_html(app):
    dl = app.get("download") or {}
    kind = (dl.get("type") or "none").lower()
    note = dl.get("note") or ""
    btns = []

    if kind == "github" and dl.get("url"):
        btns.append(
            '<a class="btn btn-primary" href="%s" target="_blank" rel="noopener">'
            "%s</a>"
            % (esc(dl["url"]), DOWNLOAD_ICON + "下载")
        )
        if not note:
            note = "从 GitHub Releases 下载，免费使用。"
    elif kind == "store":
        stores = dl.get("stores") or []
        for i, s in enumerate(stores):
            cls = "btn btn-primary" if i == 0 else "btn btn-ghost"
            btns.append(
                '<a class="%s" href="%s" target="_blank" rel="noopener">%s</a>'
                % (cls, esc(s.get("url", "#")), esc(s.get("name", "应用市场")))
            )
        if not note:
            note = "在应用市场安装，更新由市场自动推送。"
    elif kind == "direct" and dl.get("url"):
        btns.append(
            '<a class="btn btn-primary" href="{{ASSETS}}%s" download>%s</a>'
            % (esc(dl["url"]), DOWNLOAD_ICON + "下载")
        )
    else:
        btns.append('<span class="btn btn-ghost" aria-disabled="true">暂未发布</span>')
        if not note:
            note = "还在做，做好了会放在这里。"

    return (
        '<div class="dl-box">'
        "<h3>获取这个软件</h3>"
        '<p class="dl-note">%s</p>'
        "%s"
        "</div>" % (esc(note), "".join(btns))
    )


DOWNLOAD_ICON = (
    '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
    'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
    '<path d="M12 3v12M7 11l5 5 5-5M5 21h14"/></svg>'
)

ARROW_ICON = (
    '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
    'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
    '<path d="M5 12h14M13 6l6 6-6 6"/></svg>'
)


def spec_rows(app):
    rows = []
    rows.append(("平台", " / ".join(app.get("platforms", [])) or "—"))
    rows.append(("版本", ("v" + app["version"]) if app.get("version") else "—"))
    rows.append(("体积", app.get("size") or "—"))
    rows.append(("更新", app.get("updated") or "—"))
    return "".join(
        '<div class="spec"><dt>%s</dt><dd>%s</dd></div>' % (esc(k), esc(v)) for k, v in rows
    )


def features_html(app):
    feats = app.get("features") or []
    if not feats:
        return ""
    items = "".join("<li>%s</li>" % esc(f) for f in feats)
    return (
        "<section><h2 class=\"sec\">功能</h2>"
        '<ul class="feature-list">%s</ul></section>' % items
    )


def shots_html(app):
    shots = app.get("screenshots") or []
    if shots:
        inner = "".join(
            '<img src="{{ASSETS}}%s" alt="%s 截图">' % (esc(s), esc(app.get("name", "")))
            for s in shots
        )
    else:
        inner = '<div class="shot-ph">截图待补</div>'
    return '<section><h2 class="sec">截图</h2><div class="shots">%s</div></section>' % inner


def changelog_html(app):
    logs = app.get("changelog") or []
    if not logs:
        return ""
    items = []
    for log in logs:
        notes = "".join("<li>%s</li>" % esc(n) for n in (log.get("notes") or []))
        items.append(
            '<div class="log-item">'
            '<div class="log-head"><span class="log-ver">v%s</span>'
            '<span class="log-date">%s</span></div>'
            "<ul>%s</ul></div>"
            % (esc(log.get("version", "")), esc(log.get("date", "")), notes)
        )
    return (
        '<section><h2 class="sec">更新记录</h2><div class="log">%s</div></section>'
        % "".join(items)
    )


def card_html(app):
    slug = app["slug"]
    text = " ".join(
        [app.get("name", ""), app.get("tagline", "")] + list(app.get("platforms", []))
    )
    badge = '<span class="sample-badge">示例</span>' if app.get("sample") else ""
    return (
        '<a class="card" href="{{ASSETS}}apps/%s/index.html" '
        'data-platforms="%s" data-text="%s">%s'
        '<div class="card-top">%s'
        '<div><h3>%s</h3><p class="tagline">%s</p></div></div>'
        '<div class="card-bottom">%s<span class="card-arrow">%s</span></div></a>'
    ) % (
        esc(slug),
        esc(",".join(app.get("platforms", []))),
        esc(text),
        badge,
        icon_html(app),
        esc(app.get("name", "")),
        esc(app.get("tagline", "")),
        pills_html(app),
        ARROW_ICON,
    )


def read(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def write(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def main():
    if not os.path.exists(DATA):
        print("[错误] 找不到 data/apps.json")
        sys.exit(1)

    with open(DATA, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as e:
            print("[错误] apps.json 格式有问题，第 %d 行第 %d 列：%s" % (e.lineno, e.colno, e.msg))
            print("       常见原因：少了逗号、多了一个逗号、引号用了中文引号。")
            sys.exit(1)

    site = data.get("site", {})
    apps = [a for a in data.get("apps", []) if a.get("slug")]
    year = datetime.now().year

    index_tpl = read(os.path.join(TPL, "index.html"))
    app_tpl = read(os.path.join(TPL, "app.html"))

    platforms = []
    for a in apps:
        for p in a.get("platforms", []):
            if p not in platforms:
                platforms.append(p)
    platforms.sort()

    chips = ['<button class="chip" data-platform="all" aria-pressed="true">全部</button>']
    for p in platforms:
        chips.append('<button class="chip" data-platform="%s" aria-pressed="false">%s</button>' % (esc(p), esc(p)))

    cards = "".join(card_html(a) for a in apps) or (
        '<div class="empty">还没有软件，去 data/apps.json 里加一个吧。</div>'
    )

    github = (site.get("github") or "").strip()
    email = (site.get("email") or "").strip()

    nav_links = ""
    footer_links = ""
    if github:
        nav_links += '<a href="%s" target="_blank" rel="noopener">GitHub</a>' % esc(github)
        footer_links += '<a href="%s" target="_blank" rel="noopener">GitHub</a>' % esc(github)
    if email:
        nav_links += '<a href="mailto:%s">联系</a>' % esc(email)
        footer_links += '<a href="mailto:%s">%s</a>' % (esc(email), esc(email))

    common = {
        "SITE_NAME": esc(site.get("name", "我的软件")),
        "BRAND_LETTER": esc(site.get("brandLetter", "S")),
        "TAGLINE": esc(site.get("tagline", "")),
        "INTRO": esc(site.get("intro", "")),
        "COPYRIGHT": esc(site.get("copyright", "")),
        "EMAIL": esc(email),
        "GITHUB": esc(github),
        "YEAR": year,
        "APP_COUNT": len(apps),
        "PLATFORM_COUNT": len(platforms),
        "NAV_LINKS": nav_links,
        "FOOTER_LINKS": footer_links,
    }

    index_html = render(
        index_tpl,
        dict(
            common,
            CHIPS="".join(chips),
            CARDS=cards.replace("{{ASSETS}}", ""),
            ASSETS="",
        ),
    )
    write(os.path.join(BASE, "index.html"), index_html)

    for a in apps:
        body = render(
            app_tpl,
            dict(
                common,
                ASSETS="{{ASSETS}}",
                NAME=esc(a.get("name", "")),
                APP_TAGLINE=esc(a.get("tagline", "")),
                ICON=icon_html(a),
                PILLS=pills_html(a),
                DESCRIPTION=esc(a.get("description", "")),
                FEATURES=features_html(a),
                SHOTS=shots_html(a),
                SPEC=spec_rows(a),
                DL=download_html(a),
                CHANGELOG=changelog_html(a),
            ),
        )
        body = body.replace("{{ASSETS}}", "../../")
        body = body.replace("{{NAME}}", esc(a.get("name", "")))
        write(os.path.join(BASE, "apps", a["slug"], "index.html"), body)

    # 清掉已经不存在的软件目录
    apps_dir = os.path.join(BASE, "apps")
    if os.path.isdir(apps_dir):
        keep = set(a["slug"] for a in apps)
        for d in os.listdir(apps_dir):
            full = os.path.join(apps_dir, d)
            if os.path.isdir(full) and d not in keep:
                shutil.rmtree(full, ignore_errors=True)

    print("生成完成：%d 个软件页面 + 1 个首页" % len(apps))
    print("首页：%s" % os.path.join(BASE, "index.html"))


if __name__ == "__main__":
    main()
