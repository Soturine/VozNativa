"""User and project configuration for ``voznativa rewrite`` (v0.9 CP1).

One configuration system, two files, one precedence:

    command-line flag  >  project file  >  user file  >  built-in default

* **User file**: ``$VOZNATIVA_CONFIG`` if set; otherwise
  ``%APPDATA%\\voznativa\\config.toml`` on Windows and
  ``$XDG_CONFIG_HOME/voznativa/config.toml`` (``~/.config/...``) elsewhere.
* **Project file**: ``.voznativa.toml`` in the current directory or the
  nearest parent, stopping at the first directory that holds ``.git``.

Both are TOML (``tomllib``, standard library) with a single ``[rewrite]``
table. Values are checked by type and unknown keys are refused, so a typo is
an error instead of a silently ignored setting.

**Trust boundary.** A project file comes with a repository someone else may
have written. Keys that decide *what runs*, *where the text is sent* or
*what reaches the model process* (``cmd``, ``judge_cmd``, ``provider_env``,
``provider_env_allow`` and the ``api_*`` keys of the chat-API provider) are
accepted only from the user file or the command line; in a project file
they are refused with an error. Otherwise cloning a hostile repository and
running ``voznativa rewrite`` would execute a command chosen by the
repository. No file is ever written by VozNativa, and no secret value is read
from either file: credentials stay in the environment.
"""
from __future__ import annotations

import os
import sys
import tomllib
from pathlib import Path

PROJECT_FILE = ".voznativa.toml"

# key -> (type, built-in default, allowed in a project file)
KEYS: dict[str, tuple[type | tuple, object, bool]] = {
    "cmd": (str, None, False),
    "judge_cmd": (str, None, False),
    "provider_env": (str, "inherit", False),
    "provider_env_allow": (list, [], False),
    # v0.9 CP2: chat-API provider. The URL decides where the text goes: user file or flag only.
    "api_url": (str, None, False),
    "api_model": (str, None, False),
    "api_key_env": (str, None, False),
    "api_allow_remote": (bool, False, False),
    "judge_api_url": (str, None, False),
    "judge_api_model": (str, None, False),
    "timeout": ((int, float), 300.0, True),
    "attempts": (int, 3, True),
    "candidates": (int, 1, True),
    "judge_votes": (int, 2, True),
    "max_calls": (int, 800, True),
    "segment_words": (int, 600, True),
    "long_form": (str, "auto", True),
    "genre": (str, None, True),
    "channel": (str, None, True),
    "register": (str, None, True),
    "protect": (list, [], True),
}
CHOICES = {"provider_env": ("inherit", "minimal"), "long_form": ("auto", "on", "off")}


class ConfigError(ValueError):
    """A configuration file is unreadable, has an unknown key, a wrong type or a forbidden key."""


def user_path() -> Path:
    explicit = os.environ.get("VOZNATIVA_CONFIG")
    if explicit:
        return Path(explicit)
    if sys.platform == "win32" and os.environ.get("APPDATA"):
        return Path(os.environ["APPDATA"]) / "voznativa" / "config.toml"
    base = os.environ.get("XDG_CONFIG_HOME") or str(Path.home() / ".config")
    return Path(base) / "voznativa" / "config.toml"


def project_path(start: Path | None = None) -> Path | None:
    here = (start or Path.cwd()).resolve()
    for folder in (here, *here.parents):
        candidate = folder / PROJECT_FILE
        if candidate.is_file():
            return candidate
        if (folder / ".git").exists():
            return None
    return None


def _load(path: Path, scope: str) -> dict:
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError) as error:
        raise ConfigError(f"{scope} config {path}: cannot read ({error})") from None
    except tomllib.TOMLDecodeError as error:
        raise ConfigError(f"{scope} config {path}: invalid TOML ({error})") from None
    extra = sorted(set(data) - {"rewrite"})
    if extra:
        raise ConfigError(f"{scope} config {path}: unknown table(s) {extra}; only [rewrite] exists")
    table = data.get("rewrite", {})
    if not isinstance(table, dict):
        raise ConfigError(f"{scope} config {path}: [rewrite] must be a table")
    out = {}
    for key, value in table.items():
        if key not in KEYS:
            raise ConfigError(f"{scope} config {path}: unknown key '{key}' (known: {', '.join(sorted(KEYS))})")
        kind, _default, project_ok = KEYS[key]
        if scope == "project" and not project_ok:
            raise ConfigError(f"project config {path}: '{key}' is refused in a project file (it decides what runs "
                              f"or what reaches the model process); set it in the user file "
                              f"({user_path()}) or on the command line")
        if (isinstance(value, bool) != (kind is bool)) or not isinstance(value, kind):
            raise ConfigError(f"{scope} config {path}: '{key}' has the wrong type ({type(value).__name__})")
        if kind is list and not all(isinstance(v, str) for v in value):
            raise ConfigError(f"{scope} config {path}: '{key}' must be a list of strings")
        if key in CHOICES and value not in CHOICES[key]:
            raise ConfigError(f"{scope} config {path}: '{key}' must be one of {CHOICES[key]}")
        out[key] = value
    return out


def load(cwd: Path | None = None) -> dict:
    """The files that apply here: ``{"user": (path, values) | None, "project": ...}``."""
    files = {"user": None, "project": None}
    upath = user_path()
    if upath.is_file():
        files["user"] = (upath, _load(upath, "user"))
    ppath = project_path(cwd)
    if ppath is not None:
        files["project"] = (ppath, _load(ppath, "project"))
    return files


def resolve(flags: dict, files: dict | None = None) -> dict:
    """Effective value and source of every key. ``flags`` holds the command
    line values, ``None`` meaning "not given". ``protect`` is the union of
    all sources (a term protected anywhere stays protected)."""
    files = load() if files is None else files
    out = {}
    for key, (_kind, default, _project_ok) in KEYS.items():
        layers = [("flag", flags.get(key))]
        for scope in ("project", "user"):
            if files.get(scope):
                layers.append((scope, files[scope][1].get(key)))
        if key == "protect":
            merged, sources = [], []
            for scope, value in layers:
                for term in value or []:
                    if term not in merged:
                        merged.append(term)
                if value:
                    sources.append(scope)
            out[key] = {"value": merged, "source": "+".join(sources) or "default"}
            continue
        for scope, value in layers:
            if value is not None:
                out[key] = {"value": value, "source": scope}
                break
        else:
            out[key] = {"value": default, "source": "default"}
    return out


def describe(files: dict | None = None) -> dict:
    files = load() if files is None else files
    return {"kind": "voznativa.config", "schema_version": 1,
            "precedence": ["flag", "project", "user", "default"],
            "user_file": {"path": str(user_path()), "present": files["user"] is not None},
            "project_file": {"path": str(files["project"][0]) if files["project"] else None,
                             "present": files["project"] is not None, "name": PROJECT_FILE},
            "project_refused_keys": sorted(k for k, v in KEYS.items() if not v[2]),
            "effective": resolve({}, files)}
