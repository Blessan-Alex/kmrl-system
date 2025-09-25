"""
Aggregate batch outputs into a processing report.

Reads outputs/index.json and produces (under outputs/reports/ by default):
- report.json (structured counters)
- report.md (human-readable summary)
"""
from __future__ import annotations

import json
from pathlib import Path
from collections import Counter, defaultdict


def main(out_dir: str = "./outputs", reports_subdir: str = "reports") -> int:
    out_path = Path(out_dir)
    index_file = out_path / "index.json"
    if not index_file.exists():
        print(f"index.json not found in {out_path}")
        return 1

    data = json.loads(index_file.read_text(encoding="utf-8"))

    total = 0
    skipped = 0
    decisions = Counter()
    detected_types = Counter()
    processed_success = 0
    processed_failed = 0
    enhancement_needed = 0
    rejected = 0
    errors = 0

    examples_by_decision = defaultdict(list)

    for item in data:
        total += 1

        if item.get("skipped"):
            skipped += 1
            continue

        det = item.get("detected", {})
        q = item.get("quality", {})
        p = item.get("processing", {})
        err = item.get("errors", []) or []

        detected_types[det.get("type", "unknown")] += 1

        decision = q.get("decision", "unknown")
        decisions[decision] += 1
        if decision == "reject":
            rejected += 1

        if p.get("enhancement_needed"):
            enhancement_needed += 1

        if p.get("attempted"):
            if p.get("success"):
                processed_success += 1
            else:
                processed_failed += 1

        if err:
            errors += 1

        # capture up to 5 examples per decision
        if len(examples_by_decision[decision]) < 5:
            examples_by_decision[decision].append({
                "file": item.get("file"),
                "type": det.get("type"),
                "score": q.get("overall_score"),
                "processor": (item.get("processing") or {}).get("processor"),
            })

    report = {
        "totals": {
            "files_seen": total,
            "skipped_unsupported": skipped,
            "processed_success": processed_success,
            "processed_failed": processed_failed,
            "rejected": rejected,
            "enhancement_needed": enhancement_needed,
            "with_errors": errors,
        },
        "by_decision": decisions,
        "by_type": detected_types,
        "examples": examples_by_decision,
    }

    # Ensure reports directory
    reports_dir = out_path / reports_subdir
    reports_dir.mkdir(parents=True, exist_ok=True)

    # Write JSON report
    (reports_dir / "report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # Write Markdown summary
    md_lines = []
    md_lines.append("# Batch Processing Report")
    md_lines.append("")
    t = report["totals"]
    md_lines.append(f"- Files seen: {t['files_seen']}")
    md_lines.append(f"- Skipped (unsupported): {t['skipped_unsupported']}")
    md_lines.append(f"- Processed (success): {t['processed_success']}")
    md_lines.append(f"- Processed (failed): {t['processed_failed']}")
    md_lines.append(f"- Rejected (quality): {t['rejected']}")
    md_lines.append(f"- Enhancement needed: {t['enhancement_needed']}")
    md_lines.append(f"- With errors: {t['with_errors']}")
    md_lines.append("")

    md_lines.append("## By Decision")
    for k, v in decisions.items():
        md_lines.append(f"- {k}: {v}")
    md_lines.append("")

    md_lines.append("## By Detected Type")
    for k, v in detected_types.items():
        md_lines.append(f"- {k}: {v}")
    md_lines.append("")

    md_lines.append("## Examples")
    for dec, exs in examples_by_decision.items():
        md_lines.append(f"### {dec}")
        for e in exs:
            md_lines.append(f"- {e['file']} (type={e['type']}, score={e['score']}, processor={e['processor']})")
        md_lines.append("")

    (reports_dir / "report.md").write_text("\n".join(md_lines), encoding="utf-8")

    print(f"Report written to {reports_dir / 'report.json'} and {reports_dir / 'report.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


