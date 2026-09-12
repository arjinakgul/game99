#!/usr/bin/env python3
"""
Minimal Meshy REST client (no MCP needed). Requires MESHY_API_KEY in the environment.

  python3 tools/meshy_api.py image2mesh <image.png> <out.glb> [--poly 20000] [--no-texture] [--prompt "..."]
  python3 tools/meshy_api.py remesh <task_id> <out.glb> [--poly 20000] [--quad]
  python3 tools/meshy_api.py rig <task_id> <out.glb>
  python3 tools/meshy_api.py status <kind> <task_id>          # kind: image-to-3d | remesh | rigging
  python3 tools/meshy_api.py download <kind> <task_id> <out.glb>
"""
import base64, json, os, sys, time, urllib.request

API = "https://api.meshy.ai/openapi"
KEY = os.environ.get("MESHY_API_KEY")
if not KEY:
    sys.exit("MESHY_API_KEY is not set (add it to the cloud environment's variables)")

def call(method, path, body=None):
    req = urllib.request.Request(API + path, method=method,
                                 headers={"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"},
                                 data=json.dumps(body).encode() if body is not None else None)
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read().decode() or "{}")

def wait(kind, task_id, every=8):
    while True:
        t = call("GET", f"/v1/{kind}/{task_id}")
        st, pr = t.get("status"), t.get("progress", 0)
        print(f"  {kind} {task_id}: {st} {pr}%", flush=True)
        if st in ("SUCCEEDED", "FAILED", "CANCELED", "EXPIRED"):
            if st != "SUCCEEDED":
                sys.exit(f"task ended with {st}: {t.get('task_error')}")
            return t
        time.sleep(every)

def download(task, out):
    url = task["model_urls"]["glb"]
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    urllib.request.urlretrieve(url, out)
    print("saved", out, os.path.getsize(out) // 1024, "KB")

def opt(flag, default=None, cast=str):
    return cast(sys.argv[sys.argv.index(flag) + 1]) if flag in sys.argv else default

cmd = sys.argv[1] if len(sys.argv) > 1 else "help"
if cmd == "image2mesh":
    img, out = sys.argv[2], sys.argv[3]
    ext = os.path.splitext(img)[1].lstrip(".").replace("jpg", "jpeg")
    data_uri = f"data:image/{ext};base64," + base64.b64encode(open(img, "rb").read()).decode()
    body = {"image_url": data_uri, "ai_model": opt("--model", "meshy-7"),
            "should_remesh": True, "target_polycount": opt("--poly", 20000, int),
            "topology": "quad" if "--quad" in sys.argv else "triangle",
            "should_texture": "--no-texture" not in sys.argv, "enable_pbr": False}
    if opt("--prompt"):
        body["texture_prompt"] = opt("--prompt")
    r = call("POST", "/v1/image-to-3d", body)
    print("task", r); download(wait("image-to-3d", r["result"]), out)
elif cmd == "remesh":
    tid, out = sys.argv[2], sys.argv[3]
    r = call("POST", "/v1/remesh", {"input_task_id": tid, "target_formats": ["glb", "fbx"],
                                     "topology": "quad" if "--quad" in sys.argv else "triangle",
                                     "target_polycount": opt("--poly", 20000, int)})
    print("task", r); download(wait("remesh", r["result"]), out)
elif cmd == "rig":
    tid, out = sys.argv[2], sys.argv[3]
    r = call("POST", "/v1/rigging", {"input_task_id": tid})
    print("task", r); download(wait("rigging", r["result"]), out)
elif cmd == "status":
    print(json.dumps(call("GET", f"/v1/{sys.argv[2]}/{sys.argv[3]}"), indent=1)[:3000])
elif cmd == "download":
    download(call("GET", f"/v1/{sys.argv[2]}/{sys.argv[3]}"), sys.argv[4])
else:
    print(__doc__)
