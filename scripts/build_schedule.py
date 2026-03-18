"""
build_schedule.py  —  infra__schedule_builder

Reads config/video_archive.csv (tagged, 481 videos) and generates a
rolling post schedule written to config/post_schedule.csv.

Usage:
    python3 scripts/build_schedule.py [--days 240] [--start 2026-03-18]

Schedule logic (from docs/blueprints/social-repost-blueprint.md):
  - 2 TikTok repost posts/day (AM + PM slots)
  - 1 IG Reel/day  (mirrors TikTok AM video, 1-day lag)
  - 1 X post/day
  - 4 Facebook posts/week  (Mon / Wed / Fri / Sat)
  - Same video never repeats on same platform within 60 days
  - Bucket rotation follows weekly pattern
  - Caption template + hashtag set assigned per platform × bucket
  - link_target resolved per platform
"""

import argparse
import csv
import os
import random
import uuid
from collections import defaultdict
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional

# ── paths ──────────────────────────────────────────────────────────────────
ROOT      = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARCHIVE   = os.path.join(ROOT, "config", "video_archive.csv")
SCHEDULE  = os.path.join(ROOT, "config", "post_schedule.csv")

# ── schedule columns ───────────────────────────────────────────────────────
COLUMNS = [
    "post_id", "video_id", "platform", "scheduled_date", "time_slot",
    "caption_template_id", "hashtag_set_id", "link_target", "link_url",
    "bucket_id", "theme_day", "loop_number", "audit_verdict", "status",
]

# ── weekly bucket rotation (AM bucket, PM bucket) per weekday ──────────────
# 0=Mon … 6=Sun
WEEKLY_BUCKETS = {
    0: ("A", "B"),
    1: ("C", "D"),
    2: ("A", "C"),
    3: ("E", "F"),
    4: ("B", "G"),
    5: ("H", "E"),
    6: ("D", "H"),
}

# ── hashtag sets per platform ──────────────────────────────────────────────
TT_HASHTAG_SETS  = ["TT-H1", "TT-H2", "TT-H3", "TT-H4"]
IG_HASHTAG_SETS  = ["IG-H1", "IG-H2"]
X_HASHTAG_SETS   = ["X-H1", "X-H2"]
FB_HASHTAG_SETS  = ["FB-H1"]

# ── caption template per platform × bucket ────────────────────────────────
TT_TEMPLATE = {"A":"T-1","B":"T-2","C":"T-3","D":"T-4","E":"T-5",
               "F":"T-2","G":"T-4","H":"T-5"}
IG_TEMPLATE = {"A":"I-3","B":"I-4","C":"I-5","D":"I-1","E":"I-2",
               "F":"I-4","G":"I-1","H":"I-2"}
X_TEMPLATE  = {"A":"X-4","B":"X-1","C":"X-2","D":"X-5","E":"X-3",
               "F":"X-1","G":"X-5","H":"X-3"}
FB_TEMPLATE = {"A":"F-1","B":"F-3","C":"F-2","D":"F-1","E":"F-3",
               "F":"F-2","G":"F-1","H":"F-3"}

# ── link targets ───────────────────────────────────────────────────────────
LINK_MAP = {
    "tiktok_repost": ("linkinbio",  "https://instagram.com/thesteelezone"),
    "ig_reel":       ("linkfly",    "https://linkfly.to/thesteelezone"),
    "x":             ("of_direct",  "https://onlyfans.com/thesteelezone"),
    "facebook":      ("linkfly",    "https://linkfly.to/thesteelezone"),
}

# ── Facebook posting days (Mon=0, Wed=2, Fri=4, Sat=5) ────────────────────
FB_DAYS = {0, 2, 4, 5}


# ── helpers ────────────────────────────────────────────────────────────────

def load_archive() -> Dict[str, List[dict]]:
    """Return videos grouped by bucket_id."""
    buckets: Dict[str, List[dict]] = defaultdict(list)
    with open(ARCHIVE, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            b = row.get("bucket_id", "").strip().upper() or "F"
            buckets[b].append(row)
    # shuffle each bucket so order isn't predictable
    for b in buckets:
        random.shuffle(buckets[b])
    return buckets


def next_video(
    bucket_pool: Dict[str, List[dict]],
    bucket_id: str,
    used_recently: Dict[str, Dict[str, date]],
    platform: str,
    today: date,
    fallback_buckets: List[str],
) -> Optional[dict]:
    """
    Pick the next unused-in-60-days video from bucket_id.
    Falls back to adjacent buckets if depleted.
    """
    candidates = [bucket_id] + fallback_buckets
    for b in candidates:
        pool = bucket_pool.get(b, [])
        for video in pool:
            vid = video["video_id"]
            last = used_recently.get(platform, {}).get(vid)
            if last is None or (today - last).days >= 60:
                pool.remove(video)
                pool.append(video)          # rotate to end so it cycles
                used_recently.setdefault(platform, {})[vid] = today
                return video
    return None


def hashtag_for_day(sets: List[str], day_number: int) -> str:
    return sets[day_number % len(sets)]


def make_post(
    video: dict,
    platform: str,
    post_date: date,
    slot: str,
    template_map: dict,
    hashtag_sets: List[str],
    day_number: int,
    loop: int,
) -> dict:
    bucket    = video.get("bucket_id", "F").upper()
    lt, url   = LINK_MAP[platform]
    return {
        "post_id":            str(uuid.uuid4())[:8],
        "video_id":           video["video_id"],
        "platform":           platform,
        "scheduled_date":     post_date.isoformat(),
        "time_slot":          slot,
        "caption_template_id": template_map.get(bucket, "T-1"),
        "hashtag_set_id":     hashtag_for_day(hashtag_sets, day_number),
        "link_target":        lt,
        "link_url":           url,
        "bucket_id":          bucket,
        "theme_day":          video.get("theme_day", ""),
        "loop_number":        loop,
        "audit_verdict":      "pending",
        "status":             "scheduled",
    }


def build_schedule(days: int, start: date) -> List[dict]:
    random.seed(42)                          # reproducible shuffles
    buckets    = load_archive()
    used: Dict[str, Dict[str, date]] = {}   # platform → video_id → last_post_date
    posts: List[dict] = []

    # track loop number per platform queue
    loop_counters: Dict[str, int] = defaultdict(lambda: 1)
    post_counts:   Dict[str, int] = defaultdict(int)
    archive_size = sum(len(v) for v in buckets.values())

    for day_offset in range(days):
        today    = start + timedelta(days=day_offset)
        weekday  = today.weekday()
        am_b, pm_b = WEEKLY_BUCKETS[weekday]
        fallback   = [b for b in "ABCDEFGH" if b not in (am_b, pm_b)]

        # ── TikTok repost: AM ────────────────────────────────────────────
        vid_am = next_video(buckets, am_b, used, "tiktok_repost", today, fallback)
        if vid_am:
            post_counts["tiktok_repost"] += 1
            loop = (post_counts["tiktok_repost"] - 1) // archive_size + 1
            posts.append(make_post(vid_am, "tiktok_repost", today, "AM",
                                   TT_TEMPLATE, TT_HASHTAG_SETS, day_offset, loop))

        # ── TikTok repost: PM ────────────────────────────────────────────
        vid_pm = next_video(buckets, pm_b, used, "tiktok_repost", today, fallback)
        if vid_pm:
            post_counts["tiktok_repost"] += 1
            loop = (post_counts["tiktok_repost"] - 1) // archive_size + 1
            posts.append(make_post(vid_pm, "tiktok_repost", today, "PM",
                                   TT_TEMPLATE, TT_HASHTAG_SETS, day_offset, loop))

        # ── IG Reel: mirrors yesterday's TikTok AM (1-day lag) ───────────
        if day_offset > 0:
            ig_source = next(
                (p for p in reversed(posts)
                 if p["platform"] == "tiktok_repost"
                 and p["time_slot"] == "AM"
                 and p["scheduled_date"] == (today - timedelta(days=1)).isoformat()),
                None,
            )
            if ig_source:
                ig_vid = {"video_id": ig_source["video_id"],
                          "bucket_id": ig_source["bucket_id"],
                          "theme_day": ig_source["theme_day"]}
                used.setdefault("ig_reel", {})[ig_vid["video_id"]] = today
                post_counts["ig_reel"] += 1
                loop = (post_counts["ig_reel"] - 1) // archive_size + 1
                posts.append(make_post(ig_vid, "ig_reel", today, "PM",
                                       IG_TEMPLATE, IG_HASHTAG_SETS, day_offset, loop))

        # ── X: 1/day ─────────────────────────────────────────────────────
        x_b = pm_b  # X uses PM bucket (higher energy)
        vid_x = next_video(buckets, x_b, used, "x", today, fallback)
        if vid_x:
            post_counts["x"] += 1
            loop = (post_counts["x"] - 1) // archive_size + 1
            posts.append(make_post(vid_x, "x", today, "PM",
                                   X_TEMPLATE, X_HASHTAG_SETS, day_offset, loop))

        # ── Facebook: Mon/Wed/Fri/Sat only ───────────────────────────────
        if weekday in FB_DAYS:
            vid_fb = next_video(buckets, am_b, used, "facebook", today, fallback)
            if vid_fb:
                post_counts["facebook"] += 1
                loop = (post_counts["facebook"] - 1) // archive_size + 1
                posts.append(make_post(vid_fb, "facebook", today, "AM",
                                       FB_TEMPLATE, FB_HASHTAG_SETS, day_offset, loop))

    return posts


def write_schedule(posts: List[dict]) -> None:
    with open(SCHEDULE, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS)
        w.writeheader()
        w.writerows(posts)


def print_summary(posts: List[dict], days: int) -> None:
    from collections import Counter
    by_platform = Counter(p["platform"] for p in posts)
    print(f"\n  Schedule generated — {days} days, {len(posts)} total posts")
    print(f"  Written → {SCHEDULE}\n")
    print("  Platform breakdown:")
    for platform, count in sorted(by_platform.items()):
        print(f"    {platform:<18} {count} posts")
    print()
    print("  First 3 rows:")
    for p in posts[:3]:
        print(f"    {p['post_id']}  {p['scheduled_date']}  {p['time_slot']}  "
              f"{p['platform']:<18}  {p['video_id']}  [{p['bucket_id']}]  "
              f"{p['caption_template_id']}  {p['hashtag_set_id']}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--days",  type=int, default=240,
                        help="Number of days to schedule (default: 240)")
    parser.add_argument("--start", type=str,
                        default=date.today().isoformat(),
                        help="Start date ISO 8601 (default: today)")
    args = parser.parse_args()

    start_date = datetime.strptime(args.start, "%Y-%m-%d").date()
    posts = build_schedule(args.days, start_date)
    write_schedule(posts)
    print_summary(posts, args.days)


if __name__ == "__main__":
    main()
