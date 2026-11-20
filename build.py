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
    "released": ("已发布", "Released"),
    "beta": ("测试版", "Beta"),
    "coming": ("即将上线", "Coming soon"),
}

ICON_GRADIENTS = [
    ("#7b8cff", "#4451c9"),
    ("#45d69b", "#128f63"),
    ("#f0b429", "#c07a12"),
    ("#ff7ea8", "#c4356b"),
    ("#7ad0ff", "#2f7fd6"),
    ("#c69bff", "#7b46d6"),
    ("#ff9d6b", "#c9552b"),
]


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
    seed = sum(ord(c) for c in (app.get("name") or "?"))
    c1, c2 = ICON_GRADIENTS[seed % len(ICON_GRADIENTS)]
    return '<div class="%s ph" style="background:linear-gradient(155deg,%s,%s)">%s</div>' % (
        cls.strip(),
        c1,
        c2,
        esc(letter),
    )


def pills_html(app, with_status=True, with_version=True):
    parts = []
    if with_status:
        st = app.get("status", "released")
        zh, en = STATUS_LABEL.get(st, (st, st))
        cls = "pill accent" if st == "released" else ("pill warn" if st == "beta" else "pill")
        parts.append(
            '<span class="%s" data-zh="%s" data-en="%s">%s</span>' % (cls, esc(zh), esc(en), esc(zh))
        )
    for p in app.get("platforms", []):
        parts.append('<span class="pill">%s</span>' % esc(p))
    ver = (app.get("version") or "").strip()
    if ver and with_version:
        parts.append('<span class="pill">v%s</span>' % esc(ver))
    return "".join(parts)


STORE_ICONS = {
    "apple": (
        '<svg width="22" height="22" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">'
        '<path d="M12.152 6.896c-.948 0-2.415-1.078-3.96-1.04-2.04.027-3.91 1.183-4.961 3.014'
        "-2.117 3.675-.546 9.103 1.519 12.09 1.013 1.454 2.208 3.09 3.792 3.039 1.52-.065 "
        "2.09-.987 3.935-.987 1.831 0 2.35.987 3.96.948 1.637-.026 2.676-1.48 3.676-2.948 "
        "1.156-1.688 1.636-3.325 1.662-3.415-.039-.013-3.182-1.221-3.22-4.857-.026-3.04 "
        "2.48-4.494 2.597-4.559-1.429-2.09-3.623-2.324-4.39-2.376-2-.156-3.675 1.09-4.61 "
        "1.09zM15.53 3.83c.843-1.012 1.4-2.427 1.245-3.83-1.207.052-2.662.805-3.532 1.818"
        "-.78.896-1.454 2.338-1.273 3.714 1.338.104 2.715-.688 3.559-1.701"
        '"/></svg>'
    ),
    "google": (
        '<svg width="21" height="21" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">'
        '<path d="M22.018 13.298l-3.919 2.218-3.515-3.493 3.543-3.521 3.891 2.202a1.49 1.49 '
        "0 0 1 0 2.594zM1.337.924a1.486 1.486 0 0 0-.112.568v21.017c0 .217.045.419.124.6"
        "l11.155-11.087L1.337.924zm12.207 10.065l3.258-3.238L3.45.195a1.466 1.466 0 0 0-.946"
        "-.179l11.04 10.973zm0 2.067l-11 10.933c.298.036.612-.016.906-.183l13.324-7.54-3.23"
        "-3.21z"
        '"/></svg>'
    ),
    "microsoft": (
        '<svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">'
        '<rect x="2" y="2" width="9.2" height="9.2"/><rect x="12.8" y="2" width="9.2" height="9.2"/>'
        '<rect x="2" y="12.8" width="9.2" height="9.2"/><rect x="12.8" y="12.8" width="9.2" height="9.2"/>'
        "</svg>"
    ),
    "generic": (
        '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
        'stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
        '<rect x="3" y="4" width="18" height="16" rx="3"/><path d="M3 9h18M8 4v5"/></svg>'
    ),
}

STORE_META = {
    "apple": ("Download on the", "App Store"),
    "google": ("GET IT ON", "Google Play"),
    "microsoft": ("Get it from", "Microsoft Store"),
    "generic": ("", "应用市场"),
}


def store_kind(name):
    n = (name or "").lower()
    if "app store" in n or "apple" in n or "ios" in n:
        return "apple"
    if "google" in n or "play" in n or "安卓" in n or "android" in n:
        return "google"
    if "microsoft" in n or "windows" in n or "微软" in n:
        return "microsoft"
    return "generic"


def store_btn(name, url):
    kind = store_kind(name)
    small, big = STORE_META[kind]
    label = name if kind == "generic" else big
    if kind == "generic":
        small = "前往"
    return (
        '<a class="btn-store" href="%s" target="_blank" rel="noopener">'
        '<span class="si">%s</span>'
        '<span class="txt"><span class="small">%s</span><span class="big">%s</span></span>'
        "</a>"
    ) % (esc(url), STORE_ICONS[kind], esc(small), esc(label))


def download_html(app):
    dl = app.get("download") or {}
    kind = (dl.get("type") or "none").lower()
    note = dl.get("note") or ""
    note_en = dl.get("noteEn") or note
    btns = []

    if kind == "github" and dl.get("url"):
        btns.append(
            '<a class="btn btn-primary" href="%s" target="_blank" rel="noopener">'
            "%s<span data-i18n=\"download\">下载</span></a>"
            % (esc(dl["url"]), DOWNLOAD_ICON)
        )
        if not note:
            note = "从 GitHub Releases 下载，免费使用。"
            note_en = "Download from GitHub Releases. Free to use."
    elif kind == "store":
        stores = dl.get("stores") or []
        for s in stores:
            btns.append(store_btn(s.get("name", ""), s.get("url", "#")))
        if not note:
            note = "在应用市场安装，更新由市场自动推送。"
            note_en = "Install from the store — updates are pushed automatically."
    elif kind == "direct" and dl.get("url"):
        btns.append(
            '<a class="btn btn-primary" href="{{ASSETS}}%s" download>'
            '%s<span data-i18n="download">下载</span></a>'
            % (esc(dl["url"]), DOWNLOAD_ICON)
        )
    else:
        btns.append(
            '<span class="btn btn-ghost" aria-disabled="true" data-i18n="notYet">暂未发布</span>'
        )
        if not note:
            note = "还在做，做好了会放在这里。"
            note_en = "Still in the works — it will show up here when it's ready."

    return (
        '<div class="dl-box">'
        '<h3 data-i18n="getApp">获取这个软件</h3>'
        '<p class="dl-note" data-zh="%s" data-en="%s">%s</p>'
        "%s"
        "</div>" % (esc(note), esc(note_en), esc(note), "".join(btns))
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
    rows.append((("平台", "Platform"), " / ".join(app.get("platforms", [])) or "—"))
    rows.append((("版本", "Version"), ("v" + app["version"]) if app.get("version") else "—"))
    rows.append((("体积", "Size"), app.get("size") or "—"))
    rows.append((("更新", "Updated"), app.get("updated") or "—"))
    return "".join(
        '<div class="spec"><dt data-zh="%s" data-en="%s">%s</dt><dd>%s</dd></div>'
        % (esc(k[0]), esc(k[1]), esc(k[0]), esc(v))
        for k, v in rows
    )


def features_html(app):
    feats = app.get("features") or []
    if not feats:
        return ""
    feats_en = app.get("featuresEn") or []
    items = []
    for i, f in enumerate(feats):
        en = feats_en[i] if i < len(feats_en) and feats_en[i] else f
        items.append('<li data-zh="%s" data-en="%s">%s</li>' % (esc(f), esc(en), esc(f)))
    return (
        '<section><h2 class="sec" data-i18n="features">功能</h2>'
        '<ul class="feature-list">%s</ul></section>' % "".join(items)
    )


def shots_html(app):
    shots = app.get("screenshots") or []
    if shots:
        inner = "".join(
            '<img src="{{ASSETS}}%s" alt="%s 截图" loading="lazy">' % (esc(s), esc(app.get("name", "")))
            for s in shots
        )
    else:
        inner = '<div class="shot-ph" data-zh="截图待补" data-en="Screenshots coming">截图待补</div>'
    return (
        '<section><h2 class="sec" data-i18n="shots">截图</h2><div class="shots">%s</div></section>'
        % inner
    )


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
        '<section><h2 class="sec" data-i18n="logs">更新记录</h2><div class="log">%s</div></section>'
        % "".join(items)
    )


def card_html(app, featured=False):
    slug = app["slug"]
    text = " ".join(
        [app.get("name", ""), app.get("tagline", "")] + list(app.get("platforms", []))
    )
    text_en = " ".join(
        [
            app.get("nameEn", "") or app.get("name", ""),
            app.get("taglineEn", "") or app.get("tagline", ""),
        ]
        + list(app.get("platforms", []))
    )
    badge = (
        '<span class="sample-badge" data-zh="示例" data-en="Sample">示例</span>'
        if app.get("sample")
        else ""
    )
    name = app.get("name", "")
    name_en = app.get("nameEn") or name
    tagline = app.get("tagline", "")
    tagline_en = app.get("taglineEn") or tagline
    return (
        '<a class="card%s" href="{{ASSETS}}apps/%s/index.html" '
        'data-platforms="%s" data-text="%s" data-text-en="%s">%s'
        '<div class="card-top">%s'
        '<div><h3 data-zh="%s" data-en="%s">%s</h3>'
        '<p class="tagline" data-zh="%s" data-en="%s">%s</p></div></div>'
        '<div class="card-bottom">%s<span class="card-arrow">%s</span></div></a>'
    ) % (
        " grand" if featured else "",
        esc(slug),
        esc(",".join(app.get("platforms", []))),
        esc(text),
        esc(text_en),
        badge,
        icon_html(app),
        esc(name),
        esc(name_en),
        esc(name),
        esc(tagline),
        esc(tagline_en),
        esc(tagline),
        pills_html(app, with_version=False),
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

    chips = ['<button class="chip" data-platform="all" aria-pressed="true" data-zh="全部" data-en="All">全部</button>']
    for p in platforms:
        chips.append(
            '<button class="chip" data-platform="%s" aria-pressed="false" data-zh="%s" data-en="%s">%s</button>'
            % (esc(p), esc(p), esc(p), esc(p))
        )

    # 数量能被 3 整除时不做主推大卡，让网格刚好排满，避免最后一行只剩一个
    featured_at = -1 if (len(apps) % 3 == 0 or len(apps) < 4) else 0
    cards = "".join(
        card_html(a, featured=(i == featured_at)) for i, a in enumerate(apps)
    ) or ('<div class="empty">还没有软件，去 data/apps.json 里加一个吧。</div>')

    github = (site.get("github") or "").strip()
    email = (site.get("email") or "").strip()

    nav_links = (
        '<a href="{{ASSETS}}potato/" data-zh="土豆清单" data-en="Potato List">土豆清单</a>'
        '<a href="{{ASSETS}}pricing.html" data-zh="定价" data-en="Pricing">定价</a>'
    )
    footer_links = (
        '<a href="{{ASSETS}}potato/" data-zh="土豆清单" data-en="Potato List">土豆清单</a>'
        '<a href="{{ASSETS}}pricing.html" data-zh="定价" data-en="Pricing">定价</a>'
        '<a href="{{ASSETS}}terms.html" data-zh="服务条款" data-en="Terms">服务条款</a>'
        '<a href="{{ASSETS}}privacy.html" data-zh="隐私政策" data-en="Privacy">隐私政策</a>'
    )
    if github:
        nav_links += '<a href="%s" target="_blank" rel="noopener">GitHub</a>' % esc(github)
        footer_links += '<a href="%s" target="_blank" rel="noopener">GitHub</a>' % esc(github)
    if email:
        nav_links += '<a href="mailto:%s" data-zh="联系" data-en="Contact">联系</a>' % esc(email)
        footer_links += '<a href="mailto:%s">%s</a>' % (esc(email), esc(email))

    common = {
        "SITE_NAME": esc(site.get("name", "我的软件")),
        "SITE_NAME_EN": esc(site.get("nameEn", "") or site.get("name", "我的软件")),
        "BRAND_LETTER": esc(site.get("brandLetter", "S")),
        "TAGLINE": esc(site.get("tagline", "")),
        "TAGLINE_EN": esc(site.get("taglineEn", "") or site.get("tagline", "")),
        "INTRO": esc(site.get("intro", "")),
        "INTRO_EN": esc(site.get("introEn", "") or site.get("intro", "")),
        "COPYRIGHT": esc(site.get("copyright", "")),
        "COPYRIGHT_EN": esc(site.get("copyrightEn", "") or site.get("copyright", "")),
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

    # 条款 / 隐私 / 定价（放在根目录，路径不带前缀）
    doc_pages = []
    for name in ("terms", "privacy", "pricing"):
        tpl_path = os.path.join(TPL, name + ".html")
        if not os.path.exists(tpl_path):
            continue
        doc = render(read(tpl_path), dict(common, ASSETS=""))
        write(os.path.join(BASE, name + ".html"), doc)
        doc_pages.append(name + ".html")

    for a in apps:
        body = render(
            app_tpl,
            dict(
                common,
                ASSETS="{{ASSETS}}",
                NAME=esc(a.get("name", "")),
                NAME_EN=esc(a.get("nameEn", "") or a.get("name", "")),
                APP_TAGLINE=esc(a.get("tagline", "")),
                APP_TAGLINE_EN=esc(a.get("taglineEn", "") or a.get("tagline", "")),
                ICON=icon_html(a),
                PILLS=pills_html(a),
                DESCRIPTION=esc(a.get("description", "")),
                DESCRIPTION_EN=esc(a.get("descriptionEn", "") or a.get("description", "")),
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
    if doc_pages:
        print("文档页：" + "、".join(doc_pages))
    print("首页：%s" % os.path.join(BASE, "index.html"))


if __name__ == "__main__":
    main()
