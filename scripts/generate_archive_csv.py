"""
generate_archive_csv.py

Scans a directory of video files and produces a tagged archive CSV at
config/video_archive.csv.

Usage:
    python3 scripts/generate_archive_csv.py /path/to/videos [--prefix SZ]

Output columns:
    video_id       — e.g. SZ-0001 (padded to 4 digits)
    file_path      — absolute path to the video file
    bucket_id      — BLANK — fill in manually (A–H)
    theme_day      — BLANK — fill in manually (couple/fitcheck/pov/vlog/behind_scenes/confidence/teasy/viral)
    notes          — BLANK — optional freeform notes per clip

Bucket reference (copy into your spreadsheet as a lookup):
    A  Couple Energy       — us together, date night, candid
    B  Fit Check/Fashion   — outfit reveal, mirror selfie
    C  POV/Playful         — camera-forward, direct address, funny
    D  Day-in-Life/Vlog    — real-life moments, routines
    E  Teasy/Suggestive    — compliant, hinting at exclusive content
    F  Confidence/Solo     — solo content, attitude, energy
    G  Behind-the-Scenes   — setup, candid, "what we don't post" framing
    H  High-Energy/Viral   — best hooks, most shareable, trend-adjacent
"""

import argparse
import csv
import os
import sys

VIDEO_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv", ".webm", ".m4v"}

OUTPUT_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "config",
    "video_archive.csv",
)

COLUMNS = ["video_id", "file_path", "bucket_id", "theme_day", "notes"]


def collect_videos(root_dir: str) -> list[str]:
    paths = []
    for dirpath, _, filenames in os.walk(root_dir):
        for name in sorted(filenames):
            if os.path.splitext(name)[1].lower() in VIDEO_EXTENSIONS:
                paths.append(os.path.abspath(os.path.join(dirpath, name)))
    return sorted(paths)


def generate_csv(video_dir: str, prefix: str) -> None:
    if not os.path.isdir(video_dir):
        print(f"ERROR: '{video_dir}' is not a directory.", file=sys.stderr)
        sys.exit(1)

    videos = collect_videos(video_dir)
    if not videos:
        print(f"No video files found in '{video_dir}'.", file=sys.stderr)
        sys.exit(1)

    rows = [
        {
            "video_id": f"{prefix}-{str(i + 1).zfill(4)}",
            "file_path": path,
            "bucket_id": "",
            "theme_day": "",
            "notes": "",
        }
        for i, path in enumerate(videos)
    ]

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

    with open(OUTPUT_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Written {len(rows)} rows → {OUTPUT_PATH}")
    print()
    print("Next step: open config/video_archive.csv and fill in bucket_id (A–H)")
    print("and theme_day for each row. Leave notes blank or use it for tagging hints.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("video_dir", help="Path to the folder containing your video archive")
    parser.add_argument("--prefix", default="SZ", help="Video ID prefix (default: SZ)")
    args = parser.parse_args()
    generate_csv(args.video_dir, args.prefix.upper())


if __name__ == "__main__":
    main()
