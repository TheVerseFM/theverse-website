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
import urllib.error

APP_KEY = os.environ.get("YVP_APP_KEY")
if not APP_KEY:
    print("Missing YVP_APP_KEY environment variable (set it as a repo secret).", file=sys.stderr)
    sys.exit(1)

HEADERS = {"X-YVP-App-Key": APP_KEY}

# The Berean Standard Bible's Bible ID on the YouVersion Platform. KJV
# (Bible ID 1) turned out not to be included in any of the fast-track
# license bundles available on the Platform, including the "Public
# Domain and Creative Commons" set -- so requests to it return a 403
# regardless of app/licensing status. BSB is public domain, modern, and
# is the version YouVersion uses in all of their own official API
# examples, confirming it's genuinely accessible.
BSB_BIBLE_ID = 3034


def api_get(url):
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        print(f"Request failed: {url}", file=sys.stderr)
        print(f"HTTP {e.code} {e.reason}: {body}", file=sys.stderr)
        raise


def main():
    now = datetime.datetime.now(datetime.timezone.utc)
    day_of_year = now.timetuple().tm_yday

    votd = api_get(f"https://api.youversion.com/v1/verse_of_the_days/{day_of_year}")
    passage_id = votd["passage_id"]

    passage = api_get(
        f"https://api.youversion.com/v1/bibles/{BSB_BIBLE_ID}/passages/{passage_id}?format=text"
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
