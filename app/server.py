"""Exhibit Builder: a small local server for the Harvard Art Museums API.

Run:
    HAM_API_KEY=your-key python3 server.py        # then open http://localhost:8765

Get a free key at https://harvardartmuseums.org/collections/api.
Without a key the saved exhibits still open; search needs the key.
"""
import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

ROOT = os.path.dirname(os.path.abspath(__file__))
STATIC = os.path.join(ROOT, "static")
EXHIBITS = os.path.join(ROOT, "exhibits")
CACHE = os.path.join(ROOT, ".image-cache")
API = "https://api.harvardartmuseums.org"
PORT = int(os.environ.get("PORT", "8765"))
UA = {"User-Agent": "exhibit-builder/1.0"}

FIELDS = ",".join([
    "id", "objectnumber", "title", "dated", "datebegin", "dateend", "culture", "period",
    "medium", "dimensions", "creditline", "classification", "primaryimageurl", "url",
    "description", "labeltext", "people",
])


def api_key():
    """HAM_API_KEY from the environment, or from a HAM_API_KEY=... line in app/.env."""
    key = os.environ.get("HAM_API_KEY", "").strip()
    env_file = os.path.join(ROOT, ".env")
    if not key and os.path.exists(env_file):
        with open(env_file) as f:
            for line in f:
                name, _, value = line.partition("=")
                if name.strip() == "HAM_API_KEY":
                    key = value.strip().strip('"')
    return key


def api_get(path, params):
    query = urllib.parse.urlencode({"apikey": api_key(), **params})
    req = urllib.request.Request(f"{API}/{path}?{query}", headers=UA)
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.load(resp)


def slim(record):
    people = record.get("people") or []
    artist = next((p for p in people if p.get("role") == "Artist"), people[0] if people else None)
    return {
        "id": record["id"],
        "objectnumber": record.get("objectnumber"),
        "title": record.get("title"),
        "dated": record.get("dated"),
        "datebegin": record.get("datebegin"),
        "culture": record.get("culture"),
        "period": record.get("period"),
        "medium": (record.get("medium") or "").strip(),
        "dimensions": record.get("dimensions"),
        "creditline": record.get("creditline"),
        "classification": record.get("classification"),
        "artist": artist.get("displayname") if artist else None,
        "image": record.get("primaryimageurl"),
        "url": record.get("url"),
        "description": (record.get("description") or record.get("labeltext") or "").strip(),
    }


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


def fetch_image(urn):
    """Resolve an image URN through Harvard's name resolver and fetch a 900px IIIF rendition."""
    os.makedirs(CACHE, exist_ok=True)
    path = os.path.join(CACHE, re.sub(r"[^A-Za-z0-9_.-]", "_", urn) + ".jpg")
    if os.path.exists(path):
        with open(path, "rb") as f:
            return f.read()
    opener = urllib.request.build_opener(NoRedirect)
    try:
        opener.open(urllib.request.Request(f"https://nrs.harvard.edu/{urn}", headers=UA), timeout=20)
        raise ValueError("no redirect from resolver")
    except urllib.error.HTTPError as e:
        location = e.headers.get("Location")
    if not location:
        raise ValueError("resolver gave no image location")
    # The resolver may hop more than once before reaching the IIIF server.
    with urllib.request.urlopen(urllib.request.Request(location, method="HEAD", headers=UA), timeout=20) as resp:
        final = resp.geturl()
    sized = final.replace("/full/full/", "/full/!900,900/")
    with urllib.request.urlopen(urllib.request.Request(sized, headers=UA), timeout=30) as resp:
        data = resp.read()
    with open(path, "wb") as f:
        f.write(data)
    return data


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=STATIC, **kwargs)

    def log_message(self, fmt, *args):
        print("  " + fmt % args)

    def send_json(self, payload, status=200):
        body = json.dumps(payload, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        url = urllib.parse.urlparse(self.path)
        q = urllib.parse.parse_qs(url.query)
        try:
            if url.path == "/api/status":
                return self.send_json({"hasKey": bool(api_key())})
            if url.path == "/api/search":
                if not api_key():
                    return self.send_json({"error": "Search needs an API key. Put HAM_API_KEY=your-key in app/.env and restart the server."}, 400)
                params = {
                    "keyword": q.get("q", [""])[0],
                    "hasimage": 1,
                    "q": "imagepermissionlevel:0",
                    "size": 60,
                    "page": q.get("page", ["1"])[0],
                    "sort": "rank",
                    "fields": FIELDS,
                }
                data = api_get("object", params)
                records = [slim(r) for r in data.get("records", []) if r.get("primaryimageurl")]
                return self.send_json({"total": data["info"]["totalrecords"], "pages": data["info"]["pages"], "records": records})
            if url.path == "/api/exhibits":
                names = sorted(f[:-5] for f in os.listdir(EXHIBITS) if f.endswith(".json"))
                return self.send_json([{"slug": n, "title": json.load(open(os.path.join(EXHIBITS, n + ".json")))["title"]} for n in names])
            if url.path.startswith("/api/exhibits/"):
                slug = re.sub(r"[^a-z0-9-]", "", url.path.rsplit("/", 1)[1])
                with open(os.path.join(EXHIBITS, slug + ".json")) as f:
                    return self.send_json(json.load(f))
            if url.path == "/img":
                urn = q.get("urn", [""])[0]
                if not re.fullmatch(r"urn-3:[A-Za-z]+:[A-Za-z0-9_]+", urn):
                    return self.send_json({"error": "bad image id"}, 400)
                data = fetch_image(urn)
                self.send_response(200)
                self.send_header("Content-Type", "image/jpeg")
                self.send_header("Cache-Control", "max-age=86400")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                return self.wfile.write(data)
        except FileNotFoundError:
            return self.send_json({"error": "not found"}, 404)
        except urllib.error.HTTPError as e:
            msg = "The API rejected the key." if e.code == 401 else f"The API returned {e.code}."
            return self.send_json({"error": msg}, 502)
        except Exception as e:  # network failures, bad redirects
            return self.send_json({"error": str(e)}, 502)
        return super().do_GET()

    def do_POST(self):
        url = urllib.parse.urlparse(self.path)
        if not url.path.startswith("/api/exhibits/"):
            return self.send_json({"error": "not found"}, 404)
        slug = re.sub(r"[^a-z0-9-]", "", url.path.rsplit("/", 1)[1])[:60]
        if not slug:
            return self.send_json({"error": "Give the exhibit a title first."}, 400)
        body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))))
        if not isinstance(body.get("works"), list) or len(body["works"]) > 6:
            return self.send_json({"error": "An exhibit holds one to six works."}, 400)
        with open(os.path.join(EXHIBITS, slug + ".json"), "w") as f:
            json.dump(body, f, indent=2, ensure_ascii=False)
        return self.send_json({"saved": slug})


if __name__ == "__main__":
    print(f"Exhibit Builder on http://localhost:{PORT}")
    print("API key: " + ("found" if api_key() else "not set (search disabled, saved exhibits still open)"))
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
