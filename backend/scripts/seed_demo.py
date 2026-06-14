"""Author the demo feed (posts.json) plus a neutral starter cache (cache.json).

This writes ONLY post content/metadata. Classification + analysis come from the
real pipeline via `build_cache.py` (or POST /rebuild-cache). The starter cache
marks every post unflagged so the app serves a valid feed before the first
rebuild; running the real pipeline then fills in flags + analyses.

All harmful examples are synthetic, mild-to-moderate, and reference only
unnamed/fictional groups (never real ethnic, religious, or national groups).

Run:  python backend/scripts/seed_demo.py
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

USERS = {
    "maya":    {"name": "Maya Chen",        "handle": "maya_codes",      "initial": "M", "color": "#2563EB", "verified": False},
    "dave":    {"name": "Dave R.",          "handle": "grillmaster_dave","initial": "D", "color": "#D97706", "verified": False},
    "priya":   {"name": "Priya K.",         "handle": "aerialnomad",     "initial": "P", "color": "#0D9488", "verified": True},
    "lena":    {"name": "Lena Ortiz",       "handle": "lena_writes",     "initial": "L", "color": "#DB2777", "verified": False},
    "sam":     {"name": "Sam · RN",         "handle": "nightshift_sam",  "initial": "S", "color": "#7C3AED", "verified": False},
    "tom":     {"name": "Tom B.",           "handle": "tom_b",           "initial": "T", "color": "#0F172A", "verified": False},
    "anna":    {"name": "Anna Whitfield",   "handle": "historybuff_anna","initial": "A", "color": "#9333EA", "verified": True},
    "truth":   {"name": "Truth Hour",       "handle": "TheRealTruthHour","initial": "T", "color": "#DC2626", "verified": False},
    "wake":    {"name": "Open Your Eyes",   "handle": "wakeup_sheeple",  "initial": "O", "color": "#7C2D12", "verified": False},
    "brad":    {"name": "Brad // crypto",   "handle": "cryptobrad",      "initial": "B", "color": "#F59E0B", "verified": False},
    "radio":   {"name": "Real Talk Radio",  "handle": "realtalkradio",   "initial": "R", "color": "#B91C1C", "verified": False},
    "parent":  {"name": "Concerned Parent", "handle": "concerned_parent_99","initial": "C","color": "#92400E","verified": False},
    "doom":    {"name": "doomscroller",     "handle": "doomscroller",    "initial": "d", "color": "#475569", "verified": False},
    "quiet":   {"name": "just asking",      "handle": "quiet_observer",  "initial": "j", "color": "#64748B", "verified": False},
    "mike":    {"name": "Mike",             "handle": "patriot_mike49",  "initial": "M", "color": "#991B1B", "verified": False},
    "zephyr":  {"name": "ZephyrX",          "handle": "ZephyrX_",        "initial": "Z", "color": "#1F2937", "verified": False},
    "border":  {"name": "Borderwatch",      "handle": "borderwatch_now", "initial": "B", "color": "#7F1D1D", "verified": False},
    "oldtown": {"name": "Old Town Voice",   "handle": "oldtownvoice",    "initial": "O", "color": "#78350F", "verified": False},
    "jane":    {"name": "Jane",             "handle": "realtalk_jane",   "initial": "J", "color": "#a16207", "verified": False},
}

POSTS = []


def add(pid, user, time, text, *, media=None, replies=0, reposts=0, likes=0):
    POSTS.append({
        "id": pid,
        "user": USERS[user],
        "time": time,
        "text": text,
        "media": media,
        "engagement": {"replies": replies, "reposts": reposts, "likes": likes},
    })


# ---- Normal posts --------------------------------------------------------
add("p1", "maya", "12m",
    "spent three hours debugging today only to realize i'd been editing the wrong file the entire time. "
    "anyway. how is everyone's monday going",
    replies=156, reposts=89, likes=1243)

add("p2", "dave", "34m",
    "Unpopular opinion: pineapple absolutely belongs on pizza and I'm tired of pretending it doesn't \U0001F34D",
    replies=890, reposts=320, likes=4500)

add("p3", "priya", "1h",
    "Sunrise over the valley in Patagonia right now. Some places just don't feel real until you're standing in them. \U0001F3D4️",
    media={"type": "gradient"}, replies=230, reposts=1200, likes=8900)

add("p4", "lena", "2h",
    "finished the first draft of my novel at 2am and immediately started doubting every single word of it. "
    "writing is just professionally arguing with yourself.",
    replies=98, reposts=340, likes=2100)

add("p5", "sam", "3h",
    "12 hour shift done. feet wrecked, heart full. a patient's family brought the whole unit donuts today "
    "and i nearly cried in the break room. it's the small stuff.",
    replies=145, reposts=210, likes=3400)

add("p6", "tom", "4h", "is it coffee o'clock yet", replies=34, reposts=12, likes=540)

add("p7", "anna", "5h",
    "people ask why i love history and honestly it's because nothing is ever as simple as the textbook makes it "
    "sound. every 'obvious' decision was made by a real person who couldn't see the ending, who was scared and "
    "tired and working with bad information. we read the past like the outcome was inevitable, but the people "
    "living it had no idea which way it would go. that's the part that stays with me, not the dates or the "
    "battles but the uncertainty. it makes me a lot gentler about the present, knowing future generations will "
    "flatten us into a tidy paragraph too.",
    replies=210, reposts=980, likes=5600)

# ---- Manipulation posts --------------------------------------------------
add("p8", "truth", "26m",
    "They don't want you to know this, but the new digital ID rolling out next month means they can switch off "
    "your bank account with a single click. This is NOT a conspiracy. Screenshot this before it gets taken down. ⏰",
    replies=3400, reposts=8900, likes=12000)

add("p9", "wake", "1h",
    "Wake up. Everything you were taught was designed to keep you obedient and quiet. The people at the top are "
    "laughing at how easy it was. Stop trusting them and start trusting your gut.",
    replies=890, reposts=4200, likes=6700)

add("p10", "brad", "1h",
    "\U0001F6A8 ONLY 100 spots left. This is your LAST chance to get in before the price 10x's. The people who "
    "hesitate will be kicking themselves in 6 months. DM me NOW or stay broke. \U0001F449 https://t.co/x9f2aQ",
    replies=1200, reposts=450, likes=890)

add("p11", "radio", "2h",
    "Notice how every time regular people start asking real questions, there's suddenly a brand new crisis to "
    "distract everyone? That's not a coincidence. They've been running this exact playbook for decades.",
    replies=780, reposts=5600, likes=9800)

add("p12", "parent", "3h",
    "If you don't share this, don't call yourself a real parent. They are putting things into the curriculum "
    "that will destroy your child's mind by next year. Act before it's too late.",
    replies=2300, reposts=6700, likes=4500)

add("p13", "doom", "3h",
    "oh good, another 'once in a lifetime' crisis this week. truly we are so blessed to live through the single "
    "most important moment in human history every monday \U0001F644",
    replies=120, reposts=670, likes=3200)

# ---- Borderline ----------------------------------------------------------
add("p14", "quiet", "4h",
    "i'm not saying anything is definitely wrong with the new policy... but doesn't it feel a little convenient? "
    "a lot of people are quietly starting to wonder, and maybe that's worth paying attention to.",
    replies=200, reposts=340, likes=1200)

# ---- Hate speech (synthetic, unnamed groups) -----------------------------
add("p15", "mike", "5h",
    "These people pour into our town, don't bother learning how we live, and expect us to bend over backwards "
    "for them. They breed faster than we can keep up and soon there'll be nothing left of who we are. Enough.",
    replies=1200, reposts=3400, likes=5600)

add("p16", "zephyr", "6h",
    "Every one of them is the same — vermin who swarm in and bleed this place dry. They don't belong here and "
    "they should be driven out before there's nothing left.",
    replies=890, reposts=1100, likes=2300)

add("p17", "border", "7h",
    "They're animals, plain and simple, and you can't civilize an animal. People like that should be removed "
    "from our streets before they ruin everything.",
    replies=1500, reposts=2100, likes=3400)

add("p18", "oldtown", "9h",
    "They've infested every neighborhood they've touched and turned it into a dump. Pack them up and send them "
    "back where they came from before there's nothing left of this place.",
    replies=1900, reposts=2800, likes=4500)

add("p19", "jane", "11h",
    "funny how a certain kind of people always seem to end up at the center of every single problem in this city. "
    "at some point you stop calling it a coincidence.",
    replies=600, reposts=900, likes=1800)


def write_starter_cache() -> None:
    """Neutral cache so the app serves a valid feed before the first rebuild."""
    posts = {
        p["id"]: {
            "classification": {
                "label": "NOT_HATE", "flagged": False, "confidence": 0.0,
                "high_confidence": False, "truncated": False, "raw_scores": {},
                "model": "starter (unanalyzed)",
            },
            "analysis": None,
        }
        for p in POSTS
    }
    payload = {
        "meta": {
            "built_at": None,
            "model": "starter (unanalyzed)",
            "device": "n/a",
            "note": "Neutral starter cache. Run build_cache.py or POST /rebuild-cache for real analysis.",
        },
        "posts": posts,
    }
    with open(DATA / "cache.json", "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def main() -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    with open(DATA / "posts.json", "w", encoding="utf-8") as f:
        json.dump(POSTS, f, ensure_ascii=False, indent=2)
    if not (DATA / "cache.json").exists():
        write_starter_cache()
    print(f"Wrote {len(POSTS)} posts -> posts.json")
    print("Run build_cache.py (or POST /rebuild-cache) to generate real classification + analysis.")


if __name__ == "__main__":
    main()
