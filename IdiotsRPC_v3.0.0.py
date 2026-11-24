import datetime
import json
import re
import ssl
import time
import urllib.request
import xml.etree.ElementTree as ET
from pypresence import Presence
from pypresence.types import ActivityType

CLIENT_ID = "1574257573828362272"
YOUTUBE_CHANNEL_ID = "UCDMzXYZ-T767m1ozBSkyFZA"

# Replace YOUR_GITHUB_USERNAME with your actual GitHub username
CONFIG_URL = "https://raw.githubusercontent.com" + "/idiotsonstuff/IdiotsRPC/refs/heads/main/slides.json"

FALLBACK_CONFIG = {
    "channel_url": "https://youtube.com/@IdiotsOnStuff",
    "button1_label": "our youtube channel",
    "slides": [
        {
            "activity_type": 3,
            "details": "Uh oh! This is lowk a fallback config",
            "state": "This means taht aeker freaking sucks and you aren't meant to see this",
            "large_image": "aether",
            "large_text": "oopsie!",
            "small_image": "aether",
            "small_text": "mini aeker",
        }
    ],
}

def get_remote_config():
    """Pulls the latest slides and links from GitHub."""
    try:
        ctx = ssl._create_unverified_context()
        req = urllib.request.Request(CONFIG_URL, headers={"User-Agent": "Mozilla/5.0"})
        res = urllib.request.urlopen(req, timeout=5, context=ctx)
        return json.loads(res.read().decode("utf-8"))
    except Exception as e:
        print("Remote config fallback used:", e)
        return FALLBACK_CONFIG

def get_channel_stats(channel_url):
    """Fetches latest video title, URL, upload age, and current subscriber count."""
    rss_url = "https://youtube.com" + "/feeds/videos.xml?channel_id=" + YOUTUBE_CHANNEL_ID
    ctx = ssl._create_unverified_context()

    latest_label = "watch our videos"
    latest_url = "https://youtube.com/@IdiotsOnStuff/videos"
    upload_age = "whenever"
    sub_count = 17

    try:
        req = urllib.request.Request(rss_url, headers={"User-Agent": "Mozilla/5.0"})
        response = urllib.request.urlopen(req, timeout=5, context=ctx)
        root = ET.fromstring(response.read())
        ns = {"atom": "http://w3.org" + "/2005/Atom"}

        latest_entry = root.find("atom:entry", ns)
        if latest_entry is not None:
            title = latest_entry.find("atom:title", ns).text
            latest_url = latest_entry.find("atom:link", ns).attrib["href"]

            prefix = "watch: "
            max_len = 32 - len(prefix)
            short_title = title if len(title) <= max_len else title[:max_len - 3] + "..."
            latest_label = f"{prefix}{short_title}"

            pub_str = latest_entry.find("atom:published", ns).text[:10]
            pub_date = datetime.date.fromisoformat(pub_str)
            days_ago = (datetime.date.today() - pub_date).days
            if days_ago == 0:
                upload_age = "today"
            elif days_ago == 1:
                upload_age = "1 day ago"
            else:
                upload_age = f"{days_ago} days ago"
    except Exception as e:
        print("RSS Feed Error:", e)

    try:
        req_sub = urllib.request.Request(channel_url, headers={"User-Agent": "Mozilla/5.0", "Accept-Language": "en-US,en;q=0.9"})
        html = urllib.request.urlopen(req_sub, timeout=5, context=ctx).read().decode("utf-8", errors="ignore")
        match = re.search(r'"subscriberCountText":\{"simpleText":"([\d\.KMB]+)\s+subscriber', html)
        if match:
            raw_subs = match.group(1)
            sub_count = int(raw_subs) if raw_subs.isdigit() else raw_subs
    except Exception as e:
        print("Sub Count Error:", e)

    return latest_label, latest_url, upload_age, sub_count

while True:
    try:
        RPC = Presence(CLIENT_ID)
        RPC.connect()
        print("Connected to Discord! IdiotsRPC v3.0.0 is live. Minimize this window.")
        break
    except Exception:
        print("Waiting for Discord to open... retrying in 5 seconds.")
        time.sleep(5)

config = get_remote_config()
channel_url = config.get("channel_url", "https://youtube.com")
latest_label, latest_url, upload_age, sub_count = get_channel_stats(channel_url)
last_checked = time.time()
print(f"Loaded {len(config.get('slides', []))} remote slides | Subs: {sub_count} | Latest: {latest_label}")

try:
    index = 0
    while True:
        if time.time() - last_checked > 900:
            config = get_remote_config()
            channel_url = config.get("channel_url", "https://youtube.com")
            latest_label, latest_url, upload_age, sub_count = get_channel_stats(channel_url)
            last_checked = time.time()

        slides = config.get("slides", FALLBACK_CONFIG["slides"])
        subs_left = max(0, 100 - sub_count) if isinstance(sub_count, int) else "many"
        slide = slides[index % len(slides)]

        details_txt = slide["details"].format(subs=sub_count, subs_left=subs_left, upload_age=upload_age)
        state_txt = slide["state"].format(subs=sub_count, subs_left=subs_left, upload_age=upload_age)
        small_txt = slide["small_text"].format(subs=sub_count, subs_left=subs_left, upload_age=upload_age)

        btn2_label = slide.get("btn2_label", latest_label)
        btn2_url = slide.get("btn2_url", latest_url)
        act_type = ActivityType(slide.get("activity_type", 3))
        now = int(time.time())

        RPC.update(
            activity_type=act_type,
            details=details_txt,
            state=state_txt,
            start=now,
            end=now + 15,
            large_image=slide["large_image"],
            large_text=slide["large_text"],
            small_image=slide["small_image"],
            small_text=small_txt,
            buttons=[
                {"label": config.get("button1_label", "our youtube channel"), "url": channel_url},
                {"label": btn2_label, "url": btn2_url},
            ],
        )
        index = (index + 1) % len(slides)
        time.sleep(15)
except KeyboardInterrupt:
    print("Closing Rich Presence...")
    RPC.close()
