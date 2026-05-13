#!/usr/bin/env python3
"""
board_validator_basic.py
AMD/Xilinx Board Store — Basic Pre-PR Validation Script

Validates board file structure and content for pull requests to XilinxBoardStore.

Checks performed:
  • Required files present  (board.xml, part0_pins.xml, preset.xml)
  • XML files are well-formed
  • JSON files are valid
  • board.xml required attributes and elements
  • part0_pins.xml required attributes per pin
  • preset.xml required attributes
  • xitem.json required fields and cross-check against board.xml version
  • Cross-check: preset_proc names consistent between board.xml and preset.xml

Usage (CI – changed files from a text file):
    python board_validator_basic.py --changed-files /tmp/changed.txt --repo-root .

Usage (explicit directories):
    python board_validator_basic.py --board-dirs boards/Xilinx/vck190/production/3.3

Usage (validate all boards):
    python board_validator_basic.py --all --repo-root .
"""

import os
import sys
import json
import argparse
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Optional

# ─── Colour helpers ────────────────────────────────────────────────────────────
_USE_COLOUR = sys.stdout.isatty()


def _c(code: str, text: str) -> str:
    return f"\033[{code}m{text}\033[0m" if _USE_COLOUR else text


def RED(t: str) -> str:    return _c("31;1", t)
def GREEN(t: str) -> str:  return _c("32;1", t)
def YELLOW(t: str) -> str: return _c("33;1", t)
def BOLD(t: str) -> str:   return _c("1",    t)


# ─── Validation result container ───────────────────────────────────────────────

class ValidationResult:
    def __init__(self, board_dir: str):
        self.board_dir = board_dir
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.passed_checks: List[str] = []

    def error(self, msg: str):
        self.errors.append(msg)

    def warn(self, msg: str):
        self.warnings.append(msg)

    def ok(self, msg: str):
        self.passed_checks.append(msg)

    @property
    def passed(self) -> bool:
        return len(self.errors) == 0


# ─── File parsers ──────────────────────────────────────────────────────────────

def parse_xml(path: Path, result: ValidationResult) -> Optional[ET.Element]:
    """Parse XML file and return root element, or None on failure."""
    try:
        tree = ET.parse(str(path))
        return tree.getroot()
    except ET.ParseError as e:
        result.error(f"{path.name}: XML parse error — {e}")
        return None
    except OSError as e:
        result.error(f"{path.name}: Cannot read file — {e}")
        return None


def parse_json(path: Path, result: ValidationResult) -> Optional[dict]:
    """Parse JSON file and return dict, or None on failure."""
    try:
        with open(str(path), "r", encoding="utf-8") as fh:
            return json.load(fh)
    except json.JSONDecodeError as e:
        result.error(
            f"{path.name}: JSON parse error at line {e.lineno}, col {e.colno} — {e.msg}"
        )
        return None
    except OSError as e:
        result.error(f"{path.name}: Cannot read file — {e}")
        return None


# ─── Per-file validators ───────────────────────────────────────────────────────

def validate_board_xml(path: Path, result: ValidationResult) -> Optional[ET.Element]:
    """Validate board.xml structure and required fields."""
    root = parse_xml(path, result)
    if root is None:
        return None

    result.ok("board.xml: Well-formed XML")

    # Root element check
    if root.tag != "board":
        result.error(
            f"board.xml: Root element must be <board>, found <{root.tag}>"
        )
        return root
    result.ok("board.xml: Root element is <board>")

    # Required attributes on <board>
    for attr in ("vendor", "name", "display_name"):
        val = root.get(attr)
        if not val:
            result.error(f"board.xml: <board> missing required attribute '{attr}'")
        else:
            result.ok(f"board.xml: <board> {attr} = \"{val}\"")

    if not root.get("schema_version"):
        result.warn("board.xml: <board> does not declare 'schema_version' attribute")

    # <file_version> element
    file_ver = root.find("file_version")
    if file_ver is None or not (file_ver.text and file_ver.text.strip()):
        result.error("board.xml: Missing or empty <file_version> element")
    else:
        result.ok(f"board.xml: <file_version> = {file_ver.text.strip()}")

    # <compatible_board_revisions>
    cbr = root.find("compatible_board_revisions")
    if cbr is None:
        result.error("board.xml: Missing <compatible_board_revisions> element")
    else:
        revisions = cbr.findall("revision")
        if not revisions:
            result.error(
                "board.xml: <compatible_board_revisions> contains no <revision> entries"
            )
        else:
            result.ok(
                f"board.xml: {len(revisions)} compatible board revision(s) declared"
            )

    # <description>
    desc = root.find("description")
    if desc is None or not (desc.text and desc.text.strip()):
        result.warn("board.xml: Missing or empty <description> element")

    # <components> — must have at least one fpga component
    components = root.find("components")
    if components is None:
        result.error("board.xml: Missing <components> element")
    else:
        fpga_comps = [
            c for c in components.findall("component")
            if c.get("type") == "fpga"
        ]
        if not fpga_comps:
            result.error(
                "board.xml: No <component type=\"fpga\"> found inside <components>"
            )
        else:
            result.ok(f"board.xml: {len(fpga_comps)} FPGA component(s) declared")
            for comp in fpga_comps:
                cname = comp.get("name", "?")
                if not comp.get("part_name"):
                    result.error(
                        f"board.xml: FPGA component '{cname}' missing 'part_name' attribute"
                    )
                if not comp.get("pin_map_file"):
                    result.warn(
                        f"board.xml: FPGA component '{cname}' missing 'pin_map_file' attribute"
                    )

    return root


def validate_part0_pins_xml(path: Path, result: ValidationResult) -> Optional[ET.Element]:
    """Validate part0_pins.xml structure and pin attributes."""
    root = parse_xml(path, result)
    if root is None:
        return None

    result.ok("part0_pins.xml: Well-formed XML")

    if root.tag != "part_info":
        result.error(
            f"part0_pins.xml: Root element must be <part_info>, found <{root.tag}>"
        )
        return root
    result.ok("part0_pins.xml: Root element is <part_info>")

    if not root.get("part_name"):
        result.error("part0_pins.xml: <part_info> missing required 'part_name' attribute")
    else:
        result.ok(f"part0_pins.xml: part_name = \"{root.get('part_name')}\"")

    # Pins may live directly under root or under a <pins> wrapper
    pins_container = root.find("pins")
    pins = pins_container.findall("pin") if pins_container is not None else root.findall("pin")

    if not pins:
        result.error("part0_pins.xml: No <pin> elements found")
    else:
        result.ok(f"part0_pins.xml: {len(pins)} pin(s) defined")
        bad_pins = []
        for pin in pins:
            for attr in ("index", "name", "loc"):
                if not pin.get(attr):
                    bad_pins.append(
                        f"pin index={pin.get('index', '?')} is missing attribute '{attr}'"
                    )
        for msg in bad_pins[:10]:
            result.error(f"part0_pins.xml: {msg}")
        if len(bad_pins) > 10:
            result.error(
                f"part0_pins.xml: … and {len(bad_pins) - 10} more pin attribute errors"
            )

    return root


def validate_preset_xml(path: Path, result: ValidationResult) -> Optional[ET.Element]:
    """Validate preset.xml structure."""
    root = parse_xml(path, result)
    if root is None:
        return None

    result.ok("preset.xml: Well-formed XML")

    if root.tag != "ip_presets":
        result.error(
            f"preset.xml: Root element must be <ip_presets>, found <{root.tag}>"
        )
        return root
    result.ok("preset.xml: Root element is <ip_presets>")

    presets = root.findall("ip_preset")
    if not presets:
        result.warn(
            "preset.xml: No <ip_preset> entries found (acceptable if board has no IP presets)"
        )
    else:
        result.ok(f"preset.xml: {len(presets)} preset entry/entries defined")
        for p in presets:
            if not p.get("preset_proc_name"):
                result.error(
                    "preset.xml: An <ip_preset> element is missing 'preset_proc_name' attribute"
                )

    return root


def validate_xitem_json(
    path: Path,
    result: ValidationResult,
    board_xml_root: Optional[ET.Element] = None,
) -> Optional[dict]:
    """Validate xitem.json fields and cross-check version against board.xml."""
    data = parse_json(path, result)
    if data is None:
        return None

    result.ok("xitem.json: Valid JSON")

    # Top-level version fields
    for field in ("_major", "_minor"):
        if field not in data:
            result.error(f"xitem.json: Missing top-level field '{field}'")
        else:
            result.ok(f"xitem.json: '{field}' = {data[field]}")

    # config.items[0].infra
    try:
        infra = data["config"]["items"][0]["infra"]
    except (KeyError, IndexError, TypeError):
        result.error("xitem.json: Missing required path config > items[0] > infra")
        return data

    for field in ("name", "display", "revision", "description", "company"):
        val = infra.get(field)
        if not val:
            result.error(f"xitem.json: infra.{field} is missing or empty")
        else:
            result.ok(f"xitem.json: infra.{field} = \"{val}\"")

    # Cross-check revision vs board.xml <file_version>
    if board_xml_root is not None:
        fv_elem = board_xml_root.find("file_version")
        if fv_elem is not None and fv_elem.text:
            bv = fv_elem.text.strip()
            jv = str(infra.get("revision", "")).strip()
            if bv != jv:
                result.error(
                    f"xitem.json: infra.revision \"{jv}\" does not match "
                    f"board.xml <file_version> \"{bv}\""
                )
            else:
                result.ok(
                    f"xitem.json: infra.revision matches board.xml <file_version> ({bv})"
                )

    return data


def cross_validate_preset_vs_board(
    preset_root: Optional[ET.Element],
    board_root: Optional[ET.Element],
    result: ValidationResult,
) -> None:
    """
    Verify preset_proc_name entries in preset.xml match preset_proc
    references in board.xml interface declarations.
    """
    if preset_root is None or board_root is None:
        return

    preset_names = {
        p.get("preset_proc_name")
        for p in preset_root.findall("ip_preset")
        if p.get("preset_proc_name")
    }
    board_preset_refs = {
        iface.get("preset_proc")
        for iface in board_root.iter("interface")
        if iface.get("preset_proc")
    }

    orphan = preset_names - board_preset_refs
    missing = board_preset_refs - preset_names

    if orphan:
        result.warn(
            "preset.xml: Preset(s) not referenced by any board.xml interface — "
            + ", ".join(sorted(orphan))
        )
    if missing:
        result.error(
            "board.xml: Interface preset_proc reference(s) not defined in preset.xml — "
            + ", ".join(sorted(missing))
        )
    if not orphan and not missing and (preset_names or board_preset_refs):
        result.ok(
            "Cross-check: preset_proc references are consistent between "
            "board.xml and preset.xml"
        )


# ─── Board directory validator ─────────────────────────────────────────────────

REQUIRED_FILES = ("board.xml", "part0_pins.xml", "preset.xml")


def validate_board_directory(board_dir: Path) -> ValidationResult:
    result = ValidationResult(str(board_dir))

    # 1. Required files
    for fname in REQUIRED_FILES:
        fpath = board_dir / fname
        if not fpath.exists():
            result.error(f"Missing required file: {fname}")
        else:
            result.ok(f"Required file present: {fname}")

    # 2. Optional but recommended
    if not (board_dir / "xitem.json").exists():
        result.warn(
            "xitem.json not found (recommended for Board Catalog registration)"
        )

    # 3. Validate individual files
    board_xml_root: Optional[ET.Element] = None
    preset_root: Optional[ET.Element] = None

    board_xml_path = board_dir / "board.xml"
    if board_xml_path.exists():
        board_xml_root = validate_board_xml(board_xml_path, result)

    pins_path = board_dir / "part0_pins.xml"
    if pins_path.exists():
        validate_part0_pins_xml(pins_path, result)

    preset_path = board_dir / "preset.xml"
    if preset_path.exists():
        preset_root = validate_preset_xml(preset_path, result)

    xitem_path = board_dir / "xitem.json"
    if xitem_path.exists():
        validate_xitem_json(xitem_path, result, board_xml_root)

    # 4. Cross-validation
    cross_validate_preset_vs_board(preset_root, board_xml_root, result)

    return result


# ─── Console output ────────────────────────────────────────────────────────────

def print_result(result: ValidationResult) -> None:
    print()
    print(BOLD(f"Board directory: {result.board_dir}"))
    print("─" * 70)
    for msg in result.passed_checks:
        print(f"  {GREEN('✔')} {msg}")
    for msg in result.warnings:
        print(f"  {YELLOW('⚠')} {msg}")
    for msg in result.errors:
        print(f"  {RED('✖')} {msg}")
    print()
    board_name = Path(result.board_dir).name
    if result.passed:
        print(GREEN(f"  RESULT: All checks passed for {board_name}"))
    else:
        print(RED(f"  RESULT: {len(result.errors)} error(s) found in {board_name}"))


# ─── Markdown report for PR comments ──────────────────────────────────────────

def generate_markdown_report(results: List[ValidationResult]) -> str:
    """Return a GitHub-flavoured Markdown string for posting as a PR comment."""
    lines = ["## 🔍 Board Pre-Validation Report", ""]

    all_passed = all(r.passed for r in results)

    if all_passed:
        lines += [
            "### ✅ All pre-validation checks passed before merge",
            "",
            "Every board file in this pull request passed the automated checks. "
            "A reviewer may now proceed with the technical review.",
            "",
        ]
    else:
        failed_count = sum(1 for r in results if not r.passed)
        lines += [
            f"### ❌ {failed_count} board(s) failed pre-validation",
            "",
            "Please fix the errors listed below before requesting a review.",
            "",
        ]

    for result in results:
        board_name = Path(result.board_dir).name
        status_icon = "✅" if result.passed else "❌"
        status_text = "Passed" if result.passed else "Failed"

        lines += [
            "<details>",
            f"<summary><b>{board_name}</b> &nbsp;—&nbsp; {status_icon} {status_text}</summary>",
            "",
        ]

        if result.passed_checks:
            lines.append("**Passed checks:**")
            for msg in result.passed_checks:
                lines.append(f"- ✔️ {msg}")
            lines.append("")

        if result.warnings:
            lines.append("**Warnings:**")
            for msg in result.warnings:
                lines.append(f"- ⚠️ {msg}")
            lines.append("")

        if result.errors:
            lines.append("**Errors — must be fixed before merge:**")
            for msg in result.errors:
                lines.append(f"- ❌ {msg}")
            lines.append("")

        lines += ["</details>", ""]

    lines += [
        "---",
        "*Generated by `board_validator_basic.py` — AMD/Xilinx Board Store CI*",
    ]

    return "\n".join(lines)


# ─── Helpers ───────────────────────────────────────────────────────────────────

def find_board_dirs_from_changed_files(
    changed_files: List[str], repo_root: Path
) -> List[Path]:
    """
    Given a list of changed file paths (relative to repo root), return the
    unique set of board version directories that contain those changed files.
    A board version directory is defined as the directory containing board.xml.
    """
    board_dirs: set = set()
    for fpath_str in changed_files:
        fpath = Path(fpath_str.strip())
        if not fpath.parts or fpath.parts[0] != "boards":
            continue
        # Walk upward from the changed file's parent until we find board.xml
        candidate = (repo_root / fpath.parent).resolve()
        while candidate != repo_root and str(candidate) != str(repo_root):
            if (candidate / "board.xml").exists() or (
                candidate / "part0_pins.xml"
            ).exists():
                board_dirs.add(candidate)
                break
            if candidate.parent == candidate:
                break
            candidate = candidate.parent

    return sorted(board_dirs)


# ─── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="AMD/Xilinx Board Store — board file pre-validation tool.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--board-dirs",
        nargs="+",
        metavar="DIR",
        help="One or more explicit board version directories to validate.",
    )
    group.add_argument(
        "--changed-files",
        metavar="FILE",
        help="Path to a text file listing changed files (one per line, relative to repo root).",
    )
    group.add_argument(
        "--all",
        action="store_true",
        help="Validate all board directories found under boards/ in the repo root.",
    )

    parser.add_argument(
        "--repo-root",
        metavar="DIR",
        default=".",
        help="Repository root directory (default: current directory).",
    )
    parser.add_argument(
        "--markdown-output",
        metavar="FILE",
        help="Write a Markdown report to this file (used in CI for PR comments).",
    )

    args = parser.parse_args()
    repo_root = Path(args.repo_root).resolve()
    board_dirs: List[Path] = []

    if args.board_dirs:
        for d in args.board_dirs:
            p = Path(d) if Path(d).is_absolute() else repo_root / d
            if not p.is_dir():
                print(RED(f"ERROR: Not a directory: {p}"), file=sys.stderr)
                sys.exit(2)
            board_dirs.append(p.resolve())

    elif args.changed_files:
        try:
            changed = Path(args.changed_files).read_text(encoding="utf-8").splitlines()
        except OSError as e:
            print(RED(f"ERROR: Cannot read changed-files list: {e}"), file=sys.stderr)
            sys.exit(2)
        board_dirs = find_board_dirs_from_changed_files(changed, repo_root)
        if not board_dirs:
            print(
                YELLOW(
                    "No board directories detected in the changed files. "
                    "Nothing to validate."
                )
            )
            # Write a minimal markdown report so the PR comment still appears
            if args.markdown_output:
                md = (
                    "## 🔍 Board Pre-Validation Report\n\n"
                    "> No board files (under `boards/`) were changed in this pull request.\n"
                )
                Path(args.markdown_output).write_text(md, encoding="utf-8")
            sys.exit(0)

    elif args.all:
        boards_root = repo_root / "boards"
        if not boards_root.is_dir():
            print(
                RED(f"ERROR: boards/ directory not found under {repo_root}"),
                file=sys.stderr,
            )
            sys.exit(2)
        board_dirs = sorted(p.parent for p in boards_root.rglob("board.xml"))

    if not board_dirs:
        print(YELLOW("No board directories to validate."))
        sys.exit(0)

    print(BOLD(f"\nXilinx Board Store — Pre-Validation ({len(board_dirs)} board(s))"))
    print("=" * 70)

    results: List[ValidationResult] = []
    for bd in board_dirs:
        r = validate_board_directory(bd)
        results.append(r)
        print_result(r)

    # Summary
    passed = [r for r in results if r.passed]
    failed = [r for r in results if not r.passed]

    print("=" * 70)
    print(BOLD("SUMMARY"))
    print(f"  Boards validated : {len(results)}")
    print(f"  {GREEN('Passed')}           : {len(passed)}")
    if failed:
        print(f"  {RED('Failed')}           : {len(failed)}")
        print()
        print(RED("Board(s) with errors:"))
        for r in failed:
            print(f"  • {r.board_dir}")

    # Write Markdown report if requested
    if args.markdown_output:
        md = generate_markdown_report(results)
        Path(args.markdown_output).write_text(md, encoding="utf-8")
        print(f"\nMarkdown report written to: {args.markdown_output}")

    print()
    if all(r.passed for r in results):
        print(GREEN("✅  All pre-validation checks passed before merge"))
        sys.exit(0)
    else:
        print(RED("❌  Pre-validation failed — please fix the errors above before merging"))
        sys.exit(1)


if __name__ == "__main__":
    main()
