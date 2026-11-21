"""TradingAgents Ultimate · اجراکنندهٔ GitHub Actions (بدون مرورگر، بدون Colab).
- موتور تحلیل در engine.py است (تبدیل‌شده از نوت‌بوک).
- خروجی تحلیل فقط به‌صورت اعلان ntfy به گوشی می‌رود؛ لاگ عمومی Actions فقط وضعیت کوتاه نشان می‌دهد.
"""
import os, sys, io, re, json, time, types, html, tempfile, traceback

_REAL = sys.__stdout__
HERE = os.path.dirname(os.path.abspath(__file__))
ENGINE = os.path.join(HERE, "engine.py")
DATA = os.environ.get("TA_DATA") or os.path.join(HERE, "data")
os.makedirs(DATA, exist_ok=True)
os.environ.setdefault("TA_REPO_DIR", os.path.join(HERE, "TradingAgents"))
LOGP = os.path.join(tempfile.gettempdir(), "ta_last_run.log")


class _Tee:
    """همهٔ خروجی موتور (که ممکن است نتیجهٔ تحلیل باشد) فقط در فایل موقت می‌رود، نه در لاگ عمومی."""
    encoding = "utf-8"
    def __init__(self): self.f = open(LOGP, "w", encoding="utf-8", errors="ignore")
    def write(self, s):
        try: self.f.write(s)
        except Exception: pass
        return len(s)
    def flush(self):
        try: self.f.flush()
        except Exception: pass
    def isatty(self): return False


sys.stdout = sys.stderr = _Tee()


def say(m):
    _REAL.write(str(m) + "\n"); _REAL.flush()


def _scrub(t):
    for k in ("GOOGLE_API_KEY", "NTFY_TOPIC"):
        v = os.environ.get(k, "")
        if v: t = str(t).replace(v, "***")
    return str(t)


# ---------- جایگزین IPython: کارت‌های HTML به متن ساده در فایل موقت تبدیل می‌شوند ----------
def _txt(h):
    h = re.sub(r"<style.*?</style>", "", h, flags=re.S | re.I)
    h = re.sub(r"<script.*?</script>", "", h, flags=re.S | re.I)
    h = re.sub(r"<br\s*/?>|</(div|p|tr|summary|li|details|table)>", "\n", h, flags=re.I)
    h = re.sub(r"</t[dh]>", " | ", h, flags=re.I)
    h = html.unescape(re.sub(r"<[^>]+>", "", h))
    return re.sub(r"\n\s*\n+", "\n", h).strip()


class HTML:
    def __init__(self, data=""): self.data = data


class Pretty(HTML):
    pass


def display(*objs, **kw):
    if kw.get("display_id"): return None          # کارت‌های زندهٔ پیشرفت (هر چند ثانیه) در لاگ نمی‌آیند
    for o in objs:
        t = _txt(o.data if hasattr(o, "data") else str(o))
        if t: sys.stdout.write(t + "\n")


def update_display(*a, **k): return None
def clear_output(*a, **k): return None


class StopExecution(Exception):
    pass


class _HeadlessStop(Exception):
    """خروج عادی: ستاپ فعالی نیست یا همین سیگنال تازه فرستاده شده."""


_m = {n: types.ModuleType(n) for n in ("IPython", "IPython.display", "IPython.core", "IPython.core.error")}
for _n in ("display", "HTML", "Pretty", "clear_output", "update_display"): setattr(_m["IPython.display"], _n, globals()[_n])
_m["IPython.core.error"].StopExecution = StopExecution
_m["IPython"].display = _m["IPython.display"]; _m["IPython"].core = _m["IPython.core"]; _m["IPython.core"].error = _m["IPython.core.error"]
sys.modules.update(_m)


def _fail_notify(title, body):
    """اعلان خطا؛ حداکثر هر ۶ ساعت یک‌بار تا هر ۳۰ دقیقه گوشی را پر نکند."""
    tp = os.environ.get("NTFY_TOPIC", "").strip()
    if not tp: return
    stamp = os.path.join(DATA, "fail_stamp")
    try:
        if time.time() - float(open(stamp).read()) < 6 * 3600: return
    except Exception: pass
    try:
        import requests
        requests.post("https://ntfy.sh/", json={"topic": tp, "title": title[:100], "message": _scrub(body)[:900], "priority": 4, "tags": ["warning"]}, timeout=15)
        open(stamp, "w").write(str(time.time()))
    except Exception: pass


G = {"__name__": "ta_engine", "__file__": ENGINE, "_HEADLESS": True, "_DATA": DATA, "_HeadlessStop": _HeadlessStop,
     "_FALLBACK": os.environ.get("TA_FALLBACK", "0") == "1", "_COOLDOWN_H": float(os.environ.get("TA_COOLDOWN_H", "3") or 3)}

rc, status = 0, "ok"
t0 = time.time()
if not os.environ.get("NTFY_TOPIC", "").strip(): say("⚠ NTFY_TOPIC خالی است؛ هیچ اعلانی نمی‌آید.")
if not os.environ.get("GOOGLE_API_KEY", "").strip(): say("⚠ GOOGLE_API_KEY خالی است."); status, rc = "error: no key", 1
else:
    try:
        exec(compile(open(ENGINE, encoding="utf-8").read(), ENGINE, "exec"), G)
    except _HeadlessStop as e:
        status = f"skip ({e})"
    except BaseException as e:
        status, rc = f"error: {type(e).__name__}", 1
        tail = _scrub("".join(traceback.format_exception_only(type(e), e)))[:400]
        say("خطا: " + tail)
        try: sys.stdout.flush(); log_tail = open(LOGP, encoding="utf-8", errors="ignore").read()[-700:]
        except Exception: log_tail = ""
        _fail_notify("❌ اجرای GitHub خطا داد", tail + "\n---\n" + log_tail)
say(f"TradingAgents: {status} · {(time.time() - t0) / 60:.1f} دقیقه")
sys.stdout.flush()
os._exit(rc)      # نخ‌های پس‌زمینه بسته شوند؛ Actions منتظر نماند
