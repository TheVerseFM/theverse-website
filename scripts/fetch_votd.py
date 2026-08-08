"""
Fetches today's actual Verse of the Day from the YouVersion (Bible App)
Platform API and writes it to votd.json at the repo root.

Runs daily via GitHub Actions. The YVP_APP_KEY secret never leaves this
script or GitHub's servers -- it's read from an environment variable
that Actions injects from a repository secret, and it is never written
to any file or logged.
"""
import os
import sys
import json
import datetime
import urllib.request

APP_KEY = os.environ.get("YVP_APP_KEY")
if not APP_KEY:
    print("Missing YVP_APP_KEY environment variable (set it as a repo secret).", file=sys.stderr)
    sys.exit(1)

HEADERS = {"X-YVP-App-Key": APP_KEY}


def api_get(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode())


def find_kjv_bible_id():
    url = (
        "https://api.youversion.com/v1/bibles"
        "?language_ranges%5B%5D=en"
        "&fields%5B%5D=id&fields%5B%5D=title&fields%5B%5D=abbreviation"
        "&page_size="
    )
    bibles = api_get(url)
    for b in bibles.get("data", []):
        title = (b.get("title") or "").lower()
        abbr = (b.get("abbreviation") or "").lower()
        if "king james" in title or abbr == "kjv":
            return b["id"]
    raise RuntimeError("Could not find the King James Version in the Bible collection.")


def main():
    now = datetime.datetime.utcnow()
    day_of_year = now.timetuple().tm_yday

    votd = api_get(f"https://api.youversion.com/v1/verse_of_the_days/{day_of_year}")
    passage_id = votd["passage_id"]

    bible_id = find_kjv_bible_id()

    passage = api_get(
        f"https://api.youversion.com/v1/bibles/{bible_id}/passages/{passage_id}?format=text"
    )

    result = {
        "date": now.strftime("%B %-d, %Y"),
        "ref": passage["reference"],
        "text": passage["content"].strip(),
    }

    with open("votd.json", "w") as f:
        json.dump(result, f, indent=2)
        f.write("\n")

    print("Wrote votd.json:", result)


if __name__ == "__main__":
    main()
