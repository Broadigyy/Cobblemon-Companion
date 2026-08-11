import webbrowser

import json
import os
import re
import threading
import sys
import zipfile
import tempfile
import traceback
import urllib.request
import urllib.error
import tkinter as tk
from tkinter import messagebox, filedialog
from pathlib import Path
from PIL import Image, ImageDraw, ImageTk
from datetime import date

APP_NAME = "Cobblemon Companion"
APP_VERSION = "1.7.1"
SPECIES_PARSER_VERSION = 5

def user_data_dir() -> Path:
    base = os.getenv("APPDATA")
    path = Path(base) / APP_NAME if base else Path.home() / ".cobblemon_companion"
    path.mkdir(parents=True, exist_ok=True)
    return path

SAVE_FILE = user_data_dir() / "profile.json"
DEX_FILE = user_data_dir() / "cobblemon_species.json"
DEX_META_FILE = user_data_dir() / "cobblemon_species_meta.json"
SPAWN_FILE = user_data_dir() / "cobblemon_spawns.json"
SPRITE_CACHE_DIR = user_data_dir() / "sprites"
MOVE_META_FILE = user_data_dir() / "move_metadata.json"
ITEM_DB_FILE = user_data_dir() / "item_database.json"
ABILITY_DB_FILE = user_data_dir() / "ability_database.json"
ITEM_INDEX_FILE = user_data_dir() / "cobblemon_item_index_v2.json"
ITEM_DETAIL_FILE = user_data_dir() / "cobblemon_item_details_v1.json"
SPRITE_CACHE_DIR.mkdir(parents=True, exist_ok=True)

def resource_path(filename: str) -> str:
    """Resolve bundled assets both from source and a PyInstaller build."""
    base = getattr(sys, "_MEIPASS", os.path.abspath(os.path.dirname(__file__)))
    return os.path.join(base, filename)

BG = "#161b22"
PANEL = "#202833"
PANEL_2 = "#283341"
CARD = "#2f3b4b"
TEXT = "#f4f7fb"
MUTED = "#aeb8c5"
ACCENT = "#ef5350"
ACCENT_2 = "#5aa9ff"
GOOD = "#63c174"

TYPE_COLORS = {
    "Normal": "#9fa19f", "Fire": "#e62829", "Water": "#2980ef",
    "Electric": "#fac000", "Grass": "#3fa129", "Ice": "#3dcef3",
    "Fighting": "#ff8000", "Poison": "#9141cb", "Ground": "#915121",
    "Flying": "#81b9ef", "Psychic": "#ef4179", "Bug": "#91a119",
    "Rock": "#afa981", "Ghost": "#704170", "Dragon": "#5060e1",
    "Dark": "#624d4e", "Steel": "#60a1b8", "Fairy": "#ef70ef"
}

FALLBACK_POKEDEX = [
    {"dex": 1, "name": "Bulbasaur", "types": ["Grass", "Poison"], "hp": 45, "atk": 49, "def": 49, "spa": 65, "spd": 65, "spe": 45},
    {"dex": 4, "name": "Charmander", "types": ["Fire"], "hp": 39, "atk": 52, "def": 43, "spa": 60, "spd": 50, "spe": 65},
    {"dex": 7, "name": "Squirtle", "types": ["Water"], "hp": 44, "atk": 48, "def": 65, "spa": 50, "spd": 64, "spe": 43},
    {"dex": 25, "name": "Pikachu", "types": ["Electric"], "hp": 35, "atk": 55, "def": 40, "spa": 50, "spd": 50, "spe": 90},
    {"dex": 94, "name": "Gengar", "types": ["Ghost", "Poison"], "hp": 60, "atk": 65, "def": 60, "spa": 130, "spd": 75, "spe": 110},
    {"dex": 123, "name": "Scyther", "types": ["Bug", "Flying"], "hp": 70, "atk": 110, "def": 80, "spa": 55, "spd": 80, "spe": 105},
    {"dex": 133, "name": "Eevee", "types": ["Normal"], "hp": 55, "atk": 55, "def": 50, "spa": 45, "spd": 65, "spe": 55},
    {"dex": 147, "name": "Dratini", "types": ["Dragon"], "hp": 41, "atk": 64, "def": 45, "spa": 50, "spd": 50, "spe": 50},
    {"dex": 246, "name": "Larvitar", "types": ["Rock", "Ground"], "hp": 50, "atk": 64, "def": 50, "spa": 45, "spd": 50, "spe": 41},
    {"dex": 280, "name": "Ralts", "types": ["Psychic", "Fairy"], "hp": 28, "atk": 25, "def": 25, "spa": 45, "spd": 35, "spe": 40},
    {"dex": 302, "name": "Sableye", "types": ["Dark", "Ghost"], "hp": 50, "atk": 75, "def": 75, "spa": 65, "spd": 65, "spe": 50},
    {"dex": 349, "name": "Feebas", "types": ["Water"], "hp": 20, "atk": 15, "def": 20, "spa": 10, "spd": 55, "spe": 80},
    {"dex": 374, "name": "Beldum", "types": ["Steel", "Psychic"], "hp": 40, "atk": 55, "def": 80, "spa": 35, "spd": 60, "spe": 30},
    {"dex": 447, "name": "Riolu", "types": ["Fighting"], "hp": 40, "atk": 70, "def": 40, "spa": 35, "spd": 40, "spe": 60},
    {"dex": 479, "name": "Rotom", "types": ["Electric", "Ghost"], "hp": 50, "atk": 50, "def": 77, "spa": 95, "spd": 77, "spe": 91},
    {"dex": 607, "name": "Litwick", "types": ["Ghost", "Fire"], "hp": 50, "atk": 30, "def": 55, "spa": 65, "spd": 55, "spe": 20},
    {"dex": 778, "name": "Mimikyu", "types": ["Ghost", "Fairy"], "hp": 55, "atk": 90, "def": 80, "spa": 50, "spd": 105, "spe": 96},
    {"dex": 999, "name": "Gimmighoul", "types": ["Ghost"], "hp": 45, "atk": 30, "def": 70, "spa": 75, "spd": 70, "spe": 10},
    {"dex": 1000, "name": "Gholdengo", "types": ["Steel", "Ghost"], "hp": 87, "atk": 60, "def": 95, "spa": 133, "spd": 91, "spe": 84},
]


def _title_type(value):
    return str(value or "").replace("_", " ").title()


ROTOM_FORM_SIGNATURE_MOVES = {
    "Rotom Heat": "Overheat",
    "Rotom Wash": "Hydro Pump",
    "Rotom Frost": "Blizzard",
    "Rotom Fan": "Air Slash",
    "Rotom Mow": "Leaf Storm",
}

ROTOM_FORM_TYPES = {
    "Rotom Heat": ["Electric", "Fire"],
    "Rotom Wash": ["Electric", "Water"],
    "Rotom Frost": ["Electric", "Ice"],
    "Rotom Fan": ["Electric", "Flying"],
    "Rotom Mow": ["Electric", "Grass"],
}

def _form_display_name(base_name, form_id, raw_form=None):
    fid = str(form_id or "").strip().lower().replace("_", " ").replace("-", " ")
    if base_name.casefold() == "rotom":
        for suffix in ("heat", "wash", "frost", "fan", "mow"):
            if suffix in fid:
                return f"Rotom {suffix.title()}"

    if isinstance(raw_form, dict):
        explicit = (
            raw_form.get("displayName")
            or raw_form.get("formName")
            or raw_form.get("name")
            or ""
        )
        explicit = str(explicit or "").strip()
        if explicit and explicit.casefold() != base_name.casefold():
            if base_name.casefold() in explicit.casefold():
                return explicit
            return f"{base_name} {friendly_resource_name(explicit)}"

    if isinstance(raw_form, dict):
        aspects = raw_form.get("aspects") or []
        if isinstance(aspects, list):
            meaningful = [
                friendly_resource_name(x)
                for x in aspects
                if str(x).strip()
            ]
            if meaningful:
                return f"{base_name} {' '.join(meaningful)}".strip()

    pretty = friendly_resource_name(fid)
    return f"{base_name} {pretty}".strip() if pretty else base_name

def _move_id_from_pretty(name):
    return re.sub(r"[^a-z0-9]+", "_", str(name or "").lower()).strip("_")

def _merge_form_species(base_item, raw_form, form_id):
    item = dict(base_item)
    item["is_form"] = True
    item["base_species"] = base_item.get("name", "")
    item["form_id"] = str(form_id or "")
    item["name"] = _form_display_name(base_item.get("name",""), form_id, raw_form)

    if isinstance(raw_form, dict):
        types = []
        if raw_form.get("primaryType"):
            types.append(_title_type(raw_form.get("primaryType")))
        if raw_form.get("secondaryType"):
            types.append(_title_type(raw_form.get("secondaryType")))
        if types:
            item["types"] = types

        stats = raw_form.get("baseStats") or raw_form.get("stats") or {}
        if isinstance(stats, dict):
            keys = {
                "hp":"hp", "attack":"atk", "defence":"def", "defense":"def",
                "special_attack":"spa", "specialAttack":"spa",
                "special_defence":"spd", "specialDefense":"spd", "speed":"spe",
            }
            for raw_key, dst in keys.items():
                if raw_key in stats:
                    try:
                        item[dst] = int(stats.get(raw_key) or 0)
                    except Exception:
                        pass

        if raw_form.get("abilities"):
            item["abilities"] = raw_form.get("abilities") or []
        if raw_form.get("eggGroups"):
            item["egg_groups"] = raw_form.get("eggGroups") or []

        form_moves = raw_form.get("moves") or raw_form.get("moveSet") or []
    else:
        form_moves = []

    merged_moves = list(base_item.get("moves", []) or [])
    if isinstance(form_moves, list):
        for move in form_moves:
            if move not in merged_moves:
                merged_moves.append(move)

    sig = ROTOM_FORM_SIGNATURE_MOVES.get(item["name"])
    if sig:
        existing = {
            friendly_resource_name(str(x).rsplit(":",1)[-1]).casefold()
            for x in merged_moves
        }
        if sig.casefold() not in existing:
            merged_moves.append(f"form:{_move_id_from_pretty(sig)}")

    item["moves"] = merged_moves

    if item["name"] in ROTOM_FORM_TYPES:
        item["types"] = list(ROTOM_FORM_TYPES[item["name"]])

    return item

def expand_species_forms(raw, base_item):
    out = []
    forms = raw.get("forms") or raw.get("formData") or raw.get("variations") or []

    if isinstance(forms, dict):
        iterable = list(forms.items())
    elif isinstance(forms, list):
        iterable = []
        for i, form in enumerate(forms):
            if isinstance(form, dict):
                fid = _form_identity(base_item.get("name",""), form, i)
                iterable.append((fid, form))
    else:
        iterable = []

    for form_id, raw_form in iterable:
        name = _form_display_name(base_item.get("name",""), form_id, raw_form)
        if not name or name.casefold() == base_item.get("name","").casefold():
            continue
        if base_item.get("name","").casefold() == "rotom" and name not in ROTOM_FORM_SIGNATURE_MOVES:
            continue
        out.append(_merge_form_species(base_item, raw_form, form_id))

    if base_item.get("name","").casefold() == "rotom":
        existing = {x["name"] for x in out}
        for name in ROTOM_FORM_SIGNATURE_MOVES:
            if name in existing:
                continue
            form_id = name.split()[-1].lower()
            item = _merge_form_species(base_item, {}, form_id)
            item["name"] = name
            item["types"] = list(ROTOM_FORM_TYPES[name])
            out.append(item)

    return out

def normalize_species(raw):
    stats = raw.get("baseStats", {}) or {}
    types = []
    if raw.get("primaryType"):
        types.append(_title_type(raw.get("primaryType")))
    if raw.get("secondaryType"):
        types.append(_title_type(raw.get("secondaryType")))
    return {
        "dex": int(raw.get("nationalPokedexNumber", 0) or 0),
        "name": str(raw.get("name", "")).strip(),
        "types": types,
        "hp": int(stats.get("hp", 0) or 0),
        "atk": int(stats.get("attack", 0) or 0),
        "def": int(stats.get("defence", 0) or 0),
        "spa": int(stats.get("special_attack", 0) or 0),
        "spd": int(stats.get("special_defence", 0) or 0),
        "spe": int(stats.get("speed", 0) or 0),
        "catch_rate": raw.get("catchRate"),
        "base_friendship": raw.get("baseFriendship"),
        "experience_group": raw.get("experienceGroup"),
        "egg_groups": raw.get("eggGroups", []) or [],
        "abilities": raw.get("abilities", []) or [],
        "moves": raw.get("moves", []) or [],
        "evolutions": raw.get("evolutions", []) or [],
        "labels": raw.get("labels", []) or [],
        "height": raw.get("height"),
        "weight": raw.get("weight"),
        "implemented": True,
        "resource_identifier": raw.get("resourceIdentifier") or raw.get("identifier") or raw.get("name", "").lower().replace(" ", ""),
    }

def inspect_cobblemon_jar(jar_path):
    """Return simple diagnostics about a selected JAR."""
    jar_path = Path(jar_path)
    info = {
        "path": str(jar_path),
        "total_files": 0,
        "json_files": 0,
        "species_json_files": 0,
        "spawn_json_files": 0,
    }
    if not jar_path.exists():
        return info
    with zipfile.ZipFile(jar_path, "r") as zf:
        names = zf.namelist()
        info["total_files"] = len(names)
        for n in names:
            low = n.replace("\\", "/").lower()
            if low.endswith(".json"):
                info["json_files"] += 1
            if low.endswith(".json") and "/data/cobblemon/species/" in ("/" + low):
                info["species_json_files"] += 1
            if low.endswith(".json") and (
                "/data/cobblemon/spawn_pool_world/" in ("/" + low)
                or "/data/cobblemon/spawns/" in ("/" + low)
            ):
                info["spawn_json_files"] += 1
    return info

def audit_species_from_cobblemon_jar(jar_path):
    """Count modern/legacy species flag patterns for diagnostics."""
    jar_path = Path(jar_path)
    report = {
        "species_json_files": 0,
        "valid_species": 0,
        "explicit_true": 0,
        "explicit_false": 0,
        "missing_implemented": 0,
        "invalid": 0,
    }
    if not jar_path.exists():
        return report

    with zipfile.ZipFile(jar_path, "r") as zf:
        for name in zf.namelist():
            low = name.replace("\\", "/").lower()
            if not low.endswith(".json"):
                continue
            if "/data/cobblemon/species/" not in ("/" + low):
                continue

            report["species_json_files"] += 1
            try:
                raw = json.loads(zf.read(name).decode("utf-8-sig"))
            except Exception:
                report["invalid"] += 1
                continue

            if not isinstance(raw, dict):
                report["invalid"] += 1
                continue

            flag = raw.get("implemented", None)
            if flag is None:
                report["missing_implemented"] += 1
            elif flag is True or flag == 1 or str(flag).strip().lower() == "true":
                report["explicit_true"] += 1
            elif flag is False or flag == 0 or str(flag).strip().lower() == "false":
                report["explicit_false"] += 1

            try:
                dex = int(raw.get("nationalPokedexNumber", 0) or 0)
            except Exception:
                dex = 0
            name_value = str(raw.get("name", "") or "").strip()
            if dex and name_value:
                report["valid_species"] += 1

    return report



def _target_species_name(target):
    target = str(target or "").strip()
    if ":" in target:
        target = target.split(":", 1)[1]
    return friendly_resource_name(target)

def read_species_additions_from_jar(jar_path):
    """Collect species_additions from any namespace inside a mod/datapack JAR."""
    jar_path = Path(jar_path)
    additions = []

    if not jar_path.exists():
        return additions

    try:
        with zipfile.ZipFile(jar_path, "r") as zf:
            for name in zf.namelist():
                low = "/" + name.replace("\\", "/").lower()
                if not low.endswith(".json"):
                    continue
                if "/species_additions/" not in low:
                    continue

                try:
                    raw = json.loads(zf.read(name).decode("utf-8-sig"))
                except Exception:
                    continue

                if not isinstance(raw, dict):
                    continue

                target = raw.get("target")
                if not target:
                    continue

                additions.append({
                    "target": _target_species_name(target),
                    "raw": raw,
                    "source_file": f"{jar_path.name}::{name}",
                })
    except Exception:
        pass

    return additions

def apply_species_addition(base_raw, addition_raw):
    """Apply simple species-addition replacement rules and append forms/evolutions.

    Cobblemon species additions replace ordinary fields, while forms/evolutions
    append rather than replace. We mimic that enough for Companion's data model.
    """
    merged = dict(base_raw)

    for key, value in (addition_raw or {}).items():
        if key == "target":
            continue

        if key in ("forms", "evolutions"):
            existing = list(merged.get(key, []) or [])
            incoming = list(value or []) if isinstance(value, list) else []
            merged[key] = existing + incoming
        else:
            merged[key] = value

    return merged

def merge_species_additions_into_raw_species(raw_species_records, additions):
    """Return species records after applying additions targeted by species name."""
    by_name = {}
    order = []

    for record in raw_species_records:
        raw = record["raw"]
        name = str(raw.get("name", "") or "").strip()
        if not name:
            continue
        key = name.casefold()
        by_name[key] = dict(record)
        order.append(key)

    for addition in additions:
        target = str(addition.get("target", "") or "").strip().casefold()
        record = by_name.get(target)
        if not record:
            continue

        updated = dict(record)
        updated["raw"] = apply_species_addition(
            record["raw"],
            addition.get("raw", {})
        )
        # Track the latest addition source for diagnostics.
        sources = list(updated.get("addition_sources", []) or [])
        sources.append(addition.get("source_file", ""))
        updated["addition_sources"] = sources
        by_name[target] = updated

    return [by_name[k] for k in order if k in by_name]

def _form_identity(base_name, raw_form, fallback_id):
    """Create a useful stable identity from aspects/name/form metadata."""
    if not isinstance(raw_form, dict):
        return str(fallback_id)

    for key in ("form", "formName", "identifier", "name"):
        value = raw_form.get(key)
        if value:
            return str(value)

    aspects = raw_form.get("aspects") or []
    if isinstance(aspects, list) and aspects:
        # Regional/form aspects are often the most meaningful identifier.
        return "-".join(str(x) for x in aspects if x)

    return str(fallback_id)

def import_species_from_cobblemon_jar_single(jar_path):
    """Read species + species_additions from one JAR and expand battle forms."""
    jar_path = Path(jar_path)
    if not jar_path.exists():
        raise FileNotFoundError(jar_path)

    species = {}
    readable_species = 0
    implemented_count = 0
    raw_records = []

    with zipfile.ZipFile(jar_path, "r") as zf:
        for name in zf.namelist():
            low = "/" + name.replace("\\", "/").lower()
            if not low.endswith(".json"):
                continue
            if "/data/cobblemon/species/" not in low:
                continue

            try:
                raw = json.loads(zf.read(name).decode("utf-8-sig"))
            except Exception:
                continue

            if not isinstance(raw, dict):
                continue

            readable_species += 1
            raw_records.append({
                "raw": raw,
                "source_file": f"{jar_path.name}::{name}",
            })

    additions = read_species_additions_from_jar(jar_path)
    raw_records = merge_species_additions_into_raw_species(raw_records, additions)

    for record in raw_records:
        raw = record["raw"]

        implemented = raw.get("implemented", None)
        explicit_false = (
            implemented is False
            or implemented == 0
            or str(implemented).strip().lower() == "false"
        )
        if explicit_false:
            continue

        try:
            item = normalize_species(raw)
        except Exception:
            continue

        if not item.get("name") or not item.get("dex"):
            continue

        item["source_file"] = record.get("source_file", "")
        if record.get("addition_sources"):
            item["addition_sources"] = record["addition_sources"]

        implemented_count += 1
        species[(item["dex"], item["name"].casefold())] = item

        for form_item in expand_species_forms(raw, item):
            form_item["source_file"] = record.get("source_file", "")
            if record.get("addition_sources"):
                form_item["addition_sources"] = record["addition_sources"]
            species[(form_item["dex"], form_item["name"].casefold())] = form_item

    result = sorted(species.values(), key=lambda p: (p["dex"], p["name"].lower()))

    if not result:
        diag = inspect_cobblemon_jar(jar_path)
        raise ValueError(
            "No implemented species could be imported from this JAR.\\n\\n"
            f"JAR: {jar_path.name}\\n"
            f"JSON files: {diag['json_files']}\\n"
            f"Species JSON files found: {diag['species_json_files']}\\n"
            f"Readable species files: {readable_species}\\n"
            f"Valid species accepted: {implemented_count}\\n\\n"
            "Your existing cached Pokédex has NOT been deleted."
        )

    return result


def import_species_from_cobblemon_jar(jar_path):
    return import_species_from_data_sources(jar_path)

def form_audit_from_species(species):
    """Summarize discovered first-class form entries."""
    forms = [p for p in (species or []) if p.get("is_form")]
    by_base = {}
    for p in forms:
        by_base.setdefault(p.get("base_species","Unknown"), []).append(p.get("name",""))
    return {
        "form_count": len(forms),
        "species_with_forms": len(by_base),
        "forms_by_species": {
            k: sorted(v) for k, v in sorted(by_base.items())
        },
    }

def import_species_from_data_sources(primary_jar):
    """Merge base species plus form additions from all compatible sibling JARs."""
    sources = discover_cobblemon_data_jars(primary_jar)
    merged = {}

    # First load every full species record. Primary source wins duplicates because
    # it is first in discover_cobblemon_data_jars().
    for source in sources:
        try:
            species = import_species_from_cobblemon_jar_single(source)
        except Exception:
            continue

        for item in species:
            key = (item.get("dex"), str(item.get("name","")).casefold())
            if key not in merged:
                item = dict(item)
                item["data_source"] = source.name
                merged[key] = item

    # Then apply species_additions from every source to already-known targets.
    # This is crucial for addons that contain ONLY species_additions and no
    # standalone species files.
    for source in sources:
        for addition in read_species_additions_from_jar(source):
            target_name = str(addition.get("target","") or "").strip()
            if not target_name:
                continue

            base = next(
                (
                    item for item in merged.values()
                    if not item.get("is_form")
                    and str(item.get("name","")).casefold() == target_name.casefold()
                ),
                None
            )
            if not base:
                continue

            raw = addition.get("raw", {}) or {}

            # Apply common base-field replacements that matter to Companion.
            if raw.get("primaryType") or raw.get("secondaryType"):
                types = []
                if raw.get("primaryType"):
                    types.append(_title_type(raw.get("primaryType")))
                if raw.get("secondaryType"):
                    types.append(_title_type(raw.get("secondaryType")))
                if types:
                    base["types"] = types

            if raw.get("abilities"):
                base["abilities"] = raw.get("abilities") or []
            if raw.get("eggGroups"):
                base["egg_groups"] = raw.get("eggGroups") or []
            if raw.get("moves"):
                base["moves"] = raw.get("moves") or []

            stats = raw.get("baseStats") or {}
            if isinstance(stats, dict) and stats:
                mapping = {
                    "hp":"hp","attack":"atk","defence":"def","defense":"def",
                    "special_attack":"spa","specialAttack":"spa",
                    "special_defence":"spd","specialDefense":"spd","speed":"spe"
                }
                for rk,nk in mapping.items():
                    if rk in stats:
                        try:
                            base[nk] = int(stats.get(rk) or 0)
                        except Exception:
                            pass

            # Forms/evolutions append in Cobblemon species additions.
            forms = raw.get("forms") or []
            if isinstance(forms, list):
                for idx, raw_form in enumerate(forms):
                    if not isinstance(raw_form, dict):
                        continue
                    fid = _form_identity(base.get("name",""), raw_form, idx)
                    form_item = _merge_form_species(base, raw_form, fid)
                    form_item["data_source"] = source.name
                    form_item["addition_source"] = addition.get("source_file","")
                    key = (form_item.get("dex"), form_item.get("name","").casefold())
                    if key not in merged:
                        merged[key] = form_item

            if raw.get("evolutions"):
                base_evos = list(base.get("evolutions", []) or [])
                for evo in raw.get("evolutions") or []:
                    if evo not in base_evos:
                        base_evos.append(evo)
                base["evolutions"] = base_evos

    return sorted(merged.values(), key=lambda p: (p["dex"], p["name"].lower()))


def enrich_cached_species_from_jar(species, jar_path):
    """Add move/ability data from the installed Cobblemon JAR to an existing Dex cache."""
    jar_path = Path(jar_path)
    if not jar_path.exists() or not species:
        return species, 0

    by_dex = {}
    for item in species:
        try:
            by_dex[int(item.get("dex", 0) or 0)] = item
        except Exception:
            continue

    updated = 0
    with zipfile.ZipFile(jar_path, "r") as zf:
        for name in zf.namelist():
            low = name.replace("\\", "/").lower()
            if not low.endswith(".json"):
                continue
            if "/data/cobblemon/species/" not in ("/" + low):
                continue
            try:
                raw = json.loads(zf.read(name).decode("utf-8-sig"))
            except Exception:
                continue
            if not isinstance(raw, dict):
                continue
            try:
                dex = int(raw.get("nationalPokedexNumber", 0) or 0)
            except Exception:
                continue
            item = by_dex.get(dex)
            if not item:
                continue

            changed = False
            moves = raw.get("moves", []) or []
            abilities = raw.get("abilities", []) or []
            evolutions = raw.get("evolutions", []) or []
            if moves and item.get("moves") != moves:
                item["moves"] = moves
                changed = True
            if abilities and item.get("abilities") != abilities:
                item["abilities"] = abilities
                changed = True
            if evolutions and item.get("evolutions") != evolutions:
                item["evolutions"] = evolutions
                changed = True
            if changed:
                updated += 1

    if updated:
        DEX_FILE.write_text(
            json.dumps(species, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )
    return species, updated

def dex_has_move_data(species):
    return any(bool(p.get("moves")) for p in (species or []))

def dex_has_evolution_data(species):
    """True when the cache contains at least some real evolution data."""
    return any(bool(p.get("evolutions")) for p in (species or []))


def save_dex(species, jar_path):
    DEX_FILE.write_text(json.dumps(species, indent=2, ensure_ascii=False), encoding="utf-8")
    try:
        spawns = import_spawns_from_cobblemon_jar(jar_path)
        save_spawn_data(spawns)
        spawn_count = len(spawns)
    except Exception:
        spawn_count = 0
    data_sources = discover_cobblemon_data_jars(jar_path)
    meta = {
        "source_jar": str(jar_path),
        "species_count": len(species),
        "spawn_count": spawn_count,
        "source": "Cobblemon + sibling addon datapack JARs",
        "species_parser_version": SPECIES_PARSER_VERSION,
        "data_sources": [str(p) for p in data_sources],
        "data_source_count": len(data_sources),
    }
    DEX_META_FILE.write_text(json.dumps(meta, indent=2), encoding="utf-8")

def load_dex():
    try:
        if DEX_FILE.exists():
            data = json.loads(DEX_FILE.read_text(encoding="utf-8"))
            if isinstance(data, list) and data:
                return data
    except Exception:
        pass
    return list(FALLBACK_POKEDEX)

def load_dex_meta():
    try:
        if DEX_META_FILE.exists():
            return json.loads(DEX_META_FILE.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {}

def candidate_cobblemon_jars():
    home = Path.home()
    appdata = Path(os.getenv("APPDATA", home))
    roots = [
        appdata / ".minecraft" / "mods",
        home / "curseforge" / "minecraft" / "Instances",
        home / "Documents" / "Curse" / "Minecraft" / "Instances",
        appdata / "com.modrinth.theseus" / "profiles",
        appdata / "ModrinthApp" / "profiles",
    ]
    found = []
    for root in roots:
        if not root.exists():
            continue
        try:
            for p in root.rglob("*.jar"):
                name = p.name.lower()
                if "cobblemon" in name and "cobblemonintegrations" not in name:
                    found.append(p)
        except (PermissionError, OSError):
            continue

    def version_key(p):
        try:
            return (p.stat().st_mtime, p.stat().st_size)
        except OSError:
            return (0, 0)
    return sorted(set(found), key=version_key, reverse=True)


def _flatten_strings(value):
    out = []
    if isinstance(value, str):
        out.append(value)
    elif isinstance(value, list):
        for item in value:
            out.extend(_flatten_strings(item))
    elif isinstance(value, dict):
        for item in value.values():
            out.extend(_flatten_strings(item))
    return out

def _extract_condition_values(condition, keys):
    values = []
    if not isinstance(condition, dict):
        return values
    for key in keys:
        if key in condition:
            values.extend(_flatten_strings(condition.get(key)))
    return [str(v) for v in values]

def normalize_spawn_entry(raw, source_file):
    """Convert a Cobblemon spawn entry into a compact UI-friendly record."""
    if not isinstance(raw, dict):
        return None

    pokemon = raw.get("pokemon") or raw.get("species") or raw.get("id")
    if isinstance(pokemon, dict):
        pokemon = pokemon.get("pokemon") or pokemon.get("species") or pokemon.get("name")
    if not pokemon:
        return None

    pokemon = str(pokemon)
    if ":" in pokemon:
        pokemon = pokemon.split(":", 1)[1]
    # Remove common property syntax such as "pikachu level=5".
    pokemon_name = pokemon.split()[0].strip().replace("_", " ").title()

    cond = raw.get("condition") or {}
    anti = raw.get("anticondition") or {}
    composite = raw.get("compositeCondition") or {}
    if isinstance(composite, dict):
        # Some versions use nested condition structures.
        merged = dict(cond) if isinstance(cond, dict) else {}
        merged.update({k: v for k, v in composite.items() if k not in merged})
        cond = merged

    biomes = _extract_condition_values(cond, ["biomes", "biome", "biomeTags"])
    dimensions = _extract_condition_values(cond, ["dimensions", "dimension"])
    structures = _extract_condition_values(cond, ["structures", "structure"])
    weather = _extract_condition_values(cond, ["weather"])
    blocks = _extract_condition_values(cond, ["neededNearbyBlocks", "blocks", "block"])

    time_range = None
    if isinstance(cond, dict):
        for key in ("timeRange", "time", "skyLight", "moonPhase"):
            if key in cond:
                time_range = cond.get(key)
                break

    level = raw.get("level") or raw.get("levelRange")
    if level is None:
        min_lvl = raw.get("minLevel")
        max_lvl = raw.get("maxLevel")
        if min_lvl is not None or max_lvl is not None:
            level = {"min": min_lvl, "max": max_lvl}

    return {
        "pokemon": pokemon_name,
        "bucket": raw.get("bucket") or raw.get("rarity") or "",
        "weight": raw.get("weight"),
        "level": level,
        "presets": raw.get("presets", []) or [],
        "biomes": biomes,
        "dimensions": dimensions,
        "structures": structures,
        "weather": weather,
        "blocks": blocks,
        "time": time_range,
        "condition": cond,
        "anticondition": anti,
        "source_file": source_file,
    }

def _walk_spawn_json(obj, source_file, out):
    if isinstance(obj, list):
        for item in obj:
            _walk_spawn_json(item, source_file, out)
        return
    if not isinstance(obj, dict):
        return

    # Standard Cobblemon spawn pool files often have "spawns": [...]
    if isinstance(obj.get("spawns"), list):
        for entry in obj["spawns"]:
            norm = normalize_spawn_entry(entry, source_file)
            if norm:
                out.append(norm)

    # Also accept files/structures where entries are directly nested.
    if any(k in obj for k in ("pokemon", "species")):
        norm = normalize_spawn_entry(obj, source_file)
        if norm:
            out.append(norm)

    for key, value in obj.items():
        if key == "spawns":
            continue
        if isinstance(value, (dict, list)):
            _walk_spawn_json(value, source_file, out)

def jar_contains_cobblemon_data(jar_path):
    """True if a mod JAR contains Cobblemon species or spawn datapack resources."""
    try:
        with zipfile.ZipFile(jar_path, "r") as zf:
            for name in zf.namelist():
                low = "/" + name.replace("\\", "/").lower()
                if (
                    low.endswith(".json")
                    and (
                        "/data/cobblemon/species/" in low
                        or "/species_additions/" in low
                        or "/data/cobblemon/spawn_pool_world/" in low
                        or "/data/cobblemon/spawns/" in low
                    )
                ):
                    return True
    except Exception:
        return False
    return False

def discover_cobblemon_data_jars(primary_jar):
    """Find addon/mod JARs next to the selected Cobblemon JAR that contribute data."""
    primary = Path(primary_jar)
    result = []
    seen = set()

    def add(path):
        try:
            p = Path(path)
            key = str(p.resolve())
            if key not in seen and p.exists() and p.is_file():
                seen.add(key)
                result.append(p)
        except Exception:
            pass

    add(primary)

    # Typical CurseForge/Modrinth/Prism layout: selected Cobblemon jar sits in mods/.
    mods_dir = primary.parent
    try:
        for candidate in mods_dir.glob("*.jar"):
            if candidate == primary:
                continue
            # Avoid opening obviously unrelated tiny metadata jars first by only
            # checking regular JAR files in the same mods folder.
            if jar_contains_cobblemon_data(candidate):
                add(candidate)
    except Exception:
        pass

    return result

def import_spawns_from_single_jar(jar_path):
    jar_path = Path(jar_path)
    if not jar_path.exists():
        raise FileNotFoundError(jar_path)

    results = []
    with zipfile.ZipFile(jar_path, "r") as zf:
        candidates = []
        for n in zf.namelist():
            low = n.replace("\\", "/").lower()
            if not low.endswith(".json"):
                continue
            if (
                "data/cobblemon/spawn_pool_world/" in low
                or "data/cobblemon/spawns/" in low
            ):
                candidates.append(n)

        for name in candidates:
            try:
                raw = json.loads(zf.read(name).decode("utf-8-sig"))
            except Exception:
                continue
            _walk_spawn_json(raw, f"{jar_path.name}::{name}", results)

    return results

def merge_spawn_entries(entries):
    """De-duplicate exact repeated spawn rules while retaining addon sources."""
    seen = set()
    unique = []
    for item in entries:
        compare = dict(item)
        # Source location does not define spawn identity.
        compare.pop("source_file", None)
        key = json.dumps(compare, sort_keys=True, default=str)
        if key not in seen:
            seen.add(key)
            unique.append(item)
    return unique

def import_spawns_from_cobblemon_jar(jar_path):
    """Import base Cobblemon spawns plus any addon spawn datapacks in sibling mod JARs."""
    sources = discover_cobblemon_data_jars(jar_path)
    results = []

    for source in sources:
        try:
            results.extend(import_spawns_from_single_jar(source))
        except Exception:
            continue

    return merge_spawn_entries(results)


def save_spawn_data(spawns):
    SPAWN_FILE.write_text(json.dumps(spawns, indent=2, ensure_ascii=False), encoding="utf-8")

def load_spawn_data():
    try:
        if SPAWN_FILE.exists():
            data = json.loads(SPAWN_FILE.read_text(encoding="utf-8"))
            if isinstance(data, list):
                return data
    except Exception:
        pass
    return []

def refresh_spawn_cache_from_jar(jar_path):
    """Refresh spawn data without touching the existing species cache."""
    spawns = import_spawns_from_cobblemon_jar(jar_path)
    save_spawn_data(spawns)
    meta = load_dex_meta()
    meta["source_jar"] = str(jar_path)
    meta["spawn_count"] = len(spawns)
    DEX_META_FILE.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    return spawns

def _sprite_url_for_dex(dex_number):
    # PokeAPI's public sprite repository. Standard front sprites are compact,
    # transparent PNGs and look clean in a desktop Pokédex.
    return f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/{int(dex_number)}.png"

def get_cached_sprite(dex_number):
    """Return/download a clean 2D sprite for a National Dex number."""
    try:
        dex_number = int(dex_number)
    except Exception:
        return None
    if dex_number <= 0:
        return None

    out_path = SPRITE_CACHE_DIR / f"{dex_number:04d}.png"
    if out_path.exists() and out_path.stat().st_size > 100:
        return out_path

    url = _sprite_url_for_dex(dex_number)
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Cobblemon-Companion/0.3.2"}
        )
        with urllib.request.urlopen(req, timeout=4) as response:
            data = response.read()
        if data.startswith(b"\x89PNG") and len(data) > 100:
            out_path.write_bytes(data)
            return out_path
    except Exception:
        return None
    return None



FRIENDLY_TAG_OVERRIDES = {
    "is_hills": "Hills",
    "is_temperate": "Temperate Areas",
    "is_magical": "Magical Biomes",
    "is_overworld": "Overworld",
    "is_mountain": "Mountains",
    "is_snowy_forest": "Snowy Forests",
    "is_taiga": "Taiga",
    "is_swamp": "Swamps",
    "is_nether": "Nether",
    "is_forest": "Forests",
    "is_plains": "Plains",
    "is_desert": "Deserts",
    "is_jungle": "Jungles",
    "is_ocean": "Oceans",
    "is_river": "Rivers",
    "is_beach": "Beaches",
    "is_savanna": "Savannas",
    "is_cave": "Caves",
    "is_deep_dark": "Deep Dark",
    "is_end": "The End",
}

def friendly_resource_name(value):
    """Turn Minecraft/Cobblemon ids and tags into player-friendly text."""
    if value is None:
        return ""
    s = str(value).strip()
    if not s:
        return ""
    if s.startswith("#"):
        s = s[1:]
    if ":" in s:
        namespace, path = s.split(":", 1)
    else:
        namespace, path = "", s
    path = path.strip()
    if path in FRIENDLY_TAG_OVERRIDES:
        return FRIENDLY_TAG_OVERRIDES[path]
    words = path.replace("/", " ").replace("_", " ").replace("-", " ").split()
    pretty = " ".join(w.capitalize() for w in words)
    if path.startswith("is_"):
        pretty = pretty[3:] if pretty.lower().startswith("is ") else pretty
    return pretty or s

def friendly_bucket(value):
    s = str(value or "").strip()
    return s.title() if s else "Unknown"

def friendly_level(value):
    if value in (None, "", [], {}):
        return "Any"
    if isinstance(value, dict):
        mn = value.get("min")
        mx = value.get("max")
        if mn is not None and mx is not None:
            return f"{mn}–{mx}"
        if mn is not None:
            return f"{mn}+"
        if mx is not None:
            return f"≤ {mx}"
    return str(value)

def friendly_time(value):
    if value in (None, "", [], {}):
        return "Any"
    if isinstance(value, str):
        return value.replace("_", " ").title()
    if isinstance(value, list):
        return ", ".join(friendly_time(v) for v in value)
    if isinstance(value, dict):
        parts = []
        for k,v in value.items():
            parts.append(f"{friendly_resource_name(k)}: {v}")
        return ", ".join(parts)
    return str(value)

def spawn_source_info(app, entry):
    raw = str(entry.get("source_file", "") or "")
    jar_name = raw.split("::", 1)[0].strip()
    # Path(...).name on Linux does not split Windows backslashes, so normalize first.
    primary_raw = str(app.dex_meta.get("source_jar", "") or "").replace("\\", "/")
    primary = primary_raw.rsplit("/", 1)[-1]

    if not jar_name:
        return ("unknown", "Unknown source")
    if primary and jar_name.casefold() == primary.casefold():
        return ("base", "Base Cobblemon")
    return ("addon", f"Addon: {jar_name}")

def species_spawn_status(app, pokemon_name):
    entries = species_spawn_entries(app, pokemon_name)
    if entries:
        kinds = {spawn_source_info(app, e)[0] for e in entries}
        if "base" in kinds:
            if "addon" in kinds:
                return ("base+addon", "Base + Addon Natural Spawns")
            return ("base", "Base Cobblemon Natural Spawn")
        if "addon" in kinds:
            return ("addon", "Addon Natural Spawn")
        return ("spawn", "Natural Spawn")

    species = species_by_name(app.pokedex, pokemon_name)
    if species:
        source = str(species.get("data_source", "") or "")
        primary_raw = str(app.dex_meta.get("source_jar", "") or "").replace("\\", "/")
        primary = primary_raw.rsplit("/", 1)[-1]
        if source and primary and source.casefold() != primary.casefold():
            return ("addon-no-spawn", "Addon Species — No Standard Spawn Rule")
        return ("no-spawn", "No Standard Natural Spawn")

    return ("unknown", "No Spawn Data")

def spawn_habitat_labels(entry):
    values = []
    for key in ("biomes", "dimensions", "structures"):
        for v in entry.get(key, []) or []:
            friendly = friendly_resource_name(v)
            if friendly and friendly not in values:
                values.append(friendly)
    return values

def shared_habitats_for_hunts(hunts, spawns):
    """Return habitat -> set of hunted Pokémon that can spawn there."""
    hunt_names = {h.get("pokemon","").strip().lower(): h.get("pokemon","").strip()
                  for h in hunts if h.get("pokemon","").strip()}
    habitats = {}
    for entry in spawns:
        p = entry.get("pokemon","").strip().lower()
        if p not in hunt_names:
            continue
        for habitat in spawn_habitat_labels(entry):
            habitats.setdefault(habitat, set()).add(hunt_names[p])
    ranked = sorted(habitats.items(), key=lambda kv: (-len(kv[1]), kv[0]))
    return ranked


def hunt_intelligence(app):
    """Combine Hunts + weekly Bingo + missing Collection into actionable targets."""
    profile=app.profile
    owned={str(x).strip().casefold() for x in profile.get("living_dex",[]) if str(x).strip()}
    hunt_names={
        str(h.get("pokemon","")).strip().casefold(): str(h.get("pokemon","")).strip()
        for h in profile.get("hunts",[]) if str(h.get("pokemon","")).strip()
    }
    bingo_names={
        str(x.get("pokemon","")).strip().casefold(): str(x.get("pokemon","")).strip()
        for x in profile.get("bingo",[])
        if str(x.get("pokemon","")).strip() and not x.get("caught")
    }

    # Primary targets are things the player explicitly needs right now.
    names={}
    for key,name in hunt_names.items(): names[key]=name
    for key,name in bingo_names.items(): names[key]=name

    spawn_by={}
    for entry in app.spawns or []:
        key=str(entry.get("pokemon","")).strip().casefold()
        if key:
            spawn_by.setdefault(key,[]).append(entry)

    targets=[]
    for key,name in names.items():
        species=species_by_name(app.pokedex,name)
        entries=spawn_by.get(key,[])
        habitats=[]
        times=[]
        weather=[]
        for entry in entries:
            for h in spawn_habitat_labels(entry):
                if h not in habitats: habitats.append(h)
            t=friendly_time(entry.get("time"))
            if t and t not in ("Any time","Unknown","—") and t not in times: times.append(t)
            for w in entry.get("weather",[]) or []:
                fw=friendly_resource_name(w)
                if fw and fw not in weather: weather.append(fw)

        reasons=[]
        score=0
        if key in bingo_names:
            reasons.append("Weekly Bingo"); score+=6
        if key in hunt_names:
            reasons.append("Active Hunt"); score+=5
        if key not in owned:
            reasons.append("Missing from Collection"); score+=3
        if entries:
            score+=2
        if len(habitats)>1:
            score+=1

        snack=pokesnack_recommendation(species)
        targets.append({
            "name":name,
            "species":species,
            "score":score,
            "reasons":reasons,
            "entries":entries,
            "habitats":habitats,
            "times":times,
            "weather":weather,
            "snack":snack,
            "owned":key in owned,
        })

    targets.sort(key=lambda x:(-x["score"],x["name"].casefold()))

    # Group all current targets by shared location.
    habitat_map={}
    for target in targets:
        for habitat in target["habitats"]:
            habitat_map.setdefault(habitat,[]).append(target["name"])
    areas=sorted(
        ((h,sorted(set(mons))) for h,mons in habitat_map.items()),
        key=lambda x:(-len(x[1]),x[0])
    )

    return {"targets":targets,"areas":areas}


def cached_sprite_path(dex_number):
    """Return an already-cached sprite without making a network request."""
    try:
        dex_number = int(dex_number)
    except Exception:
        return None
    path = SPRITE_CACHE_DIR / f"{dex_number:04d}.png"
    if path.exists() and path.stat().st_size > 100:
        return path
    return None

def species_by_name(pokedex, name):
    target = str(name or "").strip().lower()
    for p in pokedex:
        if p.get("name", "").strip().lower() == target:
            return p
    return None



GENERATION_RANGES = [
    (1, 151, 1),
    (152, 251, 2),
    (252, 386, 3),
    (387, 493, 4),
    (494, 649, 5),
    (650, 721, 6),
    (722, 809, 7),
    (810, 905, 8),
    (906, 1025, 9),
]

def generation_for_dex(dex_number):
    try:
        dex_number = int(dex_number)
    except Exception:
        return 0
    for low, high, generation in GENERATION_RANGES:
        if low <= dex_number <= high:
            return generation
    return 0



POKESNACK_TYPE_SEASONINGS = {
    "Bug": "Tanga Berry",
    "Dark": "Colbur Berry",
    "Dragon": "Haban Berry",
    "Electric": "Wacan Berry",
    "Fairy": "Roseli Berry",
    "Fighting": "Chople Berry",
    "Fire": "Occa Berry",
    "Flying": "Coba Berry",
    "Ghost": "Kasib Berry",
    "Grass": "Rindo Berry",
    "Ground": "Shuca Berry",
    "Ice": "Yache Berry",
    "Normal": "Chilan Berry",
    "Poison": "Kebia Berry",
    "Psychic": "Payapa Berry",
    "Rock": "Charti Berry",
    "Steel": "Babiri Berry",
    "Water": "Passho Berry",
}

POKESNACK_EGG_SEASONINGS = {
    "dragon": "Lum Berry",
    "monster": "Lum Berry",
    "water 3": "Pecha Berry",
    "water3": "Pecha Berry",
    "bug": "Pecha Berry",
    "fairy": "Cheri Berry",
    "grass": "Cheri Berry",
    "human-like": "Chesto Berry",
    "human like": "Chesto Berry",
    "humanlike": "Chesto Berry",
    "flying": "Chesto Berry",
    "field": "Rawst Berry",
    "water 1": "Aspear Berry",
    "water1": "Aspear Berry",
    "water 2": "Aspear Berry",
    "water2": "Aspear Berry",
    "mineral": "Persim Berry",
    "amorphous": "Persim Berry",
}

POKESNACK_UTILITY = [
    ("Golden Carrot", "Raises the rarity bucket by 1 tier"),
    ("Glistering Melon Slice", "Raises the rarity bucket by 1 tier"),
    ("Starf Berry", "5× shiny chance"),
    ("Enigma Berry", "5% chance to attract a Hidden Ability Pokémon"),
    ("Leppa Berry", "+5 levels"),
    ("Hopo Berry", "+10 levels"),
]

def normalize_egg_group_name(value):
    s = str(value or "").strip().lower().replace("_", " ")
    s = re.sub(r"\\s+", " ", s)
    return s


def pokesnack_recommendation(species):
    """Return target-specific Bait Seasonings for a species.

    Type and Egg Group matches are deliberately presented as independent
    10x targeting options. We do not claim that duplicate/multiple boosts
    multiply together because that is not needed for the companion UI.
    """
    if not species:
        return {"targeting": [], "combo": [], "utility": POKESNACK_UTILITY[:3]}

    targeting = []
    seen = set()

    # Type-targeting seasonings.
    for ptype in species.get("types", []) or []:
        berry = POKESNACK_TYPE_SEASONINGS.get(ptype)
        if berry and berry not in seen:
            targeting.append((berry, f"10× attraction for {ptype}-type Pokémon"))
            seen.add(berry)

    # Egg-group-targeting seasonings.
    for egg in species.get("egg_groups", []) or []:
        normalized = normalize_egg_group_name(egg)
        berry = POKESNACK_EGG_SEASONINGS.get(normalized)
        if berry and berry not in seen:
            pretty = friendly_resource_name(egg)
            targeting.append((berry, f"10× attraction for the {pretty} Egg Group"))
            seen.add(berry)

    # Poké Snack has three Bait Seasoning positions in its cooking recipe.
    # Fill target-specific slots first; remaining slots can use utility effects.
    combo = list(targeting[:3])
    used = {x[0] for x in combo}
    for utility in POKESNACK_UTILITY:
        if len(combo) >= 3:
            break
        if utility[0] not in used:
            combo.append(utility)
            used.add(utility[0])

    return {
        "targeting": targeting,
        "combo": combo,
        "utility": POKESNACK_UTILITY,
    }


TEAM_NATURES = ["Hardy","Lonely","Brave","Adamant","Naughty","Bold","Docile","Relaxed","Impish","Lax",
"Timid","Hasty","Serious","Jolly","Naive","Modest","Mild","Quiet","Bashful","Rash","Calm","Gentle","Sassy","Careful","Quirky"]
TEAM_STATS = ["HP","Atk","Def","SpA","SpD","Spe"]
TYPE_EFFECTIVENESS = {
"Normal":{"Rock":.5,"Ghost":0,"Steel":.5},"Fire":{"Fire":.5,"Water":.5,"Grass":2,"Ice":2,"Bug":2,"Rock":.5,"Dragon":.5,"Steel":2},
"Water":{"Fire":2,"Water":.5,"Grass":.5,"Ground":2,"Rock":2,"Dragon":.5},"Electric":{"Water":2,"Electric":.5,"Grass":.5,"Ground":0,"Flying":2,"Dragon":.5},
"Grass":{"Fire":.5,"Water":2,"Grass":.5,"Poison":.5,"Ground":2,"Flying":.5,"Bug":.5,"Rock":2,"Dragon":.5,"Steel":.5},
"Ice":{"Fire":.5,"Water":.5,"Grass":2,"Ice":.5,"Ground":2,"Flying":2,"Dragon":2,"Steel":.5},
"Fighting":{"Normal":2,"Ice":2,"Poison":.5,"Flying":.5,"Psychic":.5,"Bug":.5,"Rock":2,"Ghost":0,"Dark":2,"Steel":2,"Fairy":.5},
"Poison":{"Grass":2,"Poison":.5,"Ground":.5,"Rock":.5,"Ghost":.5,"Steel":0,"Fairy":2},
"Ground":{"Fire":2,"Electric":2,"Grass":.5,"Poison":2,"Flying":0,"Bug":.5,"Rock":2,"Steel":2},
"Flying":{"Electric":.5,"Grass":2,"Fighting":2,"Bug":2,"Rock":.5,"Steel":.5},
"Psychic":{"Fighting":2,"Poison":2,"Psychic":.5,"Dark":0,"Steel":.5},
"Bug":{"Fire":.5,"Grass":2,"Fighting":.5,"Poison":.5,"Flying":.5,"Psychic":2,"Ghost":.5,"Dark":2,"Steel":.5,"Fairy":.5},
"Rock":{"Fire":2,"Ice":2,"Fighting":.5,"Ground":.5,"Flying":2,"Bug":2,"Steel":.5},
"Ghost":{"Normal":0,"Psychic":2,"Ghost":2,"Dark":.5},"Dragon":{"Dragon":2,"Steel":.5,"Fairy":0},
"Dark":{"Fighting":.5,"Psychic":2,"Ghost":2,"Dark":.5,"Fairy":.5},
"Steel":{"Fire":.5,"Water":.5,"Electric":.5,"Ice":2,"Rock":2,"Steel":.5,"Fairy":2},
"Fairy":{"Fire":.5,"Fighting":2,"Poison":.5,"Dragon":2,"Dark":2,"Steel":.5}}
def blank_team_member():
    return {"pokemon":"","ability":"","nature":"","item":"","moves":["","","",""],"evs":{s:0 for s in TEAM_STATS}}
def blank_team(name="New Team"):
    return {"name":name,"members":[blank_team_member() for _ in range(6)]}
def normalize_team_member(m):
    m=m if isinstance(m,dict) else {}; o=blank_team_member()
    for k in ("pokemon","ability","nature","item"): o[k]=str(m.get(k,"") or "")
    moves=m.get("moves",[]) if isinstance(m.get("moves",[]),list) else []
    o["moves"]=[str(x or "") for x in moves[:4]]+[""]*max(0,4-len(moves[:4]))
    evs=m.get("evs",{}) if isinstance(m.get("evs",{}),dict) else {}
    for s in TEAM_STATS:
        try:o["evs"][s]=max(0,min(252,int(evs.get(s,0) or 0)))
        except:o["evs"][s]=0
    return o
def defensive_multiplier(atk, defender_types):
    m=1.0
    for d in defender_types or []: m*=TYPE_EFFECTIVENESS.get(atk,{}).get(d,1.0)
    return m
def team_defensive_summary(members,pokedex):
    species=[species_by_name(pokedex,m.get("pokemon","")) for m in members]
    species=[s for s in species if s]
    out={}
    for atk in TYPE_EFFECTIVENESS:
        d={"weak":0,"resist":0,"immune":0}
        for s in species:
            mult=defensive_multiplier(atk,s.get("types",[]))
            if mult==0:d["immune"]+=1
            elif mult>1:d["weak"]+=1
            elif mult<1:d["resist"]+=1
        out[atk]=d
    return out
def clean_team_id(v):
    s=str(v or "").strip()
    hidden=s.startswith("h:")
    if hidden:s=s[2:]
    if ":" in s:s=s.split(":",1)[1]
    return friendly_resource_name(s),hidden
def species_ability_options(species):
    out=[]
    for raw in (species or {}).get("abilities",[]) or []:
        pretty,hidden=clean_team_id(raw)
        if pretty:out.append(pretty+(" (Hidden)" if hidden else ""))
    return out
def species_move_options(species):
    out = set()
    for raw in (species or {}).get("moves", []) or []:
        if isinstance(raw, dict):
            candidate = raw.get("move") or raw.get("id") or raw.get("name") or ""
        else:
            candidate = str(raw)
        s = str(candidate or "").strip()
        if not s:
            continue
        move_id = s.rsplit(":", 1)[-1]
        pretty = friendly_resource_name(move_id)
        if pretty:
            out.add(pretty)
    return sorted(out)




MEGA_STONES = {
    "Abomasite", "Absolite", "Aerodactylite", "Aggronite", "Alakazite",
    "Altarianite", "Ampharosite", "Audinite", "Banettite", "Beedrillite",
    "Blastoisinite", "Blazikenite", "Cameruptite", "Charizardite X",
    "Charizardite Y", "Diancite", "Galladite", "Garchompite", "Gardevoirite",
    "Gengarite", "Glalitite", "Gyaradosite", "Heracronite", "Houndoominite",
    "Kangaskhanite", "Latiasite", "Latiosite", "Lopunnite", "Lucarionite",
    "Manectite", "Mawilite", "Medichamite", "Metagrossite", "Mewtwonite X",
    "Mewtwonite Y", "Pidgeotite", "Pinsirite", "Sablenite", "Salamencite",
    "Sceptilite", "Scizorite", "Sharpedonite", "Slowbronite", "Steelixite",
    "Swampertite", "Tyranitarite", "Venusaurite"
}

def is_mega_stone_entry(entry):
    """Recognize Mega Stones even when Cobblemon doesn't categorize them as held items."""
    if not isinstance(entry, dict):
        return False

    name = str(entry.get("name", "") or "").strip()
    item_id = str(entry.get("id", "") or "").strip().lower()
    category = str(entry.get("category", "") or "").strip().lower()

    if name in MEGA_STONES:
        return True
    if "mega" in category and "stone" in category:
        return True
    if "mega_stone" in item_id or "megastone" in item_id:
        return True

    # Exact normalized fallback against the known Mega Stone names.
    normalized_name = re.sub(r"[^a-z0-9]+", "", name.lower())
    normalized_id = re.sub(r"[^a-z0-9]+", "", item_id.lower())
    known = {
        re.sub(r"[^a-z0-9]+", "", stone.lower())
        for stone in MEGA_STONES
    }
    return normalized_name in known or normalized_id in known

HELD_ITEM_EFFECTS = {
    "Choice Band": {"Atk": 1.5, "note": "Attack ×1.5; usually locks the holder into its first selected move."},
    "Choice Specs": {"SpA": 1.5, "note": "Sp. Atk ×1.5; usually locks the holder into its first selected move."},
    "Choice Scarf": {"Spe": 1.5, "note": "Speed ×1.5; usually locks the holder into its first selected move."},
    "Assault Vest": {"SpD": 1.5, "note": "Sp. Def ×1.5; status moves cannot normally be selected."},
    "Eviolite": {"Def": 1.5, "SpD": 1.5, "note": "Defense and Sp. Def ×1.5 when the holder can still evolve."},
    "Life Orb": {"note": "Damaging moves are boosted, at the cost of recoil after attacking."},
    "Expert Belt": {"note": "Boosts super-effective attacks."},
    "Muscle Band": {"note": "Boosts physical attacks."},
    "Wise Glasses": {"note": "Boosts special attacks."},
    "Focus Sash": {"note": "Can let a full-HP holder survive one otherwise-fatal hit."},
    "Leftovers": {"note": "Restores a small amount of HP each turn."},
    "Black Sludge": {"note": "Restores HP for Poison-types; normally harms non-Poison holders."},
    "Heavy-Duty Boots": {"note": "Prevents entry-hazard damage/effects when switching in."},
    "Rocky Helmet": {"note": "Damages opponents that make contact."},
    "Weakness Policy": {"note": "Raises offensive stats after being hit super effectively."},
    "Light Clay": {"note": "Extends Reflect / Light Screen / Aurora Veil duration."},
    "Loaded Dice": {"note": "Improves the consistency of multi-hit moves."},
    "Covert Cloak": {"note": "Blocks many secondary effects from damaging moves."},
    "Clear Amulet": {"note": "Prevents the holder's stats from being lowered by opponents."},
    "Booster Energy": {"note": "Activates certain Paradox Pokémon abilities without terrain/weather support."},
}

def held_item_options(app):
    """Return held-item candidates, including all Mega Stones."""
    items = []

    for entry in getattr(app, "item_index", []) or []:
        name = str(entry.get("name", "") or "").strip()
        category = str(entry.get("category", "") or "").strip().lower()

        if not name:
            continue

        if category in ("held items", "held item") or is_mega_stone_entry(entry):
            items.append(name)

    # Competitive staples + complete Mega Stone fallback list.
    items.extend(HELD_ITEM_EFFECTS.keys())
    items.extend(MEGA_STONES)

    return sorted(dict.fromkeys(items))


def held_item_effect(item_name):
    name = str(item_name or "").strip()
    if name in MEGA_STONES:
        return {
            "note": "Mega Stone — enables the matching Pokémon to Mega Evolve when the server/modpack supports Mega Evolution."
        }
    return HELD_ITEM_EFFECTS.get(name, {})

def held_item_stat_preview(species, member):
    """Base-stat comparison after known multiplicative held-item effects.

    This intentionally avoids pretending to be a full battle-stat calculator;
    it shows how known held-item multipliers affect the Pokémon's imported base
    stat profile.
    """
    if not species:
        return {}

    values = {
        "HP": int(species.get("hp", 0) or 0),
        "Atk": int(species.get("atk", 0) or 0),
        "Def": int(species.get("def", 0) or 0),
        "SpA": int(species.get("spa", 0) or 0),
        "SpD": int(species.get("spd", 0) or 0),
        "Spe": int(species.get("spe", 0) or 0),
    }
    effect = held_item_effect((member or {}).get("item", ""))
    preview = {}
    for stat, base in values.items():
        mult = float(effect.get(stat, 1.0) or 1.0)
        preview[stat] = {
            "base": base,
            "multiplier": mult,
            "effective": round(base * mult, 1),
        }
    return preview


class HeldItemPicker(tk.Toplevel):
    """Searchable held-item selector backed by Companion's imported item catalog."""

    def __init__(self, app, current, callback):
        super().__init__(app)
        self.app = app
        self.callback = callback
        self.items = held_item_options(app)
        self.filtered = []

        self.title("Choose Held Item")
        self.configure(bg=BG)
        self.geometry("520x560")
        self.minsize(460, 440)
        self.transient(app)
        self.grab_set()

        tk.Label(
            self, text="Choose Held Item",
            bg=BG, fg=TEXT,
            font=("Segoe UI Semibold", 17)
        ).pack(anchor="w", padx=18, pady=(18,4))

        tk.Label(
            self,
            text="Search held items imported from your installed Cobblemon data.",
            bg=BG, fg=MUTED, font=("Segoe UI",9)
        ).pack(anchor="w", padx=18, pady=(0,10))

        self.query = tk.StringVar(value=current or "")
        entry = tk.Entry(
            self, textvariable=self.query,
            bg=PANEL, fg=TEXT, insertbackground=TEXT,
            relief="flat", font=("Segoe UI",11)
        )
        entry.pack(fill="x", padx=18, ipady=8)
        entry.focus_set()
        entry.select_range(0, "end")
        entry.bind("<KeyRelease>", lambda e:self.refresh_list())

        body = tk.Frame(self, bg=BG)
        body.pack(fill="both", expand=True, padx=18, pady=10)

        self.listbox = tk.Listbox(
            body, bg=PANEL, fg=TEXT,
            selectbackground=ACCENT_2, selectforeground="white",
            relief="flat", bd=0, highlightthickness=0,
            font=("Segoe UI",10)
        )
        scroll = tk.Scrollbar(body, orient="vertical", command=self.listbox.yview)
        self.listbox.configure(yscrollcommand=scroll.set)
        self.listbox.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        self.listbox.bind("<Double-Button-1>", lambda e:self.choose())
        self.listbox.bind("<Return>", lambda e:self.choose())

        self.status = tk.Label(self, text="", bg=BG, fg=MUTED, font=("Segoe UI",9))
        self.status.pack(anchor="w", padx=18, pady=(0,8))

        buttons = tk.Frame(self, bg=BG)
        buttons.pack(fill="x", padx=18, pady=(0,18))

        tk.Button(
            buttons, text="Clear Item",
            command=lambda:self.submit(""),
            bg=PANEL_2, fg=TEXT, relief="flat",
            padx=12, pady=8
        ).pack(side="left")

        tk.Button(
            buttons, text="Cancel",
            command=self.destroy,
            bg=PANEL_2, fg=TEXT, relief="flat",
            padx=12, pady=8
        ).pack(side="right")

        tk.Button(
            buttons, text="Choose Item",
            command=self.choose,
            bg=ACCENT_2, fg="white", relief="flat",
            padx=14, pady=8
        ).pack(side="right", padx=(0,8))

        self.refresh_list()

    def refresh_list(self):
        q = self.query.get().strip().lower()
        self.filtered = [x for x in self.items if q in x.lower()] if q else list(self.items)
        self.listbox.delete(0, "end")
        for name in self.filtered:
            self.listbox.insert("end", name)
        self.status.config(text=f"{len(self.filtered)} held item{'s' if len(self.filtered) != 1 else ''} match")
        if self.filtered:
            self.listbox.selection_set(0)

    def choose(self):
        sel = self.listbox.curselection()
        if not sel:
            return
        idx = sel[0]
        if idx < len(self.filtered):
            self.submit(self.filtered[idx])

    def submit(self, value):
        self.callback(value)
        self.destroy()


UTILITY_MOVE_GROUPS = {
    "Hazards": {"Stealth Rock","Spikes","Toxic Spikes","Sticky Web","Stone Axe","Ceaseless Edge"},
    "Hazard Removal": {"Rapid Spin","Defog","Mortal Spin","Tidy Up","Court Change"},
    "Recovery": {"Recover","Roost","Slack Off","Soft Boiled","Softboiled","Milk Drink","Moonlight","Morning Sun",
                 "Synthesis","Shore Up","Strength Sap","Wish","Rest","Life Dew","Jungle Healing","Heal Order"},
    "Pivoting": {"U Turn","U-Turn","Volt Switch","Flip Turn","Parting Shot","Baton Pass","Teleport","Chilly Reception"},
    "Priority": {"Aqua Jet","Bullet Punch","Extreme Speed","Extremespeed","Fake Out","First Impression","Ice Shard",
                 "Mach Punch","Quick Attack","Shadow Sneak","Sucker Punch","Vacuum Wave","Water Shuriken",
                 "Grassy Glide","Thunderclap","Jet Punch"},
    "Physical Setup": {"Swords Dance","Dragon Dance","Bulk Up","Coil","Belly Drum","Shell Smash","Victory Dance",
                       "Howl","Curse","Shift Gear","Tidy Up"},
    "Special Setup": {"Nasty Plot","Calm Mind","Quiver Dance","Tail Glow","Geomancy","Shell Smash","Torch Song"},
    "Speed Control": {"Thunder Wave","Glare","Icy Wind","Electroweb","Rock Tomb","Bulldoze","Tailwind","Trick Room",
                      "Sticky Web","Scary Face","String Shot"},
    "Screens": {"Reflect","Light Screen","Aurora Veil"},
    "Status": {"Will O Wisp","Will-O-Wisp","Toxic","Thunder Wave","Glare","Spore","Sleep Powder","Hypnosis",
               "Stun Spore","Nuzzle","Yawn"},
    "Weather": {"Rain Dance","Sunny Day","Sandstorm","Snowscape","Hail"},
    "Terrain": {"Electric Terrain","Grassy Terrain","Misty Terrain","Psychic Terrain"},
    "Trick Room": {"Trick Room"},
    "Cleric": {"Heal Bell","Aromatherapy","Healing Wish","Lunar Dance","Wish"},
    "Phazing": {"Roar","Whirlwind","Dragon Tail","Circle Throw"},
    "Knock / Item Control": {"Knock Off","Trick","Switcheroo","Corrosive Gas"},
}

def move_cache_load():
    try:
        if MOVE_META_FILE.exists():
            data = json.loads(MOVE_META_FILE.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return data
    except Exception:
        pass
    return {}

def move_cache_save(data):
    try:
        MOVE_META_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass

def move_slug(name):
    s = str(name or "").strip().lower()
    s = s.replace("’", "").replace("'", "")
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s


# Cobblemon learnsets commonly use compact resource IDs (fakeout, icebeam,
# highhorsepower, etc.). PokeAPI uses hyphenated canonical slugs.
# This map covers common ambiguous/compact IDs immediately; the resolver also
# learns the complete canonical move list from PokeAPI on first refresh.
MOVE_SLUG_ALIASES = {
    "fakeout": "fake-out",
    "flareblitz": "flare-blitz",
    "grassyglide": "grassy-glide",
    "highhorsepower": "high-horsepower",
    "icebeam": "ice-beam",
    "icepunch": "ice-punch",
    "icywind": "icy-wind",
    "knockoff": "knock-off",
    "meteormash": "meteor-mash",
    "partingshot": "parting-shot",
    "pollenpuff": "pollen-puff",
    "ragepowder": "rage-powder",
    "thunderwave": "thunder-wave",
    "woodhammer": "wood-hammer",
    "airslash": "air-slash",
    "hydropump": "hydro-pump",
    "leafstorm": "leaf-storm",
    "voltswitch": "volt-switch",
    "uturn": "u-turn",
    "willowisp": "will-o-wisp",
    "stealthrock": "stealth-rock",
    "rapidspin": "rapid-spin",
    "suckerpunch": "sucker-punch",
    "bulletpunch": "bullet-punch",
    "extremespeed": "extreme-speed",
    "quickattack": "quick-attack",
    "shadowball": "shadow-ball",
    "shadowclaw": "shadow-claw",
    "earthpower": "earth-power",
    "earthquake": "earthquake",
    "dracometeor": "draco-meteor",
    "dragonclaw": "dragon-claw",
    "dragondance": "dragon-dance",
    "swordsdance": "swords-dance",
    "nastyplot": "nasty-plot",
    "calmmind": "calm-mind",
    "closecombat": "close-combat",
    "ironhead": "iron-head",
    "flashcannon": "flash-cannon",
    "powergem": "power-gem",
    "energyball": "energy-ball",
    "gigadrain": "giga-drain",
    "sludgebomb": "sludge-bomb",
    "sludgewave": "sludge-wave",
    "psychicfangs": "psychic-fangs",
    "playrough": "play-rough",
    "moonblast": "moonblast",
    "dazzlinggleam": "dazzling-gleam",
    "fireblast": "fire-blast",
    "flamethrower": "flamethrower",
    "thunderbolt": "thunderbolt",
    "thunderpunch": "thunder-punch",
    "wildcharge": "wild-charge",
    "stoneedge": "stone-edge",
    "rockslide": "rock-slide",
    "rockblast": "rock-blast",
    "bodypress": "body-press",
    "body slam": "body-slam",
    "bodyslam": "body-slam",
    "drainpunch": "drain-punch",
    "machpunch": "mach-punch",
    "focusblast": "focus-blast",
    "focuspunch": "focus-punch",
    "firstimpression": "first-impression",
    "aquajet": "aqua-jet",
    "liquidation": "liquidation",
    "scald": "scald",
    "surf": "surf",
    "waterfall": "waterfall",
    "flipturn": "flip-turn",
    "hurricane": "hurricane",
    "bravebird": "brave-bird",
    "dualwingbeat": "dual-wingbeat",
    "roost": "roost",
    "recover": "recover",
    "softboiled": "soft-boiled",
    "slackoff": "slack-off",
    "morning sun": "morning-sun",
    "morningsun": "morning-sun",
    "trickroom": "trick-room",
    "tailwind": "tailwind",
    "lightscreen": "light-screen",
    "reflect": "reflect",
    "auroraveil": "aurora-veil",
    "toxicspikes": "toxic-spikes",
    "stickyweb": "sticky-web",
    "partingshot": "parting-shot",
    "heavyslam": "heavy-slam",
    "gyroball": "gyro-ball",
    "meteorbeam": "meteor-beam",
}

_MOVE_CANONICAL_INDEX = None

def normalized_move_key(value):
    return re.sub(r"[^a-z0-9]+", "", str(value or "").lower())

def load_or_fetch_move_slug_index(allow_network=True):
    """Map alphanumeric-normalized move names to canonical PokeAPI slugs."""
    global _MOVE_CANONICAL_INDEX
    if isinstance(_MOVE_CANONICAL_INDEX, dict):
        return _MOVE_CANONICAL_INDEX

    cache = move_cache_load()
    saved = cache.get("__slug_index__")
    if isinstance(saved, dict) and saved:
        _MOVE_CANONICAL_INDEX = saved
        return saved

    index = {}
    for compact, slug in MOVE_SLUG_ALIASES.items():
        index[normalized_move_key(compact)] = slug

    if allow_network:
        try:
            req = urllib.request.Request(
                "https://pokeapi.co/api/v2/move?limit=2000",
                headers={"User-Agent": "Cobblemon-Companion/1.3.0"}
            )
            with urllib.request.urlopen(req, timeout=8) as response:
                raw = json.loads(response.read().decode("utf-8"))
            for entry in raw.get("results", []) or []:
                slug = str(entry.get("name","") or "").strip()
                if slug:
                    index[normalized_move_key(slug)] = slug

            cache["__slug_index__"] = index
            move_cache_save(cache)
        except Exception:
            pass

    _MOVE_CANONICAL_INDEX = index
    return index

def canonical_move_slug(move_name, allow_network=True):
    raw = str(move_name or "").strip()
    if not raw:
        return ""

    norm = normalized_move_key(raw)
    alias = MOVE_SLUG_ALIASES.get(norm)
    if alias:
        return alias

    index = load_or_fetch_move_slug_index(allow_network=allow_network)
    if norm in index:
        return index[norm]

    # Normal display names with spaces usually convert correctly.
    return move_slug(raw)

def get_move_metadata(move_name, allow_network=True):
    """Return cached move metadata, resolving compact Cobblemon IDs correctly."""
    name = str(move_name or "").strip()
    if not name:
        return None

    cache = move_cache_load()
    key = name.lower()

    if key in cache and isinstance(cache[key], dict):
        return cache[key]

    if not allow_network:
        return None

    slug = canonical_move_slug(name, allow_network=True)
    if not slug:
        return None

    try:
        url = f"https://pokeapi.co/api/v2/move/{slug}"
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Cobblemon-Companion/1.3.0"}
        )
        with urllib.request.urlopen(req, timeout=6) as response:
            raw = json.loads(response.read().decode("utf-8"))

        meta = {
            "name": friendly_resource_name(raw.get("name", name)),
            "type": friendly_resource_name((raw.get("type") or {}).get("name", "")),
            "category": friendly_resource_name((raw.get("damage_class") or {}).get("name", "")),
            "power": raw.get("power"),
            "accuracy": raw.get("accuracy"),
            "priority": raw.get("priority", 0),
            "slug": slug,
        }

        # Cache under both the Companion display spelling and canonical pretty name.
        cache[key] = meta
        canonical_name = str(meta.get("name","") or "").lower()
        if canonical_name:
            cache[canonical_name] = meta
        move_cache_save(cache)
        return meta
    except Exception:
        return None


def selected_move_metadata(members, allow_network=False):
    result = {}
    for member in members:
        for move in member.get("moves", []) or []:
            move = str(move or "").strip()
            if move and move.lower() not in result:
                result[move.lower()] = get_move_metadata(move, allow_network=allow_network)
    return result

def offensive_coverage(members, move_meta):
    coverage = {t: 0 for t in TYPE_EFFECTIVENESS}
    damaging_types = set()
    physical = special = status = 0
    for member in members:
        for move in member.get("moves", []) or []:
            move = str(move or "").strip()
            if not move:
                continue
            meta = move_meta.get(move.lower())
            if not meta:
                continue
            category = meta.get("category", "")
            if category == "Physical":
                physical += 1
            elif category == "Special":
                special += 1
            else:
                status += 1
            mtype = meta.get("type")
            if category in ("Physical","Special") and mtype in TYPE_EFFECTIVENESS:
                damaging_types.add(mtype)
                for defender in coverage:
                    if TYPE_EFFECTIVENESS.get(mtype, {}).get(defender, 1) > 1:
                        coverage[defender] += 1
    return coverage, damaging_types, physical, special, status

def utility_summary(members):
    chosen = {str(m or "").strip() for member in members for m in member.get("moves", []) or [] if str(m or "").strip()}
    result = {}
    for group, moves in UTILITY_MOVE_GROUPS.items():
        hits = sorted(chosen.intersection(moves))
        result[group] = hits
    return result

def pokemon_role(species, member, move_meta):
    if not species:
        return "Empty"
    atk, spa, spe = species.get("atk",0), species.get("spa",0), species.get("spe",0)
    hp, de, sd = species.get("hp",0), species.get("def",0), species.get("spd",0)
    moves = [move_meta.get(str(m).lower()) for m in member.get("moves",[]) if m]
    phys = sum(1 for x in moves if x and x.get("category")=="Physical")
    spec = sum(1 for x in moves if x and x.get("category")=="Special")
    setup = any(str(m) in UTILITY_MOVE_GROUPS["Physical Setup"]|UTILITY_MOVE_GROUPS["Special Setup"] for m in member.get("moves",[]))
    recovery = any(str(m) in UTILITY_MOVE_GROUPS["Recovery"] for m in member.get("moves",[]))
    if recovery and (hp + de + sd) >= 250:
        return "Bulky / Defensive"
    if setup and spe >= 80:
        return "Setup Sweeper"
    if phys > spec and atk >= spa:
        return "Physical Attacker"
    if spec > phys and spa >= atk:
        return "Special Attacker"
    if max(atk, spa) >= 110 and spe >= 90:
        return "Fast Attacker"
    if hp + de + sd >= 260:
        return "Bulky"
    return "Balanced"

def nature_effects(name):
    # +stat, -stat for non-neutral natures.
    mapping = {
        "Lonely":("Atk","Def"),"Brave":("Atk","Spe"),"Adamant":("Atk","SpA"),"Naughty":("Atk","SpD"),
        "Bold":("Def","Atk"),"Relaxed":("Def","Spe"),"Impish":("Def","SpA"),"Lax":("Def","SpD"),
        "Timid":("Spe","Atk"),"Hasty":("Spe","Def"),"Jolly":("Spe","SpA"),"Naive":("Spe","SpD"),
        "Modest":("SpA","Atk"),"Mild":("SpA","Def"),"Quiet":("SpA","Spe"),"Rash":("SpA","SpD"),
        "Calm":("SpD","Atk"),"Gentle":("SpD","Def"),"Sassy":("SpD","Spe"),"Careful":("SpD","SpA")
    }
    return mapping.get(name)

def analyze_team(members, pokedex, move_meta):
    populated = [(normalize_team_member(m), species_by_name(pokedex, m.get("pokemon",""))) for m in members]
    populated = [(m,s) for m,s in populated if s]
    issues, strengths = [], []
    defense = team_defensive_summary([m for m,s in populated], pokedex)
    offense, damaging_types, physical, special, status = offensive_coverage([m for m,s in populated], move_meta)
    utility = utility_summary([m for m,s in populated])

    if len(populated) < 6:
        issues.append(f"Team is incomplete ({len(populated)}/6 Pokémon).")
    names = [s.get("name","").lower() for m,s in populated]
    if len(names) != len(set(names)):
        issues.append("Duplicate species detected.")

    stacked = sorted([(t,d["weak"]) for t,d in defense.items() if d["weak"] >= 3], key=lambda x:-x[1])
    for t,c in stacked[:5]:
        issues.append(f"{c} team members are weak to {t}.")
    if not stacked and populated:
        strengths.append("No attacking type hits 3+ team members super effectively.")

    uncovered = [t for t,c in offense.items() if c == 0]
    if len(uncovered) >= 6:
        issues.append("Offensive coverage misses many types: " + ", ".join(uncovered[:8]) + ("…" if len(uncovered)>8 else ""))
    elif uncovered:
        issues.append("No super-effective move coverage for: " + ", ".join(uncovered))
    else:
        strengths.append("Selected damaging moves can hit all 18 types super effectively.")

    if physical == 0 and special > 0:
        issues.append("No selected physical attacks; special walls may be difficult to break.")
    if special == 0 and physical > 0:
        issues.append("No selected special attacks; physical walls may be difficult to break.")
    if physical and special:
        strengths.append(f"Mixed offense present ({physical} physical / {special} special damaging moves).")

    for need in ("Hazards","Hazard Removal","Recovery","Pivoting","Priority","Speed Control"):
        if not utility.get(need):
            issues.append(f"No {need.lower()} option selected.")
    if utility.get("Hazards") and utility.get("Hazard Removal"):
        strengths.append("Team has both entry hazards and hazard removal.")
    if utility.get("Pivoting"):
        strengths.append("Pivoting support is present.")
    if utility.get("Priority"):
        strengths.append("Priority move support is present.")

    for m,s in populated:
        chosen = [x for x in m.get("moves",[]) if x]
        metas = [move_meta.get(x.lower()) for x in chosen]
        damaging = [x for x in metas if x and x.get("category") in ("Physical","Special")]
        if chosen and not damaging:
            issues.append(f"{s['name']} currently has no recognized damaging move.")
        if damaging and not any(x.get("type") in s.get("types",[]) for x in damaging):
            issues.append(f"{s['name']} has no selected STAB damaging move.")
        evtotal = sum(m.get("evs",{}).values())
        if evtotal and evtotal < 500:
            issues.append(f"{s['name']} uses only {evtotal}/510 EVs.")
        item = m.get("item","")
        effect = held_item_effect(item)
        if item == "Assault Vest" and any(
            meta and meta.get("category") not in ("Physical","Special")
            for meta in metas
        ):
            issues.append(f"{s['name']} has Assault Vest but also has a selected status move.")
        if item == "Choice Band" and special > 0 and not any(
            meta and meta.get("category") == "Physical" for meta in metas
        ):
            issues.append(f"{s['name']} has Choice Band but no recognized physical attack selected.")
        if item == "Choice Specs" and physical > 0 and not any(
            meta and meta.get("category") == "Special" for meta in metas
        ):
            issues.append(f"{s['name']} has Choice Specs but no recognized special attack selected.")
        if item == "Eviolite" and not (s.get("evolutions") or []):
            issues.append(f"{s['name']} has Eviolite but no outgoing evolution is recorded in the imported species data.")

        nat = nature_effects(m.get("nature",""))
        if nat:
            plus, minus = nat
            # flag obvious nature mismatch for pure physical/special sets.
            pcount = sum(1 for x in damaging if x.get("category")=="Physical")
            scount = sum(1 for x in damaging if x.get("category")=="Special")
            if pcount and not scount and minus=="Atk":
                issues.append(f"{s['name']}'s {m['nature']} nature lowers Attack on a physical set.")
            if scount and not pcount and minus=="SpA":
                issues.append(f"{s['name']}'s {m['nature']} nature lowers Sp. Atk on a special set.")

    stats = {}
    if populated:
        for label,key in [("HP","hp"),("Attack","atk"),("Defense","def"),("Sp. Atk","spa"),("Sp. Def","spd"),("Speed","spe")]:
            vals=[s.get(key,0) for m,s in populated]
            stats[label]={"avg":round(sum(vals)/len(vals),1),"max":max(vals),"min":min(vals)}
    roles=[(s["name"],pokemon_role(s,m,move_meta)) for m,s in populated]

    return {
        "issues": issues, "strengths": strengths, "defense": defense, "offense": offense,
        "damaging_types": damaging_types, "physical": physical, "special": special, "status": status,
        "utility": utility, "stats": stats, "roles": roles,
    }


def species_defensive_profile(species):
    result = {"weak": [], "resist": [], "immune": []}
    if not species:
        return result
    types = species.get("types", []) or []
    for attacking_type in TYPE_EFFECTIVENESS:
        mult = defensive_multiplier(attacking_type, types)
        if mult == 0:
            result["immune"].append(attacking_type)
        elif mult > 1:
            result["weak"].append((attacking_type, mult))
        elif mult < 1:
            result["resist"].append((attacking_type, mult))
    return result

def species_bst(species):
    if not species:
        return 0
    return sum(int(species.get(k, 0) or 0) for k in ("hp","atk","def","spa","spd","spe"))

def species_spawn_entries(app, pokemon_name):
    target = str(pokemon_name or "").strip().lower()
    return [x for x in (app.spawns or []) if x.get("pokemon","").strip().lower() == target]

def species_user_status(app, pokemon_name):
    key = str(pokemon_name or "").strip().lower()
    owned = key in {str(x).strip().lower() for x in app.profile.get("living_dex", [])}
    hunted = any(str(x.get("pokemon","")).strip().lower() == key for x in app.profile.get("hunts", []))
    bingo = any(
        str(x.get("pokemon","")).strip().lower() == key and not x.get("caught", False)
        for x in app.profile.get("bingo", [])
    )
    bingo_caught = any(
        str(x.get("pokemon","")).strip().lower() == key and x.get("caught", False)
        for x in app.profile.get("bingo", [])
    )
    return {"owned": owned, "hunted": hunted, "bingo": bingo, "bingo_caught": bingo_caught}

def pretty_evolution_text(species):
    evos = (species or {}).get("evolutions", []) or []
    if not evos:
        return ["No outgoing evolution for this species."]

    lines = []
    for evo in evos:
        if not isinstance(evo, dict):
            lines.append("→ " + str(evo))
            continue

        target_raw = (
            evo.get("result")
            or evo.get("to")
            or evo.get("target")
            or evo.get("species")
            or ""
        )
        target = friendly_resource_name(target_raw) if target_raw else "Unknown"

        method_raw = evo.get("variant") or evo.get("type") or ""
        method = friendly_resource_name(method_raw)

        reqs = evo.get("requirements") or evo.get("requirement") or evo.get("conditions") or []
        req_texts = []

        if isinstance(reqs, dict):
            reqs = [reqs]

        if isinstance(reqs, list):
            for req in reqs:
                if not isinstance(req, dict):
                    if req:
                        req_texts.append(str(req))
                    continue

                variant = str(req.get("variant", "") or "").lower()

                if variant == "level" and req.get("minLevel") is not None:
                    req_texts.append(f"Level {req.get('minLevel')}")
                elif variant == "item":
                    item = req.get("item") or req.get("identifier") or ""
                    if item:
                        req_texts.append(f"Use {friendly_resource_name(item)}")
                elif variant in ("friendship", "happiness"):
                    amount = req.get("amount") or req.get("minimum") or req.get("minFriendship")
                    req_texts.append(
                        f"Friendship {amount}+" if amount is not None else "High friendship"
                    )
                elif variant == "time_range":
                    value = req.get("range") or req.get("timeRange") or req.get("time") or ""
                    req_texts.append(f"Time: {value}" if value else "Specific time")
                elif variant:
                    # Friendly generic rendering for less-common Cobblemon requirements.
                    details = []
                    for k, v in req.items():
                        if k == "variant":
                            continue
                        details.append(f"{friendly_resource_name(k)} {friendly_resource_name(v)}")
                    pretty_variant = friendly_resource_name(variant)
                    req_texts.append(
                        pretty_variant + (": " + ", ".join(details) if details else "")
                    )

        parts = [f"→ {target}"]
        if method:
            parts.append(method)
        if req_texts:
            parts.append(" • ".join(req_texts))

        lines.append("   •   ".join(parts))

    return lines



def all_move_names(pokedex):
    return sorted({m for p in (pokedex or []) for m in species_move_options(p)})

def all_ability_names(pokedex):
    return sorted({a for p in (pokedex or []) for a in species_ability_options(p)})

def pokemon_learning_move(pokedex, move_name):
    target=str(move_name or "").strip().lower()
    return [p for p in (pokedex or []) if target in {m.lower() for m in species_move_options(p)}]

def pokemon_with_ability(pokedex, ability_name):
    target=str(ability_name or "").strip().lower()
    return [p for p in (pokedex or []) if target in {a.lower() for a in species_ability_options(p)}]

def load_simple_db(path):
    try:
        if path.exists():
            data=json.loads(path.read_text(encoding="utf-8"))
            return data if isinstance(data,dict) else {}
    except Exception: pass
    return {}

def save_simple_db(path,data):
    try:path.write_text(json.dumps(data,indent=2,ensure_ascii=False),encoding="utf-8")
    except Exception:pass

def fetch_named_api_resource(kind,name):
    slug=move_slug(name); path=ITEM_DB_FILE if kind=="item" else ABILITY_DB_FILE
    cache=load_simple_db(path)
    if slug in cache:return cache[slug]
    try:
        req=urllib.request.Request(f"https://pokeapi.co/api/v2/{kind}/{slug}",headers={"User-Agent":"Cobblemon-Companion/1.0"})
        with urllib.request.urlopen(req,timeout=5) as response:raw=json.loads(response.read().decode("utf-8"))
        effect=""
        for e in raw.get("effect_entries",[]):
            if (e.get("language") or {}).get("name")=="en":
                effect=e.get("short_effect") or e.get("effect") or ""; break
        data={"name":friendly_resource_name(raw.get("name",name)),"effect":effect,
              "category":friendly_resource_name(((raw.get("category") or {}).get("name",""))),"cost":raw.get("cost")}
        cache[slug]=data; save_simple_db(path,cache); return data
    except Exception:return None

def calc_stat(base,iv,ev,level,nature=1.0,hp=False):
    base=int(base);iv=int(iv);ev=int(ev);level=int(level)
    if hp:return int(((2*base+iv+(ev//4))*level)/100)+level+10
    return int((int(((2*base+iv+(ev//4))*level)/100)+5)*nature)

def type_matchup_for_types(types):
    return species_defensive_profile({"types":[t for t in types if t]})

def global_search_entries(app, query):
    q = str(query or "").strip().lower()
    if not q:
        return []

    ensure_reference_indexes(app)
    out = []

    for p in app.pokedex:
        name = p.get("name","")
        if q in name.lower():
            out.append(("Pokémon",name,name))

    for record in app._move_index.values():
        name = record["name"]
        if q in name.lower():
            out.append(("Move",name,name))

    for record in app._ability_index.values():
        name = record["name"]
        if q in name.lower():
            out.append(("Ability",name,name))

    for item in app.item_index or []:
        name = item.get("name","")
        if q in name.lower():
            out.append(("Item",name,name))

    out.sort(key=lambda x:(not x[1].lower().startswith(q),x[0],x[1]))
    return out[:100]

def load_item_index():
    try:
        if ITEM_INDEX_FILE.exists():
            data = json.loads(ITEM_INDEX_FILE.read_text(encoding="utf-8"))
            if isinstance(data, list):
                return data
    except Exception:
        pass
    return []

def save_item_index(items):
    try:
        ITEM_INDEX_FILE.write_text(
            json.dumps(items, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )
    except Exception:
        pass

def _item_category_from_id(item_id, tag_paths=None):
    s = str(item_id or "").lower()
    paths = " ".join(tag_paths or []).lower()

    if "pokeball" in s or "poke_ball" in s or "ball" in paths:
        return "Poké Balls"
    if any(x in s for x in ("potion","restore","revive","antidote","heal","ether","elixir")):
        return "Medicine"
    if "berry" in s:
        return "Berries"
    if any(x in s for x in ("stone","candy","mint","vitamin","feather")):
        return "Training / Evolution"
    if any(x in paths for x in ("held", "battle", "choice", "type_boosting")):
        return "Held Items"
    if any(x in s for x in ("fossil","amber")) or "fossil" in paths:
        return "Fossils"
    if any(x in s for x in ("apricorn","tumblestone","vivichoke")):
        return "Materials"
    return "Other"

def import_items_from_cobblemon_jar(jar_path):
    """Build the item catalog from Cobblemon's own item translation keys.

    item.cobblemon.<id> keys correspond to Cobblemon-registered item names and are
    much broader than the berries that were previously known to the Companion.
    Item tags are used opportunistically for broad UI categories.
    """
    jar_path = Path(jar_path)
    if not jar_path.exists():
        raise FileNotFoundError(jar_path)

    item_names = {}
    item_tags = {}

    with zipfile.ZipFile(jar_path, "r") as zf:
        names = zf.namelist()

        lang_candidates = [
            n for n in names
            if n.replace("\\","/").lower().endswith("assets/cobblemon/lang/en_us.json")
        ]

        for lang_name in lang_candidates:
            try:
                raw = json.loads(zf.read(lang_name).decode("utf-8-sig"))
            except Exception:
                continue
            if not isinstance(raw, dict):
                continue
            for key, value in raw.items():
                if not isinstance(key, str) or not key.startswith("item.cobblemon."):
                    continue
                item_id = key[len("item.cobblemon."):]

                # Registered item names are top-level translation keys such as
                # item.cobblemon.choice_band.  Nested keys are tooltip/effect text
                # and were the source of entries like "1.5× catch rate".
                if not item_id or "." in item_id:
                    continue

                display = str(value or "").strip()

                # Dynamic/template strings are UI text, not standalone item names.
                if not display or "%" in display or "\\n" in display or "\n" in display:
                    continue

                # Keep plausible item display names only.
                if len(display) > 64:
                    continue

                item_names[item_id] = display

        # Read item tag JSONs to improve broad categorization.
        for n in names:
            low = n.replace("\\","/").lower()
            if not low.endswith(".json"):
                continue
            if "/tags/item/" not in ("/" + low) and "/tags/items/" not in ("/" + low):
                continue
            try:
                raw = json.loads(zf.read(n).decode("utf-8-sig"))
            except Exception:
                continue
            values = raw.get("values", []) if isinstance(raw, dict) else []
            for value in values:
                if isinstance(value, dict):
                    value = value.get("id", "")
                value = str(value or "")
                if value.startswith("cobblemon:"):
                    iid = value.split(":",1)[1]
                    item_tags.setdefault(iid, []).append(n)

    result = []
    seen_names = set()
    for item_id, name in item_names.items():
        norm = name.casefold()
        if norm in seen_names:
            continue
        seen_names.add(norm)
        result.append({
            "id": item_id,
            "name": name,
            "category": _item_category_from_id(item_id, item_tags.get(item_id, [])),
        })
    result.sort(key=lambda x: (x["category"], x["name"]))
    return result

def find_item_index_entry(app, item_name):
    target = str(item_name or "").strip().casefold()
    for item in getattr(app, "item_index", []) or []:
        if str(item.get("name","")).strip().casefold() == target:
            return item
    return None

def _recipe_result_id(recipe):
    if not isinstance(recipe, dict):
        return "", 1
    result = recipe.get("result")
    if isinstance(result, str):
        return result, 1
    if isinstance(result, dict):
        rid = result.get("id") or result.get("item") or result.get("name") or ""
        count = result.get("count", 1)
        return str(rid or ""), count
    # Some special recipes use output/item fields.
    rid = recipe.get("output") or recipe.get("item") or ""
    if isinstance(rid, dict):
        return str(rid.get("id") or rid.get("item") or ""), rid.get("count", 1)
    return str(rid or ""), 1

def _pretty_ingredient(value):
    if value is None:
        return "—"
    if isinstance(value, str):
        if value.startswith("#"):
            return "Any " + friendly_resource_name(value[1:])
        return friendly_resource_name(value)
    if isinstance(value, list):
        opts = [_pretty_ingredient(v) for v in value]
        return " / ".join(x for x in opts if x)
    if isinstance(value, dict):
        if "item" in value:
            return friendly_resource_name(value.get("item"))
        if "id" in value and str(value.get("id","")).startswith(("minecraft:","cobblemon:")):
            return friendly_resource_name(value.get("id"))
        if "tag" in value:
            return "Any " + friendly_resource_name(value.get("tag"))
        if "items" in value:
            return _pretty_ingredient(value.get("items"))
        # Ingredient components/data components can be noisy; prefer identifiable item/tag.
        for key in ("ingredient","value"):
            if key in value:
                return _pretty_ingredient(value.get(key))
    return friendly_resource_name(str(value))

GUI_CACHE_DIR = user_data_dir() / "gui_cache"
ITEM_ICON_CACHE_DIR = user_data_dir() / "item_icons"
GUI_CACHE_DIR.mkdir(parents=True, exist_ok=True)
ITEM_ICON_CACHE_DIR.mkdir(parents=True, exist_ok=True)

def _jar_png_candidates(jar_path, include_words):
    jar_path = Path(jar_path)
    if not jar_path.exists():
        return []
    words = [w.lower() for w in include_words]
    out = []
    try:
        with zipfile.ZipFile(jar_path, "r") as zf:
            for name in zf.namelist():
                low = name.replace("\\","/").lower()
                if not low.endswith(".png"):
                    continue
                if all(w in low for w in words):
                    out.append(name)
    except Exception:
        return []
    return out

def extract_best_cobblemon_gui_texture(jar_path, station_kind):
    """Try to extract Cobblemon's actual station GUI texture for a recipe station."""
    if station_kind != "cooking_pot":
        return None
    cache = GUI_CACHE_DIR / "cobblemon_cooking_pot.png"
    if cache.exists() and cache.stat().st_size > 100:
        return cache

    jar_path = Path(jar_path)
    if not jar_path.exists():
        return None

    # Search broadly; Cobblemon versions may rename folders.
    candidates = []
    for words in (("textures","gui","cooking"),("textures","gui","pot"),("gui","cooking"),("gui","pot")):
        candidates.extend(_jar_png_candidates(jar_path, words))
    candidates = list(dict.fromkeys(candidates))

    # Prefer container/background-like files over tiny icons.
    def score(name):
        low=name.lower()
        s=0
        for token, pts in (("background",8),("container",7),("screen",6),("cooking",5),("pot",4),("gui",3)):
            if token in low:s+=pts
        if "icon" in low:s-=4
        return s
    candidates.sort(key=score, reverse=True)

    try:
        with zipfile.ZipFile(jar_path, "r") as zf:
            for name in candidates:
                try:
                    data = zf.read(name)
                    cache.write_bytes(data)
                    # validate image
                    Image.open(cache).verify()
                    return cache
                except Exception:
                    try: cache.unlink(missing_ok=True)
                    except Exception: pass
    except Exception:
        pass
    return None

def _minecraft_id_parts(value):
    s=str(value or "").strip()
    if s.startswith("Any "):
        return "", ""
    if ":" in s:
        ns, iid = s.split(":",1)
        return ns, iid
    # Pretty labels don't reliably map back to IDs.
    return "", ""

def extract_cobblemon_item_icon(jar_path, item_id):
    """Extract a Cobblemon item texture when an obvious direct texture exists."""
    item_id = str(item_id or "").strip()
    if not item_id:
        return None
    cache = ITEM_ICON_CACHE_DIR / f"{item_id}.png"
    if cache.exists() and cache.stat().st_size > 50:
        return cache
    jar_path = Path(jar_path)
    if not jar_path.exists():
        return None

    # Direct conventional paths first.
    direct = [
        f"assets/cobblemon/textures/item/{item_id}.png",
        f"assets/cobblemon/textures/items/{item_id}.png",
    ]
    try:
        with zipfile.ZipFile(jar_path,"r") as zf:
            names=set(zf.namelist())
            for name in direct:
                if name in names:
                    cache.write_bytes(zf.read(name))
                    return cache

            # Fallback scan by basename.
            wanted=f"/{item_id}.png"
            for name in names:
                low=name.replace("\\","/").lower()
                if "/textures/item/" in low and low.endswith(wanted):
                    cache.write_bytes(zf.read(name))
                    return cache
    except Exception:
        return None
    return None

def recipe_ingredient_lookup_id(label, recipe):
    """Best-effort map a rendered ingredient label back to a Cobblemon item id."""
    label=str(label or "").strip()
    # Use recipe's source structures where possible; for now resolve Cobblemon by pretty-name index later.
    return label


VANILLA_ICON_CACHE_DIR = user_data_dir() / "vanilla_item_icons"
VANILLA_ICON_CACHE_DIR.mkdir(parents=True, exist_ok=True)

def candidate_minecraft_client_jars(cobblemon_jar=None):
    found = []
    seen = set()

    def add(path):
        try:
            p = Path(path)
            if p.exists() and p.is_file() and p.suffix.lower() == ".jar":
                key = str(p.resolve())
                if key not in seen:
                    seen.add(key)
                    found.append(p)
        except Exception:
            pass

    home = Path.home()
    versions = home / "AppData" / "Roaming" / ".minecraft" / "versions"
    if versions.exists():
        try:
            for p in versions.glob("*/*.jar"):
                add(p)
        except Exception:
            pass

    if cobblemon_jar:
        try:
            cj = Path(cobblemon_jar)
            roots = [cj.parent, cj.parent.parent, cj.parent.parent.parent]
            for root in roots:
                for rel in ("versions", ".minecraft/versions", "minecraft/versions"):
                    d = root / rel
                    if d.exists():
                        for p in d.glob("*/*.jar"):
                            add(p)
        except Exception:
            pass

    try:
        found.sort(key=lambda p: (p.stat().st_mtime, p.stat().st_size), reverse=True)
    except Exception:
        pass
    return found[:20]

def _texture_from_jar(jar_path, namespace, item_id):
    namespace = str(namespace or "").strip()
    item_id = str(item_id or "").strip()
    if not namespace or not item_id:
        return None

    cache_dir = ITEM_ICON_CACHE_DIR if namespace == "cobblemon" else VANILLA_ICON_CACHE_DIR
    cache = cache_dir / f"{namespace}_{item_id.replace('/','_')}.png"
    if cache.exists() and cache.stat().st_size > 40:
        return cache

    candidates = [
        f"assets/{namespace}/textures/item/{item_id}.png",
        f"assets/{namespace}/textures/items/{item_id}.png",
    ]
    try:
        with zipfile.ZipFile(jar_path, "r") as zf:
            names = set(zf.namelist())
            for name in candidates:
                if name in names:
                    cache.write_bytes(zf.read(name))
                    return cache
    except Exception:
        pass
    return None

def extract_vanilla_item_icon(cobblemon_jar, item_id):
    item_id = str(item_id or "").strip()
    if not item_id:
        return None
    cache = VANILLA_ICON_CACHE_DIR / f"minecraft_{item_id.replace('/','_')}.png"
    if cache.exists() and cache.stat().st_size > 40:
        return cache
    for jar in candidate_minecraft_client_jars(cobblemon_jar):
        path = _texture_from_jar(jar, "minecraft", item_id)
        if path:
            return path
    return None

def item_id_from_pretty_name(app, label):
    raw = str(label or "").strip()
    if not raw:
        return None
    if ":" in raw and " " not in raw:
        return raw.lstrip("#")

    target = raw.casefold()
    if target.startswith("any "):
        return None

    for item in getattr(app, "item_index", []) or []:
        if str(item.get("name","")).strip().casefold() == target:
            return f"cobblemon:{item.get('id','')}"

    vanilla_id = re.sub(r"[^a-z0-9]+", "_", raw.lower()).strip("_")
    return f"minecraft:{vanilla_id}" if vanilla_id else None

def local_item_icon_path(app, label):
    rid = item_id_from_pretty_name(app, label)
    if not rid or ":" not in rid:
        return None
    ns, iid = rid.split(":", 1)
    if ns == "cobblemon":
        return extract_cobblemon_item_icon(app.dex_meta.get("source_jar",""), iid)
    if ns == "minecraft":
        return extract_vanilla_item_icon(app.dex_meta.get("source_jar",""), iid)
    return None

def _pil_icon(path, size=42):
    try:
        img = Image.open(path).convert("RGBA")
        img.thumbnail((size, size), Image.Resampling.NEAREST)
        return img
    except Exception:
        return None

def _draw_slot_base(draw, xy, slot=54):
    x, y = xy
    draw.rectangle((x, y, x+slot-1, y+slot-1), fill=(139,139,139,255))
    draw.line((x, y, x+slot-1, y), fill=(55,55,55,255), width=3)
    draw.line((x, y, x, y+slot-1), fill=(55,55,55,255), width=3)
    draw.line((x+3, y+3, x+slot-4, y+3), fill=(255,255,255,255), width=3)
    draw.line((x+3, y+3, x+3, y+slot-4), fill=(255,255,255,255), width=3)
    draw.rectangle((x+6, y+6, x+slot-7, y+slot-7), fill=(198,198,198,255))

def _draw_fallback_symbol(image, xy, label, slot=54):
    x,y = xy
    draw = ImageDraw.Draw(image)
    low = str(label or "").lower()
    cx, cy = x+slot/2, y+slot/2

    if "gem" in low or "crystal" in low:
        pts=[(cx,y+6),(x+slot-7,y+18),(cx,y+slot-5),(x+7,y+18)]
        draw.polygon(pts, fill=(86,207,246,255), outline=(30,90,130,255))
    elif "ingot" in low or "metal" in low:
        draw.polygon([(x+11,y+35),(x+17,y+17),(x+39,y+14),(x+44,y+30),(x+35,y+40),(x+16,y+42)],
                     fill=(220,183,74,255), outline=(100,75,25,255))
    elif "glass" in low:
        draw.rectangle((x+8,y+8,x+slot-9,y+slot-9),fill=(180,230,235,150),outline=(70,130,140,255),width=2)
        draw.line((x+12,y+12,x+slot-13,y+slot-13),fill=(235,255,255,220),width=2)
    else:
        draw.ellipse((x+8,y+8,x+slot-9,y+slot-9),fill=(120,160,190,255),outline=(50,80,100,255),width=2)

def _paste_recipe_icon(image, app, label, xy, slot=54):
    x,y = xy
    path = local_item_icon_path(app, label)

    # Fill most of the usable inner slot. Minecraft's native 16x16 icons can
    # safely be enlarged with NEAREST filtering and stay crisp/pixel-perfect.
    icon_size = max(16, slot - 8)
    icon = _pil_icon(path, size=icon_size) if path else None
    if icon:
        px = int(x + (slot-icon.width)/2)
        py = int(y + (slot-icon.height)/2)
        image.alpha_composite(icon, (px,py))
        return True

    _draw_fallback_symbol(image, xy, label, slot)
    return False

def compose_recipe_image(app, recipe, station_kind, output_name):
    bg_color=(198,198,198,255)
    border=(55,55,55,255)
    slot=54
    gap=6

    if station_kind=="crafting":
        W,H=560,300
        im=Image.new("RGBA",(W,H),(0,0,0,0))
        d=ImageDraw.Draw(im)
        d.rounded_rectangle((4,4,W-5,H-5),radius=8,fill=bg_color,outline=border,width=5)
        ox,oy=55,62
        pattern=recipe.get("pattern",[]) or []
        key=recipe.get("key",{}) or {}
        ingredients=recipe.get("ingredients",[]) or []

        for r in range(3):
            for c in range(3):
                xy=(ox+c*(slot+gap),oy+r*(slot+gap))
                _draw_slot_base(d,xy,slot)
                label=""
                if pattern:
                    row=pattern[r] if r<len(pattern) else ""
                    sym=row[c] if c<len(row) else " "
                    if sym!=" ": label=key.get(sym,sym)
                else:
                    idx=r*3+c
                    if idx<len(ingredients): label=ingredients[idx]
                if label:
                    _paste_recipe_icon(im,app,label,xy,slot)

        ax,ay=300,125
        d.polygon([(ax,ay+16),(ax+62,ay+16),(ax+62,ay),(ax+100,ay+28),(ax+62,ay+56),(ax+62,ay+40),(ax,ay+40)],
                  fill=(95,95,95,255))
        outxy=(445,112)
        _draw_slot_base(d,outxy,74)
        _paste_recipe_icon(im,app,output_name,outxy,74)
        count=recipe.get("count",1)
        if count and count!=1:
            d.text((outxy[0]+50,outxy[1]+52),str(count),fill=(255,255,255,255),stroke_width=2,stroke_fill=(0,0,0,255))
        return im

    if station_kind=="furnace":
        W,H=500,330
        im=Image.new("RGBA",(W,H),(0,0,0,0))
        d=ImageDraw.Draw(im)
        d.rounded_rectangle((4,4,W-5,H-5),radius=8,fill=bg_color,outline=border,width=5)
        inxy=(95,50); fuelxy=(95,220); outxy=(360,120)
        for xy in (inxy,fuelxy): _draw_slot_base(d,xy,slot)
        _draw_slot_base(d,outxy,74)
        ing=(recipe.get("ingredients",[]) or ["Ingredient"])[0]
        _paste_recipe_icon(im,app,ing,inxy,slot)
        d.polygon([(120,210),(104,180),(112,145),(128,171),(139,139),(157,177),(145,210)],
                  fill=(232,110,20,255))
        ax,ay=205,122
        d.polygon([(ax,ay+16),(ax+62,ay+16),(ax+62,ay),(ax+100,ay+28),(ax+62,ay+56),(ax+62,ay+40),(ax,ay+40)],
                  fill=(95,95,95,255))
        _paste_recipe_icon(im,app,output_name,outxy,74)
        return im

    if station_kind=="smithing":
        W,H=610,240
        im=Image.new("RGBA",(W,H),(0,0,0,0))
        d=ImageDraw.Draw(im)
        d.rounded_rectangle((4,4,W-5,H-5),radius=8,fill=bg_color,outline=border,width=5)
        vals={"Template":"Template","Base":"Base","Addition":"Addition"}
        for line in recipe.get("extra",[]) or []:
            if ":" in line:
                k,v=line.split(":",1)
                if k.strip() in vals: vals[k.strip()]=v.strip()
        x0=50
        for i,k in enumerate(("Template","Base","Addition")):
            xy=(x0+i*80,85)
            _draw_slot_base(d,xy,slot)
            _paste_recipe_icon(im,app,vals[k],xy,slot)
        ax,ay=305,84
        d.polygon([(ax,ay+16),(ax+62,ay+16),(ax+62,ay),(ax+100,ay+28),(ax+62,ay+56),(ax+62,ay+40),(ax,ay+40)],
                  fill=(95,95,95,255))
        outxy=(470,75)
        _draw_slot_base(d,outxy,74)
        _paste_recipe_icon(im,app,output_name,outxy,74)
        return im

    if station_kind=="cooking_pot":
        W,H=620,330
        im=Image.new("RGBA",(W,H),(0,0,0,0))
        d=ImageDraw.Draw(im)
        d.rounded_rectangle((4,4,W-5,H-5),radius=8,fill=bg_color,outline=border,width=5)
        d.rounded_rectangle((28,28,275,290),radius=16,fill=(165,165,165,255),outline=(65,65,65,255),width=4)
        ingredients=list(recipe.get("ingredients",[]) or [])
        if not ingredients and recipe.get("pattern"):
            key=recipe.get("key",{}) or {}
            for row in recipe.get("pattern",[])[:3]:
                for sym in row[:3]:
                    if sym!=" ": ingredients.append(key.get(sym,sym))
        ox,oy=62,57
        for i in range(9):
            xy=(ox+(i%3)*(slot+8),oy+(i//3)*(slot+8))
            _draw_slot_base(d,xy,slot)
            if i<len(ingredients):
                _paste_recipe_icon(im,app,ingredients[i],xy,slot)
        d.polygon([(146,286),(127,252),(137,220),(153,247),(166,214),(185,252),(171,286)],
                  fill=(232,110,20,255))
        ax,ay=330,126
        d.polygon([(ax,ay+16),(ax+72,ay+16),(ax+72,ay),(ax+112,ay+28),(ax+72,ay+56),(ax+72,ay+40),(ax,ay+40)],
                  fill=(95,95,95,255))
        outxy=(505,112)
        _draw_slot_base(d,outxy,78)
        _paste_recipe_icon(im,app,output_name,outxy,78)
        return im

    return None

def recipe_interactive_regions(recipe, station_kind, output_name):
    """Return hover/click regions matching compose_recipe_image coordinates."""
    regions = []
    slot = 54
    gap = 6

    def add(x, y, w, h, label, output=False):
        label = str(label or "").strip()
        if not label:
            return
        regions.append({
            "x1": x, "y1": y, "x2": x+w, "y2": y+h,
            "label": label,
            "output": output,
            "clickable": not label.lower().startswith("any "),
        })

    if station_kind == "crafting":
        ox, oy = 55, 62
        pattern = recipe.get("pattern", []) or []
        key = recipe.get("key", {}) or {}
        ingredients = recipe.get("ingredients", []) or []
        for r in range(3):
            for c in range(3):
                label = ""
                if pattern:
                    row = pattern[r] if r < len(pattern) else ""
                    sym = row[c] if c < len(row) else " "
                    if sym != " ":
                        label = key.get(sym, sym)
                else:
                    idx = r*3 + c
                    if idx < len(ingredients):
                        label = ingredients[idx]
                add(ox+c*(slot+gap), oy+r*(slot+gap), slot, slot, label)
        add(445, 112, 74, 74, output_name, output=True)

    elif station_kind == "furnace":
        ingredients = recipe.get("ingredients", []) or []
        if ingredients:
            add(95, 50, slot, slot, ingredients[0])
        add(360, 120, 74, 74, output_name, output=True)

    elif station_kind == "smithing":
        vals = {"Template":"", "Base":"", "Addition":""}
        for line in recipe.get("extra", []) or []:
            if ":" in line:
                k, v = line.split(":", 1)
                if k.strip() in vals:
                    vals[k.strip()] = v.strip()
        for x, keyname in zip((50,130,210), ("Template","Base","Addition")):
            add(x, 85, slot, slot, vals[keyname])
        add(470, 75, 74, 74, output_name, output=True)

    elif station_kind == "cooking_pot":
        ingredients = list(recipe.get("ingredients", []) or [])
        if not ingredients and recipe.get("pattern"):
            key = recipe.get("key", {}) or {}
            for row in recipe.get("pattern", [])[:3]:
                for sym in row[:3]:
                    if sym != " ":
                        ingredients.append(key.get(sym, sym))
        ox, oy = 62, 57
        for i, value in enumerate(ingredients[:9]):
            add(ox+(i%3)*(slot+8), oy+(i//3)*(slot+8), slot, slot, value)
        add(505, 112, 78, 78, output_name, output=True)

    return regions

def recipe_station_kind(recipe):
    """Classify a normalized recipe into a visual station."""
    rtype = str((recipe or {}).get("raw_type") or (recipe or {}).get("type", "") or "").lower()
    source = str((recipe or {}).get("source", "") or "").lower()

    hay = f"{rtype} {source}"

    # Cobblemon cooking-pot / food style recipes.
    if any(x in hay for x in ("cooking pot", "cooking_pot", "pot recipe", "campfire_pot", "poké snack", "poke snack")):
        return "cooking_pot"

    if "smith" in hay:
        return "smithing"

    if any(x in hay for x in ("smelt", "blast", "smoker", "campfire cooking", "furnace")):
        return "furnace"

    if "crafting" in hay or (recipe or {}).get("pattern") or (recipe or {}).get("ingredients"):
        return "crafting"

    return "generic"

def short_slot_text(value, max_len=18):
    s = str(value or "Empty").strip()
    if len(s) <= max_len:
        return s
    # Prefer readable two-line labels rather than microscopic text.
    words = s.split()
    if len(words) > 1:
        line1 = ""
        line2 = ""
        for word in words:
            if len(line1) + len(word) + 1 <= max_len // 2 + 3:
                line1 = (line1 + " " + word).strip()
            else:
                line2 = (line2 + " " + word).strip()
        if line2:
            return line1 + "\n" + line2[:max_len]
    return s[:max_len-1] + "…"

def _normalize_recipe(recipe, source_name):
    if not isinstance(recipe, dict):
        return None
    rtype = str(recipe.get("type","") or "")
    type_name = friendly_resource_name(rtype.split(":",1)[-1]) if rtype else "Crafting"
    rid, count = _recipe_result_id(recipe)

    out = {
        "type": type_name or "Crafting",
        "raw_type": rtype,
        "result": rid,
        "count": count,
        "source": source_name,
        "pattern": [],
        "key": {},
        "ingredients": [],
        "extra": [],
    }

    pattern = recipe.get("pattern")
    key = recipe.get("key")
    if isinstance(pattern, list) and isinstance(key, dict):
        out["pattern"] = [str(x) for x in pattern]
        for symbol, ingredient in key.items():
            out["key"][str(symbol)] = _pretty_ingredient(ingredient)

    ingredients = recipe.get("ingredients")
    if isinstance(ingredients, list):
        out["ingredients"] = [_pretty_ingredient(v) for v in ingredients]

    if recipe.get("ingredient") is not None:
        out["ingredients"].append(_pretty_ingredient(recipe.get("ingredient")))

    # Smithing-style recipes.
    for label, keyname in (("Template","template"),("Base","base"),("Addition","addition")):
        if recipe.get(keyname) is not None:
            out["extra"].append(f"{label}: {_pretty_ingredient(recipe.get(keyname))}")

    # Cooking / processing metadata.
    if recipe.get("cookingtime") is not None:
        out["extra"].append(f"Cooking time: {recipe.get('cookingtime')} ticks")
    if recipe.get("experience") is not None:
        out["extra"].append(f"Experience: {recipe.get('experience')}")

    return out

def _clean_item_description_strings(values):
    cleaned = []
    seen = set()
    for value in values:
        s = str(value or "").strip().replace("\\n"," ").replace("\n"," ")
        if not s:
            continue
        # Replace common Minecraft format placeholders with readable blanks.
        s = re.sub(r"%\d*\$?[sdif]", "…", s)
        s = re.sub(r"\s+", " ", s).strip()
        if len(s) < 4 or len(s) > 300:
            continue
        norm = s.casefold()
        if norm not in seen:
            seen.add(norm)
            cleaned.append(s)
    return cleaned

def extract_cobblemon_item_details(jar_path, item_id):
    """Read local Cobblemon item descriptions and recipes for one item."""
    jar_path = Path(jar_path)
    if not jar_path.exists():
        return {"descriptions": [], "recipes": []}

    item_id = str(item_id or "").strip()
    if not item_id:
        return {"descriptions": [], "recipes": []}

    descriptions = []
    recipes = []

    with zipfile.ZipFile(jar_path, "r") as zf:
        names = zf.namelist()

        # Nested translation keys frequently contain item tooltip/effect text.
        for name in names:
            low = name.replace("\\","/").lower()
            if not low.endswith("assets/cobblemon/lang/en_us.json"):
                continue
            try:
                lang = json.loads(zf.read(name).decode("utf-8-sig"))
            except Exception:
                continue
            prefix = f"item.cobblemon.{item_id}."
            if isinstance(lang, dict):
                for key, value in lang.items():
                    if isinstance(key, str) and key.startswith(prefix):
                        descriptions.append(value)

        # Support both pre-1.21 plural recipes and 1.21+ singular recipe path.
        for name in names:
            low = name.replace("\\","/").lower()
            if not low.endswith(".json"):
                continue
            if "/recipe/" not in ("/" + low) and "/recipes/" not in ("/" + low):
                continue
            try:
                raw = json.loads(zf.read(name).decode("utf-8-sig"))
            except Exception:
                continue

            # Normal single recipe.
            candidates = [raw]
            # A few datapack structures may wrap recipe arrays.
            if isinstance(raw, dict) and isinstance(raw.get("recipes"), list):
                candidates.extend(raw.get("recipes"))

            for recipe in candidates:
                rid, _ = _recipe_result_id(recipe)
                if str(rid).lower() == f"cobblemon:{item_id}".lower():
                    norm = _normalize_recipe(recipe, name)
                    if norm:
                        recipes.append(norm)

    # De-dupe recipes by normalized JSON.
    unique = []
    seen = set()
    for recipe in recipes:
        key = json.dumps(recipe, sort_keys=True, ensure_ascii=False)
        if key not in seen:
            seen.add(key)
            unique.append(recipe)

    return {
        "descriptions": _clean_item_description_strings(descriptions),
        "recipes": unique,
    }

def load_item_detail_cache():
    return load_simple_db(ITEM_DETAIL_FILE)

def save_item_detail_cache(data):
    save_simple_db(ITEM_DETAIL_FILE, data)

def get_local_item_details(app, item_name):
    entry = find_item_index_entry(app, item_name)
    if not entry:
        return None

    item_id = entry.get("id","")
    cache = load_item_detail_cache()
    key = item_id.lower()
    if key in cache:
        data = dict(cache[key])
        data.setdefault("id", item_id)
        data.setdefault("name", entry.get("name", item_name))
        data.setdefault("category", entry.get("category", "Other"))
        return data

    jar = app.dex_meta.get("source_jar")
    if not jar or not Path(jar).exists():
        return {
            "id": item_id,
            "name": entry.get("name", item_name),
            "category": entry.get("category", "Other"),
            "descriptions": [],
            "recipes": [],
        }

    data = extract_cobblemon_item_details(jar, item_id)
    data.update({
        "id": item_id,
        "name": entry.get("name", item_name),
        "category": entry.get("category", "Other"),
    })
    cache[key] = data
    save_item_detail_cache(cache)
    return data

def ensure_reference_indexes(app):
    """Build move/ability cross-reference indexes once per session."""
    if getattr(app, "_reference_indexes_ready", False):
        return

    move_users = {}
    ability_users = {}

    for p in app.pokedex:
        pname = p.get("name", "")
        for move in species_move_options(p):
            move_users.setdefault(move.lower(), {"name": move, "pokemon": []})["pokemon"].append(pname)
        for ability in species_ability_options(p):
            ability_users.setdefault(ability.lower(), {"name": ability, "pokemon": []})["pokemon"].append(pname)

    app._move_index = move_users
    app._ability_index = ability_users
    app._reference_indexes_ready = True

def indexed_move_names(app):
    ensure_reference_indexes(app)
    return sorted(v["name"] for v in app._move_index.values())

def indexed_ability_names(app):
    ensure_reference_indexes(app)
    return sorted(v["name"] for v in app._ability_index.values())

def indexed_pokemon_learning_move(app, move_name):
    ensure_reference_indexes(app)
    names = app._move_index.get(str(move_name or "").lower(), {}).get("pokemon", [])
    wanted = set(names)
    return [p for p in app.pokedex if p.get("name") in wanted]

def indexed_pokemon_with_ability(app, ability_name):
    ensure_reference_indexes(app)
    names = app._ability_index.get(str(ability_name or "").lower(), {}).get("pokemon", [])
    wanted = set(names)
    return [p for p in app.pokedex if p.get("name") in wanted]


def species_moves_by_method(species):
    """Group imported Cobblemon learnset entries by learn method."""
    groups = {}
    for raw in (species or {}).get("moves", []) or []:
        method = "Other"
        move = ""

        if isinstance(raw, dict):
            move = raw.get("move") or raw.get("id") or raw.get("name") or ""
            raw_method = raw.get("method") or raw.get("variant") or raw.get("type") or ""
            method = friendly_resource_name(raw_method) if raw_method else "Other"
        else:
            s = str(raw or "").strip()
            if not s:
                continue
            if ":" in s:
                prefix, move = s.rsplit(":", 1)
                plow = prefix.lower()
                if plow == "egg" or "egg" in plow:
                    method = "Egg"
                elif plow in ("tm", "machine") or "tm" in plow:
                    method = "TM"
                elif "tutor" in plow:
                    method = "Tutor"
                elif plow.isdigit() or plow.startswith("level"):
                    method = "Level"
                else:
                    method = friendly_resource_name(prefix)
            else:
                move = s

        pretty = friendly_resource_name(move)
        if pretty:
            groups.setdefault(method or "Other", set()).add(pretty)

    return {k: sorted(v) for k, v in groups.items()}

def species_egg_moves(species):
    groups = species_moves_by_method(species)
    out = set()
    for method, moves in groups.items():
        if "egg" in method.lower():
            out.update(moves)
    return sorted(out)

def shared_egg_groups(a, b):
    ag = {str(x).lower() for x in (a or {}).get("egg_groups", []) if x}
    bg = {str(x).lower() for x in (b or {}).get("egg_groups", []) if x}
    return sorted(ag & bg)

def breeding_compatible_species(pokedex, target):
    if not target:
        return []
    result = []
    for p in pokedex or []:
        if p.get("name","").casefold() == target.get("name","").casefold():
            continue
        shared = shared_egg_groups(target, p)
        if shared:
            result.append((p, shared))
    return result

def move_method_for_species(species, move_name):
    target = str(move_name or "").casefold()
    methods = []
    for method, moves in species_moves_by_method(species).items():
        if target in {m.casefold() for m in moves}:
            methods.append(method)
    return methods

def breeding_move_sources(pokedex, target, move_name):
    """Direct compatible parents that have the desired move in their learnset."""
    results = []
    for p, shared in breeding_compatible_species(pokedex, target):
        methods = move_method_for_species(p, move_name)
        if methods:
            results.append({
                "species": p,
                "shared_groups": shared,
                "methods": methods,
            })

    # Prefer obvious non-egg sources, then shorter/easier-looking learn methods.
    def rank(entry):
        methods = {m.lower() for m in entry["methods"]}
        egg_only = bool(methods) and all("egg" in m for m in methods)
        return (egg_only, entry["species"].get("dex", 9999))
    results.sort(key=rank)
    return results

def breeding_chain_candidates(pokedex, target, move_name, max_depth=3):
    """Find Egg-Group connectivity chains to species that know a move.

    This is intentionally presented as a candidate chain rather than a guaranteed
    breeding recipe because gender/form/inheritance mechanics may add constraints.
    """
    if not target or not move_name:
        return []

    by_name = {p.get("name",""): p for p in pokedex or []}
    compat = {}
    species_list = list(pokedex or [])

    # Build adjacency lazily for only species reached by BFS.
    def neighbors(species):
        name = species.get("name","")
        if name in compat:
            return compat[name]
        out = []
        for p in species_list:
            if p.get("name","") == name:
                continue
            shared = shared_egg_groups(species, p)
            if shared:
                out.append((p, shared))
        compat[name] = out
        return out

    target_name = target.get("name","")
    queue = [(target, [target_name], [])]
    seen = {target_name}
    found = []

    while queue:
        current, path, group_path = queue.pop(0)
        depth = len(path) - 1
        if depth >= max_depth:
            continue

        for nxt, shared in neighbors(current):
            nname = nxt.get("name","")
            if nname in seen:
                continue
            seen.add(nname)
            npath = path + [nname]
            ngroups = group_path + [shared]

            methods = move_method_for_species(nxt, move_name)
            if methods:
                found.append({
                    "path": npath,
                    "groups": ngroups,
                    "methods": methods,
                    "source": nxt,
                })
                if len(found) >= 20:
                    return found

            queue.append((nxt, npath, ngroups))

    return found


DEFAULT_BINGO = [
    "Pikachu", "Eevee", "Riolu", "Ralts", "Dratini",
    "Larvitar", "Beldum", "Feebas", "Mimikyu", "Litwick",
    "Gengar", "Scyther", "Rotom", "Sableye", "Gimmighoul",
    "Bulbasaur", "Charmander", "Squirtle", "Gholdengo", "",
    "", "", "", "", ""
]

def default_profile():
    return {
        "profile_name": "My Cobblemon World",
        "bingo_name": "Weekly Bingo Card",
        "bingo": [{"pokemon": p, "caught": False} for p in DEFAULT_BINGO],
        "hunts": [],
        "living_dex": [],
        "teams": [],
        "last_breeding_target": "",
    }

def load_profile():
    if not SAVE_FILE.exists():
        return default_profile()
    try:
        with open(SAVE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        base = default_profile()
        base.update(data)
        if len(base.get("bingo", [])) != 25:
            base["bingo"] = default_profile()["bingo"]
        return base
    except Exception:
        return default_profile()

def save_profile(profile):
    with open(SAVE_FILE, "w", encoding="utf-8") as f:
        json.dump(profile, f, indent=2)

class NavButton(tk.Button):
    def __init__(self, master, text, command):
        super().__init__(
            master, text=text, command=command,
            bg=PANEL, fg=TEXT, activebackground=PANEL_2, activeforeground=TEXT,
            relief="flat", bd=0, anchor="w", padx=18, pady=11,
            font=("Segoe UI", 10, "bold"), cursor="hand2"
        )

class Page(tk.Frame):
    title = ""
    subtitle = ""

    def __init__(self, master, app):
        super().__init__(master, bg=BG)
        self.app = app

    def header(self, title=None, subtitle=None):
        tk.Label(self, text=title or self.title, bg=BG, fg=TEXT,
                 font=("Segoe UI Semibold", 24)).pack(anchor="w", padx=28, pady=(24, 0))
        sub = self.subtitle if subtitle is None else subtitle
        if sub:
            tk.Label(self, text=sub, bg=BG, fg=MUTED,
                     font=("Segoe UI", 10)).pack(anchor="w", padx=29, pady=(3, 18))

class HomePage(Page):
    title = "Home"
    subtitle = "Live dashboard for the things you're actually doing in Cobblemon."

    def __init__(self, master, app):
        super().__init__(master, app)
        self.sprite_refs = {}
        self._potd_ref = None
        self._potd_sprite_fetch_running = False

        # Home is itself scrollable because it is the page most likely to stay open.
        self.canvas = tk.Canvas(self, bg=BG, highlightthickness=0)
        self.scroll = tk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.inner = tk.Frame(self.canvas, bg=BG)
        self.inner_win = self.canvas.create_window((0,0), window=self.inner, anchor="nw")

        self.inner.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        self.canvas.bind(
            "<Configure>",
            lambda e: self.canvas.itemconfigure(self.inner_win, width=e.width)
        )
        self.canvas.configure(yscrollcommand=self.scroll.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scroll.pack(side="right", fill="y")

        # Header.
        header = tk.Frame(self.inner, bg=BG)
        header.pack(fill="x", padx=28, pady=(24, 10))

        left = tk.Frame(header, bg=BG)
        left.pack(side="left", fill="x", expand=True)
        tk.Label(
            left, text="Home Dashboard",
            bg=BG, fg=TEXT,
            font=("Segoe UI Semibold", 24)
        ).pack(anchor="w")
        self.profile_label = tk.Label(
            left, text="",
            bg=BG, fg=MUTED,
            font=("Segoe UI", 9)
        )
        self.profile_label.pack(anchor="w", pady=(2,0))

        # Quick global search directly on Home.
        search = tk.Frame(header, bg=BG)
        search.pack(side="right", padx=(15,0))
        self.search_query = tk.StringVar()
        entry = tk.Entry(
            search, textvariable=self.search_query,
            bg=PANEL, fg=TEXT, insertbackground=TEXT,
            relief="flat", width=30,
            font=("Segoe UI", 10)
        )
        entry.pack(side="left", ipady=8)
        entry.bind("<Return>", lambda e:self.open_search())
        tk.Button(
            search, text="Search",
            command=self.open_search,
            bg=ACCENT_2, fg="white",
            relief="flat", padx=12, pady=8
        ).pack(side="left", padx=(6,0))

        # Top progress strip.
        self.stats = tk.Frame(self.inner, bg=BG)
        self.stats.pack(fill="x", padx=28, pady=(0, 12))
        self.stat_widgets = {}
        for i, label in enumerate(("COLLECTION", "BINGO", "ACTIVE HUNTS", "SAVED TEAMS")):
            self.stats.grid_columnconfigure(i, weight=1, uniform="home_stats")
            box = tk.Frame(self.stats, bg=PANEL)
            box.grid(row=0, column=i, sticky="nsew", padx=(0 if i==0 else 4, 0))
            tk.Label(box, text=label, bg=PANEL, fg=MUTED,
                     font=("Segoe UI", 8, "bold")).pack(anchor="w", padx=12, pady=(9,1))
            value = tk.Label(box, text="—", bg=PANEL, fg=TEXT,
                             font=("Segoe UI Semibold", 17))
            value.pack(anchor="w", padx=12)
            action = tk.Button(
                box, text="Open →",
                bg=PANEL, fg=MUTED,
                activebackground=PANEL_2, activeforeground=TEXT,
                relief="flat", bd=0,
                font=("Segoe UI", 7),
                command=lambda:None
            )
            action.pack(anchor="w", padx=7, pady=(1,7))
            self.stat_widgets[label] = (value, action)

        # Responsive two-column dashboard.
        self.grid = tk.Frame(self.inner, bg=BG)
        self.grid.pack(fill="both", expand=True, padx=28, pady=(0, 12))
        self.grid.grid_columnconfigure(0, weight=1, uniform="home_col")
        self.grid.grid_columnconfigure(1, weight=1, uniform="home_col")

        self.hunts_card = self.make_card(self.grid, "Hunt Planner", 0, 0)
        self.bingo_card = self.make_card(self.grid, "Weekly Bingo", 0, 1)
        self.team_card = self.make_card(self.grid, "Current Team", 1, 0)
        self.breeding_card = self.make_card(self.grid, "Breeding Project", 1, 1)

        self.potd_card = self.make_card(self.inner, "Pokémon of the Day", None, None)
        self.potd_card.pack(fill="x", padx=28, pady=(0, 12))

        self.quick_card = self.make_card(self.inner, "Quick Actions", None, None)
        self.quick_card.pack(fill="x", padx=28, pady=(0, 28))

        self.refresh()

    def make_card(self, parent, title, row, col):
        card = tk.Frame(parent, bg=PANEL)
        if row is not None:
            card.grid(row=row, column=col, sticky="nsew", padx=(0 if col==0 else 5, 5 if col==0 else 0), pady=5)

        header = tk.Frame(card, bg=PANEL)
        header.pack(fill="x", padx=14, pady=(11,6))
        tk.Label(header, text=title, bg=PANEL, fg=TEXT,
                 font=("Segoe UI Semibold", 13)).pack(side="left")
        body = tk.Frame(card, bg=PANEL)
        body.pack(fill="both", expand=True, padx=12, pady=(0,12))
        card._dashboard_body = body
        return card

    def card_body(self, card):
        body = card._dashboard_body
        for w in body.winfo_children():
            w.destroy()
        return body

    def open_search(self):
        q = self.search_query.get().strip()
        win = GlobalSearchWindow(self.app, q)
        self.search_query.set("")

    def refresh(self):
        p = self.app.profile
        self.profile_label.config(
            text=f"{p.get('profile_name', 'My Cobblemon World')}   •   Cobblemon Companion v{APP_VERSION}"
        )

        total = int(self.app.dex_meta.get("species_count", 0) or len(self.app.pokedex) or 0)
        owned = len(p.get("living_dex", []))
        bingo = p.get("bingo", [])
        caught = sum(1 for x in bingo if x.get("pokemon") and x.get("caught"))
        filled = sum(1 for x in bingo if x.get("pokemon"))
        hunts = p.get("hunts", [])
        teams = p.get("teams", [])

        stat_data = {
            "COLLECTION": (f"{owned} / {total}" if total else str(owned), "Collection"),
            "BINGO": (f"{caught} / {filled}", "Bingo"),
            "ACTIVE HUNTS": (str(len(hunts)), "Hunts"),
            "SAVED TEAMS": (str(len(teams)), "Teams"),
        }
        for label, (value, page) in stat_data.items():
            val, btn = self.stat_widgets[label]
            val.config(text=value)
            btn.config(command=lambda p=page:self.app.show_page(p))

        self.render_hunts()
        self.render_bingo()
        self.render_team()
        self.render_breeding()
        self.render_pokemon_of_day()
        self.render_quick_actions()

    def render_hunts(self):
        body = self.card_body(self.hunts_card)
        hunts = self.app.profile.get("hunts", [])

        if not hunts:
            tk.Label(body, text="No active hunts yet.", bg=PANEL, fg=MUTED,
                     font=("Segoe UI", 9)).pack(anchor="w", pady=(2,8))
            tk.Button(body, text="Add a Hunt", command=lambda:self.app.show_page("Hunts"),
                      bg=ACCENT_2, fg="white", relief="flat",
                      padx=11, pady=6).pack(anchor="w")
            return

        for i, hunt in enumerate(hunts[:4]):
            name = str(hunt.get("pokemon","") or "").strip()
            if not name:
                continue
            row = tk.Frame(body, bg=PANEL_2)
            row.pack(fill="x", pady=2)

            species = species_by_name(self.app.pokedex, name)
            img = None
            if species:
                path = cached_sprite_path(species.get("dex"))
                if path:
                    try:
                        img = tk.PhotoImage(file=str(path))
                        if img.width() >= 80:
                            img = img.subsample(2,2)
                        self.sprite_refs[f"hunt_{i}"] = img
                    except Exception:
                        img = None

            tk.Label(row, image=img if img else "", text="" if img else "●",
                     bg=PANEL_2, fg=MUTED, width=48 if img else 4).pack(side="left", padx=6, pady=5)
            info = tk.Frame(row, bg=PANEL_2)
            info.pack(side="left", fill="x", expand=True, pady=5)
            tk.Label(info, text=name, bg=PANEL_2, fg=TEXT,
                     font=("Segoe UI Semibold", 9)).pack(anchor="w")

            if species:
                snack = pokesnack_recommendation(species)
                combo = " + ".join(x[0] for x in snack.get("combo", []))
                tk.Label(info, text=combo or "Open Spawn Finder for details",
                         bg=PANEL_2, fg=MUTED, font=("Segoe UI", 7),
                         wraplength=270, justify="left").pack(anchor="w")

            tk.Button(row, text="Spawn",
                      command=lambda n=name:self.open_spawn(n),
                      bg=PANEL_2, fg=MUTED, relief="flat",
                      padx=8, pady=5).pack(side="right", padx=5)

        if len(hunts) > 4:
            tk.Label(body, text=f"+ {len(hunts)-4} more active hunt(s)",
                     bg=PANEL, fg=MUTED, font=("Segoe UI", 7)).pack(anchor="w", pady=(4,0))

    def render_bingo(self):
        body = self.card_body(self.bingo_card)
        card = self.app.profile.get("bingo", [])
        caught = sum(1 for x in card if x.get("pokemon") and x.get("caught"))
        filled = sum(1 for x in card if x.get("pokemon"))

        top = tk.Frame(body, bg=PANEL)
        top.pack(fill="x", pady=(0,6))
        tk.Label(
            top,
            text=f"{caught} / {filled} caught",
            bg=PANEL,
            fg=TEXT,
            font=("Segoe UI Semibold", 10)
        ).pack(side="left")
        tk.Button(
            top,
            text="Open Card",
            command=lambda:self.app.show_page("Bingo"),
            bg=PANEL_2,
            fg=TEXT,
            relief="flat",
            padx=8,
            pady=5
        ).pack(side="right")

        grid = tk.Frame(body, bg=PANEL)
        grid.pack(fill="x")
        for c in range(5):
            grid.grid_columnconfigure(c, weight=1, uniform="mini_bingo")
        for r in range(5):
            grid.grid_rowconfigure(r, weight=1, uniform="mini_bingo_row")

        for i in range(25):
            item = card[i] if i < len(card) else {}
            name = str(item.get("pokemon","") or "").strip()
            done = bool(item.get("caught")) and bool(name)

            cell = tk.Frame(
                grid,
                bg=GOOD if done else PANEL_2,
                height=58
            )
            cell.grid(
                row=i//5,
                column=i%5,
                sticky="nsew",
                padx=2,
                pady=2
            )
            cell.grid_propagate(False)

            if not name:
                tk.Label(
                    cell,
                    text="—",
                    bg=PANEL_2,
                    fg=MUTED,
                    font=("Segoe UI", 9)
                ).place(relx=.5, rely=.5, anchor="center")
                continue

            species = species_by_name(self.app.pokedex, name)
            sprite = None

            if species:
                path = cached_sprite_path(species.get("dex"))
                if path:
                    try:
                        img = tk.PhotoImage(file=str(path))
                        # Mini-home Bingo should be icon-first. Target roughly 36-44px.
                        while img.width() > 44 or img.height() > 44:
                            img = img.subsample(2, 2)
                        sprite = img
                        self.sprite_refs[f"bingo_{i}"] = img
                    except Exception:
                        sprite = None

            bg = GOOD if done else PANEL_2

            if sprite:
                label = tk.Label(
                    cell,
                    image=sprite,
                    bg=bg,
                    bd=0,
                    cursor="hand2"
                )
            else:
                initials = "".join(
                    part[:1].upper()
                    for part in re.split(r"[\s\-_]+", name)
                    if part
                )[:3] or name[:2].upper()
                label = tk.Label(
                    cell,
                    text=initials,
                    bg=bg,
                    fg=TEXT,
                    font=("Segoe UI Semibold", 9),
                    cursor="hand2"
                )

            label.place(relx=.5, rely=.5, anchor="center")
            HoverTooltip(
                label,
                f"{name}\n" + ("Caught ✓" if done else "Still needed")
            )
            label.bind(
                "<Button-1>",
                lambda e: self.app.show_page("Bingo"),
                add="+"
            )

            if done:
                check = tk.Label(
                    cell,
                    text="✓",
                    bg=GOOD,
                    fg="white",
                    font=("Segoe UI Semibold", 8)
                )
                check.place(relx=1.0, rely=0.0, x=-4, y=3, anchor="ne")
                HoverTooltip(check, f"{name}\nCaught ✓")


    def current_team(self):
        page = getattr(self.app, "pages", {}).get("Teams") if getattr(self.app, "pages", None) else None
        if page and hasattr(page, "current_team"):
            try:
                return page.current_team()
            except Exception:
                pass
        teams = self.app.profile.get("teams", [])
        return teams[0] if teams else None

    def render_team(self):
        body = self.card_body(self.team_card)
        team = self.current_team()

        if not team:
            tk.Label(body, text="No saved team yet.", bg=PANEL, fg=MUTED,
                     font=("Segoe UI", 9)).pack(anchor="w", pady=(2,8))
            tk.Button(body, text="Build a Team", command=lambda:self.app.show_page("Teams"),
                      bg=ACCENT_2, fg="white", relief="flat",
                      padx=11, pady=6).pack(anchor="w")
            return

        top=tk.Frame(body,bg=PANEL); top.pack(fill="x",pady=(0,6))
        tk.Label(top,text=team.get("name","Team"),bg=PANEL,fg=TEXT,
                 font=("Segoe UI Semibold",10)).pack(side="left")
        tk.Button(top,text="Open Analysis",command=lambda:self.app.show_page("Teams"),
                  bg=PANEL_2,fg=TEXT,relief="flat",padx=8,pady=5).pack(side="right")

        row=tk.Frame(body,bg=PANEL); row.pack(fill="x")
        members=team.get("members",[]) or []
        filled=0
        for i in range(6):
            m=members[i] if i<len(members) else {}
            name=str(m.get("pokemon","") or "").strip()
            if name: filled+=1
            slot=tk.Frame(row,bg=PANEL_2)
            slot.pack(side="left",fill="x",expand=True,padx=2)
            img=None
            species=species_by_name(self.app.pokedex,name) if name else None
            if species:
                path=cached_sprite_path(species.get("dex"))
                if path:
                    try:
                        img=tk.PhotoImage(file=str(path))
                        if img.width()>=80: img=img.subsample(2,2)
                        self.sprite_refs[f"team_{i}"]=img
                    except Exception: img=None
            tk.Label(slot,image=img if img else "",text="" if img else ("+" if not name else name[:2]),
                     bg=PANEL_2,fg=MUTED,font=("Segoe UI Semibold",9)).pack(pady=(5,2))
            tk.Label(slot,text=name[:9] if name else "Empty",bg=PANEL_2,fg=TEXT if name else MUTED,
                     font=("Segoe UI",6)).pack(pady=(0,5))

        move_meta=selected_move_metadata(members,allow_network=False)
        analysis=analyze_team(members,self.app.pokedex,move_meta)
        warning=analysis["issues"][0] if analysis["issues"] else "No major quick-analysis warnings."
        tk.Label(body,text=f"{filled}/6 Pokémon   •   {warning}",
                 bg=PANEL,fg=MUTED,font=("Segoe UI",7),
                 wraplength=430,justify="left").pack(anchor="w",pady=(6,0))

    def render_breeding(self):
        body = self.card_body(self.breeding_card)
        target = str(self.app.profile.get("last_breeding_target","") or "").strip()

        if not target:
            tk.Label(body, text="No breeding project selected yet.",
                     bg=PANEL, fg=MUTED, font=("Segoe UI", 9)).pack(anchor="w", pady=(2,8))
            tk.Button(body, text="Start Planning", command=lambda:self.app.show_page("Breeding"),
                      bg=ACCENT_2, fg="white", relief="flat",
                      padx=11, pady=6).pack(anchor="w")
            return

        species=species_by_name(self.app.pokedex,target)
        row=tk.Frame(body,bg=PANEL); row.pack(fill="x")

        img=None
        if species:
            path=cached_sprite_path(species.get("dex"))
            if path:
                try:
                    img=tk.PhotoImage(file=str(path))
                    if img.width()>=80: img=img.subsample(2,2)
                    self.sprite_refs["breeding"]=img
                except Exception: img=None

        tk.Label(row,image=img if img else "",text="" if img else "●",
                 bg=PANEL,fg=MUTED).pack(side="left",padx=(0,10))
        info=tk.Frame(row,bg=PANEL); info.pack(side="left",fill="x",expand=True)
        tk.Label(info,text=target,bg=PANEL,fg=TEXT,
                 font=("Segoe UI Semibold",11)).pack(anchor="w")

        if species:
            groups=", ".join(friendly_resource_name(x) for x in species.get("egg_groups",[])) or "Unknown"
            eggmoves=species_egg_moves(species)
            tk.Label(info,text=f"Egg Groups: {groups}\n{len(eggmoves)} explicitly marked Egg move(s)",
                     bg=PANEL,fg=MUTED,font=("Segoe UI",8),
                     justify="left").pack(anchor="w",pady=(2,0))

        tk.Button(body,text="Continue Planning",command=lambda:self.open_breeding(target),
                  bg=ACCENT_2,fg="white",relief="flat",
                  padx=11,pady=6).pack(anchor="w",pady=(8,0))

    def pokemon_of_day(self):
        if not self.app.pokedex:
            return None
        # Stable within a date, changes the next day, no network/random state required.
        ordinal = date.today().toordinal()
        return self.app.pokedex[ordinal % len(self.app.pokedex)]

    def render_pokemon_of_day(self):
        body = self.card_body(self.potd_card)
        p = self.pokemon_of_day()
        if not p:
            tk.Label(
                body,
                text="Import a Cobblemon JAR to enable Pokémon of the Day.",
                bg=PANEL,fg=MUTED,font=("Segoe UI",9)
            ).pack(anchor="w")
            return

        row=tk.Frame(body,bg=PANEL)
        row.pack(fill="x")

        img=None
        path=cached_sprite_path(p.get("dex"))
        if path:
            try:
                img=tk.PhotoImage(file=str(path))
                if img.width()<=128 and img.height()<=128:
                    img=img.zoom(2,2)
                self._potd_ref=img
            except Exception:
                img=None

        # If today's Pokémon has never been viewed before, fetch its sprite once
        # in the background and refresh Home when ready.
        if not img and not self._potd_sprite_fetch_running:
            self._potd_sprite_fetch_running=True
            dex=p.get("dex")

            def worker():
                try:
                    get_cached_sprite(dex)
                except Exception:
                    pass

                def done():
                    self._potd_sprite_fetch_running=False
                    try:
                        if self.winfo_exists():
                            self.render_pokemon_of_day()
                    except Exception:
                        pass

                try:
                    self.after(0,done)
                except Exception:
                    self._potd_sprite_fetch_running=False

            threading.Thread(target=worker,daemon=True).start()

        tk.Label(
            row,
            image=img if img else "",
            text="" if img else "Loading sprite…",
            bg=PANEL,
            fg=MUTED,
            font=("Segoe UI",8)
        ).pack(side="left",padx=(0,16))

        info=tk.Frame(row,bg=PANEL)
        info.pack(side="left",fill="x",expand=True)

        tk.Label(
            info,
            text=f"#{p.get('dex',0):04d}  {p.get('name','')}",
            bg=PANEL,fg=TEXT,
            font=("Segoe UI Semibold",16)
        ).pack(anchor="w")

        tk.Label(
            info,
            text=" / ".join(p.get("types",[]))+"   •   BST "+str(species_bst(p)),
            bg=PANEL,fg=MUTED,font=("Segoe UI",9)
        ).pack(anchor="w",pady=(2,0))

        abilities=", ".join(species_ability_options(p)) or "—"
        tk.Label(
            info,text="Abilities: "+abilities,
            bg=PANEL,fg=MUTED,font=("Segoe UI",8),
            wraplength=650,justify="left"
        ).pack(anchor="w",pady=(2,0))

        entries=species_spawn_entries(self.app,p.get("name",""))
        if entries:
            habitats=[]
            for e in entries:
                for h in spawn_habitat_labels(e):
                    if h not in habitats:
                        habitats.append(h)
            if habitats:
                tk.Label(
                    info,text="Found around: "+", ".join(habitats[:6]),
                    bg=PANEL,fg=MUTED,font=("Segoe UI",8),
                    wraplength=650,justify="left"
                ).pack(anchor="w",pady=(2,0))

        tk.Button(
            row,text="View Pokédex",
            command=lambda n=p["name"]:self.app.open_pokemon_detail(n),
            bg=ACCENT_2,fg="white",relief="flat",
            padx=12,pady=7
        ).pack(side="right",padx=(12,0))


    def render_quick_actions(self):
        body = self.card_body(self.quick_card)
        actions = [
            ("Find a Pokémon", "Pokédex"),
            ("Add / View Hunts", "Hunts"),
            ("Update Bingo", "Bingo"),
            ("Build a Team", "Teams"),
            ("Plan Breeding", "Breeding"),
            ("Browse Database", "Database"),
        ]
        for text, page in actions:
            tk.Button(
                body, text=text,
                command=lambda p=page:self.app.show_page(p),
                bg=PANEL_2, fg=TEXT,
                activebackground=ACCENT_2, activeforeground="white",
                relief="flat", padx=12, pady=8
            ).pack(side="left", padx=(0,6), pady=2)

    def open_spawn(self, pokemon):
        self.app.show_page("Spawn Finder")
        page=self.app.pages.get("Spawn Finder")
        if page and hasattr(page,"focus_pokemon"):
            page.focus_pokemon(pokemon)

    def open_breeding(self, pokemon):
        self.app.show_page("Breeding")
        page=self.app.pages.get("Breeding")
        if page and hasattr(page,"focus_pokemon"):
            page.focus_pokemon(pokemon)


class HoverTooltip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tip = None
        widget.bind("<Enter>", self.show, add="+")
        widget.bind("<Leave>", self.hide, add="+")
    def show(self, _=None):
        if self.tip or not self.text:
            return
        try:
            x = self.widget.winfo_rootx() + 20
            y = self.widget.winfo_rooty() + self.widget.winfo_height() + 4
            self.tip = tk.Toplevel(self.widget)
            self.tip.wm_overrideredirect(True)
            self.tip.wm_geometry(f"+{x}+{y}")
            tk.Label(
                self.tip, text=self.text,
                bg="#111820", fg="white",
                relief="solid", bd=1,
                padx=7, pady=4,
                font=("Segoe UI", 8)
            ).pack()
        except Exception:
            self.tip = None
    def hide(self, _=None):
        if self.tip:
            try:
                self.tip.destroy()
            except Exception:
                pass
            self.tip = None

class ReferenceDetailWindow(tk.Toplevel):
    def __init__(self, app, kind, name):
        super().__init__(app)
        self.app = app
        self.kind = kind
        self.name = name
        self._loading = False
        self._recipe_hover_tip = None
        self._recipe_hover_region = None

        self.title(f"{name} — {kind}")
        self.configure(bg=BG)
        self.geometry("1040x780")
        self.minsize(900, 650)
        self.transient(app)

        top = tk.Frame(self, bg=BG)
        top.pack(fill="x", padx=20, pady=(18, 10))

        tk.Label(
            top, text=name,
            bg=BG, fg=TEXT,
            font=("Segoe UI Semibold", 22)
        ).pack(side="left")

        tk.Label(
            top, text=kind.upper(),
            bg=PANEL_2, fg=MUTED,
            font=("Segoe UI Semibold", 8),
            padx=8, pady=4
        ).pack(side="left", padx=(10, 0))

        self.loading_label = tk.Label(
            top, text="",
            bg=BG, fg=MUTED,
            font=("Segoe UI", 8)
        )
        self.loading_label.pack(side="right")

        outer = tk.Frame(self, bg=BG)
        outer.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        self.canvas = tk.Canvas(outer, bg=BG, highlightthickness=0)
        scroll = tk.Scrollbar(outer, orient="vertical", command=self.canvas.yview)
        self.body = tk.Frame(self.canvas, bg=BG)
        win = self.canvas.create_window((0, 0), window=self.body, anchor="nw")

        self.body.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        self.canvas.bind(
            "<Configure>",
            lambda e: self.canvas.itemconfigure(win, width=e.width)
        )
        self.canvas.configure(yscrollcommand=scroll.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        self.render()
        self.after(50, self.auto_load_missing_details)

    def section(self, title):
        box = tk.Frame(self.body, bg=PANEL)
        box.pack(fill="x", pady=5)
        tk.Label(
            box, text=title,
            bg=PANEL, fg=TEXT,
            font=("Segoe UI Semibold", 12)
        ).pack(anchor="w", padx=14, pady=(10, 6))
        return box

    def auto_load_missing_details(self):
        if self._loading:
            return

        needs_load = False
        if self.kind == "Move":
            needs_load = get_move_metadata(self.name, False) is None
        elif self.kind == "Ability":
            needs_load = move_slug(self.name) not in load_simple_db(ABILITY_DB_FILE)
        elif self.kind == "Item":
            # Local Cobblemon details are always loaded automatically. Standard
            # Pokémon metadata is fetched too when not already cached.
            needs_load = True

        if not needs_load:
            return

        self._loading = True
        self.loading_label.config(text="Loading details…")

        def worker():
            try:
                if self.kind == "Move":
                    get_move_metadata(self.name, True)
                elif self.kind == "Ability":
                    fetch_named_api_resource("ability", self.name)
                elif self.kind == "Item":
                    get_local_item_details(self.app, self.name)
                    # Supplement standard Pokémon items with effect text when available.
                    if move_slug(self.name) not in load_simple_db(ITEM_DB_FILE):
                        fetch_named_api_resource("item", self.name)
            finally:
                def done():
                    self._loading = False
                    self.loading_label.config(text="")
                    self.render()
                try:
                    self.after(0, done)
                except Exception:
                    pass

        threading.Thread(target=worker, daemon=True).start()

    def render(self):
        for w in self.body.winfo_children():
            w.destroy()

        if self.kind == "Move":
            self.render_move()
        elif self.kind == "Ability":
            self.render_ability()
        else:
            self.render_item()

    def render_move(self):
        meta = get_move_metadata(self.name, False)
        box = self.section("Move Details")
        if meta:
            line = (
                f"Type: {meta.get('type','—')}   •   "
                f"Category: {meta.get('category','—')}   •   "
                f"Power: {meta.get('power') or '—'}   •   "
                f"Accuracy: {meta.get('accuracy') or '—'}   •   "
                f"Priority: {meta.get('priority',0)}"
            )
            tk.Label(
                box, text=line,
                bg=PANEL, fg=TEXT,
                font=("Segoe UI", 9),
                wraplength=680, justify="left"
            ).pack(anchor="w", padx=14, pady=(0, 10))
        else:
            tk.Label(
                box, text="Move details are loading automatically…",
                bg=PANEL, fg=MUTED, font=("Segoe UI", 9)
            ).pack(anchor="w", padx=14, pady=(0, 10))

        self.pokemon_list(
            indexed_pokemon_learning_move(self.app, self.name),
            "Implemented Pokémon that can learn this move"
        )

    def render_ability(self):
        info = load_simple_db(ABILITY_DB_FILE).get(move_slug(self.name))
        box = self.section("Ability Effect")

        text_value = info.get("effect") if info else ""
        tk.Label(
            box,
            text=text_value or "Ability details are loading automatically…",
            bg=PANEL,
            fg=TEXT if text_value else MUTED,
            font=("Segoe UI", 9),
            wraplength=680,
            justify="left"
        ).pack(anchor="w", padx=14, pady=(0, 10))

        self.pokemon_list(
            indexed_pokemon_with_ability(self.app, self.name),
            "Implemented Pokémon with this ability"
        )

    def render_item(self):
        entry = find_item_index_entry(self.app, self.name)
        local_cache = load_item_detail_cache()
        local = None
        if entry:
            local = local_cache.get(str(entry.get("id","")).lower())

        api = load_simple_db(ITEM_DB_FILE).get(move_slug(self.name))

        # Overview.
        box = self.section("Item Overview")
        category = (entry or {}).get("category") or (local or {}).get("category") or (api or {}).get("category") or "Other"
        tk.Label(
            box,
            text=f"Category: {category}",
            bg=PANEL, fg=MUTED,
            font=("Segoe UI", 9)
        ).pack(anchor="w", padx=14, pady=(0, 5))

        descriptions = []
        for value in (local or {}).get("descriptions", []) or []:
            if value not in descriptions:
                descriptions.append(value)
        if api and api.get("effect") and api.get("effect") not in descriptions:
            descriptions.append(api.get("effect"))

        if descriptions:
            for desc in descriptions[:4]:
                tk.Label(
                    box,
                    text=desc,
                    bg=PANEL, fg=TEXT,
                    font=("Segoe UI", 9),
                    wraplength=680,
                    justify="left"
                ).pack(anchor="w", padx=14, pady=2)
        else:
            tk.Label(
                box,
                text="Item description is loading automatically…" if self._loading else "No item description was found in the installed Cobblemon data.",
                bg=PANEL, fg=MUTED,
                font=("Segoe UI", 9)
            ).pack(anchor="w", padx=14, pady=2)

        tk.Frame(box, bg=PANEL, height=8).pack()

        # Crafting recipes.
        box = self.section("Crafting / Recipe")
        recipes = (local or {}).get("recipes", []) if local else []

        if not local and self._loading:
            tk.Label(
                box, text="Checking the installed Cobblemon JAR for recipes…",
                bg=PANEL, fg=MUTED, font=("Segoe UI", 9)
            ).pack(anchor="w", padx=14, pady=(0, 10))
        elif not recipes:
            tk.Label(
                box,
                text="No crafting recipe for this item was found in the installed Cobblemon JAR.",
                bg=PANEL, fg=MUTED, font=("Segoe UI", 9)
            ).pack(anchor="w", padx=14, pady=(0, 10))
        else:
            for i, recipe in enumerate(recipes, start=1):
                sub = tk.Frame(box, bg=PANEL_2)
                sub.pack(fill="x", padx=12, pady=5)

                heading = f"Recipe {i}" if len(recipes) > 1 else "Recipe"
                tk.Label(
                    sub,
                    text=heading,
                    bg=PANEL_2,
                    fg=TEXT,
                    font=("Segoe UI Semibold", 10)
                ).pack(anchor="w", padx=10, pady=(8, 4))

                # Visual station renderer replaces the old line-of-text recipe.
                station = tk.Frame(sub, bg=PANEL)
                station.pack(fill="x", padx=8, pady=(0, 8))
                self.render_visual_recipe(station, recipe)

                # Keep technical recipe type only as subtle secondary info.
                tk.Label(
                    sub,
                    text=f"Recipe type: {recipe.get('type','Unknown')}",
                    bg=PANEL_2,
                    fg=MUTED,
                    font=("Segoe UI", 7)
                ).pack(anchor="w", padx=10, pady=(0, 7))

    def render_visual_recipe(self, parent, recipe):
        kind = recipe_station_kind(recipe)

        try:
            image = compose_recipe_image(self.app, recipe, kind, self.name)
        except Exception:
            image = None

        if image is None:
            return self.render_generic_station(parent, recipe)

        try:
            self._recipe_composite_ref = ImageTk.PhotoImage(image)
            regions = recipe_interactive_regions(recipe, kind, self.name)

            lbl = tk.Label(
                parent,
                image=self._recipe_composite_ref,
                bg=PANEL,
                bd=0,
                cursor="arrow"
            )
            lbl.pack(anchor="w", padx=12, pady=(4, 10))
        except Exception:
            return self.render_generic_station(parent, recipe)

        def region_at(event):
            for region in regions:
                if (
                    region["x1"] <= event.x <= region["x2"]
                    and region["y1"] <= event.y <= region["y2"]
                ):
                    return region
            return None

        def hide_tip():
            if self._recipe_hover_tip:
                try:
                    self._recipe_hover_tip.destroy()
                except Exception:
                    pass
                self._recipe_hover_tip = None
            self._recipe_hover_region = None
            try:
                lbl.config(cursor="arrow")
            except Exception:
                pass

        def show_tip(event, region):
            # Do not constantly recreate the same tooltip while moving within a slot.
            if self._recipe_hover_region is region and self._recipe_hover_tip:
                return

            hide_tip()
            self._recipe_hover_region = region

            try:
                tip = tk.Toplevel(self)
                tip.wm_overrideredirect(True)
                sx = lbl.winfo_rootx() + event.x + 14
                sy = lbl.winfo_rooty() + event.y + 16
                tip.wm_geometry(f"+{sx}+{sy}")

                tooltip_text = region["label"]
                if region.get("clickable"):
                    tooltip_text += "\nClick for item details"

                tk.Label(
                    tip,
                    text=tooltip_text,
                    bg="#111820",
                    fg="white",
                    relief="solid",
                    bd=1,
                    padx=8,
                    pady=5,
                    justify="left",
                    font=("Segoe UI", 8)
                ).pack()

                self._recipe_hover_tip = tip
                lbl.config(cursor="hand2" if region.get("clickable") else "arrow")
            except Exception:
                self._recipe_hover_tip = None

        def on_motion(event):
            region = region_at(event)
            if region:
                show_tip(event, region)
            else:
                hide_tip()

        def on_click(event):
            region = region_at(event)
            if not region or not region.get("clickable"):
                return

            label = region["label"]

            # Avoid opening the exact same item window again when clicking output.
            if region.get("output") and label.casefold() == self.name.casefold():
                return

            self.app.open_reference_detail("Item", label)

        lbl.bind("<Motion>", on_motion)
        lbl.bind("<Leave>", lambda e: hide_tip())
        lbl.bind("<Button-1>", on_click)

        requirements = []
        for value in recipe.get("ingredients", []) or []:
            if str(value).startswith("Any "):
                requirements.append(str(value))
        for value in (recipe.get("key", {}) or {}).values():
            if str(value).startswith("Any ") and str(value) not in requirements:
                requirements.append(str(value))

        if requirements:
            tk.Label(
                parent,
                text="Accepts: " + " • ".join(requirements),
                bg=PANEL,
                fg=MUTED,
                font=("Segoe UI", 8),
                justify="left",
                wraplength=700
            ).pack(anchor="w", padx=12, pady=(0, 6))


    def render_generic_station(self, parent, recipe):
        """Always-visible fallback for any serializer or rendering failure."""
        area = tk.Frame(parent, bg=PANEL)
        area.pack(fill="x", padx=12, pady=(2, 10))

        pattern = recipe.get("pattern", []) or []
        key = recipe.get("key", {}) or {}
        ingredients = recipe.get("ingredients", []) or []

        if pattern:
            grid = tk.Frame(area, bg=PANEL)
            grid.pack(anchor="w", pady=(0, 6))

            for r in range(3):
                row = pattern[r] if r < len(pattern) else ""
                for c in range(3):
                    sym = row[c] if c < len(row) else " "
                    value = "" if sym == " " else key.get(sym, sym)

                    cell = tk.Frame(
                        grid,
                        bg=PANEL_2,
                        width=84,
                        height=56
                    )
                    cell.grid(row=r, column=c, padx=2, pady=2)
                    cell.grid_propagate(False)

                    tk.Label(
                        cell,
                        text=short_slot_text(value, 20) if value else "",
                        bg=PANEL_2,
                        fg=TEXT,
                        font=("Segoe UI", 8),
                        justify="center",
                        wraplength=76
                    ).place(relx=.5, rely=.5, anchor="center")

        elif ingredients:
            tk.Label(
                area,
                text="Ingredients: " + " + ".join(ingredients),
                bg=PANEL,
                fg=TEXT,
                font=("Segoe UI", 9),
                wraplength=700,
                justify="left"
            ).pack(anchor="w")

        for line in recipe.get("extra", []) or []:
            tk.Label(
                area,
                text=line,
                bg=PANEL,
                fg=MUTED,
                font=("Segoe UI", 8)
            ).pack(anchor="w", pady=1)

    def pokemon_list(self, mons, title):
        box = self.section(f"{title} ({len(mons)})")
        holder = tk.Frame(box, bg=PANEL)
        holder.pack(fill="x", padx=10, pady=(0, 10))

        for i, p in enumerate(mons[:60]):
            tk.Button(
                holder,
                text=p["name"],
                command=lambda n=p["name"]: self.app.open_pokemon_detail(n),
                bg=PANEL_2, fg=TEXT,
                relief="flat", padx=6, pady=5
            ).grid(row=i//5, column=i%5, sticky="ew", padx=2, pady=2)

        for c in range(5):
            holder.grid_columnconfigure(c, weight=1)



# ---------------------------------------------------------------------------
# V1.4.1 — Embedded Database detail page
# ---------------------------------------------------------------------------

class EmbeddedReferenceDetailPage(tk.Frame):
    section = ReferenceDetailWindow.section
    auto_load_missing_details = ReferenceDetailWindow.auto_load_missing_details
    render = ReferenceDetailWindow.render
    render_move = ReferenceDetailWindow.render_move
    render_ability = ReferenceDetailWindow.render_ability
    render_item = ReferenceDetailWindow.render_item
    render_visual_recipe = ReferenceDetailWindow.render_visual_recipe
    render_generic_station = ReferenceDetailWindow.render_generic_station

    def __init__(self, master, app, kind, name):
        super().__init__(master, bg=BG)
        self.app=app
        self.kind=kind
        self.name=name
        self._loading=False
        self._recipe_hover_tip=None
        self._recipe_hover_region=None

        top=tk.Frame(self,bg=BG)
        top.pack(fill="x",padx=20,pady=(14,10))

        tk.Button(
            top,text="← Back",command=self.app.go_back,
            bg=PANEL_2,fg=TEXT,relief="flat",padx=12,pady=7
        ).pack(side="left",padx=(0,12))

        tk.Label(
            top,text=name,bg=BG,fg=TEXT,
            font=("Segoe UI Semibold",22)
        ).pack(side="left")

        tk.Label(
            top,text=kind.upper(),bg=PANEL_2,fg=MUTED,
            font=("Segoe UI Semibold",8),padx=8,pady=4
        ).pack(side="left",padx=(10,0))

        self.loading_label=tk.Label(
            top,text="",bg=BG,fg=MUTED,font=("Segoe UI",8)
        )
        self.loading_label.pack(side="right")

        outer=tk.Frame(self,bg=BG)
        outer.pack(fill="both",expand=True,padx=20,pady=(0,20))
        self.canvas=tk.Canvas(outer,bg=BG,highlightthickness=0)
        scroll=tk.Scrollbar(outer,orient="vertical",command=self.canvas.yview)
        self.body=tk.Frame(self.canvas,bg=BG)
        win=self.canvas.create_window((0,0),window=self.body,anchor="nw")
        self.body.bind("<Configure>",lambda e:self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>",lambda e:self.canvas.itemconfigure(win,width=e.width))
        self.canvas.configure(yscrollcommand=scroll.set)
        self.canvas.pack(side="left",fill="both",expand=True)
        scroll.pack(side="right",fill="y")

        self.render()
        self.after(50,self.auto_load_missing_details)

    def pokemon_list(self, mons, title):
        box=self.section(f"{title} ({len(mons)})")
        holder=tk.Frame(box,bg=PANEL)
        holder.pack(fill="x",padx=10,pady=(0,10))
        for i,p in enumerate(mons[:60]):
            tk.Button(
                holder,text=p["name"],
                command=lambda n=p["name"]:self.app.open_pokemon_detail(n),
                bg=PANEL_2,fg=TEXT,relief="flat",padx=6,pady=5
            ).grid(row=i//5,column=i%5,sticky="ew",padx=2,pady=2)
        for c in range(5):
            holder.grid_columnconfigure(c,weight=1)


class GlobalSearchWindow(tk.Toplevel):
    def __init__(self,app,initial_query=""):
        super().__init__(app);self.app=app;self.results=[]
        self.title("Search Cobblemon Companion");self.configure(bg=BG);self.geometry("620x560");self.transient(app)
        tk.Label(self,text="Search Everything",bg=BG,fg=TEXT,font=("Segoe UI Semibold",19)).pack(anchor="w",padx=18,pady=(18,4))
        tk.Label(self,text="Pokémon • Moves • Abilities • Known Items",bg=BG,fg=MUTED).pack(anchor="w",padx=18,pady=(0,8))
        self.q=tk.StringVar(value=initial_query);e=tk.Entry(self,textvariable=self.q,bg=PANEL,fg=TEXT,insertbackground=TEXT,relief="flat",font=("Segoe UI",12))
        e.pack(fill="x",padx=18,ipady=8);e.focus_set()
        self._search_after=None
        e.bind("<KeyRelease>",lambda x:self.schedule_refresh())
        self.lb=tk.Listbox(self,bg=PANEL,fg=TEXT,selectbackground=ACCENT_2,selectforeground="white",relief="flat",font=("Segoe UI",10))
        self.lb.pack(fill="both",expand=True,padx=18,pady=10);self.lb.bind("<Double-Button-1>",lambda e:self.open());self.lb.bind("<Return>",lambda e:self.open())
        tk.Button(self,text="Open",command=self.open,bg=ACCENT_2,fg="white",relief="flat",padx=14,pady=8).pack(anchor="e",padx=18,pady=(0,18))
        if initial_query:
            self.refresh()
    def schedule_refresh(self):
        if self._search_after is not None:
            try:self.after_cancel(self._search_after)
            except Exception:pass
        self._search_after=self.after(160,self.refresh)
    def refresh(self):
        self._search_after=None
        self.results=global_search_entries(self.app,self.q.get());self.lb.delete(0,"end")
        for kind,name,_ in self.results:self.lb.insert("end",f"{kind:<10}  {name}")
    def open(self):
        sel=self.lb.curselection()
        if not sel:return
        kind,name,_=self.results[sel[0]]
        try:self.destroy()
        except Exception:pass
        if kind=="Pokémon":
            self.app.open_pokemon_detail(name)
        else:
            self.app.open_reference_detail(kind,name)

class PokemonDetailWindow(tk.Toplevel):
    """Pokédex 2.0 — central Pokémon hub with tabbed, cross-linked data."""
    TABS = ("Overview", "Spawns", "Moves", "Evolution", "Breeding", "Competitive")

    def __init__(self, app, pokemon_name):
        super().__init__(app)
        self.app = app
        self.pokemon_name = pokemon_name
        self.species = species_by_name(app.pokedex, pokemon_name)
        self.active_tab = "Overview"
        self.sprite_ref = None

        self.title(f"{pokemon_name} — Pokédex 2.0")
        self.configure(bg=BG)
        self.geometry("1080x800")
        self.minsize(920, 680)
        self.transient(app)

        self.build_header()
        self.build_tabs()

        self.status_line = tk.Label(self, text="", bg=BG, fg=MUTED, font=("Segoe UI", 9))
        self.status_line.pack(anchor="w", padx=22, pady=(6, 6))

        content = tk.Frame(self, bg=BG)
        content.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        self.canvas = tk.Canvas(content, bg=BG, highlightthickness=0)
        scroll = tk.Scrollbar(content, orient="vertical", command=self.canvas.yview)
        self.body = tk.Frame(self.canvas, bg=BG)
        self.body_win = self.canvas.create_window((0,0), window=self.body, anchor="nw")
        self.body.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfigure(self.body_win, width=e.width))
        self.canvas.configure(yscrollcommand=scroll.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        self.render_tab()

    def build_header(self):
        top = tk.Frame(self, bg=BG)
        top.pack(fill="x", padx=20, pady=(18, 10))

        if self.species:
            path = cached_sprite_path(self.species.get("dex"))
            if path:
                try:
                    img = tk.PhotoImage(file=str(path))
                    if img.width() <= 128 and img.height() <= 128:
                        img = img.zoom(2, 2)
                    self.sprite_ref = img
                    tk.Label(top, image=img, bg=BG, bd=0).pack(side="left", padx=(0, 16))
                except Exception:
                    pass

        titlebox = tk.Frame(top, bg=BG)
        titlebox.pack(side="left", fill="x", expand=True)

        dex = self.species.get("dex", 0) if self.species else 0
        tk.Label(titlebox, text=f"#{int(dex):04d}", bg=BG, fg=MUTED,
                 font=("Segoe UI Semibold", 10)).pack(anchor="w")
        tk.Label(titlebox, text=self.pokemon_name, bg=BG, fg=TEXT,
                 font=("Segoe UI Semibold", 28)).pack(anchor="w")

        type_row = tk.Frame(titlebox, bg=BG)
        type_row.pack(anchor="w", pady=(5, 5))
        for t in (self.species or {}).get("types", []):
            tk.Label(type_row, text=t.upper(), bg=TYPE_COLORS.get(t, CARD), fg="white",
                     padx=11, pady=4, font=("Segoe UI", 8, "bold")).pack(side="left", padx=(0, 4))

        bst = species_bst(self.species) if self.species else 0
        abilities = ", ".join(species_ability_options(self.species or {})) or "—"
        if self.species and self.species.get("is_form"):
            tk.Label(
                titlebox,
                text=f"Form of {self.species.get('base_species','')}",
                bg=BG, fg=MUTED,
                font=("Segoe UI",8)
            ).pack(anchor="w", pady=(0,2))
        tk.Label(titlebox, text=f"BST {bst}   •   {abilities}", bg=BG, fg=MUTED,
                 font=("Segoe UI", 9), wraplength=580, justify="left").pack(anchor="w")

        actions = tk.Frame(top, bg=BG)
        actions.pack(side="right")
        buttons = [
            ("Find Spawns", self.open_spawns, ACCENT_2),
            ("Toggle Owned", self.toggle_owned, PANEL_2),
            ("Toggle Hunt", self.toggle_hunt, PANEL_2),
            ("Add to Team", self.add_to_team, PANEL_2),
        ]
        for label, cmd, color in buttons:
            tk.Button(actions, text=label, command=cmd, bg=color, fg="white" if color==ACCENT_2 else TEXT,
                      relief="flat", padx=12, pady=7).pack(fill="x", pady=2)

    def build_tabs(self):
        self.tabbar = tk.Frame(self, bg=BG)
        self.tabbar.pack(fill="x", padx=20, pady=(0, 0))
        self.tab_buttons = {}
        for tab in self.TABS:
            b = tk.Button(self.tabbar, text=tab, command=lambda t=tab:self.set_tab(t),
                          bg=PANEL_2, fg=TEXT, relief="flat", padx=14, pady=8,
                          font=("Segoe UI Semibold", 9))
            b.pack(side="left", padx=(0, 4))
            self.tab_buttons[tab] = b
        self.update_tab_buttons()

    def update_tab_buttons(self):
        for tab, button in self.tab_buttons.items():
            button.config(bg=ACCENT_2 if tab == self.active_tab else PANEL_2,
                          fg="white" if tab == self.active_tab else TEXT)

    def set_tab(self, tab):
        self.active_tab = tab
        self.update_tab_buttons()
        self.render_tab()

    def section(self, title, subtitle=None):
        box = tk.Frame(self.body, bg=PANEL)
        box.pack(fill="x", pady=5)
        tk.Label(box, text=title, bg=PANEL, fg=TEXT,
                 font=("Segoe UI Semibold", 13)).pack(anchor="w", padx=14, pady=(10, 2 if subtitle else 6))
        if subtitle:
            tk.Label(box, text=subtitle, bg=PANEL, fg=MUTED,
                     font=("Segoe UI", 8), wraplength=920, justify="left").pack(anchor="w", padx=14, pady=(0, 7))
        return box

    def refresh_status(self):
        s = species_user_status(self.app, self.pokemon_name)
        bits = [
            "Owned ✓" if s["owned"] else "Missing from Collection",
            "Active Hunt ✓" if s["hunted"] else "Not in Hunts",
        ]
        if s["bingo_caught"]:
            bits.append("Weekly Bingo: caught ✓")
        elif s["bingo"]:
            bits.append("Weekly Bingo: still needed")
        self.status_line.config(text="   •   ".join(bits))

    def render_tab(self):
        for w in self.body.winfo_children():
            w.destroy()
        self.refresh_status()
        if not self.species:
            return
        getattr(self, "render_" + self.active_tab.lower())()
        self.canvas.yview_moveto(0)

    def render_overview(self):
        s = self.species
        box = self.section("Species Overview", "Core information imported from the installed Cobblemon build.")
        egg = ", ".join(friendly_resource_name(x) for x in s.get("egg_groups", [])) or "—"
        rows = [
            ("Abilities", ", ".join(species_ability_options(s)) or "—"),
            ("Egg Groups", egg),
            ("Catch Rate", str(s.get("catch_rate","—"))),
            ("Growth Rate", friendly_resource_name(s.get("experience_group","")) or "—"),
            ("Base Stat Total", str(species_bst(s))),
        ]
        grid=tk.Frame(box,bg=PANEL); grid.pack(fill="x",padx=14,pady=(0,10))
        for i,(label,value) in enumerate(rows):
            c=tk.Frame(grid,bg=PANEL_2); c.grid(row=i//3,column=i%3,sticky="nsew",padx=3,pady=3)
            grid.grid_columnconfigure(i%3,weight=1)
            tk.Label(c,text=label,bg=PANEL_2,fg=MUTED,font=("Segoe UI",8)).pack(anchor="w",padx=9,pady=(7,1))
            tk.Label(c,text=value,bg=PANEL_2,fg=TEXT,font=("Segoe UI Semibold",9),
                     wraplength=260,justify="left").pack(anchor="w",padx=9,pady=(0,7))

        box = self.section("Base Stats")
        stats=[("HP","hp"),("Attack","atk"),("Defense","def"),("Sp. Atk","spa"),("Sp. Def","spd"),("Speed","spe")]
        for label,key in stats:
            row=tk.Frame(box,bg=PANEL); row.pack(fill="x",padx=14,pady=4)
            val=int(s.get(key,0) or 0)
            tk.Label(row,text=label,width=10,anchor="w",bg=PANEL,fg=MUTED,font=("Segoe UI",9,"bold")).pack(side="left")
            tk.Label(row,text=str(val),width=4,anchor="e",bg=PANEL,fg=TEXT,font=("Segoe UI",9)).pack(side="left",padx=(0,10))
            bgbar=tk.Frame(row,bg=CARD,height=10); bgbar.pack(side="left",fill="x",expand=True)
            tk.Frame(bgbar,bg=ACCENT_2,height=10).place(relx=0,rely=0,relheight=1,relwidth=min(val/180,1))
        tk.Frame(box,bg=PANEL,height=8).pack()

        box=self.section("Defensive Matchups")
        prof=species_defensive_profile(s)
        for title,vals in (
            ("Weak to", [f"{t} ×{m:g}" for t,m in prof["weak"]]),
            ("Resists", [f"{t} ×{m:g}" for t,m in prof["resist"]]),
            ("Immune to", prof["immune"]),
        ):
            tk.Label(box,text=f"{title}: "+(", ".join(vals) or "None"),bg=PANEL,fg=TEXT,
                     font=("Segoe UI",9),wraplength=920,justify="left").pack(anchor="w",padx=14,pady=2)
        tk.Frame(box,bg=PANEL,height=8).pack()

    def render_spawns(self):
        s=self.species
        entries=species_spawn_entries(self.app,self.pokemon_name)
        status_kind, status_label = species_spawn_status(self.app, self.pokemon_name)
        box=self.section("Natural Spawns", status_label)

        if not entries:
            notice=tk.Frame(box,bg=PANEL_2); notice.pack(fill="x",padx=12,pady=(0,10))
            tk.Label(notice,text="No standard natural spawn rule was found for this Pokémon.",
                     bg=PANEL_2,fg=TEXT,font=("Segoe UI Semibold",10)).pack(anchor="w",padx=12,pady=(10,3))
            if status_kind == "addon-no-spawn":
                explanation=("This Pokémon was contributed by an installed addon, but Companion did not find a "
                             "normal Cobblemon spawn_pool_world rule for it. The addon may obtain it through an "
                             "event, structure, custom mechanic, command, or server-side datapack.")
            else:
                explanation=("The species exists in your installed Cobblemon data, but Companion did not find a "
                             "standard spawn_pool_world rule for it. It may be unobtainable by normal wild spawning, "
                             "or it may come from an event, structure, addon mechanic, command, or server-side datapack.")
            tk.Label(notice,text=explanation,bg=PANEL_2,fg=MUTED,font=("Segoe UI",8),
                     wraplength=900,justify="left").pack(anchor="w",padx=12,pady=(0,10))
        else:
            for i,e in enumerate(entries[:30],1):
                card=tk.Frame(box,bg=PANEL_2); card.pack(fill="x",padx=12,pady=3)
                habitats=", ".join(spawn_habitat_labels(e)) or "General / unspecified"
                bucket=friendly_bucket(e.get("bucket")) if e.get("bucket") else "—"
                level=friendly_level(e.get("level")) if e.get("level") not in (None,"",{},[]) else "—"
                source_kind, source_label = spawn_source_info(self.app, e)
                top=tk.Frame(card,bg=PANEL_2); top.pack(fill="x",padx=10,pady=(7,2))
                tk.Label(top,text=f"Rule {i}   •   {bucket}   •   Levels {level}",
                         bg=PANEL_2,fg=TEXT,font=("Segoe UI Semibold",9)).pack(side="left")
                tk.Label(top,text=source_label,bg=PANEL_2,
                         fg=ACCENT if source_kind=="base" else GOOD,
                         font=("Segoe UI Semibold",8)).pack(side="right")
                tk.Label(card,text=habitats,bg=PANEL_2,fg=MUTED,font=("Segoe UI",8),
                         wraplength=900,justify="left").pack(anchor="w",padx=10,pady=(0,7))

        box=self.section("Poké Snack Recommendation")
        snack=pokesnack_recommendation(s)
        tk.Label(box,text="Suggested seasonings: "+(" + ".join(x[0] for x in snack.get("combo",[])) or "—"),
                 bg=PANEL,fg=TEXT,font=("Segoe UI Semibold",9)).pack(anchor="w",padx=14,pady=(0,4))
        for berry,effect in snack.get("targeting",[]):
            tk.Label(box,text=f"{berry} — {effect}",bg=PANEL,fg=MUTED,font=("Segoe UI",8)).pack(anchor="w",padx=14,pady=1)
        if entries:
            tk.Button(box,text="Open in Spawn Finder",command=self.open_spawns,bg=ACCENT_2,fg="white",
                      relief="flat",padx=12,pady=7).pack(anchor="w",padx=14,pady=(8,10))
        else:
            tk.Label(box,text="Poké Snack suggestions are based on this Pokémon's type and Egg Group. "
                              "They do not mean the Pokémon has a standard natural spawn.",
                     bg=PANEL,fg=MUTED,font=("Segoe UI",8),wraplength=900,justify="left"
                     ).pack(anchor="w",padx=14,pady=(8,10))


    def render_moves(self):
        s=self.species
        moves=species_move_options(s)
        box=self.section("Learnset", f"{len(moves)} learnable moves imported for {self.pokemon_name}. Click a move to open its Database entry.")
        if not moves:
            tk.Label(box,text="No learnset data found.",bg=PANEL,fg=MUTED,font=("Segoe UI",9)).pack(anchor="w",padx=14,pady=(0,10))
            return
        holder=tk.Frame(box,bg=PANEL); holder.pack(fill="x",padx=10,pady=(0,10))
        for i,move in enumerate(moves[:120]):
            tk.Button(holder,text=move,command=lambda m=move:self.app.open_reference_detail("Move", m),
                      bg=PANEL_2,fg=TEXT,relief="flat",padx=6,pady=5).grid(row=i//5,column=i%5,sticky="ew",padx=2,pady=2)
        for c in range(5): holder.grid_columnconfigure(c,weight=1)
        if len(moves)>120:
            tk.Label(box,text=f"Showing first 120 of {len(moves)} moves.",bg=PANEL,fg=MUTED,font=("Segoe UI",8)).pack(anchor="w",padx=14,pady=(0,8))

    def render_evolution(self):
        s=self.species
        box=self.section("Evolution Family", "Evolution requirements come from the installed Cobblemon species data.")
        lines=pretty_evolution_text(s)
        for line in lines:
            tk.Label(box,text=line,bg=PANEL,fg=TEXT,font=("Segoe UI",10),
                     wraplength=900,justify="left").pack(anchor="w",padx=14,pady=4)
        tk.Frame(box,bg=PANEL,height=6).pack()

        # Cross-link any implemented Pokémon names mentioned by the evolution text.
        related=[]
        joined=" ".join(lines).casefold()
        for p in self.app.pokedex:
            if p["name"].casefold()!=self.pokemon_name.casefold() and p["name"].casefold() in joined:
                related.append(p["name"])
        if related:
            links=self.section("Related Pokémon")
            for name in related[:12]:
                tk.Button(links,text=name,command=lambda n=name:self.open_related_pokemon(n),
                          bg=PANEL_2,fg=TEXT,relief="flat",padx=10,pady=6).pack(side="left",padx=4,pady=(0,10))

    def render_breeding(self):
        s=self.species
        box=self.section("Breeding", "This is the Pokédex-side foundation for the upcoming full Breeding Planner.")
        groups=[friendly_resource_name(x) for x in s.get("egg_groups",[])]
        tk.Label(box,text="Egg Groups: "+(", ".join(groups) or "Unknown / not breedable"),
                 bg=PANEL,fg=TEXT,font=("Segoe UI Semibold",10)).pack(anchor="w",padx=14,pady=(0,5))

        # Compatible implemented species by shared egg group.
        own={str(x).lower() for x in s.get("egg_groups",[]) if x}
        compatible=[]
        if own:
            for p in self.app.pokedex:
                if p["name"].casefold()==self.pokemon_name.casefold(): continue
                theirs={str(x).lower() for x in p.get("egg_groups",[]) if x}
                if own & theirs:
                    compatible.append(p)
        tk.Label(box,text=f"{len(compatible)} implemented Pokémon share at least one egg group.",
                 bg=PANEL,fg=MUTED,font=("Segoe UI",9)).pack(anchor="w",padx=14,pady=(0,8))

        holder=tk.Frame(box,bg=PANEL); holder.pack(fill="x",padx=10,pady=(0,10))
        for i,p in enumerate(compatible[:40]):
            tk.Button(holder,text=p["name"],command=lambda n=p["name"]:self.open_related_pokemon(n),
                      bg=PANEL_2,fg=TEXT,relief="flat",padx=6,pady=5).grid(row=i//5,column=i%5,sticky="ew",padx=2,pady=2)
        for c in range(5): holder.grid_columnconfigure(c,weight=1)

        tk.Button(
            box, text="Open in Breeding Planner",
            command=self.open_breeding_planner,
            bg=ACCENT_2, fg="white", relief="flat",
            padx=12, pady=7
        ).pack(anchor="w", padx=14, pady=(0,10))

        box=self.section("Egg / Inherited Moves")
        # Current species_move_options includes the complete imported learnset; surface
        # a safe handoff rather than mislabeling methods the source didn't preserve.
        moves=species_move_options(s)
        tk.Label(box,text="Cobblemon learnset data is available. The dedicated Breeding Planner will separate inherited/egg move chains where the installed data exposes them.",
                 bg=PANEL,fg=MUTED,font=("Segoe UI",9),wraplength=900,justify="left").pack(anchor="w",padx=14,pady=(0,10))
        tk.Button(box,text="Browse Current Learnset",command=lambda:MovePicker(self.app,moves,"",lambda x:None),
                  bg=PANEL_2,fg=TEXT,relief="flat",padx=12,pady=7).pack(anchor="w",padx=14,pady=(0,10))

    def render_competitive(self):
        s=self.species
        box=self.section("Competitive Snapshot", "Quick team-building information; use Teams for full analysis.")
        stats=[("HP","hp"),("Atk","atk"),("Def","def"),("SpA","spa"),("SpD","spd"),("Spe","spe")]
        ordered=sorted(stats,key=lambda kv:int(s.get(kv[1],0) or 0),reverse=True)
        tk.Label(box,text="Highest stats: "+", ".join(f"{n} {s.get(k,0)}" for n,k in ordered[:3]),
                 bg=PANEL,fg=TEXT,font=("Segoe UI Semibold",10)).pack(anchor="w",padx=14,pady=(0,4))
        tk.Label(box,text="Abilities: "+(", ".join(species_ability_options(s)) or "—"),
                 bg=PANEL,fg=TEXT,font=("Segoe UI",9),wraplength=900,justify="left").pack(anchor="w",padx=14,pady=(0,8))

        prof=species_defensive_profile(s)
        tk.Label(box,text="Key weaknesses: "+(", ".join(f"{t} ×{m:g}" for t,m in prof["weak"]) or "None"),
                 bg=PANEL,fg=MUTED,font=("Segoe UI",9),wraplength=900,justify="left").pack(anchor="w",padx=14,pady=(0,8))
        tk.Button(box,text="Add to Team Builder",command=self.add_to_team,bg=ACCENT_2,fg="white",
                  relief="flat",padx=12,pady=7).pack(anchor="w",padx=14,pady=(0,10))

        box=self.section("Useful Moves")
        moves=species_move_options(s)
        holder=tk.Frame(box,bg=PANEL); holder.pack(fill="x",padx=10,pady=(0,10))
        for i,move in enumerate(moves[:35]):
            tk.Button(holder,text=move,command=lambda m=move:self.app.open_reference_detail("Move", m),
                      bg=PANEL_2,fg=TEXT,relief="flat",padx=6,pady=5).grid(row=i//5,column=i%5,sticky="ew",padx=2,pady=2)
        for c in range(5): holder.grid_columnconfigure(c,weight=1)

    def open_related_pokemon(self, name):
        self.app.open_pokemon_detail(name)

    def open_breeding_planner(self):
        self.app.show_page("Breeding")
        page=self.app.pages.get("Breeding")
        if page and hasattr(page,"focus_pokemon"):
            page.focus_pokemon(self.pokemon_name)

    def open_spawns(self):
        self.app.show_page("Spawn Finder")
        page=self.app.pages.get("Spawn Finder")
        if page and hasattr(page,"focus_pokemon"):
            page.focus_pokemon(self.pokemon_name)

    def toggle_owned(self):
        current=list(self.app.profile.get("living_dex",[]))
        low=[str(x).strip().lower() for x in current]
        key=self.pokemon_name.lower()
        if key in low: current.pop(low.index(key))
        else: current.append(self.pokemon_name)
        self.app.profile["living_dex"]=current
        self.app.save()
        page=self.app.pages.get("Collection")
        if page and hasattr(page,"refresh"): page.refresh()
        self.refresh_status()

    def toggle_hunt(self):
        hunts=self.app.profile.setdefault("hunts",[])
        key=self.pokemon_name.lower()
        idx=next((i for i,h in enumerate(hunts) if str(h.get("pokemon","")).strip().lower()==key),None)
        if idx is None: hunts.append({"pokemon":self.pokemon_name,"note":""})
        else: hunts.pop(idx)
        self.app.save()
        page=self.app.pages.get("Hunts")
        if page and hasattr(page,"refresh"): page.refresh()
        self.refresh_status()

    def add_to_team(self):
        teams=self.app.profile.setdefault("teams",[])
        if not teams: teams.append(blank_team("Team 1"))
        team=teams[0]
        members=team.setdefault("members",[blank_team_member() for _ in range(6)])
        while len(members)<6: members.append(blank_team_member())
        idx=next((i for i,m in enumerate(members) if not m.get("pokemon")),None)
        if idx is None:
            messagebox.showinfo(APP_NAME,"The first saved team is already full. Open Teams to choose where to place this Pokémon.")
            return
        members[idx]["pokemon"]=self.pokemon_name
        self.app.save()
        page=self.app.pages.get("Teams")
        if page and hasattr(page,"refresh"): page.refresh()
        messagebox.showinfo(APP_NAME,f"Added {self.pokemon_name} to {team.get('name','Team 1')} slot {idx+1}.")



# ---------------------------------------------------------------------------
# V1.4.1 — Embedded Pokédex 2.0 page
# ---------------------------------------------------------------------------

class EmbeddedPokemonDetailPage(tk.Frame):
    TABS = PokemonDetailWindow.TABS
    build_tabs = PokemonDetailWindow.build_tabs
    update_tab_buttons = PokemonDetailWindow.update_tab_buttons
    set_tab = PokemonDetailWindow.set_tab
    section = PokemonDetailWindow.section
    refresh_status = PokemonDetailWindow.refresh_status
    render_tab = PokemonDetailWindow.render_tab
    render_overview = PokemonDetailWindow.render_overview
    render_spawns = PokemonDetailWindow.render_spawns
    render_evolution = PokemonDetailWindow.render_evolution
    render_breeding = PokemonDetailWindow.render_breeding
    render_competitive = PokemonDetailWindow.render_competitive
    toggle_owned = PokemonDetailWindow.toggle_owned
    toggle_hunt = PokemonDetailWindow.toggle_hunt
    add_to_team = PokemonDetailWindow.add_to_team

    def __init__(self, master, app, pokemon_name):
        super().__init__(master,bg=BG)
        self.app=app
        self.pokemon_name=pokemon_name
        self.species=species_by_name(app.pokedex,pokemon_name)
        self.active_tab="Overview"
        self.sprite_ref=None

        self.build_header()
        self.build_tabs()

        self.status_line=tk.Label(self,text="",bg=BG,fg=MUTED,font=("Segoe UI",9))
        self.status_line.pack(anchor="w",padx=22,pady=(6,6))

        content=tk.Frame(self,bg=BG)
        content.pack(fill="both",expand=True,padx=20,pady=(0,20))
        self.canvas=tk.Canvas(content,bg=BG,highlightthickness=0)
        scroll=tk.Scrollbar(content,orient="vertical",command=self.canvas.yview)
        self.body=tk.Frame(self.canvas,bg=BG)
        self.body_win=self.canvas.create_window((0,0),window=self.body,anchor="nw")
        self.body.bind("<Configure>",lambda e:self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>",lambda e:self.canvas.itemconfigure(self.body_win,width=e.width))
        self.canvas.configure(yscrollcommand=scroll.set)
        self.canvas.pack(side="left",fill="both",expand=True)
        scroll.pack(side="right",fill="y")

        self.render_tab()

    def build_header(self):
        top=tk.Frame(self,bg=BG)
        top.pack(fill="x",padx=20,pady=(14,10))

        tk.Button(
            top,text="← Back",command=self.app.go_back,
            bg=PANEL_2,fg=TEXT,relief="flat",padx=12,pady=7
        ).pack(side="left",padx=(0,14))

        if self.species:
            path=cached_sprite_path(self.species.get("dex"))
            if path:
                try:
                    img=tk.PhotoImage(file=str(path))
                    if img.width()<=128 and img.height()<=128:
                        img=img.zoom(2,2)
                    self.sprite_ref=img
                    tk.Label(top,image=img,bg=BG,bd=0).pack(side="left",padx=(0,16))
                except Exception:
                    pass

        titlebox=tk.Frame(top,bg=BG)
        titlebox.pack(side="left",fill="x",expand=True)
        dex=self.species.get("dex",0) if self.species else 0
        tk.Label(titlebox,text=f"#{int(dex):04d}",bg=BG,fg=MUTED,font=("Segoe UI Semibold",10)).pack(anchor="w")
        tk.Label(titlebox,text=self.pokemon_name,bg=BG,fg=TEXT,font=("Segoe UI Semibold",28)).pack(anchor="w")

        type_row=tk.Frame(titlebox,bg=BG)
        type_row.pack(anchor="w",pady=(5,5))
        for t in (self.species or {}).get("types",[]):
            tk.Label(
                type_row,text=t.upper(),bg=TYPE_COLORS.get(t,CARD),fg="white",
                padx=11,pady=4,font=("Segoe UI",8,"bold")
            ).pack(side="left",padx=(0,4))

        bst=species_bst(self.species) if self.species else 0
        abilities=", ".join(species_ability_options(self.species or {})) or "—"
        if self.species and self.species.get("is_form"):
            tk.Label(
                titlebox,text=f"Form of {self.species.get('base_species','')}",
                bg=BG,fg=MUTED,font=("Segoe UI",8)
            ).pack(anchor="w",pady=(0,2))
        tk.Label(
            titlebox,text=f"BST {bst}   •   {abilities}",
            bg=BG,fg=MUTED,font=("Segoe UI",9),
            wraplength=540,justify="left"
        ).pack(anchor="w")

        actions=tk.Frame(top,bg=BG)
        actions.pack(side="right")
        for label,cmd,color in [
            ("Find Spawns",self.open_spawns,ACCENT_2),
            ("Toggle Owned",self.toggle_owned,PANEL_2),
            ("Toggle Hunt",self.toggle_hunt,PANEL_2),
            ("Add to Team",self.add_to_team,PANEL_2),
        ]:
            tk.Button(
                actions,text=label,command=cmd,bg=color,
                fg="white" if color==ACCENT_2 else TEXT,
                relief="flat",padx=12,pady=7
            ).pack(fill="x",pady=2)

    def render_moves(self):
        s=self.species
        moves=species_move_options(s)
        box=self.section(
            "Learnset",
            f"{len(moves)} learnable moves imported for {self.pokemon_name}. Click a move to open its Database entry."
        )
        if not moves:
            tk.Label(
                box,text="No learnset data found.",
                bg=PANEL,fg=MUTED,font=("Segoe UI",9)
            ).pack(anchor="w",padx=14,pady=(0,10))
            return

        holder=tk.Frame(box,bg=PANEL)
        holder.pack(fill="x",padx=10,pady=(0,10))
        for i,move in enumerate(moves[:120]):
            tk.Button(
                holder,text=move,
                command=lambda m=move:self.app.open_reference_detail("Move",m),
                bg=PANEL_2,fg=TEXT,relief="flat",padx=6,pady=5
            ).grid(row=i//5,column=i%5,sticky="ew",padx=2,pady=2)
        for c in range(5):
            holder.grid_columnconfigure(c,weight=1)

        if len(moves)>120:
            tk.Label(
                box,text=f"Showing first 120 of {len(moves)} moves.",
                bg=PANEL,fg=MUTED,font=("Segoe UI",8)
            ).pack(anchor="w",padx=14,pady=(0,8))

    def open_related_pokemon(self,name):
        self.app.open_pokemon_detail(name)

    def open_breeding_planner(self):
        self.app.show_page("Breeding")
        page=self.app.pages.get("Breeding")
        if page and hasattr(page,"focus_pokemon"):
            page.focus_pokemon(self.pokemon_name)

    def open_spawns(self):
        self.app.show_page("Spawn Finder")
        page=self.app.pages.get("Spawn Finder")
        if page and hasattr(page,"focus_pokemon"):
            page.focus_pokemon(self.pokemon_name)



class PokedexPage(Page):
    title = "Pokédex"
    subtitle = "Pokédex 2.0 — a connected hub for every implemented Pokémon in your installed Cobblemon build."

    def __init__(self, master, app):
        super().__init__(master, app)
        self.header()
        self.dex_status = tk.Label(
            self, text="", bg=BG, fg=MUTED, font=("Segoe UI", 9)
        )
        self.dex_status.pack(anchor="w", padx=29, pady=(0, 10))
        searchbar = tk.Frame(self, bg=BG)
        searchbar.pack(fill="x", padx=28, pady=(0, 12))
        self.query = tk.StringVar()
        entry = tk.Entry(searchbar, textvariable=self.query, bg=PANEL, fg=TEXT,
                         insertbackground=TEXT, relief="flat", font=("Segoe UI", 12))
        entry.pack(side="left", fill="x", expand=True, ipady=9)
        entry.bind("<KeyRelease>", lambda e: self.refresh_list())
        tk.Button(searchbar, text="Clear", command=self.clear_search,
                  bg=PANEL_2, fg=TEXT, relief="flat", padx=16, pady=9).pack(side="left", padx=(8,0))

        body = tk.Frame(self, bg=BG)
        body.pack(fill="both", expand=True, padx=28, pady=(0, 28))
        body.grid_columnconfigure(1, weight=1)
        body.grid_rowconfigure(0, weight=1)

        left = tk.Frame(body, bg=PANEL, width=290)
        left.grid(row=0, column=0, sticky="nsw", padx=(0, 12))
        left.grid_propagate(False)

        self.listbox = tk.Listbox(left, bg=PANEL, fg=TEXT, selectbackground=ACCENT_2,
                                  selectforeground=TEXT, relief="flat", bd=0,
                                  highlightthickness=0, font=("Segoe UI", 11))
        self.listbox.pack(fill="both", expand=True, padx=8, pady=8)
        self.listbox.bind("<<ListboxSelect>>", self.select_pokemon)
        self.listbox.bind("<Double-Button-1>", lambda e: self.open_selected_detail())

        self.detail = tk.Frame(body, bg=PANEL)
        self.detail.grid(row=0, column=1, sticky="nsew")
        self.refresh_list()

    def refresh(self):
        meta = self.app.dex_meta
        if meta.get("species_count"):
            source_name = Path(meta.get("source_jar", "")).name
            self.dex_status.config(
                text=f"{meta['species_count']} implemented Pokémon loaded from {source_name}"
            )
        else:
            self.dex_status.config(
                text="Starter preview data only — import your Cobblemon .jar in Settings for the full implemented Dex."
            )
        self.refresh_list()

    def clear_search(self):
        self.query.set("")
        self.refresh_list()

    def refresh_list(self):
        q = self.query.get().strip().lower()
        self.filtered = [
            p for p in self.app.pokedex
            if (not q
                or q in p["name"].lower()
                or q == str(p["dex"])
                or any(q in t.lower() for t in p.get("types", [])))
        ]
        self.listbox.delete(0, "end")
        for p in self.filtered:
            self.listbox.insert("end", f"#{p['dex']:04d}   {p['name']}")
        if self.filtered:
            self.listbox.selection_set(0)
            self.show_detail(self.filtered[0])
        else:
            for w in self.detail.winfo_children():
                w.destroy()
            tk.Label(self.detail, text="No Pokémon found.", bg=PANEL, fg=MUTED,
                     font=("Segoe UI", 12)).pack(padx=25, pady=25)

    def select_pokemon(self, _=None):
        sel = self.listbox.curselection()
        if sel:
            self.show_detail(self.filtered[sel[0]])

    def open_selected_detail(self):
        sel = self.listbox.curselection()
        if sel and sel[0] < len(self.filtered):
            self.app.open_pokemon_detail(self.filtered[sel[0]]["name"])

    def show_detail(self, p):
        for w in self.detail.winfo_children():
            w.destroy()

        tk.Label(self.detail, text=f"#{p['dex']:04d}", bg=PANEL, fg=MUTED,
                 font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=24, pady=(22, 0))
        title_row = tk.Frame(self.detail, bg=PANEL)
        title_row.pack(fill="x", padx=24, pady=(0, 8))

        name_box = tk.Frame(title_row, bg=PANEL)
        name_box.pack(side="left", fill="x", expand=True)
        tk.Label(name_box, text=p["name"], bg=PANEL, fg=TEXT,
                 font=("Segoe UI Semibold", 28)).pack(anchor="w")

        self._sprite_ref = None
        sprite_path = get_cached_sprite(p.get("dex"))
        if sprite_path:
            try:
                img = tk.PhotoImage(file=str(sprite_path))
                # Standard sprites are 96x96 and can be shown 1:1 without smoothing.
                self._sprite_ref = img
                tk.Label(title_row, image=img, bg=PANEL, bd=0).pack(
                    side="right", padx=(12, 8)
                )
            except Exception:
                pass

        types = tk.Frame(self.detail, bg=PANEL)
        types.pack(anchor="w", padx=20, pady=(0, 18))
        for t in p["types"]:
            tk.Label(types, text=t.upper(), bg=TYPE_COLORS.get(t, CARD), fg="white",
                     padx=12, pady=5, font=("Segoe UI", 9, "bold")).pack(side="left", padx=4)

        stat_names = [("HP","hp"),("Attack","atk"),("Defense","def"),
                      ("Sp. Atk","spa"),("Sp. Def","spd"),("Speed","spe")]
        for label, key in stat_names:
            row = tk.Frame(self.detail, bg=PANEL)
            row.pack(fill="x", padx=24, pady=5)
            tk.Label(row, text=label, width=9, anchor="w", bg=PANEL, fg=MUTED,
                     font=("Segoe UI", 10, "bold")).pack(side="left")
            tk.Label(row, text=str(p[key]), width=4, anchor="e", bg=PANEL, fg=TEXT,
                     font=("Segoe UI", 10)).pack(side="left", padx=(0, 10))
            bar_bg = tk.Frame(row, bg=CARD, height=10)
            bar_bg.pack(side="left", fill="x", expand=True)
            fill = tk.Frame(bar_bg, bg=ACCENT_2, height=10)
            fill.place(relx=0, rely=0, relheight=1, relwidth=min(p[key]/180, 1))

        bst = sum(p[k] for k in ("hp","atk","def","spa","spd","spe"))
        tk.Label(self.detail, text=f"Base Stat Total: {bst}", bg=PANEL, fg=TEXT,
                 font=("Segoe UI Semibold", 11)).pack(anchor="w", padx=24, pady=(18, 0))

        tk.Button(
            self.detail, text="Open Pokédex 2.0 Hub",
            command=lambda name=p["name"]: self.app.open_pokemon_detail(name),
            bg=ACCENT_2, fg="white", relief="flat", padx=14, pady=8
        ).pack(anchor="w", padx=24, pady=(14, 0))

        extras = []
        if p.get("catch_rate") is not None:
            extras.append(f"Catch Rate: {p['catch_rate']}")
        if p.get("experience_group"):
            extras.append(f"Growth: {str(p['experience_group']).replace('_', ' ').title()}")
        if p.get("egg_groups"):
            extras.append("Egg Groups: " + ", ".join(_title_type(x) for x in p["egg_groups"]))
        if extras:
            tk.Label(self.detail, text="   •   ".join(extras), bg=PANEL, fg=MUTED,
                     font=("Segoe UI", 9), wraplength=600, justify="left").pack(
                         anchor="w", padx=24, pady=(10, 0)
                     )

class BingoPage(Page):
    title = "Bingo"
    subtitle = "Mirror your server’s predetermined weekly 5×5 card and track what you still need to catch."

    def __init__(self, master, app):
        super().__init__(master, app)
        self.sprite_refs = {}
        self._sprite_download_running = False

        self.header()

        top = tk.Frame(self, bg=BG)
        top.pack(fill="x", padx=28, pady=(0, 8))

        left = tk.Frame(top, bg=BG)
        left.pack(side="left", fill="x", expand=True)

        self.card_name = tk.Label(
            left, text="", bg=BG, fg=TEXT,
            font=("Segoe UI Semibold", 14)
        )
        self.card_name.pack(anchor="w")

        self.progress = tk.Label(
            left, text="", bg=BG, fg=MUTED,
            font=("Segoe UI", 9)
        )
        self.progress.pack(anchor="w", pady=(2, 0))

        controls = tk.Frame(top, bg=BG)
        controls.pack(side="right")

        tk.Button(
            controls, text="Reset Caught", command=self.reset_caught,
            bg=PANEL_2, fg=TEXT, relief="flat", padx=12, pady=7
        ).pack(side="left", padx=3)

        tk.Button(
            controls, text="New Weekly Card", command=self.clear_card,
            bg=PANEL_2, fg=TEXT, relief="flat", padx=12, pady=7
        ).pack(side="left", padx=3)

        help_row = tk.Frame(self, bg=BG)
        help_row.pack(fill="x", padx=28, pady=(0, 6))
        tk.Label(
            help_row,
            text="Enter the Pokémon shown on your in-game weekly card • Click = caught/uncaught • Find Spawns = open Spawn Finder",
            bg=BG, fg=MUTED, font=("Segoe UI", 8)
        ).pack(anchor="w")

        self.grid_frame = tk.Frame(self, bg=BG)
        self.grid_frame.pack(fill="both", expand=True, padx=28, pady=(0, 28))

        for i in range(5):
            self.grid_frame.grid_columnconfigure(i, weight=1, uniform="bingo")
            self.grid_frame.grid_rowconfigure(i, weight=1, uniform="bingo")

        self.tiles = []
        for i in range(25):
            outer = tk.Frame(self.grid_frame, bg=PANEL, bd=0)
            outer.grid(row=i // 5, column=i % 5, sticky="nsew", padx=4, pady=4)

            main = tk.Button(
                outer, text="", bg=PANEL, fg=TEXT,
                activebackground=PANEL_2, activeforeground=TEXT,
                relief="flat", bd=0, compound="top",
                font=("Segoe UI Semibold", 9),
                cursor="hand2",
                command=lambda idx=i: self.toggle(idx)
            )
            main.pack(fill="both", expand=True)
            main.bind("<Button-3>", lambda e, idx=i: self.edit_tile(idx))

            footer = tk.Frame(outer, bg=PANEL)
            footer.pack(fill="x")

            edit = tk.Button(
                footer, text="Edit",
                command=lambda idx=i: self.edit_tile(idx),
                bg=PANEL_2, fg=MUTED, activebackground=CARD, activeforeground=TEXT,
                relief="flat", bd=0, font=("Segoe UI", 7), pady=3
            )
            edit.pack(side="left", fill="x", expand=True, padx=(0, 1))

            spawn = tk.Button(
                footer, text="Find Spawns",
                command=lambda idx=i: self.open_spawn_for_tile(idx),
                bg=PANEL_2, fg=MUTED, activebackground=ACCENT_2, activeforeground="white",
                relief="flat", bd=0, font=("Segoe UI", 7), pady=3
            )
            spawn.pack(side="left", fill="x", expand=True, padx=(1, 0))

            self.tiles.append({
                "outer": outer, "main": main, "footer": footer,
                "edit": edit, "spawn": spawn
            })

        self.refresh()

    def _spawnable_names(self):
        names = {x.get("pokemon", "").strip().lower() for x in (self.app.spawns or [])}
        return {n for n in names if n}

    def refresh(self):
        card = self.app.profile.get("bingo", [])
        if len(card) != 25:
            self.app.profile["bingo"] = default_profile()["bingo"]
            card = self.app.profile["bingo"]

        self.card_name.config(text=self.app.profile.get("bingo_name", "Weekly Bingo Card"))

        caught = 0
        filled = 0
        self.sprite_refs = {}

        for i, item in enumerate(card):
            name = item.get("pokemon", "").strip()
            is_caught = bool(item.get("caught"))
            tile = self.tiles[i]

            if name:
                filled += 1
            if name and is_caught:
                caught += 1

            bg = GOOD if (name and is_caught) else PANEL
            tile["outer"].config(bg=bg)
            tile["footer"].config(bg=bg)

            sprite = None
            species = species_by_name(self.app.pokedex, name) if name else None
            if species:
                path = cached_sprite_path(species.get("dex"))
                if path:
                    try:
                        img = tk.PhotoImage(file=str(path))
                        # Standard PokeAPI sprite is 96×96. 48×48 fits a 5×5 card well.
                        if img.width() >= 80 or img.height() >= 80:
                            img = img.subsample(2, 2)
                        sprite = img
                        self.sprite_refs[i] = img
                    except Exception:
                        sprite = None

            if name:
                label = f"✓  {name}" if is_caught else name
            else:
                label = "Empty Slot"

            tile["main"].config(
                text=label,
                image=sprite if sprite else "",
                bg=bg,
                activebackground=GOOD if is_caught else PANEL_2,
                fg=TEXT
            )
            tile["edit"].config(bg=PANEL_2)
            tile["spawn"].config(
                bg=PANEL_2,
                state="normal" if name else "disabled"
            )

        percent = round((caught / filled * 100), 1) if filled else 0
        self.progress.config(
            text=f"{caught} / {filled} caught  •  {max(filled-caught, 0)} remaining  •  {percent:g}% complete"
        )

        self._prefetch_missing_sprites()

    def _prefetch_missing_sprites(self):
        if self._sprite_download_running:
            return

        missing = []
        for item in self.app.profile.get("bingo", []):
            name = item.get("pokemon", "").strip()
            if not name:
                continue
            species = species_by_name(self.app.pokedex, name)
            if species and not cached_sprite_path(species.get("dex")):
                missing.append(species.get("dex"))

        missing = list(dict.fromkeys(missing))
        if not missing:
            return

        self._sprite_download_running = True

        def worker():
            for dex in missing:
                try:
                    get_cached_sprite(dex)
                except Exception:
                    pass

            def done():
                self._sprite_download_running = False
                # Refresh only if the widget still exists.
                try:
                    if self.winfo_exists():
                        self.refresh()
                except Exception:
                    pass

            try:
                self.after(0, done)
            except Exception:
                pass

        threading.Thread(target=worker, daemon=True).start()

    def toggle(self, idx):
        item = self.app.profile["bingo"][idx]
        if not item.get("pokemon"):
            self.edit_tile(idx)
            return
        item["caught"] = not item.get("caught", False)
        self.app.save()
        self.refresh()

    def edit_tile(self, idx):
        current = self.app.profile["bingo"][idx].get("pokemon", "")
        PokemonPicker(
            self.app,
            self.app.pokedex,
            title="Choose Bingo Pokémon",
            current=current,
            callback=lambda pokemon: self.set_tile(idx, pokemon)
        )

    def set_tile(self, idx, value):
        value = str(value or "").strip()
        self.app.profile["bingo"][idx] = {"pokemon": value, "caught": False}
        self.app.save()
        self.refresh()

    def open_spawn_for_tile(self, idx):
        name = self.app.profile["bingo"][idx].get("pokemon", "").strip()
        if not name:
            return
        self.app.show_page("Spawn Finder")
        page = self.app.pages.get("Spawn Finder")
        if page and hasattr(page, "focus_pokemon"):
            page.focus_pokemon(name)

    def reset_caught(self):
        if messagebox.askyesno(APP_NAME, "Clear all caught marks on this Bingo card?"):
            for item in self.app.profile["bingo"]:
                item["caught"] = False
            self.app.save()
            self.refresh()

    def clear_card(self):
        if messagebox.askyesno(APP_NAME, "Start a new weekly Bingo card?\n\nThis clears all 25 Pokémon and their caught progress."):
            self.app.profile["bingo"] = [{"pokemon": "", "caught": False} for _ in range(25)]
            self.app.profile["bingo_name"] = "Weekly Bingo Card"
            self.app.save()
            self.refresh()


class SpawnFinderPage(Page):
    title = "Spawn Finder"
    subtitle = "Search real Cobblemon spawn rules in a player-friendly format."

    def __init__(self, master, app):
        super().__init__(master, app)
        self.header()

        controls = tk.Frame(self, bg=BG)
        controls.pack(fill="x", padx=28, pady=(0, 10))

        self.query = tk.StringVar()
        self.biome_query = tk.StringVar()
        self.rarity_var = tk.StringVar(value="All rarities")
        self.time_var = tk.StringVar(value="Any time")

        search = tk.Entry(
            controls, textvariable=self.query, bg=PANEL, fg=TEXT,
            insertbackground=TEXT, relief="flat", font=("Segoe UI", 11)
        )
        search.grid(row=0, column=0, sticky="ew", ipady=9)

        biome = tk.Entry(
            controls, textvariable=self.biome_query, bg=PANEL, fg=TEXT,
            insertbackground=TEXT, relief="flat", font=("Segoe UI", 11)
        )
        biome.grid(row=0, column=1, sticky="ew", padx=8, ipady=9)

        rarity = tk.OptionMenu(
            controls, self.rarity_var,
            "All rarities", "Common", "Uncommon", "Rare", "Ultra Rare"
        )
        rarity.config(bg=PANEL_2, fg=TEXT, activebackground=PANEL_2,
                      activeforeground=TEXT, relief="flat", highlightthickness=0,
                      font=("Segoe UI", 9))
        rarity["menu"].config(bg=PANEL_2, fg=TEXT)
        rarity.grid(row=0, column=2, sticky="ew", padx=(0, 8))

        time_menu = tk.OptionMenu(
            controls, self.time_var,
            "Any time", "Day", "Night", "Dawn", "Dusk"
        )
        time_menu.config(bg=PANEL_2, fg=TEXT, activebackground=PANEL_2,
                         activeforeground=TEXT, relief="flat", highlightthickness=0,
                         font=("Segoe UI", 9))
        time_menu["menu"].config(bg=PANEL_2, fg=TEXT)
        time_menu.grid(row=0, column=3, sticky="ew")

        controls.grid_columnconfigure(0, weight=3)
        controls.grid_columnconfigure(1, weight=2)
        controls.grid_columnconfigure(2, weight=1)
        controls.grid_columnconfigure(3, weight=1)

        labels = tk.Frame(self, bg=BG)
        labels.pack(fill="x", padx=28)
        tk.Label(labels, text="Pokémon", bg=BG, fg=MUTED,
                 font=("Segoe UI", 9)).pack(side="left")
        tk.Label(labels, text="Habitat / biome", bg=BG, fg=MUTED,
                 font=("Segoe UI", 9)).pack(side="left", padx=(245, 0))

        self.status = tk.Label(self, text="", bg=BG, fg=MUTED, font=("Segoe UI", 9))
        self.status.pack(anchor="w", padx=29, pady=(8, 8))

        self.canvas = tk.Canvas(self, bg=BG, highlightthickness=0)
        self.scroll = tk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.results_frame = tk.Frame(self.canvas, bg=BG)

        self.window_id = self.canvas.create_window((0, 0), window=self.results_frame, anchor="nw")
        self.results_frame.bind(
            "<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        self.canvas.bind(
            "<Configure>", lambda e: self.canvas.itemconfigure(self.window_id, width=e.width)
        )
        self.canvas.configure(yscrollcommand=self.scroll.set)

        self.canvas.pack(side="left", fill="both", expand=True, padx=(28, 0), pady=(0, 28))
        self.scroll.pack(side="right", fill="y", padx=(0, 28), pady=(0, 28))

        for var in (self.query, self.biome_query, self.rarity_var, self.time_var):
            var.trace_add("write", lambda *_: self.refresh_results())

        # Do NOT render thousands of spawn-rule widgets during application startup.
        # The data is already cached in memory; results are drawn only after the
        # player actually enters a search/filter.
        self.show_idle_state()

    def refresh(self):
        self.app.spawns = load_spawn_data()
        if self.has_active_filters():
            self.refresh_results()
        else:
            self.show_idle_state()

    def has_active_filters(self):
        return bool(
            self.query.get().strip()
            or self.biome_query.get().strip()
            or self.rarity_var.get() != "All rarities"
            or self.time_var.get() != "Any time"
        )

    def show_idle_state(self):
        for w in self.results_frame.winfo_children():
            w.destroy()
        total = len(self.app.spawns or [])
        self.status.config(
            text=f"{total} spawn rules loaded and ready."
            if total else
            "No spawn data cached yet. Open Settings and refresh your Cobblemon JAR."
        )
        box = tk.Frame(self.results_frame, bg=PANEL)
        box.pack(fill="x", pady=6)
        tk.Label(
            box,
            text="Search for a Pokémon or choose a filter to view spawn locations.",
            bg=PANEL, fg=TEXT, font=("Segoe UI Semibold", 13),
            padx=18
        ).pack(pady=(24, 6))
        tk.Label(
            box,
            text="Keeping the results empty until you search makes the Companion launch much faster.",
            bg=PANEL, fg=MUTED, font=("Segoe UI", 9),
            padx=18
        ).pack(pady=(0, 24))

    def focus_pokemon(self, pokemon_name):
        self.query.set(pokemon_name or "")
        self.biome_query.set("")
        self.rarity_var.set("All rarities")
        self.time_var.set("Any time")
        self.refresh_results()
        self.canvas.yview_moveto(0)

    def _passes_filters(self, item):
        q = self.query.get().strip().lower()
        habitat_q = self.biome_query.get().strip().lower()
        rarity_q = self.rarity_var.get().strip().lower()
        time_q = self.time_var.get().strip().lower()

        if q and q not in item.get("pokemon", "").lower():
            return False

        habitat_text = " ".join(
            spawn_habitat_labels(item) +
            [str(v) for v in item.get("biomes", []) or []]
        ).lower()
        if habitat_q and habitat_q not in habitat_text:
            return False

        bucket = friendly_bucket(item.get("bucket")).lower()
        if rarity_q != "all rarities" and rarity_q not in bucket:
            return False

        if time_q != "any time":
            t = friendly_time(item.get("time")).lower()
            if time_q not in t:
                return False

        return True

    def refresh_results(self):
        if not self.has_active_filters():
            self.show_idle_state()
            return

        for w in self.results_frame.winfo_children():
            w.destroy()

        data = self.app.spawns or []
        filtered = [x for x in data if self._passes_filters(x)]
        grouped = {}
        for item in filtered:
            grouped.setdefault(item.get("pokemon","Unknown"), []).append(item)

        self.status.config(
            text=(
                f"{len(grouped)} Pokémon • {len(filtered)} matching spawn rules • "
                f"{len(data)} total parsed"
                if data else
                "No spawn data cached yet. Open Settings and refresh your Cobblemon JAR."
            )
        )

        if not grouped:
            q = self.query.get().strip()
            exact_species = species_by_name(self.app.pokedex, q) if q else None
            if exact_species:
                kind, label = species_spawn_status(self.app, q)
                box = tk.Frame(self.results_frame, bg=PANEL); box.pack(fill="x", pady=6)
                tk.Label(box, text=f"{q} — {label}", bg=PANEL, fg=TEXT,
                         font=("Segoe UI Semibold", 13), padx=18).pack(anchor="w", pady=(18,5))
                tk.Label(box,text=("This Pokémon exists in the installed species data, but no standard natural "
                                   "spawn rule was found. It may be obtained through an event, structure, addon "
                                   "mechanic, command, or a server-side datapack Companion cannot see locally."),
                         bg=PANEL,fg=MUTED,font=("Segoe UI",9),padx=18,
                         wraplength=850,justify="left").pack(anchor="w",pady=(0,18))
            else:
                tk.Label(self.results_frame,text="No matching Pokémon found.",
                         bg=PANEL,fg=MUTED,font=("Segoe UI",11),padx=18,pady=28).pack(fill="x")
            return

        # Broad filters can still match hundreds of Pokémon. Limit what gets
        # rendered at once; the search/filter remains over the full dataset.
        display_groups = sorted(grouped.items())
        MAX_RENDERED_POKEMON = 75
        hidden_count = max(0, len(display_groups) - MAX_RENDERED_POKEMON)
        display_groups = display_groups[:MAX_RENDERED_POKEMON]

        if hidden_count:
            notice = tk.Label(
                self.results_frame,
                text=f"Showing the first {MAX_RENDERED_POKEMON} Pokémon. "
                     f"Refine your search to view the other {hidden_count}.",
                bg=PANEL, fg=MUTED, font=("Segoe UI", 9),
                padx=14, pady=10
            )
            notice.pack(fill="x", pady=(0, 4))

        for pokemon, entries in display_groups:
            card = tk.Frame(self.results_frame, bg=PANEL)
            card.pack(fill="x", pady=6)

            header = tk.Frame(card, bg=PANEL)
            header.pack(fill="x", padx=16, pady=(14, 8))

            tk.Label(
                header, text=pokemon, bg=PANEL, fg=TEXT,
                font=("Segoe UI Semibold", 15)
            ).pack(side="left")

            source_kinds = {spawn_source_info(self.app, e)[0] for e in entries}
            if "base" in source_kinds and "addon" in source_kinds:
                group_source = "Base + Addon"
            elif "addon" in source_kinds:
                group_source = "Addon"
            elif "base" in source_kinds:
                group_source = "Base Cobblemon"
            else:
                group_source = "Unknown source"
            tk.Label(
                header,
                text=f"{len(entries)} spawn rule{'s' if len(entries) != 1 else ''}   •   {group_source}",
                bg=PANEL, fg=MUTED, font=("Segoe UI", 9)
            ).pack(side="right")

            # Target-specific Poké Snack seasonings from this species' actual
            # Cobblemon types and Egg Groups.
            species = species_by_name(self.app.pokedex, pokemon)
            snack = pokesnack_recommendation(species)
            if snack.get("combo"):
                snack_box = tk.Frame(card, bg=CARD)
                snack_box.pack(fill="x", padx=14, pady=(0, 5))

                tk.Label(
                    snack_box, text="Poké Snack", bg=CARD, fg=TEXT,
                    font=("Segoe UI Semibold", 10)
                ).pack(anchor="w", padx=10, pady=(8, 2))

                combo_text = "  +  ".join(item[0] for item in snack["combo"])
                tk.Label(
                    snack_box, text=f"Suggested seasoning slots: {combo_text}",
                    bg=CARD, fg=TEXT, font=("Segoe UI", 9),
                    anchor="w", justify="left", wraplength=780
                ).pack(anchor="w", padx=10)

                target_lines = [
                    f"{berry} — {effect}"
                    for berry, effect in snack.get("targeting", [])
                ]
                if target_lines:
                    tk.Label(
                        snack_box,
                        text="Targeting options: " + "   •   ".join(target_lines),
                        bg=CARD, fg=MUTED, font=("Segoe UI", 8),
                        anchor="w", justify="left", wraplength=820
                    ).pack(anchor="w", padx=10, pady=(3, 8))
                else:
                    tk.Label(
                        snack_box,
                        text="No type/Egg-Group targeting berry is available for this species; utility seasonings are shown instead.",
                        bg=CARD, fg=MUTED, font=("Segoe UI", 8),
                        anchor="w", justify="left", wraplength=820
                    ).pack(anchor="w", padx=10, pady=(3, 8))

            for entry in entries:
                row = tk.Frame(card, bg=PANEL_2)
                row.pack(fill="x", padx=14, pady=3)

                left = tk.Frame(row, bg=PANEL_2)
                left.pack(side="left", fill="both", expand=True, padx=12, pady=10)

                habitats = spawn_habitat_labels(entry)
                habitat_text = ", ".join(habitats) if habitats else "General / unspecified"

                tk.Label(
                    left, text=habitat_text, bg=PANEL_2, fg=TEXT,
                    font=("Segoe UI Semibold", 10), anchor="w", justify="left"
                ).pack(anchor="w")

                source_kind, source_label = spawn_source_info(self.app, entry)
                detail_parts = [
                    f"Rarity: {friendly_bucket(entry.get('bucket'))}",
                    f"Level: {friendly_level(entry.get('level'))}",
                    f"Time: {friendly_time(entry.get('time'))}",
                    f"Source: {source_label}",
                ]

                weather = [friendly_resource_name(x) for x in entry.get("weather", []) or []]
                if weather:
                    detail_parts.append("Weather: " + ", ".join(weather))

                if entry.get("weight") is not None:
                    detail_parts.append(f"Weight: {entry.get('weight')}")

                tk.Label(
                    left, text="   •   ".join(detail_parts),
                    bg=PANEL_2, fg=MUTED, font=("Segoe UI", 9),
                    anchor="w", justify="left", wraplength=780
                ).pack(anchor="w", pady=(3, 0))

class HuntsPage(Page):
    title = "Hunt Planner"
    subtitle = "Turn Hunts, weekly Bingo and Collection progress into an actionable hunting plan."

    def __init__(self, master, app):
        super().__init__(master, app)
        self.sprite_refs={}
        self.header()

        add=tk.Frame(self,bg=BG)
        add.pack(fill="x",padx=28,pady=(0,10))
        self.name_var=tk.StringVar()
        self.note_var=tk.StringVar()

        tk.Entry(
            add,textvariable=self.name_var,bg=PANEL,fg=TEXT,
            insertbackground=TEXT,relief="flat",font=("Segoe UI",11)
        ).pack(side="left",fill="x",expand=True,ipady=9)
        tk.Entry(
            add,textvariable=self.note_var,bg=PANEL,fg=TEXT,
            insertbackground=TEXT,relief="flat",font=("Segoe UI",11)
        ).pack(side="left",fill="x",expand=True,ipady=9,padx=8)
        tk.Button(
            add,text="Add Hunt",command=self.add_hunt,
            bg=ACCENT_2,fg="white",relief="flat",padx=16,pady=9
        ).pack(side="left")

        self.canvas=tk.Canvas(self,bg=BG,highlightthickness=0)
        sb=tk.Scrollbar(self,orient="vertical",command=self.canvas.yview)
        self.body=tk.Frame(self.canvas,bg=BG)
        self.body.bind("<Configure>",lambda e:self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0,0),window=self.body,anchor="nw",tags=("body",))
        self.canvas.bind("<Configure>",lambda e:self.canvas.itemconfigure("body",width=e.width))
        self.canvas.configure(yscrollcommand=sb.set)
        self.canvas.pack(side="left",fill="both",expand=True,padx=(28,0),pady=(0,28))
        sb.pack(side="right",fill="y",padx=(0,18),pady=(0,28))
        self.refresh()

    def add_hunt(self):
        name=self.name_var.get().strip()
        note=self.note_var.get().strip()
        if not name:return
        # Prefer canonical Pokédex capitalization when possible.
        species=species_by_name(self.app.pokedex,name)
        if species:name=species.get("name",name)
        existing={str(h.get("pokemon","")).strip().casefold() for h in self.app.profile.setdefault("hunts",[])}
        if name.casefold() not in existing:
            self.app.profile["hunts"].append({"pokemon":name,"note":note})
        self.name_var.set(""); self.note_var.set("")
        self.app.save(); self.refresh()

    def remove_hunt(self,name):
        key=str(name).strip().casefold()
        hunts=self.app.profile.setdefault("hunts",[])
        self.app.profile["hunts"]=[h for h in hunts if str(h.get("pokemon","")).strip().casefold()!=key]
        self.app.save(); self.refresh()

    def open_spawn_finder(self,pokemon):
        self.app.show_page("Spawn Finder")
        page=self.app.pages.get("Spawn Finder")
        if page and hasattr(page,"focus_pokemon"):page.focus_pokemon(pokemon)

    def refresh(self):
        for w in self.body.winfo_children():w.destroy()
        intel=hunt_intelligence(self.app)
        targets=intel["targets"]
        active={str(h.get("pokemon","")).strip().casefold() for h in self.app.profile.get("hunts",[])}

        # Recommendation hero.
        hero=tk.Frame(self.body,bg=PANEL)
        hero.pack(fill="x",pady=(0,10))
        tk.Label(hero,text="What should I hunt?",bg=PANEL,fg=TEXT,font=("Segoe UI Semibold",14)).pack(anchor="w",padx=14,pady=(12,4))
        if targets:
            best=targets[0]
            tk.Label(
                hero,text=best["name"],bg=PANEL,fg=TEXT,
                font=("Segoe UI Semibold",20)
            ).pack(anchor="w",padx=14)
            tk.Label(
                hero,text="  •  ".join(best["reasons"]),
                bg=PANEL,fg=MUTED,font=("Segoe UI",9)
            ).pack(anchor="w",padx=14,pady=(2,4))
            detail=[]
            if best["habitats"]:detail.append("Best known areas: "+", ".join(best["habitats"][:4]))
            if best["times"]:detail.append("Time: "+", ".join(best["times"][:3]))
            if best["weather"]:detail.append("Weather: "+", ".join(best["weather"][:3]))
            if detail:
                tk.Label(hero,text="   •   ".join(detail),bg=PANEL,fg=MUTED,font=("Segoe UI",8),wraplength=900,justify="left").pack(anchor="w",padx=14,pady=(0,6))
            snack=" + ".join(x[0] for x in best["snack"].get("combo",[]))
            if snack:
                tk.Label(hero,text="Poké Snack: "+snack,bg=PANEL,fg=TEXT,font=("Segoe UI",8)).pack(anchor="w",padx=14,pady=(0,8))
            buttons=tk.Frame(hero,bg=PANEL); buttons.pack(fill="x",padx=14,pady=(0,12))
            tk.Button(buttons,text="Find Spawns",command=lambda n=best["name"]:self.open_spawn_finder(n),bg=ACCENT_2,fg="white",relief="flat",padx=11,pady=6).pack(side="left")
            tk.Button(buttons,text="Pokédex",command=lambda n=best["name"]:self.app.open_pokemon_detail(n),bg=PANEL_2,fg=TEXT,relief="flat",padx=11,pady=6).pack(side="left",padx=6)
        else:
            tk.Label(hero,text="Add a Hunt or fill your weekly Bingo card and I'll build a plan.",bg=PANEL,fg=MUTED,font=("Segoe UI",9)).pack(anchor="w",padx=14,pady=(0,14))

        # Shared area intelligence.
        areas=[x for x in intel["areas"] if len(x[1])>=2][:8]
        area_box=tk.Frame(self.body,bg=PANEL)
        area_box.pack(fill="x",pady=(0,10))
        tk.Label(area_box,text="Best shared hunting areas",bg=PANEL,fg=TEXT,font=("Segoe UI Semibold",13)).pack(anchor="w",padx=14,pady=(12,5))
        if areas:
            for habitat,mons in areas:
                row=tk.Frame(area_box,bg=PANEL_2); row.pack(fill="x",padx=14,pady=3)
                tk.Label(row,text=habitat,bg=PANEL_2,fg=TEXT,font=("Segoe UI Semibold",9)).pack(anchor="w",padx=10,pady=(7,1))
                tk.Label(row,text=f"{len(mons)} targets • "+", ".join(mons),bg=PANEL_2,fg=MUTED,font=("Segoe UI",8),wraplength=900,justify="left").pack(anchor="w",padx=10,pady=(0,7))
        else:
            tk.Label(area_box,text="No overlapping known spawn areas among your current targets yet.",bg=PANEL,fg=MUTED,font=("Segoe UI",9)).pack(anchor="w",padx=14,pady=(0,12))

        # All actionable targets.
        tk.Label(self.body,text="Current target plan",bg=BG,fg=TEXT,font=("Segoe UI Semibold",15)).pack(anchor="w",pady=(4,6))
        if not targets:
            return

        for rank,t in enumerate(targets,1):
            card=tk.Frame(self.body,bg=PANEL); card.pack(fill="x",pady=4)
            left=tk.Frame(card,bg=PANEL); left.pack(side="left",fill="both",expand=True,padx=14,pady=11)

            title=tk.Frame(left,bg=PANEL); title.pack(fill="x")
            tk.Label(title,text=f"#{rank}  {t['name']}",bg=PANEL,fg=TEXT,font=("Segoe UI Semibold",12)).pack(side="left")
            tk.Label(title,text=f"Priority {t['score']}",bg=PANEL_2,fg=TEXT,font=("Segoe UI",8,"bold"),padx=7,pady=3).pack(side="left",padx=8)

            tk.Label(left,text="  •  ".join(t["reasons"]),bg=PANEL,fg=MUTED,font=("Segoe UI",8)).pack(anchor="w",pady=(3,3))
            if t["habitats"]:
                tk.Label(left,text="Areas: "+", ".join(t["habitats"][:6]),bg=PANEL,fg=TEXT,font=("Segoe UI",8),wraplength=760,justify="left").pack(anchor="w")
            elif not t["entries"]:
                tk.Label(left,text="No imported spawn rules found for this target.",bg=PANEL,fg=MUTED,font=("Segoe UI",8)).pack(anchor="w")

            conditions=[]
            if t["times"]:conditions.append("Time: "+", ".join(t["times"][:3]))
            if t["weather"]:conditions.append("Weather: "+", ".join(t["weather"][:3]))
            if conditions:
                tk.Label(left,text="   •   ".join(conditions),bg=PANEL,fg=MUTED,font=("Segoe UI",8)).pack(anchor="w",pady=(2,0))

            combo=" + ".join(x[0] for x in t["snack"].get("combo",[]))
            if combo:
                tk.Label(left,text="Poké Snack: "+combo,bg=PANEL,fg=MUTED,font=("Segoe UI",8),wraplength=760,justify="left").pack(anchor="w",pady=(2,0))

            buttons=tk.Frame(card,bg=PANEL); buttons.pack(side="right",padx=12)
            tk.Button(buttons,text="Spawns",command=lambda n=t["name"]:self.open_spawn_finder(n),bg=ACCENT_2,fg="white",relief="flat",padx=10,pady=6).pack(fill="x",pady=2)
            tk.Button(buttons,text="Pokédex",command=lambda n=t["name"]:self.app.open_pokemon_detail(n),bg=PANEL_2,fg=TEXT,relief="flat",padx=10,pady=6).pack(fill="x",pady=2)
            if t["name"].casefold() in active:
                tk.Button(buttons,text="Remove Hunt",command=lambda n=t["name"]:self.remove_hunt(n),bg=PANEL_2,fg=TEXT,relief="flat",padx=10,pady=6).pack(fill="x",pady=2)


class MovePicker(tk.Toplevel):
    """Compact searchable move selector for a single team move slot."""

    def __init__(self, app, moves, current, callback):
        super().__init__(app)
        self.app = app
        self.moves = sorted(dict.fromkeys([m for m in moves if m]))
        self.callback = callback
        self.filtered = []

        self.title("Choose Move")
        self.configure(bg=BG)
        self.geometry("500x520")
        self.minsize(440, 420)
        self.transient(app)
        self.grab_set()

        tk.Label(
            self, text="Choose Move",
            bg=BG, fg=TEXT, font=("Segoe UI Semibold", 17)
        ).pack(anchor="w", padx=18, pady=(18, 4))

        tk.Label(
            self,
            text="Search this Pokémon's Cobblemon learnset.",
            bg=BG, fg=MUTED, font=("Segoe UI", 9)
        ).pack(anchor="w", padx=18, pady=(0, 10))

        self.query = tk.StringVar(value=current or "")
        entry = tk.Entry(
            self, textvariable=self.query,
            bg=PANEL, fg=TEXT, insertbackground=TEXT,
            relief="flat", font=("Segoe UI", 11)
        )
        entry.pack(fill="x", padx=18, ipady=8)
        entry.focus_set()
        entry.select_range(0, "end")
        entry.bind("<KeyRelease>", lambda e: self.refresh_list())

        body = tk.Frame(self, bg=BG)
        body.pack(fill="both", expand=True, padx=18, pady=10)

        self.listbox = tk.Listbox(
            body,
            bg=PANEL, fg=TEXT,
            selectbackground=ACCENT_2, selectforeground="white",
            relief="flat", bd=0, highlightthickness=0,
            font=("Segoe UI", 10)
        )
        scroll = tk.Scrollbar(body, orient="vertical", command=self.listbox.yview)
        self.listbox.config(yscrollcommand=scroll.set)

        self.listbox.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        self.listbox.bind("<Double-Button-1>", lambda e: self.choose())
        self.listbox.bind("<Return>", lambda e: self.choose())

        self.status = tk.Label(
            self, text="", bg=BG, fg=MUTED, font=("Segoe UI", 9)
        )
        self.status.pack(anchor="w", padx=18, pady=(0, 8))

        buttons = tk.Frame(self, bg=BG)
        buttons.pack(fill="x", padx=18, pady=(0, 18))

        tk.Button(
            buttons, text="Clear Move",
            command=lambda: self.submit(""),
            bg=PANEL_2, fg=TEXT, relief="flat", padx=12, pady=8
        ).pack(side="left")

        tk.Button(
            buttons, text="Cancel",
            command=self.destroy,
            bg=PANEL_2, fg=TEXT, relief="flat", padx=12, pady=8
        ).pack(side="right")

        tk.Button(
            buttons, text="Choose Move",
            command=self.choose,
            bg=ACCENT_2, fg="white", relief="flat", padx=14, pady=8
        ).pack(side="right", padx=(0, 8))

        self.refresh_list()

    def refresh_list(self):
        q = self.query.get().strip().lower()

        if q:
            self.filtered = [m for m in self.moves if q in m.lower()]
        else:
            self.filtered = list(self.moves)

        self.listbox.delete(0, "end")
        for move in self.filtered:
            self.listbox.insert("end", move)

        self.status.config(text=f"{len(self.filtered)} move{'s' if len(self.filtered) != 1 else ''} match")

        if self.filtered:
            self.listbox.selection_set(0)

    def choose(self):
        selected = self.listbox.curselection()
        if not selected:
            return
        idx = selected[0]
        if idx < len(self.filtered):
            self.submit(self.filtered[idx])

    def submit(self, value):
        self.callback(value)
        self.destroy()




# ---------------------------------------------------------------------------
# V1.3.3 — Competitive analysis performance cache
# ---------------------------------------------------------------------------

def competitive_species_cache(app):
    """Build lightweight competitive facts once per Pokédex version/session."""
    pokedex = getattr(app, "pokedex", []) or []
    signature = (
        len(pokedex),
        tuple((p.get("dex"), p.get("name")) for p in pokedex[:8]),
        tuple((p.get("dex"), p.get("name")) for p in pokedex[-8:]),
    )
    cached = getattr(app, "_competitive_species_cache", None)
    if cached and cached.get("signature") == signature:
        return cached["data"]

    data = {}
    for species in pokedex:
        name = str(species.get("name","") or "")
        moves = set(species_move_options(species))

        damaging_types = set()
        for move in moves:
            meta = get_move_metadata(move, allow_network=False) or {}
            if meta.get("power") and meta.get("type"):
                damaging_types.add(str(meta["type"]).title())

        data[name.casefold()] = {
            "species": species,
            "moves": moves,
            "damaging_types": damaging_types,
            "setup": moves & SETUP_MOVE_NAMES if "SETUP_MOVE_NAMES" in globals() else set(),
            "priority": moves & PRIORITY_MOVE_NAMES if "PRIORITY_MOVE_NAMES" in globals() else set(),
            "hazards": moves & HAZARD_MOVE_NAMES if "HAZARD_MOVE_NAMES" in globals() else set(),
            "status": moves & STATUS_PRESSURE_MOVE_NAMES if "STATUS_PRESSURE_MOVE_NAMES" in globals() else set(),
            "removal": moves & REMOVAL_MOVE_NAMES if "REMOVAL_MOVE_NAMES" in globals() else set(),
            "recovery": moves & ADVISOR_RECOVERY_MOVES if "ADVISOR_RECOVERY_MOVES" in globals() else set(),
            "speed_control": moves & ADVISOR_SPEED_CONTROL if "ADVISOR_SPEED_CONTROL" in globals() else set(),
            "pivot": moves & ADVISOR_PIVOT_MOVES if "ADVISOR_PIVOT_MOVES" in globals() else set(),
            "bst": species_bst(species),
            "speed": _species_speed(species) if "_species_speed" in globals() else int(species.get("spe",0) or 0),
        }

    app._competitive_species_cache = {"signature": signature, "data": data}
    return data

def invalidate_competitive_species_cache(app):
    try:
        app._competitive_species_cache = None
    except Exception:
        pass

# ---------------------------------------------------------------------------
# V1.3.1 — Team Threat Analyzer
# ---------------------------------------------------------------------------

SETUP_MOVE_NAMES = {
    "Swords Dance","Dragon Dance","Nasty Plot","Quiver Dance","Shell Smash",
    "Calm Mind","Bulk Up","Coil","Agility","Rock Polish","Shift Gear",
    "Belly Drum","Growth","Tail Glow","Geomancy","Clangorous Soul",
}

HAZARD_MOVE_NAMES = {
    "Stealth Rock","Spikes","Toxic Spikes","Sticky Web","Ceaseless Edge",
    "Stone Axe",
}

REMOVAL_MOVE_NAMES = {
    "Rapid Spin","Defog","Mortal Spin","Tidy Up",
}

PRIORITY_MOVE_NAMES = {
    "Extreme Speed","Quick Attack","Aqua Jet","Bullet Punch","Mach Punch",
    "Ice Shard","Shadow Sneak","Sucker Punch","Vacuum Wave","Water Shuriken",
    "First Impression","Fake Out","Grassy Glide","Jet Punch","Accelerock",
}

STATUS_PRESSURE_MOVE_NAMES = {
    "Spore","Sleep Powder","Hypnosis","Will-O-Wisp","Thunder Wave","Toxic",
    "Glare","Stun Spore","Nuzzle","Toxic Thread",
}

def _member_species(app, member):
    name = str((member or {}).get("pokemon","") or "").strip()
    if not name:
        return None
    for species in getattr(app, "pokedex", []) or []:
        if str(species.get("name","")).casefold() == name.casefold():
            return species
    return None

def _member_move_names(member):
    return [friendly_resource_name(x) for x in (member or {}).get("moves",[]) if str(x).strip()]

def _move_type_and_power(move_name):
    meta = get_move_metadata(move_name, allow_network=False) or {}
    return (
        str(meta.get("type","") or "").title(),
        meta.get("power"),
        str(meta.get("category","") or "").title()
    )

def _species_speed(species):
    try:
        return int((species or {}).get("spe",0) or 0)
    except Exception:
        return 0

def _type_multiplier_for_types(attacking_type, defending_types):
    mult = 1.0
    chart = TYPE_EFFECTIVENESS.get(attacking_type, {})
    for dtype in defending_types or []:
        mult *= chart.get(dtype, 1.0)
    return mult

def _species_stab_pressure(threat, target):
    best = 1.0
    best_type = ""
    for atype in threat.get("types",[]) or []:
        mult = _type_multiplier_for_types(atype, target.get("types",[]) or [])
        if mult > best:
            best = mult
            best_type = atype
    return best, best_type

def _team_super_effective_answers(members, threat):
    answers = []
    threat_types = threat.get("types",[]) or []
    for member, species in members:
        best = None
        for move in _member_move_names(member):
            mtype, power, category = _move_type_and_power(move)
            if not mtype or not power:
                continue
            mult = _type_multiplier_for_types(mtype, threat_types)
            if mult > 1:
                candidate = (mult, move, mtype)
                if best is None or candidate[0] > best[0]:
                    best = candidate
        if best:
            answers.append({
                "pokemon": species.get("name",""),
                "move": best[1],
                "type": best[2],
                "multiplier": best[0],
                "speed": _species_speed(species),
            })
    return answers

def analyze_team_threats(app, team, limit=30):
    """Score imported Pokémon against the currently selected six-member team."""
    members = []
    for member in (team or {}).get("members",[]) or []:
        species = _member_species(app, member)
        if species:
            members.append((member, species))

    if not members:
        return []

    team_names = {s.get("name","").casefold() for _,s in members}
    team_speeds = [_species_speed(s) for _,s in members if _species_speed(s)]
    median_speed = sorted(team_speeds)[len(team_speeds)//2] if team_speeds else 0

    has_removal = any(
        move in REMOVAL_MOVE_NAMES
        for member,_ in members
        for move in _member_move_names(member)
    )

    comp_cache = competitive_species_cache(app)
    results = []
    for threat in getattr(app, "pokedex", []) or []:
        name = str(threat.get("name","") or "")
        if not name or name.casefold() in team_names:
            continue

        score = 0
        reasons = []
        weak_targets = []
        resisted_targets = []

        # STAB matchup pressure.
        for member, target in members:
            mult, atype = _species_stab_pressure(threat, target)
            if mult >= 4:
                score += 18
                weak_targets.append(f"{target.get('name')} ({atype} ×{int(mult)})")
            elif mult >= 2:
                score += 10
                weak_targets.append(f"{target.get('name')} ({atype} ×2)")
            elif mult < 1:
                resisted_targets.append(target.get("name",""))

        if len(weak_targets) >= 3:
            score += 12
            reasons.append(f"STAB threatens {len(weak_targets)}/{len(members)} team members")
        elif weak_targets:
            reasons.append("Super-effective STAB into " + ", ".join(weak_targets[:3]))

        # Natural speed pressure.
        threat_speed = _species_speed(threat)
        slower_count = sum(1 for _,s in members if threat_speed > _species_speed(s))
        if threat_speed and slower_count:
            score += min(18, slower_count * 3)
            if slower_count >= 4:
                reasons.append(f"Base {threat_speed} Speed outspeeds {slower_count}/{len(members)} naturally")

        # Learnset-based pressure.
        facts = comp_cache.get(name.casefold(), {})
        moves = facts.get("moves", set())
        setup = sorted(facts.get("setup", moves & SETUP_MOVE_NAMES))
        priority = sorted(facts.get("priority", moves & PRIORITY_MOVE_NAMES))
        hazards = sorted(facts.get("hazards", moves & HAZARD_MOVE_NAMES))
        status = sorted(facts.get("status", moves & STATUS_PRESSURE_MOVE_NAMES))

        if setup:
            score += 8
            reasons.append("Setup threat: " + ", ".join(setup[:2]))
        if priority:
            score += 5
            reasons.append("Priority access: " + ", ".join(priority[:2]))
        if hazards and not has_removal:
            score += 7
            reasons.append("Hazard pressure with no removal on your team")
        if status:
            score += 4
            reasons.append("Status pressure: " + ", ".join(status[:2]))

        # How many actual selected attacks can answer it?
        answers = _team_super_effective_answers(members, threat)
        if not answers:
            score += 18
            reasons.append("No selected team move hits it super effectively")
        elif len(answers) == 1:
            score += 9
            reasons.append(f"Only {answers[0]['pokemon']} has a selected super-effective answer")

        # Bulk / wall tendency: high defenses and few answers.
        try:
            physical_bulk = int(threat.get("hp",0) or 0) + int(threat.get("def",0) or 0)
            special_bulk = int(threat.get("hp",0) or 0) + int(threat.get("spd",0) or 0)
        except Exception:
            physical_bulk = special_bulk = 0
        if max(physical_bulk, special_bulk) >= 210 and len(answers) <= 1:
            score += 7
            reasons.append("High natural bulk may make it difficult to break")

        score = min(100, score)
        if score >= 75:
            level = "CRITICAL"
        elif score >= 55:
            level = "HIGH"
        elif score >= 35:
            level = "MODERATE"
        else:
            level = "LOW"

        # Best answers first: SE coverage, then speed.
        answers.sort(key=lambda x: (x["multiplier"], x["speed"]), reverse=True)

        results.append({
            "name": name,
            "dex": threat.get("dex",0),
            "score": score,
            "level": level,
            "types": list(threat.get("types",[]) or []),
            "speed": threat_speed,
            "reasons": reasons[:6],
            "answers": answers[:3],
            "species": threat,
        })

    results.sort(key=lambda x: (-x["score"], x["name"].lower()))
    return results[:limit]


# ---------------------------------------------------------------------------
# V1.3.2 — Team Advisor
# ---------------------------------------------------------------------------

ADVISOR_RECOVERY_MOVES = {
    "Recover","Roost","Slack Off","Soft-Boiled","Milk Drink","Moonlight",
    "Morning Sun","Synthesis","Shore Up","Strength Sap","Wish",
}
ADVISOR_PIVOT_MOVES = {"U-turn","Volt Switch","Flip Turn","Parting Shot","Chilly Reception"}
ADVISOR_SPEED_CONTROL = {
    "Thunder Wave","Glare","Icy Wind","Electroweb","Tailwind","Trick Room",
    "Sticky Web",
}

def _team_structural_summary(app, team):
    members=[]
    for member in (team or {}).get("members",[]) or []:
        species=_member_species(app,member)
        if species:
            members.append((member,species))

    summary={
        "members":members,
        "weak_counts":{},
        "resist_counts":{},
        "immune_counts":{},
        "has_removal":False,
        "has_hazards":False,
        "has_recovery":False,
        "has_speed_control":False,
        "has_pivot":False,
    }

    for member,species in members:
        types=species.get("types",[]) or []
        for attack_type in TYPE_EFFECTIVENESS:
            mult=_type_multiplier_for_types(attack_type,types)
            if mult>1:
                summary["weak_counts"][attack_type]=summary["weak_counts"].get(attack_type,0)+1
            elif mult==0:
                summary["immune_counts"][attack_type]=summary["immune_counts"].get(attack_type,0)+1
            elif mult<1:
                summary["resist_counts"][attack_type]=summary["resist_counts"].get(attack_type,0)+1

        moves=set(_member_move_names(member))
        summary["has_removal"] |= bool(moves & REMOVAL_MOVE_NAMES)
        summary["has_hazards"] |= bool(moves & HAZARD_MOVE_NAMES)
        summary["has_recovery"] |= bool(moves & ADVISOR_RECOVERY_MOVES)
        summary["has_speed_control"] |= bool(moves & ADVISOR_SPEED_CONTROL)
        summary["has_pivot"] |= bool(moves & ADVISOR_PIVOT_MOVES)

    return summary

def _candidate_defensive_value(species, problem_types):
    value=0
    details=[]
    stypes=species.get("types",[]) or []
    for atype in problem_types:
        mult=_type_multiplier_for_types(atype,stypes)
        if mult==0:
            value+=5
            details.append(f"immune to {atype}")
        elif mult<1:
            value+=3
            details.append(f"resists {atype}")
        elif mult>1:
            value-=4
    return value,details

def _candidate_utility_value(species, needs, facts=None):
    facts = facts or {}
    moves = facts.get("moves")
    if moves is None:
        moves = set(species_move_options(species))
    value=0
    details=[]
    if needs.get("removal") and (facts.get("removal") or moves & REMOVAL_MOVE_NAMES):
        value+=8; details.append("adds hazard removal")
    if needs.get("hazards") and (facts.get("hazards") or moves & HAZARD_MOVE_NAMES):
        value+=5; details.append("adds entry hazards")
    if needs.get("recovery") and (facts.get("recovery") or moves & ADVISOR_RECOVERY_MOVES):
        value+=4; details.append("has reliable recovery")
    if needs.get("speed_control") and (facts.get("speed_control") or moves & ADVISOR_SPEED_CONTROL):
        value+=5; details.append("adds speed control")
    if needs.get("pivot") and (facts.get("pivot") or moves & ADVISOR_PIVOT_MOVES):
        value+=3; details.append("adds pivoting")
    return value,details


def _candidate_threat_answer_value(candidate, threats, facts=None):
    value=0
    details=[]
    ctypes=candidate.get("types",[]) or []
    facts=facts or {}
    damaging_types=facts.get("damaging_types", set())
    answered=[]

    for threat in threats[:12]:
        defensive=any(
            _type_multiplier_for_types(atype,ctypes)<1
            for atype in threat.get("types",[]) or []
        )
        offensive=any(
            _type_multiplier_for_types(mtype,threat.get("types",[]) or [])>1
            for mtype in damaging_types
        )

        if defensive and offensive:
            value+=4; answered.append(threat["name"])
        elif defensive or offensive:
            value+=2; answered.append(threat["name"])

    if answered:
        details.append("helps against "+", ".join(answered[:3]))
    return value,details,answered


def _existing_member_move_fixes(app, team, summary):
    fixes=[]
    comp_cache = competitive_species_cache(app)
    needs={
        "removal":not summary["has_removal"],
        "hazards":not summary["has_hazards"],
        "recovery":not summary["has_recovery"],
        "speed_control":not summary["has_speed_control"],
        "pivot":not summary["has_pivot"],
    }

    categories=[
        ("removal",REMOVAL_MOVE_NAMES,"hazard removal"),
        ("hazards",HAZARD_MOVE_NAMES,"entry hazards"),
        ("recovery",ADVISOR_RECOVERY_MOVES,"reliable recovery"),
        ("speed_control",ADVISOR_SPEED_CONTROL,"speed control"),
        ("pivot",ADVISOR_PIVOT_MOVES,"pivoting"),
    ]

    for member,species in summary["members"]:
        selected=set(_member_move_names(member))
        learnable=set(comp_cache.get(species.get("name","").casefold(), {}).get("moves", set()))
        for key,pool,label in categories:
            if not needs[key]:
                continue
            options=sorted((learnable & pool)-selected)
            if options:
                fixes.append({
                    "pokemon":species.get("name",""),
                    "move":options[0],
                    "reason":f"adds {label} without changing Pokémon",
                })
    return fixes[:8]

def analyze_team_advice(app, team):
    comp_cache=competitive_species_cache(app)
    summary=_team_structural_summary(app,team)
    threats=analyze_team_threats(app,team,limit=25)
    serious=[x for x in threats if x["level"] in ("CRITICAL","HIGH")]

    problems=[]
    problem_types=[]
    for atype,count in sorted(summary["weak_counts"].items(),key=lambda x:(-x[1],x[0])):
        resist=summary["resist_counts"].get(atype,0)+summary["immune_counts"].get(atype,0)
        if count>=3 and resist<=1:
            problems.append({
                "kind":"typing",
                "severity":"HIGH" if count>=4 else "MODERATE",
                "title":f"{atype} pressure",
                "detail":f"{count} team members are weak to {atype}, with only {resist} resistance/immunity answer{'s' if resist!=1 else ''}.",
            })
            problem_types.append(atype)

    utility_checks=[
        ("has_removal","Hazard removal","No selected team move removes entry hazards."),
        ("has_hazards","Entry hazards","No selected team move sets Stealth Rock, Spikes, Toxic Spikes, or Sticky Web."),
        ("has_recovery","Reliable recovery","No selected team member currently has a reliable recovery move."),
        ("has_speed_control","Speed control","No selected team move provides obvious speed control."),
        ("has_pivot","Pivoting","The selected moves provide no U-turn / Volt Switch / Flip Turn style pivoting."),
    ]
    for key,title,detail in utility_checks:
        if not summary[key]:
            problems.append({"kind":"utility","severity":"MODERATE","title":title,"detail":detail})

    if serious:
        problems.insert(0,{
            "kind":"threats",
            "severity":"HIGH",
            "title":"High-priority matchup threats",
            "detail":f"{len(serious)} imported Pokémon currently score HIGH or CRITICAL. Top threats: "+", ".join(x["name"] for x in serious[:4])+".",
        })

    needs={
        "removal":not summary["has_removal"],
        "hazards":not summary["has_hazards"],
        "recovery":not summary["has_recovery"],
        "speed_control":not summary["has_speed_control"],
        "pivot":not summary["has_pivot"],
    }

    current_names={s.get("name","").casefold() for _,s in summary["members"]}
    candidates=[]
    for species in getattr(app,"pokedex",[]) or []:
        if str(species.get("name","")).casefold() in current_names:
            continue
        score=0
        reasons=[]

        facts=comp_cache.get(str(species.get("name","")).casefold(), {})
        defensive,dwhy=_candidate_defensive_value(species,problem_types[:4])
        utility,uwhy=_candidate_utility_value(species,needs,facts)
        threat_value,twhy,answered=_candidate_threat_answer_value(species,serious,facts)

        score+=defensive+utility+threat_value

        # Useful baseline stats without overclaiming exact battle performance.
        bst=facts.get("bst", species_bst(species))
        if bst>=550: score+=3
        elif bst>=500: score+=2
        if facts.get("speed", _species_speed(species))>=100 and needs["speed_control"]: score+=2

        reasons.extend(dwhy[:2]); reasons.extend(uwhy[:2]); reasons.extend(twhy[:1])
        if score>0:
            candidates.append({
                "species":species,
                "name":species.get("name",""),
                "score":score,
                "reasons":reasons[:5],
                "answers":answered,
            })

    candidates.sort(key=lambda x:(-x["score"],x["name"].lower()))
    move_fixes=_existing_member_move_fixes(app,team,summary)

    return {
        "summary":summary,
        "threats":threats,
        "serious_threats":serious,
        "problems":problems,
        "move_fixes":move_fixes,
        "candidates":candidates[:20],
    }

class TeamAdvisorWindow(tk.Toplevel):
    def __init__(self,parent,app,team):
        super().__init__(parent)
        self.app=app
        self.team=team
        self.title("Team Advisor — Cobblemon Companion")
        self.configure(bg=BG)
        self.geometry("1060x780")
        self.minsize(880,640)
        self.analysis=None
        self.build_loading_ui()
        self.after(30, self.start_analysis)

    def build_loading_ui(self):
        self.loading_frame=tk.Frame(self,bg=BG)
        self.loading_frame.pack(fill="both",expand=True)
        tk.Label(
            self.loading_frame,text="Team Advisor",
            bg=BG,fg=TEXT,font=("Segoe UI",20,"bold")
        ).pack(pady=(70,8))
        self.loading_label=tk.Label(
            self.loading_frame,
            text="Analyzing team structure and scoring recommendations…",
            bg=BG,fg=MUTED,font=("Segoe UI",10)
        )
        self.loading_label.pack()
        self.progress=tk.Label(
            self.loading_frame,text="This runs in the background — the app will stay responsive.",
            bg=BG,fg=MUTED,font=("Segoe UI",8)
        )
        self.progress.pack(pady=(7,0))

    def start_analysis(self):
        def worker():
            try:
                result=analyze_team_advice(self.app,self.team)
                error=None
            except Exception as exc:
                result=None
                error=str(exc)

            def done():
                if not self.winfo_exists():
                    return
                if error:
                    self.loading_label.config(text="Team Advisor could not finish analysis.")
                    self.progress.config(text=error)
                    return
                self.analysis=result
                try:self.loading_frame.destroy()
                except Exception:pass
                self.build_ui()

            try:self.after(0,done)
            except Exception:pass

        threading.Thread(target=worker,daemon=True).start()

    def build_ui(self):
        top=tk.Frame(self,bg=BG); top.pack(fill="x",padx=20,pady=(18,10))
        tk.Label(top,text="Team Advisor",bg=BG,fg=TEXT,font=("Segoe UI",20,"bold")).pack(anchor="w")
        tk.Label(
            top,
            text="Turns the Threat Analyzer into actionable fixes using your imported Pokémon, learnsets and current selected moves.",
            bg=BG,fg=MUTED,font=("Segoe UI",9)
        ).pack(anchor="w",pady=(4,0))

        canvas=tk.Canvas(self,bg=BG,highlightthickness=0)
        sb=tk.Scrollbar(self,orient="vertical",command=canvas.yview)
        body=tk.Frame(canvas,bg=BG)
        body.bind("<Configure>",lambda e:canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0,0),window=body,anchor="nw",tags=("body",))
        canvas.bind("<Configure>",lambda e:canvas.itemconfigure("body",width=e.width))
        canvas.configure(yscrollcommand=sb.set)
        canvas.pack(side="left",fill="both",expand=True,padx=(20,0),pady=(0,18))
        sb.pack(side="right",fill="y",padx=(0,12),pady=(0,18))

        self.section(body,"What needs attention",self.problem_widgets)
        self.section(body,"Fix it without replacing a Pokémon",self.move_fix_widgets)
        self.section(body,"Recommended Pokémon",self.candidate_widgets)

    def section(self,parent,title,builder):
        box=tk.Frame(parent,bg=PANEL); box.pack(fill="x",pady=(0,12))
        tk.Label(box,text=title,bg=PANEL,fg=TEXT,font=("Segoe UI",13,"bold")).pack(anchor="w",padx=14,pady=(12,8))
        builder(box)
        return box

    def problem_widgets(self,box):
        rows=self.analysis["problems"]
        if not rows:
            tk.Label(box,text="No major structural problems detected from the current data.",bg=PANEL,fg=MUTED,font=("Segoe UI",9)).pack(anchor="w",padx=14,pady=(0,14))
            return
        for p in rows[:10]:
            row=tk.Frame(box,bg=PANEL_2); row.pack(fill="x",padx=14,pady=(0,7))
            tk.Label(row,text=f"{p['severity']}  •  {p['title']}",bg=PANEL_2,fg=TEXT,font=("Segoe UI",9,"bold")).pack(anchor="w",padx=10,pady=(8,2))
            tk.Label(row,text=p["detail"],bg=PANEL_2,fg=MUTED,font=("Segoe UI",8),wraplength=940,justify="left").pack(anchor="w",padx=10,pady=(0,8))

    def move_fix_widgets(self,box):
        fixes=self.analysis["move_fixes"]
        if not fixes:
            tk.Label(box,text="No obvious one-move utility fixes were found from the imported learnsets.",bg=PANEL,fg=MUTED,font=("Segoe UI",9)).pack(anchor="w",padx=14,pady=(0,14))
            return
        for f in fixes:
            row=tk.Frame(box,bg=PANEL_2); row.pack(fill="x",padx=14,pady=(0,7))
            tk.Label(row,text=f"{f['pokemon']}  →  {f['move']}",bg=PANEL_2,fg=TEXT,font=("Segoe UI",9,"bold")).pack(anchor="w",padx=10,pady=(8,2))
            tk.Label(row,text=f["reason"],bg=PANEL_2,fg=MUTED,font=("Segoe UI",8)).pack(anchor="w",padx=10,pady=(0,8))

    def candidate_widgets(self,box):
        rows=self.analysis["candidates"]
        if not rows:
            tk.Label(box,text="No replacement recommendations could be scored from the current imported Pokédex.",bg=PANEL,fg=MUTED,font=("Segoe UI",9)).pack(anchor="w",padx=14,pady=(0,14))
            return
        for rank,c in enumerate(rows[:12],1):
            row=tk.Frame(box,bg=PANEL_2); row.pack(fill="x",padx=14,pady=(0,8))
            head=tk.Frame(row,bg=PANEL_2); head.pack(fill="x",padx=10,pady=(8,2))
            tk.Label(head,text=f"#{rank}  {c['name']}",bg=PANEL_2,fg=TEXT,font=("Segoe UI",10,"bold")).pack(side="left")
            tk.Label(head,text=f"Fit score {c['score']}",bg=PANEL,fg=TEXT,font=("Segoe UI",8,"bold"),padx=7,pady=3).pack(side="right")
            reason="  •  ".join(c["reasons"]) if c["reasons"] else "Improves the team's structural matchup profile."
            tk.Label(row,text=reason,bg=PANEL_2,fg=MUTED,font=("Segoe UI",8),wraplength=850,justify="left").pack(anchor="w",padx=10,pady=(2,6))
            buttons=tk.Frame(row,bg=PANEL_2); buttons.pack(fill="x",padx=10,pady=(0,8))
            tk.Button(buttons,text="Open Pokédex",bg=PANEL,fg=TEXT,relief="flat",padx=9,pady=4,
                      command=lambda s=c["species"]:self.open_dex(s)).pack(side="left")
            tk.Button(buttons,text="Find Spawns",bg=PANEL,fg=TEXT,relief="flat",padx=9,pady=4,
                      command=lambda s=c["species"]:self.find_spawns(s)).pack(side="left",padx=(6,0))

    def open_dex(self,species):
        try:
            PokemonDetailWindow(self,self.app,species)
        except Exception:
            pass

    def find_spawns(self,species):
        try:
            page=self.app.pages.get("Spawn Finder")
            if page:
                self.app.show_page("Spawn Finder")
                if hasattr(page,"search_var"):
                    page.search_var.set(species.get("name",""))
                if hasattr(page,"search"):
                    page.search()
                self.destroy()
        except Exception:
            pass

class ThreatAnalyzerWindow(tk.Toplevel):
    def __init__(self, parent, app, team):
        super().__init__(parent)
        self.app = app
        self.team = team
        self.title("Team Threat Analyzer — Cobblemon Companion")
        self.configure(bg=BG)
        self.geometry("1040x760")
        self.minsize(860,620)
        self.results = []
        self.filter_var = tk.StringVar(value="All")
        self.search_var = tk.StringVar()
        self.build_loading_ui()
        self.after(30, self.start_analysis)

    def build_loading_ui(self):
        self.loading_frame=tk.Frame(self,bg=BG)
        self.loading_frame.pack(fill="both",expand=True)
        tk.Label(
            self.loading_frame,text="Team Threat Analyzer",
            bg=BG,fg=TEXT,font=("Segoe UI",20,"bold")
        ).pack(pady=(70,8))
        self.loading_label=tk.Label(
            self.loading_frame,
            text="Scanning the imported Pokédex…",
            bg=BG,fg=MUTED,font=("Segoe UI",10)
        )
        self.loading_label.pack()
        tk.Label(
            self.loading_frame,text="Analysis runs in the background.",
            bg=BG,fg=MUTED,font=("Segoe UI",8)
        ).pack(pady=(7,0))

    def start_analysis(self):
        def worker():
            try:
                result=analyze_team_threats(self.app,self.team,limit=60)
                error=None
            except Exception as exc:
                result=[]
                error=str(exc)

            def done():
                if not self.winfo_exists():
                    return
                if error:
                    self.loading_label.config(text="Threat analysis could not finish: "+error)
                    return
                self.results=result
                try:self.loading_frame.destroy()
                except Exception:pass
                self.build_ui()

            try:self.after(0,done)
            except Exception:pass

        threading.Thread(target=worker,daemon=True).start()

    def build_ui(self):
        top = tk.Frame(self,bg=BG)
        top.pack(fill="x",padx=20,pady=(18,10))
        tk.Label(top,text="Team Threat Analyzer",bg=BG,fg=TEXT,font=("Segoe UI",20,"bold")).pack(anchor="w")
        tk.Label(
            top,
            text="Scans your imported Pokédex against this team's typings, selected moves, speed, hazards, setup and status pressure.",
            bg=BG,fg=MUTED,font=("Segoe UI",9)
        ).pack(anchor="w",pady=(4,10))

        controls=tk.Frame(top,bg=BG); controls.pack(fill="x")
        for label in ("All","Critical","High","Moderate"):
            tk.Button(
                controls,text=label,
                command=lambda x=label:self.set_filter(x),
                bg=PANEL_2,fg=TEXT,relief="flat",padx=12,pady=6
            ).pack(side="left",padx=(0,6))
        tk.Entry(controls,textvariable=self.search_var,bg=PANEL_2,fg=TEXT,insertbackground=TEXT,relief="flat").pack(side="right",fill="x",expand=True,padx=(30,0))
        self.search_var.trace_add("write",lambda *_:self.render())

        self.canvas=tk.Canvas(self,bg=BG,highlightthickness=0)
        sb=tk.Scrollbar(self,orient="vertical",command=self.canvas.yview)
        self.body=tk.Frame(self.canvas,bg=BG)
        self.body.bind("<Configure>",lambda e:self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0,0),window=self.body,anchor="nw",tags=("body",))
        self.canvas.bind("<Configure>",lambda e:self.canvas.itemconfigure("body",width=e.width))
        self.canvas.configure(yscrollcommand=sb.set)
        self.canvas.pack(side="left",fill="both",expand=True,padx=(20,0),pady=(0,18))
        sb.pack(side="right",fill="y",padx=(0,12),pady=(0,18))
        self.render()

    def set_filter(self,value):
        self.filter_var.set(value)
        self.render()

    def render(self):
        for w in self.body.winfo_children():
            w.destroy()

        query=self.search_var.get().strip().casefold()
        wanted=self.filter_var.get().upper()
        rows=[]
        for r in self.results:
            if wanted!="ALL" and r["level"]!=wanted:
                continue
            if query and query not in r["name"].casefold():
                continue
            rows.append(r)

        if not rows:
            tk.Label(self.body,text="No threats match this filter.",bg=BG,fg=MUTED,font=("Segoe UI",10)).pack(anchor="w",pady=20)
            return

        for i,r in enumerate(rows):
            card=tk.Frame(self.body,bg=PANEL)
            card.pack(fill="x",pady=(0,9))

            head=tk.Frame(card,bg=PANEL)
            head.pack(fill="x",padx=14,pady=(12,6))
            tk.Label(head,text=f"#{int(r['dex']):04d}  {r['name']}",bg=PANEL,fg=TEXT,font=("Segoe UI",13,"bold")).pack(side="left")
            tk.Label(head,text=f"{r['level']}  {r['score']}/100",bg=PANEL_2,fg=TEXT,font=("Segoe UI",9,"bold"),padx=9,pady=4).pack(side="right")

            meta=" / ".join(r["types"]) or "Unknown type"
            if r["speed"]:
                meta += f"   •   Base Speed {r['speed']}"
            tk.Label(card,text=meta,bg=PANEL,fg=MUTED,font=("Segoe UI",8)).pack(anchor="w",padx=14)

            if r["reasons"]:
                tk.Label(card,text="Why:  "+"  •  ".join(r["reasons"]),bg=PANEL,fg=TEXT,font=("Segoe UI",8),wraplength=920,justify="left").pack(anchor="w",padx=14,pady=(7,3))

            if r["answers"]:
                answer_text="Best selected-move answers:  "+", ".join(
                    f"{a['pokemon']} — {a['move']} (×{a['multiplier']:g})"
                    for a in r["answers"]
                )
            else:
                answer_text="Best selected-move answers:  None detected"
            tk.Label(card,text=answer_text,bg=PANEL,fg=MUTED,font=("Segoe UI",8),wraplength=920,justify="left").pack(anchor="w",padx=14,pady=(2,8))

            buttons=tk.Frame(card,bg=PANEL)
            buttons.pack(fill="x",padx=14,pady=(0,12))
            tk.Button(
                buttons,text="Open Pokédex",bg=PANEL_2,fg=TEXT,relief="flat",padx=10,pady=5,
                command=lambda s=r["species"]:self.open_dex(s)
            ).pack(side="left")
            tk.Button(
                buttons,text="Find Spawns",bg=PANEL_2,fg=TEXT,relief="flat",padx=10,pady=5,
                command=lambda s=r["species"]:self.find_spawns(s)
            ).pack(side="left",padx=(6,0))

    def open_dex(self,species):
        try:
            PokemonDetailWindow(self, self.app, species)
        except Exception:
            try:
                self.app.open_pokemon_detail(species)
            except Exception:
                pass

    def find_spawns(self,species):
        name=species.get("name","")
        try:
            page=self.app.pages.get("Spawn Finder")
            if page:
                self.app.show_page("Spawn Finder")
                if hasattr(page,"search_var"):
                    page.search_var.set(name)
                if hasattr(page,"search"):
                    page.search()
                self.destroy()
        except Exception:
            pass


# ---------------------------------------------------------------------------
# V1.4.0 — Navigation 2.0 embedded analysis pages
# ---------------------------------------------------------------------------

class EmbeddedAnalysisBase(tk.Frame):
    def __init__(self, master, app, team, title):
        super().__init__(master, bg=BG)
        self.app = app
        self.team = team
        self.view_title = title

    def nav_header(self, title, subtitle=""):
        bar = tk.Frame(self, bg=BG)
        bar.pack(fill="x", padx=20, pady=(14, 8))

        tk.Button(
            bar,
            text="← Back",
            command=self.app.go_back,
            bg=PANEL_2,
            fg=TEXT,
            relief="flat",
            padx=12,
            pady=7
        ).pack(side="left", padx=(0, 12))

        labels = tk.Frame(bar, bg=BG)
        labels.pack(side="left", fill="x", expand=True)
        tk.Label(
            labels, text=title,
            bg=BG, fg=TEXT,
            font=("Segoe UI Semibold", 19)
        ).pack(anchor="w")
        if subtitle:
            tk.Label(
                labels, text=subtitle,
                bg=BG, fg=MUTED,
                font=("Segoe UI", 8),
                wraplength=760,
                justify="left"
            ).pack(anchor="w", pady=(2, 0))
        return bar


class EmbeddedCompetitiveAnalysisPage(EmbeddedAnalysisBase):
    def __init__(self, master, app, team):
        super().__init__(master, app, team, "Competitive Analysis")

        top = self.nav_header(
            f"Competitive Analysis — {team.get('name','Team')}",
            "Full offensive coverage, utility, role, metadata and matchup analysis."
        )

        self.refresh_button = tk.Button(
            top, text="Refresh Move Data",
            command=self.refresh_online,
            bg=ACCENT_2, fg="white",
            relief="flat", padx=12, pady=7
        )
        self.refresh_button.pack(side="right")

        tk.Button(
            top, text="Threat Analyzer",
            command=lambda:self.app.open_threat_analyzer(self.team),
            bg=ACCENT, fg="white",
            relief="flat", padx=12, pady=7
        ).pack(side="right", padx=(0,8))

        tk.Button(
            top, text="Team Advisor",
            command=lambda:self.app.open_team_advisor(self.team),
            bg=ACCENT, fg="white",
            relief="flat", padx=12, pady=7
        ).pack(side="right", padx=(0,8))

        self.canvas=tk.Canvas(self,bg=BG,highlightthickness=0)
        scroll=tk.Scrollbar(self,orient="vertical",command=self.canvas.yview)
        self.body=tk.Frame(self.canvas,bg=BG)
        win=self.canvas.create_window((0,0),window=self.body,anchor="nw")
        self.body.bind("<Configure>",lambda e:self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>",lambda e:self.canvas.itemconfigure(win,width=e.width))
        self.canvas.configure(yscrollcommand=scroll.set)
        self.canvas.pack(side="left",fill="both",expand=True,padx=(20,0),pady=(0,20))
        scroll.pack(side="right",fill="y",padx=(0,20),pady=(0,20))
        self.render()

    def refresh_online(self):
        moves={
            str(x).strip()
            for m in self.team["members"]
            for x in m.get("moves",[])
            if str(x).strip()
        }
        if not moves:
            return

        self.refresh_button.config(text="Refreshing…", state="disabled")

        def worker():
            for move in moves:
                get_move_metadata(move,allow_network=True)

            def done():
                if not self.winfo_exists():
                    return
                self.render()
                unresolved=[
                    move for move in moves
                    if not get_move_metadata(move,allow_network=False)
                ]
                self.refresh_button.config(
                    text=(
                        f"Refresh Move Data ({len(unresolved)} unresolved)"
                        if unresolved else
                        "Move Data Up to Date ✓"
                    ),
                    state="normal"
                )
            try:self.after(0,done)
            except Exception:pass

        threading.Thread(target=worker,daemon=True).start()

    def section(self,title):
        box=tk.Frame(self.body,bg=PANEL)
        box.pack(fill="x",pady=5)
        tk.Label(
            box,text=title,bg=PANEL,fg=TEXT,
            font=("Segoe UI Semibold",13)
        ).pack(anchor="w",padx=14,pady=(10,6))
        return box

    def render(self):
        for w in self.body.winfo_children():
            w.destroy()

        meta=selected_move_metadata(self.team["members"],allow_network=False)
        a=analyze_team(self.team["members"],self.app.pokedex,meta)

        box=self.section("Team Health")
        if not a["issues"]:
            tk.Label(
                box,text="✓ No major issues detected from the current analysis rules.",
                bg=PANEL,fg=GOOD,font=("Segoe UI",10)
            ).pack(anchor="w",padx=14,pady=(0,10))
        else:
            for x in a["issues"]:
                tk.Label(
                    box,text="⚠  "+x,bg=PANEL,fg=TEXT,
                    font=("Segoe UI",9),anchor="w",justify="left"
                ).pack(fill="x",padx=14,pady=2)
        for x in a["strengths"]:
            tk.Label(
                box,text="✓  "+x,bg=PANEL,fg=GOOD,
                font=("Segoe UI",9),anchor="w",justify="left"
            ).pack(fill="x",padx=14,pady=2)
        tk.Frame(box,bg=PANEL,height=8).pack()

        box=self.section("Roles & Stat Profile")
        for name,role in a["roles"]:
            tk.Label(
                box,text=f"{name}: {role}",
                bg=PANEL,fg=TEXT,font=("Segoe UI",9)
            ).pack(anchor="w",padx=14,pady=1)
        if a["stats"]:
            st="   •   ".join(f"{k} avg {v['avg']}" for k,v in a["stats"].items())
            tk.Label(
                box,text=st,bg=PANEL,fg=MUTED,
                font=("Segoe UI",8),wraplength=900,justify="left"
            ).pack(anchor="w",padx=14,pady=(6,10))

        box=self.section("Offensive Coverage")
        tk.Label(
            box,
            text=f"Selected attacks: {a['physical']} physical • {a['special']} special • {a['status']} status",
            bg=PANEL,fg=MUTED,font=("Segoe UI",9)
        ).pack(anchor="w",padx=14,pady=(0,6))
        grid=tk.Frame(box,bg=PANEL)
        grid.pack(fill="x",padx=10,pady=(0,10))
        for c in range(6):
            grid.grid_columnconfigure(c,weight=1,uniform="off")
        for i,tp in enumerate(TYPE_EFFECTIVENESS):
            count=a["offense"][tp]
            b=tk.Frame(grid,bg=PANEL_2)
            b.grid(row=i//6,column=i%6,sticky="nsew",padx=2,pady=2)
            tk.Label(b,text=tp,bg=PANEL_2,fg=TEXT,font=("Segoe UI Semibold",8)).pack(pady=(5,0))
            tk.Label(
                b,text=f"{count} SE option{'s' if count!=1 else ''}",
                bg=PANEL_2,fg=MUTED,font=("Segoe UI",7)
            ).pack(pady=(0,5))

        box=self.section("Team Utility")
        for group,hits in a["utility"].items():
            tk.Label(
                box,
                text=f"{group}: {', '.join(hits) if hits else 'None'}",
                bg=PANEL,fg=TEXT if hits else MUTED,
                font=("Segoe UI",9),anchor="w",justify="left"
            ).pack(fill="x",padx=14,pady=2)
        tk.Frame(box,bg=PANEL,height=8).pack()

        missing=[
            m for m in {
                str(x).strip()
                for member in self.team["members"]
                for x in member.get("moves",[])
                if str(x).strip()
            }
            if not meta.get(m.lower())
        ]
        if missing:
            box=self.section("Move Metadata")
            tk.Label(
                box,
                text="Some selected moves have not been analyzed yet: "+", ".join(sorted(missing)),
                bg=PANEL,fg=MUTED,font=("Segoe UI",9),
                wraplength=900,justify="left"
            ).pack(anchor="w",padx=14,pady=(0,4))
            tk.Label(
                box,
                text="Use “Refresh Move Data” above. Resolved move data is cached locally.",
                bg=PANEL,fg=MUTED,font=("Segoe UI",8),
                wraplength=900,justify="left"
            ).pack(anchor="w",padx=14,pady=(0,10))


class EmbeddedThreatAnalyzerPage(EmbeddedAnalysisBase):
    def __init__(self, master, app, team):
        super().__init__(master, app, team, "Threat Analyzer")
        self.results=[]
        self.filter_var=tk.StringVar(value="All")
        self.search_var=tk.StringVar()

        top=self.nav_header(
            "Team Threat Analyzer",
            "Scans the imported Pokédex against this team's typings, moves, speed and utility."
        )
        tk.Button(
            top,text="Team Advisor",
            command=lambda:self.app.open_team_advisor(self.team),
            bg=ACCENT,fg="white",relief="flat",padx=12,pady=7
        ).pack(side="right")

        self.loading=tk.Frame(self,bg=BG)
        self.loading.pack(fill="both",expand=True)
        tk.Label(
            self.loading,text="Scanning the imported Pokédex…",
            bg=BG,fg=MUTED,font=("Segoe UI",11)
        ).pack(pady=(80,8))
        tk.Label(
            self.loading,text="Analysis is running in the background.",
            bg=BG,fg=MUTED,font=("Segoe UI",8)
        ).pack()
        self.after(30,self.start_analysis)

    def start_analysis(self):
        def worker():
            try:
                result=analyze_team_threats(self.app,self.team,limit=60)
                error=None
            except Exception as exc:
                result=[]
                error=str(exc)

            def done():
                if not self.winfo_exists():
                    return
                if error:
                    for w in self.loading.winfo_children(): w.destroy()
                    tk.Label(
                        self.loading,text="Threat analysis could not finish:\n"+error,
                        bg=BG,fg=DANGER,font=("Segoe UI",9),justify="left"
                    ).pack(pady=60)
                    return
                self.results=result
                self.loading.destroy()
                self.build_results_ui()
            try:self.after(0,done)
            except Exception:pass

        threading.Thread(target=worker,daemon=True).start()

    def build_results_ui(self):
        controls=tk.Frame(self,bg=BG)
        controls.pack(fill="x",padx=20,pady=(0,8))
        for label in ("All","Critical","High","Moderate"):
            tk.Button(
                controls,text=label,
                command=lambda x=label:self.set_filter(x),
                bg=PANEL_2,fg=TEXT,relief="flat",padx=12,pady=6
            ).pack(side="left",padx=(0,6))
        tk.Entry(
            controls,textvariable=self.search_var,
            bg=PANEL_2,fg=TEXT,insertbackground=TEXT,
            relief="flat"
        ).pack(side="right",fill="x",expand=True,padx=(30,0))
        self.search_var.trace_add("write",lambda *_:self.render_results())

        self.canvas=tk.Canvas(self,bg=BG,highlightthickness=0)
        sb=tk.Scrollbar(self,orient="vertical",command=self.canvas.yview)
        self.body=tk.Frame(self.canvas,bg=BG)
        self.body.bind("<Configure>",lambda e:self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0,0),window=self.body,anchor="nw",tags=("body",))
        self.canvas.bind("<Configure>",lambda e:self.canvas.itemconfigure("body",width=e.width))
        self.canvas.configure(yscrollcommand=sb.set)
        self.canvas.pack(side="left",fill="both",expand=True,padx=(20,0),pady=(0,18))
        sb.pack(side="right",fill="y",padx=(0,12),pady=(0,18))
        self.render_results()

    def set_filter(self,value):
        self.filter_var.set(value)
        self.render_results()

    def render_results(self):
        for w in self.body.winfo_children():
            w.destroy()
        query=self.search_var.get().strip().casefold()
        wanted=self.filter_var.get().upper()
        rows=[
            r for r in self.results
            if (wanted=="ALL" or r["level"]==wanted)
            and (not query or query in r["name"].casefold())
        ]

        if not rows:
            tk.Label(
                self.body,text="No threats match this filter.",
                bg=BG,fg=MUTED,font=("Segoe UI",10)
            ).pack(anchor="w",pady=20)
            return

        for r in rows:
            card=tk.Frame(self.body,bg=PANEL)
            card.pack(fill="x",pady=(0,9))
            head=tk.Frame(card,bg=PANEL)
            head.pack(fill="x",padx=14,pady=(12,6))
            tk.Label(
                head,text=f"#{int(r['dex']):04d}  {r['name']}",
                bg=PANEL,fg=TEXT,font=("Segoe UI",13,"bold")
            ).pack(side="left")
            tk.Label(
                head,text=f"{r['level']}  {r['score']}/100",
                bg=PANEL_2,fg=TEXT,font=("Segoe UI",9,"bold"),
                padx=9,pady=4
            ).pack(side="right")

            meta=" / ".join(r["types"]) or "Unknown type"
            if r["speed"]:
                meta+=f"   •   Base Speed {r['speed']}"
            tk.Label(card,text=meta,bg=PANEL,fg=MUTED,font=("Segoe UI",8)).pack(anchor="w",padx=14)

            if r["reasons"]:
                tk.Label(
                    card,text="Why:  "+"  •  ".join(r["reasons"]),
                    bg=PANEL,fg=TEXT,font=("Segoe UI",8),
                    wraplength=940,justify="left"
                ).pack(anchor="w",padx=14,pady=(7,3))

            answer_text=(
                "Best selected-move answers:  "+", ".join(
                    f"{a['pokemon']} — {a['move']} (×{a['multiplier']:g})"
                    for a in r["answers"]
                )
                if r["answers"] else
                "Best selected-move answers:  None detected"
            )
            tk.Label(
                card,text=answer_text,bg=PANEL,fg=MUTED,
                font=("Segoe UI",8),wraplength=940,justify="left"
            ).pack(anchor="w",padx=14,pady=(2,8))

            buttons=tk.Frame(card,bg=PANEL)
            buttons.pack(fill="x",padx=14,pady=(0,12))
            tk.Button(
                buttons,text="Open Pokédex",
                command=lambda n=r["name"]:self.app.open_pokemon_detail(n),
                bg=PANEL_2,fg=TEXT,relief="flat",padx=10,pady=5
            ).pack(side="left")
            tk.Button(
                buttons,text="Find Spawns",
                command=lambda n=r["name"]:self.open_spawn(n),
                bg=PANEL_2,fg=TEXT,relief="flat",padx=10,pady=5
            ).pack(side="left",padx=(6,0))

    def open_spawn(self,name):
        self.app.show_page("Spawn Finder")
        page=self.app.pages.get("Spawn Finder")
        if page and hasattr(page,"focus_pokemon"):
            page.focus_pokemon(name)


class EmbeddedTeamAdvisorPage(EmbeddedAnalysisBase):
    def __init__(self, master, app, team):
        super().__init__(master, app, team, "Team Advisor")
        self.analysis=None

        top=self.nav_header(
            "Team Advisor",
            "Turns structural and threat analysis into actionable team-building fixes."
        )
        tk.Button(
            top,text="Threat Analyzer",
            command=lambda:self.app.open_threat_analyzer(self.team),
            bg=ACCENT,fg="white",relief="flat",padx=12,pady=7
        ).pack(side="right")

        self.loading=tk.Frame(self,bg=BG)
        self.loading.pack(fill="both",expand=True)
        tk.Label(
            self.loading,text="Analyzing team structure and scoring recommendations…",
            bg=BG,fg=MUTED,font=("Segoe UI",11)
        ).pack(pady=(80,8))
        tk.Label(
            self.loading,text="Analysis is running in the background.",
            bg=BG,fg=MUTED,font=("Segoe UI",8)
        ).pack()
        self.after(30,self.start_analysis)

    def start_analysis(self):
        def worker():
            try:
                result=analyze_team_advice(self.app,self.team)
                error=None
            except Exception as exc:
                result=None
                error=str(exc)

            def done():
                if not self.winfo_exists():
                    return
                if error:
                    for w in self.loading.winfo_children(): w.destroy()
                    tk.Label(
                        self.loading,text="Team Advisor could not finish:\n"+error,
                        bg=BG,fg=DANGER,font=("Segoe UI",9),justify="left"
                    ).pack(pady=60)
                    return
                self.analysis=result
                self.loading.destroy()
                self.build_results_ui()
            try:self.after(0,done)
            except Exception:pass

        threading.Thread(target=worker,daemon=True).start()

    def build_results_ui(self):
        canvas=tk.Canvas(self,bg=BG,highlightthickness=0)
        sb=tk.Scrollbar(self,orient="vertical",command=canvas.yview)
        body=tk.Frame(canvas,bg=BG)
        body.bind("<Configure>",lambda e:canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0,0),window=body,anchor="nw",tags=("body",))
        canvas.bind("<Configure>",lambda e:canvas.itemconfigure("body",width=e.width))
        canvas.configure(yscrollcommand=sb.set)
        canvas.pack(side="left",fill="both",expand=True,padx=(20,0),pady=(0,18))
        sb.pack(side="right",fill="y",padx=(0,12),pady=(0,18))

        self.section(body,"What needs attention",self.problem_widgets)
        self.section(body,"Fix it without replacing a Pokémon",self.move_fix_widgets)
        self.section(body,"Recommended Pokémon",self.candidate_widgets)

    def section(self,parent,title,builder):
        box=tk.Frame(parent,bg=PANEL)
        box.pack(fill="x",pady=(0,12))
        tk.Label(
            box,text=title,bg=PANEL,fg=TEXT,
            font=("Segoe UI",13,"bold")
        ).pack(anchor="w",padx=14,pady=(12,8))
        builder(box)

    def problem_widgets(self,box):
        rows=self.analysis["problems"]
        if not rows:
            tk.Label(
                box,text="No major structural problems detected from the current data.",
                bg=PANEL,fg=MUTED,font=("Segoe UI",9)
            ).pack(anchor="w",padx=14,pady=(0,14))
            return
        for p in rows[:10]:
            row=tk.Frame(box,bg=PANEL_2)
            row.pack(fill="x",padx=14,pady=(0,7))
            tk.Label(
                row,text=f"{p['severity']}  •  {p['title']}",
                bg=PANEL_2,fg=TEXT,font=("Segoe UI",9,"bold")
            ).pack(anchor="w",padx=10,pady=(8,2))
            tk.Label(
                row,text=p["detail"],bg=PANEL_2,fg=MUTED,
                font=("Segoe UI",8),wraplength=940,justify="left"
            ).pack(anchor="w",padx=10,pady=(0,8))

    def move_fix_widgets(self,box):
        fixes=self.analysis["move_fixes"]
        if not fixes:
            tk.Label(
                box,text="No obvious one-move utility fixes were found from the imported learnsets.",
                bg=PANEL,fg=MUTED,font=("Segoe UI",9)
            ).pack(anchor="w",padx=14,pady=(0,14))
            return
        for f in fixes:
            row=tk.Frame(box,bg=PANEL_2)
            row.pack(fill="x",padx=14,pady=(0,7))
            tk.Label(
                row,text=f"{f['pokemon']}  →  {f['move']}",
                bg=PANEL_2,fg=TEXT,font=("Segoe UI",9,"bold")
            ).pack(anchor="w",padx=10,pady=(8,2))
            tk.Label(
                row,text=f["reason"],bg=PANEL_2,fg=MUTED,
                font=("Segoe UI",8)
            ).pack(anchor="w",padx=10,pady=(0,8))

    def candidate_widgets(self,box):
        rows=self.analysis["candidates"]
        if not rows:
            tk.Label(
                box,text="No replacement recommendations could be scored from the current imported Pokédex.",
                bg=PANEL,fg=MUTED,font=("Segoe UI",9)
            ).pack(anchor="w",padx=14,pady=(0,14))
            return
        for rank,c in enumerate(rows[:12],1):
            row=tk.Frame(box,bg=PANEL_2)
            row.pack(fill="x",padx=14,pady=(0,8))
            head=tk.Frame(row,bg=PANEL_2)
            head.pack(fill="x",padx=10,pady=(8,2))
            tk.Label(
                head,text=f"#{rank}  {c['name']}",
                bg=PANEL_2,fg=TEXT,font=("Segoe UI",10,"bold")
            ).pack(side="left")
            tk.Label(
                head,text=f"Fit score {c['score']}",
                bg=PANEL,fg=TEXT,font=("Segoe UI",8,"bold"),
                padx=7,pady=3
            ).pack(side="right")
            reason="  •  ".join(c["reasons"]) if c["reasons"] else "Improves the team's structural matchup profile."
            tk.Label(
                row,text=reason,bg=PANEL_2,fg=MUTED,
                font=("Segoe UI",8),wraplength=900,justify="left"
            ).pack(anchor="w",padx=10,pady=(2,6))
            buttons=tk.Frame(row,bg=PANEL_2)
            buttons.pack(fill="x",padx=10,pady=(0,8))
            tk.Button(
                buttons,text="Open Pokédex",
                command=lambda n=c["name"]:self.app.open_pokemon_detail(n),
                bg=PANEL,fg=TEXT,relief="flat",padx=9,pady=4
            ).pack(side="left")
            tk.Button(
                buttons,text="Find Spawns",
                command=lambda n=c["name"]:self.open_spawn(n),
                bg=PANEL,fg=TEXT,relief="flat",padx=9,pady=4
            ).pack(side="left",padx=(6,0))

    def open_spawn(self,name):
        self.app.show_page("Spawn Finder")
        page=self.app.pages.get("Spawn Finder")
        if page and hasattr(page,"focus_pokemon"):
            page.focus_pokemon(name)


class CompetitiveAnalysisWindow(tk.Toplevel):
    def __init__(self, app, team):
        super().__init__(app)
        self.app=app; self.team=team
        self.title(f"Competitive Analysis — {team.get('name','Team')}")
        self.configure(bg=BG); self.geometry("920x760"); self.minsize(820,650); self.transient(app)

        top=tk.Frame(self,bg=BG); top.pack(fill="x",padx=20,pady=(18,8))
        tk.Label(top,text=f"Competitive Analysis — {team.get('name','Team')}",bg=BG,fg=TEXT,font=("Segoe UI Semibold",19)).pack(side="left")
        self.refresh_button=tk.Button(
            top,text="Refresh Move Data",command=self.refresh_online,
            bg=ACCENT_2,fg="white",relief="flat",padx=12,pady=7
        )
        self.refresh_button.pack(side="right")
        tk.Button(
            top,text="Threat Analyzer",
            command=lambda:ThreatAnalyzerWindow(self,self.app,self.team),
            bg=ACCENT,fg="white",relief="flat",padx=12,pady=7
        ).pack(side="right",padx=(0,8))
        tk.Button(
            top,text="Team Advisor",
            command=lambda:TeamAdvisorWindow(self,self.app,self.team),
            bg=ACCENT,fg="white",relief="flat",padx=12,pady=7
        ).pack(side="right",padx=(0,8))

        self.canvas=tk.Canvas(self,bg=BG,highlightthickness=0)
        scroll=tk.Scrollbar(self,orient="vertical",command=self.canvas.yview)
        self.body=tk.Frame(self.canvas,bg=BG)
        win=self.canvas.create_window((0,0),window=self.body,anchor="nw")
        self.body.bind("<Configure>",lambda e:self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>",lambda e:self.canvas.itemconfigure(win,width=e.width))
        self.canvas.configure(yscrollcommand=scroll.set)
        self.canvas.pack(side="left",fill="both",expand=True,padx=(20,0),pady=(0,20)); scroll.pack(side="right",fill="y",padx=(0,20),pady=(0,20))
        self.render()

    def refresh_online(self):
        moves={
            str(x).strip()
            for m in self.team["members"]
            for x in m.get("moves",[])
            if str(x).strip()
        }
        if not moves:
            return

        try:
            self.refresh_button.config(text="Refreshing…", state="disabled")
        except Exception:
            pass

        def worker():
            resolved = 0
            for move in moves:
                if get_move_metadata(move,allow_network=True):
                    resolved += 1

            def done():
                try:
                    self.render()
                    unresolved = [
                        move for move in moves
                        if not get_move_metadata(move,allow_network=False)
                    ]
                    if unresolved:
                        self.refresh_button.config(
                            text=f"Refresh Move Data ({len(unresolved)} unresolved)",
                            state="normal"
                        )
                    else:
                        self.refresh_button.config(
                            text="Move Data Up to Date ✓",
                            state="normal"
                        )
                except Exception:
                    pass

            try:
                self.after(0, done)
            except Exception:
                pass

        threading.Thread(target=worker,daemon=True).start()

    def section(self,title):
        box=tk.Frame(self.body,bg=PANEL); box.pack(fill="x",pady=5)
        tk.Label(box,text=title,bg=PANEL,fg=TEXT,font=("Segoe UI Semibold",13)).pack(anchor="w",padx=14,pady=(10,6))
        return box

    def render(self):
        for w in self.body.winfo_children():w.destroy()
        meta=selected_move_metadata(self.team["members"],allow_network=False)
        a=analyze_team(self.team["members"],self.app.pokedex,meta)

        box=self.section("Team Health")
        if not a["issues"]:
            tk.Label(box,text="✓ No major issues detected from the current analysis rules.",bg=PANEL,fg=GOOD,font=("Segoe UI",10)).pack(anchor="w",padx=14,pady=(0,10))
        else:
            for x in a["issues"]:
                tk.Label(box,text="⚠  "+x,bg=PANEL,fg=TEXT,font=("Segoe UI",9),anchor="w",justify="left").pack(fill="x",padx=14,pady=2)
        for x in a["strengths"]:
            tk.Label(box,text="✓  "+x,bg=PANEL,fg=GOOD,font=("Segoe UI",9),anchor="w",justify="left").pack(fill="x",padx=14,pady=2)
        tk.Frame(box,bg=PANEL,height=8).pack()

        box=self.section("Roles & Stat Profile")
        for name,role in a["roles"]:
            tk.Label(box,text=f"{name}: {role}",bg=PANEL,fg=TEXT,font=("Segoe UI",9)).pack(anchor="w",padx=14,pady=1)
        if a["stats"]:
            st="   •   ".join(f"{k} avg {v['avg']}" for k,v in a["stats"].items())
            tk.Label(box,text=st,bg=PANEL,fg=MUTED,font=("Segoe UI",8),wraplength=820,justify="left").pack(anchor="w",padx=14,pady=(6,10))

        box=self.section("Offensive Coverage")
        tk.Label(box,text=f"Selected attacks: {a['physical']} physical • {a['special']} special • {a['status']} status",
                 bg=PANEL,fg=MUTED,font=("Segoe UI",9)).pack(anchor="w",padx=14,pady=(0,6))
        grid=tk.Frame(box,bg=PANEL); grid.pack(fill="x",padx=10,pady=(0,10))
        for c in range(6):grid.grid_columnconfigure(c,weight=1,uniform="off")
        for i,tp in enumerate(TYPE_EFFECTIVENESS):
            c=a["offense"][tp]; b=tk.Frame(grid,bg=PANEL_2); b.grid(row=i//6,column=i%6,sticky="nsew",padx=2,pady=2)
            tk.Label(b,text=tp,bg=PANEL_2,fg=TEXT,font=("Segoe UI Semibold",8)).pack(pady=(5,0))
            tk.Label(b,text=f"{c} SE option{'s' if c!=1 else ''}",bg=PANEL_2,fg=MUTED,font=("Segoe UI",7)).pack(pady=(0,5))

        box=self.section("Team Utility")
        for group,hits in a["utility"].items():
            tk.Label(box,text=f"{group}: {', '.join(hits) if hits else 'None'}",bg=PANEL,fg=TEXT if hits else MUTED,font=("Segoe UI",9),
                     anchor="w",justify="left").pack(fill="x",padx=14,pady=2)
        tk.Frame(box,bg=PANEL,height=8).pack()

        missing=[m for m in {str(x).strip() for member in self.team["members"] for x in member.get("moves",[]) if str(x).strip()} if not meta.get(m.lower())]
        if missing:
            box=self.section("Move Metadata")
            tk.Label(box,text="Some selected moves have not been analyzed yet: "+", ".join(sorted(missing)),
                     bg=PANEL,fg=MUTED,font=("Segoe UI",9),wraplength=820,justify="left").pack(anchor="w",padx=14,pady=(0,4))
            tk.Label(box,text="Use “Refresh Move Data” above. Compact Cobblemon move IDs are automatically resolved to canonical move names and cached locally.",bg=PANEL,fg=MUTED,font=("Segoe UI",8),wraplength=820,justify="left").pack(anchor="w",padx=14,pady=(0,10))

class TeamMemberEditor(tk.Toplevel):
    def __init__(self,app,page,idx):
        super().__init__(app)
        self.app=app; self.page=page; self.idx=idx
        self.team=page.current_team()
        self.member=normalize_team_member(self.team["members"][idx])

        self.title(f"Edit Team Slot {idx+1}")
        self.configure(bg=BG)

        # Tall enough at launch to expose Save / Cancel on a standard 1080p desktop.
        self.geometry("720x860")
        self.minsize(680,800)
        self.transient(app)
        self.grab_set()

        tk.Label(
            self,text=f"Team Slot {idx+1}",
            bg=BG,fg=TEXT,
            font=("Segoe UI Semibold",18)
        ).pack(anchor="w",padx=20,pady=(18,4))

        tk.Label(
            self,
            text="Build data is saved with this team. Ability, item, and move choices come from Companion's imported data.",
            bg=BG,fg=MUTED,font=("Segoe UI",9),
            wraplength=650,justify="left"
        ).pack(anchor="w",padx=20,pady=(0,12))

        # Scrollable body protects smaller displays, while buttons stay pinned below.
        outer=tk.Frame(self,bg=BG)
        outer.pack(fill="both",expand=True,padx=20)

        self.canvas=tk.Canvas(outer,bg=BG,highlightthickness=0)
        scroll=tk.Scrollbar(outer,orient="vertical",command=self.canvas.yview)
        body=tk.Frame(self.canvas,bg=BG)
        win=self.canvas.create_window((0,0),window=body,anchor="nw")
        body.bind("<Configure>",lambda e:self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>",lambda e:self.canvas.itemconfigure(win,width=e.width))
        self.canvas.configure(yscrollcommand=scroll.set)
        self.canvas.pack(side="left",fill="both",expand=True)
        scroll.pack(side="right",fill="y")

        self.pokemon=tk.StringVar(value=self.member["pokemon"])
        self.ability=tk.StringVar(value=self.member["ability"])
        self.nature=tk.StringVar(value=self.member["nature"])
        self.item=tk.StringVar(value=self.member["item"])
        self.moves=[tk.StringVar(value=x) for x in self.member["moves"]]
        self.evs={s:tk.StringVar(value=str(self.member["evs"][s])) for s in TEAM_STATS}

        self.label(body,"Pokémon")
        row=tk.Frame(body,bg=BG); row.pack(fill="x",pady=(0,8))
        tk.Entry(
            row,textvariable=self.pokemon,state="readonly",
            readonlybackground=PANEL,fg=TEXT,relief="flat"
        ).pack(side="left",fill="x",expand=True,ipady=8)
        tk.Button(
            row,text="Choose",command=self.choose,
            bg=ACCENT_2,fg="white",relief="flat",
            padx=12,pady=8
        ).pack(side="left",padx=(8,0))

        self.label(body,"Ability")
        self.ability_holder=tk.Frame(body,bg=BG)
        self.ability_holder.pack(fill="x",pady=(0,8))

        self.label(body,"Nature")
        nm=tk.OptionMenu(body,self.nature,"",*TEAM_NATURES)
        nm.config(bg=PANEL,fg=TEXT,relief="flat",highlightthickness=0)
        nm["menu"].config(bg=PANEL_2,fg=TEXT)
        nm.pack(fill="x",pady=(0,8))
        self.nature.trace_add("write",lambda *_:self.update_live_preview())

        self.label(body,"Held Item")
        item_row=tk.Frame(body,bg=BG)
        item_row.pack(fill="x",pady=(0,6))
        tk.Entry(
            item_row,textvariable=self.item,
            state="readonly",
            readonlybackground=PANEL,
            fg=TEXT,relief="flat"
        ).pack(side="left",fill="x",expand=True,ipady=8)
        tk.Button(
            item_row,text="Choose",
            command=self.choose_item,
            bg=PANEL_2,fg=TEXT,
            activebackground=ACCENT_2,activeforeground="white",
            relief="flat",padx=12,pady=8
        ).pack(side="left",padx=(8,0))

        self.item_effect=tk.Label(
            body,text="",bg=BG,fg=MUTED,
            font=("Segoe UI",8),
            wraplength=640,justify="left"
        )
        self.item_effect.pack(anchor="w",pady=(0,8))

        self.label(body,"Moves")
        self.move_holder=tk.Frame(body,bg=BG)
        self.move_holder.pack(fill="x",pady=(0,8))

        self.label(body,"EVs")
        evf=tk.Frame(body,bg=PANEL)
        evf.pack(fill="x")
        for i,s in enumerate(TEAM_STATS):
            c=tk.Frame(evf,bg=PANEL)
            c.grid(row=0,column=i,padx=5,pady=8)
            tk.Label(c,text=s,bg=PANEL,fg=MUTED).pack()
            tk.Entry(
                c,textvariable=self.evs[s],width=5,
                bg=PANEL_2,fg=TEXT,insertbackground=TEXT,
                relief="flat",justify="center"
            ).pack(ipady=4)
            self.evs[s].trace_add("write",lambda *_:self.on_build_change())

        self.ev_status=tk.Label(body,text="",bg=BG,fg=MUTED,font=("Segoe UI",9))
        self.ev_status.pack(anchor="w",pady=(5,6))

        self.label(body,"Live Item / Stat Preview")
        self.preview_box=tk.Frame(body,bg=PANEL)
        self.preview_box.pack(fill="x",pady=(0,12))

        buttons=tk.Frame(self,bg=BG)
        buttons.pack(fill="x",padx=20,pady=18)

        tk.Button(
            buttons,text="Clear Slot",command=self.clear,
            bg=PANEL_2,fg=TEXT,relief="flat",
            padx=12,pady=8
        ).pack(side="left")

        tk.Button(
            buttons,text="Cancel",command=self.destroy,
            bg=PANEL_2,fg=TEXT,relief="flat",
            padx=12,pady=8
        ).pack(side="right")

        tk.Button(
            buttons,text="Save Build",command=self.save,
            bg=ACCENT_2,fg="white",relief="flat",
            padx=14,pady=8
        ).pack(side="right",padx=(0,8))

        self.rebuild()
        self.ev_status_update()
        self.update_live_preview()

    def label(self,m,t):
        tk.Label(
            m,text=t,bg=BG,fg=MUTED,
            font=("Segoe UI Semibold",9)
        ).pack(anchor="w",pady=(2,4))

    def choose(self):
        PokemonPicker(
            self.app,self.app.pokedex,
            "Choose Team Pokémon",
            self.pokemon.get(),
            self.set_pokemon
        )

    def set_pokemon(self,p):
        self.pokemon.set(p)
        self.ability.set("")
        for v in self.moves:
            v.set("")
        self.rebuild()
        self.update_live_preview()

    def choose_item(self):
        HeldItemPicker(
            self.app,
            self.item.get(),
            self.set_item
        )

    def set_item(self,item):
        self.item.set(item)
        self.update_live_preview()

    def rebuild(self):
        for w in self.ability_holder.winfo_children():
            w.destroy()
        for w in self.move_holder.winfo_children():
            w.destroy()

        s=species_by_name(self.app.pokedex,self.pokemon.get())
        av=[""]+species_ability_options(s)
        am=tk.OptionMenu(self.ability_holder,self.ability,*av)
        am.config(bg=PANEL,fg=TEXT,relief="flat",highlightthickness=0)
        am["menu"].config(bg=PANEL_2,fg=TEXT)
        am.pack(fill="x")

        self.available_moves = species_move_options(s)
        for i,v in enumerate(self.moves):
            r=tk.Frame(self.move_holder,bg=BG)
            r.pack(fill="x",pady=3)

            tk.Label(
                r,text=str(i+1),width=3,
                bg=BG,fg=MUTED,font=("Segoe UI",9)
            ).pack(side="left")

            entry=tk.Entry(
                r,textvariable=v,state="readonly",
                readonlybackground=PANEL,fg=TEXT,
                relief="flat",font=("Segoe UI",10)
            )
            entry.pack(side="left",fill="x",expand=True,ipady=7)

            tk.Button(
                r,text="Choose",
                command=lambda idx=i:self.choose_move(idx),
                bg=PANEL_2,fg=TEXT,
                activebackground=ACCENT_2,activeforeground="white",
                relief="flat",padx=12,pady=7
            ).pack(side="left",padx=(8,0))

    def choose_move(self,index):
        if not getattr(self,"available_moves",None):
            messagebox.showinfo(
                APP_NAME,
                "No moves are available for this Pokémon in the imported Cobblemon learnset."
            )
            return

        MovePicker(
            self.app,
            self.available_moves,
            self.moves[index].get(),
            lambda move,idx=index:self.set_move(idx,move)
        )

    def set_move(self,index,move):
        self.moves[index].set(move)
        if move and not get_move_metadata(move,allow_network=False):
            threading.Thread(
                target=lambda:get_move_metadata(move,allow_network=True),
                daemon=True
            ).start()
        self.update_live_preview()

    def parsed_evs(self):
        o={}
        for s in TEAM_STATS:
            try:
                o[s]=max(0,min(252,int(self.evs[s].get() or 0)))
            except:
                o[s]=0
        return o

    def on_build_change(self):
        self.ev_status_update()
        self.update_live_preview()

    def ev_status_update(self):
        total=sum(self.parsed_evs().values())
        self.ev_status.config(
            text=f"EV total: {total} / 510 • 252 max per stat",
            fg=GOOD if total<=510 else DANGER
        )

    def preview_member(self):
        return {
            "pokemon":self.pokemon.get().strip(),
            "ability":self.ability.get().strip(),
            "nature":self.nature.get().strip(),
            "item":self.item.get().strip(),
            "moves":[v.get().strip() for v in self.moves],
            "evs":self.parsed_evs(),
        }

    def update_live_preview(self):
        for w in self.preview_box.winfo_children():
            w.destroy()

        member=self.preview_member()
        species=species_by_name(self.app.pokedex,member["pokemon"])
        if not species:
            tk.Label(
                self.preview_box,
                text="Choose a Pokémon to preview item effects.",
                bg=PANEL,fg=MUTED,font=("Segoe UI",8)
            ).pack(anchor="w",padx=10,pady=9)
            return

        effect=held_item_effect(member["item"])
        note=effect.get("note","")
        self.item_effect.config(
            text=note if note else (
                "No competitive stat modifier is currently mapped for this held item."
                if member["item"] else
                "Choose a held item to preview its known competitive effect."
            )
        )

        preview=held_item_stat_preview(species,member)
        row=tk.Frame(self.preview_box,bg=PANEL)
        row.pack(fill="x",padx=8,pady=8)

        for i,stat in enumerate(("HP","Atk","Def","SpA","SpD","Spe")):
            info=preview[stat]
            box=tk.Frame(row,bg=PANEL_2)
            box.grid(row=0,column=i,sticky="nsew",padx=2)
            row.grid_columnconfigure(i,weight=1,uniform="preview")
            tk.Label(
                box,text=stat,bg=PANEL_2,fg=MUTED,
                font=("Segoe UI",7,"bold")
            ).pack(pady=(5,1))

            if info["multiplier"] != 1:
                value=f"{info['base']} → {info['effective']:g}"
                fg=GOOD
            else:
                value=str(info["base"])
                fg=TEXT

            tk.Label(
                box,text=value,bg=PANEL_2,fg=fg,
                font=("Segoe UI Semibold",8)
            ).pack(pady=(0,5))

        if member["item"]:
            tk.Label(
                self.preview_box,
                text=note or f"{member['item']} selected. No direct stat multiplier is mapped.",
                bg=PANEL,fg=MUTED,font=("Segoe UI",8),
                wraplength=630,justify="left"
            ).pack(anchor="w",padx=10,pady=(0,8))

    def save(self):
        evs=self.parsed_evs()
        if sum(evs.values())>510:
            messagebox.showerror(APP_NAME,"EV total cannot exceed 510.")
            return

        self.team["members"][self.idx]=self.preview_member()
        self.app.save()
        self.page.refresh()
        self.destroy()

    def clear(self):
        self.team["members"][self.idx]=blank_team_member()
        self.app.save()
        self.page.refresh()
        self.destroy()


class TeamBuilderPage(Page):
    title="Teams"; subtitle="Build and save six-Pokémon teams with Cobblemon moves, abilities, EVs, natures, items, and type analysis."
    def __init__(self,master,app):
        super().__init__(master,app); self.team_index=0; self.sprite_refs={}; self._sprite_download_running=False; self.header()
        top=tk.Frame(self,bg=BG); top.pack(fill="x",padx=28,pady=(0,10)); self.menu_holder=tk.Frame(top,bg=BG); self.menu_holder.pack(side="left")
        tk.Button(top,text="New Team",command=self.new_team,bg=ACCENT_2,fg="white",relief="flat",padx=12,pady=8).pack(side="left",padx=6)
        tk.Button(top,text="Rename",command=self.rename_team,bg=PANEL_2,fg=TEXT,relief="flat",padx=12,pady=8).pack(side="left",padx=3)
        tk.Button(top,text="Delete",command=self.delete_team,bg=PANEL_2,fg=TEXT,relief="flat",padx=12,pady=8).pack(side="left",padx=3)
        tk.Button(top,text="Full Analysis",command=self.open_analysis,bg=GOOD,fg="white",relief="flat",padx=12,pady=8).pack(side="left",padx=(10,3))
        self.status=tk.Label(top,text="",bg=BG,fg=MUTED); self.status.pack(side="right")
        mf=tk.Frame(self,bg=BG); mf.pack(fill="x",padx=28,pady=(0,8)); self.cards=[]
        for c in range(3):mf.grid_columnconfigure(c,weight=1,uniform="team")
        for i in range(6):
            card=tk.Frame(mf,bg=PANEL); card.grid(row=i//3,column=i%3,sticky="nsew",padx=4,pady=4)
            main=tk.Button(card,text="",bg=PANEL,fg=TEXT,compound="left",relief="flat",anchor="w",justify="left",command=lambda x=i:self.edit(x)); main.pack(fill="both",expand=True,padx=4,pady=4)
            foot=tk.Frame(card,bg=PANEL); foot.pack(fill="x")
            tk.Button(foot,text="Edit Build",command=lambda x=i:self.edit(x),bg=PANEL_2,fg=TEXT,relief="flat",pady=5).pack(side="left",fill="x",expand=True)
            sp=tk.Button(foot,text="Find Spawns",command=lambda x=i:self.spawn(x),bg=PANEL_2,fg=MUTED,relief="flat",pady=5); sp.pack(side="left",fill="x",expand=True)
            self.cards.append((main,sp))
        an=tk.Frame(self,bg=PANEL); an.pack(fill="both",expand=True,padx=28,pady=(0,28))
        header=tk.Frame(an,bg=PANEL); header.pack(fill="x",padx=14,pady=(10,2))
        tk.Label(header,text="Quick Team Analysis",bg=PANEL,fg=TEXT,font=("Segoe UI Semibold",13)).pack(side="left")
        tk.Label(header,text="Use Full Analysis for detailed offensive coverage, utility, roles, STAB and warnings.",bg=PANEL,fg=MUTED,font=("Segoe UI",8)).pack(side="right")
        self.quick_issues=tk.Label(an,text="",bg=PANEL,fg=MUTED,font=("Segoe UI",8),wraplength=900,justify="left")
        self.quick_issues.pack(anchor="w",padx=14,pady=(2,5))
        self.analysis=tk.Frame(an,bg=PANEL); self.analysis.pack(fill="both",expand=True,padx=10,pady=8)
        self.ensure_team(); self.refresh_menu(); self.refresh()
    def ensure_team(self):
        teams=self.app.profile.setdefault("teams",[])
        if not teams:teams.append(blank_team("Team 1"))
        for t in teams:
            members=t.get("members",[]) if isinstance(t.get("members",[]),list) else []
            t["members"]=[normalize_team_member(x) for x in members[:6]]
            while len(t["members"])<6:t["members"].append(blank_team_member())
        self.team_index=max(0,min(self.team_index,len(teams)-1))
    def current_team(self):self.ensure_team(); return self.app.profile["teams"][self.team_index]
    def refresh_menu(self):
        for w in self.menu_holder.winfo_children():w.destroy()
        names=[t.get("name",f"Team {i+1}") for i,t in enumerate(self.app.profile["teams"])]
        v=tk.StringVar(value=names[self.team_index]); m=tk.OptionMenu(self.menu_holder,v,*names,command=self.select); m.config(bg=PANEL,fg=TEXT,relief="flat",highlightthickness=0); m["menu"].config(bg=PANEL_2,fg=TEXT); m.pack()
    def select(self,name):
        for i,t in enumerate(self.app.profile["teams"]):
            if t.get("name")==name:self.team_index=i;break
        self.refresh()
    def new_team(self):
        ts=self.app.profile["teams"]; ts.append(blank_team(f"Team {len(ts)+1}")); self.team_index=len(ts)-1; self.app.save(); self.refresh_menu(); self.refresh()
    def rename_team(self): PopupEntry(self.app,"Rename Team","Team name:",self.current_team().get("name",""),self.apply_rename)
    def apply_rename(self,v):
        if str(v).strip():self.current_team()["name"]=str(v).strip(); self.app.save(); self.refresh_menu(); self.refresh()
    def delete_team(self):
        ts=self.app.profile["teams"]
        if len(ts)<=1:messagebox.showinfo(APP_NAME,"Keep at least one team.");return
        if messagebox.askyesno(APP_NAME,"Delete this team?"):ts.pop(self.team_index);self.team_index=max(0,self.team_index-1);self.app.save();self.refresh_menu();self.refresh()
    def edit(self,i):TeamMemberEditor(self.app,self,i)
    def open_analysis(self): self.app.open_competitive_analysis(self.current_team())
    def spawn(self,i):
        p=self.current_team()["members"][i].get("pokemon","")
        if p:self.app.show_page("Spawn Finder"); self.app.pages["Spawn Finder"].focus_pokemon(p)
    def refresh(self):
        self.ensure_team(); t=self.current_team(); self.sprite_refs={}; dexes=[]; count=0
        for i,m in enumerate(t["members"]):
            m=normalize_team_member(m); t["members"][i]=m; p=m["pokemon"]; s=species_by_name(self.app.pokedex,p) if p else None; img=None
            if s:
                count+=1; dexes.append(s.get("dex")); path=cached_sprite_path(s.get("dex"))
                if path:
                    try:img=tk.PhotoImage(file=str(path)); img=img.subsample(2,2) if img.width()>=80 else img; self.sprite_refs[i]=img
                    except:img=None
            details=[p,(" / ".join(s.get("types",[])) if s else ""),f"{m['nature'] or 'No nature'} • {m['ability'] or 'No ability'}",m["item"] or "No held item",", ".join(x for x in m["moves"] if x) or "No moves selected"] if p else [f"Slot {i+1}","Click to choose a Pokémon"]
            self.cards[i][0].config(text="\n".join(x for x in details if x),image=img if img else "")
            self.cards[i][1].config(state="normal" if p else "disabled")
        self.status.config(text=f"{count} / 6 Pokémon"); self.render_analysis(t["members"]); self.prefetch(dexes)
    def prefetch(self,dexes):
        if self._sprite_download_running:return
        miss=[d for d in dexes if d and not cached_sprite_path(d)]
        if not miss:return
        self._sprite_download_running=True
        def worker():
            for d in set(miss):
                try:get_cached_sprite(d)
                except:pass
            def done():self._sprite_download_running=False; self.refresh()
            try:self.after(0,done)
            except:pass
        threading.Thread(target=worker,daemon=True).start()
    def render_analysis(self,members):
        for w in self.analysis.winfo_children():w.destroy()
        move_meta=selected_move_metadata(members,allow_network=False)
        full=analyze_team(members,self.app.pokedex,move_meta)
        quick=full["issues"][:4]
        self.quick_issues.config(text=("⚠  "+"   •   ".join(quick)) if quick else "✓ No major quick-analysis warnings.")
        sm=team_defensive_summary(members,self.app.pokedex)
        for c in range(6):self.analysis.grid_columnconfigure(c,weight=1,uniform="types")
        for i,tp in enumerate(TYPE_EFFECTIVENESS):
            d=sm[tp]; b=tk.Frame(self.analysis,bg=PANEL_2); b.grid(row=i//6,column=i%6,sticky="nsew",padx=3,pady=3)
            tk.Label(b,text=tp,bg=PANEL_2,fg=TEXT,font=("Segoe UI Semibold",9)).pack(pady=(5,1))
            tk.Label(b,text=f"Weak {d['weak']} • Resist {d['resist']} • Immune {d['immune']}",bg=PANEL_2,fg=MUTED,font=("Segoe UI",7)).pack(pady=(0,5))

class CollectionPage(Page):
    title = "Collection 2.0"
    subtitle = "A visual Living Dex and completion center for every Pokémon implemented in your Cobblemon version."

    PAGE_SIZE = 24

    def __init__(self, master, app):
        super().__init__(master, app)
        self.page_index=0
        self.filtered=[]
        self.sprite_refs={}
        self._sprite_download_running=False
        self.header()

        self.progress_box=tk.Frame(self,bg=PANEL)
        self.progress_box.pack(fill="x",padx=28,pady=(0,10))
        self.progress_title=tk.Label(self.progress_box,text="",bg=PANEL,fg=TEXT,font=("Segoe UI Semibold",18))
        self.progress_title.pack(anchor="w",padx=16,pady=(13,2))
        self.progress_detail=tk.Label(self.progress_box,text="",bg=PANEL,fg=MUTED,font=("Segoe UI",9))
        self.progress_detail.pack(anchor="w",padx=16,pady=(0,7))
        self.progress=tk.Canvas(self.progress_box,height=12,bg=PANEL_2,highlightthickness=0)
        self.progress.pack(fill="x",padx=16,pady=(0,13))

        controls=tk.Frame(self,bg=BG); controls.pack(fill="x",padx=28,pady=(0,8))
        self.query=tk.StringVar()
        self.status_var=tk.StringVar(value="All")
        self.type_var=tk.StringVar(value="All types")
        self.gen_var=tk.StringVar(value="All generations")
        search=tk.Entry(controls,textvariable=self.query,bg=PANEL,fg=TEXT,insertbackground=TEXT,relief="flat",font=("Segoe UI",11))
        search.grid(row=0,column=0,sticky="ew",ipady=9)
        for col,(var,values) in enumerate([
            (self.status_var,["All","Owned","Missing"]),
            (self.type_var,["All types"]+list(TYPE_COLORS.keys())),
            (self.gen_var,["All generations"]+[f"Generation {i}" for i in range(1,10)])
        ],1):
            menu=tk.OptionMenu(controls,var,*values)
            menu.config(bg=PANEL_2,fg=TEXT,activebackground=PANEL_2,activeforeground=TEXT,relief="flat",highlightthickness=0,font=("Segoe UI",9))
            menu["menu"].config(bg=PANEL_2,fg=TEXT)
            menu.grid(row=0,column=col,sticky="ew",padx=(8 if col==1 else 0,8 if col<3 else 0))
        controls.grid_columnconfigure(0,weight=4)
        for c in range(1,4):controls.grid_columnconfigure(c,weight=1)

        # Regional / generation completion strip.
        self.gen_strip=tk.Frame(self,bg=BG)
        self.gen_strip.pack(fill="x",padx=28,pady=(0,8))

        self.summary=tk.Label(self,text="",bg=BG,fg=MUTED,font=("Segoe UI",9))
        self.summary.pack(anchor="w",padx=29,pady=(0,6))

        # Keep page navigation ABOVE the collection grid so it remains visible
        # even at the app's default window height.
        pager=tk.Frame(self,bg=BG)
        pager.pack(fill="x",padx=28,pady=(0,6))
        self.prev_btn=tk.Button(
            pager,text="← Previous",command=self.prev_page,
            bg=PANEL_2,fg=TEXT,relief="flat",padx=14,pady=7
        )
        self.prev_btn.pack(side="left")

        self.page_label=tk.Label(
            pager,text="",bg=BG,fg=TEXT,
            font=("Segoe UI Semibold",10)
        )
        self.page_label.pack(side="left",expand=True)

        self.next_btn=tk.Button(
            pager,text="Next →",command=self.next_page,
            bg=ACCENT_2,fg="white",relief="flat",padx=14,pady=7
        )
        self.next_btn.pack(side="right")

        self.grid_frame=tk.Frame(self,bg=BG)
        self.grid_frame.pack(fill="both",expand=True,padx=28,pady=(0,10))
        for col in range(6):
            self.grid_frame.grid_columnconfigure(col,weight=1,uniform="collection")
        for row in range(4):
            self.grid_frame.grid_rowconfigure(
                row,
                weight=1,
                uniform="collection",
                minsize=132
            )

        self.cards=[]
        for i in range(self.PAGE_SIZE):
            outer=tk.Frame(self.grid_frame,bg=PANEL,height=132)
            outer.grid(row=i//6,column=i%6,sticky="nsew",padx=4,pady=4)
            outer.grid_propagate(False)

            # Dedicated clickable main area keeps sprite/text separate from footer.
            main=tk.Frame(outer,bg=PANEL,cursor="hand2")
            main.pack(fill="both",expand=True)

            sprite_label=tk.Label(
                main,text="",bg=PANEL,fg=TEXT,
                font=("Segoe UI",8),cursor="hand2"
            )
            sprite_label.pack(pady=(6,1))

            info_label=tk.Label(
                main,text="",bg=PANEL,fg=TEXT,
                font=("Segoe UI Semibold",8),
                justify="center",
                wraplength=135,
                cursor="hand2"
            )
            info_label.pack(fill="x",padx=4,pady=(0,4))

            footer=tk.Frame(outer,bg=PANEL)
            footer.pack(fill="x",side="bottom")

            detail=tk.Button(
                footer,text="Pokédex",
                bg=PANEL_2,fg=MUTED,
                relief="flat",bd=0,font=("Segoe UI",7),pady=2
            )
            detail.pack(side="left",fill="x",expand=True,padx=(0,1))

            hunt=tk.Button(
                footer,text="Hunt",
                bg=PANEL_2,fg=MUTED,
                relief="flat",bd=0,font=("Segoe UI",7),pady=2
            )
            hunt.pack(side="left",fill="x",expand=True,padx=1)

            spawn=tk.Button(
                footer,text="Spawns",
                bg=PANEL_2,fg=MUTED,
                relief="flat",bd=0,font=("Segoe UI",7),pady=2
            )
            spawn.pack(side="left",fill="x",expand=True,padx=(1,0))

            self.cards.append({
                "outer":outer,
                "main":main,
                "sprite":sprite_label,
                "info":info_label,
                "detail":detail,
                "hunt":hunt,
                "spawn":spawn
            })

        for var in (self.query,self.status_var,self.type_var,self.gen_var):
            var.trace_add("write",lambda *_:self.filters_changed())
        self.rebuild_filter(); self.render_page(prefetch=False)

    def owned_set(self):
        return {str(x).strip().casefold() for x in self.app.profile.get("living_dex",[]) if str(x).strip()}

    def generation_stats(self):
        owned=self.owned_set()
        result={}
        for gen in range(1,10):
            mons=[p for p in self.app.pokedex if generation_for_dex(p.get("dex",0))==gen]
            have=sum(1 for p in mons if p.get("name","").strip().casefold() in owned)
            result[gen]=(have,len(mons))
        return result

    def filters_changed(self):
        self.page_index=0; self.rebuild_filter(); self.render_page(prefetch=True)

    def refresh(self):
        self.rebuild_filter()
        self.page_index=min(self.page_index,max(0,(len(self.filtered)-1)//self.PAGE_SIZE))
        self.render_page(prefetch=True)

    def rebuild_filter(self):
        q=self.query.get().strip().casefold(); status=self.status_var.get()
        tf=self.type_var.get(); gf=self.gen_var.get(); owned=self.owned_set()
        wanted=None
        if gf.startswith("Generation "):
            try:wanted=int(gf.split()[-1])
            except Exception:pass
        out=[]
        for p in self.app.pokedex:
            name=p.get("name",""); dex=p.get("dex",0); types=p.get("types",[])
            is_owned=name.strip().casefold() in owned
            if q and not(q in name.casefold() or q==str(dex) or any(q in str(t).casefold() for t in types)):continue
            if status=="Owned" and not is_owned:continue
            if status=="Missing" and is_owned:continue
            if tf!="All types" and tf not in types:continue
            if wanted and generation_for_dex(dex)!=wanted:continue
            out.append(p)
        self.filtered=out

    def render_progress(self,owned_total,total):
        pct=(owned_total/total*100) if total else 0
        self.progress_title.config(text=f"National Living Dex   {owned_total} / {total}   •   {pct:.1f}%")
        missing=max(0,total-owned_total)
        self.progress_detail.config(text=f"{missing} remaining  •  Click a Pokémon sprite to toggle ownership  •  Missing Pokémon can be sent directly to Hunt Planner.")
        self.progress.delete("all")
        self.progress.update_idletasks()
        w=max(1,self.progress.winfo_width()); h=max(1,self.progress.winfo_height())
        self.progress.create_rectangle(0,0,w,h,fill=PANEL_2,outline="")
        self.progress.create_rectangle(0,0,w*(pct/100),h,fill=GOOD,outline="")

        for wgt in self.gen_strip.winfo_children():wgt.destroy()
        stats=self.generation_stats()
        for gen in range(1,10):
            have,totalg=stats[gen]; gp=(have/totalg*100) if totalg else 0
            b=tk.Button(self.gen_strip,text=f"Gen {gen}\n{have}/{totalg}  {gp:.0f}%",command=lambda g=gen:self.gen_var.set(f"Generation {g}"),bg=GOOD if totalg and have==totalg else PANEL,fg=TEXT,activebackground=PANEL_2,activeforeground=TEXT,relief="flat",font=("Segoe UI",8),padx=7,pady=5)
            b.pack(side="left",fill="x",expand=True,padx=(0,4 if gen<9 else 0))

    def render_page(self,prefetch=True):
        owned=self.owned_set(); total=len(self.app.pokedex)
        owned_total=sum(1 for p in self.app.pokedex if p.get("name","").strip().casefold() in owned)
        self.render_progress(owned_total,total)
        start=self.page_index*self.PAGE_SIZE; visible=self.filtered[start:start+self.PAGE_SIZE]
        self.sprite_refs={}; visible_dex=[]
        active_hunts={str(h.get("pokemon","")).strip().casefold() for h in self.app.profile.get("hunts",[])}

        for i,card in enumerate(self.cards):
            if i>=len(visible):card["outer"].grid_remove(); continue
            card["outer"].grid()
            p=visible[i]; name=p.get("name",""); dex=p.get("dex",0); types=" / ".join(p.get("types",[]))
            is_owned=name.strip().casefold() in owned
            bg=GOOD if is_owned else PANEL
            card["outer"].config(bg=bg)
            sprite=None; path=cached_sprite_path(dex)
            if path:
                try:
                    img=tk.PhotoImage(file=str(path))
                    if img.width()>=96 or img.height()>=96:img=img.subsample(2,2)
                    sprite=img; self.sprite_refs[i]=img
                except Exception:pass
            mark="✓ " if is_owned else ""
            card["main"].config(bg=bg)
            card["sprite"].config(
                image=sprite if sprite else "",
                text="" if sprite else "No sprite",
                bg=bg
            )
            card["info"].config(
                text=f"{mark}#{int(dex):04d}\n{name}\n{types}",
                bg=bg
            )

            # Entire main card area toggles ownership.
            toggle_cmd=lambda e=None,n=name:self.toggle_owned(n)
            for widget in (card["main"],card["sprite"],card["info"]):
                widget.bind("<Button-1>",toggle_cmd)

            card["detail"].config(command=lambda n=name:self.app.open_pokemon_detail(n))
            card["spawn"].config(command=lambda n=name:self.open_spawn_finder(n))
            card["hunt"].config(
                text="Hunting ✓" if name.casefold() in active_hunts else "Add Hunt",
                command=lambda n=name:self.add_hunt(n)
            )
            visible_dex.append(dex)

        pages=max(1,(len(self.filtered)+self.PAGE_SIZE-1)//self.PAGE_SIZE)
        self.page_label.config(text=f"Page {min(self.page_index+1,pages)} of {pages}")
        self.prev_btn.config(state="normal" if self.page_index>0 else "disabled")
        self.next_btn.config(state="normal" if (self.page_index+1)*self.PAGE_SIZE<len(self.filtered) else "disabled")
        self.summary.config(
            text=(
                f"{len(self.filtered)} Pokémon match current filters  •  "
                f"{owned_total} owned  •  {max(0,total-owned_total)} missing  •  "
                f"{pages} page{'s' if pages != 1 else ''}"
            )
        )
        if prefetch:self._prefetch_visible_sprites(tuple(visible_dex))

    def _prefetch_visible_sprites(self,dex_numbers):
        if not dex_numbers or self._sprite_download_running:return
        missing=[d for d in dex_numbers if not cached_sprite_path(d)]
        if not missing:return
        self._sprite_download_running=True
        def worker():
            for dex in missing:
                try:get_cached_sprite(dex)
                except Exception:pass
            def done():
                self._sprite_download_running=False
                try:
                    if self.winfo_exists():self.render_page(prefetch=False)
                except Exception:pass
            try:self.after(0,done)
            except Exception:pass
        threading.Thread(target=worker,daemon=True).start()

    def toggle_owned(self,pokemon):
        name=str(pokemon or "").strip()
        if not name:return
        current=list(self.app.profile.get("living_dex",[]))
        keys=[str(x).strip().casefold() for x in current]; key=name.casefold()
        if key in keys:current.pop(keys.index(key))
        else:current.append(name)
        self.app.profile["living_dex"]=current; self.app.save()
        self.rebuild_filter()
        self.page_index=min(self.page_index,max(0,(len(self.filtered)-1)//self.PAGE_SIZE))
        self.render_page(prefetch=False)

    def add_hunt(self,pokemon):
        name=str(pokemon or "").strip()
        if not name:return
        hunts=self.app.profile.setdefault("hunts",[])
        keys={str(h.get("pokemon","")).strip().casefold() for h in hunts}
        if name.casefold() not in keys:
            hunts.append({"pokemon":name,"note":"Added from Collection 2.0"})
            self.app.save()
        self.render_page(prefetch=False)

    def open_spawn_finder(self,pokemon):
        self.app.show_page("Spawn Finder")
        page=self.app.pages.get("Spawn Finder")
        if page and hasattr(page,"focus_pokemon"):page.focus_pokemon(pokemon)

    def prev_page(self):
        if self.page_index>0:self.page_index-=1; self.render_page(prefetch=True)

    def next_page(self):
        if (self.page_index+1)*self.PAGE_SIZE<len(self.filtered):
            self.page_index+=1; self.render_page(prefetch=True)


class PlaceholderPage(Page):
    def __init__(self, master, app, title, subtitle, bullets):
        self.title = title
        self.subtitle = subtitle
        super().__init__(master, app)
        self.header()
        card = tk.Frame(self, bg=PANEL)
        card.pack(fill="both", expand=True, padx=28, pady=(0,28))
        tk.Label(card, text="Coming next", bg=PANEL, fg=TEXT,
                 font=("Segoe UI Semibold", 16)).pack(anchor="w", padx=20, pady=(20,10))
        for b in bullets:
            tk.Label(card, text=f"•  {b}", bg=PANEL, fg=MUTED,
                     font=("Segoe UI", 11), anchor="w", justify="left").pack(fill="x", padx=22, pady=5)

class SettingsPage(Page):
    title = "Settings"
    subtitle = "Profile settings and official Cobblemon data source."

    def __init__(self, master, app):
        super().__init__(master, app)
        self.header()

        card = tk.Frame(self, bg=PANEL)
        card.pack(fill="x", padx=28, pady=(0, 14))
        tk.Label(card, text="Profile name", bg=PANEL, fg=TEXT,
                 font=("Segoe UI Semibold", 11)).pack(anchor="w", padx=18, pady=(18,5))
        self.profile_var = tk.StringVar(value=app.profile.get("profile_name",""))
        tk.Entry(card, textvariable=self.profile_var, bg=PANEL_2, fg=TEXT, insertbackground=TEXT,
                 relief="flat", font=("Segoe UI", 11)).pack(fill="x", padx=18, ipady=8)
        tk.Button(card, text="Save Profile", command=self.save_settings,
                  bg=ACCENT_2, fg="white", relief="flat", padx=14, pady=9).pack(anchor="w", padx=18, pady=18)

        data = tk.Frame(self, bg=PANEL)
        data.pack(fill="x", padx=28, pady=(0, 28))
        tk.Label(data, text="Cobblemon Pokédex Source", bg=PANEL, fg=TEXT,
                 font=("Segoe UI Semibold", 14)).pack(anchor="w", padx=18, pady=(18,5))
        tk.Label(
            data,
            text="Species and spawn rules come from your installed Cobblemon JAR. Clean 2D Pokédex sprites "
                 "are downloaded only when viewed and then cached locally.",
            bg=PANEL, fg=MUTED, font=("Segoe UI", 9), justify="left", wraplength=780
        ).pack(anchor="w", padx=18, pady=(0, 10))
        self.data_status = tk.Label(data, text="", bg=PANEL, fg=TEXT,
                                    font=("Segoe UI", 10, "bold"), justify="left")
        self.data_status.pack(anchor="w", padx=18, pady=(3, 10))

        buttons = tk.Frame(data, bg=PANEL)
        buttons.pack(anchor="w", padx=14, pady=(0, 18))
        tk.Button(buttons, text="Auto-Detect Cobblemon", command=self.auto_detect,
                  bg=ACCENT_2, fg="white", relief="flat", padx=14, pady=9).pack(side="left", padx=4)
        tk.Button(buttons, text="Select / Refresh JAR", command=self.select_jar,
                  bg=PANEL_2, fg=TEXT, relief="flat", padx=14, pady=9).pack(side="left", padx=4)
        tk.Button(buttons, text="Refresh Spawns Only", command=self.refresh_spawns_only,
                  bg=PANEL_2, fg=TEXT, relief="flat", padx=14, pady=9).pack(side="left", padx=4)
        self.refresh()

    def refresh(self):
        meta = self.app.dex_meta
        if meta.get("species_count"):
            self.data_status.config(
                text=f"✓ {meta['species_count']} implemented Pokémon loaded\n"
                     f"✓ {meta.get('spawn_count', 0)} spawn rules parsed\n"
                     f"Source: {meta.get('source_jar', 'Cobblemon JAR')}"
            )
        else:
            self.data_status.config(
                text="No full Cobblemon Dex imported yet. The Pokédex is showing a small starter preview."
            )

    def save_settings(self):
        self.app.profile["profile_name"] = self.profile_var.get().strip() or "My Cobblemon World"
        self.app.save()
        messagebox.showinfo(APP_NAME, "Profile saved.")

    def auto_detect(self):
        jars = candidate_cobblemon_jars()
        if not jars:
            messagebox.showinfo(
                APP_NAME,
                "I couldn't automatically find a Cobblemon .jar.\n\n"
                "Use 'Select Cobblemon .jar' and choose the Cobblemon file from your modpack's mods folder."
            )
            return
        self.import_jar(jars[0])

    def select_jar(self):
        path = filedialog.askopenfilename(
            title="Select your Cobblemon mod JAR",
            filetypes=[("Java archive", "*.jar"), ("All files", "*.*")]
        )
        if path:
            self.import_jar(Path(path))

    def refresh_spawns_only(self):
        path = self.app.dex_meta.get("source_jar")
        if not path or not Path(path).exists():
            path = filedialog.askopenfilename(
                title="Select your Cobblemon mod JAR",
                filetypes=[("Java archive", "*.jar"), ("All files", "*.*")]
            )
        if not path:
            return
        try:
            spawns = refresh_spawn_cache_from_jar(path)
            self.app.spawns = spawns
            self.app.dex_meta = load_dex_meta()
            self.app.refresh_data_pages()
            self.refresh()
            messagebox.showinfo(
                APP_NAME,
                f"Spawn cache refreshed.\n\nParsed {len(spawns)} spawn rules.\n"
                "Your existing Pokédex cache was left untouched."
            )
        except Exception as exc:
            messagebox.showerror(APP_NAME, f"Could not refresh spawn data:\n\n{exc}")

    def import_jar(self, path):
        try:
            species = import_species_from_cobblemon_jar(path)
            save_dex(species, path)
            self.app.pokedex = species
            self.app.dex_meta = load_dex_meta()
            self.app.spawns = load_spawn_data()
            self.app.refresh_data_pages()
            self.refresh()
            messagebox.showinfo(
                APP_NAME,
                f"Imported {len(species)} implemented Pokémon from:\n{Path(path).name}\n"
                f"Parsed {len(self.app.spawns)} spawn rules.\n"
                f"Data sources: {self.app.dex_meta.get('data_source_count', 1)} JAR(s).\n\n"
                "Base Cobblemon plus compatible addon datapacks were merged."
            )
        except Exception as exc:
            cached = self.app.dex_meta.get("species_count", 0)
            suffix = (
                f"\n\nYour existing cached Pokédex ({cached} Pokémon) is still intact."
                if cached else ""
            )
            messagebox.showerror(
                APP_NAME,
                f"Could not refresh species from that Cobblemon JAR:\n\n{exc}{suffix}"
            )

class PokemonPicker(tk.Toplevel):
    """Searchable selector backed by the Companion's implemented Cobblemon Pokédex."""

    def __init__(self, app, pokedex, title, current, callback):
        super().__init__(app)
        self.app = app
        self.pokedex = list(pokedex)
        self.callback = callback
        self.filtered = []

        self.title(title)
        self.configure(bg=BG)
        self.geometry("540x560")
        self.minsize(480, 480)
        self.transient(app)
        self.grab_set()

        tk.Label(
            self, text=title, bg=BG, fg=TEXT,
            font=("Segoe UI Semibold", 17)
        ).pack(anchor="w", padx=18, pady=(18, 4))

        tk.Label(
            self,
            text="Search by Pokémon name, National Dex number, or type.",
            bg=BG, fg=MUTED, font=("Segoe UI", 9)
        ).pack(anchor="w", padx=18, pady=(0, 10))

        self.query = tk.StringVar(value=current or "")
        entry = tk.Entry(
            self, textvariable=self.query, bg=PANEL, fg=TEXT,
            insertbackground=TEXT, relief="flat", font=("Segoe UI", 11)
        )
        entry.pack(fill="x", padx=18, ipady=8)
        entry.focus_set()
        entry.select_range(0, "end")
        entry.bind("<KeyRelease>", lambda e: self.refresh_list())

        body = tk.Frame(self, bg=BG)
        body.pack(fill="both", expand=True, padx=18, pady=10)

        self.listbox = tk.Listbox(
            body, bg=PANEL, fg=TEXT,
            selectbackground=ACCENT_2, selectforeground="white",
            relief="flat", bd=0, highlightthickness=0,
            font=("Segoe UI", 10)
        )
        scroll = tk.Scrollbar(body, orient="vertical", command=self.listbox.yview)
        self.listbox.config(yscrollcommand=scroll.set)
        self.listbox.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        self.listbox.bind("<Double-Button-1>", lambda e: self.choose())
        self.listbox.bind("<Return>", lambda e: self.choose())

        self.status = tk.Label(self, text="", bg=BG, fg=MUTED, font=("Segoe UI", 9))
        self.status.pack(anchor="w", padx=18, pady=(0, 8))

        buttons = tk.Frame(self, bg=BG)
        buttons.pack(fill="x", padx=18, pady=(0, 18))

        tk.Button(
            buttons, text="Clear Slot", command=lambda: self.submit(""),
            bg=PANEL_2, fg=TEXT, relief="flat", padx=12, pady=8
        ).pack(side="left")

        tk.Button(
            buttons, text="Cancel", command=self.destroy,
            bg=PANEL_2, fg=TEXT, relief="flat", padx=12, pady=8
        ).pack(side="right")

        tk.Button(
            buttons, text="Choose Pokémon", command=self.choose,
            bg=ACCENT_2, fg="white", relief="flat", padx=14, pady=8
        ).pack(side="right", padx=(0, 8))

        self.refresh_list()

    def refresh_list(self):
        q = self.query.get().strip().lower()
        self.filtered = [
            p for p in self.pokedex
            if (
                not q
                or q in p.get("name", "").lower()
                or q == str(p.get("dex", ""))
                or any(q in t.lower() for t in p.get("types", []))
            )
        ]

        self.listbox.delete(0, "end")
        for p in self.filtered[:500]:
            type_text = " / ".join(p.get("types", []))
            self.listbox.insert(
                "end",
                f"#{int(p.get('dex', 0)):04d}   {p.get('name','')}   —   {type_text}"
            )

        self.status.config(
            text=f"{len(self.filtered)} implemented Pokémon match"
            + (" • showing first 500" if len(self.filtered) > 500 else "")
        )

        if self.filtered:
            self.listbox.selection_set(0)

    def choose(self):
        selected = self.listbox.curselection()
        if not selected:
            return
        idx = selected[0]
        if idx < len(self.filtered):
            self.submit(self.filtered[idx].get("name", ""))

    def submit(self, value):
        self.callback(value)
        self.destroy()

class PopupEntry(tk.Toplevel):
    def __init__(self, app, title, label, initial, callback):
        super().__init__(app)
        self.callback = callback
        self.title(title)
        self.configure(bg=BG)
        self.geometry("420x160")
        self.resizable(False, False)
        self.transient(app)
        self.grab_set()

        tk.Label(self, text=label, bg=BG, fg=TEXT,
                 font=("Segoe UI Semibold", 11)).pack(anchor="w", padx=18, pady=(18,6))
        self.var = tk.StringVar(value=initial)
        entry = tk.Entry(self, textvariable=self.var, bg=PANEL, fg=TEXT,
                         insertbackground=TEXT, relief="flat", font=("Segoe UI", 11))
        entry.pack(fill="x", padx=18, ipady=8)
        entry.select_range(0, "end")
        entry.focus_set()

        buttons = tk.Frame(self, bg=BG)
        buttons.pack(fill="x", padx=18, pady=14)
        tk.Button(buttons, text="Cancel", command=self.destroy, bg=PANEL_2, fg=TEXT,
                  relief="flat", padx=12, pady=7).pack(side="right")
        tk.Button(buttons, text="Save", command=self.submit, bg=ACCENT_2, fg="white",
                  relief="flat", padx=12, pady=7).pack(side="right", padx=(0,8))
        self.bind("<Return>", lambda e: self.submit())
        self.bind("<Escape>", lambda e: self.destroy())

    def submit(self):
        self.callback(self.var.get())
        self.destroy()

class DatabasePage(Page):
    title = "Database"
    subtitle = "Moves, abilities, and Cobblemon items — separated, searchable, and cross-referenced."

    PAGE_SIZE = 36

    def __init__(self, master, app):
        super().__init__(master, app)
        self.active_category = "Moves"
        self.query = tk.StringVar()
        self.page_index = 0
        self.entries = []
        self._loaded_once = False
        self._search_after = None

        self.header()

        tabs = tk.Frame(self, bg=BG)
        tabs.pack(fill="x", padx=28, pady=(0, 10))
        self.tab_buttons = {}

        for category in ("Moves", "Abilities", "Items"):
            btn = tk.Button(
                tabs, text=category,
                command=lambda c=category: self.set_category(c),
                bg=PANEL_2, fg=TEXT,
                activebackground=ACCENT_2, activeforeground="white",
                relief="flat", bd=0, padx=18, pady=9,
                font=("Segoe UI Semibold", 10)
            )
            btn.pack(side="left", padx=(0, 6))
            self.tab_buttons[category] = btn

        self.category_blurb = tk.Label(
            self, text="", bg=BG, fg=MUTED,
            font=("Segoe UI", 9), justify="left"
        )
        self.category_blurb.pack(anchor="w", padx=29, pady=(0, 8))

        search = tk.Frame(self, bg=BG)
        search.pack(fill="x", padx=28, pady=(0, 8))

        tk.Entry(
            search, textvariable=self.query,
            bg=PANEL, fg=TEXT, insertbackground=TEXT,
            relief="flat", font=("Segoe UI", 11)
        ).pack(side="left", fill="x", expand=True, ipady=9)

        tk.Button(
            search, text="Clear", command=lambda: self.query.set(""),
            bg=PANEL_2, fg=TEXT, relief="flat", padx=12, pady=8
        ).pack(side="left", padx=(8, 0))

        self.status = tk.Label(self, text="", bg=BG, fg=MUTED, font=("Segoe UI", 9))
        self.status.pack(anchor="w", padx=29, pady=(0, 8))

        body = tk.Frame(self, bg=BG)
        body.pack(fill="both", expand=True, padx=28, pady=(0, 8))

        self.canvas = tk.Canvas(body, bg=BG, highlightthickness=0)
        self.scroll = tk.Scrollbar(body, orient="vertical", command=self.canvas.yview)
        self.results_frame = tk.Frame(self.canvas, bg=BG)
        self.window_id = self.canvas.create_window((0, 0), window=self.results_frame, anchor="nw")
        self.results_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        self.canvas.bind(
            "<Configure>",
            lambda e: self.canvas.itemconfigure(self.window_id, width=e.width)
        )
        self.canvas.configure(yscrollcommand=self.scroll.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scroll.pack(side="right", fill="y")

        pager = tk.Frame(self, bg=BG)
        pager.pack(fill="x", padx=28, pady=(0, 28))

        self.prev_btn = tk.Button(
            pager, text="← Previous", command=self.prev_page,
            bg=PANEL_2, fg=TEXT, relief="flat", padx=14, pady=7
        )
        self.prev_btn.pack(side="left")

        self.page_label = tk.Label(
            pager, text="", bg=BG, fg=TEXT,
            font=("Segoe UI Semibold", 9)
        )
        self.page_label.pack(side="left", expand=True)

        self.next_btn = tk.Button(
            pager, text="Next →", command=self.next_page,
            bg=PANEL_2, fg=TEXT, relief="flat", padx=14, pady=7
        )
        self.next_btn.pack(side="right")

        self.query.trace_add("write", lambda *_: self.schedule_search())
        self._set_tab_visuals()
        self.show_idle()

    def refresh(self):
        # Called only when the user actually opens Database via show_page().
        if not self._loaded_once:
            self._loaded_once = True
            self.rebuild_entries()
        self.render_page()

    def items_refreshed(self):
        if self.active_category == "Items" and self._loaded_once:
            self.rebuild_entries()
            self.render_page()

    def _set_tab_visuals(self):
        for name, btn in self.tab_buttons.items():
            btn.config(
                bg=ACCENT_2 if name == self.active_category else PANEL_2,
                fg="white" if name == self.active_category else TEXT
            )

        blurbs = {
            "Moves": "Moves found in implemented Cobblemon learnsets. Details cross-reference exactly which implemented Pokémon can learn them.",
            "Abilities": "Abilities found on implemented Cobblemon species, separated from moves and linked back to compatible Pokémon.",
            "Items": "Items registered by the installed Cobblemon JAR. Categories are inferred from Cobblemon item tags and identifiers where possible."
        }
        self.category_blurb.config(text=blurbs[self.active_category])

    def set_category(self, category):
        self.active_category = category
        self.page_index = 0
        self._set_tab_visuals()
        if self._loaded_once:
            self.rebuild_entries()
            self.render_page()

    def schedule_search(self):
        self.page_index = 0
        if self._search_after is not None:
            try:
                self.after_cancel(self._search_after)
            except Exception:
                pass
        self._search_after = self.after(180, self._run_search)

    def _run_search(self):
        self._search_after = None
        if not self._loaded_once:
            return
        self.rebuild_entries()
        self.render_page()

    def show_idle(self):
        for w in self.results_frame.winfo_children():
            w.destroy()
        self.status.config(text="Database loads when you open this tab.")
        self.page_label.config(text="")
        self.prev_btn.config(state="disabled")
        self.next_btn.config(state="disabled")
        tk.Label(
            self.results_frame,
            text="Reference database ready.",
            bg=PANEL, fg=TEXT,
            font=("Segoe UI Semibold", 13),
            padx=18, pady=24
        ).pack(fill="x")

    def rebuild_entries(self):
        q = self.query.get().strip().lower()

        if self.active_category == "Moves":
            values = [{"name": n} for n in indexed_move_names(self.app)]
        elif self.active_category == "Abilities":
            values = [{"name": n} for n in indexed_ability_names(self.app)]
        else:
            values = list(self.app.item_index or [])

        if q:
            values = [x for x in values if q in x.get("name","").lower()]
            values.sort(key=lambda x: (not x.get("name","").lower().startswith(q), x.get("name","")))
        else:
            values.sort(key=lambda x: x.get("name",""))

        self.entries = values
        max_page = max(0, (len(values)-1)//self.PAGE_SIZE)
        self.page_index = min(self.page_index, max_page)

    def render_page(self):
        for w in self.results_frame.winfo_children():
            w.destroy()

        total = len(self.entries)
        start = self.page_index * self.PAGE_SIZE
        visible = self.entries[start:start+self.PAGE_SIZE]

        self.status.config(text=f"{total} {self.active_category.lower()} match")

        if not visible:
            msg = (
                "Item catalog is still being indexed from your Cobblemon JAR…"
                if self.active_category == "Items" and not self.app.item_index
                else f"No {self.active_category.lower()} match your search."
            )
            tk.Label(
                self.results_frame, text=msg,
                bg=PANEL, fg=MUTED,
                font=("Segoe UI", 11),
                padx=18, pady=28
            ).pack(fill="x")

        for entry in visible:
            name = entry.get("name","")
            card = tk.Frame(self.results_frame, bg=PANEL)
            card.pack(fill="x", pady=3)

            left = tk.Frame(card, bg=PANEL)
            left.pack(side="left", fill="x", expand=True, padx=14, pady=9)

            tk.Label(
                left, text=name,
                bg=PANEL, fg=TEXT,
                font=("Segoe UI Semibold", 10)
            ).pack(anchor="w")

            if self.active_category == "Moves":
                record = self.app._move_index.get(name.lower(), {})
                count = len(record.get("pokemon", []))
                meta = get_move_metadata(name, allow_network=False)
                sub = f"{count} implemented Pokémon can learn it"
                if meta:
                    sub = f"{meta.get('type','—')} • {meta.get('category','—')} • {sub}"
                kind = "Move"
            elif self.active_category == "Abilities":
                record = self.app._ability_index.get(name.lower(), {})
                count = len(record.get("pokemon", []))
                sub = f"Available to {count} implemented Pokémon"
                kind = "Ability"
            else:
                sub = entry.get("category") or "Cobblemon Item"
                kind = "Item"

            tk.Label(
                left, text=sub,
                bg=PANEL, fg=MUTED,
                font=("Segoe UI", 8)
            ).pack(anchor="w", pady=(2,0))

            tk.Button(
                card, text="Open Details",
                command=lambda k=kind,n=name: self.app.open_reference_detail(k,n),
                bg=PANEL_2, fg=TEXT,
                activebackground=ACCENT_2, activeforeground="white",
                relief="flat", padx=12, pady=7
            ).pack(side="right", padx=12)

        total_pages = max(1, (total+self.PAGE_SIZE-1)//self.PAGE_SIZE)
        self.page_label.config(text=f"Page {min(self.page_index+1,total_pages)} of {total_pages}")
        self.prev_btn.config(state="normal" if self.page_index > 0 else "disabled")
        self.next_btn.config(
            state="normal"
            if (self.page_index+1)*self.PAGE_SIZE < total
            else "disabled"
        )
        self.canvas.yview_moveto(0)

    def prev_page(self):
        if self.page_index > 0:
            self.page_index -= 1
            self.render_page()

    def next_page(self):
        if (self.page_index+1)*self.PAGE_SIZE < len(self.entries):
            self.page_index += 1
            self.render_page()


class BreedingPlannerPage(Page):
    title = "Breeding Planner"
    subtitle = "Plan compatible parents and candidate Egg Move routes using your installed Cobblemon species data."

    def __init__(self, master, app):
        super().__init__(master, app)
        self.target_name = tk.StringVar()
        self.target = None
        self.desired_move = tk.StringVar()
        self.sprite_ref = None
        self.header()

        top = tk.Frame(self, bg=PANEL)
        top.pack(fill="x", padx=28, pady=(0, 10))

        tk.Label(top, text="Target Pokémon", bg=PANEL, fg=TEXT,
                 font=("Segoe UI Semibold", 11)).pack(anchor="w", padx=14, pady=(12, 5))

        row = tk.Frame(top, bg=PANEL)
        row.pack(fill="x", padx=14, pady=(0, 12))

        tk.Entry(row, textvariable=self.target_name, state="readonly",
                 readonlybackground=PANEL_2, fg=TEXT, relief="flat",
                 font=("Segoe UI", 10)).pack(side="left", fill="x", expand=True, ipady=8)

        tk.Button(row, text="Choose Pokémon", command=self.choose_target,
                  bg=ACCENT_2, fg="white", relief="flat",
                  padx=12, pady=8).pack(side="left", padx=(8,0))

        self.summary = tk.Frame(self, bg=BG)
        self.summary.pack(fill="x", padx=28, pady=(0, 8))

        tabs = tk.Frame(self, bg=BG)
        tabs.pack(fill="x", padx=28, pady=(0, 8))
        self.mode = tk.StringVar(value="Compatible Parents")
        self.mode_buttons = {}
        for label in ("Compatible Parents", "Egg Move Planner"):
            b = tk.Button(tabs, text=label,
                          command=lambda v=label:self.set_mode(v),
                          bg=PANEL_2, fg=TEXT, relief="flat",
                          padx=16, pady=8, font=("Segoe UI Semibold", 9))
            b.pack(side="left", padx=(0,5))
            self.mode_buttons[label] = b

        self.controls = tk.Frame(self, bg=BG)
        self.controls.pack(fill="x", padx=28, pady=(0, 8))

        body = tk.Frame(self, bg=BG)
        body.pack(fill="both", expand=True, padx=28, pady=(0, 28))

        self.canvas = tk.Canvas(body, bg=BG, highlightthickness=0)
        scroll = tk.Scrollbar(body, orient="vertical", command=self.canvas.yview)
        self.results = tk.Frame(self.canvas, bg=BG)
        win = self.canvas.create_window((0,0), window=self.results, anchor="nw")
        self.results.bind("<Configure>", lambda e:self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", lambda e:self.canvas.itemconfigure(win, width=e.width))
        self.canvas.configure(yscrollcommand=scroll.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        self.update_mode_buttons()
        self.render_idle()

    def refresh(self):
        current = self.target_name.get().strip()
        remembered = str(self.app.profile.get("last_breeding_target", "") or "").strip()
        target = current or remembered
        if target:
            # Avoid re-saving/rebuilding needlessly when already focused.
            if self.target and self.target.get("name","").casefold() == target.casefold():
                return
            self.target_name.set(target)
            self.target = species_by_name(self.app.pokedex, target)
            self.render_summary()
            self.render_controls()
            self.render_results()

    def focus_pokemon(self, pokemon):
        self.target_name.set(pokemon)
        self.target = species_by_name(self.app.pokedex, pokemon)
        self.app.profile["last_breeding_target"] = pokemon
        self.app.save()
        self.desired_move.set("")
        self.render_summary()
        self.render_controls()
        self.render_results()

    def choose_target(self):
        PokemonPicker(self.app, self.app.pokedex, "Choose Breeding Target",
                      self.target_name.get(), self.focus_pokemon)

    def set_mode(self, mode):
        self.mode.set(mode)
        self.update_mode_buttons()
        self.render_controls()
        self.render_results()

    def update_mode_buttons(self):
        for name,b in self.mode_buttons.items():
            b.config(bg=ACCENT_2 if name==self.mode.get() else PANEL_2,
                     fg="white" if name==self.mode.get() else TEXT)

    def render_idle(self):
        for w in self.summary.winfo_children(): w.destroy()
        for w in self.controls.winfo_children(): w.destroy()
        for w in self.results.winfo_children(): w.destroy()
        tk.Label(self.results, text="Choose a Pokémon to begin planning.",
                 bg=PANEL, fg=MUTED, font=("Segoe UI", 12),
                 padx=18, pady=30).pack(fill="x")

    def render_summary(self):
        for w in self.summary.winfo_children(): w.destroy()
        if not self.target: return

        box=tk.Frame(self.summary,bg=PANEL); box.pack(fill="x")
        left=tk.Frame(box,bg=PANEL); left.pack(side="left",fill="x",expand=True,padx=14,pady=12)

        tk.Label(left,text=self.target["name"],bg=PANEL,fg=TEXT,
                 font=("Segoe UI Semibold",18)).pack(anchor="w")
        groups=[friendly_resource_name(x) for x in self.target.get("egg_groups",[])]
        egg_moves=species_egg_moves(self.target)
        tk.Label(left,text="Egg Groups: "+(", ".join(groups) or "None / unknown"),
                 bg=PANEL,fg=MUTED,font=("Segoe UI",9)).pack(anchor="w",pady=(3,0))
        tk.Label(left,text=f"{len(egg_moves)} move(s) explicitly marked Egg in imported learnset data",
                 bg=PANEL,fg=MUTED,font=("Segoe UI",8)).pack(anchor="w",pady=(2,0))

        path=cached_sprite_path(self.target.get("dex"))
        if path:
            try:
                img=tk.PhotoImage(file=str(path))
                self.sprite_ref=img
                tk.Label(box,image=img,bg=PANEL,bd=0).pack(side="right",padx=14,pady=8)
            except Exception: pass

    def render_controls(self):
        for w in self.controls.winfo_children(): w.destroy()
        if not self.target: return

        if self.mode.get()=="Egg Move Planner":
            box=tk.Frame(self.controls,bg=PANEL)
            box.pack(fill="x")

            tk.Label(box,text="Desired Egg Move",bg=PANEL,fg=TEXT,
                     font=("Segoe UI Semibold",10)).pack(anchor="w",padx=12,pady=(10,4))

            row=tk.Frame(box,bg=PANEL)
            row.pack(fill="x",padx=12,pady=(0,10))

            tk.Entry(row,textvariable=self.desired_move,state="readonly",
                     readonlybackground=PANEL_2,fg=TEXT,relief="flat",
                     font=("Segoe UI",10)).pack(side="left",fill="x",expand=True,ipady=7)

            tk.Button(row,text="Choose Move",command=self.choose_egg_move,
                      bg=PANEL_2,fg=TEXT,relief="flat",
                      padx=12,pady=7).pack(side="left",padx=(8,0))

    def choose_egg_move(self):
        moves=species_egg_moves(self.target)
        if not moves:
            messagebox.showinfo(
                APP_NAME,
                "This installed Cobblemon species data does not explicitly mark any Egg moves for this Pokémon."
            )
            return
        MovePicker(self.app,moves,self.desired_move.get(),self.set_egg_move)

    def set_egg_move(self, move):
        self.desired_move.set(move)
        self.render_results()

    def render_results(self):
        for w in self.results.winfo_children(): w.destroy()
        if not self.target:
            self.render_idle()
            return

        if self.mode.get()=="Compatible Parents":
            self.render_compatible()
        else:
            self.render_egg_routes()
        self.canvas.yview_moveto(0)

    def render_compatible(self):
        compatible=breeding_compatible_species(self.app.pokedex,self.target)
        tk.Label(self.results,
                 text=f"{len(compatible)} implemented Pokémon share at least one Egg Group with {self.target['name']}.",
                 bg=BG,fg=MUTED,font=("Segoe UI",9)).pack(anchor="w",pady=(0,6))

        for p,shared in compatible[:160]:
            card=tk.Frame(self.results,bg=PANEL); card.pack(fill="x",pady=3)
            left=tk.Frame(card,bg=PANEL); left.pack(side="left",fill="x",expand=True,padx=12,pady=8)
            tk.Label(left,text=p["name"],bg=PANEL,fg=TEXT,
                     font=("Segoe UI Semibold",10)).pack(anchor="w")
            tk.Label(left,text="Shared: "+", ".join(friendly_resource_name(x) for x in shared),
                     bg=PANEL,fg=MUTED,font=("Segoe UI",8)).pack(anchor="w",pady=(2,0))

            actions=tk.Frame(card,bg=PANEL); actions.pack(side="right",padx=10)
            tk.Button(actions,text="Pokédex",command=lambda n=p["name"]:self.app.open_pokemon_detail(n),
                      bg=PANEL_2,fg=TEXT,relief="flat",padx=8,pady=5).pack(side="left",padx=2)
            tk.Button(actions,text="Find Spawns",command=lambda n=p["name"]:self.open_spawn(n),
                      bg=PANEL_2,fg=TEXT,relief="flat",padx=8,pady=5).pack(side="left",padx=2)
            tk.Button(actions,text="Add Hunt",command=lambda n=p["name"]:self.add_hunt(n),
                      bg=PANEL_2,fg=TEXT,relief="flat",padx=8,pady=5).pack(side="left",padx=2)

        if len(compatible)>160:
            tk.Label(self.results,text=f"Showing first 160 of {len(compatible)} compatible species.",
                     bg=BG,fg=MUTED,font=("Segoe UI",8)).pack(anchor="w",pady=(5,0))

    def render_egg_routes(self):
        move=self.desired_move.get().strip()
        if not move:
            moves=species_egg_moves(self.target)
            box=tk.Frame(self.results,bg=PANEL); box.pack(fill="x")
            if moves:
                tk.Label(box,text=f"Choose one of {len(moves)} Egg moves explicitly marked for {self.target['name']}.",
                         bg=PANEL,fg=TEXT,font=("Segoe UI",10),padx=14,pady=16).pack(anchor="w")
            else:
                tk.Label(box,text="No moves are explicitly marked as Egg moves in this Pokémon's imported data.",
                         bg=PANEL,fg=MUTED,font=("Segoe UI",10),padx=14,pady=16).pack(anchor="w")
            return

        direct=breeding_move_sources(self.app.pokedex,self.target,move)

        tk.Label(self.results,text=f"Direct compatible parents for {move}",
                 bg=BG,fg=TEXT,font=("Segoe UI Semibold",12)).pack(anchor="w",pady=(0,4))
        tk.Label(self.results,
                 text="Candidates below share an Egg Group with the target and have the move somewhere in their imported learnset.",
                 bg=BG,fg=MUTED,font=("Segoe UI",8),wraplength=900,justify="left").pack(anchor="w",pady=(0,6))

        if direct:
            for entry in direct[:80]:
                p=entry["species"]
                card=tk.Frame(self.results,bg=PANEL); card.pack(fill="x",pady=3)
                left=tk.Frame(card,bg=PANEL); left.pack(side="left",fill="x",expand=True,padx=12,pady=8)
                tk.Label(left,text=p["name"],bg=PANEL,fg=TEXT,font=("Segoe UI Semibold",10)).pack(anchor="w")
                method=", ".join(entry["methods"])
                shared=", ".join(friendly_resource_name(x) for x in entry["shared_groups"])
                tk.Label(left,text=f"Learns {move} via: {method}   •   Shared Egg Group: {shared}",
                         bg=PANEL,fg=MUTED,font=("Segoe UI",8)).pack(anchor="w",pady=(2,0))
                tk.Button(card,text="Open Pokédex",command=lambda n=p["name"]:self.app.open_pokemon_detail(n),
                          bg=PANEL_2,fg=TEXT,relief="flat",padx=9,pady=6).pack(side="right",padx=10)
        else:
            tk.Label(self.results,text="No direct compatible move source found.",
                     bg=PANEL,fg=MUTED,font=("Segoe UI",9),padx=10,pady=8).pack(anchor="w")

        chains=breeding_chain_candidates(self.app.pokedex,self.target,move,max_depth=3)
        tk.Label(self.results,text="Candidate Egg Group chains",
                 bg=BG,fg=TEXT,font=("Segoe UI Semibold",12)).pack(anchor="w",pady=(14,4))
        tk.Label(self.results,
                 text="These are connectivity candidates, not guaranteed breeding recipes. Gender, form, or server-specific inheritance rules may still matter.",
                 bg=BG,fg=MUTED,font=("Segoe UI",8),wraplength=900,justify="left").pack(anchor="w",pady=(0,6))

        shown=0
        seen_paths=set()
        for chain in chains:
            path=tuple(chain["path"])
            if len(path)<=2 or path in seen_paths:
                continue
            seen_paths.add(path); shown+=1
            card=tk.Frame(self.results,bg=PANEL); card.pack(fill="x",pady=3)
            tk.Label(card,text="  →  ".join(path),bg=PANEL,fg=TEXT,
                     font=("Segoe UI Semibold",9),wraplength=880,justify="left").pack(anchor="w",padx=12,pady=(8,2))
            tk.Label(card,text=f"Source learns {move} via: {', '.join(chain['methods'])}",
                     bg=PANEL,fg=MUTED,font=("Segoe UI",8)).pack(anchor="w",padx=12,pady=(0,8))
            if shown>=20: break
        if not shown:
            tk.Label(self.results,text="No longer Egg Group chain found within 3 breeding steps.",
                     bg=PANEL,fg=MUTED,font=("Segoe UI",9),padx=10,pady=8).pack(anchor="w")

    def open_spawn(self, pokemon):
        self.app.show_page("Spawn Finder")
        page=self.app.pages.get("Spawn Finder")
        if page and hasattr(page,"focus_pokemon"):
            page.focus_pokemon(pokemon)

    def add_hunt(self, pokemon):
        hunts=self.app.profile.setdefault("hunts",[])
        if not any(str(h.get("pokemon","")).casefold()==pokemon.casefold() for h in hunts):
            hunts.append({"pokemon":pokemon,"note":"Breeding parent"})
            self.app.save()
        page=self.app.pages.get("Hunts")
        if page and hasattr(page,"refresh"): page.refresh()



# ---------------------------------------------------------------------------
# V1.7.0 — Desktop Overlay System
# ---------------------------------------------------------------------------

class CompanionOverlay(tk.Toplevel):
    def __init__(self, app, kind):
        super().__init__(app)
        self.app=app
        self.kind=kind
        self.edit_mode=True
        self.sprite_refs={}
        self._drag=None
        self.configure(bg="#10151d")
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        try:self.attributes("-alpha", float(app.profile.setdefault("overlay_settings",{}).get("opacity",0.94)))
        except Exception:pass

        saved=app.profile.setdefault("overlay_settings",{}).setdefault("geometry",{}).get(kind)
        default="360x250+40+80" if kind=="hunt" else "430x390+760+80"
        self.geometry(saved or default)
        self.minsize(260,170)

        self.shell=tk.Frame(self,bg="#10151d",highlightthickness=2,highlightbackground=ACCENT_2)
        self.shell.pack(fill="both",expand=True)
        self.header=tk.Frame(self.shell,bg="#18202b",height=32,cursor="fleur")
        self.header.pack(fill="x")
        self.header.pack_propagate(False)
        self.title_label=tk.Label(self.header,text="",bg="#18202b",fg=TEXT,font=("Segoe UI Semibold",9))
        self.title_label.pack(side="left",padx=10)
        self.lock_btn=tk.Button(self.header,text="LOCK",command=self.toggle_edit,bg="#18202b",fg=MUTED,relief="flat",bd=0,font=("Segoe UI",7,"bold"))
        self.lock_btn.pack(side="right",padx=4)
        tk.Button(self.header,text="×",command=lambda:self.app.close_overlay(kind),bg="#18202b",fg=MUTED,relief="flat",bd=0,font=("Segoe UI",11)).pack(side="right",padx=(0,5))
        self.body=tk.Frame(self.shell,bg="#10151d")
        self.body.pack(fill="both",expand=True,padx=10,pady=8)
        self.grip=tk.Label(self.shell,text="◢",bg="#10151d",fg=MUTED,cursor="size_nw_se",font=("Segoe UI",9))
        self.grip.place(relx=1,rely=1,anchor="se")

        for w in (self.header,self.title_label):
            w.bind("<ButtonPress-1>",self.drag_start)
            w.bind("<B1-Motion>",self.drag_move)
        self.grip.bind("<ButtonPress-1>",self.resize_start)
        self.grip.bind("<B1-Motion>",self.resize_move)
        self.bind("<Configure>",self.remember_geometry)
        self.protocol("WM_DELETE_WINDOW",lambda:self.app.close_overlay(kind))
        self.refresh()

    def drag_start(self,e):
        if not self.edit_mode:return
        self._drag=(e.x_root-self.winfo_x(),e.y_root-self.winfo_y())
    def drag_move(self,e):
        if not self.edit_mode or not self._drag:return
        self.geometry(f"+{e.x_root-self._drag[0]}+{e.y_root-self._drag[1]}")
    def resize_start(self,e):
        if self.edit_mode:self._resize=(e.x_root,e.y_root,self.winfo_width(),self.winfo_height())
    def resize_move(self,e):
        if not self.edit_mode or not hasattr(self,"_resize"):return
        x,y,w,h=self._resize
        self.geometry(f"{max(260,w+e.x_root-x)}x{max(170,h+e.y_root-y)}")
    def remember_geometry(self,e=None):
        if getattr(self,"_save_after",None):
            try:self.after_cancel(self._save_after)
            except Exception:pass
        self._save_after=self.after(350,self._save_geometry)
    def _save_geometry(self):
        self.app.profile.setdefault("overlay_settings",{}).setdefault("geometry",{})[self.kind]=self.geometry()
        save_profile(self.app.profile)
    def toggle_edit(self):
        self.edit_mode=not self.edit_mode
        self.lock_btn.config(text="LOCK" if self.edit_mode else "EDIT")
        self.grip.place(relx=1,rely=1,anchor="se") if self.edit_mode else self.grip.place_forget()
        self.shell.config(highlightthickness=2 if self.edit_mode else 1,highlightbackground=ACCENT_2 if self.edit_mode else "#283442")

    def refresh(self):
        for w in self.body.winfo_children():w.destroy()
        self.sprite_refs={}
        if self.kind=="hunt":self.render_hunt()
        else:self.render_bingo()

    def render_hunt(self):
        self.title_label.config(text="COBBLEMON • CURRENT HUNT")
        intel=hunt_intelligence(self.app)
        targets=intel.get("targets",[])
        if not targets:
            tk.Label(self.body,text="No active hunt targets",bg="#10151d",fg=TEXT,font=("Segoe UI Semibold",14)).pack(anchor="w",pady=12)
            tk.Label(self.body,text="Add a Pokémon in Hunt Planner.",bg="#10151d",fg=MUTED,font=("Segoe UI",9)).pack(anchor="w")
            return
        t=targets[0]
        row=tk.Frame(self.body,bg="#10151d"); row.pack(fill="x")
        species=t.get("species")
        if species:
            path=cached_sprite_path(species.get("dex"))
            if path:
                try:
                    img=tk.PhotoImage(file=str(path))
                    if img.width()>=80:img=img.subsample(2,2)
                    self.sprite_refs["main"]=img
                    tk.Label(row,image=img,bg="#10151d").pack(side="left",padx=(0,10))
                except Exception:pass
        info=tk.Frame(row,bg="#10151d"); info.pack(side="left",fill="x",expand=True)
        tk.Label(info,text=t["name"],bg="#10151d",fg=TEXT,font=("Segoe UI Semibold",18)).pack(anchor="w")
        tk.Label(info,text=" • ".join(t["reasons"]),bg="#10151d",fg=ACCENT_2,font=("Segoe UI",8,"bold"),wraplength=260,justify="left").pack(anchor="w")
        lines=[]
        if t["habitats"]:lines.append("Areas  "+", ".join(t["habitats"][:3]))
        if t["times"]:lines.append("Time   "+", ".join(t["times"][:2]))
        if t["weather"]:lines.append("Weather   "+", ".join(t["weather"][:2]))
        combo=" + ".join(x[0] for x in t["snack"].get("combo",[]))
        if combo:lines.append("Snack   "+combo)
        for line in lines:
            tk.Label(self.body,text=line,bg="#10151d",fg=MUTED,font=("Segoe UI",8),wraplength=max(220,self.winfo_width()-30),justify="left").pack(anchor="w",pady=2)

    def render_bingo(self):
        self.title_label.config(text="COBBLEMON • WEEKLY BINGO")
        card=self.app.profile.get("bingo",[])
        filled=sum(bool(x.get("pokemon","").strip()) for x in card)
        caught=sum(bool(x.get("pokemon","").strip()) and bool(x.get("caught")) for x in card)
        tk.Label(self.body,text=f"{caught}/{filled} caught",bg="#10151d",fg=MUTED,font=("Segoe UI",8)).pack(anchor="w",pady=(0,5))
        grid=tk.Frame(self.body,bg="#10151d"); grid.pack(fill="both",expand=True)
        for r in range(5):grid.grid_rowconfigure(r,weight=1,uniform="b")
        for c in range(5):grid.grid_columnconfigure(c,weight=1,uniform="b")
        for i in range(25):
            item=card[i] if i<len(card) else {}
            name=item.get("pokemon","").strip(); caught=bool(item.get("caught"))
            bg=GOOD if name and caught else "#18202b"
            tile=tk.Frame(grid,bg=bg)
            tile.grid(row=i//5,column=i%5,sticky="nsew",padx=2,pady=2)
            species=species_by_name(self.app.pokedex,name) if name else None
            image=None
            if species:
                path=cached_sprite_path(species.get("dex"))
                if path:
                    try:
                        image=tk.PhotoImage(file=str(path))
                        if image.width()>=80:image=image.subsample(3,3)
                        self.sprite_refs[i]=image
                    except Exception:image=None
            tk.Label(tile,image=image if image else "",text="" if image else ("✓" if caught else "•"),bg=bg,fg=TEXT,font=("Segoe UI",8)).pack(expand=True)
            if name:
                tk.Label(tile,text=("✓ " if caught else "")+name,bg=bg,fg=TEXT,font=("Segoe UI",6),wraplength=75).pack(fill="x",pady=(0,2))


class OverlayManagerPage(Page):
    title="Overlays"
    subtitle="Pin clean, live Companion information over Minecraft. Best with windowed or borderless fullscreen."

    def __init__(self,master,app):
        super().__init__(master,app); self.header()
        box=tk.Frame(self,bg=PANEL); box.pack(fill="x",padx=28,pady=(0,12))
        tk.Label(box,text="Overlay Controls",bg=PANEL,fg=TEXT,font=("Segoe UI Semibold",14)).pack(anchor="w",padx=16,pady=(14,4))
        tk.Label(box,text="Overlays stay above Minecraft, remember their size and position, and can be locked after placement.",bg=PANEL,fg=MUTED,font=("Segoe UI",9),wraplength=800,justify="left").pack(anchor="w",padx=16,pady=(0,12))
        row=tk.Frame(box,bg=PANEL); row.pack(fill="x",padx=16,pady=(0,14))
        tk.Button(row,text="Toggle Current Hunt",command=lambda:app.toggle_overlay("hunt"),bg=ACCENT_2,fg="white",relief="flat",padx=14,pady=8).pack(side="left")
        tk.Button(row,text="Toggle Bingo Card",command=lambda:app.toggle_overlay("bingo"),bg=ACCENT_2,fg="white",relief="flat",padx=14,pady=8).pack(side="left",padx=8)
        tk.Button(row,text="Refresh Overlays",command=app.refresh_overlays,bg=PANEL_2,fg=TEXT,relief="flat",padx=14,pady=8).pack(side="left")

        settings=tk.Frame(self,bg=PANEL); settings.pack(fill="x",padx=28,pady=(0,12))
        tk.Label(settings,text="Appearance",bg=PANEL,fg=TEXT,font=("Segoe UI Semibold",14)).pack(anchor="w",padx=16,pady=(14,5))
        self.opacity=tk.DoubleVar(value=float(app.profile.setdefault("overlay_settings",{}).get("opacity",0.94)))
        tk.Label(settings,text="Opacity",bg=PANEL,fg=MUTED,font=("Segoe UI",9)).pack(anchor="w",padx=16)
        scale=tk.Scale(settings,from_=0.55,to=1.0,resolution=.05,orient="horizontal",variable=self.opacity,command=self.change_opacity,bg=PANEL,fg=TEXT,troughcolor=PANEL_2,highlightthickness=0,length=360)
        scale.pack(anchor="w",padx=12,pady=(0,10))
        tk.Label(settings,text="Tip: unlock an overlay to drag it by its header or resize it from the lower-right corner. Lock it when you're happy with placement.",bg=PANEL,fg=MUTED,font=("Segoe UI",8),wraplength=800,justify="left").pack(anchor="w",padx=16,pady=(0,14))

    def change_opacity(self,value):
        self.app.profile.setdefault("overlay_settings",{})["opacity"]=float(value)
        save_profile(self.app.profile)
        for overlay in self.app.overlays.values():
            try:overlay.attributes("-alpha",float(value))
            except Exception:pass

class ToolsPage(Page):
    title = "Tools"
    subtitle = "Small utilities that are genuinely useful during Cobblemon play."

    def __init__(self, master, app):
        super().__init__(master, app)
        self.header()

        typebox = tk.Frame(self, bg=PANEL)
        typebox.pack(fill="x", padx=28, pady=(0, 12))

        tk.Label(
            typebox, text="Type Matchup Calculator",
            bg=PANEL, fg=TEXT, font=("Segoe UI Semibold", 14)
        ).pack(anchor="w", padx=16, pady=(14, 4))

        tk.Label(
            typebox,
            text="Pick one or two defensive types to instantly see weaknesses, resistances, and immunities.",
            bg=PANEL, fg=MUTED, font=("Segoe UI", 9)
        ).pack(anchor="w", padx=16, pady=(0, 10))

        row = tk.Frame(typebox, bg=PANEL)
        row.pack(fill="x", padx=16)

        self.t1 = tk.StringVar(value="Fire")
        self.t2 = tk.StringVar(value="")
        options = [""] + list(TYPE_EFFECTIVENESS.keys())

        for var in (self.t1, self.t2):
            menu = tk.OptionMenu(row, var, *options)
            menu.config(
                bg=PANEL_2, fg=TEXT,
                activebackground=PANEL_2, activeforeground=TEXT,
                relief="flat", highlightthickness=0, width=16
            )
            menu["menu"].config(bg=PANEL_2, fg=TEXT)
            menu.pack(side="left", padx=(0, 8))

        tk.Button(
            row, text="Calculate", command=self.type_calc,
            bg=ACCENT_2, fg="white", relief="flat",
            padx=14, pady=7
        ).pack(side="left")

        self.type_result = tk.Label(
            typebox, text="", bg=PANEL, fg=TEXT,
            font=("Segoe UI", 9),
            wraplength=860, justify="left"
        )
        self.type_result.pack(anchor="w", padx=16, pady=(12, 14))

        snackbox = tk.Frame(self, bg=PANEL)
        snackbox.pack(fill="x", padx=28, pady=(0, 12))

        tk.Label(
            snackbox, text="Poké Snack Target Helper",
            bg=PANEL, fg=TEXT, font=("Segoe UI Semibold", 14)
        ).pack(anchor="w", padx=16, pady=(14, 4))

        tk.Label(
            snackbox,
            text="Choose a Pokémon to see its best target-specific Poké Snack seasonings without opening Spawn Finder.",
            bg=PANEL, fg=MUTED, font=("Segoe UI", 9)
        ).pack(anchor="w", padx=16, pady=(0, 10))

        snackrow = tk.Frame(snackbox, bg=PANEL)
        snackrow.pack(fill="x", padx=16)

        self.snack_pokemon = tk.StringVar()
        tk.Entry(
            snackrow,
            textvariable=self.snack_pokemon,
            state="readonly",
            readonlybackground=PANEL_2,
            fg=TEXT,
            relief="flat",
            font=("Segoe UI", 10)
        ).pack(side="left", fill="x", expand=True, ipady=8)

        tk.Button(
            snackrow,
            text="Choose Pokémon",
            command=self.choose_snack_pokemon,
            bg=PANEL_2,
            fg=TEXT,
            relief="flat",
            padx=12,
            pady=8
        ).pack(side="left", padx=(8, 0))

        self.snack_result = tk.Label(
            snackbox, text="", bg=PANEL, fg=TEXT,
            font=("Segoe UI", 9),
            wraplength=860, justify="left"
        )
        self.snack_result.pack(anchor="w", padx=16, pady=(12, 14))

        teambox = tk.Frame(self, bg=PANEL)
        teambox.pack(fill="x", padx=28, pady=(0, 28))

        tk.Label(
            teambox, text="Competitive Team Analysis",
            bg=PANEL, fg=TEXT, font=("Segoe UI Semibold", 14)
        ).pack(anchor="w", padx=16, pady=(14, 4))

        tk.Label(
            teambox,
            text="The serious competitive tools live in Teams. Open your saved teams for weakness, coverage, utility, STAB, role, and matchup analysis.",
            bg=PANEL, fg=MUTED, font=("Segoe UI", 9),
            wraplength=860, justify="left"
        ).pack(anchor="w", padx=16, pady=(0, 10))

        tk.Button(
            teambox, text="Open Teams",
            command=lambda: self.app.show_page("Teams"),
            bg=ACCENT_2, fg="white", relief="flat",
            padx=14, pady=8
        ).pack(anchor="w", padx=16, pady=(0, 14))

        self.type_calc()

    def type_calc(self):
        selected = [x for x in (self.t1.get(), self.t2.get()) if x]
        profile = type_matchup_for_types(selected)

        weak = ", ".join(f"{t} ×{m:g}" for t, m in profile["weak"]) or "None"
        resist = ", ".join(f"{t} ×{m:g}" for t, m in profile["resist"]) or "None"
        immune = ", ".join(profile["immune"]) or "None"

        self.type_result.config(
            text=f"Weak to: {weak}\nResists: {resist}\nImmune to: {immune}"
        )

    def choose_snack_pokemon(self):
        PokemonPicker(
            self.app,
            self.app.pokedex,
            "Choose Pokémon",
            self.snack_pokemon.get(),
            self.set_snack_pokemon
        )

    def set_snack_pokemon(self, pokemon):
        self.snack_pokemon.set(pokemon)
        species = species_by_name(self.app.pokedex, pokemon)
        snack = pokesnack_recommendation(species)

        combo = " + ".join(x[0] for x in snack.get("combo", [])) or "No recommendation"
        targeting = "   •   ".join(
            f"{berry}: {effect}" for berry, effect in snack.get("targeting", [])
        ) or "No type/Egg-Group targeting seasoning available."

        self.snack_result.config(
            text=f"Suggested seasoning slots: {combo}\n{targeting}"
        )



class CobblemonCompanion(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(f"{APP_NAME} v{APP_VERSION}")
        self.geometry("1180x760")
        self.minsize(980, 650)
        self.configure(bg=BG)

        # Global search is available anywhere in the app.
        self.bind_all("<Control-k>", lambda e: GlobalSearchWindow(self))
        self.bind_all("<Control-K>", lambda e: GlobalSearchWindow(self))
        self.bind_all("<Control-Shift-o>", lambda e: self.show_page("Overlays"))
        self.bind_all("<Control-Shift-O>", lambda e: self.show_page("Overlays"))
        self.bind_all("<Escape>", lambda e: self.go_back() if getattr(self, "_embedded_view", None) is not None else None)

        # Global mouse-wheel support. Route the wheel to the scrollable widget
        # under the pointer so users do not need to drag scrollbars manually.
        self.bind_all("<MouseWheel>", self._global_mousewheel, add="+")
        self.bind_all("<Shift-MouseWheel>", self._global_shift_mousewheel, add="+")
        self.bind_all("<Button-4>", self._global_mousewheel_linux, add="+")
        self.bind_all("<Button-5>", self._global_mousewheel_linux, add="+")

        self.profile = load_profile()
        self.overlays = {}
        self.pokedex = load_dex()
        self.dex_meta = load_dex_meta()
        self.spawns = load_spawn_data()
        self.item_index = load_item_index()
        self._reference_indexes_ready = False
        self._move_index = {}
        self._ability_index = {}

        # Older Companion caches were created in stages:
        # - pre-V0.7.2 caches may lack move lists
        # - pre-V0.9.1 caches may already have moves but still lack evolutions
        # Enrich whenever either dataset is missing.
        remembered_species_jar = self.dex_meta.get("source_jar")
        needs_move_enrichment = not dex_has_move_data(self.pokedex)
        needs_evolution_enrichment = not dex_has_evolution_data(self.pokedex)
        if (
            self.dex_meta.get("species_count")
            and (needs_move_enrichment or needs_evolution_enrichment)
            and remembered_species_jar
            and Path(remembered_species_jar).exists()
        ):
            try:
                self.pokedex, enriched_count = enrich_cached_species_from_jar(
                    self.pokedex, remembered_species_jar
                )
                if enriched_count:
                    self.dex_meta["species_data_enriched"] = True
                    self.dex_meta["enriched_species_count"] = enriched_count
                    self.dex_meta["move_data_ready"] = dex_has_move_data(self.pokedex)
                    self.dex_meta["evolution_data_ready"] = dex_has_evolution_data(self.pokedex)
                    DEX_META_FILE.write_text(
                        json.dumps(self.dex_meta, indent=2),
                        encoding="utf-8"
                    )
            except Exception:
                pass

        # V0.2 users may already have a valid full Dex cache but no spawn cache.
        # Refresh ONLY spawns from the remembered JAR instead of forcing a Dex re-import.
        remembered_jar = self.dex_meta.get("source_jar")
        if self.dex_meta.get("species_count") and not self.spawns and remembered_jar and Path(remembered_jar).exists():
            try:
                self.spawns = refresh_spawn_cache_from_jar(remembered_jar)
                self.dex_meta = load_dex_meta()
            except Exception:
                pass

        # On first launch, quietly try common Minecraft/modpack locations.
        if not self.dex_meta.get("species_count"):
            for jar in candidate_cobblemon_jars():
                try:
                    species = import_species_from_cobblemon_jar(jar)
                    save_dex(species, jar)
                    self.pokedex = species
                    self.dex_meta = load_dex_meta()
                    self.spawns = load_spawn_data()
                    break
                except Exception:
                    continue

        sidebar = tk.Frame(self, bg=PANEL, width=225)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)
        self.sidebar = sidebar
        self.nav_buttons = {}

        self.logo_image = None
        try:
            self.logo_image = tk.PhotoImage(file=resource_path("cobblemon_companion_logo.png"))
            tk.Label(sidebar,image=self.logo_image,bg=PANEL,bd=0).pack(anchor="center",padx=8,pady=(8,2))
        except Exception:
            tk.Label(sidebar,text="COBBLEMON\\nCOMPANION",bg=PANEL,fg=TEXT,font=("Segoe UI Black",14)).pack(pady=(12,2))
        tk.Label(sidebar,text=f"v{APP_VERSION}",bg=PANEL,fg=MUTED,font=("Segoe UI",7)).pack(pady=(0,5))

        self.content = tk.Frame(self, bg=BG)
        self.content.pack(side="left", fill="both", expand=True)
        self._nav_stack = []
        self._embedded_view = None
        self._current_page_name = None

        self.pages = {
            "Home": HomePage(self.content, self), "Pokédex": PokedexPage(self.content, self),
            "Bingo": BingoPage(self.content, self), "Hunts": HuntsPage(self.content, self),
            "Collection": CollectionPage(self.content, self), "Teams": TeamBuilderPage(self.content, self),
            "Breeding": BreedingPlannerPage(self.content, self), "Spawn Finder": SpawnFinderPage(self.content, self),
            "Database": DatabasePage(self.content, self), "Overlays": OverlayManagerPage(self.content, self),
            "Tools": ToolsPage(self.content, self), "Settings": SettingsPage(self.content, self),
        }

        tk.Button(sidebar,text="⌕   Search Companion",command=lambda:GlobalSearchWindow(self),
            bg=PANEL_2,fg=TEXT,activebackground="#263445",activeforeground=TEXT,relief="flat",bd=0,
            anchor="w",font=("Segoe UI Semibold",9),padx=12,pady=7,cursor="hand2").pack(fill="x",padx=10,pady=(2,5))

        nav_area=tk.Frame(sidebar,bg=PANEL)
        nav_area.pack(fill="both",expand=True,padx=7)
        sections=[
            ("HOME",[("Home","⌂")]),
            ("POKÉMON",[("Pokédex","◉"),("Spawn Finder","⌖"),("Collection","▦")]),
            ("PROGRESS",[("Hunts","◎"),("Bingo","▦")]),
            ("COMPETITIVE",[("Teams","⚔"),("Breeding","◇")]),
            ("REFERENCE",[("Database","▤"),("Tools","⚙")]),
            ("OVERLAY",[("Overlays","▣")]),
        ]
        for section,items in sections:
            tk.Label(nav_area,text=section,bg=PANEL,fg="#73839a",font=("Segoe UI Semibold",7),anchor="w").pack(fill="x",padx=10,pady=(4,1))
            for label,icon in items:
                row=tk.Frame(nav_area,bg=PANEL,height=27); row.pack(fill="x"); row.pack_propagate(False)
                indicator=tk.Frame(row,bg=PANEL,width=3); indicator.pack(side="left",fill="y")
                btn=tk.Button(row,text=f"{icon}   {label}",command=lambda p=label:self.show_page(p),
                    bg=PANEL,fg=MUTED,activebackground="#263445",activeforeground=TEXT,relief="flat",bd=0,
                    anchor="w",font=("Segoe UI",8),padx=9,cursor="hand2")
                btn.pack(side="left",fill="both",expand=True)
                self.nav_buttons[label]=(row,indicator,btn)

        settings_row=tk.Frame(sidebar,bg=PANEL,height=29)
        settings_row.pack(fill="x",side="bottom",padx=7,pady=(0,5)); settings_row.pack_propagate(False)
        si=tk.Frame(settings_row,bg=PANEL,width=3); si.pack(side="left",fill="y")
        sb=tk.Button(settings_row,text="⚙   Settings",command=lambda:self.show_page("Settings"),
            bg=PANEL,fg=MUTED,activebackground="#263445",activeforeground=TEXT,relief="flat",bd=0,
            anchor="w",font=("Segoe UI",8),padx=9,cursor="hand2")
        sb.pack(side="left",fill="both",expand=True); self.nav_buttons["Settings"]=(settings_row,si,sb)

        support=tk.Frame(sidebar,bg="#18202b",highlightthickness=1,highlightbackground="#2a3747")
        support.pack(fill="x",side="bottom",padx=10,pady=(2,5))
        tk.Label(support,text="Enjoying Companion?",bg="#18202b",fg=TEXT,font=("Segoe UI Semibold",8)).pack(anchor="w",padx=9,pady=(7,0))
        tk.Label(support,text="Help support development ♥",bg="#18202b",fg=MUTED,font=("Segoe UI",7)).pack(anchor="w",padx=9,pady=(0,5))
        tk.Button(support,text="☕  Buy Us a Coffee",command=self.open_support_page,
            bg="#d95d5d",fg="white",activebackground="#e66a6a",activeforeground="white",
            relief="flat",bd=0,font=("Segoe UI Semibold",8),pady=6,cursor="hand2").pack(fill="x",padx=7,pady=(0,7))

        self.current = None
        self.show_page("Home")
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        # Build the full Cobblemon item index after the window is already visible.
        # This prevents JAR scanning from delaying app startup.
        if not self.item_index:
            self.after(250, self._start_item_index_refresh)

        # V1.2.3 fixes modern species files that omit the implemented flag.
        # Existing installs transparently rebuild from the remembered Cobblemon JAR.
        if int(self.dex_meta.get("species_parser_version", 0) or 0) < SPECIES_PARSER_VERSION:
            self.after(350, self._start_species_parser_upgrade)

    def _scrollable_under_pointer(self):
        try:
            widget = self.winfo_containing(self.winfo_pointerx(), self.winfo_pointery())
        except Exception:
            return None

        while widget is not None:
            if isinstance(widget, (tk.Canvas, tk.Listbox, tk.Text)):
                return widget
            try:
                parent_name = widget.winfo_parent()
                if not parent_name:
                    break
                widget = widget._nametowidget(parent_name)
            except Exception:
                break
        return None

    def _global_mousewheel(self, event):
        widget = self._scrollable_under_pointer()
        if not widget:
            return
        try:
            units = -1 if event.delta > 0 else 1
            # Windows often reports multiples of 120.
            if abs(event.delta) >= 120:
                units = int(-event.delta / 120)
            widget.yview_scroll(units * 3, "units")
            return "break"
        except Exception:
            return

    def _global_shift_mousewheel(self, event):
        widget = self._scrollable_under_pointer()
        if not widget:
            return
        try:
            units = -1 if event.delta > 0 else 1
            if abs(event.delta) >= 120:
                units = int(-event.delta / 120)
            widget.xview_scroll(units * 3, "units")
            return "break"
        except Exception:
            return

    def _global_mousewheel_linux(self, event):
        widget = self._scrollable_under_pointer()
        if not widget:
            return
        try:
            units = -3 if event.num == 4 else 3
            widget.yview_scroll(units, "units")
            return "break"
        except Exception:
            return

    def _start_species_parser_upgrade(self):
        jar = self.dex_meta.get("source_jar")
        if not jar or not Path(jar).exists():
            return

        # Avoid starting twice if multiple refresh paths fire.
        if getattr(self, "_species_upgrade_running", False):
            return
        self._species_upgrade_running = True

        def worker():
            try:
                species = import_species_from_cobblemon_jar(jar)

                # Only replace the cache if the parser produced valid data.
                if species:
                    save_dex(species, jar)

                    def done():
                        try:
                            self.pokedex = species
                            self.dex_meta = load_dex_meta()
                            self.spawns = load_spawn_data()
                            self._reference_indexes_ready = False
                            self._move_index = {}
                            self._ability_index = {}
                            self.refresh_data_pages()
                        finally:
                            self._species_upgrade_running = False

                    self.after(0, done)
                else:
                    self._species_upgrade_running = False
            except Exception:
                self._species_upgrade_running = False

        threading.Thread(target=worker, daemon=True).start()

    def _start_item_index_refresh(self):
        jar = self.dex_meta.get("source_jar")
        if not jar or not Path(jar).exists():
            return

        def worker():
            try:
                items = import_items_from_cobblemon_jar(jar)
                if items:
                    save_item_index(items)
                    def done():
                        self.item_index = items
                        page = self.pages.get("Database") if getattr(self, "pages", None) else None
                        if page and hasattr(page, "items_refreshed"):
                            page.items_refreshed()
                    self.after(0, done)
            except Exception:
                pass

        threading.Thread(target=worker, daemon=True).start()

    def save(self):
        save_profile(self.profile)
        pages = getattr(self, "pages", None)
        if not pages:
            return
        home = pages.get("Home")
        if home and hasattr(home, "refresh"):
            home.refresh()
        self.refresh_overlays()

    def _hide_current_content(self):
        if self._embedded_view is not None:
            try:
                self._embedded_view.pack_forget()
            except Exception:
                pass
        elif self.current:
            try:
                self.current.pack_forget()
            except Exception:
                pass

    def open_support_page(self):
        try:
            webbrowser.open("https://ko-fi.com/broadigy", new=2)
        except Exception as exc:
            messagebox.showerror("Could not open browser", f"Companion could not open the support page.\\n\\n{exc}")

    def _update_sidebar_selection(self, page_name):
        for label,(row,indicator,btn) in getattr(self,"nav_buttons",{}).items():
            active=(label==page_name)
            bg="#263445" if active else PANEL
            row.config(bg=bg)
            indicator.config(bg=ACCENT_2 if active else PANEL)
            btn.config(bg=bg,fg=TEXT if active else MUTED,
                font=("Segoe UI Semibold",8) if active else ("Segoe UI",8))

    def show_page(self, name, clear_history=True):
        self._hide_current_content()

        # Sidebar navigation starts a new branch, just like clicking a top-level
        # section in a browser/app shell.
        if clear_history:
            self._nav_stack.clear()
            if self._embedded_view is not None:
                try:self._embedded_view.destroy()
                except Exception:pass
                self._embedded_view = None

        page = self.pages[name]
        self.current = page
        self._current_page_name = name
        if hasattr(page, "refresh"):
            page.refresh()
        page.pack(fill="both", expand=True)
        self._update_sidebar_selection(name)

    def push_embedded_view(self, factory, title=""):
        # Remember whatever is visible right now.
        if self._embedded_view is not None:
            self._nav_stack.append(("embedded", self._embedded_view))
            try:self._embedded_view.pack_forget()
            except Exception:pass
        else:
            self._nav_stack.append(("page", self._current_page_name))
            if self.current:
                try:self.current.pack_forget()
                except Exception:pass

        view = factory(self.content)
        self._embedded_view = view
        self.current = None
        view.pack(fill="both", expand=True)
        return view

    def go_back(self):
        if not self._nav_stack:
            self.show_page("Home")
            return

        if self._embedded_view is not None:
            try:self._embedded_view.destroy()
            except Exception:pass
            self._embedded_view = None

        kind, target = self._nav_stack.pop()

        if kind == "page":
            page_name = target or "Home"
            page = self.pages.get(page_name, self.pages["Home"])
            self.current = page
            self._current_page_name = page_name
            if hasattr(page, "refresh"):
                page.refresh()
            page.pack(fill="both", expand=True)
        else:
            self._embedded_view = target
            self.current = None
            try:
                target.pack(fill="both", expand=True)
            except Exception:
                # If an older transient view was destroyed, safely fall back.
                self.show_page("Teams")

    def open_competitive_analysis(self, team):
        return self.push_embedded_view(
            lambda master: EmbeddedCompetitiveAnalysisPage(master, self, team),
            "Competitive Analysis"
        )

    def open_threat_analyzer(self, team):
        return self.push_embedded_view(
            lambda master: EmbeddedThreatAnalyzerPage(master, self, team),
            "Threat Analyzer"
        )

    def open_team_advisor(self, team):
        return self.push_embedded_view(
            lambda master: EmbeddedTeamAdvisorPage(master, self, team),
            "Team Advisor"
        )

    def open_pokemon_detail(self, pokemon_name):
        return self.push_embedded_view(
            lambda master: EmbeddedPokemonDetailPage(master, self, pokemon_name),
            f"Pokédex — {pokemon_name}"
        )

    def open_reference_detail(self, kind, name):
        return self.push_embedded_view(
            lambda master: EmbeddedReferenceDetailPage(master, self, kind, name),
            f"{kind} — {name}"
        )



    def toggle_overlay(self, kind):
        existing=self.overlays.get(kind)
        if existing:
            try:
                if existing.winfo_exists():
                    self.close_overlay(kind); return
            except Exception:pass
        self.overlays[kind]=CompanionOverlay(self,kind)

    def close_overlay(self, kind):
        overlay=self.overlays.pop(kind,None)
        if overlay:
            try:overlay._save_geometry()
            except Exception:pass
            try:overlay.destroy()
            except Exception:pass

    def refresh_overlays(self):
        for overlay in list(self.overlays.values()):
            try:
                if overlay.winfo_exists():overlay.refresh()
            except Exception:pass

    def refresh_data_pages(self):
        for name in ("Pokédex", "Spawn Finder", "Home", "Settings"):
            page = self.pages.get(name)
            if page and hasattr(page, "refresh"):
                page.refresh()

    def on_close(self):
        for kind in list(getattr(self,"overlays",{}).keys()):
            self.close_overlay(kind)
        self.save()
        self.destroy()

if __name__ == "__main__":
    try:
        app = CobblemonCompanion()
        app.mainloop()
    except Exception:
        error_text = traceback.format_exc()
        try:
            crash_file = user_data_dir() / "crash.log"
            crash_file.write_text(error_text, encoding="utf-8")
        except Exception:
            pass
        try:
            import ctypes
            ctypes.windll.user32.MessageBoxW(
                0,
                error_text[-3500:],
                "Cobblemon Companion - Startup Error",
                0x10
            )
        except Exception:
            print(error_text)
        raise
