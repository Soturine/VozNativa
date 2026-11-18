#!/usr/bin/env python3
"""Fire-trial corpus of v0.10.5: real PT-BR texts, rights per operation, text kept outside the repository.

Reads sources already obtained under their own terms and writes:

* ``<out>/items.jsonl`` — the texts (outside the repository; never committed);
* ``evals/v0105/MANIFEST.json`` — ids, source, genre, length band, word count, sha256 and the rights of each
  operation (local analysis, model API processing, publication of excerpts), no text.

Sources (see ``docs/releases/v0.10.5/CORPUS_AND_LICENSES.md``):

* Machado de Assis corpus (Project Gutenberg / Wikisource, public domain; registry entry CC0-1.0);
* federal laws from planalto.gov.br (official acts: not protected, Lei 9.610/1998, art. 8, IV);
* abstracts listed by Crossref with a CC BY 4.0 licence URL (attribution kept: DOI);
* UD Portuguese-GSD, -Bosque (CETENFolha part), -PetroGold, -DANTEStocks and B2W-Reviews01: underlying text
  without a clear licence, or non-commercial: **local analysis only** (no model API, no publication).

Selection is deterministic (sorted ids, fixed strides), so the same inputs give the same corpus.

    python scripts/v0105_build_corpus.py --raw ~/.voznativa/fire-trial/raw --corpora ~/.voznativa/corpora \
        --out ~/.voznativa/fire-trial
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from voznativa.ptbr import language_of  # noqa: E402

BANDS = ((20, "micro"), (150, "curto"), (800, "medio"), (4000, "longo"), (10 ** 9, "documento"))
RIGHTS = {
    "public_domain": {"local_analysis": True, "model_api": True, "publish_excerpts": True},
    "cc_by": {"local_analysis": True, "model_api": True, "publish_excerpts": True},
    "local_only": {"local_analysis": True, "model_api": False, "publish_excerpts": False},
}


def band(words: int) -> str:
    return next(name for limit, name in BANDS if words <= limit)


def item(source, family, genre, text, rights, ref, work):
    text = text.strip()
    words = len(text.split())
    return {"id": None, "source": source, "family": family, "genre": genre, "work": work, "ref": ref,
            "rights": rights, "words": words, "band": band(words), "text": text,
            "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest()}


# --- Machado de Assis ------------------------------------------------------------------------------------

def _clean_gutenberg(text: str) -> str:
    start = re.search(r"\n\s*I\s*\n", text)
    return text[start.start():] if start else text


def _paragraphs(text: str) -> list[str]:
    return [p.strip() for p in re.split(r"\n\s*\n", text) if len(p.split()) >= 3]


def _is_verse(text: str) -> bool:
    """Verse: almost every non-empty line short and no prose-length line (dialogue in prose has short lines
    too, but also long ones)."""
    lines = [x for x in text.splitlines() if x.strip()]
    if len(lines) < 6 or len(text) > 6000:
        return False
    short = sum(len(x) <= 55 for x in lines) / len(lines)
    return short >= 0.85 and max(len(x) for x in lines) <= 90


def machado(path: Path) -> list[dict]:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            rows.append(json.loads(line))
        except ValueError:
            continue
    out = []
    pd = "public_domain"
    for r in rows:
        title, text = r["titulo"], r["texto"].replace("\r", "")
        t = title.lower()
        if "gutenberg" in r.get("fonte", "").lower():
            body = _clean_gutenberg(text)
            paras = _paragraphs(body)
            if title == "Poesias Completas":
                stanzas = [p for p in paras if p.count("\n") >= 3][20:220:25]
                out += [item("machado", "literario", "poema (estrofe)", s, pd, f"{title} #{k}", title)
                        for k, s in enumerate(stanzas)]
                continue
            genre = "conto (coletânea)" if title in ("Papéis Avulsos", "Histórias sem Data", "Relíquias de Casa Velha") \
                else "romance"
            # one passage of each band per work: paragraphs joined up to a word target
            for target, label in ((12, "micro"), (90, "curto"), (450, "medio"), (2200, "longo")):
                start = (len(paras) // 3) + target % 7
                chunk, words = [], 0
                for p in paras[start:]:
                    chunk.append(p)
                    words += len(p.split())
                    if words >= target:
                        break
                if label == "micro":
                    sentence = re.split(r"(?<=[.!?])\s+", chunk[0])[0]
                    chunk = [sentence] if 3 <= len(sentence.split()) <= 20 else []
                if chunk:
                    out.append(item("machado", "literario", f"{genre} (trecho)", "\n\n".join(chunk), pd,
                                    f"{title} @{start}:{label}", title))
            if title in ("Dom Casmurro", "Memorial de Aires"):
                out.append(item("machado", "literario", f"{genre} (capítulos)", "\n\n".join(paras[:60]), pd,
                                f"{title} @0:documento", title))
            continue
        if t.startswith("crônica") or "crônica" in t:
            genre = "crônica"
        elif t.startswith("discursos na academia"):
            genre = "discurso"
        elif "crítica" in t or ":" in title:
            genre = "crítica literária ou teatral"
        elif "advertência" in t:
            genre = "advertência/prefácio"
        elif t.startswith("dom casmurro/"):
            genre = "romance (capítulo)"
        elif _is_verse(text):
            genre = "poema"
        else:
            genre = "conto"
        out.append(item("machado", "literario", genre, text, pd, title, title.split("/")[0]))
    return out


# --- federal laws ----------------------------------------------------------------------------------------

LAW_TITLES = {"lei8078": "Código de Defesa do Consumidor (Lei 8.078/1990)", "lei13709": "LGPD (Lei 13.709/2018)",
              "lei9394": "LDB (Lei 9.394/1996)", "lei13146": "Estatuto da Pessoa com Deficiência (Lei 13.146/2015)",
              "lei8069": "ECA (Lei 8.069/1990)"}


def _law_text(raw: bytes) -> str:
    s = raw.decode("cp1252", "replace")
    s = re.sub(r"(?is)<(strike|del|s)\b.*?</\1>", " ", s)          # revoked wording in compiled laws
    s = re.sub(r"(?is)<(script|style)\b.*?</\1>", " ", s)
    s = re.sub(r"(?i)<br\s*/?>|</p>", "\n", s)
    s = html.unescape(re.sub(r"<[^>]+>", " ", s))
    lines = [" ".join(line.split()) for line in s.splitlines()]
    lines = [x for x in lines if x and not re.search(r"\((?:Reda[çc][ãa]o dada|Inclu[íi]d[oa]|Vide|Vig[êe]ncia|Revogad)",
                                                         x)]
    return "\n".join(lines)


def laws(raw_dir: Path) -> list[dict]:
    out = []
    for key, title in LAW_TITLES.items():
        path = raw_dir / f"{key}.htm"
        if not path.exists():
            continue
        text = _law_text(path.read_bytes())
        arts = re.split(r"\n(?=Art\. ?\d+)", text)
        arts = [a for a in arts if a.startswith("Art") and 8 <= len(a.split()) <= 700]
        for a in arts[3::max(1, len(arts) // 6)][:6]:
            num = re.match(r"Art\. ?([\dº°]+)", a).group(1)
            out.append(item("planalto", "institucional_juridico", "lei (artigo)", a, "public_domain",
                            f"{title}, art. {num}", title))
        caps = [c for c in re.split(r"\n(?=CAP[ÍI]TULO )", text) if c.startswith("CAP")]
        if caps:
            cap = sorted(caps, key=len)[len(caps) // 2]
            out.append(item("planalto", "institucional_juridico", "lei (capítulo)", cap, "public_domain",
                            f"{title}, {cap.splitlines()[0][:40]}", title))
        if key == "lei13709":
            body = text[text.find("Art. 1"):]
            out.append(item("planalto", "institucional_juridico", "lei (íntegra)", body, "public_domain",
                            f"{title}, íntegra", title))
    return out


# --- Crossref CC BY abstracts ----------------------------------------------------------------------------

AREAS = {"agricultura_": "agricultura", "direito_cons": "direito", "economia_ren": "economia",
         "educa_C3_A7_": "educação", "engenharia_m": "engenharia", "hist_C3_B3ri": "história",
         "lingu_C3_ADs": "linguística", "sa_C3_BAde_p": "saúde"}


def abstracts(raw_dir: Path) -> list[dict]:
    out, seen = [], set()
    for path in sorted(raw_dir.glob("cr_*.json")):
        area = AREAS.get(path.stem[3:], path.stem[3:])
        data = json.loads(path.read_text(encoding="utf-8"))
        for w in data["message"]["items"]:
            text = html.unescape(re.sub(r"<[^>]+>", " ", w.get("abstract", "")))
            text = re.sub(r"^\s*(?:Resumo|RESUMO|Abstract)\s*[:.]?\s*", "", " ".join(text.split()))
            if w["DOI"] in seen or language_of(text)["value"] != "pt" or len(text.split()) < 40:
                continue
            seen.add(w["DOI"])
            lic = [x.get("URL", "") for x in w.get("license", [])]
            if not any("creativecommons.org/licenses/by/4.0" in u for u in lic):
                continue
            out.append(item("crossref", "academico", f"resumo acadêmico ({area})", text, "cc_by",
                            f"doi:{w['DOI']}", (w.get("container-title") or ["?"])[0]))
    return out


# --- local-only corpora ----------------------------------------------------------------------------------

def _conllu_docs(path: Path, keep=lambda d: True):
    docs, current, doc = {}, None, None
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("# newdoc"):
            doc = line.split("=", 1)[1].strip()
        elif line.startswith("# sent_id"):
            current = line.split("=", 1)[1].strip()
            if doc is None:
                doc = current
        elif line.startswith("# text = ") and keep(doc or current):
            docs.setdefault(str(doc or current or f"anon-{len(docs)}"), []).append(line[9:].strip())
    return docs


def local_only(corpora: Path) -> list[dict]:
    out, lo = [], "local_only"
    gsd = corpora / "ud-portuguese-gsd" / "pt_gsd-ud-train.conllu"
    if gsd.exists():
        sents = [t for v in _conllu_docs(gsd).values() for t in v]
        for k, s in enumerate(sents[::420][:20]):
            out.append(item("ud-gsd", "jornalistico_blog", "notícia/blog (frase)", s, lo, f"gsd-train #{k * 420}",
                            "UD-GSD"))
    bosque = corpora / "ud-portuguese-bosque" / "pt_bosque-ud-train.conllu"
    if bosque.exists():
        docs = _conllu_docs(bosque, keep=lambda d: str(d).startswith("CF"))
        for doc in sorted(docs)[::40][:20]:
            out.append(item("ud-bosque", "jornalistico", "notícia (Folha, CETENFolha)", " ".join(docs[doc]), lo, doc,
                            "UD-Bosque CF"))
    petro = corpora / "ud-portuguese-petrogold" / "pt_petrogold-ud-train.conllu"
    if petro.exists():
        docs = _conllu_docs(petro)
        for doc in sorted(docs)[::3][:15]:
            sents = docs[doc][:12]
            out.append(item("ud-petrogold", "academico", "tese/dissertação técnica (trecho)", " ".join(sents), lo, doc,
                            "UD-PetroGold"))
    dante = corpora / "ud-portuguese-dantestocks" / "pt_dantestocks-ud-train.conllu"
    if dante.exists():
        sents = [t for v in _conllu_docs(dante).values() for t in v]
        for k, s in enumerate(sents[::150][:20]):
            out.append(item("ud-dantestocks", "redes_sociais", "tweet sobre mercado", s, lo, f"dante-train #{k * 150}",
                            "UD-DANTEStocks"))
    b2w = corpora / "b2w-reviews01" / "B2W-Reviews01.prefix.csv"
    if b2w.exists():
        with b2w.open(encoding="utf-8", newline="") as fh:
            rows = list(csv.DictReader(fh))
        good = [r for r in rows if r.get("review_text") and r.get("overall_rating") in ("4", "5")]
        bad = [r for r in rows if r.get("review_text") and r.get("overall_rating") in ("1", "2")]
        for label, pool in (("avaliação de produto positiva", good), ("avaliação de produto negativa", bad)):
            for r in pool[::max(1, len(pool) // 12)][:12]:
                out.append(item("b2w", "comercial_consumidor", label, r["review_text"], lo,
                                f"b2w {r['submission_date']}", "B2W-Reviews01"))
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--raw", required=True)
    ap.add_argument("--corpora", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args(argv)
    raw, corpora, out = Path(args.raw).expanduser(), Path(args.corpora).expanduser(), Path(args.out).expanduser()
    items = []
    mpath = corpora / "machado-de-assis-corpus" / "machado_corpus.prefix.jsonl"
    if mpath.exists():
        mach = machado(mpath)
        # keep the corpus balanced: every non-chapter Machado text, a stride of Dom Casmurro chapters
        chapters = [m for m in mach if m["genre"] == "romance (capítulo)"]
        items += [m for m in mach if m["genre"] != "romance (capítulo)"] + chapters[::12]
    items += laws(raw) + abstracts(raw) + local_only(corpora)
    seen, unique = set(), []
    french = re.compile(r"\b(?:je|tu|les|des|une|dans|pour|mon|ma|mes|est|sont|avec|n'est|c'est|qu'|j'ai)\b", re.I)
    for it in items:
        if it["sha256"] in seen or it["words"] < 1:
            continue
        lang = language_of(it["text"])["value"]
        if lang == "en" or (it["words"] >= 30 and lang != "pt") or len(french.findall(it["text"])) >= 3:
            continue          # a PT-BR trial: Machado's French poems and non-Portuguese texts are left out
        seen.add(it["sha256"])
        unique.append(it)
    for k, it in enumerate(sorted(unique, key=lambda x: (x["source"], x["ref"]))):
        it["id"] = f"ft-{k:04d}"
    out.mkdir(parents=True, exist_ok=True)
    (out / "items.jsonl").write_text("".join(json.dumps(i, ensure_ascii=False) + "\n" for i in unique),
                                     encoding="utf-8")
    manifest_items = [{k: v for k, v in i.items() if k != "text"} | {"rights_by_operation": RIGHTS[i["rights"]]}
                      for i in sorted(unique, key=lambda x: x["id"])]
    from collections import Counter
    summary = {"items": len(unique), "genres": len({i["genre"] for i in unique}),
               "families": dict(Counter(i["family"] for i in unique)), "bands": dict(Counter(i["band"] for i in unique)),
               "rights": dict(Counter(i["rights"] for i in unique)), "sources": dict(Counter(i["source"] for i in unique))}
    print(json.dumps(summary, ensure_ascii=False, indent=1))
    target = ROOT / "evals" / "v0105" / "corpus_manifest.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps({"kind": "voznativa.fire_trial_corpus", "schema_version": 1,
                                  "text_stored_in_repository": False, "summary": summary,
                                  "items": manifest_items}, ensure_ascii=False, indent=1) + "\n",
                      encoding="utf-8", newline="\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
