#!/usr/bin/env python3
"""Browser QA of the VozNativa Observatory (R18): a real browser opens ``docs/observatory/index.html`` and checks
behaviour and content, not only markup. Every check is a hard check: one failure makes the verdict FAIL.

The first version of this script passed a page whose criteria, documents, gaps, tracks and method sections were
empty (a script error stopped rendering halfway) because it only looked for the absence of console errors and at
two widgets. Now every section must hold the number of rows the data says it has.

Checks
* content: each section renders as many items as the payload holds (corpus squares, perturbation rows, 12 tasks,
  18 criteria, every gap, the four tracks, every document flow); the "in one minute" numbers equal the payload;
* interaction: gap state/severity chips and search change the visible rows and the counter; the live version
  switch changes the matrix; a click on a run opens it in the review desk and in the URL; split/inline, word/sentence,
  "only changes", j/k navigation, copy (toast), theme switch, the help dialog, the three exports (downloaded and
  parsed);
* states: a payload with no live runs, no judge, no documents and no texts renders without error and shows the
  missing states; hostile strings in the data never become markup;
* privacy: no local path, user name, temp directory or raw command in the page or in the exports;
* layout and access: no horizontal scroll at 320, 390 and 768 px; first Tab is the skip link; every button and
  form control has a name; reduced motion turns transitions off and shows all content; dark scheme changes the page.

Screenshots of the real page go to ``--shots``.

    python scripts/v0105_observatory_qa.py --shots <dir> --out qa.json
"""
from __future__ import annotations

import argparse
import json
import re
import tempfile
from pathlib import Path

PAGE = Path(__file__).resolve().parent.parent / "docs" / "observatory" / "index.html"
EDGE = Path(r"C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe")
FORBIDDEN = [r"[A-Za-z]:\\\\?Users", r"/Users/", r"AppData", r"vn-fire-", r"\brafael\b", r"\.voznativa/fire-trial/items",
             r"voznativa_cli\.py", r"--protect"]
HOSTILE = '<img src=x onerror="window.__xss=1">'


def payload_of(html: str) -> dict:
    m = re.search(r'<script type="application/json" id="payload">(.*?)</script>', html, re.S)
    return json.loads(m.group(1))


def with_payload(html: str, payload: dict) -> str:
    body = json.dumps(payload, ensure_ascii=False).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    return re.sub(r'(<script type="application/json" id="payload">)(.*?)(</script>)',
                  lambda m: m.group(1) + body + m.group(3), html, count=1, flags=re.S)


def main(argv=None) -> int:
    from playwright.sync_api import sync_playwright
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--shots", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--page", default=str(PAGE))
    args = ap.parse_args(argv)
    shots = Path(args.shots)
    shots.mkdir(parents=True, exist_ok=True)
    page_path = Path(args.page).resolve()
    html = page_path.read_text(encoding="utf-8")
    P = payload_of(html)
    D = P["data"]
    checks: dict[str, object] = {}
    problems: list[str] = []

    def expect(name, ok, detail=None):
        checks[name] = {"ok": bool(ok), **({"detail": detail} if detail is not None else {})}
        if not ok:
            problems.append(f"{name}: {detail}")

    # ---- privacy of the page source
    hits = sorted({pat for pat in FORBIDDEN if re.search(pat, html)})
    expect("privacy_page_source", not hits, hits)
    local_ids = {i["id"] for i in D["corpus"]["list"] if i["rights"] == "local_only"}
    pub_tasks = {t["task"] for t in D["live"]["tasks"] if t["publishable"]}
    expect("texts_only_publishable", set(D["texts"]) <= pub_tasks, sorted(set(D["texts"]) - pub_tasks))
    expect("no_local_only_text", not any(i in json.dumps(D["texts"]) for i in local_ids))
    pr = D.get("prospective") or {}
    pr_pub = {t["task"] for t in pr.get("tasks", []) if t["publishable"]}
    expect("prospective_texts_only_publishable", set(pr.get("texts", {})) <= pr_pub, sorted(set(pr.get("texts", {})) - pr_pub))

    with tempfile.TemporaryDirectory(prefix="obs-qa-") as tmp, sync_playwright() as p:
        kwargs = {"executable_path": str(EDGE)} if EDGE.exists() else {}
        browser = p.chromium.launch(**kwargs)
        checks["browser"] = ("msedge " if kwargs else "chromium ") + browser.version
        errors: list[str] = []

        def open_page(url, *, ready="html[data-ready]", **ctx):
            context = browser.new_context(accept_downloads=True, **ctx)
            context.grant_permissions(["clipboard-read", "clipboard-write"])
            page = context.new_page()
            page.on("console", lambda m: errors.append(f"console.{m.type}: {m.text}") if m.type == "error" else None)
            page.on("pageerror", lambda e: errors.append(f"pageerror: {e}"))
            page.goto(url)
            page.wait_for_selector(ready, timeout=10000)
            return context, page

        url = page_path.as_uri()
        ctx, page = open_page(url, viewport={"width": 1440, "height": 900}, color_scheme="light")
        count = lambda sel: page.locator(sel).count()
        # ---- content: every section holds what the data holds
        n_docs = len(D["documents"] or [])
        expect("minute_blocks", count("#minute .mi") == 4, count("#minute .mi"))
        expect("minute_corpus_number", page.locator("#minute .mi").first.locator(".big").inner_text().replace(".", "")
               == str(D["corpus"]["items"]))
        expect("corpus_squares", count("#units .u") == D["corpus"]["items"], count("#units .u"))
        expect("corpus_missing_rows", count("#units .fam.missing") == len(D["corpus"]["missing_families"]))
        n_kinds = len(D["offline"]["v0.10.5"]["kinds"]) if D["offline"] else 0
        expect("offline_rows", count("#db .trk") == n_kinds, count("#db .trk"))
        expect("offline_family_rows", count("#fam tbody tr") == len((D["offline"].get("v0.10.5") or {}).get("families", {})))
        expect("live_task_rows", count("#mx tbody tr") == len(D["live"]["tasks"]), count("#mx tbody tr"))
        expect("live_run_buttons", count("#mx button.pip") == len(D["live"]["runs"]), [count("#mx button.pip"), len(D["live"]["runs"])])
        if P.get("online"):
            expect("online_pilot_cases", count("#online-runs tbody tr") == len(P["online"]["cases"]))
            expect("online_pilot_source_links", count('#online-runs tbody a[href^="https://"]') == len(P["online"]["cases"]))
            expect("online_pilot_table_fits", page.locator("#online-runs").evaluate("(el) => el.scrollWidth <= el.parentElement.clientWidth"))
        expect("comparator_rows", count("#cmp tbody tr") == 8, count("#cmp tbody tr"))
        expect("judge_r6_rows", count("#r6 tbody tr") == (4 if D.get("judge") else 1), count("#r6 tbody tr"))
        n_hold = len({r["task"] for r in (D.get("holdout") or {}).get("runs", [])}) or 1
        expect("holdout_rows", count("#hold tbody tr") == n_hold, count("#hold tbody tr"))
        expect("desk_rows", count("#d-rows .p") >= 1, count("#d-rows .p"))
        expect("documents", count("#dossiers article") == max(n_docs, 1), count("#dossiers article"))
        expect("gaps", count("#gap-list > li") == len(P["gaps"]) and len(P["gaps"]) > 0, count("#gap-list > li"))
        expect("tracks", count("#tracks article") == 4, count("#tracks article"))
        expect("gates", count("#gates tbody tr") == 18, count("#gates tbody tr"))
        expect("method", count("#method li") == len(P["tracks"]["method"]))
        expect("toc", count("#toc a") == count("main section.s") == 11)
        has_pr = bool(D.get("prospective"))
        expect("prospective_rows", count("#pr-arms tbody tr") == (6 if has_pr else 1), count("#pr-arms tbody tr"))
        expect("ablation_rows", count("#pr-abl tbody tr") == (3 if has_pr and D["prospective"].get("ablation") else 1),
               count("#pr-abl tbody tr"))
        page.screenshot(path=str(shots / "desktop-light-top.png"))
        # section shots show every block: blocks below the fold of a section would still be waiting to reveal
        page.evaluate("document.querySelectorAll('.reveal').forEach(e => e.classList.add('in'))")
        for sec in ("minuto", "corpus", "offline", "live", "prospectivo", "docs", "gaps", "trilhas", "criterios", "metodo"):
            page.locator("#" + sec).scroll_into_view_if_needed()
            page.wait_for_timeout(900)
            page.locator("#" + sec).screenshot(path=str(shots / f"desktop-{sec}.png"))
        # ---- interaction: gaps
        visible = lambda: page.locator("#gap-list > li:not([hidden])").count()
        total = visible()
        chip = page.locator("#gap-filter button").first
        chip.click()
        expect("gap_chip_pressed", chip.get_attribute("aria-pressed") == "false", chip.get_attribute("aria-pressed"))
        expect("gap_chip_filters", visible() < total, [total, visible()])
        expect("gap_counter_follows", f"Mostrando {visible()} de {len(P['gaps'])}" in page.inner_text("#gap-count"))
        chip.click()
        page.fill("#gap-q", "negacao")
        expect("gap_search_accent_insensitive", 0 < visible() < total, visible())
        page.fill("#gap-q", "zzzz-nada")
        expect("gap_search_empty_state", visible() == 0 and "Nenhum gap" in page.inner_text("#gap-count"))
        page.fill("#gap-q", "")
        page.locator("#gap-sev button").first.click()
        expect("gap_severity_filters", visible() < total)
        page.locator("#gap-sev button").first.click()
        page.locator("#gap-list summary").first.click()
        expect("gap_expands", page.locator("#gap-list details").first.get_attribute("open") is not None)
        # ---- live matrix and desk
        both = count("#mx button.pip")
        page.click('#live-ver button[data-v="v0100"]')
        only = count("#mx button.pip")
        expect("live_version_switch", only == len([r for r in D["live"]["runs"] if r["label"] == "v0100"]) and only <= both,
               [both, only])
        page.click('#live-ver button[data-v="both"]')
        target = next((r for r in D["live"]["runs"] if r["task"] in D["texts"] and r["changed"]), None)
        if target:
            key = f'{target["label"]}|{target["task"]}|{target["rep"]}|{target["arm"]}'
            page.click(f'#mx button.pip[data-run="{key}"]')
            page.wait_for_timeout(400)
            expect("pip_opens_desk", page.input_value("#d-right") == f'{target["label"]}|{target["arm"]}'
                   and page.input_value("#d-task") == target["task"], [page.input_value("#d-task"), page.input_value("#d-right")])
            expect("pip_in_url", f'caso={target["task"]}' in page.evaluate("location.hash"))
            expect("pip_marked", count("#mx .pip.sel") == 1)
            expect("diff_marks", count("#d-rows ins.i, #d-rows del.d") > 0, count("#d-rows ins.i, #d-rows del.d"))
            expect("diff_symbols_not_only_color", count("#d-rows .mk") > 0)
            page.locator("body").click(position={"x": 5, "y": 5})
            page.keyboard.press("j")
            pos = page.inner_text("#d-pos")
            expect("diff_next_change", pos.startswith("1 /"), pos)
            expect("diff_evidence_panel", "trecho 1" in page.inner_text("#d-evid").lower(), page.inner_text("#d-evid")[:80])
            page.locator("#mesa").screenshot(path=str(shots / "desktop-mesa-split.png"))
            page.click('#d-mode button[data-m="inline"]')
            expect("diff_inline", "inline" in page.get_attribute("#d-rows", "class"))
            page.locator("#mesa").screenshot(path=str(shots / "desktop-mesa-inline.png"))
            page.click('#d-mode button[data-m="split"]')
            words = count("#d-rows ins.i, #d-rows del.d")
            page.click('#d-unit button[data-u="sentence"]')
            expect("diff_sentence_unit", "frase" in page.inner_text("#d-stats") or "idênticos" in page.inner_text("#d-stats"))
            page.click('#d-unit button[data-u="word"]')
            expect("diff_word_unit_back", count("#d-rows ins.i, #d-rows del.d") == words)
            rows_all = page.locator("#d-rows .p:not([hidden])").count()
            page.click("#d-fold")
            expect("diff_fold", page.locator("#d-rows .p:not([hidden])").count() <= rows_all)
            folded_url = page.url
            page.reload()
            page.wait_for_selector("html[data-ready]")
            expect("deep_link_restores_fold", page.get_attribute("#d-fold", "aria-pressed") == "true"
                   and f'caso={target["task"]}' in folded_url)
            page.click("#d-fold")
            page.click("#d-copy")
            page.wait_for_timeout(200)
            expect("copy_toast", "copiada" in page.inner_text("#toast").lower(), page.inner_text("#toast"))
        else:
            expect("desk_has_changed_publishable_run", False, "no publishable run changed the text")
        # ---- exports
        for kind, name in (("json", ".json"), ("runs", ".csv"), ("gaps", ".csv")):
            with page.expect_download() as dl:
                page.click(f'[data-export="{kind}"]')
            path = Path(tmp) / (kind + name)
            dl.value.save_as(str(path))
            text = path.read_text(encoding="utf-8")
            leak = sorted({pat for pat in FORBIDDEN if re.search(pat, text)})
            ok = bool(text.strip()) and not leak
            if kind == "json":
                ok = ok and json.loads(text)["provenance"]["data_sha256"] == P["provenance"]["data_sha256"]
            if kind == "runs":
                ok = ok and len(text.strip().splitlines()) == len(D["live"]["runs"]) + 1
            expect(f"export_{kind}", ok, leak)
        # ---- help, theme, a11y
        page.keyboard.press("?")
        expect("help_dialog", page.evaluate("document.getElementById('help').open"))
        page.keyboard.press("Escape")
        light_bg = page.evaluate("getComputedStyle(document.body).backgroundColor")
        page.click('[data-theme-set="dark"]')
        page.wait_for_timeout(500)
        dark_bg = page.evaluate("getComputedStyle(document.body).backgroundColor")
        expect("theme_switch", light_bg != dark_bg, [light_bg, dark_bg])
        page.screenshot(path=str(shots / "desktop-dark-top.png"))
        page.click('[data-theme-set="auto"]')
        unnamed = page.evaluate("""() => [...document.querySelectorAll('button,select,input,a[href]')]
            .filter(e => e.offsetParent !== null && !(e.getAttribute('aria-label') || e.textContent.trim() || (e.labels && e.labels.length)))
            .map(e => e.outerHTML.slice(0, 80))""")
        expect("controls_named", not unnamed, unnamed[:5])
        ctx.close()

        ctx, page = open_page(url, viewport={"width": 1280, "height": 800})
        page.keyboard.press("Tab")
        expect("first_tab_skip_link", page.evaluate("document.activeElement.className") == "skip")
        ctx.close()

        # ---- reduced motion
        ctx, page = open_page(url, viewport={"width": 1280, "height": 800}, reduced_motion="reduce")
        rm = page.evaluate("""() => { const r = document.querySelector('.reveal'); const s = getComputedStyle(r);
            return [s.transitionDuration, s.opacity, getComputedStyle(document.documentElement).scrollBehavior]; }""")
        expect("reduced_motion", rm[0] in ("0s", "0s, 0s") and rm[1] == "1" and rm[2] == "auto", rm)
        ctx.close()

        # ---- widths
        for w in (320, 390, 768):
            ctx, page = open_page(url, viewport={"width": w, "height": 860}, is_mobile=w < 700, has_touch=w < 700)
            over = page.evaluate("document.scrollingElement.scrollWidth - window.innerWidth")
            expect(f"no_horizontal_scroll_{w}", over <= 0, over)
            if w == 390 and P.get("online"):
                expect("online_pilot_mobile_cards", page.locator("#online-runs tbody tr").first.evaluate(
                    "(el) => getComputedStyle(el).display === 'grid' && el.scrollWidth <= el.clientWidth"))
            if w == 390:
                page.screenshot(path=str(shots / "mobile-top.png"))
                for sec in ("minuto", "live", "mesa", "gaps"):
                    page.locator("#" + sec).scroll_into_view_if_needed()
                    page.wait_for_timeout(900)
                    page.locator("#" + sec).screenshot(path=str(shots / f"mobile-{sec}.png"))
            ctx.close()

        sample = page_path.with_name("relatorio-exemplo.html")
        if sample.exists():
            url_report = sample.as_uri()
            ctx, report = open_page(url_report, ready="#theme", viewport={"width": 1440, "height": 980},
                                    color_scheme="light")
            expect("report_diff_and_rationales", report.locator(".pair.change").count() == 2 and
                   report.locator(".reasons li").count() == 4 and report.locator(".reasons .jump").count() == 4)
            expect("report_diff_marks", report.locator(".pair del").count() > 0
                   and report.locator(".pair ins").count() > 0 and "Equivalência a verificar" in report.inner_text(".badge"))
            report.screenshot(path=str(shots / "relatorio-desktop.png"), full_page=True, animations="disabled")
            report.click("#next")
            expect("report_change_keyboard_focus", report.evaluate("document.activeElement.id") == "mudanca-1")
            report.keyboard.press("ArrowRight")
            expect("report_change_keyboard_navigation", report.inner_text("#progress") == "2/2")
            report.click("#changes")
            expect("report_focus_changes", report.locator(".pair.same:visible").count() == 0)
            report.click("#reading")
            expect("report_reading_all_text", report.locator(".pair.same:visible").count() > 0
                   and report.locator(".pair .before:visible").count() == 0)
            report.click("#copy")
            copied = report.evaluate("navigator.clipboard.readText()")
            expect("report_copies_full_candidate", "A confirmação chega por e-mail." in copied
                   and "Você deve enviar" in copied and "Vale ressaltar" not in copied)
            report.click("#theme")
            expect("report_theme", report.get_attribute("html", "data-theme") == "dark")
            ctx.close()
            ctx, report = open_page(url_report, ready="#theme", viewport={"width": 390, "height": 844},
                                    is_mobile=True, has_touch=True, color_scheme="dark", reduced_motion="reduce")
            expect("report_mobile_width", report.evaluate("document.scrollingElement.scrollWidth <= innerWidth"))
            expect("report_reduced_motion", report.evaluate("getComputedStyle(document.querySelector('.desk')).animationName") == "none")
            report.screenshot(path=str(shots / "relatorio-mobile.png"), full_page=True)
            ctx.close()
            ctx, report = open_page(url_report, ready="#why", java_script_enabled=False)
            expect("report_without_script", report.locator(".pair.change:visible").count() == 2 and
                   report.locator(".reasons li:visible").count() == 4)
            ctx.close()

        # ---- missing data and hostile data
        empty = json.loads(json.dumps(P))
        empty["data"]["live"]["runs"] = []
        empty["data"]["live"]["arms"] = {}
        empty["data"]["texts"] = {}
        empty["data"]["judge"] = None
        empty["data"]["documents"] = None
        empty["data"]["perf_17600_cpu_min_s"] = None
        empty["data"]["prospective"] = None
        empty["data"]["headline"].pop("prospective", None)
        f = Path(tmp) / "empty.html"
        f.write_text(with_payload(html, empty), encoding="utf-8")
        ctx, page = open_page(f.as_uri(), viewport={"width": 1280, "height": 800})
        parts = {"gates": page.locator("#gates tbody tr").count() == 18,
                 "desk": "nenhum texto publicável" in page.inner_text("#d-rows").lower(),
                 "comparator": "not run" in page.inner_text("#cmp").lower(),
                 "documents": "not run" in page.inner_text("#dossiers").lower(),
                 "judge": "not run" in page.inner_text("#ficha").lower()}
        expect("empty_data_renders", all(parts.values()), parts)
        ctx.close()
        hostile = json.loads(json.dumps(P))
        hostile["data"]["corpus"]["list"][0]["genre"] = HOSTILE
        hostile["data"]["live"]["tasks"][0]["request"] = HOSTILE
        hostile["data"]["live"]["tasks"][0]["genre"] = HOSTILE
        for t in hostile["data"]["texts"].values():
            t["original"] = HOSTILE + t["original"]
        hostile["tracks"]["tracks"][0]["findings"].append(HOSTILE)
        f = Path(tmp) / "hostile.html"
        f.write_text(with_payload(html, hostile), encoding="utf-8")
        ctx, page = open_page(f.as_uri() + "#mesa?caso=%E0%A4%A&dir=%22%3E%3Cimg", viewport={"width": 1280, "height": 800})
        page.locator("#units .u").first.hover()
        page.wait_for_timeout(300)
        expect("hostile_strings_inert", page.evaluate("window.__xss === undefined") and
               page.locator('img[src="x"]').count() == 0, page.locator('img[src="x"]').count())
        ctx.close()
        browser.close()
        expect("no_console_or_page_errors", not errors, errors[:5])

    report = {"kind": "voznativa.observatory_qa", "page": "docs/observatory/index.html",
              "data_sha256": P["provenance"]["data_sha256"], "checks": checks, "problems": problems,
              "verdict": "PASS" if not problems else "FAIL"}
    Path(args.out).write_text(json.dumps(report, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(report["verdict"], f"{sum(1 for c in checks.values() if isinstance(c, dict) and c['ok'])}/"
          f"{sum(1 for c in checks.values() if isinstance(c, dict))} checks", *problems, sep="\n")
    return 0 if not problems else 1


if __name__ == "__main__":
    raise SystemExit(main())
