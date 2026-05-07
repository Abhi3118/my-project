import os
import re
import xml.etree.ElementTree as ET
from collections import Counter
from datetime import datetime
import getpass
import json

# ════════════════════════════════════════════════════════════════════════════
# CONFIG  ← edit these to match your project
# ════════════════════════════════════════════════════════════════════════════
PROJECT_NAME    = "MarketplaceOrderManagement_V2_0"
REVIEWER_NAME   = getpass.getuser()          # or hardcode: "Abhishek Reddy"
REVIEW_FOCUS    = "General"
TIME_SPENT      = "4 hours"
REVIEW_VERSION  = "0.1"
REVIEW_DATE     = datetime.today()

# Output path
OUTPUT_DIR  = "."  # Current directory
OUTPUT_FILE = f"{PROJECT_NAME}_Code_Review_Log.json"

folders_to_check = [
    os.path.join(PROJECT_NAME, "proxyservices"),
    os.path.join(PROJECT_NAME, "transformations"),
]


# ════════════════════════════════════════════════════════════════════════════
# ISSUE COLLECTOR
# ════════════════════════════════════════════════════════════════════════════

_findings: list[dict] = []

def _add(location: str, description: str,
         defect_type: str, severity: str, kind: str = "Suggestion"):
    _findings.append({
        "sl":          len(_findings) + 1,
        "level":       "Peer",
        "kind":        kind,
        "location":    location,
        "description": description,
        "owner":       "",
        "defect_type": defect_type,
        "severity":    severity,
        "accepted":    "",
        "resolution":  "",
        "closed":      "",
        "remarks":     "",
    })


# ════════════════════════════════════════════════════════════════════════════
# CHECK FUNCTIONS  (each logs to console AND calls _add for JSON export)
# ════════════════════════════════════════════════════════════════════════════

def check_description_tag(file_path):
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        found = any(
            (e.tag.split("}")[1] if "}" in e.tag else e.tag) == "description"
            for e in root.iter()
        )
        if found:
            print(f"  ✅ <description> present")
        else:
            print(f"  ❌ <description> MISSING")
            _add(file_path,
                 "Missing <description> tag in proxy/bix file.",
                 "Comments", "Minor")
    except ET.ParseError:
        print(f"  ⚠️  Non-XML / invalid file — skipped")
    except FileNotFoundError:
        print(f"  ❌ File not found")
    except Exception as e:
        print(f"  ❌ Error: {e}")


def find_comment_lines(file_path):
    lines = []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            for idx, line in enumerate(f, 1):
                if "//" in line and "http://" not in line and "https://" not in line:
                    lines.append(idx)
        if lines:
            print(f"  ⚠️  Inline '//' on lines: {lines}")
            _add(file_path,
                 f"Inline '//' comment(s) found on lines: {lines}. "
                 "Remove or replace with proper XML comments.",
                 "Comments", "Minor")
        else:
            print(f"  ✅ No inline comment lines")
    except Exception as e:
        print(f"  ❌ Error: {e}")


def find_disabled_true_lines(file_path):
    lines = []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            for idx, line in enumerate(f, 1):
                if re.search(r"<(?:[^>]*:)?disabled>true</(?:[^>]*:)?disabled>", line):
                    lines.append(idx)
        if lines:
            print(f"  🛑 Disabled elements on lines: {lines}")
            _add(file_path,
                 f"<disabled>true</disabled> found on lines: {lines}. "
                 "Remove unused/disabled steps before release.",
                 "Formatting", "Medium", "Defect")
        else:
            print(f"  ✅ No disabled elements")
    except Exception as e:
        print(f"  ❌ Error: {e}")


def find_log_tags(file_path):
    log_pat = r"<[^>]*:log>.*?</[^>]*:log>"
    msg_pat = r"<[^>]*:message>(.*?)</[^>]*:message>"
    try:
        content = open(file_path, "r", encoding="utf-8").read()
        matches = re.findall(log_pat, content, re.DOTALL)
        if matches:
            print(f"  ✅ <log> tag(s) found: {len(matches)}")
            for m in matches:
                msg = re.search(msg_pat, m)
                print(f"     - {msg.group(1).strip() if msg else '(no <message>)'}")
        else:
            print(f"  ❌ No <log> tag found")
            _add(file_path,
                 "No <log> tag found in pipeline. Add logging for traceability.",
                 "Exception/Error Handling", "Minor")
    except Exception as e:
        print(f"  ❌ Error: {e}")


def find_json_xml_conversions(file_path):
    j2x, x2j = [], []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            for idx, line in enumerate(f, 1):
                if "jsonToXml" in line: j2x.append(idx)
                if "xmlToJson" in line: x2j.append(idx)
        if j2x or x2j:
            print(f"  🔍 Conversion keywords found:")
            if j2x: print(f"     - jsonToXml on lines: {j2x}")
            if x2j: print(f"     - xmlToJson on lines: {x2j}")
            _add(file_path,
                 f"JSON↔XML conversion found (jsonToXml:{j2x}, xmlToJson:{x2j}). "
                 "Verify necessity and ensure proper namespace handling.",
                 "Data", "Minor")
        else:
            print(f"  ✅ No JSON↔XML conversions")
    except Exception as e:
        print(f"  ❌ Error: {e}")


def search_user_input(file_path, user_input):
    try:
        hits = [i for i, l in enumerate(
            open(file_path, "r", encoding="utf-8"), 1)
            if user_input.strip().lower() in l.lower()]
        if hits:
            print(f"  🧑‍💻 '{user_input}' on line(s): {hits}")
        else:
            print(f"  🔍 '{user_input}' NOT found")
    except Exception as e:
        print(f"  ❌ Error: {e}")


def search_in_config_files(file_path, user_input):
    try:
        content = open(file_path, "r", encoding="utf-8").read()
        if user_input.strip().lower() in content.lower():
            print(f"  ✅ '{user_input}' found")
        else:
            print(f"  🔍 '{user_input}' NOT found")
    except Exception as e:
        print(f"  ❌ Error: {e}")


def find_unique_varname(file_path):
    try:
        content = open(file_path, "r", encoding="utf-8").read()
        varnames = re.findall(r'varName="([^"]+)"', content)

        def count_occ(var, text):
            pat = re.compile(rf"\b{re.escape(var)}\b|\${re.escape(var)}[/*]?")
            return len(pat.findall(text))

        unused = [v for v in varnames if count_occ(v, content) == 1]
        if unused:
            print(f"  ⚠️  Unreferenced varName(s): {unused}")
            _add(file_path,
                 f"varName(s) defined but never referenced: {unused}. "
                 "Remove unused variables.",
                 "Data", "Minor")
        else:
            print(f"  ✅ All varNames referenced")
    except Exception as e:
        print(f"  ❌ Error: {e}")


def find_bix_in_pipeline(file_path, bix_files):
    try:
        content = open(file_path, "r", encoding="utf-8").read()
        missing = [b for b in bix_files if b not in content]
        if missing:
            print(f"  ⚠️  Missing .bix refs: {missing}")
            _add(file_path,
                 f"Pipeline does not reference .bix file(s): {missing}.",
                 "Functional/Design Non-Conformance", "Major", "Defect")
        else:
            print(f"  ✅ All .bix files referenced")
    except Exception as e:
        print(f"  ❌ Error: {e}")


def find_missing_comments(file_path):
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        missing = []
        for elem in root.iter():
            tag = elem.tag.split("}")[1] if "}" in elem.tag else elem.tag
            if tag in ("pipeline-node", "stage", "route-node"):
                name = elem.attrib.get("name")
                if name and elem.find(".//{*}comment") is None:
                    missing.append(name)
        if missing:
            print(f"  ⚠️  Nodes/stages missing <comment>: {missing}")
            _add(file_path,
                 f"Nodes/stages missing <comment>: {missing}. "
                 "Add descriptions for all nodes and stages.",
                 "Comments", "Minor")
        else:
            print(f"  ✅ All nodes/stages have comments")
    except ET.ParseError:
        print(f"  ⚠️  Non-XML — skipped")
    except Exception as e:
        print(f"  ❌ Error: {e}")


def find_duplicate_nodes(file_path):
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        names = []
        for elem in root.iter():
            tag = elem.tag.split("}")[1] if "}" in elem.tag else elem.tag
            if tag in ("pipeline-node", "stage", "route-node"):
                n = elem.attrib.get("name")
                if n: names.append(n)
        dups = [n for n, c in Counter(names).items() if c > 1]
        if dups:
            print(f"  ❌ Duplicate node names: {dups}")
            _add(file_path,
                 f"Duplicate node/stage names found: {dups}. "
                 "Each node must have a unique name.",
                 "Logical", "Major", "Defect")
        else:
            print(f"  ✅ No duplicate node names")
    except ET.ParseError:
        print(f"  ⚠️  Non-XML — skipped")
    except Exception as e:
        print(f"  ❌ Error: {e}")


def find_duplicate_bix(bix_files_all):
    dups = {n: c for n, c in Counter(bix_files_all).items() if c > 1}
    print(f"\n{'='*60}")
    print(f"🔍 PROJECT-WIDE: Duplicate .bix Files")
    print(f"{'='*60}")
    if dups:
        for name, cnt in dups.items():
            print(f"  ❌ '{name}' appears {cnt} times")
            _add(f"[Project-wide] {name}",
                 f"Duplicate .bix filename '{name}' appears {cnt} times across folders. "
                 "Rename to avoid shadowing.",
                 "Functional/Design Non-Conformance", "Major", "Defect")
    else:
        print(f"  ✅ No duplicate .bix filenames")


def find_stage_missing_descriptions(file_path):
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        missing, empty = [], []
        for elem in root.iter():
            tag = elem.tag.split("}")[1] if "}" in elem.tag else elem.tag
            if tag == "stage":
                name = elem.attrib.get("name", "<unnamed>")
                d = elem.find(".//{*}description")
                if d is None:
                    missing.append(name)
                elif not (d.text and d.text.strip()):
                    empty.append(name)
        if missing:
            print(f"  ❌ Stages missing <description>: {missing}")
            _add(file_path,
                 f"Stages have no <description> tag: {missing}.",
                 "Comments", "Minor")
        if empty:
            print(f"  ⚠️  Stages with empty <description>: {empty}")
            _add(file_path,
                 f"Stages have empty <description>: {empty}.",
                 "Comments", "Minor")
        if not missing and not empty:
            print(f"  ✅ All stages have descriptions")
    except ET.ParseError:
        print(f"  ⚠️  Non-XML — skipped")
    except Exception as e:
        print(f"  ❌ Error: {e}")


PAIR_SUFFIXES = [("REQ","RES"), ("Request","Response"),
                 ("Input","Output"), ("Req","Res")]

def find_pipeline_pair_description_mismatch(folder):
    pipeline_files = {}
    for root_dir, _, files in os.walk(folder):
        for fn in files:
            if fn.endswith(".pipeline"):
                base = os.path.splitext(fn)[0]
                pipeline_files[base] = os.path.join(root_dir, fn)

    checked, pair_issues, unpaired = set(), [], []

    for base, path in pipeline_files.items():
        for req_s, res_s in PAIR_SUFFIXES:
            if base.endswith(f"_{req_s}"):
                partner = f"{base[:-(len(req_s)+1)]}_{res_s}"
            elif base.endswith(f"_{res_s}"):
                partner = f"{base[:-(len(res_s)+1)]}_{req_s}"
            else:
                continue

            key = tuple(sorted([base, partner]))
            if key in checked:
                break
            checked.add(key)

            if partner not in pipeline_files:
                unpaired.append(f"'{base}.pipeline' — partner '{partner}.pipeline' missing")
                break

            for b, p in [(base, path), (partner, pipeline_files[partner])]:
                try:
                    tree = ET.parse(p)
                    d = tree.getroot().find(".//{*}description")
                    if d is None:
                        pair_issues.append((b, "root <description> tag missing"))
                    elif not (d.text and d.text.strip()):
                        pair_issues.append((b, "root <description> is empty"))
                except ET.ParseError:
                    pair_issues.append((b, "invalid XML"))
                except Exception as ex:
                    pair_issues.append((b, str(ex)))
            break

    print(f"\n{'='*60}")
    print(f"🔍 PROJECT-WIDE: Pipeline Pair Descriptions ({folder})")
    print(f"{'='*60}")
    for msg in unpaired:
        print(f"  ⚠️  {msg}")
        _add(f"[{folder}] Pipeline pairs",
             f"Unpaired pipeline: {msg}.", "Functional/Design Non-Conformance", "Medium")
    for b, issue in pair_issues:
        print(f"  ❌ {b}.pipeline — {issue}")
        _add(f"{b}.pipeline",
             f"Pipeline pair description issue: {issue}.", "Comments", "Minor")
    if not unpaired and not pair_issues:
        print(f"  ✅ All pipeline pairs have descriptions")
    if not checked:
        print(f"  ℹ️  No paired pipelines detected")


# ════════════════════════════════════════════════════════════════════════════
# JSON REPORT BUILDER (works in Pyodide)
# ════════════════════════════════════════════════════════════════════════════

def _count(severity=None, defect_type=None):
    return sum(
        1 for f in _findings
        if (severity is None or f["severity"] == severity)
        and (defect_type is None or f["defect_type"] == defect_type)
    )

DEFECT_TYPES = [
    "Assignment", "Comments", "Data",
    "Exception/Error Handling", "Formatting",
    "Functional/Design Non-Conformance", "Logical",
]

def build_json_report():
    """Build and save JSON report (works in all environments)"""
    
    # Build summary
    summary = {
        "project_name": PROJECT_NAME,
        "work_product_type": "Code",
        "work_product_name": PROJECT_NAME,
        "review_metadata": {
            "version_no": REVIEW_VERSION,
            "date": REVIEW_DATE.isoformat(),
            "review_focus": REVIEW_FOCUS,
            "time_spent": TIME_SPENT,
            "reviewed_by": REVIEWER_NAME,
            "review_result": "To Re-review after rework" if _findings else "Accepted",
        },
        "defect_count": {
            "severity": {
                "Major": _count(severity="Major"),
                "Medium": _count(severity="Medium"),
                "Minor": _count(severity="Minor"),
            },
            "by_type": {dt: _count(defect_type=dt) for dt in DEFECT_TYPES}
        }
    }
    
    # Build analysis
    analysis = {
        "defect_types": {}
    }
    for dt in DEFECT_TYPES:
        analysis["defect_types"][dt] = {
            "Major": _count("Major", dt),
            "Medium": _count("Medium", dt),
            "Minor": _count("Minor", dt),
            "Total": _count(defect_type=dt)
        }
    
    # Build complete report
    report = {
        "summary": summary,
        "details": _findings,
        "analysis": analysis,
        "guidelines": {
            "Assignment": "Assigning invalid data/object.",
            "Comments": "Comments not written per language standards; inaccurate or out of sync with functionality.",
            "Data": "Improper declaration, initialization, or description of data; incorrect data usage or type conversion.",
            "Exception/Error Handling": "Missing, wrong, or inadequate handling of errors and exceptions.",
            "Formatting": "Code not formatted per prescribed standards; readability and neatness also considered.",
            "Functional/Design Non-Conformance": "Code does not conform to requirements specification document.",
            "Logical": "Incorrect logic or procedure used: wrong math, incorrect comparison, wrong algorithm.",
        }
    }
    
    # Save report
    out_path = os.path.join(OUTPUT_DIR, OUTPUT_FILE)
    with open(out_path, "w") as f:
        json.dump(report, f, indent=2)
    
    print(f"\n{'='*60}")
    print(f"📊 JSON report generated:")
    print(f"   {out_path}")
    print(f"   Findings written: {len(_findings)}")
    print(f"   Major: {_count('Major')}  Medium: {_count('Medium')}  Minor: {_count('Minor')}")
    print(f"{'='*60}")


# ════════════════════════════════════════════════════════════════════════════
# MAIN RUNNERS
# ════════════════════════════════════════════════════════════════════════════

def run_script():
    """Per-file static analysis."""
    print(f"\n{'='*60}")
    print(f"📁 Static Analysis — CWD: {os.getcwd()}")
    print(f"{'='*60}")

    bix_files_all = []

    for folder in folders_to_check:
        if not os.path.exists(folder):
            print(f"\n❌ Folder not found: {folder}")
            continue

        for root_dir, _, files in os.walk(folder):
            for filename in sorted(files):
                file_path = os.path.join(root_dir, filename)

                if filename.endswith(".bix"):
                    bix_files_all.append(filename)

                if filename.endswith((".proxy", ".bix")):
                    print(f"\n📄 {file_path}")
                    print(f"  — PART 1:  Description Tag")
                    check_description_tag(file_path)

                if filename.endswith(".pipeline"):
                    print(f"\n📄 {file_path}")
                    bix_snap = list(bix_files_all)

                    print(f"  — PART 2:  Inline '//' Comments")
                    find_comment_lines(file_path)

                    print(f"  — PART 3:  Disabled Elements")
                    find_disabled_true_lines(file_path)

                    print(f"  — PART 4:  Log Tags")
                    find_log_tags(file_path)

                    print(f"  — PART 5:  JSON↔XML Conversions")
                    find_json_xml_conversions(file_path)

                    print(f"  — PART 8:  Unreferenced varNames")
                    find_unique_varname(file_path)

                    print(f"  — PART 9:  Missing .bix References")
                    find_bix_in_pipeline(file_path, bix_snap)

                    print(f"  — PART 10: Missing Node Comments")
                    find_missing_comments(file_path)

                    print(f"  — PART 11: Duplicate Node Names")
                    find_duplicate_nodes(file_path)

                    print(f"  — PART 13: Stage Descriptions")
                    find_stage_missing_descriptions(file_path)

    find_duplicate_bix(bix_files_all)
    for folder in folders_to_check:
        if os.path.exists(folder):
            find_pipeline_pair_description_mismatch(folder)


def run_script2():
    """Search for reviewer name across .xqy and config XML files."""
    user_input = REVIEWER_NAME
    print(f"\n{'='*60}")
    print(f"🔍 Searching for: '{user_input}'")
    print(f"{'='*60}")

    found_any = False
    for folder in folders_to_check:
        if not os.path.exists(folder):
            continue
        for root_dir, _, files in os.walk(folder):
            for filename in files:
                file_path = os.path.join(root_dir, filename)
                if filename.endswith(".xqy"):
                    print(f"\n  📄 {file_path}")
                    search_user_input(file_path, user_input)
                    found_any = True
                if filename in ("log-config.xml", "errormap-config.xml", "service-config.xml"):
                    print(f"\n  📄 {file_path}")
                    search_in_config_files(file_path, user_input)
                    found_any = True

    if not found_any:
        print("  ℹ️  No .xqy or config XML files found to search.")


# ════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    run_script()
    run_script2()

    # ── Generate the JSON report (works in Pyodide) ──
    build_json_report()
    
    print("\n✅ Analysis complete!")
