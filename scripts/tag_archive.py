"""
tag_archive.py

Interactive CLI tagger for config/video_archive.csv.
Opens each untagged TikTok URL in your browser, then prompts for bucket + theme.
Saves after every entry — safe to quit (q) and resume any time.

Usage:
    python3 scripts/tag_archive.py

Controls:
    bucket_id   : A–H  (or enter to skip)
    theme_day   : couple | fitcheck | pov | vlog | behind_scenes |
                  confidence | teasy | viral  (or enter to skip)
    notes       : freeform, optional
    q / quit    : save and exit
    s / skip    : skip this video without tagging
    b / back    : go back one row (re-tag previous)
"""

import csv
import os
import sys
import webbrowser
from typing import Optional, List

CSV_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "config",
    "video_archive.csv",
)

COLUMNS = ["video_id", "source_url", "tiktok_video_id", "local_path",
           "bucket_id", "theme_day", "notes"]

VALID_BUCKETS = set("ABCDEFGH")

VALID_THEMES = {
    "couple", "fitcheck", "pov", "vlog",
    "behind_scenes", "confidence", "teasy", "viral",
}

BUCKET_LABELS = {
    "A": "Couple Energy",
    "B": "Fit Check / Fashion",
    "C": "POV / Playful",
    "D": "Day-in-Life / Vlog",
    "E": "Teasy / Suggestive",
    "F": "Confidence / Solo",
    "G": "Behind-the-Scenes",
    "H": "High-Energy / Viral",
}


def load_csv() -> List[dict]:
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def save_csv(rows: List[dict]) -> None:
    with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def untagged_indices(rows: List[dict]) -> List[int]:
    return [i for i, r in enumerate(rows) if not r.get("bucket_id", "").strip()]


def print_header() -> None:
    print("\n" + "=" * 60)
    print("  THESTEELEZONE — Archive Tagger")
    print("  q=quit  s=skip  b=back  enter=skip field")
    print("=" * 60)


def print_bucket_ref() -> None:
    print("\n  Buckets:")
    for k, v in BUCKET_LABELS.items():
        print(f"    {k}  {v}")
    print()
    print("  Themes: couple | fitcheck | pov | vlog |")
    print("          behind_scenes | confidence | teasy | viral\n")


def prompt(label: str, valid: Optional[set] = None, required: bool = False) -> Optional[str]:
    while True:
        val = input(f"  {label}: ").strip()
        if val.lower() in ("q", "quit"):
            return "QUIT"
        if val.lower() in ("s", "skip"):
            return "SKIP"
        if val.lower() in ("b", "back"):
            return "BACK"
        if not val:
            if required:
                print(f"  Required. Valid: {', '.join(sorted(valid))}")
                continue
            return ""
        if valid and val.upper() not in valid and val.lower() not in valid:
            print(f"  Invalid. Valid values: {', '.join(sorted(valid))}")
            continue
        return val.upper() if valid and len(next(iter(valid))) == 1 else val.lower()


def tag_row(row: dict, index: int, total: int, tagged: int) -> str:
    """Tag one row. Returns 'QUIT', 'SKIP', 'BACK', or 'OK'."""
    print(f"\n  [{index+1} / {total}]  tagged so far: {tagged}")
    print(f"  ID   : {row['video_id']}")
    print(f"  URL  : {row['source_url']}")

    webbrowser.open(row["source_url"])

    bucket = prompt("bucket_id (A–H)", VALID_BUCKETS, required=False)
    if bucket in ("QUIT", "SKIP", "BACK"):
        return bucket

    theme = prompt("theme_day", {v for v in VALID_THEMES}, required=False)
    if theme in ("QUIT", "SKIP", "BACK"):
        return theme

    notes = input("  notes (optional): ").strip()
    if notes.lower() in ("q", "quit"):
        return "QUIT"

    row["bucket_id"] = bucket
    row["theme_day"] = theme
    row["notes"] = notes
    return "OK"


def main() -> None:
    if not os.path.exists(CSV_PATH):
        print(f"ERROR: CSV not found at {CSV_PATH}", file=sys.stderr)
        sys.exit(1)

    rows = load_csv()
    total = len(rows)

    print_header()
    print_bucket_ref()

    queue = untagged_indices(rows)
    tagged_count = total - len(queue)

    if not queue:
        print("  All rows are already tagged. Nothing to do.")
        sys.exit(0)

    print(f"  {len(queue)} untagged rows remaining out of {total} total.")
    input("  Press enter to start tagging (or q to quit)... ")

    pos = 0  # position within queue

    while pos < len(queue):
        idx = queue[pos]
        tagged_so_far = total - len(untagged_indices(rows))

        result = tag_row(rows[idx], idx, total, tagged_so_far)

        if result == "QUIT":
            save_csv(rows)
            print(f"\n  Saved. {total - len(untagged_indices(rows))} rows tagged total. See you next time.")
            sys.exit(0)

        if result == "SKIP":
            pos += 1
            continue

        if result == "BACK":
            if pos > 0:
                pos -= 1
                # clear the previous row's tags so it shows as untagged on re-visit
                rows[queue[pos]]["bucket_id"] = ""
                rows[queue[pos]]["theme_day"] = ""
                rows[queue[pos]]["notes"] = ""
            else:
                print("  Already at the first untagged row.")
            continue

        # result == "OK"
        save_csv(rows)
        pos += 1

    save_csv(rows)
    final_untagged = len(untagged_indices(rows))
    print(f"\n  Done! {total - final_untagged} / {total} rows tagged.")
    if final_untagged:
        print(f"  {final_untagged} rows were skipped — run again to tag them.")


if __name__ == "__main__":
    main()
