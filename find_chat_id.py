import os, json, urllib.request, urllib.error

TOKEN = os.environ.get("RUBIKA_TOKEN", "").strip()
BASE = f"https://botapi.rubika.ir/v3/{TOKEN}/"


def call(method, data=None):
    req = urllib.request.Request(BASE + method, json.dumps(data or {}).encode(),
                                 {"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            return json.loads(r.read().decode("utf-8", "replace"))
    except urllib.error.HTTPError as e:
        return {"status": f"HTTP_{e.code}", "body": e.read().decode("utf-8", "replace")[:300]}
    except Exception as e:
        return {"status": "ERR", "body": f"{type(e).__name__}: {e}"}


def walk(o, path=""):
    if isinstance(o, dict):
        for k, v in o.items():
            if k in ("chat_id", "from_chat_id") and isinstance(v, str):
                yield path + "/" + k, v
            yield from walk(v, path + "/" + k)
    elif isinstance(o, list):
        for v in o:
            yield from walk(v, path)


def kind(cid):
    return {"c": "کانال", "g": "گروه", "u": "کاربر", "b": "ربات/کاربر"}.get(cid[:1], "؟")


if not TOKEN:
    raise SystemExit("Secret به نام RUBIKA_TOKEN تنظیم نشده")

me = call("getMe")
print("getMe:", json.dumps(me, ensure_ascii=False)[:300])
if me.get("status") != "OK":
    raise SystemExit("توکن اشتباه است یا ربات در دسترس نیست")

updates = []; offset = None
for _ in range(10):
    body = {"limit": 100}
    if offset: body["offset_id"] = offset
    r = call("getUpdates", body)
    if r.get("status") != "OK":
        print("getUpdates:", json.dumps(r, ensure_ascii=False)[:400]); break
    d = r.get("data") or {}
    ups = d.get("updates") or []
    updates += ups
    nxt = d.get("next_offset_id")
    if not ups or not nxt or nxt == offset: break
    offset = nxt

print(f"تعداد آپدیت دریافتی: {len(updates)}")
found = {}
for u in updates:
    for path, cid in walk(u):
        found.setdefault(cid, set()).add(path)

if not found:
    print("\nهیچ شناسه‌ای پیدا نشد. مراحل را انجام بده و فوراً دوباره اجرا کن:")
    print("1) ربات را در کانال ادمین کن و یک پیام داخل کانال بفرست")
    print("2) یا یک پست از کانال را برای خود ربات فوروارد کن")
    for u in updates[:3]:
        print("نمونه آپدیت:", json.dumps(u, ensure_ascii=False)[:400])
else:
    print("\n===== شناسه‌های پیدا شده =====")
    for cid, srcs in found.items():
        info = call("getChat", {"chat_id": cid})
        chat = (info.get("data") or {}).get("chat") or {}
        title = chat.get("title") or (str(chat.get("first_name", "")) + " " + str(chat.get("last_name", ""))).strip()
        print(f"{cid} | {kind(cid)} | {title} | {chat.get('username', '')}")
