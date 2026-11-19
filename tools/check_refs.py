#!/usr/bin/env python3
"""Check ERP OBE XML IDs, references, load order, and retired demo markers."""

import ast
import re
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path


MODULE_DIR = Path(__file__).resolve().parents[1]
MARKER_DIRS = ("data", "migrations", "docs", "controllers")
STALE_MARKERS = {
    "informatika": re.compile(r"informatika", re.IGNORECASE),
    "_if_": re.compile(r"_if_", re.IGNORECASE),
    "prodi_in": re.compile(r"\bprodi_in\b", re.IGNORECASE),
}
REF_CALL = re.compile(r"""ref\(\s*['"]([^'"]+)['"]\s*\)""")


def external_id(value):
    return value if "." in value else f"erpobe.{value}"


def manifest_files():
    manifest = ast.literal_eval((MODULE_DIR / "__manifest__.py").read_text(encoding="utf-8"))
    return [MODULE_DIR / name for name in manifest.get("data", [])]


def check_xml_and_refs():
    loaded_files = manifest_files()
    load_order = {path.resolve(): index for index, path in enumerate(loaded_files)}
    xml_files = sorted(MODULE_DIR.rglob("*.xml"))
    definitions = defaultdict(list)
    references = []
    problems = []

    for path in xml_files:
        try:
            root = ET.parse(path).getroot()
        except ET.ParseError as error:
            problems.append(f"Malformed XML: {path.relative_to(MODULE_DIR)}: {error}")
            continue

        for node in root.iter():
            record_id = node.get("id")
            if record_id:
                definitions[external_id(record_id)].append(path.resolve())

            for name, value in node.attrib.items():
                if name == "ref":
                    references.append((external_id(value), path.resolve()))
                references.extend(
                    (external_id(match.group(1)), path.resolve())
                    for match in REF_CALL.finditer(value)
                )

    for record_id, paths in sorted(definitions.items()):
        if len(paths) > 1:
            locations = ", ".join(str(path.relative_to(MODULE_DIR)) for path in paths)
            problems.append(f"Duplicate ID {record_id}: {locations}")

    for record_id, source in references:
        if not record_id.startswith("erpobe."):
            continue
        if record_id.startswith("erpobe.model_"):
            continue
        targets = definitions.get(record_id)
        if not targets:
            problems.append(
                f"Undefined reference {record_id} in {source.relative_to(MODULE_DIR)}"
            )
            continue
        source_order = load_order.get(source)
        target_order = load_order.get(targets[0])
        if (
            source_order is not None
            and target_order is not None
            and target_order > source_order
        ):
            problems.append(
                f"Late reference {record_id}: "
                f"{source.relative_to(MODULE_DIR)} loads before "
                f"{targets[0].relative_to(MODULE_DIR)}"
            )

    return problems, len(xml_files), len(definitions), len(references)


def check_stale_markers():
    findings = []
    for directory in MARKER_DIRS:
        root = MODULE_DIR / directory
        if not root.exists():
            continue
        for path in sorted(root.rglob("*")):
            if not path.is_file() or path.suffix in {".pyc", ".pyo"}:
                continue
            try:
                content = path.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue
            for marker, pattern in STALE_MARKERS.items():
                if pattern.search(content):
                    findings.append(
                        f"Retired marker {marker} in {path.relative_to(MODULE_DIR)}"
                    )
    return findings


def main():
    problems, xml_count, id_count, ref_count = check_xml_and_refs()
    problems.extend(check_stale_markers())
    print(
        f"Scanned {xml_count} XML files, {id_count} IDs, "
        f"and {ref_count} references."
    )
    if problems:
        for problem in problems:
            print(f"ERROR: {problem}")
        print(f"PROBLEMS: {len(problems)}")
        return 1
    print("Undefined references: 0")
    print("Duplicate IDs: 0")
    print("Late references: 0")
    print("Retired markers: 0")
    print("PROBLEMS: 0")
    return 0


if __name__ == "__main__":
    sys.exit(main())
