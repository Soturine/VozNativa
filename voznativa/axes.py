"""Quality axes of a candidate, reported separately (v0.8 CP8).

Each axis is a **deterministic proxy** built from detectors the engine
already has; none is a naturalness, fluency or quality score, and the report
says so. An axis that has nothing to measure says ``not_applicable`` instead
of passing. Axes:

* ``editorial``: editorial formulas the candidate removed and the ones it
  introduced (``patterns``);
* ``unnecessary_change``: sentences the plan said to keep that changed, and
  any change at all when the plan was ``no_change`` (``planner``);
* ``slang_and_epoch``: slang or epoch-marked terms introduced without
  evidence (``temporal``);
* ``regional``: regional forms introduced without a licensing pack
  (``regional``);
* ``genre``: the genre the router infers for the candidate versus the source
  (a drift is a signal, not an error: a requested destination may change it);
* ``voice``: distance to the author's profile, only when one is given
  (``drift``; uncalibrated).

``signal`` means a person or a judge should look; ``ok`` means the proxy saw
nothing, which is not a proof of quality.
"""
from __future__ import annotations

PROXY_NOTE = "deterministic proxy from the engine's detectors; not a quality, naturalness or fluency score"


def _axis(status: str, method: str, **evidence) -> dict:
    return {"status": status, "method": method, **evidence}


def evaluate(original: str, candidate: str, context: dict, profile: dict | None = None) -> dict:
    from . import drift as drift_mod
    from . import patterns as patterns_mod
    from . import planner as planner_mod
    from . import regional, temporal
    from .router import explicit_channel, route

    genre = context["genre"]["value"]
    channel = explicit_channel(context)
    register = context["register"]["value"]
    axes = {}

    before = patterns_mod.detect(original, genre, channel, register)["findings"]
    after = patterns_mod.detect(candidate, genre, channel, register)["findings"]
    removed = sorted({f["id"] for f in before} - {f["id"] for f in after})
    introduced = sorted({f["id"] for f in after} - {f["id"] for f in before})
    axes["editorial"] = _axis("signal" if introduced else "ok", "patterns (genre-aware editorial findings)",
                              removed=removed, introduced=introduced)

    the_plan = planner_mod.plan(original, context)
    if candidate == original:
        axes["unnecessary_change"] = _axis("ok", "planner", changed=False)
    elif the_plan["decision"] == "no_change":
        axes["unnecessary_change"] = _axis("signal", "planner", changed=True,
                                           note="the plan found nothing to change, the candidate changed the text")
    else:
        fit = planner_mod.adherence(the_plan, original, candidate, genre, channel, register)
        axes["unnecessary_change"] = _axis("signal" if fit["unplanned_edits"] else "ok", "planner adherence",
                                           unplanned_edits=len(fit["unplanned_edits"]), scope=fit["scope"])

    slang = temporal.introduced_terms(original, candidate, temporal.activate(context, original))
    axes["slang_and_epoch"] = _axis("signal" if slang else "ok", "temporal lexicon (attested senses)",
                                    introduced=sorted({s.get("term", s.get("form", "?")) for s in slang}))

    forms = regional.introduced_forms(original, candidate, regional.activate(context, original, profile))
    axes["regional"] = _axis("signal" if forms else "ok", "regional evidence packs",
                             introduced=sorted({f["form"] for f in forms}))

    # The full router (structure and channel cues too), not the bare genre scorer.
    source_genre, candidate_genre = route(original)["genre"]["value"], route(candidate)["genre"]["value"]
    if "unknown" in (source_genre, candidate_genre):
        axes["genre"] = _axis("not_applicable", "router genre inference (abstained)",
                              source=source_genre, candidate=candidate_genre)
    else:
        axes["genre"] = _axis("signal" if source_genre != candidate_genre else "ok", "router genre inference",
                              source=source_genre, candidate=candidate_genre)

    if profile:
        src_d, out_d = drift_mod.voice_distance(original, profile), drift_mod.voice_distance(candidate, profile)
        if "error" in src_d or "error" in out_d:
            axes["voice"] = _axis("not_applicable", "voice profile distance",
                                  reason=src_d.get("error") or out_d.get("error"))
        else:
            moved_away = out_d["mean"] > src_d["mean"]
            axes["voice"] = _axis("signal" if moved_away else "ok", "voice profile distance (uncalibrated)",
                                  source_distance=src_d["mean"], candidate_distance=out_d["mean"])
    else:
        axes["voice"] = _axis("not_applicable", "voice profile distance", reason="no author profile given")

    return {"kind": "voznativa.quality_axes", "schema_version": 1, "note": PROXY_NOTE, "axes": axes,
            "signals": sorted(k for k, v in axes.items() if v["status"] == "signal")}
