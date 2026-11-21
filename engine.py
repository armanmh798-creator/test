# TradingAgents Ultimate · موتور (تبدیل‌شده از نوت‌بوک v22_1 برای GitHub Actions). این فایل را دستی ویرایش نکنید.
import os, re, time, json, getpass, requests

LLM_PROVIDER = "google"      # "google" = Gemini (پیش‌فرض) | "rayegan" = مدل‌های رایگان از چند سرویس (v22)
LLM_PROVIDER = str(LLM_PROVIDER).strip().lower()
if LLM_PROVIDER not in ("google", "rayegan"): raise ValueError('LLM_PROVIDER باید "google" یا "rayegan" باشد')
import warnings; warnings.filterwarnings("ignore")
from IPython.display import display, HTML

import html as _hl

def _ui(c1, c2, ic, title, sub=""):

    display(HTML("<style>@import url('https://fonts.googleapis.com/css2?family=Vazirmatn:wght@400;600;800&display=swap');</style>"

        f"<div dir='rtl' style=\"font-family:Vazirmatn,Tahoma,sans-serif;line-height:1.8;background:linear-gradient(110deg,{c2},{c1});color:#fff;border-radius:14px;padding:12px 18px;margin:8px 0;box-shadow:0 2px 10px rgba(0,0,0,.28)\"><b style='font-size:19px'>{ic} {title}</b>"

        + (f"<div style='opacity:.9;font-size:12.5px'>{sub}</div>" if sub else "") + "</div>"))

def _msg(c, text):

    display(HTML(f"<div dir='rtl' style=\"font-family:Vazirmatn,Tahoma,sans-serif;line-height:1.8;border-radius:10px;padding:7px 13px;margin:5px 0;border-right:5px solid {c};background:{c}1a;white-space:pre-wrap\">{_hl.escape(text)}</div>"))

os.chdir(os.environ.get("TA_REPO_DIR", "TradingAgents"))      # GitHub: نصب را workflow انجام داده است
# ═══════════════ (ادغام‌شده) از اینجا: مرحله ۲ · کلید Gemini ═══════════════
# ═══════════════ مرحله ۲ · کلید Gemini + انتخاب هوشمند و کم‌هزینهٔ مدل‌ها ═══════════════
import os, re, time, getpass, base64, io, wave, requests
import html as _hl
from IPython.display import display, HTML

if '_ui' not in globals():          # (در این سلول ادغام‌شده همیشه تعریف شده‌اند) اگر نشده بود، نسخهٔ ساده جایگزین می‌شود
    def _ui(c1, c2, ic, title, sub=""):
        display(HTML(f"<div dir='rtl' style='font-family:Vazirmatn,Tahoma,sans-serif;background:linear-gradient(110deg,{c2},{c1});color:#fff;border-radius:14px;padding:12px 18px;margin:8px 0'><b>{ic} {title}</b><div style='opacity:.9;font-size:12.5px'>{sub}</div></div>"))
if '_msg' not in globals():
    def _msg(c, text):
        display(HTML(f"<div dir='rtl' style='font-family:Vazirmatn,Tahoma,sans-serif;border-radius:10px;padding:7px 13px;margin:5px 0;border-right:5px solid {c};background:{c}1a;white-space:pre-wrap'>{_hl.escape(text)}</div>"))

# ═══════════════ گزینهٔ Rayegan · دروازهٔ محلی مدل‌های رایگان (فقط وقتی LLM_PROVIDER = "rayegan" ؛ پیش‌فرض Gemini است) ═══════════════
import json, subprocess

RG_REPO = "https://github.com/ssepehrnoush/rayegan"
RG_COMMIT = "f33810cbad300488a437f29029a1b6a5db6ae65a"   # نسخه‌ای که کدش بررسی شد؛ کد روی همین نسخه قفل است تا تغییر بعدیِ مخزن روی کلیدهای شما اجرا نشود
RG_ALLOW_LATEST = False                                   # فقط اگر آگاهانه می‌خواهید آخرین نسخهٔ بررسی‌نشده را بگیرید True کنید
RG_PORT = 8787
RG_DIR = os.path.expanduser("~/rayegan_gw")
RG_CONFIG = {"timeoutMs": 90000, "maxAttempts": 6}        # بدون هیچ کلیدی؛ کلیدها فقط از متغیر محیطیِ همین پردازش می‌روند
RG_SECRETS = ["GROQ_API_KEY", "CEREBRAS_API_KEY", "OPENROUTER_API_KEY", "NVIDIA_API_KEY", "GEMINI_API_KEY", "MISTRAL_API_KEY", "CLOUDFLARE_API_TOKEN", "CLOUDFLARE_ACCOUNT_ID"]
RG_WAIT_SEC = 90
_RG_PROC = globals().get("_RG_PROC")

def _rg_secret(name):
    v = os.environ.get(name, "")
    if not v:
        try:
            from google.colab import userdata
            v = userdata.get(name) or ""
        except Exception:
            v = ""
    return str(v).strip().strip('"').strip("'")

def _rg_get(path, timeout=3):
    try:
        return requests.get(f"http://127.0.0.1:{RG_PORT}{path}", timeout=timeout).json()
    except Exception:
        return None

def _rg_git(*a):
    return subprocess.run(["git", "-C", RG_DIR, *a], capture_output=True, text=True)

def _rg_launch():
    """کد را (قفل‌شده روی RG_COMMIT) می‌گیرد، گیت‌وی را در پس‌زمینه بالا می‌آورد و تا آماده‌شدن صبر می‌کند. وضعیت /status را برمی‌گرداند."""
    global _RG_PROC
    try:
        nv = subprocess.run(["node", "--version"], capture_output=True, text=True).stdout.strip()
        if int(nv.lstrip("v").split(".")[0]) < 18: raise ValueError(nv)
    except Exception:
        raise RuntimeError("Node.js نسخهٔ ۱۸ یا بالاتر روی این Colab پیدا نشد؛ Rayegan بدون آن اجرا نمی‌شود. پیام را برای من بفرستید.")
    if not os.path.isdir(os.path.join(RG_DIR, ".git")):
        r = subprocess.run(["git", "clone", "-q", RG_REPO, RG_DIR], capture_output=True, text=True)
        if r.returncode: raise RuntimeError("دریافت Rayegan ناموفق بود:\n" + r.stderr[-400:])
    if _rg_git("rev-parse", "HEAD").stdout.strip() != RG_COMMIT:
        if _rg_git("checkout", "-q", RG_COMMIT).returncode:
            _rg_git("fetch", "-q", "origin", RG_COMMIT); _rg_git("checkout", "-q", RG_COMMIT)
        if _rg_git("rev-parse", "HEAD").stdout.strip() != RG_COMMIT:
            if not RG_ALLOW_LATEST: raise RuntimeError("نسخهٔ بررسی‌شدهٔ Rayegan قابل‌دریافت نبود و برای امنیت ادامه نمی‌دهم (RG_ALLOW_LATEST = False).")
            _msg("#d99a00", "⚠ آخرین نسخهٔ بررسی‌نشدهٔ Rayegan استفاده می‌شود.")
    open(os.path.join(RG_DIR, "rayegan.json"), "w").write(json.dumps({**RG_CONFIG, "port": RG_PORT}))
    env = dict(os.environ)
    for n in RG_SECRETS:
        v = _rg_secret(n)
        if not v and n == "GEMINI_API_KEY": v = _rg_secret("GOOGLE_API_KEY")      # همان کلید Gemini قبلی، اگر در Secrets دارید
        if v: env[n] = v
    p = subprocess.Popen(["node", "src/cli.js", "--port", str(RG_PORT)], cwd=RG_DIR, env=env, stdout=open(os.path.join(RG_DIR, "rayegan.log"), "ab"), stderr=subprocess.STDOUT, start_new_session=True)
    _RG_PROC = p
    for _ in range(RG_WAIT_SEC):
        time.sleep(1)
        if p.poll() is not None:
            tail = open(os.path.join(RG_DIR, "rayegan.log"), errors="ignore").read()[-500:]
            raise RuntimeError("Rayegan بلافاصله بسته شد:\n" + tail)
        st = _rg_get("/status")
        if st is not None: return st
    raise RuntimeError(f"Rayegan تا {RG_WAIT_SEC} ثانیه آماده نشد (احتمالاً اینترنت یا فیلتر).")

def rg_ensure():
    """اگر گیت‌وی خاموش شده بود (مثلاً Colab ریست شد) دوباره بالا می‌آورد."""
    st = _rg_get("/status", 2)
    return st if st is not None else _rg_launch()

_RG_FA = {"ok": "✅ فعال", "needs-key": "🔑 کلید ندارد", "blocked": "⛔ ۴۰۳ (بسته)", "bad-key": "❌ کلید غلط", "unreachable": "⚠ وصل نشد"}

def _rg_show(st):
    rows = ''.join(f"<tr><td style='padding:3px 10px'>{_hl.escape(str(p.get('id')))}</td><td style='padding:3px 10px'>{_hl.escape(_RG_FA.get(p.get('state'), str(p.get('state'))))}</td>"
                   f"<td style='padding:3px 10px'>{p.get('using', '') if p.get('state') == 'ok' else ''}</td></tr>" for p in st.get("providers", []))
    top = ', '.join(c['id'] for c in st.get("chain", [])[:3]) or '—'
    display(HTML("<div dir='rtl' style='font-family:Vazirmatn,Tahoma,sans-serif;margin:6px 0'>"
                 f"<table style='border-collapse:collapse;direction:ltr;text-align:left'><tr><td style='padding:3px 10px'><b>سرویس</b></td><td style='padding:3px 10px'><b>وضعیت</b></td><td style='padding:3px 10px'><b>مدل</b></td></tr>{rows}</table>"
                 f"<div style='margin-top:6px'>مدل‌های آمادهٔ زنجیره: <b>{st.get('available', 0)}</b> · اولین‌ها: <span dir='ltr'>{_hl.escape(top)}</span></div></div>"))

if LLM_PROVIDER == "rayegan":
    _ui("#e58a00", "#5c3500", "🆓", "مرحله ۲ · دروازهٔ Rayegan (مدل‌های رایگان)", "بدون کلید هم کار می‌کند؛ هر کلید رایگانی که در Colab Secrets بگذارید به زنجیره اضافه می‌شود")
    _old = _rg_get("/status", 2)
    if _old is not None and _RG_PROC is not None and _RG_PROC.poll() is None:      # اجرای دوباره: برای خواندن کلیدهای تازه، گیت‌وی قبلی بسته و دوباره ساخته می‌شود
        _RG_PROC.terminate(); time.sleep(1.5); _old = None
    _st = _old if _old is not None else _rg_launch()
    if _old is not None: _msg("#d99a00", "ℹ یک گیت‌وی از قبل روشن بود و همان استفاده می‌شود (برای خواندن کلیدهای تازه، Runtime را Restart کنید).")
    _rg_show(_st)
    if not _st.get("available"):
        _msg("#e5484d", "❌ هیچ مدلی در دسترس نیست. معمولاً یعنی از این شبکه به سرویس‌های رایگان نمی‌رسد. فایل گزارش: " + os.path.join(RG_DIR, "rayegan.log") + "\nپیام بالا را برای من بفرستید.")
        raise RuntimeError("Rayegan: no model available")
    if not any(p.get("state") == "ok" and not p.get("keyless") for p in _st.get("providers", [])):
        _msg("#d99a00", "ℹ فقط سرویس‌های بدون‌کلید فعال‌اند (سقف ساعتی کم). برای سهمیهٔ بیشتر در Secrets کلید بگذارید: GROQ_API_KEY، MISTRAL_API_KEY، CEREBRAS_API_KEY، OPENROUTER_API_KEY، NVIDIA_API_KEY، CLOUDFLARE_API_TOKEN (+CLOUDFLARE_ACCOUNT_ID)، GEMINI_API_KEY.")
    try:                                                                      # یک تماس واقعی کوچک
        _r = requests.post(f"http://127.0.0.1:{RG_PORT}/v1/chat/completions", json={"model": "auto", "messages": [{"role": "user", "content": "Reply with: ok"}]}, timeout=(5, 150))
    except Exception as _e:
        raise RuntimeError(f"تماس آزمایشی با Rayegan شکست خورد ({type(_e).__name__})") from None
    if _r.status_code != 200:
        _msg("#e5484d", f"❌ تماس آزمایشی ناموفق (HTTP {_r.status_code}): {_r.text[:240]}")
        raise RuntimeError("Rayegan test call failed")
    _who = f"{_r.headers.get('x-rayegan-provider', '?')}/{_r.headers.get('x-rayegan-model', '?')}"
    os.environ['TRADINGAGENTS_LLM_PROVIDER'] = 'openai_compatible'
    os.environ['TRADINGAGENTS_LLM_BACKEND_URL'] = f"http://127.0.0.1:{RG_PORT}/v1"
    os.environ['OPENAI_COMPATIBLE_API_KEY'] = 'rayegan'
    os.environ['TRADINGAGENTS_DEEP_THINK_LLM'] = 'auto'
    os.environ['TRADINGAGENTS_QUICK_THINK_LLM'] = 'auto'
    os.environ['TRADINGAGENTS_MAX_DEBATE_ROUNDS'] = '2'
    os.environ['TRADINGAGENTS_MAX_RISK_ROUNDS'] = '1'
    os.environ['TRADINGAGENTS_LLM_MAX_RETRIES'] = '5'
    DEEP = QUICK = 'auto'; _lvl = '-'
    _msg('#30a46c', f"✅ آماده · همهٔ عامل‌ها از طریق Rayegan (مدل «auto») · تماس آزمایشی را «{_who}» جواب داد. سلول ۲ را اجرا کنید.\n⚠ مدل‌های رایگان ناهمگون‌اند (هر تماس ممکن است مدل دیگری جواب دهد) و از Gemini ضعیف‌تر؛ سیگنال‌ها را با احتیاط بیشتری بخوانید. سقف مصرف هر سرویس در داشبورد http://127.0.0.1:{RG_PORT}/ دیده می‌شود.")

if LLM_PROVIDER != "rayegan":
    _ui("#7c4dff", "#341f7a", "🔑", "مرحله ۲ · کلید Gemini و انتخاب مدل", "کلید از Colab Secrets (نام GOOGLE_API_KEY) خوانده می‌شود؛ اگر نبود در کادر بچسبانید و Enter بزنید")

    # ── تنظیمات قابل‌تغییر (معمولاً دست نزنید) ──
    THINK_TARGET = 'high'          # سقف سطح Thinking: high | medium | low  (high دقیق‌تر ولی کندتر و پرمصرف‌تر است؛ اگر Timeout دیدید medium بگذارید)
    MAX_TESTS_PER_TIER = 2         # حداکثر تعداد مدلی که از هر رده (Pro / Flash / Flash-Lite) آزمایش می‌شود (+ بهترین مدل پایدار آن رده اگر هر دو Preview بودند)؛ سقف مصرف، و تضمین اینکه رد شدن یک رده جلوی آزمایش رده بعدی را نگیرد
    FORCE_DEEP = None              # اختیاری، مثلاً 'gemini-2.5-pro'؛ باید در فهرست واقعی API باشد و آزمایش را رد کند
    FORCE_QUICK = None
    _BASE = "https://generativelanguage.googleapis.com/v1beta"
    _LEVELS = ['minimal', 'low', 'medium', 'high']

    # ── ۱) کلید: Colab Secrets ← در غیر این صورت getpass. کلید هرگز چاپ یا ذخیرهٔ فایلی نمی‌شود ──
    def _read_key():
        k = os.environ.get('GOOGLE_API_KEY', '').strip()
        try:
            from google.colab import userdata
            k = (userdata.get('GOOGLE_API_KEY') or '').strip()
        except Exception:
            pass
        if not k:
            k = ''
        if not k:
            raise RuntimeError('کلید Gemini وارد نشده است؛ GOOGLE_API_KEY را در GitHub Secrets بگذارید.')
        return k

    os.environ['GOOGLE_API_KEY'] = _read_key()
    os.environ['TRADINGAGENTS_LLM_PROVIDER'] = 'google'
    os.environ['TRADINGAGENTS_MAX_DEBATE_ROUNDS'] = '2'
    os.environ['TRADINGAGENTS_MAX_RISK_ROUNDS'] = '1'
    os.environ['TRADINGAGENTS_LLM_MAX_RETRIES'] = '5'

    _S = requests.Session()
    _S.headers.update({'x-goog-api-key': os.environ['GOOGLE_API_KEY'], 'Content-Type': 'application/json'})   # کلید فقط در هدر است، نه در آدرس
    _n_req = [0]

    class _ApiError(Exception):
        def __init__(self, code, text): super().__init__(f"HTTP {code}"); self.code, self.text = code, text

    def _scrub(t):
        k = os.environ.get('GOOGLE_API_KEY', '')
        t = str(t)
        return (t.replace(k, '***') if k else t)[:240]

    # ── ۲) فهرست واقعی مدل‌های همین کلید (یک درخواست GET؛ فقط در خطای شبکه/سرور یک بار دیگر) ──
    def _list_models():
        out, token = [], None
        for _ in range(4):
            params = {'pageSize': 1000}
            if token: params['pageToken'] = token
            r = None
            for attempt in (1, 2):
                _n_req[0] += 1
                try:
                    r = _S.get(f"{_BASE}/models", params=params, timeout=(6, 15))
                except requests.RequestException:
                    if attempt == 2: raise
                    time.sleep(2); continue
                if r.status_code >= 500 and attempt == 1: time.sleep(2); continue
                break
            if r.status_code != 200: raise _ApiError(r.status_code, _scrub(r.text))
            j = r.json(); out += j.get('models', []); token = j.get('nextPageToken')
            if not token: break
        return out

    # ── ۳) نامزدها: فقط مدل‌های Gemini ≥ ۲٫۵ (دارای Thinking) که generateContent را پشتیبانی می‌کنند؛ مدل‌های تصویر/صوت/امبدینگ/آزمایشی حذف می‌شوند ──
    _RX = re.compile(r"^gemini-(\d+(?:\.\d+)?)-(pro|flash-lite|flash)(-.*)?$")
    _SKIP = ('embedding', 'aqa', 'imagen', 'veo', 'tts', 'audio', 'live', 'image', 'robotics', 'computer', 'native', 'learnlm', 'vision', 'custom', '-exp')
    _TIER = {'pro': 3, 'flash': 2, 'flash-lite': 1}

    def _candidates(models):
        res = []
        for m in models:
            name = str(m.get('name', '')).split('/')[-1]; mt = _RX.match(name)
            if not mt or any(s in name for s in _SKIP): continue
            if 'generateContent' not in (m.get('supportedGenerationMethods') or []): continue
            if float(m.get('inputTokenLimit') or 10 ** 9) < 100_000: continue       # گزارش‌های تیم بلندند
            ver = float(mt.group(1))
            if ver < 2.5: continue
            res.append({'name': name, 'ver': ver, 'tier': mt.group(2), 'preview': 'preview' in name})
        res.sort(key=lambda c: c['name'], reverse=True)                              # بین اسنپ‌شات‌های هم‌ردیف، جدیدترین اول
        return res

    def _rank(c, tiers):                                                              # بالاتر = جلوتر؛ نسخهٔ پایدار روی Preview هم‌نسخه مقدم است
        return (tiers.index(c['tier']) if c['tier'] in tiers else 99, -c['ver'], c['preview'])

    # ── ۴) Thinking: همان نگاشتی که کلاینت TradingAgents اعمال می‌کند (نسل ۳ ← thinking_level، نسل ۲٫۵ ← thinking_budget) ──
    def _think_cfg(c, lvl):
        if c['ver'] >= 3:
            return {'thinkingLevel': 'low' if (c['tier'] == 'pro' and lvl == 'minimal') else lvl}
        return {'thinkingBudget': -1 if lvl == 'high' else 0}                          # -1 = پویا (بالاترین)؛ ۲٫۵ Pro خاموش‌شدن Thinking را نمی‌پذیرد

    def _ladder(c):                                                                    # سطح‌های مجازِ مدل از بالا به پایین، تا سقف THINK_TARGET
        base = (['high', 'low'] if c['tier'] == 'pro' else ['high', 'medium', 'low', 'minimal']) if c['ver'] >= 3 else (['high'] if c['tier'] == 'pro' else ['high', 'low'])
        cap = _LEVELS.index(THINK_TARGET) if THINK_TARGET in _LEVELS else 3
        return [l for l in base if _LEVELS.index(l) <= cap] or base[:1]

    # ── ۵) آزمایش کم‌هزینه: برای هر مدل یک درخواست کوچک (حداکثر ۶۴ توکن)؛ فقط اگر خودِ Thinking رد شد، یک بار با سطح پایین‌تر ──
    _FA = {'OK': '✅ پاسخ داد', 'THROTTLED': '⏳ محدودیت لحظه‌ای ۴۲۹', 'QUOTA_DAY': '⛔ سهمیهٔ روزانه پر است', 'NO_QUOTA': '⛔ سهمیهٔ این مدل برای کلید شما صفر است',
           'NOT_FOUND': '✖ مدل پیدا نشد (404)', 'FORBIDDEN': '⛔ دسترسی/منطقه (403)', 'THINK_REJECT': '↘ سطح Thinking رد شد', 'BAD_REQUEST': '✖ درخواست نامعتبر (400)',
           'SERVER': '⚠ خطای سرور (5xx)', 'TIMEOUT': '⚠ Timeout', 'NETWORK': '⚠ خطای شبکه', 'AUTH': '❌ کلید نامعتبر/منقضی'}
    _probe, _log = {}, []

    def _classify(r):
        sc, low = r.status_code, (r.text or '').lower()
        if sc == 200: return 'OK'
        if sc == 429:                                    # «limit: 0» = بسته‌بودن مدل برای این کلید؛ بقیهٔ ۴۲۹ها محدودیت موقت‌اند، نه مدرکِ دسترسی کامل
            return 'NO_QUOTA' if re.search(r'limit: 0\b', low) else 'QUOTA_DAY' if 'perday' in low else 'THROTTLED'
        if sc == 400: return 'THINK_REJECT' if 'thinking' in low else 'AUTH' if (('api key' in low or 'api_key' in low) and any(w in low for w in ('invalid', 'not valid', 'expired'))) else 'BAD_REQUEST'
        if sc == 401: return 'AUTH'
        if sc == 403: return 'FORBIDDEN'
        if sc == 404: return 'NOT_FOUND'
        return 'SERVER' if sc >= 500 else 'BAD_REQUEST'

    def _try(c, lvl):
        k = (c['name'], lvl)
        if k in _probe: return _probe[k]
        body = {'contents': [{'parts': [{'text': 'Reply with: ok'}]}], 'generationConfig': {'maxOutputTokens': 64, 'thinkingConfig': _think_cfg(c, lvl)}}
        _n_req[0] += 1
        try: st = _classify(_S.post(f"{_BASE}/models/{c['name']}:generateContent", json=body, timeout=(6, 25)))
        except requests.Timeout: st = 'TIMEOUT'
        except requests.RequestException: st = 'NETWORK'
        _probe[k] = st; _log.append((c['name'], lvl, st))
        if st == 'AUTH': raise _ApiError(401, 'API key rejected')
        return st

    def _shortlist(cands):                                # از هر رده: بهترین‌ها + (اگر همه Preview بودند) بهترین مدل پایدار، چون Previewها اغلب سهمیهٔ صفر دارند
        keep, tiers = set(), {}
        for c in cands: tiers.setdefault(c['tier'], []).append(c)
        for lst in tiers.values():
            top = lst[:MAX_TESTS_PER_TIER]; keep.update(c['name'] for c in top)
            if all(c['preview'] for c in top):
                stable = next((c for c in lst if not c['preview']), None)
                if stable: keep.add(stable['name'])
        return [c for c in cands if c['name'] in keep]

    def _choose(cands, levels_of):
        soft = None
        for c in _shortlist(cands):
            for lvl in levels_of(c)[:2]:
                st = _try(c, lvl)
                if st == 'OK': return c, lvl, st
                if st == 'THROTTLED' and soft is None: soft = (c, lvl, st)
                if st != 'THINK_REJECT': break
        return soft or (None, None, None)                # اگر هیچ مدلی OK نبود، بهترین مدلِ «محدودیت لحظه‌ای» (نه «بدون دسترسی»)

    # ── ۶) اجرا: فهرست ← DEEP ← QUICK ──
    try:
        _all = _list_models()
        _cands = _candidates(_all)
        if not _cands: raise RuntimeError('هیچ مدل Gemini ≥ ۲٫۵ با پشتیبانی generateContent در این حساب پیدا نشد')
        _byname = {c['name']: c for c in _cands}

        _dc = sorted(_cands, key=lambda c: _rank(c, ['pro', 'flash', 'flash-lite']))                   # DEEP: قوی‌ترین رده (Pro) و جدیدترین نسل
        if FORCE_DEEP:
            if FORCE_DEEP in _byname: _dc = [_byname[FORCE_DEEP]]
            else: _msg('#d99a00', f'⚠ FORCE_DEEP «{FORCE_DEEP}» در فهرست واقعی API نیست؛ نادیده گرفته شد.')
        D, lvl, d_st = _choose(_dc, _ladder)
        if not D: raise RuntimeError('هیچ مدل Deep قابل‌استفاده‌ای پیدا نشد (جزئیات در فهرست آزمایش‌ها)')

        _qt = ['flash', 'flash-lite'] if D['tier'] == 'pro' else ['flash-lite', 'flash']               # QUICK: سریع‌تر و سبک‌تر از DEEP
        _qc = sorted([c for c in _cands if c['name'] != D['name']], key=lambda c: _rank(c, _qt))
        _qc = [c for c in _qc if c['tier'] in _qt]
        if FORCE_QUICK:
            if FORCE_QUICK in _byname: _qc = [_byname[FORCE_QUICK]]
            else: _msg('#d99a00', f'⚠ FORCE_QUICK «{FORCE_QUICK}» در فهرست واقعی API نیست؛ نادیده گرفته شد.')
        Q, _, q_st = _choose(_qc, lambda c: [lvl])                                                      # QUICK با همان سطح Thinking (متغیر محیطی یکی است)
        if not Q: Q, q_st = D, d_st
    except _ApiError as e:
        if e.code in (400, 401, 403): _msg('#e5484d', f'❌ کلید پذیرفته نشد یا دسترسی ندارد ({e}). کلید را در aistudio.google.com بررسی کنید. {e.text[:160]}')
        else: _msg('#e5484d', f'❌ پاسخ غیرمنتظرهٔ API ({e}): {e.text[:160]}')
        raise RuntimeError('Gemini key/model check failed') from None
    except RuntimeError as e:
        _msg('#e5484d', f'❌ {e}')
        raise RuntimeError(str(e)) from None
    except Exception as e:
        _msg('#e5484d', f'❌ چک کلید/مدل انجام نشد ({type(e).__name__})؛ اتصال را بررسی و سلول را دوباره اجرا کنید')
        raise RuntimeError('Gemini connection/model check failed') from None
    finally:
        _S.headers.pop('x-goog-api-key', None)           # کلید از نشست HTTP پاک می‌شود؛ فقط متغیر محیطیِ موردنیاز TradingAgents می‌ماند

    DEEP, QUICK, _lvl = D['name'], Q['name'], lvl
    os.environ['TRADINGAGENTS_DEEP_THINK_LLM'] = DEEP
    os.environ['TRADINGAGENTS_QUICK_THINK_LLM'] = QUICK
    os.environ['TRADINGAGENTS_GOOGLE_THINKING_LEVEL'] = _lvl

    # ── ۷) گزارش شفاف ──
    _rows = ''.join(f"<tr><td style='padding:3px 10px'>{_hl.escape(n)}</td><td style='padding:3px 10px'>{_hl.escape(l)}</td><td style='padding:3px 10px'>{_hl.escape(_FA.get(s, s))}</td></tr>" for n, l, s in _log)
    display(HTML("<div dir='rtl' style='font-family:Vazirmatn,Tahoma,sans-serif;margin:6px 0'>"
                 f"<table style='border-collapse:collapse;direction:ltr;text-align:left'><tr><td style='padding:3px 10px'><b>DEEP</b> (مدیران)</td><td><b>{_hl.escape(DEEP)}</b></td></tr>"
                 f"<tr><td style='padding:3px 10px'><b>QUICK</b> (بقیهٔ عامل‌ها)</td><td><b>{_hl.escape(QUICK)}</b></td></tr>"
                 f"<tr><td style='padding:3px 10px'><b>Thinking</b></td><td><b>{_hl.escape(_lvl)}</b></td></tr></table>"
                 f"<details style='margin-top:6px'><summary>🔬 آزمایش‌ها ({_n_req[0]} درخواست شامل فهرست مدل‌ها)</summary><table style='direction:ltr;text-align:left;font-size:12.5px'>{_rows}</table></details></div>"))
    _soft = [n for n, s in ((DEEP, d_st), (QUICK, q_st)) if s == 'THROTTLED']
    if _soft: _msg('#d99a00', f"⚠ مدل‌های {', '.join(_soft)} فقط به‌خاطر محدودیت لحظه‌ایِ ۴۲۹ انتخاب شدند (مدل دیگری جواب سالم نداد). چند دقیقه صبر کنید و سلول را دوباره اجرا کنید؛ سلول ۲ بدون آن هم تلاش مجدد خودکار دارد.")
    try:                                                  # فقط اطلاعاتی: آیا کلاینت Google پروژه Thinking را می‌شناسد؟
        _gc = open('tradingagents/llm_clients/google_client.py', encoding='utf-8', errors='ignore').read()
        if 'thinking_level' not in _gc: _msg('#d99a00', 'ℹ کلاینت Google این نسخهٔ TradingAgents ظاهراً thinking_level را نمی‌شناسد؛ سطح Thinking ممکن است اعمال نشود (بی‌ضرر).')
    except Exception:
        pass
    _msg('#30a46c', f"✅ آماده · مدیران: {DEEP} · بقیه: {QUICK} · سطح تفکر: {_lvl}. سلول ۲ را اجرا کنید (۵ تا ۱۰ دقیقه؛ در حالت ALL چند دقیقه بیشتر).")


# ======================= موتور تحلیل =======================
import datetime as dt, time
import warnings; warnings.filterwarnings("ignore")      # v21: هشدارهای Pandas4Warning/FutureWarning وسط خروجی نیایند
import numpy as np, pandas as pd, yfinance as yf

# ================= ظاهر خروجی (v9): هر سلول یک رنگ، کادرهای گرد، فونت وزیرمتن =================
import builtins, threading, re, html as _hl
from IPython.display import display, Pretty, HTML, clear_output
_print0 = builtins.print
_STEPS = {1: ("🧩", "#0f9d8a", "#073f38"), 2: ("🔑", "#8b5cf6", "#2e1065"), 3: ("🧠", "#3b82f6", "#172554"), 4: ("📒", "#06b6d4", "#083344")}
_ACC = {"c": "#3b82f6"}
_CSS = """<style>
@import url('https://fonts.googleapis.com/css2?family=Vazirmatn:wght@400;600;800&display=swap');
@keyframes taShine{0%{background-position:0% 50%}100%{background-position:200% 50%}}
.ta{direction:rtl;font-family:Vazirmatn,Tahoma,system-ui,sans-serif;line-height:1.8;font-size:14px;text-align:right}
.ta *{box-sizing:border-box}
.ta-hd{border-radius:14px;padding:12px 18px;margin:8px 0;color:#fff;box-shadow:0 2px 10px rgba(0,0,0,.28)}
.ta-hd b{font-size:19px;font-weight:800}.ta-hd small{display:block;opacity:.9;font-size:12.5px}
.ta-note{border-radius:10px;padding:7px 13px;margin:5px 0;border-right:5px solid var(--c);background:var(--b);white-space:pre-wrap;unicode-bidi:plaintext}
.ta-flex{display:flex;gap:12px;flex-wrap:wrap;margin:8px 0}
.ta-card{flex:1 1 290px;border:1px solid rgba(128,128,128,.4);background:rgba(128,128,128,.09);border-radius:14px;overflow:hidden}
.ta-card .ph{color:#fff;padding:9px 14px;font-weight:800;font-size:15.5px}
.ta-card .ps{padding:6px 14px 0;font-size:12.5px;opacity:.85}
.ta-card table{width:100%;border-collapse:collapse;margin:6px 0 4px}
.ta-card td{padding:6px 14px;border-top:1px solid rgba(128,128,128,.25)}
.ta-card td.v{direction:ltr;text-align:left;font-weight:800;font-size:17px;font-variant-numeric:tabular-nums;white-space:nowrap}
.ta-card td.l small{opacity:.7}
.ta-card tr.sl td.v{color:#e5484d}.ta-card tr.tp td.v{color:#30a46c}
.ta-card .pf{padding:6px 14px 11px;font-size:12.5px;opacity:.88}
.ta-strip{border-radius:10px;padding:6px 13px;margin:6px 0;background:rgba(128,128,128,.14);font-size:13px;display:flex;gap:6px 16px;flex-wrap:wrap}
.ta details{border:1px solid rgba(128,128,128,.38);border-radius:10px;margin:6px 0;background:rgba(128,128,128,.07)}
.ta summary{cursor:pointer;padding:8px 14px;font-weight:600}
.ta .bd{padding:2px 14px 12px;white-space:pre-wrap;unicode-bidi:plaintext;font-size:13px}
.ta table.tb{border-collapse:collapse;margin:4px 0 12px}.ta table.tb td,.ta table.tb th{padding:4px 12px;border:1px solid rgba(128,128,128,.35);text-align:center}
.ta-chip{display:inline-block;background:rgba(0,0,0,.26);border-radius:999px;padding:1px 11px;margin:3px 0 0 6px;font-size:12.5px}
</style>"""
def _h(x): return _hl.escape(str(x))
def ui(htm, out=True):
    o = HTML(_CSS + "<div class='ta'>" + htm + "</div>")
    return display(o) if out else o
def _note(txt, c): return f"<div class='ta-note' style='--c:{c};--b:{c}1a'>{_h(txt)}</div>"
def ui_step(n, title, sub=""):
    ic, c1, c2 = _STEPS[n]; _ACC["c"] = c1
    ui(f"<div class='ta-hd' style='background:linear-gradient(110deg,{c2},{c1})'><b>{ic} مرحله {n} · {_h(title)}</b>" + (f"<small>{_h(sub)}</small>" if sub else "") + "</div>")
def ui_fold(title, body, open_=False):
    ui(f"<details{' open' if open_ else ''}><summary>{_h(title)}</summary><div class='bd'>{_h(body)}</div></details>")
_PC = {"⛔": "#e5484d", "❌": "#e5484d", "⚠": "#d99a00", "✅": "#30a46c", "ℹ": "#2b8fd6", "🔄": "#2b8fd6", "⏹": "#2b8fd6", "🏆": "#d4af37", "🥇": "#d4af37", "👑": "#d4af37",
       "🔎": "#06b6d4", "🧪": "#14b8a6", "📊": "#0ea5e9", "🏛": "#8b5cf6", "👔": "#6366f1", "🧠": "#6366f1", "📲": "#22c55e", "💸": "#14b8a6", "⏱": "#3b82f6",
       "🔧": "#64748b", "💬": "#a855f7", "📰": "#0891b2", "🛠": "#0d9488", "🎓": "#c084fc", "📚": "#0284c7", "🗒": "#64748b"}
_CSS += """<style>
.tb-t{font-weight:800;margin:10px 0 4px;font-size:14.5px}
.tb-w{overflow-x:auto;border-radius:16px;border:1px solid rgba(128,128,128,.32);box-shadow:0 6px 20px rgba(0,0,0,.22);margin:4px 0 12px}
.ta table.tb{border-collapse:separate;border-spacing:0;width:100%;min-width:600px;margin:0}
.ta table.tb th{position:sticky;top:0;background:linear-gradient(120deg,#0f172a,#1d4ed8);color:#fff;padding:9px 8px;font-size:12px;font-weight:700;border:0;line-height:1.5}
.ta table.tb th.rh{position:sticky;right:0;background:rgba(15,23,42,.92);color:#e2e8f0;text-align:right;font-size:12.5px;min-width:132px;z-index:2}
.ta table.tb th.rh0{background:linear-gradient(120deg,#0f172a,#1d4ed8)}
.ta table.tb td{padding:6px 7px;border:0;border-top:1px solid rgba(128,128,128,.16);text-align:center;font-size:12.5px;min-width:96px}
.ta table.tb tr:nth-child(even) td{background-color:rgba(128,128,128,.06)}
.ta table.tb td.hm{padding:5px 7px}.ta table.tb td.na{opacity:.35}
.hm .hn{font-size:10.5px;opacity:.78;direction:ltr}.hm .hw{height:5px;border-radius:3px;background:rgba(0,0,0,.30);overflow:hidden;margin:3px 0}.hm .hw i{display:block;height:100%;background:#fff;opacity:.92}
.hm .hv{display:flex;justify-content:space-between;gap:6px;font-size:12px;direction:ltr}.hm .hv span{font-weight:800}
.al-wrap{border-radius:18px;border:1px solid rgba(128,128,128,.35);background:linear-gradient(160deg,rgba(59,130,246,.12),rgba(139,92,246,.06));padding:12px 14px;margin:8px 0}
.al-top{display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:4px 12px;margin-bottom:7px;font-weight:700}
.al-bar{height:10px;border-radius:99px;background:rgba(128,128,128,.25);overflow:hidden}.al-bar i{display:block;height:100%;border-radius:99px;background:linear-gradient(90deg,#06b6d4,#3b82f6,#8b5cf6)}
.al-eta{font-size:12.5px;opacity:.9;margin-top:6px}
.al-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:8px;margin-top:10px}
.al-t{border-radius:12px;padding:8px 10px;border:1px solid rgba(128,128,128,.3);background:rgba(128,128,128,.08);border-right:4px solid var(--c);font-size:12.5px;line-height:1.55}
.al-t b{font-size:14px}.al-t .s{opacity:.88}.al-t .m{height:5px;border-radius:3px;background:rgba(128,128,128,.28);margin-top:5px;overflow:hidden}.al-t .m i{display:block;height:100%;background:var(--c)}
.al-t.win{box-shadow:0 0 18px var(--c);background:rgba(212,175,55,.15)}.al-t.scan{animation:alPulse 1.2s ease-in-out infinite}
@keyframes alPulse{0%,100%{opacity:1}50%{opacity:.55}}
.ag-st{display:flex;flex-wrap:wrap;gap:6px;margin-top:9px}.ag-st span{border-radius:999px;padding:3px 11px;font-size:12.5px;background:rgba(128,128,128,.2)}
.ag-st span.ok{background:rgba(48,164,108,.30)}.ag-st span.go{background:rgba(59,130,246,.35);animation:alPulse 1.2s ease-in-out infinite}
.ag-ev{margin-top:8px;font-size:12px;opacity:.85;white-space:pre-wrap;unicode-bidi:plaintext}
</style>"""
_HEAT = re.compile(r"^n=(\d+)\s*·\s*(\d+)%\s*·\s*([+-]?\d+(?:\.\d+)?)R$")
def _cell(v):
    s = str(v).strip(); m = _HEAT.match(s)
    if m:
        n, wr, E = int(m.group(1)), int(m.group(2)), float(m.group(3)); al = min(abs(E), 1.0) * .55 + .10
        col = "48,164,108" if E > 0 else "229,72,77" if E < 0 else "138,143,152"; op = "" if n >= 5 else ";opacity:.7"
        return f"<td class='hm' style='background:rgba({col},{al:.2f}){op}'><div class='hn'>n={n}</div><div class='hw'><i style='width:{min(wr, 100)}%'></i></div><div class='hv'><b>{wr}%</b><span>{E:+.2f}R</span></div></td>"
    if s in ("—", "-", ""): return "<td class='na'>—</td>"
    return f"<td>{_h(s)}</td>"
def ui_table(df, title=""):
    head = "".join(f"<th>{_h(c)}</th>" for c in df.columns)
    rows = "".join("<tr><th class='rh'>" + _h(i) + "</th>" + "".join(_cell(v) for v in r) + "</tr>" for i, r in zip(df.index, df.values))
    ui((f"<div class='tb-t'>{_h(title)}</div>" if title else "") + f"<div class='tb-w'><table class='tb'><tr><th class='rh0'></th>{head}</tr>{rows}</table></div>")
def print(*a, sep=" ", end="\n", **k):      # همهٔ پیام‌ها کادر رنگی می‌شوند: قرمز ⛔❌ | زرد ⚠ | سبز ✅ | آبی ℹ🔄⏹ | بقیه رنگ همین مرحله
    txt = sep.join(str(x) for x in a)
    if k.get("file") is not None or not txt.strip() or threading.current_thread() is not threading.main_thread(): return _print0(*a, sep=sep, end=end, **k)
    t = txt.strip("\n"); f = t.lstrip()[:1]
    c = _PC.get(f) or _ACC["c"]
    try: ui(_note(t, c))
    except Exception: _print0(*a, sep=sep, end=end, **k)

# --- رفع معطلی ۶۰ ثانیه‌ای Reddit (خطای 429): فقط یک تلاش سریع؛ شکست = رد شدن فوری (تحلیلگر سنتیمنت خودش «Reddit در دسترس نیست» را می‌پذیرد) ---
import logging, threading
try:
    import tradingagents.dataflows.vendors.reddit as _rd
    if not getattr(_rd, "_fast_patched", False):
        _orig_rss = _rd._fetch_subreddit_rss
        def _fast_rss(ticker, sub, limit, timeout, _retry=True):
            return _orig_rss(ticker, sub, limit, min(timeout, 4.0), _retry=False)   # بدون backoff و sleep
        _rd._fetch_subreddit_rss = _fast_rss
        _rd._fast_patched = True
    logging.getLogger("tradingagents.dataflows.vendors.reddit").setLevel(logging.ERROR)   # لاگ ۴۲۹ نمایش داده نشود
    logging.getLogger("tradingagents.dataflows.router").setLevel(logging.ERROR)           # هشدار بی‌اثر «fred not configured» (دادهٔ اقتصاد کلان اختیاری است)
except Exception as _e:
    print("هشدار: پچ Reddit اعمال نشد (سلول ۱ را اجرا کرده‌اید؟):", str(_e)[:150])
try:   # StockTwits هم اگر جواب نداد بیش از ۴ ثانیه معطل نکند (پیش‌فرض ۱۰)؛ داده‌ای که می‌رسد دست‌نخورده است
    import functools, tradingagents.agents.analysts.sentiment_analyst as _sa
    if not getattr(_sa, "_fast_patched", False):
        _sa.fetch_stocktwits_messages = functools.partial(_sa.fetch_stocktwits_messages, timeout=4.0); _sa._fast_patched = True
except Exception:
    pass

# ================= تنظیمات (فقط همین بخش را عوض کنید) =================
# ---- دارایی و حالت اجرا ----
ASSET = os.environ.get("TA_ASSET", "ALL") or "ALL"
ALL_ASSETS = ["BTC", "ETH", "DOGE", "SHIB", "XRP", "SOL", "BNB", "ADA", "TRX", "LINK", "AVAX", "EURUSD", "GBPUSD", "Gold", "US30", "NAS100", "USOIL"]  # دارایی‌هایی که ALL اسکن می‌کند؛ هر کدام را نمی‌خواهید حذف کنید
USE_AGENTS = os.environ.get("TA_AGENTS", "1") != "0"
MODE = "bold"                                 # careful | balanced | bold (جرأت بیشتر در ورود)
TZ_HOURS = 3.5                                # اختلاف ساعت شما با UTC (ایران = 3.5)
MAX_AGE_MIN = 25                              # داده قدیمی‌تر از این (دقیقه) = بازار بسته؛ سیگنال نمی‌دهد
# ---- ورود، حد ضرر و تارگت ----
SL_ATR = 0.8                                  # حد ضرر = این × ATR کندل ۱۵م
MAX_ENTRY_DIST = 0.4                          # ورود حداکثر این × ATR از قیمت زنده
MIN_PULL = 0.2                                # ورود حداقل این × ATR بهتر از قیمت (لیمیت واقعی)
ORDER_TTL = 6                                 # اعتبار سفارش لیمیت (کندل ۵م)؛ پر نشد = لغو
MAX_HOLD = 24                                 # سقف نگه‌داری بعد از فیل (کندل ۵م)
TP1_FRAC = 0.5                                # سهم حجمی که در TP1 بسته می‌شود
SAFE_R1, SAFE_R2 = 1.5, 3.0                   # 🎯 کارت اصلی: TP1 و TP2 به واحد R
RUN_R1, RUN_R2 = 3.0, 5.0                     # 🚀 کارت رانر: TP1 و TP2 به واحد R
MIN_RR = 3.0                                  # حداقل ریوارد تارگت نهایی
BE_BUFFER_ATR = 0.1                           # بعد از TP1، SL بقیه این × ATR آن‌طرف‌تر از ورود
SL_BUFFER_ATR = 0.3                           # فاصلهٔ امن SL پشت استخر نقدینگی (ATR)
MAX_RISK_ATR = 1.3                            # SL دورتر از این × ATR = پرچم ریسک
STOP_HUNT_AWARE = True                        # SL پشت جاهایی که عموم استاپ می‌گذارند
SL_SEEK_ATR = 0.5                             # اگر استخر استاپ تا این فاصله (ATR) پشت SL بود، SL پشت آن برود
SL_MAX_MOVES = 1                              # حداکثر دفعات جابه‌جایی SL
ROUND_STEP = {"BTC": 1000, "ETH": 50, "DOGE": 0.005, "SHIB": 0.0000001, "EURUSD": 0.005, "GBPUSD": 0.005, "Gold": 10, "US30": 100, "NAS100": 100, "USOIL": 1.0}  # گام «عدد رند» هر دارایی
SWEEP_LOOKBACK = 18                           # سوییپ‌های این‌قدر کندل ۵م اخیر بررسی می‌شوند
KEEP_SIZE = True                              # True = حجم خودکار کم نمی‌شود (فقط پرچم می‌آید)
RUNNER_ON = True                              # True = دو کارت: 🎯 اصلی و 🚀 رانر
# ---- اسپرد و کارمزد ----
SPREAD_ON = True                              # جابه‌جایی SL/TP فروش با اسپرد
SPREADS = {"Gold": 0.30, "USOIL": 0.06, "BTC": 0.0, "ETH": 0.0, "DOGE": 0.0, "EURUSD": 0.00010, "GBPUSD": 0.00012, "US30": 0.0, "NAS100": 0.0}  # اسپرد بروکر شما برای هر دارایی
SPREAD_MIN_MULT = 5.0                         # SL حداقل این × اسپرد
FEE_RATE = {k_: 0.0003 for k_ in ("BTC", "ETH", "DOGE", "SHIB", "XRP", "SOL", "BNB", "ADA", "TRX", "LINK", "AVAX")}  # کارمزد هر سمت در بک‌تست (کریپتو ≈ ۰٫۰۳٪)
# ---- استراتژی‌ها و بک‌تست ----
STRAT_ON = True                               # سیگنال فقط از استراتژی‌های کتابچه
STRAT_REQUIRED = True                         # True = بدون استراتژی فعال سیگنال نمی‌دهد
STRAT_DAYS = 58                               # روزهای بک‌تست در حالت تک‌دارایی
STRAT_DAYS_ALL = 14                           # روزهای بک‌تست در حالت ALL (کمتر، تا اسکن سریع بماند)
ALL_REPEAT_HOURS = 3                           # ALL: دارایی‌ای که در این چند ساعت اخیر سیگنال گرفته، کمی عقب می‌افتد (جلوگیری از تکرارِ همیشگی یک ارز)
ALL_REPEAT_PEN = 0.15                          # مقدار جریمه (هم‌مقیاس امتیاز بک‌تست / آمادگی)
ALL_FALLBACK = _FALLBACK
STRAT_LAB_HOURS = 12                          # کش نتیجهٔ بک‌تست (ساعت)
STRAT_MIN_N = 12                              # زیر این تعداد معامله = «کم‌نمونه»
STRAT_SHRINK = 10                             # انقباض آمار هر سشن به سمت آمار کل
STRAT_RANK = "mix"                            # ملاک امتیاز: expectancy | winrate | mix
STRAT_FRESH_MIN = 45                          # استراتژی تا این‌قدر دقیقه بعد از فعال‌شدن «فعال» است
STRAT_PIN_GRACE = 30                          # مهلت اضافهٔ اعتبار استراتژی انتخاب‌شده (دقیقه)
STRAT_TEAM_W = 0.25                           # وزن رأی ۱۴ عضو در انتخاب استراتژی
STRAT_GOLD_SCORE = 0.10                       # حداقل امتیاز بک‌تست برای 🥇 GOLD
STRAT_NEG_SCORE = -0.05                       # امتیاز زیر این = «بک‌تست ضعیف» (پرچم ریسک)
STRAT_DESK_LLM = True                         # ۱۴ عضو با یک تماس مدل استراتژی را انتخاب کنند
BT_LIMIT_ENTRY = True                         # بک‌تست با ورود لیمیت واقعی
OOS_FRAC = 0.4                                # سهم آخرِ داده برای آزمون خارج‌ازنمونه
OOS_MIN_N = 5                                 # زیر این تعداد معامله، OOS قضاوت نمی‌شود
EXAM_ON = True                                # آزمون تیم با موقعیت‌های واقعی گذشته
EXAM_CASES = 10                               # تعداد موقعیت‌های آزمون
EXAM_REFRESH_H = 12                           # آزمون هر چند ساعت تکرار شود
# ---- تیم عامل‌ها و مدل ----
AGENT_TIMEOUT_MIN = 30                        # سقف زمان کل تیم (دقیقه)
DEBATE_ROUNDS = 2                             # دور بحث خوش‌بین/بدبین
RISK_ROUNDS = 1                               # دور بحث ریسک
AGENT_RETRIES = 2                             # تلاش مجدد تیم هنگام خطا (مثلاً ۴۲۹)
AGENT_RETRY_WAIT = 40                         # صبر بین تلاش‌ها (ثانیه)
AGENT_MAX_AGE = 60                            # تحلیل عامل‌ها قدیمی‌تر از این (دقیقه) = هشدار
MAX_TOOL_ROUNDS = 10                          # سقف دفعات ابزار هر تحلیلگر
NEWS_LIMIT = 15                               # حداکثر خبر در تحلیل
LLM_CALL_TIMEOUT = 120                        # سقف انتظار هر تماس مدل (ثانیه)
HEARTBEAT_SEC = 30                            # هر چند ثانیه «در حال کارم» چاپ شود
SHOW_DETAILS = True                           # گزارش تحلیلگران و تصمیم مدیر زیر سیگنال
ALLOW_TECH_FALLBACK = False                   # True = اگر عامل‌ها جواب ندادند، سیگنال فقط-تکنیکال
DESK_ON = True                                # میز مناظره تکنیکال × بنیادی + مدیر سبد
DESK_ROUNDS = 1                               # دور انتقاد متقابل میز
CEO_ON = True                                 # مدیرعامل: حکم نهایی GO / WAIT / NO
COUNCIL_ON = True                             # شورای ۱۴ نفره رأی‌دهندهٔ جهت (فعال: رأی هر سبک زیر هر سیگنال نمایش داده می‌شود)
COUNCIL_LLM = True                            # یک تماس مدل برای شورا
COUNCIL_REFRESH_MIN = 20                      # کش بخش مدلیِ شورا (دقیقه)
COUNCIL_LEAN_NET = 1.2                        # تیم «نگه‌دار» گفت و شورا قوی‌تر از این بود: جهت از شورا
ICT_AS_MEMBER = True                          # ایجنت ICT/SMC فقط یکی از اعضای شورا (بدون وتو)
CHAIR_ON = True                               # رئیس ماهانهٔ شورا
CHAIR_W = 1.25                                # وزن رأی رئیس
CHAIR_MIN_POS = 1                             # حداقل ترید مثبت برای رئیس‌شدن
ECON_ON = True                                # اقتصاددان ارشد (۱ تماس مدل)
ECON_REFRESH_MIN = 60                         # کش نتیجهٔ اقتصاددان (دقیقه)
# ---- فیلترها و پرچم‌های ریسک ----
MIN_ALIGN = 2                                 # حداقل هم‌جهتی تایم‌فریم‌ها
DRIFT_WARN_ATR = 1.0                          # هشدار اگر قیمت حین تحلیل بیش از این × ATR حرکت کرد
SMC_GATES = True                              # موتور ساختار + گیت‌ها + SL کنار نقدینگی
SMC_AGENT = True                              # ایجنت ICT/SMC (۱ تماس مدل)
SMC_STRICT = True                             # True = حکم «نه/صبر» سیگنال را رد می‌کند
SMC_REQUIRED = True                           # اگر ایجنت ICT/SMC اجرا نشد، سیگنال نده
SMC_REFRESH_MIN = 10                          # تازه‌سازی حکم ایجنت (دقیقه)
SMC_MIN_GAP_MIN = 3                           # حداقل فاصلهٔ دو تماس ایجنت (دقیقه)
SMC_MIN_CONF = 0                              # حداقل اطمینان حکم GO (۰ = خاموش)
IMPULSE_ATR = 0.8                             # حرکت تند خلاف جهت (ATR) = ورود ممنوع
IMPULSE_BARS = 6                              # طول بازهٔ بررسی حرکت تند (کندل ۵م)
IMPULSE_VETO_ATR = 1.3                        # حرکت تند بزرگ‌تر از این = رد
PREPOOL_GATE = True                           # پرچم: اول سوییپ نقدینگی، بعد ورود
PREPOOL_ATR = 1.5                             # «نزدیک» یعنی تا این فاصله (ATR)
RSI_15M_EXT = 72                              # پرچم دنبال‌کردن حرکت کشیده (RSI ۱۵م)
RSI_1H_EXT = 75                               # همین قاعده روی RSI ساعتی
CHASE_GATE = True                             # پرچم دنبال‌کردن حرکت / ریتریس بعد از ۳R
CHASE_EXT_ATR = 2.0                           # کشیدگی از EMA20 (ATR) که «دنبال‌کردن» حساب می‌شود
CHASE_HOURS = 6                               # تازگی تارگت ترید قبلی (ساعت)
CHASE_NEAR_ATR = 0.6                          # نزدیکی به آن تارگت (ATR)
PROFILE_ON = True                             # VWAP روزانه و پروفایل حجم
REGIME_ON = True                              # رژیم بازار (روند / رنج)
SMT_ON = True                                 # واگرایی SMT با دارایی همبسته
DERIV_ON = True                               # فاندینگ و OI (BTC / ETH)
AUTO_BASIS = True                             # طلا/داو/نزدک/نفت: اختلاف فیوچرز با چارت خودکار
ASSET_HOURS = {"USOIL": (7.0, 20.0), "EURUSD": (7.0, 17.0), "GBPUSD": (7.0, 17.0)}  # ساعات پرنقدینگی (UTC)؛ بیرونش پرچم نرم
HIDE_RISKY = False                            # True = کارت‌های پرریسک کم‌رنگ
HORIZON_ON = True                             # آمار هندسهٔ SL/TP روی ۳ روز اخیر در کارت
# ---- رده‌بندی سیگنال ----
TIERS_ON = True                               # True = رده‌بندی: GOLD | STANDARD | HIGH-RISK
GOLD_MIN = 68                                 # حداقل امتیاز GOLD
STD_MIN = 50                                  # زیر این امتیاز = HIGH-RISK
GOLD_MAX_FLAGS = 1                            # حداکثر پرچم نرم قابل‌تحمل برای GOLD
CALIB_MIN = 10                                # حداقل ترید ثبت‌شده برای نمایش نرخ برد واقعی هر رده
# ---- خبر و اعلان ----
NEWS_GUARD_ON = True                          # تقویم اقتصادی در هر تحلیل چک شود
NEWS_WINDOW_MIN = 30                          # خبر مهم تا این‌قدر دقیقهٔ دیگر = اخطار
NEWS_AFTER_MIN = 15                           # تا این‌قدر دقیقه بعد از خبر هم «منطقهٔ خبر» است
NEWS_REFRESH_MIN = 10                         # تازه‌سازی تقویم (دقیقه)
NOTIFY_TOPIC = os.environ.get("NTFY_TOPIC", "").strip()
NOTIFY_NEWS = True                            # اعلان ۳۰ و ۵ دقیقه قبل از خبر مهم
# ---- انضباط و هم‌جهتی دارایی‌ها ----
DAILY_STOP_R = 3.0                            # ضرر امروز بدتر از این (R) = ورود جدید پرریسک
MAX_LOSS_STREAK = 3                           # بعد از این‌قدر باخت پشت‌سرهم هشدار استراحت
CORR_ON = True                                # هشدار سیگنال‌های هم‌جهتِ چند دارایی
CORR_HOURS = 8                                # بازهٔ بررسی (ساعت)
SHOCK_ON = True                               # هشدار شوک سراسری بازار
SHOCK_PCT = 1.5                               # حداقل حرکت روزانه برای شمارش (٪)
SHOCK_MIN = 4                                 # حداقل تعداد دارایی هم‌جهت
# ---- قیمت زنده ----
PRICE_SOURCE = "auto"                         # auto = میانهٔ چند صرافی | binance
PRICE_OFFSET = 0.0                            # اختلاف ثابت چارت شما با منبع (دلار)
CHART_PRICE = None                            # قیمت چارت خودتان (مثلاً 63683.66)؛ None = قیمت زنده
LIVE_SECONDS = 30                             # مدت آپدیت زندهٔ قیمت بعد از تحلیل (۰ = خاموش)
REFRESH_EVERY = 2                             # هر چند ثانیه یک‌بار
# ---- ژورنال و فایل‌ها ----
SHADOW_ON = True                              # ثبت سیگنال‌های ردشده با ورود/SL/TP فرضی
SHADOW_PATH = os.path.join(_DATA, "scalp_shadow.jsonl")
SIGNALS_PATH = os.path.join(_DATA, "scalp_journal_signals.jsonl")
JOURNAL_PATH = os.path.join(_DATA, "scalp_journal.jsonl")
# ---- ظاهر کارت‌ها ----
PX_DECIMALS = {"EURUSD": 5, "GBPUSD": 5, "DOGE": 5, "SHIB": 9, "XRP": 4, "ADA": 4, "TRX": 5}  # رقم اعشار قیمت (پیش‌فرض ۲)
SHOW_SYMBOL = True                            # نماد/واحد کنار عددها
CCY_SYMBOL = {"BTC": "$", "ETH": "$", "DOGE": "$", "SHIB": "$", "XRP": "$", "SOL": "$", "BNB": "$", "ADA": "$", "TRX": "$", "LINK": "$", "AVAX": "$", "Gold": "$", "USOIL": "$", "EURUSD": "$", "GBPUSD": "$", "US30": "", "NAS100": ""}  # نماد جلوی عدد
PX_UNIT = {"US30": "pts", "NAS100": "pts"}    # واحد پشت عدد
COPY_BTN = True                               # دکمهٔ کپی کنار اعداد
# ====================================================================
try:   # سقف انتظار هر تماس Gemini: ۱۲۰ ثانیه به‌جای ۶۰۰ (تماس گیرکرده زود رها و دوباره تلاش می‌شود؛ تماس سالم به‌ندرت از این بیشتر طول می‌کشد)
    import tradingagents.llm_clients.google_client as _gc
    _gc.REQUEST_TIMEOUT_SECONDS = LLM_CALL_TIMEOUT
except Exception as _e:
    print("هشدار: سقف زمان تماس مدل اعمال نشد:", str(_e)[:120])
_M = {"careful":  dict(wait_conf=99, soft_impulse=False, risk_soft=None, risk_hard=None, hold_override=False, reversal=False, no_agent_ok=False),
      "balanced": dict(wait_conf=6,  soft_impulse=True,  risk_soft=1.2, risk_hard=1.4, hold_override=False, reversal=True,  no_agent_ok=False),
      "bold":     dict(wait_conf=4,  soft_impulse=True,  risk_soft=1.2, risk_hard=1.5, hold_override=True,  reversal=True,  no_agent_ok=True)}
def M():
    m = dict(_M.get(MODE, _M["bold"]))
    m["risk_soft"] = MAX_RISK_ATR if m["risk_soft"] is None else m["risk_soft"]; m["risk_hard"] = MAX_RISK_ATR if m["risk_hard"] is None else m["risk_hard"]
    return m
SYMS = {"BTC": ("BTC-USD", "crypto"), "ETH": ("ETH-USD", "crypto"), "DOGE": ("DOGE-USD", "crypto"), "SHIB": ("SHIB-USD", "crypto"), "XRP": ("XRP-USD", "crypto"), "SOL": ("SOL-USD", "crypto"), "BNB": ("BNB-USD", "crypto"),
        "ADA": ("ADA-USD", "crypto"), "TRX": ("TRX-USD", "crypto"), "LINK": ("LINK-USD", "crypto"), "AVAX": ("AVAX-USD", "crypto"),
        "EURUSD": ("EURUSD=X", "forex"), "GBPUSD": ("GBPUSD=X", "forex"), "Gold": ("GC=F", "stock"),
        "US30": ("YM=F", "stock"), "NAS100": ("NQ=F", "stock"), "USOIL": ("CL=F", "stock")}      # شاخص‌ها و نفت: فیوچرز CME (E-mini Dow، E-mini Nasdaq-100، WTI) مثل طلا
_ALIAS = {"BTC": "BTC", "BITCOIN": "BTC", "ETH": "ETH", "ETHEREUM": "ETH", "DOGE": "DOGE", "DOGECOIN": "DOGE", "SHIB": "SHIB", "SHIBA": "SHIB", "SHIBAINU": "SHIB",
          "XRP": "XRP", "RIPPLE": "XRP", "SOL": "SOL", "SOLANA": "SOL", "BNB": "BNB", "BINANCECOIN": "BNB",
          "ADA": "ADA", "CARDANO": "ADA", "TRX": "TRX", "TRON": "TRX", "LINK": "LINK", "CHAINLINK": "LINK", "AVAX": "AVAX", "AVALANCHE": "AVAX",
          "EURUSD": "EURUSD", "EUR": "EURUSD", "EURO": "EURUSD", "GBPUSD": "GBPUSD", "GBP": "GBPUSD", "POUND": "GBPUSD", "STERLING": "GBPUSD", "GOLD": "Gold", "XAU": "Gold", "XAUUSD": "Gold",
          "US30": "US30", "DOW": "US30", "DOWJONES": "US30", "DJI": "US30", "DJIA": "US30", "YM": "US30",
          "NAS100": "NAS100", "NASDAQ": "NAS100", "NASDAQ100": "NAS100", "NDX": "NAS100", "NQ": "NAS100", "USTEC": "NAS100", "US100": "NAS100",
          "USOIL": "USOIL", "WTI": "USOIL", "CRUDE": "USOIL", "USCRUDE": "USOIL", "CRUDEOIL": "USOIL", "OIL": "USOIL", "CL": "USOIL", "USCRUDEOIL": "USOIL"}
ASSET_OVR = {"USOIL": dict(SL_BUFFER_ATR=0.45, IMPULSE_ATR=0.6, IMPULSE_VETO_ATR=0.9, MAX_RISK_ATR=1.5)}      # v12 پروفایل نفت: بافر SL بزرگ‌تر (شکار استاپ)، ایمپالس خلاف جهت زودتر ممنوع، سقف ریسک کمی بازتر
_BASE_OVR = {n_: globals()[n_] for o_ in ASSET_OVR.values() for n_ in o_}      # مقدار پایهٔ پارامترهایی که پروفایل بعضی دارایی‌ها عوض می‌کند
def _norm(x): return str(x).upper().replace(" ", "").replace("-", "").replace("_", "")
def _apply_asset(a):
    """دارایی فعال را عوض می‌کند (برای حالت ALL هم همین استفاده می‌شود)."""
    global ASSET, PXD, sym, atype
    ASSET = a; PXD = int(PX_DECIMALS.get(a, 2)); sym, atype = SYMS[a]
    globals().update(_BASE_OVR); globals().update(ASSET_OVR.get(a, {}))
_k = _norm(ASSET)
ALL_MODE = _k in ("ALL", "همه", "BEST", "SCAN", "AUTO")
ALL_ASSETS = list(dict.fromkeys(_ALIAS[_norm(x_)] for x_ in ALL_ASSETS if _norm(x_) in _ALIAS)) or ["BTC"]
if ALL_MODE: _apply_asset(ALL_ASSETS[0])
else:
    if _k not in _ALIAS: raise ValueError(f"دارایی ناشناخته: {ASSET}. یکی از BTC / ETH / DOGE / SHIB / XRP / SOL / EURUSD / GBPUSD / Gold / US30 / NAS100 / USOIL / ALL")
    _apply_asset(_ALIAS[_k])
BASIS_MAX_LAG = {"Gold": 3, "US30": 12, "NAS100": 12, "USOIL": 10}      # فیوچرز شاخص/نفت در ساعت‌های کم‌معامله ممکن است چند دقیقه معامله نداشته باشد؛ تا این‌قدر دقیقه برای حساب اختلاف قابل‌قبول است
FUT_BASIS = ("Gold", "US30", "NAS100", "USOIL")      # فیوچرز با اسپات/CFD چارت شما فرق دارد (کری، رول): افست از CHART_PRICE حساب می‌شود
ASSET_DESC = {"Gold": "Gold (XAUUSD spot; data = COMEX GC futures). Drivers: US real yields, USD, Fed expectations, geopolitics/safe-haven flows.",
              "US30": "US30 (Dow Jones Industrial Average CFD; data = CME YM E-mini futures). Cash session 09:30-16:00 NY. Drivers: Fed/rates, US macro data (NFP, CPI, PMI), yields, industrial/financial mega-cap earnings, risk sentiment.",
              "NAS100": "NAS100 (Nasdaq-100 CFD; data = CME NQ E-mini futures). Cash session 09:30-16:00 NY. Drivers: mega-cap tech earnings (NVDA, MSFT, AAPL, AMZN, META, GOOGL), AI sentiment, yields/Fed, USD; most volatile of the indices.",
              "USOIL": "USOIL (US crude oil, WTI; data = NYMEX CL futures). Drivers: OPEC+ decisions, EIA inventory report (Wednesday 10:30 NY), geopolitics/Middle East supply risk, USD, China demand, US shale output.",
              "BTC": "BTC (Bitcoin)", "ETH": "ETH (Ethereum)", "DOGE": "DOGE (Dogecoin; high-beta crypto that follows BTC)", "SHIB": "SHIB (Shiba Inu; meme token with very small unit price, high beta to BTC and DOGE, social-media driven spikes)",
              "XRP": "XRP (Ripple; large-cap payments coin, moves on legal/regulatory news)", "SOL": "SOL (Solana; high-beta large-cap L1, follows BTC/ETH with amplified swings)",
              "BNB": "BNB (Binance Coin; exchange token, usually lower beta than altcoins)", "ADA": "ADA (Cardano; large-cap L1, moves with broader altcoin sentiment)",
              "TRX": "TRX (Tron; large-cap payments/DeFi chain)", "LINK": "LINK (Chainlink; oracle network token, high-beta altcoin)", "AVAX": "AVAX (Avalanche; high-beta large-cap L1)",
              "EURUSD": "EUR/USD (spot FX). Drivers: ECB vs Fed policy divergence, euro-area and US data, yields, DXY, risk sentiment. Most liquid 07-17 UTC.", "GBPUSD": "GBP/USD (spot FX). Drivers: BoE vs Fed policy divergence, UK CPI/jobs/GDP, yields, DXY, risk sentiment. Most liquid 07-17 UTC."}
OHLC = {"Open": "first", "High": "max", "Low": "min", "Close": "last"}
TP1_R, TP2_R = 1.5, 3.0   # ریوارد به ریسک: TP1 = ۱ به ۱٫۵ و TP2 = ۱ به ۳ (ثابت)
SAFE_R2 = max(SAFE_R2, MIN_RR); RUN_R2 = max(RUN_R2, SAFE_R2)      # v11: ریوارد ۱ به ۳ قفل است
utcnow = lambda: dt.datetime.now(dt.timezone.utc).replace(tzinfo=None)

def _clean(d):
    if isinstance(d.columns, pd.MultiIndex): d.columns = d.columns.get_level_values(0)
    cols = [x for x in ("Open", "High", "Low", "Close", "Volume") if x in d.columns]
    d = d[cols].dropna(subset=["Open", "High", "Low", "Close"]).copy()
    if "Volume" in d.columns: d["Volume"] = d["Volume"].fillna(0.0)      # حجم برای VWAP/پروفایل حجم (v8)
    if d.index.tz is not None: d.index = d.index.tz_convert("UTC").tz_localize(None)
    return d

def load(sym):
    d5 = _clean(yf.download(sym, start=utcnow() - dt.timedelta(days=30), interval="5m", progress=False, auto_adjust=True))
    d1 = _clean(yf.download(sym, period="1y", interval="1d", progress=False, auto_adjust=True))
    return d5.iloc[:-1], d1          # آخرین کندل ۵م هنوز بسته نشده

ema = lambda s, n: s.ewm(span=n, adjust=False).mean()
def atr(d, n=14):
    pc = d.Close.shift(1)
    tr = pd.concat([d.High - d.Low, (d.High - pc).abs(), (d.Low - pc).abs()], axis=1).max(axis=1)
    return tr.ewm(alpha=1/n, adjust=False).mean()

def features(d5, d1):
    """تایم‌فریم‌های بالاتر فقط با کندل‌های بسته‌شده به کندل ۵ دقیقه وصل می‌شوند (بدون نگاه به آینده)."""
    now = d5.index + pd.Timedelta("5min")
    f = pd.DataFrame({"h": d5.High, "l": d5.Low, "c": d5.Close}, index=d5.index)
    f["ema20"] = ema(d5.Close, 20)
    for name, rule in (("15m", "15min"), ("30m", "30min"), ("1h", "60min")):
        r = d5.resample(rule, label="left", closed="left").agg(OHLC).dropna()
        av = r.index + pd.Timedelta(rule)
        f["d" + name] = pd.Series(np.sign(ema(r.Close, 20) - ema(r.Close, 50)).values, index=av).reindex(now, method="ffill").values
        if name == "15m": f["atr"] = pd.Series(atr(r).values, index=av).reindex(now, method="ffill").values
    f["d1d"] = pd.Series(np.sign(d1.Close - ema(d1.Close, 20)).values, index=d1.index + pd.Timedelta("1D")).reindex(now, method="ffill").values
    f["votes"] = f[["d15m", "d30m", "d1h", "d1d"]].sum(axis=1)
    return f.dropna()

def entry_price(c, e20, a, side):
    """ورود روی پولبک به EMA20 ولی هیچ‌وقت دورتر از MAX_ENTRY_DIST×ATR از قیمت."""
    pull = np.clip(np.maximum(side * (c - e20), 0), MIN_PULL * a, MAX_ENTRY_DIST * a)
    return c - side * pull

try:
    from langchain_core.callbacks import BaseCallbackHandler
except Exception:                      # اگر نبود، گزارش پیشرفت خاموش می‌شود ولی تحلیل اجرا می‌شود
    BaseCallbackHandler = object
ROLE_FA = {"Market Analyst": "تحلیلگر بازار/تکنیکال", "Sentiment Analyst": "تحلیلگر احساسات", "News Analyst": "تحلیلگر اخبار",
           "Fundamentals Analyst": "تحلیلگر بنیادی", "Bull Researcher": "پژوهشگر خوش‌بین", "Bear Researcher": "پژوهشگر بدبین",
           "Research Manager": "مدیر تحقیقات", "Trader": "معامله‌گر", "Aggressive Analyst": "ریسک (تهاجمی)",
           "Neutral Analyst": "ریسک (خنثی)", "Conservative Analyst": "ریسک (محافظه‌کار)", "Portfolio Manager": "مدیر سبد"}
ANALYSTS = ("Market Analyst", "Sentiment Analyst", "News Analyst", "Fundamentals Analyst")
TOOL_FA = {"get_stock_data": "قیمت و کندل‌های اخیر را گرفت", "get_indicators": "اندیکاتور{} را محاسبه کرد",
           "get_verified_market_snapshot": "عکس لحظه‌ای تأییدشدهٔ بازار را گرفت", "get_fundamentals": "اطلاعات بنیادی را گرفت",
           "get_balance_sheet": "ترازنامه را گرفت", "get_cashflow": "جریان نقدی را گرفت", "get_income_statement": "صورت سود و زیان را گرفت",
           "get_news": "خبرهای مربوط به ارز را خواند", "get_global_news": "خبرهای کلان جهانی را خواند",
           "get_insider_transactions": "معاملات داخلی را بررسی کرد", "get_macro_indicators": "شاخص اقتصاد کلان را بررسی کرد",
           "get_prediction_markets": "بازارهای پیش‌بینی را بررسی کرد"}
import re
class AgentProgress(BaseCallbackHandler):
    """گزارش زندهٔ کار عامل‌ها: هر ابزار/نوبت مدل را به زبان ساده ثبت می‌کند تا هر ۳۰ ثانیه چاپ شود. هیچ خطایی نباید از اینجا به بیرون برسد."""
    def __init__(self): self.lock = threading.RLock(); self.reset()
    def __copy__(self): return self                    # کتابخانه‌ها ممکن است handler را کپی کنند؛ قفل قابل کپی نیست، پس همان شیء برگردد
    def __deepcopy__(self, memo): return self
    def reset(self):
        self.llm = self.tools = self.errs = 0; self.active = {}; self.tactive = {}; self.events = []; self.sent = 0
        self.done = set(); self.turns = {}; self.llm_time = 0.0; self.last_err = ""; self.role_time = {}; self.tool_time = {}
    def _role(self, md):
        try:
            md = md or {}; first = str(md.get("langgraph_checkpoint_ns", "")).split("|")[0].split(":")[0]
            return first if first in ROLE_FA else str(md.get("langgraph_node", "")) or "?"
        except Exception: return "?"
    def _ev(self, txt):
        with self.lock: self.events.append(txt)
    def _start(self, rid, kw):
        try:
            with self.lock: self.llm += 1; self.active[rid] = (time.time(), self._role(kw.get("metadata")))
        except Exception: pass
    def on_llm_start(self, serialized, prompts, *, run_id, **kw): self._start(run_id, kw)
    def on_chat_model_start(self, serialized, messages, *, run_id, **kw): self._start(run_id, kw)
    def on_llm_end(self, response, *, run_id, **kw):
        try:
            with self.lock:
                t, role = self.active.pop(run_id, (None, "?"))
                if t: self.llm_time += time.time() - t; self.role_time[role] = self.role_time.get(role, 0.0) + time.time() - t
                fa = ROLE_FA.get(role, role)
                if role in ANALYSTS:
                    calls = None
                    try: calls = response.generations[0][0].message.tool_calls
                    except Exception: pass
                    if role == "Sentiment Analyst" or not calls:
                        if role not in self.done: self.done.add(role); self._ev(f"✅ {fa}: گزارشش را نوشت ({len(self.done)}/4 تحلیلگر تمام شد)")
                else:
                    self.turns[role] = self.turns.get(role, 0) + 1
                    self._ev(f"💬 {fa}: نوبت {self.turns[role]} را تمام کرد" + (f" ({time.time()-t:.0f} ثانیه)" if t else ""))
        except Exception: pass
    def on_llm_error(self, error, *, run_id, **kw):
        try:
            with self.lock:
                self.active.pop(run_id, None); self.errs += 1; self.last_err = f"{type(error).__name__}: {str(error)[:160]}"
                self._ev(f"⚠ خطای مدل: {self.last_err}")
        except Exception: pass
    def on_tool_start(self, serialized, input_str, *, run_id, **kw):
        try:
            name = (serialized or {}).get("name") or kw.get("name") or "?"
            with self.lock: self.tools += 1; self.tactive[run_id] = (time.time(), self._role(kw.get("metadata")), str(name), str(kw.get("inputs") or input_str)[:300])
        except Exception: pass
    def on_tool_end(self, output, *, run_id, **kw):
        try:
            with self.lock:
                t, role, name, inp = self.tactive.pop(run_id, (time.time(), "?", "?", ""))
                m = re.search(r"indicator['\"]?\s*[:=]\s*['\"]([\w.\-]+)", inp)
                what = TOOL_FA.get(name, f"ابزار {name} را اجرا کرد").replace("{}", f" {m.group(1)}" if m else "")
                size = len(str(getattr(output, "content", output))); self.tool_time[(role, name)] = self.tool_time.get((role, name), 0.0) + time.time() - t
                self._ev(f"🔧 {ROLE_FA.get(role, role)}: {what} ({time.time()-t:.1f} ثانیه، {size:,} نویسه)")
        except Exception: pass
    def on_tool_error(self, error, *, run_id, **kw):
        try:
            with self.lock:
                t, role, name, inp = self.tactive.pop(run_id, (time.time(), "?", "?", ""))
                self._ev(f"⚠ {ROLE_FA.get(role, role)}: ابزار {name} خطا داد: {str(error)[:120]}")
        except Exception: pass
    def summary(self):
        """کندترین بخش‌ها (مجموع زمان؛ تحلیلگران موازی کار می‌کنند پس جمعشان از زمان کل بیشتر است)."""
        with self.lock:
            rows = [(v, f"{ROLE_FA.get(r, r)}: تفکر/نوشتن مدل") for r, v in self.role_time.items()] + \
                   [(v, f"{ROLE_FA.get(r, r)}: ابزار {n}") for (r, n), v in self.tool_time.items()]
            rows.sort(reverse=True)
            return "\n".join(f"   {v:6.0f} ثانیه  {name}" for v, name in rows[:8])
    def report(self, max_events=10):
        with self.lock:
            now = time.time(); new = self.events[self.sent:]; self.sent = len(self.events)
            nb = self.turns.get("Bull Researcher", 0); nr = self.turns.get("Bear Researcher", 0)
            risk = sum(self.turns.get(r, 0) for r in ("Aggressive Analyst", "Neutral Analyst", "Conservative Analyst"))
            L = [f"      پیشرفت: تحلیلگران {len(self.done)}/4 | بحث خوش‌بین/بدبین {nb}+{nr} از {DEBATE_ROUNDS}+{DEBATE_ROUNDS} | مدیر تحقیقات {self.turns.get('Research Manager', 0)}/1 | معامله‌گر {self.turns.get('Trader', 0)}/1 | ریسک {risk}/{3 * RISK_ROUNDS} | مدیر سبد {self.turns.get('Portfolio Manager', 0)}/1",
                 f"      آمار: تماس مدل {self.llm} | ابزار {self.tools} | خطای مدل {self.errs}"]
            if len(new) > max_events: L.append(f"      … و {len(new) - max_events} رویداد قبلی‌تر"); new = new[-max_events:]
            L += ["      " + x for x in new]
            busy = [f"{ROLE_FA.get(r, r)} ({now - t:.0f}ث)" for t, r in self.active.values()] + [f"{ROLE_FA.get(r, r)}: {TOOL_FA.get(n, n).replace('{}', '')} ({now - t:.0f}ث)" for t, r, n, _ in self.tactive.values()]
            if busy: L.append("      ⏳ الان در حال کار: " + " ، ".join(busy[:6]))
            old = max([now - t for t, _ in self.active.values()] + [0.0])
            if old > 0.75 * LLM_CALL_TIMEOUT: L.append(f"      ⚠ یک تماس مدل بیش از {old:.0f} ثانیه معطل است (صف یا کندی Gemini)؛ بعد از {LLM_CALL_TIMEOUT} ثانیه رها و دوباره تلاش می‌شود")
            return "\n".join(L)
PROG = AgentProgress()

def run_agents():
    from tradingagents.default_config import DEFAULT_CONFIG
    from tradingagents.graph.trading_graph import TradingAgentsGraph
    today, errs = utcnow().date(), []; PROG.reset(); use_cb = True
    days = [today] * (1 + AGENT_RETRIES) + [today - dt.timedelta(days=1)]   # چند تلاش برای امروز؛ آخرین شانس: تاریخ دیروز
    for k, day in enumerate(days, 1):
        try:
            cfg = DEFAULT_CONFIG.copy(); cfg["max_debate_rounds"] = DEBATE_ROUNDS; cfg["max_risk_discuss_rounds"] = RISK_ROUNDS
            cfg["max_tool_rounds"] = MAX_TOOL_ROUNDS; cfg["news_article_limit"] = NEWS_LIMIT; cfg["global_news_article_limit"] = max(3, NEWS_LIMIT // 2)
            ta = TradingAgentsGraph(debug=False, config=cfg, callbacks=[PROG] if use_cb else None)   # تیم کامل، بدون حذف هیچ عاملی
            state, rating = ta.propagate(sym, day.strftime("%Y-%m-%d"), asset_type=atype)
            r = str(rating).lower()
            return (1 if r in ("buy", "overweight") else -1 if r in ("sell", "underweight") else 0), rating, state
        except Exception as e:
            errs.append(f"تلاش {k} ({day}): {type(e).__name__}: {str(e)[:350]}")
            print(f"⚠ {errs[-1][:260]}")
            if use_cb and any(w in str(e).lower() for w in ("pickle", "lock", "callback", "deepcopy", "copy")):
                use_cb = False; print("   مشکل از گزارش پیشرفت بود؛ بدون آن (فقط گزارش زمان) فوراً دوباره اجرا می‌شود ..."); continue
            if k < len(days):
                print(f"   {AGENT_RETRY_WAIT} ثانیه صبر و تلاش دوباره (تیم کامل از اول اجرا می‌شود) ...")
                time.sleep(AGENT_RETRY_WAIT)
    raise RuntimeError(" | ".join(errs))

import threading
def _agent_board(t_start, final=False):
    try:
        with PROG.lock:
            tn = dict(PROG.turns); nd = len(PROG.done); busy = [ROLE_FA.get(r, r) for t, r in PROG.active.values()] + [ROLE_FA.get(r, r) + ": " + TOOL_FA.get(n, n).replace("{}", "") for t, r, n, _ in PROG.tactive.values()]
            evs = list(PROG.events[-4:]); llm, tools, errs = PROG.llm, PROG.tools, PROG.errs
        risk = sum(tn.get(r, 0) for r in ("Aggressive Analyst", "Neutral Analyst", "Conservative Analyst"))
        stg = [("📰 تحلیلگران", nd, 4, .40), ("🐂🐻 بحث خوش‌بین/بدبین", tn.get("Bull Researcher", 0) + tn.get("Bear Researcher", 0), 2 * DEBATE_ROUNDS, .18), ("🧑‍⚖️ مدیر تحقیقات", tn.get("Research Manager", 0), 1, .06),
               ("📈 معامله‌گر", tn.get("Trader", 0), 1, .06), ("🛡 بحث ریسک", risk, 3 * RISK_ROUNDS, .18), ("👔 مدیر سبد", tn.get("Portfolio Manager", 0), 1, .12)]
        frac = sum(w * min(1.0, d_ / max(t_, 1)) for _, d_, t_, w in stg); el = time.time() - t_start
        rem = max(30.0, el * (1 - frac) / frac) if frac > 0.08 else max(60.0, 420.0 - el)
        chips = "".join(f"<span class='{'ok' if d_ >= t_ else 'go' if d_ > 0 else ''}'>{'✅' if d_ >= t_ else '⏳' if d_ > 0 else '⌛'} {n_} {min(d_, t_)}/{t_}</span>" for n_, d_, t_, _ in stg)
        bz = ("<div class='ag-ev'>⏳ الان: " + _h(" ، ".join(busy[:5])) + "</div>") if busy else ""
        ev = ("<div class='ag-ev'>" + _h("\n".join(evs)) + "</div>") if evs else ""
        ui(f"<div class='al-wrap'><div class='al-top'><span>🧠 تحلیل کامل {_h(_asset_label())} · {_mmss(el)} گذشته</span><span>{frac * 100:.0f}٪</span></div><div class='al-bar'><i style='width:{frac * 100:.0f}%'></i></div>"
           f"<div class='al-eta'>⏱ تیم عامل‌ها حدود {_mmss(rem)} دیگر · بعدش شورا، استراتژی و مدیرعامل چند دقیقه · <b>جواب نهایی حدود ساعت {_lt(rem + 3 * 60)}</b> (به وقت شما) · تماس مدل {llm} · ابزار {tools} · خطا {errs}</div><div class='ag-st'>{chips}</div>{bz}{ev}</div>")
    except Exception: pass

def _agent_live(t_start):
    """کارت زندهٔ تیم عامل‌ها: اولین‌بار display_id می‌سازد، بعد همان را آپدیت می‌کند."""
    global ui
    _orig = ui
    def _cap(htm, out=True):
        _board_show(htm, "ta_ag"); return None
    ui = _cap
    try: _agent_board(t_start)
    finally: ui = _orig

def run_agents_safe(timeout_min):
    box = {}
    def work():
        try: box["res"] = run_agents()
        except Exception as e: box["err"] = e
    th = threading.Thread(target=work, daemon=True); th.start(); t = time.time(); _last = 0.0; _ALLBOARD["ta_ag"] = False
    while th.is_alive() and time.time() - t < timeout_min * 60:
        th.join(5)
        if th.is_alive() and time.time() - _last >= 5:      # v21: یک کارت زنده که خودش آپدیت می‌شود (به‌جای چاپ پشت‌سرهم)
            _last = time.time()
            try:
                from IPython.display import update_display
                # همان کارت را آپدیت می‌کند
                _buf = {}
                _o = ui.__wrapped__ if hasattr(ui, "__wrapped__") else None
            except Exception: pass
            _agent_live(t)
    if "res" in box: return box["res"]
    why = str(box.get("err", f"بیش از {timeout_min} دقیقه طول کشید"))[:700]
    AG["err"] = why
    print("عامل‌ها نتیجه ندادند:", why)
    return None

# ---------------- قیمت زنده (مستقل از کندل بسته‌شده) ----------------
import requests
from concurrent.futures import ThreadPoolExecutor
from IPython.display import display, Pretty, HTML, clear_output

_CB, _KR, _BS = "https://api.exchange.coinbase.com/products/%s/ticker", "https://api.kraken.com/0/public/Ticker", "https://www.bitstamp.net/api/v2/ticker/%s/"
_kr = lambda j: next(iter(j["result"].values()))["c"][0]     # آخرین معاملهٔ کراکن
LIVE_SRC = {   # (نام، آدرس، پارامتر، استخراج قیمت) — همه عمومی و بدون کلید
    "BTC": [("Coinbase", _CB % "BTC-USD", None, lambda j: j["price"]),
            ("Kraken", _KR, {"pair": "XBTUSD"}, _kr),
            ("Bitstamp", _BS % "btcusd", None, lambda j: j["last"])],
    "ETH": [("Coinbase", _CB % "ETH-USD", None, lambda j: j["price"]),
            ("Kraken", _KR, {"pair": "ETHUSD"}, _kr),
            ("Bitstamp", _BS % "ethusd", None, lambda j: j["last"])],
}
BINANCE = {"BTC": "BTCUSDT", "ETH": "ETHUSDT", "DOGE": "DOGEUSDT", "SHIB": "SHIBUSDT", "XRP": "XRPUSDT", "SOL": "SOLUSDT", "BNB": "BNBUSDT", "ADA": "ADAUSDT", "TRX": "TRXUSDT", "LINK": "LINKUSDT", "AVAX": "AVAXUSDT"}

# ---- v20: چک قیمت نوبیتکس برای رمزارزها (فقط نمایش/مقایسه؛ هیچ سفارشی ثبت نمی‌شود) ----
NOBX_SYM = {"BTC": "btc", "ETH": "eth", "DOGE": "doge", "SHIB": "shib", "XRP": "xrp", "SOL": "sol", "BNB": "bnb", "ADA": "ada", "TRX": "trx", "LINK": "link", "AVAX": "avax"}
_NOBX_CACHE = {"t": 0.0, "v": None, "asset": None}
def nobitex_price(max_age=8):
    """قیمت لحظه‌ای جفت {دارایی}/تتر در نوبیتکس (API عمومی، بدون کلید). فقط برای رمزارزهای لیست‌شده؛ شکست = None (بی‌صدا، مسیر اصلی را متوقف نمی‌کند)."""
    sy = NOBX_SYM.get(ASSET)
    if not sy: return None
    if _NOBX_CACHE["asset"] == ASSET and time.time() - _NOBX_CACHE["t"] < max_age: return _NOBX_CACHE["v"]
    try:
        r = requests.get("https://api.nobitex.ir/market/stats", params={"srcCurrency": sy, "dstCurrency": "usdt"}, timeout=4)
        r.raise_for_status()
        d = (r.json() or {}).get("stats", {}).get(f"{sy}-usdt") or {}
        p = float(d.get("latest")) if d.get("latest") is not None else None
    except Exception:
        p = None
    _NOBX_CACHE.update(t=time.time(), v=p, asset=ASSET)
    return p

def _fetch(src):
    name, url, params, pick = src
    try:
        r = requests.get(url, params=params, timeout=3); r.raise_for_status()
        p = float(pick(r.json()))
        return (name, p) if p > 0 else (name, None)
    except Exception:
        return name, None

def _binance():
    for host in ("https://data-api.binance.vision", "https://api.binance.com"):   # از آی‌پی آمریکا (Colab) گاهی بلاک می‌شود
        try:
            r = requests.get(host + "/api/v3/ticker/price", params={"symbol": BINANCE[ASSET]}, timeout=3); r.raise_for_status()
            p = float(r.json()["price"])
            if p > 0: return p
        except Exception:
            continue
    return None

_LAST_LAG = [0.0]
def live_price(fallback):
    """قیمت لحظه‌ای (بدون افست): Binance اگر خواسته شد؛ وگرنه میانهٔ چند صرافی USD. نشد → yfinance یک‌دقیقه‌ای → آخرین کندل ۵م (با هشدار)."""
    t = time.time(); note = ""; _LAST_LAG[0] = 0.0
    if PRICE_SOURCE == "binance" and ASSET in BINANCE:
        p = _binance()
        if p: return p, "Binance (جفت USDT)", time.time() - t
        note = " (Binance در دسترس نبود؛ جایگزین)"
    srcs = LIVE_SRC.get(ASSET, [])
    if srcs:
        with ThreadPoolExecutor(len(srcs)) as ex:
            got = [(n, p) for n, p in ex.map(_fetch, srcs) if p]
        if got:
            return float(np.median([p for _, p in got])), "+".join(n for n, _ in got) + note, time.time() - t
    try:
        d = _clean(yf.download(sym, period="1d", interval="1m", progress=False, auto_adjust=True))
        lag = (utcnow() - d.index[-1]).total_seconds() / 60; _LAST_LAG[0] = lag
        return float(d.Close.iloc[-1]), f"yfinance 1m (شروع آخرین کندل {lag:.0f} دقیقه پیش)" + note, time.time() - t
    except Exception:
        return float(fallback), "⚠ منبع زنده در دسترس نبود؛ این آخرین کندل ۵م است", time.time() - t

DATA, _SNAP = None, {"t": 0.0, "v": None}
def snapshot(max_age=0):
    """داده‌های بسته‌شده (ATR، EMA، روندها). لحظه‌ای نیستند و لازم هم نیست؛ قیمت ورود جداگانه و زنده گرفته می‌شود. max_age>0: اگر کمتر از این ثانیه پیش گرفته شده بود دوباره دانلود نمی‌کند."""
    global DATA
    if max_age and _SNAP["v"] is not None and DATA is not None and time.time() - _SNAP["t"] < max_age: return _SNAP["v"]
    d5, d1 = load(sym); f = features(d5, d1); DATA = (d5, d1)
    age = (utcnow() - (d5.index[-1] + pd.Timedelta("5min"))).total_seconds() / 60
    _SNAP["t"], _SNAP["v"] = time.time(), (f.iloc[-1], age)
    return _SNAP["v"]

def decide(now):   # فقط تکنیکال (فالبک): امتیاز ≥۳ یعنی همهٔ تایم‌فریم‌ها هم‌جهت یا یکی خنثی (۳ از ۴ با یکی مخالف امتیاز ۲ می‌دهد)
    return 1 if now.votes >= 3 else -1 if now.votes <= -3 else 0

# ================= ایجنت جدید: متخصص ICT / اسمارت‌مانی / ویکوف / کلاسیک =================
# بخش قطعی (کد) واقعیت‌ها را می‌سازد: ساختار، نقدینگی، سوییپ، MSS، FVG/OB، پریمیوم/دیسکانت، شتاب.
# بخش مدل (ایجنت) فقط روی همین واقعیت‌ها قضاوت می‌کند و خودش قیمت نمی‌سازد (سطوح با شناسهٔ H1/L1/F1 انتخاب می‌شوند).
import os, json
from zoneinfo import ZoneInfo

def _rs(d5, rule):
    """کندل ۵م → تایم‌فریم بالاتر؛ فقط کندل‌های کاملاً بسته‌شده."""
    r = d5.resample(rule, label="left", closed="left").agg(OHLC).dropna()
    return r[(r.index + pd.Timedelta(rule)) <= d5.index[-1] + pd.Timedelta("5min")]

def _pivots(df, n):
    """سقف/کف‌های فراکتالی (تأیید بعد از n کندل). خروجی: (فهرست (ایندکس، قیمت) سقف‌ها، کف‌ها)"""
    h, l = df.High.values, df.Low.values; hi, lo = [], []
    for i in range(n, len(df) - n):
        if h[i] > h[i - n:i].max() and h[i] >= h[i + 1:i + n + 1].max(): hi.append((i, float(h[i])))
        if l[i] < l[i - n:i].min() and l[i] <= l[i + 1:i + n + 1].min(): lo.append((i, float(l[i])))
    return hi, lo

def _trend(hi, lo):
    if len(hi) < 2 or len(lo) < 2: return 0, "unknown"
    uh, ul = hi[-1][1] > hi[-2][1], lo[-1][1] > lo[-2][1]
    return (1, "up (HH/HL)") if uh and ul else (-1, "down (LH/LL)") if (not uh and not ul) else (0, "range/mixed")

def _unswept(df, piv, kind, price, tol):
    """سطح‌های نقدینگی که هنوز جارو نشده‌اند (قیمت بعد از ساخته‌شدن‌شان از آن عبور نکرده)."""
    arr = df.High.values if kind == "H" else df.Low.values; out = []
    for i, p in piv:
        later = arr[i + 1:]
        if len(later) and ((later.max() >= p) if kind == "H" else (later.min() <= p)): continue
        if (kind == "H" and p <= price) or (kind == "L" and p >= price): continue
        out.append({"p": p, "eq": sum(1 for j, q in piv if j != i and abs(q - p) <= tol)})
    return out

def _named_levels(d5t):
    """سقف/کف دیروز (PDH/PDL) و رنج آسیا (UTC ۰ تا ۷). خروجی: (نام، نوع، قیمت، جاروشده؟، موقعیت شروع)"""
    out = []; days = d5t.index.normalize(); today = days[-1]; pd_ = days[days < today]; prev = pd_[-1] if len(pd_) else today - pd.Timedelta("1D")   # آخرین روز معاملاتی قبل (برای طلا بعد از آخر هفته هم کار کند)
    py, td = d5t[days == prev], d5t[days == today]
    if len(py) > 12 and len(td):
        for nm, kind, p in (("PDH", "H", float(py.High.max())), ("PDL", "L", float(py.Low.min()))):
            out.append((nm, kind, p, bool(td.High.max() >= p if kind == "H" else td.Low.min() <= p), int(d5t.index.searchsorted(today))))
    asia, aft = td[td.index.hour < 7], td[td.index.hour >= 7]
    if len(asia) > 12 and len(aft):
        for nm, kind, p in (("Asia high", "H", float(asia.High.max())), ("Asia low", "L", float(asia.Low.min()))):
            out.append((nm, kind, p, bool(aft.High.max() >= p if kind == "H" else aft.Low.min() <= p), int(d5t.index.searchsorted(aft.index[0]))))
    return out

def _extra_levels(d5, d5t):
    """PWH/PWL (سقف/کف هفتهٔ قبل) و سقف/کف سشن لندن (UTC ۷ تا ۱۲). همان قالب _named_levels."""
    out = []
    try:
        last = d5.index[-1]; wk0 = last.normalize() - pd.Timedelta(days=int(last.weekday()))      # دوشنبهٔ این هفته
        pw, cw = d5[(d5.index >= wk0 - pd.Timedelta("7D")) & (d5.index < wk0)], d5[d5.index >= wk0]
        if len(pw) > 200 and len(cw):
            pos = int(d5t.index.searchsorted(wk0))
            for nm, kind, p in (("PWH", "H", float(pw.High.max())), ("PWL", "L", float(pw.Low.min()))):
                out.append((nm, kind, p, bool(cw.High.max() >= p if kind == "H" else cw.Low.min() <= p), pos))
        td = d5t[d5t.index.normalize() == d5t.index[-1].normalize()]
        lon, aft = td[(td.index.hour >= 7) & (td.index.hour < 12)], td[td.index.hour >= 12]
        if len(lon) > 30 and len(aft):
            for nm, kind, p in (("London high", "H", float(lon.High.max())), ("London low", "L", float(lon.Low.min()))):
                out.append((nm, kind, p, bool(aft.High.max() >= p if kind == "H" else aft.Low.min() <= p), int(d5t.index.searchsorted(aft.index[0]))))
    except Exception: pass
    return out

def _opens(d5, price, a):
    """نقاط مرجع ICT: بازشدن روز UTC، نیمه‌شب نیویورک (True Day Open)، بازشدن هفته. خروجی: [(نام، قیمت، فاصلهٔ علامت‌دار قیمت از آن به ATR)]"""
    out = []
    try:
        last = d5.index[-1]; ny = last.tz_localize("UTC").tz_convert("America/New_York")
        mid = ny.normalize().tz_convert("UTC").tz_localize(None)
        for nm, t0 in (("UTC day open", last.normalize()), ("NY midnight open", mid), ("Week open", last.normalize() - pd.Timedelta(days=int(last.weekday())))):
            seg = d5[d5.index >= t0]
            if len(seg): out.append((nm, float(seg.Open.iloc[0]), (price - float(seg.Open.iloc[0])) / a))
    except Exception: pass
    return out

def _vwap_profile(d5):
    """VWAP لنگرشده روی روز UTC + انحراف معیار وزنی؛ پروفایل حجم آخرین روز کامل قبل (POC/VAH/VAL با ۷۰٪ حجم)."""
    out = {}
    if "Volume" not in d5.columns or float(d5.Volume.tail(300).sum()) <= 0: return out
    days = d5.index.normalize(); today = days[-1]; td = d5[days == today]
    if len(td) >= 12 and float(td.Volume.sum()) > 0:
        tp = (td.High + td.Low + td.Close) / 3; v = td.Volume.astype(float); cv = v.cumsum(); vw = (tp * v).cumsum() / cv
        sd = float(np.sqrt((((tp - vw) ** 2) * v).cumsum().iloc[-1] / cv.iloc[-1])); out["vwap"] = (float(vw.iloc[-1]), sd)
    prevd = days[days < today]
    if len(prevd):
        py = d5[days == prevd[-1]]
        if len(py) > 100 and float(py.Volume.sum()) > 0:
            lo, hi = float(py.Low.min()), float(py.High.max())
            if hi > lo:
                bins = np.linspace(lo, hi, 41); tpp = ((py.High + py.Low + py.Close) / 3).values
                prof = np.bincount(np.clip(np.digitize(tpp, bins) - 1, 0, 39), weights=py.Volume.values.astype(float), minlength=40)
                poc = int(prof.argmax()); tot = float(prof.sum()); acc = float(prof[poc]); l = h = poc
                while acc < 0.7 * tot and (l > 0 or h < 39):
                    up = prof[h + 1] if h < 39 else -1.0; dn = prof[l - 1] if l > 0 else -1.0
                    if up >= dn: h += 1; acc += float(prof[h])
                    else: l -= 1; acc += float(prof[l])
                out["prev"] = (float((bins[poc] + bins[poc + 1]) / 2), float(bins[h + 1]), float(bins[l]))     # POC, VAH, VAL
    return out

def _regime(d5t, d5, a):
    """نسبت کارایی کافمن (۳ ساعت اخیر؛ ۱=روند خالص، ۰=رنج) و صدک ATR ۱۵م در ۵ روز اخیر (نوسان منبسط/منقبض)."""
    c = d5t.Close.values; n = 36; er = float(abs(c[-1] - c[-n]) / max(np.abs(np.diff(c[-n:])).sum(), 1e-9))
    at = atr(_rs(d5, "15min")).tail(480); return er, float((at <= a).mean())

_PAIR = {"t": 0.0, "df": None, "sym": None}
SMT_PAIR = {"EURUSD": "GBPUSD=X", "GBPUSD": "EURUSD=X", "BTC": "ETH-USD", "ETH": "BTC-USD", "DOGE": "BTC-USD", "SHIB": "DOGE-USD", "Gold": "SI=F", "US30": "NQ=F", "NAS100": "YM=F", "USOIL": "BZ=F"}      # واگرایی SMT: داو↔نزدک، WTI↔برنت
def _pair_df():
    sym_p = SMT_PAIR.get(ASSET)
    if not sym_p: return None
    if _PAIR["df"] is not None and _PAIR["sym"] == sym_p and time.time() - _PAIR["t"] < 120: return _PAIR["df"]
    try:
        d = _clean(yf.download(sym_p, start=utcnow() - dt.timedelta(days=4), interval="5m", progress=False, auto_adjust=True))
        _PAIR.update(t=time.time(), df=d, sym=sym_p); return d
    except Exception: return None

def _smt(d5t, pair, lookback=12, ref=48):
    """SMT ICT: یکی از دو دارایی همبسته سقف/کف تازه می‌سازد و دیگری نه = واگرایی. خروجی: {'hi':..., 'lo':..., 'pair':نام}"""
    if pair is None: return None
    j = d5t[["High", "Low"]].join(pair[["High", "Low"]], rsuffix="_p", how="inner").tail(ref + lookback)
    if len(j) < ref + lookback - 6: return None
    rec, pri = j.tail(lookback), j.iloc[:-lookback]; res = {"pair": _PAIR["sym"]}
    for k, (c1, c2, f) in (("hi", ("High", "High_p", "max")), ("lo", ("Low", "Low_p", "min"))):
        op = (lambda x, y: x > y) if f == "max" else (lambda x, y: x < y)
        n1 = op(getattr(rec[c1], f)(), getattr(pri[c1], f)()); n2 = op(getattr(rec[c2], f)(), getattr(pri[c2], f)())
        res[k] = "both" if (n1 and n2) else "asset-only" if n1 else "pair-only" if n2 else "none"
    return res

def _ifvg(df, tf, a, lookback):
    """Inversion FVG (IFVG): FVG که قیمت با بسته‌شدن کامل از آن عبور کرده و حالا نقش معکوس دارد (مقاومت↔حمایت)."""
    H, L, C = df.High.values, df.Low.values, df.Close.values; N = len(df); out = []
    for i in range(max(2, N - lookback), N - 1):
        if L[i] > H[i - 2] and L[i] - H[i - 2] >= 0.15 * a:
            lo, hi = float(H[i - 2]), float(L[i]); k = np.nonzero(C[i + 1:] < lo)[0]
            if len(k) and not (C[i + 1 + k[0]:] > hi).any(): out.append({"type": "IFVG", "dir": -1, "tf": tf, "lo": lo, "hi": hi})
        if H[i] < L[i - 2] and L[i - 2] - H[i] >= 0.15 * a:
            lo, hi = float(H[i]), float(L[i - 2]); k = np.nonzero(C[i + 1:] > hi)[0]
            if len(k) and not (C[i + 1 + k[0]:] < lo).any(): out.append({"type": "IFVG", "dir": 1, "tf": tf, "lo": lo, "hi": hi})
    return out

def _disp_fvg(d5t, sw, a):
    """بعد از سوییپ، ظرف ۹ کندل یک FVG هم‌جهت با برگشت (دیس‌پلیسمنت) ساخته شده؟ (حلقهٔ A+ مدل ICT: سوییپ ← دیس‌پلیسمنت ← MSS)"""
    H, L = d5t.High.values, d5t.Low.values; j = sw["j"]
    for i in range(max(j + 1, 2), min(len(d5t), j + 10)):
        if sw["bias"] == 1 and L[i] > H[i - 2] and L[i] - H[i - 2] >= 0.15 * a: return True
        if sw["bias"] == -1 and H[i] < L[i - 2] and L[i - 2] - H[i] >= 0.15 * a: return True
    return False

_DV = {"t": 0.0, "v": None, "a": None}
DERIV_ID = {"BTC": ("BTCUSDT", "BTC-USDT-SWAP"), "ETH": ("ETHUSDT", "ETH-USDT-SWAP")}
def derivatives():
    """فاندینگ و تغییر OI یک‌ساعته (بهترین‌حالت، Bybit سپس OKX؛ هر خطا = None). داده‌ای که نرسد هرگز ساخته نمی‌شود."""
    if ASSET not in DERIV_ID: return None
    if _DV["v"] is not None and _DV["a"] == ASSET and time.time() - _DV["t"] < 90: return _DV["v"]
    s, inst = DERIV_ID[ASSET]; out = {}
    try:
        r = requests.get("https://api.bybit.com/v5/market/tickers", params={"category": "linear", "symbol": s}, timeout=3).json()["result"]["list"][0]
        out["funding"] = float(r["fundingRate"]); out["src"] = "Bybit"
        try:
            o = requests.get("https://api.bybit.com/v5/market/open-interest", params={"category": "linear", "symbol": s, "intervalTime": "5min", "limit": 13}, timeout=3).json()["result"]["list"]
            out["oi_chg_1h"] = float(o[0]["openInterest"]) / float(o[-1]["openInterest"]) - 1
        except Exception: pass
    except Exception:
        try:
            r = requests.get("https://www.okx.com/api/v5/public/funding-rate", params={"instId": inst}, timeout=3).json()["data"][0]
            out["funding"] = float(r["fundingRate"]); out["src"] = "OKX"
        except Exception: pass
    out = out if "funding" in out else None
    _DV.update(t=time.time(), v=out, a=ASSET); return out

def _merge(lv, a):
    out = []; rank = {"day": 4, "4h": 3, "1h": 2, "15m": 1, "5m": 0}
    for kind in ("H", "L"):
        grp = []
        for x in sorted((x for x in lv if x["kind"] == kind), key=lambda x: x["p"]):
            if grp and x["p"] - grp[-1][-1]["p"] <= 0.1 * a: grp[-1].append(x)
            else: grp.append([x])
        for g in grp:
            best = max(g, key=lambda x: rank[x["tf"]])
            out.append({**best, "eq": max(max(x["eq"] for x in g), len(g) - 1), "names": ", ".join(sorted({x["name"] for x in g}))})
    return out

def _sweeps(d5t, highs, lows, lookback):
    """سوییپ = کندل از سطح عبور کرد ولی ظرف ۳ کندل بسته‌شدنش برگشت داخل (نه شکست واقعی)."""
    H, L, C = d5t.High.values, d5t.Low.values, d5t.Close.values; N = len(d5t); out, seen = [], set()
    for kind, pts in (("H", highs), ("L", lows)):
        for pos, p, nm in pts:
            if pos >= N - 1: continue
            idx = np.nonzero((H[pos:] > p) if kind == "H" else (L[pos:] < p))[0]
            if not len(idx): continue
            j = pos + int(idx[0])
            if j < N - lookback or (kind, j) in seen: continue
            if ((C[j:j + 3] < p) if kind == "H" else (C[j:j + 3] > p)).any():
                seen.add((kind, j))
                out.append({"bias": -1 if kind == "H" else 1, "level": float(p), "name": nm, "ago": N - 1 - j, "j": j,
                            "extreme": float(H[j:j + 3].max() if kind == "H" else L[j:j + 3].min())})
    out.sort(key=lambda x: x["ago"])
    return out

def _mss(d5t, sw, mh, ml):
    """MSS: بعد از سوییپ، بسته‌شدن کندل خلاف آخرین کف/سقف کوچک قبل از سوییپ."""
    C = d5t.Close.values; j = sw["j"]
    if sw["bias"] == -1:
        c = [p for i, p in ml if i < j]
        return bool(c) and bool((C[j + 1:] < c[-1]).any())
    c = [p for i, p in mh if i < j]
    return bool(c) and bool((C[j + 1:] > c[-1]).any())

def _zones(df, tf, a, lookback):
    """FVG و OB تقریبی (جاری و پرنشده)."""
    H, L, O, C = df.High.values, df.Low.values, df.Open.values, df.Close.values; N = len(df); out = []
    for i in range(max(2, N - lookback), N):
        if L[i] > H[i - 2] and L[i] - H[i - 2] >= 0.15 * a and (i == N - 1 or L[i + 1:].min() > H[i - 2]):
            out.append({"type": "FVG", "dir": 1, "tf": tf, "lo": float(H[i - 2]), "hi": float(L[i])})
            if C[i - 2] < O[i - 2] and C[i - 1:].min() > L[i - 2]: out.append({"type": "OB", "dir": 1, "tf": tf, "lo": float(L[i - 2]), "hi": float(H[i - 2])})
        if H[i] < L[i - 2] and L[i - 2] - H[i] >= 0.15 * a and (i == N - 1 or H[i + 1:].max() < L[i - 2]):
            out.append({"type": "FVG", "dir": -1, "tf": tf, "lo": float(H[i]), "hi": float(L[i - 2])})
            if C[i - 2] > O[i - 2] and C[i - 1:].max() < H[i - 2]: out.append({"type": "OB", "dir": -1, "tf": tf, "lo": float(L[i - 2]), "hi": float(H[i - 2])})
    return out

def _rsi(c, n=14):
    s = pd.Series(c); d = s.diff()
    up = d.clip(lower=0).ewm(alpha=1 / n, adjust=False).mean(); dn = (-d.clip(upper=0)).ewm(alpha=1 / n, adjust=False).mean()
    return float(np.nan_to_num((100 - 100 / (1 + up / dn.replace(0, np.nan))).iloc[-1], nan=100.0))

def _session():
    n = dt.datetime.now(ZoneInfo("America/New_York")); h = n.hour + n.minute / 60
    if n.weekday() >= 5: return "weekend (thin liquidity)"
    if 3 <= h < 4: return "London killzone (Silver Bullet window 03-04 NY)"
    if 10 <= h < 11: return "NY AM Silver Bullet window (10-11 NY)"
    if 14 <= h < 15: return "NY PM Silver Bullet window (14-15 NY)"
    if 12 <= h < 13.5: return "NY lunch (low-probability chop)"
    if 2 <= h < 5: return "London killzone"
    if 7 <= h < 10: return "New York AM killzone"
    if 13.5 <= h < 16: return "New York PM killzone"
    if h >= 20: return "Asia session"
    return "outside killzones"

_session_base = _session
def _session():
    s_ = _session_base()
    if ASSET in ("US30", "NAS100", "USOIL"):
        n = dt.datetime.now(ZoneInfo("America/New_York")); h = n.hour + n.minute / 60
        if n.weekday() < 5:
            if 9.5 <= h < 10: s_ += " | US cash open 09:30 NY (opening volatility, wait for the first 15m to define the range)"
            elif 15.5 <= h < 16: s_ += " | into the US cash close (positioning/volatility)"
            elif 17 <= h < 18: s_ += " | CME futures daily break 17:00-18:00 NY (no data)"
            if ASSET == "USOIL" and n.weekday() == 2 and 10 <= h < 11.5: s_ += " | EIA crude inventory release 10:30 NY (spike risk)"
    return s_

# ================= v11.2: RSI اجباری + نقشهٔ استاپ‌های عموم + SL هوشمند =================
def _rsi_series(c, n=14):
    s_ = pd.Series(c, dtype=float); d = s_.diff()
    up = d.clip(lower=0).ewm(alpha=1 / n, adjust=False).mean(); dn = (-d.clip(upper=0)).ewm(alpha=1 / n, adjust=False).mean()
    return (100 - 100 / (1 + up / dn.replace(0, np.nan))).fillna(100.0).values

def _rsi_div(df, n=3, recent=24):
    """واگرایی RSI روی کندل‌های ۱۵م: 'bear' = سقف قیمت بالاتر ولی سقف RSI پایین‌تر | 'bull' = کف قیمت پایین‌تر ولی کف RSI بالاتر. فقط اگر آخرین پیوت در `recent` کندل اخیر باشد."""
    try:
        ph, pl = _pivots(df, n); r = _rsi_series(df.Close.values); N = len(df)
        if len(ph) >= 2 and ph[-1][0] >= N - recent and ph[-1][1] > ph[-2][1] and r[ph[-1][0]] < r[ph[-2][0]] - 2: return "bear"
        if len(pl) >= 2 and pl[-1][0] >= N - recent and pl[-1][1] < pl[-2][1] and r[pl[-1][0]] > r[pl[-2][0]] + 2: return "bull"
    except Exception: pass
    return None

def rsi_check(S, side):
    """بررسی اجباری RSI روی ۵م/۱۵م/۱س + واگرایی ۱۵م. خروجی: (خط نمایش، فهرست پرچم‌ها). هرگز سیگنال را نمی‌کشد؛ فقط پرچم ریسک می‌دهد."""
    r5, r15, r1h, dv = S["rsi"], S.get("rsi15", S["rsi"]), S.get("rsi1h", S["rsi"]), S.get("rsi_div"); fl = []
    zone = lambda r: "اشباع خرید" if r >= 70 else "اشباع فروش" if r <= 30 else "خنثی"
    if side == 1:
        if r15 >= RSI_15M_EXT or r1h >= RSI_1H_EXT: fl.append(f"RSI کشیده است و این خرید دنبال‌کردن حرکت است (۱۵م {r15:.0f}، ۱س {r1h:.0f}؛ اشباع خرید)")
        if dv == "bear": fl.append("واگرایی نزولی RSI روی ۱۵م (سقف قیمت بالاتر، سقف RSI پایین‌تر) خلاف خرید است")
    else:
        if r15 <= 100 - RSI_15M_EXT or r1h <= 100 - RSI_1H_EXT: fl.append(f"RSI کشیده است و این فروش دنبال‌کردن حرکت است (۱۵م {r15:.0f}، ۱س {r1h:.0f}؛ اشباع فروش)")
        if dv == "bull": fl.append("واگرایی صعودی RSI روی ۱۵م (کف قیمت پایین‌تر، کف RSI بالاتر) خلاف فروش است")
    sup = " · ✅ واگرایی RSI هم‌جهت با سیگنال" if ((side == 1 and dv == "bull") or (side == -1 and dv == "bear")) else (" · ⚠ واگرایی RSI خلاف سیگنال" if dv else "")
    return f"📊 RSI  ۵م {r5:.0f} ({zone(r5)}) · ۱۵م {r15:.0f} ({zone(r15)}) · ۱س {r1h:.0f} ({zone(r1h)}){sup}", fl

def _round_step(a):
    base = float(ROUND_STEP.get(ASSET, 0) or 0)
    if base <= 0: base = 10 ** float(np.floor(np.log10(max(a * 4, 1e-9))))
    for f_ in (1, 2, 5, 10, 20, 50, 100):
        if base * f_ >= 2 * a: return base * f_
    return base * 100

def crowd_pools(S, e, a, side):
    """نقشهٔ «جایی که عموم استاپ می‌گذارند» پشت ورود (برای خرید زیر ورود، برای فروش بالای ورود): سوینگ‌های ۵م/۱۵م/۱س/۴س، سقف/کف‌های برابر، PDH/PDL/PWH/PWL، آسیا/لندن (همه از موتور ساختار)، اعداد رند و VAL/VAH/POC روز قبل.
    خروجی: [(فاصله از ورود به ATR، برچسب، قدرت)] مرتب از نزدیک به دور."""
    out = []; cap = 3.0
    for x in (S["below"] if side == 1 else S["above"]):
        d = side * (e - x["p"]) / a
        if d > 0.05: out.append((d, f"{x['id']} {x['names']}" + (f" ({x['eq'] + 1} سطح برابر)" if x["eq"] else ""), {"day": 4, "4h": 4, "1h": 3, "15m": 2}.get(x["tf"], 1.5) + min(x["eq"], 2)))
    st = _round_step(a); lo, hi = (e - cap * a, e) if side == 1 else (e, e + cap * a)
    k = int(np.floor(lo / st))
    for _ in range(12):
        p_ = k * st; k += 1
        if p_ < lo: continue
        if p_ > hi: break
        d = side * (e - p_) / a
        if d > 0.05: out.append((d, f"عدد رند {p_:g}", 2.0))
    pv = (S.get("auction") or {}).get("prev")
    if pv:
        for nm, p_ in (("VAL روز قبل", pv[2]), ("POC روز قبل", pv[0])) if side == 1 else (("VAH روز قبل", pv[1]), ("POC روز قبل", pv[0])):
            d = side * (e - p_) / a
            if 0.05 < d <= cap: out.append((d, nm, 2.0 if "V" in nm else 1.5))
    return sorted(out, key=lambda x: x[0])

def smart_stop(a, pools, d0, cap):
    """از فاصلهٔ d0 (ATR) شروع می‌کند. هر استخری که (الف) تا SL_BUFFER_ATR جلوی SL باشد (SL چسبیده به استخر = شکار) یا (ب) تا SL_SEEK_ATR پشت SL باشد (قیمت به آن کشیده می‌شود و در مسیر استاپ را می‌زند)،
    SL را پشت آن می‌برد (استخر + بافر) به شرط اینکه از سقف ریسک cap نگذرد؛ حداکثر SL_MAX_MOVES بار. خروجی: (فاصلهٔ نهایی SL، توضیح‌ها، استخرهایی که نشد پشتشان رفت)"""
    d = d0; notes = []; skipped = []
    for _ in range(SL_MAX_MOVES + 1):
        hit = next(((pd_, lab) for pd_, lab, w in pools if d - SL_BUFFER_ATR + 1e-6 < pd_ <= d + SL_SEEK_ATR), None)
        if hit is None: break
        pd_, lab = hit; nd = pd_ + SL_BUFFER_ATR
        if nd > cap + 1e-9: skipped.append((lab, pd_)); break
        if len(notes) >= SL_MAX_MOVES: break
        d = nd; notes.append(f"🛡 SL پشت «{lab}» ({pd_:.2f} ATR از ورود) گذاشته شد، با بافر {SL_BUFFER_ATR:g} ATR تا شکار استاپ نخورد: ریسک {d:.2f} ATR")
    return d, notes, skipped

def smc_engine(d5, d1, a, price, side, extras=False):
    d5t = d5.tail(600); r15 = _rs(d5, "15min").tail(300); r1h = _rs(d5, "60min").tail(168); r4h = _rs(d5, "240min").tail(120); tol = 0.12 * a
    TFS = (("5m", d5t, _pivots(d5t, 3), pd.Timedelta("5min")), ("15m", r15, _pivots(r15, 3), pd.Timedelta("15min")), ("1h", r1h, _pivots(r1h, 2), pd.Timedelta("60min")), ("4h", r4h, _pivots(r4h, 2), pd.Timedelta("240min")))
    S = {"price": price, "a": a, "side": side, "session": _session(), "trend": {}, "swing": {}}
    lv, hx, lx = [], [], []
    for tf, df_, (ph, pl), td in TFS:
        S["trend"][tf] = _trend(ph, pl); S["swing"][tf] = (ph[-1][1] if ph else None, pl[-1][1] if pl else None)
        for kind, piv in (("H", ph), ("L", pl)):
            for o in _unswept(df_, piv, kind, price, tol): lv.append({"p": o["p"], "kind": kind, "eq": o["eq"], "tf": tf, "name": f"{tf} swing"})
        hx += [(int(d5t.index.searchsorted(df_.index[i] + td)), p, f"{tf} swing") for i, p in ph]
        lx += [(int(d5t.index.searchsorted(df_.index[i] + td)), p, f"{tf} swing") for i, p in pl]
    for nm, kind, p, swept, pos in _named_levels(d5t) + _extra_levels(d5, d5t):
        (hx if kind == "H" else lx).append((pos, p, nm))
        if not swept and ((kind == "H" and p > price) or (kind == "L" and p < price)): lv.append({"p": p, "kind": kind, "eq": 0, "tf": "day", "name": nm})
    mg = _merge(lv, a)
    above = sorted([x for x in mg if x["kind"] == "H" and x["p"] > price], key=lambda x: x["p"])[:4]
    below = sorted([x for x in mg if x["kind"] == "L" and x["p"] < price], key=lambda x: -x["p"])[:4]
    for i, x in enumerate(above, 1): x["id"] = f"H{i}"; x["d"] = (x["p"] - price) / a
    for i, x in enumerate(below, 1): x["id"] = f"L{i}"; x["d"] = (price - x["p"]) / a
    S["above"], S["below"] = above, below
    mh, ml = _pivots(d5t, 2)
    S["sweeps"] = _sweeps(d5t, hx, lx, SWEEP_LOOKBACK)[:3]
    for s in S["sweeps"]: s["mss"] = _mss(d5t, s, mh, ml); s["disp"] = _disp_fvg(d5t, s, a)
    zs = [x for x in _zones(d5t, "5m", a, 60) + _zones(r15, "15m", a, 40) + _ifvg(d5t, "5m", a, 60) + _ifvg(r15, "15m", a, 40)
          if x["dir"] == side and ((x["hi"] < price - 0.05 * a) if side == 1 else (x["lo"] > price + 0.05 * a))]
    zs.sort(key=lambda x: (price - x["hi"]) if side == 1 else (x["lo"] - price))
    nf = no = ni = 0; picked = []
    for x in zs:
        if x["type"] == "FVG" and nf < 2: nf += 1; x["id"] = f"F{nf}"; picked.append(x)
        elif x["type"] == "OB" and no < 2: no += 1; x["id"] = f"O{no}"; picked.append(x)
        elif x["type"] == "IFVG" and ni < 2: ni += 1; x["id"] = f"I{ni}"; picked.append(x)
    for x in picked: x["d"] = ((price - x["hi"]) if side == 1 else (x["lo"] - price)) / a
    S["zones"] = picked
    S["ids"] = {**{x["id"]: x["p"] for x in above + below}, **{x["id"]: (x["lo"], x["hi"]) for x in picked}}
    for nm, df_ in (("15m", r15.tail(48)), ("1h", r1h.tail(24))):
        hi_, lo_ = float(df_.High.max()), float(df_.Low.min())
        S["range" + nm] = (lo_, hi_, float(np.clip((price - lo_) / (hi_ - lo_), 0, 1)) if hi_ > lo_ else 0.5)
    c = d5t.Close.values; n = IMPULSE_BARS
    S["mv"] = float((price - c[-n]) / a)
    d = np.sign(np.diff(c)); k = 0
    while k < len(d) and d[-1] != 0 and d[-1 - k] == d[-1]: k += 1
    S["streak"] = int(k * d[-1]); S["ext"] = float((c[-1] - ema(d5t.Close, 20).iloc[-1]) / a); S["rsi"] = _rsi(c); S["rsi15"] = _rsi(r15.Close.values); S["rsi1h"] = _rsi(r1h.Close.values); S["rsi_div"] = _rsi_div(r15)
    S["opens"] = _opens(d5, price, a); S["er"] = S["atr_pct"] = None; S["auction"] = {}; S["smt"] = None; S["deriv"] = None
    if REGIME_ON:
        try: S["er"], S["atr_pct"] = _regime(d5t, d5, a)
        except Exception: pass
    if PROFILE_ON:
        try: S["auction"] = _vwap_profile(d5)
        except Exception: pass
    if extras:      # شبکه (جفت SMT و مشتقات) فقط وقتی ایجنت صدا زده می‌شود، نه در هر requote
        if SMT_ON:
            try: S["smt"] = _smt(d5t, _pair_df())
            except Exception: pass
        if DERIV_ON:
            try: S["deriv"] = derivatives()
            except Exception: pass
    S["px1h"] = float(c[-1] / c[-13] - 1) if len(c) > 13 else 0.0
    S["c5"] = [(t.strftime("%H:%M"), *map(float, r)) for t, r in zip(d5t.index[-12:], d5t[["Open", "High", "Low", "Close"]].values[-12:])]
    S["c15"] = [(t.strftime("%H:%M"), *map(float, r)) for t, r in zip(r15.index[-8:], r15[["Open", "High", "Low", "Close"]].values[-8:])]
    return S

def _smc_report(S):
    P, a, f = S["price"], S["a"], (lambda x: f"{x:,.{PXD}f}"); L = [f"ASSET {ASSET} | live {f(P)} | ATR15m {a:.{PXD}f} ({a / P * 100:.2f}% of price) | session (NY time): {S['session']}"]
    for tf in ("5m", "15m", "1h", "4h"):
        sh, sl_ = S["swing"][tf]; L.append(f"STRUCTURE {tf}: {S['trend'][tf][1]} | last swing high {f(sh) if sh else '-'} | last swing low {f(sl_) if sl_ else '-'}")
    for nm in ("15m", "1h"):
        lo_, hi_, ps = S["range" + nm]; L.append(f"DEALING RANGE {nm} ({'12h' if nm == '15m' else '24h'}): low {f(lo_)} high {f(hi_)} | price at {ps:.0%} of range (0%=discount low, 100%=premium high)")
    if S["opens"]: L.append("REFERENCE OPENS (price vs open, ATR): " + " | ".join(f"{n} {f(p_)} ({d_:+.2f})" for n, p_, d_ in S["opens"]))
    if S["er"] is not None: L.append(f"REGIME: efficiency ratio 3h {S['er']:.2f} (>0.30 trending, <0.15 choppy) | ATR15m percentile vs last 5 days {S['atr_pct']:.0%} (>80% expansion, <20% compression)")
    au = S["auction"]
    if au.get("vwap"): v_, sd_ = au["vwap"]; L.append(f"VWAP (UTC day): {f(v_)} | price {(P - v_) / a:+.2f} ATR from VWAP | 1-sigma band {f(v_ - sd_)} to {f(v_ + sd_)} | price is {'above' if P > v_ else 'below'} VWAP")
    if au.get("prev"): L.append(f"PREV-DAY VOLUME PROFILE: POC {f(au['prev'][0])} | VAH {f(au['prev'][1])} | VAL {f(au['prev'][2])} | price is {'above VAH' if P > au['prev'][1] else 'below VAL' if P < au['prev'][2] else 'inside value area'}")
    if S.get("smt"): L.append(f"SMT vs {S['smt']['pair']} (last 1h vs prior 4h): highs -> {S['smt']['hi']} | lows -> {S['smt']['lo']}   (asset-only = asset made a new extreme and the pair did not = divergence; pair-only = pair led and the asset failed; both = confirmed)")
    elif SMT_ON: L.append("SMT: no data")
    if S.get("deriv"):
        d_ = S["deriv"]; L.append(f"DERIVATIVES ({d_['src']} perp): funding {d_['funding'] * 100:+.4f}% per interval" + (f" | open interest change 1h {d_['oi_chg_1h']:+.2%}" if "oi_chg_1h" in d_ else " | OI change n/a") + f" | price change 1h {S['px1h']:+.2%}")
    elif DERIV_ON and ASSET in DERIV_ID: L.append("DERIVATIVES: no data (exchange unreachable)")
    L.append(f"MOMENTUM 5m: net move over last {IMPULSE_BARS} bars {S['mv']:+.2f} ATR | consecutive same-direction closes {S['streak']:+d} | close vs EMA20 {S['ext']:+.2f} ATR | RSI14 {S['rsi']:.0f}")
    L.append(f"RSI14 (MANDATORY CHECK): 5m {S['rsi']:.0f} | 15m {S.get('rsi15', S['rsi']):.0f} | 1h {S.get('rsi1h', S['rsi']):.0f} | 15m divergence: {({'bear': 'BEARISH (price higher high, RSI lower high)', 'bull': 'BULLISH (price lower low, RSI higher low)'}).get(S.get('rsi_div'), 'none')} | overbought >=70, oversold <=30")
    for nm, arr in (("LIQUIDITY ABOVE (unswept buy-side)", S["above"]), ("LIQUIDITY BELOW (unswept sell-side)", S["below"])):
        L.append(nm + ":" + ("" if arr else " none found"))
        for x in arr: L.append(f"  {x['id']} {f(x['p'])} ({x['d']:.2f} ATR away; {x['names']}; equal-level count {x['eq']})")
    try:
        _cp = crowd_pools(S, P, a, S["side"]); L.append(f"CROWD STOP MAP (where most traders place their stops for a {'long' if S['side'] == 1 else 'short'} at the live price; your stop must go BEYOND the nearest of these with a buffer, never inside or at one, never exactly on a round number):" + ("" if _cp else " none found"))
        for d_, lab_, w_ in _cp[:6]: L.append(f"  {f(P - S['side'] * d_ * a)} ({d_:.2f} ATR behind entry; {lab_}; strength {w_:g})")
    except Exception: pass
    L.append("RECENT LIQUIDITY SWEEPS (last %d bars):" % SWEEP_LOOKBACK + ("" if S["sweeps"] else " none"))
    for s in S["sweeps"]:
        L.append(f"  {'buy-side (highs) taken -> bearish' if s['bias'] == -1 else 'sell-side (lows) taken -> bullish'}: level {f(s['level'])} ({s['name']}), wick extreme {f(s['extreme'])}, {s['ago'] * 5} min ago, MSS after sweep: {'YES' if s['mss'] else 'no'}, displacement FVG after sweep: {'YES' if s['disp'] else 'no'}" + (" => A+ MODEL COMPLETE (sweep -> displacement -> MSS)" if s['mss'] and s['disp'] else ""))
    L.append("ENTRY ARRAYS in trade direction (unmitigated):" + ("" if S["zones"] else " none"))
    for x in S["zones"]: L.append(f"  {x['id']} {x['tf']} {'bullish' if x['dir'] == 1 else 'bearish'} {x['type']} [{f(x['lo'])} - {f(x['hi'])}] ({x['d']:.2f} ATR from price)")
    L.append("LAST 12 CLOSED 5m CANDLES (UTC time O H L C):"); L += ["  %s %s %s %s %s" % (t, f(o), f(h), f(l), f(c)) for t, o, h, l, c in S["c5"]]
    L.append("LAST 8 CLOSED 15m CANDLES:"); L += ["  %s %s %s %s %s" % (t, f(o), f(h), f(l), f(c)) for t, o, h, l, c in S["c15"]]
    return "\n".join(L)

SMC_PROMPT = """You are a senior scalp trader and risk gatekeeper, fluent in ICT (liquidity pools, sweeps/Judas swing, MSS/CHoCH, displacement, FVG and inversion FVG, order blocks, premium/discount, killzones and Silver Bullet windows, SMT divergence, NY-midnight/day/week opens), Smart Money Concepts (BOS/CHoCH, internal vs external structure, mitigation), Wyckoff (range, spring/upthrust), Auction Market Theory (VWAP, value area, POC), classic price action (Dow structure, support/resistance, EMA, RSI), plus market-regime and derivatives (funding, open interest) context.
A multi-agent team proposes a <<SIDE>> on <<ASSET>> (rating: <<RATING>>). Your job is to protect the account from low-quality ENTRIES and badly placed STOPS, and equally to give the desk the courage to take structurally valid sweeps-and-displacement setups. You do not judge news or fundamentals.

Two real failures to avoid:
1) A limit order placed INTO a still-running impulse (for example a SELL limit above price while 5m candles keep closing higher) with no exhaustion, sweep or MSS: the impulse fills it and runs through the stop.
2) A stop resting just beyond an obvious liquidity pool (equal highs/lows, range extreme, day/week/session high or low) that gets swept in a V-shaped stop run, after which price returns to the original direction.

Pattern that has worked in recent live setups (mirror it for longs): with the 1h/4h structure and most timeframes aligned, a limit order at a premium (short) or discount (long) array or at a retest of a lower high / higher low, the stop BEYOND the swept liquidity or swing, targets 1.5R and 3R toward unswept liquidity on the other side. Treat it as a pattern to recognise, not as a reason to say GO without evidence.

Use ONLY the data below. The data contains a mandatory RSI line and a CROWD STOP MAP: you MUST say in your summary or risks whether RSI (5m/15m/1h and any divergence) supports or contradicts the entry (RSI stretched in the trade direction, or a divergence against it, is a RISK to flag, not a veto), and the stop you recommend MUST sit beyond the nearest crowd-stop pool with a buffer, never inside or at a pool and never exactly on a round number. Never invent prices or data; refer to levels by their IDs (H1, L2, F1, O1, I1 ...). If a data block says "no data", say so and judge without it.

<<REPORT>>

SCALP HORIZON (the owner's hard rule): the owner scalps with a relatively large position, so every trade must be settled within 1-2 hours: the limit order lives 30 minutes, and if TP1 (1.5R) is not reached within 2 hours after the fill the trade is closed at market. The stop is scalp-sized (about 0.8 ATR of the 15m chart, up to 1.3 when a liquidity pool must be cleared). Judge every setup by REACH: can TP1 and TP2 (3R) realistically be hit inside two hours given the ATR, the session and the nearest opposing liquidity? If the structural stop is wider than about 1.3 ATR the setup is too slow for this desk: lower the grade or WAIT and name the tighter entry (after sweep + MSS, at the FVG/OB) that would make the stop tight. Never choose a wide stop just to be safe. 
Proposed limit entry is about <<ENTRY>>; default stop is the scalp stop = <<RISK>> away; targets are 1.5R and 3R.

Evidence hierarchy:
 A. Primary (can create a GO): higher-timeframe bias; liquidity taken and liquidity targeted; the complete A+ ICT sequence (sweep -> displacement FVG -> MSS, then entry on the FVG/OB/IFVG) or a trend-continuation pullback into an unmitigated array.
 B. Location (improves or damages the entry): premium/discount in the dealing range, price vs VWAP and its bands, price vs previous-day value area/POC, price vs NY-midnight/day/week opens (shorts are better from above these opens in a bearish day, longs from below in a bullish day).
 C. Context (only adjusts confidence, never alone creates or vetoes a GO unless it flatly contradicts A): SMT divergence (a divergence in the trade direction supports it, a confirmed break by both assets against it warns), regime (efficiency ratio and ATR percentile: a choppy, compressed market punishes continuation entries; an expanding trending one favours them), derivatives (price falling with open interest rising = new shorts, continuation; price falling with open interest falling = liquidation, exhaustion risk; extreme funding = crowded side that can squeeze), session timing (killzones and Silver Bullet windows are better than NY lunch or weekends).

Decide:
- GO: a clear primary reason exists now, the entry is not in front of a running impulse, and the stop can sit beyond a liquidity pool at most <<MAXR>> ATR away.
- WAIT: the idea may be valid but the trigger has not formed yet; state the exact trigger.
- NO: structure or momentum argues against the trade.
Be sharp, not timid: if the primary reason is clear and only secondary evidence is mixed, answer GO with a lower confidence; use WAIT only when the trigger truly has not formed. OWNER'S LIVE EVIDENCE (v11): in the owner's last three live trades (BTC, ETH and Gold SHORTS, all 5m, entered at a premium after a sweep of the highs and a displacement leg down, stop beyond the swept high, limit order) EVERY ONE reached 3R (BTC 62272 -> 61362, ETH 1762.7 -> 1729.8, Gold 3615 -> 3537) although this desk had estimated a low probability and the owner took them anyway. Small sample, but the lesson is real: over-cautious probability estimates cost money, and a setup with a clear structural reason and 1:3 room is a GOOD trade even at 35-45%. Be confident, decisive and energetic; present risks as a management plan, never as discouragement. Stay honest: never invent levels or evidence. Confidence 8-10 is allowed only when at least three independent confirmations agree. Judge each school separately.

Reply with ONE JSON object only (no markdown, no extra text) with these keys:
{"verdict":"GO|WAIT|NO","confidence":<1-10>,"confluence":<integer count of independent confirmations, 0-8>,
"schools":{"ICT":"<bias bullish/bearish/neutral + reason, in Persian, max 20 words>","SMC":"...","Wyckoff":"...","Classic":"...","Momentum":"...","Auction":"<VWAP/value area/POC view>","SMT":"...","Regime":"...","Derivatives":"..."},
"sl_anchor":"<ID of the liquidity level the stop must sit beyond (e.g. L2 for a long, H1 for a short) or null>",
"entry_zone":"<ID of an FVG/OB/IFVG entry array (e.g. F1, O1 or I1) or null to keep the default entry>",
"trigger":"<in Persian: what must happen before entering (for WAIT/NO), else empty>",
"risks":"<in Persian: the main risk, max 20 words>",
"summary":"<in Persian: two short sentences>"}"""

RG_READ_TIMEOUT = 300          # v22: سقف انتظار یک تماس از طریق Rayegan (خودش در صورت خطا بین مدل‌ها جابه‌جا می‌شود)
def _rg_chat(prompt, model="auto"):
    """v22: تماس با گیت‌وی Rayegan (سازگار با OpenAI). اگر گیت‌وی خاموش شده بود (ریست Colab) یک‌بار دوباره بالا می‌آورد."""
    import requests as _rq
    base = os.environ.get("TRADINGAGENTS_LLM_BACKEND_URL", "http://127.0.0.1:8787/v1").rstrip("/")
    body = {"model": "auto", "messages": [{"role": "user", "content": prompt}]}
    for att in (1, 2):
        try: r = _rq.post(base + "/chat/completions", json=body, headers={"Authorization": "Bearer rayegan"}, timeout=(5, RG_READ_TIMEOUT)); break
        except _rq.ConnectionError:
            if att == 2 or "rg_ensure" not in globals(): raise
            rg_ensure()
    if r.status_code != 200:
        try: msg = r.json().get("error", {}).get("message", "")
        except Exception: msg = r.text
        raise RuntimeError(f"Rayegan HTTP {r.status_code}: {str(msg)[:160]}")
    c = (r.json()["choices"][0]["message"].get("content")) or ""
    if isinstance(c, list): c = "".join(x.get("text", "") if isinstance(x, dict) else str(x) for x in c)
    return re.sub(r"<think>.*?</think>", "", str(c), flags=re.S).strip()

def _llm_json(prompt, model):
    if globals().get("LLM_PROVIDER") == "rayegan":
        c = _rg_chat(prompt, model); m = re.search(r"\{.*\}", c, re.S)
        return json.loads(m.group(0)), c
    from langchain_google_genai import ChatGoogleGenerativeAI
    c = None
    for kw in ({"thinking_level": "medium"}, {}):     # اگر نسخهٔ کتابخانه این پارامتر را نشناخت، بدونش تلاش می‌کند
        try: c = ChatGoogleGenerativeAI(model=model, timeout=LLM_CALL_TIMEOUT, max_retries=2, **kw).invoke(prompt).content; break
        except Exception as e:
            if not kw or not any(w in str(e).lower() for w in ("thinking", "unexpected", "extra", "validation", "unsupported")): raise
    if isinstance(c, list): c = "".join(x.get("text", "") if isinstance(x, dict) else str(x) for x in c)
    m = re.search(r"\{.*\}", c, re.S)
    return json.loads(m.group(0)), c

def smc_prepare(pr=None):
    """یک‌بار بعد از تیم عامل‌ها: ایجنت ICT/SMC روی گزارش موتور قضاوت می‌کند. نتیجه در AG['smc'] نگه داشته می‌شود (دوباره صدایش نمی‌زنیم)."""
    AG["smc_tried"] = True; AG["smc"] = None; AG["smc_err"] = ""; AG["smc_t"] = utcnow()
    if not (SMC_GATES and SMC_AGENT and USE_AGENTS and AG["ok"]): return
    try:
        now, age = snapshot(); side = AG["side"]
        if side == 0 or age > MAX_AGE_MIN or (now.votes * side < MIN_ALIGN and not M()["reversal"]): return        # requote خودش دلیل را می‌گوید
        print("ایجنت ICT/SMC در حال بررسی ساختار بازار (نقدینگی، سوییپ، MSS، FVG/OB، پریمیوم/دیسکانت) ...")
        a = float(now.atr); price = pr if pr is not None else live_price(now.c)[0]; S = smc_engine(DATA[0], DATA[1], a, price, side, extras=True)
        e20 = float(now.ema20) + (2 / 21) * (price - float(now.ema20)); e_def = float(entry_price(price, e20, a, side)); rep = _smc_report(S)
        prompt = (SMC_PROMPT.replace("<<SIDE>>", "LONG (buy)" if side == 1 else "SHORT (sell)").replace("<<ASSET>>", ASSET_DESC.get(ASSET, ASSET)).replace("<<RATING>>", str(AG["rating"]))
                  .replace("<<REPORT>>", rep).replace("<<ENTRY>>", f"{e_def:,.{PXD}f}").replace("<<RISK>>", f"{SL_ATR * a:,.{PXD}f}").replace("<<MAXR>>", f"{MAX_RISK_ATR:g}"))
        deep = os.environ.get("TRADINGAGENTS_DEEP_THINK_LLM", "gemini-3.5-flash-lite"); quick = os.environ.get("TRADINGAGENTS_QUICK_THINK_LLM", deep)
        last = ""; j = None
        for k, model in enumerate((deep, deep, quick)):
            try:
                j, raw = _llm_json(prompt, model)
                if str(j.get("verdict", "")).upper() not in ("GO", "WAIT", "NO"): raise ValueError("verdict نامعتبر: " + str(j.get("verdict")))
                break
            except Exception as e:
                last = f"{type(e).__name__}: {str(e)[:200]}"; j = None; print(f"⚠ ایجنت ICT/SMC تلاش {k + 1}: {last}"); time.sleep(5)
        if j is None: AG["smc_err"] = last; return
        ids = S["ids"]; res = {"verdict": str(j["verdict"]).upper(), "confidence": j.get("confidence", "?"), "confluence": j.get("confluence", "?"), "schools": j.get("schools") or {},
                               "trigger": str(j.get("trigger") or ""), "risks": str(j.get("risks") or ""), "summary": str(j.get("summary") or ""),
                               "sl_price": None, "entry_price": None, "report": rep, "t": utcnow()}
        an, ez = j.get("sl_anchor"), j.get("entry_zone")
        if isinstance(ids.get(an), float) and side * (e_def - ids[an]) > 0.3 * a: res["sl_price"] = ids[an] - side * SL_BUFFER_ATR * a
        if isinstance(ids.get(ez), tuple):
            mid = (ids[ez][0] + ids[ez][1]) / 2
            if 0.1 * a <= side * (price - mid) <= 1.0 * a: res["entry_price"] = mid
        AG["smc"] = res
    except Exception as e:
        AG["smc_err"] = f"{type(e).__name__}: {str(e)[:250]}"; print("⚠ ایجنت ICT/SMC خطا داد:", AG["smc_err"])

def _smc_stale():
    """ایجنت ICT/SMC فقط وقتی دوباره صدا زده می‌شود که: هنوز اجرا نشده، یا حکمش GO نبوده/کهنه شده (تا بعد از «صبر» و برگشت بازار حکم قدیمی نچسبد)، با حداقل فاصلهٔ SMC_MIN_GAP_MIN دقیقه."""
    if CEO_ON and USE_AGENTS and AG["ok"] and not AG.get("ceo_tried"): return True
    if DESK_ON and USE_AGENTS and AG["ok"]:        # v8.1: مدیر سبد حکم نهایی را می‌دهد؛ اگر TAKE نبود یا کهنه شد، دوباره سنجیده می‌شود
        if not AG.get("desk_tried"): return True
        lt = AG.get("desk_t"); gp = (utcnow() - lt).total_seconds() / 60 if lt else 999.0
        if gp < SMC_MIN_GAP_MIN: return False
        d_ = AG.get("desk"); return d_ is None or d_["decision"] != "TAKE" or (utcnow() - d_["t"]).total_seconds() / 60 > SMC_REFRESH_MIN
    if not AG["smc_tried"]: return True
    last = AG.get("smc_t"); gap = (utcnow() - last).total_seconds() / 60 if last else 999.0
    if gap < SMC_MIN_GAP_MIN: return False
    ai = AG.get("smc")
    return ai is None or ai["verdict"] != "GO" or (utcnow() - ai["t"]).total_seconds() / 60 > SMC_REFRESH_MIN

# ================= میز مناظره + مدیر سبد (v8.1) =================
def _llm_raw(prompt, model):
    if globals().get("LLM_PROVIDER") == "rayegan": return _rg_chat(prompt, model)
    from langchain_google_genai import ChatGoogleGenerativeAI
    c = None
    for kw in ({"thinking_level": "medium"}, {}):
        try: c = ChatGoogleGenerativeAI(model=model, timeout=LLM_CALL_TIMEOUT, max_retries=2, **kw).invoke(prompt).content; break
        except Exception as e:
            if not kw or not any(w in str(e).lower() for w in ("thinking", "unexpected", "extra", "validation", "unsupported")): raise
    if isinstance(c, list): c = "".join(x.get("text", "") if isinstance(x, dict) else str(x) for x in c)
    return str(c).strip()

def _ask(prompt, model, tries=2):
    last = ""
    for _ in range(tries):
        try: return _llm_raw(prompt, model)
        except Exception as e: last = f"{type(e).__name__}: {str(e)[:120]}"; time.sleep(4)
    return f"(پاسخ نرسید: {last})"

def _models():
    deep = os.environ.get("TRADINGAGENTS_DEEP_THINK_LLM", "gemini-3.5-flash-lite"); return deep, os.environ.get("TRADINGAGENTS_QUICK_THINK_LLM", deep)

TACT_OPEN = """You are the TACTICAL analyst of a scalp desk (technical analysis, ICT/SMC, volume/VWAP). The desk is considering a <<SIDE>> on <<ASSET>> (team rating: <<RATING>>).
Use ONLY the data below. In Persian, max 110 words, argue honestly for or against the trade: bias on 5m/15m/1h/4h, the entry array, WHERE the stop should sit (liquidity ID, beyond which pool) and where the 1.5R/3R targets sit relative to the nearest opposing pools, and the single biggest tactical risk.
ENGINE REPORT:
<<REPORT>>
TEAM TECHNICAL REPORT:
<<MARKET>>"""
FUND_OPEN = """You are the FUNDAMENTAL / NEWS / SENTIMENT analyst of a scalp desk. The desk is considering a <<SIDE>> on <<ASSET>> (team rating: <<RATING>>); the holding horizon is 1-5 hours.
Use ONLY the reports below. In Persian, max 110 words, argue honestly for or against the trade: macro/news bias, any scheduled or very recent high-impact event close to now, sentiment crowding, and the single biggest fundamental risk during the next hours. If the news is irrelevant for such a short horizon, say that plainly.
NEWS: <<NEWS>>
SENTIMENT: <<SENT>>
FUNDAMENTALS/MACRO: <<FUND>>"""
CROSS = """You are the <<ME>> analyst in a desk debate about a <<SIDE>> on <<ASSET>>. Your colleague (the <<OTHER>> analyst) said:
"""
CROSS2 = """
Reply in Persian, max 120 words, in four parts: (1) what you accept from your colleague, (2) your two strongest objections, (3) one concrete improvement to THEIR view or to the trade (a better stop/target/entry/size or a missing check) that would help the desk, (4) what fact would change your mind. Be specific and critical but cooperative; no repetition of your opening."""

def desk_debate(rep, side):
    st = AG["state"]; ex_deep, quick = _models(); sd = "LONG (buy)" if side == 1 else "SHORT (sell)"; fill = lambda t: (t.replace("<<SIDE>>", sd).replace("<<ASSET>>", ASSET_DESC.get(ASSET, ASSET)).replace("<<RATING>>", str(AG["rating"])))
    pt = fill(TACT_OPEN).replace("<<REPORT>>", rep).replace("<<MARKET>>", _cut(st.get("market_report"), 1800) or "(empty)")
    pf = fill(FUND_OPEN).replace("<<NEWS>>", _cut(st.get("news_report"), 1500) or "(empty)").replace("<<SENT>>", _cut(st.get("sentiment_report"), 1200) or "(empty)").replace("<<FUND>>", _cut(st.get("fundamentals_report"), 1000) or "(empty)")
    with ThreadPoolExecutor(2) as ex: ft, ff = ex.submit(_ask, pt, quick), ex.submit(_ask, pf, quick); t1, f1 = ft.result(), ff.result()
    rounds = []; lt, lf = t1, f1
    for _ in range(max(0, DESK_ROUNDS)):
        ct = fill(CROSS).replace("<<ME>>", "TACTICAL").replace("<<OTHER>>", "FUNDAMENTAL") + lf + "\nYour own opening was:\n" + lt + CROSS2
        cf = fill(CROSS).replace("<<ME>>", "FUNDAMENTAL").replace("<<OTHER>>", "TACTICAL") + lt + "\nYour own opening was:\n" + lf + CROSS2
        with ThreadPoolExecutor(2) as ex: a_, b_ = ex.submit(_ask, ct, quick), ex.submit(_ask, cf, quick); t2, f2 = a_.result(), b_.result()
        rounds.append((t2, f2)); lt, lf = t2, f2
    return {"tact": t1, "fund": f1, "rounds": rounds}

OVERSEER = """You are the PORTFOLIO OVERSEER (desk head) of a scalp desk. You make the final call on a <<SIDE>> limit order on <<ASSET>> after reading the whole team, the specialist ICT/SMC agent, and a debate between the tactical and the fundamental analyst.

SCALP HORIZON (the owner's hard rule): the owner scalps with a relatively large position, so every trade must be settled within 1-2 hours: the limit order lives 30 minutes, and if TP1 (1.5R) is not reached within 2 hours after the fill the trade is closed at market. The stop is scalp-sized (about 0.8 ATR of the 15m chart, up to 1.3 when a liquidity pool must be cleared). Judge every setup by REACH: can TP1 and TP2 (3R) realistically be hit inside two hours given the ATR, the session and the nearest opposing liquidity? If the structural stop is wider than about 1.3 ATR the setup is too slow for this desk: lower the grade or WAIT and name the tighter entry (after sweep + MSS, at the FVG/OB) that would make the stop tight. Never choose a wide stop just to be safe. 
Economics of this desk: every trade risks 1R. TP1 = 1.5R closes half (then the stop moves to breakeven plus a small buffer), TP2 = 3R closes the rest. A trade that wins is worth +0.75R (TP1 then breakeven) or +2.25R (TP2); a loss is -1R. So the break-even hit-rate is only about 30-35%, and a setup you honestly estimate at 40% or more to reach TP1 is worth taking. Skipping a valid setup costs money just like a loss does. OWNER'S LIVE EVIDENCE (v11): in the owner's last three live trades (BTC, ETH and Gold SHORTS, all 5m, entered at a premium after a sweep of the highs and a displacement leg down, stop beyond the swept high, limit order) EVERY ONE reached 3R (BTC 62272 -> 61362, ETH 1762.7 -> 1729.8, Gold 3615 -> 3537) although this desk had estimated a low probability and the owner took them anyway. Small sample, but the lesson is real: over-cautious probability estimates cost money, and a setup with a clear structural reason and 1:3 room is a GOOD trade even at 35-45%. Be confident, decisive and energetic; present risks as a management plan, never as discouragement. Stay honest: never invent levels or evidence.
<<MODE>>
RSI is a MANDATORY check: always weigh the RSI readings and divergence in the data (RSI stretched in the trade direction or an opposing divergence = a risk to manage, not a veto), and judge the stop against the CROWD STOP MAP (where most traders place their stops): a stop inside or exactly at such a pool, or exactly on a round number, is a bad stop. Never take: an entry in front of a running impulse with no exhaustion/sweep/MSS; a stop sitting inside an obvious liquidity pool; a trade against the 1h/4h structure with no completed reversal sequence (sweep -> displacement -> MSS); a trade whose stop is so far that 1R is unmanageable.
Grades: A = a clear primary reason plus at least three independent confirmations, full size. B = a valid primary reason plus at least one confirmation or one notable conflict, half size. C = a valid primary reason but mostly unconfirmed or with real conflicts, quarter size. SKIP = no valid primary reason or an invalidation.

Do your own multi-timeframe check. For each of 5m, 15m, 1h, 4h, 1d give the bias in a few words. Then check the STOP: is it beyond the liquidity pools of the relevant timeframes (5m/15m swing, 1h/4h swing, PDH/PDL, PWH/PWL, Asia/London range, equal highs/lows) with a safe buffer, and could a sweep of a pool just beyond it still hit it? Then check the TARGETS: where are the nearest opposing pools (in R) relative to TP1 (1.5R) and TP2 (3R), and is there an unmitigated array or a higher-timeframe level in the way? Use the IDs (H1, L2, F1, O1, I1 ...) only from the engine report; never invent prices.
Judge the debate: who made the stronger, better-evidenced point, and did the objections change the plan? A fundamental objection alone should shrink the size, not cancel a valid structural setup, unless a high-impact scheduled event is imminent.

ENGINE REPORT:
<<REPORT>>

TIMEFRAME TREND VOTES (EMA20 vs EMA50 sign; 15m, 30m, 1h, 1d): <<VOTES>>
TEAM FINAL DECISION (portfolio manager of the base team): <<TEAM>>
ICT/SMC SPECIALIST: <<SMC>>
COUNCIL CHAIR OF THE MONTH (the style with the most winning trades this month; its vote carries extra weight; a chair that agrees with the trade is a strong sign, but never override a clear invalidation): <<CHAIR>>

DEBATE
Tactical opening: <<T1>>
Fundamental opening: <<F1>>
<<ROUNDS>>
Proposed limit entry is about <<ENTRY>>; default stop 1.0 ATR(15m) = <<RISK>>; the stop may be placed beyond a liquidity pool up to <<MAXR>> ATR away.

STRATEGY COUNCIL (13 style specialists, weighted agreement with this trade): <<COUNCIL>>

Reply with ONE JSON object only (no markdown):
{"decision":"TAKE|SKIP","grade":"A|B|C","confidence":<1-10>,"p_tp1":<integer 0-100, your honest estimate>,
"mtf":{"5m":"<Persian, max 8 words>","15m":"...","1h":"...","4h":"...","1d":"..."},
"sl_check":"<Persian, max 25 words>","tp_check":"<Persian, max 25 words>","debate_winner":"<Persian, max 25 words>",
"sl_anchor":"<ID of the liquidity level the stop must sit beyond, or null>","entry_zone":"<ID of an FVG/OB/IFVG, or null>",
"trigger":"<Persian: if SKIP, the exact trigger to wait for; else empty>","risks":"<Persian, max 20 words>","summary":"<Persian, two short sentences>"}"""
_MODE_TXT = {"bold": "MODE = BOLD. Be confident and decisive. Prefer TAKE with a smaller size over SKIP whenever the primary structure is valid but one secondary element is missing. Do not demand perfection; SKIP only for a real invalidation or when you cannot find a valid primary reason.",
             "balanced": "MODE = BALANCED. Take valid setups; use smaller grades for imperfect ones; SKIP when the primary reason is weak.",
             "careful": "MODE = CAREFUL. Take only grade A or B setups; grade C means SKIP."}

def desk_overseer(side, price, now, S, rep, deb):
    st = AG["state"]; deep, quick = _models(); a = float(now.atr); sd = "LONG (buy)" if side == 1 else "SHORT (sell)"
    e20 = float(now.ema20) + (2 / 21) * (price - float(now.ema20)); e_def = float(entry_price(price, e20, a, side)); smc = AG.get("smc")
    smc_t = (f"{smc['verdict']} (confidence {smc['confidence']}, confluence {smc.get('confluence', '?')}): {smc['summary']} | trigger: {smc['trigger']} | risks: {smc['risks']}" if smc else "not available")
    rounds = "\n".join(f"Round {i + 1} tactical critique: {t}\nRound {i + 1} fundamental critique: {f}" for i, (t, f) in enumerate(deb["rounds"]))
    prompt = (OVERSEER.replace("<<SIDE>>", sd).replace("<<ASSET>>", ASSET_DESC.get(ASSET, ASSET)).replace("<<MODE>>", _MODE_TXT.get(MODE, _MODE_TXT["bold"])).replace("<<REPORT>>", rep)
              .replace("<<VOTES>>", f"{now.d15m:+.0f}, {now.d30m:+.0f}, {now.d1h:+.0f}, {now.d1d:+.0f}").replace("<<TEAM>>", _cut(st.get("final_trade_decision"), 1500) or "(empty)").replace("<<SMC>>", smc_t)
              .replace("<<COUNCIL>>", ((lambda c_: (f"{c_['nf']} agree / {c_['na']} against / {c_['nn']} no view; weighted agreement {c_['agree']:.0%}; regime {c_['regime']}; agreeing styles: " + ", ".join(r['k'] for r in c_['rows'] if r['v'] == side) + "; opposing: " + ", ".join(r['k'] for r in c_['rows'] if r['v'] == -side)))(AG["council"]) if AG.get("council") else "not available"))
              .replace("<<T1>>", deb["tact"]).replace("<<F1>>", deb["fund"]).replace("<<ROUNDS>>", rounds).replace("<<ENTRY>>", f"{e_def:,.{PXD}f}").replace("<<RISK>>", f"{SL_ATR * a:,.{PXD}f}").replace("<<MAXR>>", f"{M()['risk_hard']:g}"))
    last = ""; j = None
    for k, model in enumerate((deep, deep, quick)):
        try:
            j, _ = _llm_json(prompt, model)
            if str(j.get("decision", "")).upper() not in ("TAKE", "SKIP") or str(j.get("grade", "")).upper() not in ("A", "B", "C"): raise ValueError("decision/grade نامعتبر")
            break
        except Exception as e: last = f"{type(e).__name__}: {str(e)[:200]}"; j = None; print(f"⚠ مدیر سبد تلاش {k + 1}: {last}"); time.sleep(5)
    if j is None: AG["desk_err"] = last; return None
    dec, gr = str(j["decision"]).upper(), str(j["grade"]).upper()
    if MODE == "careful" and gr == "C": dec = "SKIP"
    size = {"A": 1.0, "B": 0.5, "C": 0.25}[gr]
    try: p1 = int(float(j.get("p_tp1")))
    except Exception: p1 = "?"
    res = {"decision": dec, "grade": gr, "size": size, "confidence": j.get("confidence", "?"), "p_tp1": p1, "mtf": j.get("mtf") or {}, "sl_check": str(j.get("sl_check") or ""), "tp_check": str(j.get("tp_check") or ""),
           "debate_winner": str(j.get("debate_winner") or ""), "trigger": str(j.get("trigger") or ""), "risks": str(j.get("risks") or ""), "summary": str(j.get("summary") or ""),
           "sl_price": None, "entry_price": None, "t": utcnow()}
    ids = S["ids"]; an, ez = j.get("sl_anchor"), j.get("entry_zone")
    if isinstance(ids.get(an), float) and side * (e_def - ids[an]) > 0.3 * a: res["sl_price"] = ids[an] - side * SL_BUFFER_ATR * a
    if isinstance(ids.get(ez), tuple):
        mid = (ids[ez][0] + ids[ez][1]) / 2
        if 0.1 * a <= side * (price - mid) <= 1.0 * a: res["entry_price"] = mid
    return res

def _desk_prepare0(pr=None):
    """ایجنت ICT/SMC (اگر روشن) ← میز مناظره (فقط بار اول) ← حکم مدیر سبد. برای تازه‌کردن حکم هم صدا زده می‌شود."""
    if SMC_AGENT: smc_prepare(pr)
    AG["desk_tried"] = True; AG["desk"] = None; AG["desk_err"] = ""; AG["desk_t"] = utcnow()
    if not (DESK_ON and SMC_GATES and USE_AGENTS and AG["ok"]): return
    try:
        now, age = snapshot(); side = AG["side"]
        if side == 0 or age > MAX_AGE_MIN: return
        a = float(now.atr); price = pr if pr is not None else live_price(now.c)[0]; S = smc_engine(DATA[0], DATA[1], a, price, side, extras=True); rep = _smc_report(S)
        if not AG.get("debate"): print("میز مناظره: تکنیکال و بنیادی همدیگر را نقد می‌کنند ..."); AG["debate"] = desk_debate(rep, side)
        print("مدیر سبد در حال بررسی نهایی (چندتایم‌فریم، SL/TP نسبت به نقدینگی) ...")
        AG["desk"] = desk_overseer(side, price, now, S, rep, AG["debate"])
    except Exception as e: AG["desk_err"] = f"{type(e).__name__}: {str(e)[:250]}"; print("⚠ میز مناظره/مدیر سبد خطا داد:", AG["desk_err"])

def _hold_override():
    """جرأت کنترل‌شده: وقتی تیم «نگه‌دار» گفته ولی ≥۳ از ۴ تایم‌فریم هم‌جهت‌اند، جهت از هم‌جهتی تایم‌فریم‌ها می‌آید و بازهٔ تصمیم به میز مناظره + مدیر سبد (با حجم حداکثر نصف) سپرده می‌شود."""
    now, age = snapshot(); c = decide(now) or (lean(now) if TIERS_ON else 0)
    if c == 0 or age > MAX_AGE_MIN: return
    AG["override"] = True; AG["side"] = c; AG["rating"] = f"{AG['rating']} → {'Buy' if c == 1 else 'Sell'} (میز: تیم «نگه‌دار» گفت ولی تایم‌فریم‌ها هم‌جهت‌اند{'؛ حجم حداکثر نصف' if not TIERS_ON else '؛ رستهٔ ریسک‌بالا'})"
    print(f"ℹ تیم «نگه‌دار» گفت؛ تایم‌فریم‌ها هم‌جهت {'خرید' if c == 1 else 'فروش'} هستند، پس میز مناظره و مدیر سبد تصمیم می‌گیرند.")

def smc_plan(now, side, price):
    """گیت‌های قطعی + نتیجهٔ ایجنت → {ok, why, lines, entry, sl, opp}. در هر requote سریع اجرا می‌شود (بدون تماس مدل)."""
    d5, d1 = DATA; a = float(now.atr); D = lambda x: x + PRICE_OFFSET; ai = AG.get("smc")
    P = {"ok": True, "why": "", "lines": [], "entry": None, "sl": None, "opp": None, "size": 1.0, "size_why": [], "flags": [], "hard": [], "rev": False}; veto = []
    def cut(f, why):
        if TIERS_ON and KEEP_SIZE: P["flags"].append(why); P["size_adv"] = min(P.get("size_adv", 1.0), f); return        # v19: حجم کم نمی‌شود؛ فقط پرچم + «پیشنهاد اطلاعی» برای اعلان
        P["size"] = min(P["size"], f); P["size_why"].append(why); P["flags"].append(why)
    def _soft(m): P["lines"].append(m.replace("⛔", "⚠ (فقط حجم کم می‌شود)", 1)); cut(0.5, "ایمپالس فعال خلاف جهت")
    dk = AG.get("desk") if (DESK_ON and USE_AGENTS and AG["ok"]) else None
    ae = {**(ai or {}), **({k: dk[k] for k in ("entry_price", "sl_price") if dk.get(k) is not None} if dk else {})}     # ورود/SL انتخابی مدیر سبد (اگر بود) بر ایجنت ICT/SMC مقدم است
    if AG.get("override"): cut(0.5, "تیم عامل‌ها «نگه‌دار» گفته بود؛ جهت از میز تکنیکال (هم‌جهتی تایم‌فریم‌ها) آمده")
    try: S = smc_engine(d5, d1, a, price, side)
    except Exception as e:
        S = None; P["lines"].append(f"⚠ موتور ساختار خطا داد ({type(e).__name__}: {str(e)[:100]})؛ گیت‌های ساختاری اعمال نشد.")
    if S is not None:
        exempt = any(s["bias"] == side and s["mss"] and side * (price - s["extreme"]) > 0 for s in S["sweeps"])   # سوییپ+MSS هم‌جهت، به شرط اینکه قیمت هنوز از نقطهٔ سوییپ عبور نکرده باشد (باطل نشده)
        P["rev"] = bool(exempt)
        against, stk, ext_a = -side * S["mv"], -side * S["streak"], -side * S["ext"]
        if not exempt and (against >= IMPULSE_ATR or (stk >= 4 and ext_a >= 0.5)):
            (veto.append if (against >= IMPULSE_VETO_ATR or not M()["soft_impulse"]) else _soft)(f"⛔ ایمپالس فعال خلاف جهت: قیمت در حدود {IMPULSE_BARS} کندل ۵م اخیر {abs(S['mv']):.1f} ATR {'بالا' if S['mv'] > 0 else 'پایین'} رفته (رشتهٔ کندل هم‌جهت: {abs(S['streak'])}) "
                        f"و هنوز سوییپ + MSS هم‌جهت با سیگنال دیده نشده. لیمیت جلوی حرکتِ در حال اجرا معمولاً فیل می‌شود و از استاپ رد می‌شود. صبر کنید حرکت خسته شود (سوییپ نقدینگی و برگشت)، بعد سلول ۲ را دوباره اجرا کنید.")
    if S is not None:      # v11.2: بررسی اجباری RSI (فقط پرچم؛ سیگنال حذف نمی‌شود)
        try:
            _rl, _rf = rsi_check(S, side); P["rsi_line"] = _rl; P["lines"].append(_rl)
            for m_ in _rf: cut(0.5, m_)
        except Exception as ex_: P["lines"].append(f"⚠ بررسی RSI خطا داد: {type(ex_).__name__}")
    if S is not None and CHASE_GATE:      # v13: دنبال‌کردنِ حرکت و ورود دوباره روی تارگتِ قبلی
        try:
            for m_ in chase_check(S, side, a, price): cut(0.5, m_); P["lines"].append("⚠ " + m_)
        except Exception: pass
    e20 = float(now.ema20) + (2 / 21) * (price - float(now.ema20)); e = float(entry_price(price, e20, a, side))
    if ae.get("entry_price") is not None and 0.1 * a <= side * (price - ae["entry_price"]) <= 1.0 * a:
        P["entry"] = e = float(ae["entry_price"]); P["lines"].append(f"🎯 ورود روی ناحیهٔ FVG/OB انتخاب‌شده توسط ایجنت: {D(e):.{PXD}f} (به‌جای ورود پولبک ساده)")
    sl0 = e - side * SL_ATR * a; sl_s = None
    if ae.get("sl_price") is not None and side * (e - ae["sl_price"]) > 0.3 * a:
        if side * (e - ae["sl_price"]) > M()["risk_hard"] * a: P["lines"].append(f"ℹ SL پیشنهادی ایجنت‌ها ({side * (e - ae['sl_price']) / a:.1f} ATR) خیلی دور بود؛ نادیده گرفته شد و نزدیک‌ترین استخر نقدینگی کنار SL ساده استفاده می‌شود.")
        else: sl_s = float(ae["sl_price"])
    if S is not None and STOP_HUNT_AWARE:      # v11.2: SL هوشمند، پشت نقاطی که عموم استاپ می‌گذارند
        pools = crowd_pools(S, e, a, side); d0 = max(SL_ATR, side * (e - sl_s) / a) if sl_s is not None else SL_ATR
        d1, nts, sk = smart_stop(a, pools, d0, M()["risk_hard"])
        if d1 > d0 + 1e-9: sl_s = e - side * d1 * a
        P["crowd"] = pools; P["lines"] += nts
        for lab_, pd_ in sk: cut(0.5, f"استخر استاپ‌ها «{lab_}» ({pd_:.2f} ATR از ورود) پشت SL مانده و رفتن پشتش از سقف ریسک می‌گذرد؛ احتمال شکار استاپ")
        if not nts and not sk: P["lines"].append(f"🛡 SL در ناحیه‌ای است که استخر استاپ عموم داخل یا چسبیده به آن نیست ({d0:.2f} ATR از ورود).")
        P["crowd_txt"] = ("📍 استاپ‌های عموم پشت ورود: " + " · ".join(f"{lab} {D(e - side * d * a):.{PXD}f} ({d:.1f} ATR)" for d, lab, w in pools[:4]) + f" ← SL: {D(e - side * max(d1, SL_ATR) * a):.{PXD}f}") if pools else "📍 استخر استاپ عموم نزدیکی پشت ورود پیدا نشد."
    elif S is not None:
        for pl in (S["below"] if side == 1 else S["above"]):
            if abs(pl["p"] - sl0) <= SL_BUFFER_ATR * a and side * (e - pl["p"]) > 0:      # استاپ چسبیده به یک استخر نقدینگی = شکار استاپ
                cand = pl["p"] - side * SL_BUFFER_ATR * a
                sl_s = cand if sl_s is None else (min(sl_s, cand) if side == 1 else max(sl_s, cand))
    if SPREAD_ON and SPREAD_MIN_MULT and _spr() > 0:      # v12: اسپرد نباید بیش از ≈۱۲٪ ریسک باشد
        _need = SPREAD_MIN_MULT * _spr(); _cur = max(SL_ATR * a, side * (e - sl_s)) if sl_s is not None else SL_ATR * a
        if _cur < _need: sl_s = e - side * _need; P["lines"].append(f"📏 SL به {_need / a:.2f} ATR بازتر شد: اسپرد {_spr():g} روی ریسک {_cur:.{PXD}f} بیش از ۱۲٪ ریسک را می‌خورد.")
    if sl_s is not None:
        P["sl"] = sl_s; rk = max(SL_ATR * a, side * (e - sl_s))
        if rk > SL_ATR * a + 1e-9: P["lines"].append(f"🛡 SL پشت نقدینگی/سطح ساختاری گذاشته شد (نه ۱ ATR ساده): ریسک {rk:.{PXD}f} = {rk / a:.2f} ATR")
        if rk > M()["risk_hard"] * a: veto.append(f"⛔ استاپِ امن (پشت نقدینگی) {rk / a:.2f} ATR فاصله دارد و از سقف {M()['risk_hard']:g} ATR بیشتر است؛ ستاپ تمیز و کم‌ریسک وجود ندارد.")
        elif rk > M()["risk_soft"] * a: cut(0.5, f"استاپ ساختاری دور است ({rk / a:.2f} ATR)")
    if S is not None:
        for x in (S["above"] if side == 1 else S["below"]):
            if x["d"] >= 0.5 and (x["tf"] != "5m" or x["eq"] >= 1) and side * (x["p"] - e) > 0: P["opp"] = x["p"]; break
    _rr_reset()
    if S is not None:       # استخرهای نقدینگیِ سر راه تارگت‌ها، بر حسب R (همهٔ تایم‌فریم‌ها یکجا ادغام شده‌اند)
        rk_ = max(SL_ATR * a, side * (e - sl_s)) if sl_s is not None else SL_ATR * a
        ps = [(x, abs(x["p"] - e) / rk_) for x in (S["above"] if side == 1 else S["below"]) if side * (x["p"] - e) > 0][:3]
        _rr = _rr_room(S, e, rk_, side); P["rr_room"] = _rr[0] if _rr else None
        if _rr and RR_LADDER_ON and 1.35 <= _rr[0] < MIN_RR * 0.85:
            _st = (1.0, 2.0) if _rr[0] >= 1.8 else (0.75, 1.5)      # پلهٔ ۱:۲ سپس ۱:۱٫۵
            _rr_apply(*_st); P["rr_used"] = _st[1]
            P["lines"].append(f"🪜 فضای ۱:{MIN_RR:g} نیست ({_rr[1]} فقط {_rr[0]:.1f}R جلوتر است)؛ تارگت‌ها به ۱:{_st[1]:g} کاهش یافت (TP1={_st[0]:g}R، TP2={_st[1]:g}R).")
            cut(0.5, f"ریوارد کاهش‌یافته ۱:{_st[1]:g} (فضا برای ۱:{MIN_RR:g} نبود)")
        elif _rr and _rr[0] < (1.35 if RR_LADDER_ON else 1.5): veto.append(f"⛔ نقدینگی مهم مقابل ({_rr[1]}: {_rr[2]}) فقط {_rr[0]:.1f}R جلوتر است؛ ریوارد ۱ به {MIN_RR:g} واقعی نیست.")
        elif _rr and _rr[0] < MIN_RR * 0.85: cut(0.5, f"مسیر ۱:{MIN_RR:g} تا {_rr[1]} فقط {_rr[0]:.1f}R فضا دارد")
        if ps: P["lines"].append("نقدینگی سر راه هدف: " + " | ".join(f"{x['id']} {D(x['p']):.{PXD}f} = {r_:.1f}R ({x['names']})" for x, r_ in ps) + f"  ← 🎯 اصلی: {SAFE_R1:g}R و {SAFE_R2:g}R | 🚀 ریوارد بالا: {RUN_R1:g}R و {RUN_R2:g}R")
    if SMC_AGENT and USE_AGENTS and AG["ok"] and AG.get("smc_tried"):
        if ai is None:
            if ICT_AS_MEMBER: P["lines"].append("ℹ عامل ICT (عضو شورا) اجرا نشد؛ شورا بدون نظر عمیق او رأی می‌دهد.")
            elif SMC_REQUIRED and dk is None:
                if M()["no_agent_ok"]: cut(0.5, "ایجنت ICT/SMC اجرا نشد")
                else: veto.append(f"⛔ ایجنت ICT/SMC اجرا نشد و SMC_REQUIRED=True است؛ سیگنال داده نمی‌شود. علت: {AG.get('smc_err') or 'نامشخص'}")
        else:
            v = ai["verdict"]
            try: cf = float(ai["confidence"])
            except Exception: cf = 0.0
            if v == "GO" and SMC_MIN_CONF and cf < SMC_MIN_CONF: v = "WAIT"; ai = {**ai, "trigger": ai["trigger"] or f"اطمینان ایجنت ({cf:g}) از حداقل {SMC_MIN_CONF} کمتر است"}
            P["lines"].append(f"{ {'GO': '✅', 'WAIT': '⏳', 'NO': '⛔'}[v] } ایجنت ICT/SMC: {v} (اطمینان {ai['confidence']}/10، هم‌گرایی {ai.get('confluence', '?')} تأیید مستقل) — {ai['summary']}")
            P["lines"] += [f"   • {k}: {t}" for k, t in ai["schools"].items()]
            if ai["risks"]: P["lines"].append(f"   ریسک اصلی: {ai['risks']}")
            if v != "GO" and (dk is None or MODE == "careful"):
                msg = f"{'⛔ ایجنت ICT/SMC ستاپ را رد کرد (NO)' if v == 'NO' else '⏳ ایجنت ICT/SMC می‌گوید هنوز زود است (WAIT)'}: {ai['summary']}" + (f"\nمنتظر: {ai['trigger']}" if ai["trigger"] else "")
                if v == "WAIT" and cf >= M()["wait_conf"]: P["lines"].append(msg.replace("⏳", "⏳ (با اطمینان کافی؛ ورود با نصف حجم)", 1)); cut(0.5, f"ایجنت ICT/SMC «WAIT» با اطمینان {cf:g}")
                else: (cut(0.5, msg.splitlines()[0][:150]) if ICT_AS_MEMBER else veto.append(msg))      # v12: ICT فقط یک عضو است، وتو ندارد
    if DESK_ON and USE_AGENTS and AG["ok"] and AG.get("desk_tried"):
        if dk is None:
            if M()["no_agent_ok"]: cut(0.5, "مدیر سبد اجرا نشد")
            else: veto.append(f"⛔ مدیر سبد اجرا نشد و سیگنال بدون ناظر داده نمی‌شود. علت: {AG.get('desk_err') or 'نامشخص'}")
        else:
            P["lines"].append(f"🧭 مدیر سبد: {'✅ TAKE' if dk['decision'] == 'TAKE' else '⛔ SKIP'} | درجه {dk['grade']} | اطمینان {dk['confidence']}/10 | احتمال رسیدن به TP1 حدود {dk['p_tp1']}٪ — {dk['summary']}")
            if dk["mtf"]: P["lines"].append("   تایم‌فریم‌ها: " + " | ".join(f"{k}: {v}" for k, v in dk["mtf"].items()))
            for lab, key in (("بررسی SL", "sl_check"), ("بررسی TP", "tp_check"), ("برندهٔ مناظره", "debate_winner"), ("ریسک اصلی", "risks")):
                if dk.get(key): P["lines"].append(f"   {lab}: {dk[key]}")
            if dk["decision"] == "SKIP": veto.append(f"⛔ مدیر سبد رد کرد: {dk['summary']}" + (f"\nمنتظر: {dk['trigger']}" if dk["trigger"] else ""))
            elif dk["size"] < 1.0: cut(dk["size"], f"درجه {dk['grade']} از نگاه مدیر سبد")
    if S is not None:
        P["lines"].append(f"ساختار 5m/15m/1h: {S['trend']['5m'][1]} / {S['trend']['15m'][1]} / {S['trend']['1h'][1]} | موقعیت در رنج ۱۲ساعته: {S['range15m'][2]:.0%} ({'پریمیوم' if S['range15m'][2] > 0.5 else 'دیسکانت'}) | حرکت {IMPULSE_BARS} کندل اخیر: {S['mv']:+.1f} ATR | سشن: {S['session']}")
        up, dn = (S["above"][:1] or [None])[0], (S["below"][:1] or [None])[0]
        P["lines"].append("نقدینگی نزدیک: " + (f"بالا {D(up['p']):.{PXD}f} ({up['d']:.1f} ATR، {up['names']})" if up else "بالا -") + " | " + (f"پایین {D(dn['p']):.{PXD}f} ({dn['d']:.1f} ATR، {dn['names']})" if dn else "پایین -"))
        if S["sweeps"]:
            s = S["sweeps"][0]; P["lines"].append(f"آخرین سوییپ: {'سقف' if s['bias'] == -1 else 'کف'} {D(s['level']):.{PXD}f} ({s['name']}) حدود {s['ago'] * 5} دقیقه پیش، MSS بعدش: {'تأیید شد' if s['mss'] else 'ندارد'}")
    _h0 = ASSET_HOURS.get(ASSET)      # v12: ساعات کم‌نقدینگی
    if _h0:
        _hh = utcnow().hour + utcnow().minute / 60
        if not (_h0[0] <= _hh < _h0[1]): cut(0.5, f"خارج از ساعات پرنقدینگی {ASSET} ({_h0[0]:g} تا {_h0[1]:g} UTC): اسپایک، شکار استاپ و اسپرد بازتر")
    if PREPOOL_GATE and S is not None and not P.get("rev"):      # v12: اول سوییپ، بعد ورود
        try:
            _pp = [x for x in (S["below"] if side == 1 else S["above"]) if x["d"] <= PREPOOL_ATR and (x["tf"] != "5m" or x["eq"] >= 1)]
            if _pp and -side * S["mv"] >= 0.3: veto.append(f"⛔ استخر نقدینگیِ سمتِ استاپ ({_pp[0]['names']} در {D(_pp[0]['p']):.{PXD}f}، {_pp[0]['d']:.1f} ATR) هنوز سوییپ نشده و قیمت دارد به آن می‌رسد؛ معمولاً اول آن را می‌زنند و بعد برمی‌گردند. صبر کنید سوییپ + MSS دیده شود و بعد وارد شوید.")
        except Exception: pass
    try:      # v12: تقویم خبری
        _g = news_guard(); P["news"] = _g
        for _x in _g["near"]:
            _m = f"خبر {'مهم' if _x['impact'] == 'High' else 'متوسط'} فارکس‌فکتوری: {_x['title']} ({_x['ccy']}) {_when(_x['mins'])}؛ تا {NEWS_AFTER_MIN} دقیقه بعد از انتشار سفارش نگذارید"
            P["lines"].append(("🚨 " if _x["impact"] == "High" else "⚠ ") + _m)
            if _x["impact"] == "High": veto.append("⛔ " + _m)
            else: cut(0.5, _m)
        if not _g["ok"]: P["lines"].append(f"⚠ تقویم فارکس‌فکتوری گرفته نشد ({_g['err']}); دستی چک کنید.")
    except Exception as _ex: P["lines"].append(f"⚠ بررسی خبر خطا داد: {type(_ex).__name__}")
    _ec = AG.get("econ")      # v12: اقتصاددان ارشد
    if _ec:
        P["lines"].append(f"🎓 اقتصاددان (PhD): {'صعودی' if _ec['bias'] == 1 else 'نزولی' if _ec['bias'] == -1 else 'خنثی'} · اطمینان {_ec['conv']}/10 · ریسک رویداد {_ec['event_risk']} — {_ec['regime']}")
        if _ec["bias"] == -side and _ec["conv"] >= 7: cut(0.5, f"اقتصاددان با اطمینان {_ec['conv']}/10 مخالف این جهت است: {_ec['intraday'][:90]}")
        if _ec["event_risk"] == "high": cut(0.5, "اقتصاددان: ریسک رویداد/خبر بالاست")
    if STRAT_ON:      # v15: استراتژیِ کتابچه
        try:
            _sel = AG.get("strat_sel"); _pk = (_sel or {}).get("pick")
            if _pk:
                _sc = _pk.get("sc"); P["strat"] = {k_: _pk[k_] for k_ in ("k", "n", "score", "team", "gold_ok", "stale")}
                P["lines"].append(f"🛠 استراتژی کتابچه: {_pk['e']} {_pk['n']} ({'BUY' if side == 1 else 'SELL'}) · " + (f"بک‌تست سشن {SESS_FA.get(_sel['session'], _sel['session'])}: n={_sc['n_ses']} وین‌ریت {_sc['wr_ses']:.0%} میانگین {_sc['E_ses']:+.2f}R · ۲ ماه: n={_sc['n_all']} وین {_sc['wr_all']:.0%} {_sc['E_all']:+.2f}R" if _sc else "بک‌تست در دسترس نیست یا کم‌نمونه") + f" · رأی تیم {_pk['team']:.0%}")
                if _pk.get("stale"): veto.append(f"⛔ ستاپ استراتژی «{_pk['n']}» دیگر معتبر نیست ({_pk['detail']}). تحلیل کامل را دوباره اجرا کنید.")
                elif _sc is None: cut(0.5, "بک‌تست این استراتژی کم‌نمونه یا ناموجود است")
                elif _sc["score"] < STRAT_NEG_SCORE: cut(0.5, f"بک‌تست این استراتژی در سشن {SESS_FA.get(_sel['session'], _sel['session'])} ضعیف است (امتیاز {_sc['score']:+.2f})")
                if _sc is not None and _sc.get("oos_ok") is False: cut(0.5, f"آزمون خارج‌ازنمونه ({OOS_FRAC:.0%} آخرِ دادهٔ بک‌تست) منفی بود: n={_sc['n_oos']} میانگین {_sc['E_oos']:+.2f}R؛ مزیت این استراتژی هنوز تأیید نشده")
                if AG.get("team_side") not in (None, 0, side): cut(0.5, "تحلیلگران تیم عامل‌ها خلاف جهت این استراتژی رأی داده بودند")
            elif _sel is not None:
                P["lines"].append("🛠 هیچ استراتژی فعالی نبود (STRAT_REQUIRED=False)؛ جهت از تیم/تایم‌فریم‌هاست."); cut(0.5, "هیچ استراتژی کتابچه‌ای فعال نیست")
        except Exception as _e2: P["lines"].append(f"⚠ بررسی استراتژی خطا داد: {type(_e2).__name__}")
    if COUNCIL_ON:      # v11: شورای ۱۴ نفره
        try:
            Cp = council_state(now, price, side); P["council"] = Cp
            P["lines"].append(f"🏛 شورای سبک‌ها: {Cp['nf']} هم‌جهت | {Cp['na']} مخالف | {Cp['nn']} بی‌نظر · توافق وزنی {Cp['agree']:.0%} · رژیم {Cp['regime']} (ER={Cp['er']:.2f})")
            if Cp["nf"] < 3: cut(0.5, f"فقط {Cp['nf']} سبک با این جهت هم‌نظرند")
            if Cp["na"] >= Cp["nf"] + 2 and Cp["agree"] < 0.4: veto.append(f"⛔ شورای سبک‌ها مخالف است: {Cp['na']} سبک مخالف در برابر {Cp['nf']} موافق (توافق وزنی {Cp['agree']:.0%}).")
        except Exception as ex: P["lines"].append(f"⚠ شورای سبک‌ها خطا داد ({type(ex).__name__}: {str(ex)[:100]})؛ نادیده گرفته شد.")
    if CEO_ON and USE_AGENTS and AG["ok"] and AG.get("ceo_tried"):      # v11: مدیرعامل
        ck = AG.get("ceo")
        if ck is None: cut(0.5, "مدیرعامل اجرا نشد"); P["lines"].append(f"⚠ مدیرعامل اجرا نشد: {AG.get('ceo_err') or 'نامشخص'}")
        else:
            P["lines"].append(f"👔 مدیرعامل: {ck['verdict']} | درجه {ck['grade']} | احتمال TP1 ≈ {ck['p_tp1']}٪ — {ck['why']}")
            if ck["verdict"] == "NO": veto.append(f"⛔ مدیرعامل رد کرد: {ck['why']}" + (f"\nمنتظر: {ck['trigger']}" if ck["trigger"] else ""))
            elif ck["verdict"] == "WAIT": cut(0.5, "مدیرعامل: ستاپ خوب ولی هنوز زود است" + (f" ({ck['trigger'][:80]})" if ck["trigger"] else ""))
            if not ck["rr_ok"]: cut(0.5, f"مدیرعامل: رسیدن به ۱ به {MIN_RR:g} مطمئن نیست")
    try:      # v11: انضباط روزانه
        tr_, tn_, stk_ = _today_stats()
        if tr_ <= -DAILY_STOP_R: veto.append(f"⛔ انضباط: امروز {tr_:+.1f}R ثبت شده و سقف ضرر روزانه {DAILY_STOP_R:g}R است؛ امروز دیگر ترید نکنید.")
        elif stk_ >= MAX_LOSS_STREAK: cut(0.5, f"{stk_} باخت پشت‌سرهم؛ ۳۰ دقیقه استراحت و بازبینی")
    except Exception: pass
    if veto:
        if TIERS_ON:      # v9: ردکردن نداریم؛ هر «⛔» یک پرچم سخت می‌شود و سیگنال می‌رود به رستهٔ HIGH-RISK
            P["hard"] = [v_.replace("⛔", "", 1).strip() for v_ in veto]; P["flags"] += [h_.splitlines()[0][:150] for h_ in P["hard"]]
            P["lines"] += ["🔥 (v9: سیگنال کشته نشد؛ ریسک‌بالا حساب شد) " + h_ for h_ in P["hard"]]
        elif SMC_STRICT: P["ok"] = False; P["why"] = "\n".join(veto)
        else: P["lines"] += ["⚠ (حالت سایه، SMC_STRICT=False؛ فقط هشدار) " + x for x in veto]
    return P


# ================= v11: شورای سبک‌ها (۱۳ ایجنت متخصص) + مدیرعامل (CEO) =================
# هر سبک یک ایجنت متخصص دارد: بخش قطعی (کد) شرط ورود همان سبک را روی داده می‌سنجد، بخش مدل (یک تماس واحد) همان را با «کتاب قوانین» آن سبک تأیید یا رد می‌کند.
# اگر کد و مدل هم‌نظر نباشند رأیِ آن سبک صفر می‌شود (جلوی توهم مدل را می‌گیرد). مدیرعامل همه را می‌شنود و حکم نهایی + برنامهٔ اجرایی + درس تیم را می‌دهد.
STYLES = [  # (کلید، نام، ایموجی)؛ ترتیب = ترتیب عکس شما (بالاتر = وین‌ریت جهانیِ گزارش‌شدهٔ بیشتر = وزن اولیهٔ بیشتر)
    ("meanrev", "بازگشت به میانگین", "🧲"), ("scalp", "اسکالپینگ", "⚡"), ("range", "رنج‌تریدینگ", "📦"), ("grid", "گرید", "🕸"),
    ("swing", "سوینگ", "🌊"), ("pa", "پرایس‌اکشن", "🕯"), ("sd", "عرضه و تقاضا", "⚖"), ("mom", "مومنتوم", "🚀"),
    ("brk", "بریک‌اوت", "💥"), ("smc", "اسمارت‌مانی", "🧠"), ("ict", "ICT", "🎯"), ("trend", "روندپیرو", "📈"), ("pos", "پوزیشن‌تریدینگ", "🏔")]
W0 = {k: round(1.30 - 0.5 * i / (len(STYLES) - 1), 3) for i, (k, _, _) in enumerate(STYLES)}
_SNAME = {k: (n, e) for k, n, e in STYLES}
PLAYBOOKS = {
    "meanrev": "Mean Reversion: only in a RANGING regime (low efficiency ratio). Trigger = price stretched >=2 sigma from the 15m mean AND RSI extreme AND a rejection candle. Target the mean/VWAP, then extend only if structure allows. Invalid in a strong trend.",
    "scalp": "Scalping: 5m EMA9>EMA21>EMA50 stack, shallow pullback to EMA21 on declining volume, price on the right side of VWAP, trade in the active session only. Stop beyond the pullback low.",
    "range": "Range Trading: defined range (ER low). Buy discount (<20% of range) after a rejection, sell premium (>80%); never trade the middle; a close outside the range cancels it.",
    "grid": "Grid Trading: NON-directional; only valid in a clean range. It never votes a direction; it warns when the regime is trending (grid = danger) and gives the range edges.",
    "swing": "Swing Trading: 1h and 4h structure aligned, price pulls back to the 1h EMA20/50 or a 1h demand/supply zone; hold for hours; stop behind the 1h swing.",
    "pa": "Price Action: pin bar / engulfing / inside-bar break exactly at a swing, zone or round level, in the direction of the 15m-1h bias. The candle must close; context beats pattern.",
    "sd": "Supply & Demand: fresh unmitigated zone formed by displacement, first touch only. Entry at the zone edge, stop beyond the zone, target the opposing zone. Stale/mitigated zones are ignored.",
    "mom": "Momentum: RSI(15m) >58/<42 with price beyond EMA20 and expanding ATR; buy strength / sell weakness but NOT when stretched >2.2 ATR from EMA20 (wait for the pullback).",
    "brk": "Breakout: 15m close beyond the prior 20-bar high/low with range expansion; best entry = retest of the broken level. A wick-only break or a break straight into HTF liquidity is a trap.",
    "smc": "Smart Money Concepts: liquidity sweep -> displacement -> MSS/CHoCH -> entry in the FVG/OB in discount (long) or premium (short). Needs the full sequence; a sweep alone is NONE.",
    "ict": "ICT: killzone timing (London/NY AM/PM, Silver Bullet), sweep of PDH/PDL/Asia/London/PWH/PWL, displacement + FVG, entry at OTE (62-79%) in the discount/premium relative to NY midnight open, SMT divergence as a bonus. 4+ of these criteria needed.",
    "trend": "Trend Following: 15m/30m/1h/1d EMA20>EMA50 alignment (>=3 of 4), price on the right side of the 15m EMA50 and 4h structure not opposing. Enter pullbacks, never extended moves; trail behind swings.",
    "pos": "Position Trading: daily EMA20/50/200 macro phase. Not an entry timer: it tells whether the scalp is WITH or AGAINST the big picture. Against the daily phase -> reduce conviction."}

def _style_calib():
    """وزن هر سبک با نتیجهٔ واقعی ژورنال شما اصلاح می‌شود (از ۸ ترید به بالا برای هر سبک): نرخ برد بالاتر از ۴۵٪ → وزن بیشتر."""
    st = {}
    for x in _jread():
        if x.get("R") is None or not x.get("styles"): continue
        for s_ in x["styles"]: st.setdefault(s_, []).append(x["R"])
    return {k: (1.0 + float(np.clip(np.mean([r > 0 for r in v]) - 0.45, -0.35, 0.35)) if len(v) >= 8 else 1.0) for k, v in st.items()}

def _lessons(n=6):
    """آخرین نکته‌هایی که خودتان در ژورنال نوشته‌اید؛ به ایجنت‌ها داده می‌شود تا از اشتباه قبلی درس بگیرند (آموزش مداوم)."""
    rows = [x for x in _jread() if x.get("note") and x.get("source") != "seed"][-n:]
    return "\n".join(f"- {x.get('asset')} {x.get('outcome')} ({x.get('R')}R, tier {x.get('tier')}): {str(x['note'])[:160]}" for x in rows) or "(none yet)"

def _today_stats():
    """انضباط روزانه از ژورنال: جمع R امروز (UTC) و تعداد باخت‌های پشت‌سرهم."""
    rows = [x for x in _jread() if x.get("R") is not None and not str(x.get("source", "")).startswith("seed")]
    day = utcnow().date().isoformat(); td = [x for x in rows if str(x.get("logged", "")).startswith(day)]
    streak = 0
    for x in reversed(rows):
        if x["R"] < 0: streak += 1
        else: break
    return float(sum(x["R"] for x in td)), len(td), streak

RR_LADDER_ON = True       # ۱:۳ اولویت است؛ فقط اگر نقدینگیِ سر راه جا نداد ۱:۲ و بعد ۱:۱٫۵ (به‌جای رد کردن سیگنال)
_RR0 = {}
def _rr_reset():
    """تارگت‌ها را به پیش‌فرض (۱:۳) برمی‌گرداند؛ در ابتدای هر ساخت پلان و قبل از بک‌تست صدا زده می‌شود."""
    if not _RR0: _RR0.update(r1=SAFE_R1, r2=SAFE_R2, run=RUNNER_ON)
    globals().update(SAFE_R1=_RR0["r1"], SAFE_R2=_RR0["r2"], RUNNER_ON=_RR0["run"])
def _rr_apply(r1, r2):
    _rr_reset(); globals().update(SAFE_R1=r1, SAFE_R2=r2, RUNNER_ON=False)      # کارت رانر ۱:۵ وقتی فضا کم است معنا ندارد

def _rr_room(S, e, risk, side):
    """نزدیک‌ترین نقدینگی مهم مقابل برحسب R: (فاصله به R، شناسه، نام) یا None."""
    best = None
    for x in (S["above"] if side == 1 else S["below"]):
        if side * (x["p"] - e) > 0 and (x["tf"] != "5m" or x["eq"] >= 1):
            r_ = abs(x["p"] - e) / max(risk, 1e-9)
            if best is None or r_ < best[0]: best = (r_, x["id"], x["names"])
    return best

def _style_votes(now, price):
    """رأی قطعی (کد) هر ۱۳ سبک: {کلید: (جهت ۱/۰/‑۱، اطمینان ۰ تا ۱، دلیل)} + متادیتا. هر سبک جدا و در try تا خطای یکی بقیه را خراب نکند."""
    d5, d1 = DATA; a = float(now.atr)
    Su, Sd = smc_engine(d5, d1, a, price, 1), smc_engine(d5, d1, a, price, -1)
    r15, r1h = _rs(d5, "15min"), _rs(d5, "60min"); c15 = r15.Close; c5 = d5.Close
    e20_15, e50_15 = float(ema(c15, 20).iloc[-1]), float(ema(c15, 50).iloc[-1]); e9, e21, e50 = (float(ema(c5, n).iloc[-1]) for n in (9, 21, 50))
    rsi5, rsi15 = Su["rsi"], _rsi(c15.values); er = Su["er"] if Su.get("er") is not None else 0.35; pos = Su["range15m"][2]
    vw = (Su.get("auction") or {}).get("vwap"); sd20 = float(c15.tail(20).std()) or a; z = (price - float(c15.tail(20).mean())) / sd20
    V = {}
    def put(k, v, cf, why): V[k] = (int(v), float(max(0.0, min(1.0, cf))), why)
    def run(k, fn):
        try: fn()
        except Exception as ex: put(k, 0, 0, f"خطا در محاسبه ({type(ex).__name__})")
    def f_meanrev():
        if er > 0.5: put("meanrev", 0, 0, f"رژیم روندی (ER={er:.2f}) · بازگشت به میانگین پرخطر")
        elif z <= -2 and rsi5 < 32: put("meanrev", 1, 0.5 + min(0.5, (abs(z) - 2) * 0.5), f"کشیدگی منفی z={z:.1f} و RSI {rsi5:.0f}")
        elif z >= 2 and rsi5 > 68: put("meanrev", -1, 0.5 + min(0.5, (abs(z) - 2) * 0.5), f"کشیدگی مثبت z={z:.1f} و RSI {rsi5:.0f}")
        else: put("meanrev", 0, 0, "قیمت نزدیک میانگین؛ لبهٔ برگشتی ندارد")
    def f_scalp():
        pull = abs(price - e21) / a; up, dn = e9 > e21 > e50, e9 < e21 < e50
        if up and pull <= 0.5 and price >= e50 and (vw is None or price >= vw[0] - 0.3 * a): put("scalp", 1, 0.5 + 0.4 * (1 - pull / 0.5), f"پولبک کم‌عمق به EMA21 ({pull:.2f} ATR) در چیدمان صعودی")
        elif dn and pull <= 0.5 and price <= e50 and (vw is None or price <= vw[0] + 0.3 * a): put("scalp", -1, 0.5 + 0.4 * (1 - pull / 0.5), f"پولبک کم‌عمق به EMA21 ({pull:.2f} ATR) در چیدمان نزولی")
        else: put("scalp", 0, 0, "چیدمان EMA۵م یا پولبک مناسب نیست")
    def f_range():
        if er < 0.35 and pos <= 0.2: put("range", 1, 0.5 + (0.2 - pos) / 0.2 * 0.4, f"کف رنج (دیسکانت {pos:.0%}) در رژیم رنج")
        elif er < 0.35 and pos >= 0.8: put("range", -1, 0.5 + (pos - 0.8) / 0.2 * 0.4, f"سقف رنج (پریمیوم {pos:.0%}) در رژیم رنج")
        else: put("range", 0, 0, "رژیم روندی؛ رنج معتبر نیست" if er >= 0.35 else "وسط رنج؛ ورود ندارد")
    def f_grid():
        lo_, hi_, _ = Su["range1h"]
        put("grid", 0, 0, (f"رنج تمیز برای شبکه: {lo_:,.{PXD}f} تا {hi_:,.{PXD}f}؛ بدون جهت و ریوارد ۱:۳ ندارد" if er < 0.3 else f"رژیم روندی (ER={er:.2f})؛ گرید خطرناک است، دوری کنید"))
    def f_swing():
        t1, t4 = Su["trend"]["1h"][0], Su["trend"]["4h"][0]; e20h = float(ema(r1h.Close, 20).iloc[-1]); pl = (price - e20h) / a
        if t1 != 0 and t1 == t4 and -1.5 <= pl * t1 <= 0.8: put("swing", t1, 0.6 + (0.15 if int(now.d1d) == t1 else 0), f"ساختار ۱س و ۴س هم‌جهت و قیمت نزدیک EMA20 ساعتی ({pl:+.1f} ATR)")
        else: put("swing", 0, 0, "ساختار ۱س/۴س هم‌جهت نیست یا پولبک نشده")
    def f_pa():
        b, p_ = r15.iloc[-1], r15.iloc[-2]; body = abs(b.Close - b.Open); rng = max(b.High - b.Low, 1e-9); lw, uw = min(b.Open, b.Close) - b.Low, b.High - max(b.Open, b.Close)
        bp, sp = lw >= 2 * max(body, 0.05 * rng) and lw >= 0.55 * rng, uw >= 2 * max(body, 0.05 * rng) and uw >= 0.55 * rng
        be = b.Close > b.Open and p_.Close < p_.Open and b.Close >= p_.Open and b.Open <= p_.Close and body >= 0.4 * a
        se = b.Close < b.Open and p_.Close > p_.Open and b.Close <= p_.Open and b.Open >= p_.Close and body >= 0.4 * a
        if (bp or be) and pos < 0.45: put("pa", 1, 0.6 + (0.2 if (bp and be) else 0), "پین‌بار/انگالفینگ صعودی در نیمهٔ پایین رنج")
        elif (sp or se) and pos > 0.55: put("pa", -1, 0.6 + (0.2 if (sp and se) else 0), "پین‌بار/انگالفینگ نزولی در نیمهٔ بالای رنج")
        else: put("pa", 0, 0, "الگوی کندلی معتبر در ناحیهٔ درست دیده نشد")
    def f_sd():
        zl = [x for x in Su["zones"] if x["dir"] == 1 and x["d"] <= 0.7]; zs = [x for x in Sd["zones"] if x["dir"] == -1 and x["d"] <= 0.7]
        c_ = sorted([(x["d"], 1, x) for x in zl] + [(x["d"], -1, x) for x in zs], key=lambda t: t[0])
        if c_:
            d_, s_, x = c_[0]; cf = 0.45 + 0.4 * (1 - d_ / 0.7) + (0.1 if x["type"] == "OB" else 0) - (0.15 if int(now.d1h) == -s_ else 0)
            put("sd", s_, cf, f"ناحیهٔ {'تقاضا' if s_ == 1 else 'عرضه'} {x['type']} ({x['tf']}) در {d_:.2f} ATR")
        else: put("sd", 0, 0, "ناحیهٔ تازه و دست‌نخورده نزدیک قیمت نیست")
    def f_mom():
        ex = Su["ext"]
        if rsi15 >= 58 and price > e20_15 and Su["px1h"] > 0 and ex < 2.2: put("mom", 1, 0.45 + min(0.4, (rsi15 - 55) / 25), f"RSI ۱۵م {rsi15:.0f} و قیمت بالای EMA20")
        elif rsi15 <= 42 and price < e20_15 and Su["px1h"] < 0 and ex > -2.2: put("mom", -1, 0.45 + min(0.4, (45 - rsi15) / 25), f"RSI ۱۵م {rsi15:.0f} و قیمت زیر EMA20")
        else: put("mom", 0, 0, "مومنتوم کافی نیست یا قیمت از EMA20 کشیده شده")
    def f_brk():
        H, L, C = r15.High.values, r15.Low.values, r15.Close.values; hh, ll = H[-23:-3].max(), L[-23:-3].min(); ex = float((r15.High - r15.Low).iloc[-3:].max())
        if C[-3:].max() > hh and price > hh - 0.2 * a and ex >= 1.1 * a and Su["ext"] < 2.5: put("brk", 1, 0.6 + (0.2 if abs(price - hh) <= 0.5 * a else 0), f"شکست سقف ۲۰کندلی {hh:,.{PXD}f} با انبساط نوسان")
        elif C[-3:].min() < ll and price < ll + 0.2 * a and ex >= 1.1 * a and Su["ext"] > -2.5: put("brk", -1, 0.6 + (0.2 if abs(price - ll) <= 0.5 * a else 0), f"شکست کف ۲۰کندلی {ll:,.{PXD}f} با انبساط نوسان")
        else: put("brk", 0, 0, "شکست تأییدشده با انبساط نوسان وجود ندارد")
    def f_smc():
        sw = Su["sweeps"]; s_ = sw[0] if sw else None
        if s_ and s_["mss"] and s_["ago"] <= 14:
            b = s_["bias"]; cf = 0.5 + (0.25 if s_["disp"] else 0) + 0.2 - (0.2 if (b == 1 and pos > 0.55) or (b == -1 and pos < 0.45) else 0)
            put("smc", b, cf, f"سوییپ {s_['name']} ← MSS{' + دیس‌پلیسمنت' if s_['disp'] else ''} ({s_['ago'] * 5} دقیقه پیش)")
        else: put("smc", 0, 0, "سوییپ بدون MSS یا اصلاً سوییپ تازه نیست" if sw else "سوییپ تازه‌ای نیست")
    def f_ict():
        sw = Su["sweeps"]; s_ = sw[0] if sw else None
        if not s_ or not s_["mss"]: put("ict", 0, 0, "چرخهٔ سوییپ ← MSS کامل نیست"); return
        b = s_["bias"]; op = {n: p for n, p, _ in Su["opens"]}.get("NY midnight open"); kz = any(k in Su["session"] for k in ("killzone", "Silver Bullet", "cash open"))
        pts = sum([s_["name"] in ("PDH", "PDL", "Asia high", "Asia low", "London high", "London low", "PWH", "PWL"), True, bool(s_["disp"]), kz, (pos < 0.5) if b == 1 else (pos > 0.5), (op is not None and ((price < op) if b == 1 else (price > op)))])
        if pts >= 4: put("ict", b, pts / 6, f"{pts} از ۶ معیار ICT (سشن: {Su['session'][:28]})")
        else: put("ict", 0, 0, f"فقط {pts} از ۶ معیار ICT برقرار است")
    def f_trend():
        v_, t4 = int(now.votes), Su["trend"]["4h"][0]
        if v_ >= 3 and price > e50_15 and t4 >= 0: put("trend", 1, 0.5 + 0.12 * (v_ - 2) + (0.15 if t4 == 1 else 0), f"هم‌جهتی ۱۵م/۳۰م/۱س/۱روز = {v_:+d}")
        elif v_ <= -3 and price < e50_15 and t4 <= 0: put("trend", -1, 0.5 + 0.12 * (-v_ - 2) + (0.15 if t4 == -1 else 0), f"هم‌جهتی ۱۵م/۳۰م/۱س/۱روز = {v_:+d}")
        else: put("trend", 0, 0, f"روند هم‌جهت نیست (امتیاز {v_:+d})")
    def f_pos():
        dc = d1.Close; e20d, e50d, e200d = (float(ema(dc, n).iloc[-1]) for n in (20, 50, 200)); last = float(dc.iloc[-1])
        if e20d > e50d and last > e200d: put("pos", 1, 0.5 + (0.1 if last > e20d else 0), "فاز کلان روزانه صعودی (EMA20>50 و بالای EMA200)")
        elif e20d < e50d and last < e200d: put("pos", -1, 0.5 + (0.1 if last < e20d else 0), "فاز کلان روزانه نزولی (EMA20<50 و زیر EMA200)")
        else: put("pos", 0, 0, "فاز کلان روزانه مختلط")
    for k, fn in (( "meanrev", f_meanrev), ("scalp", f_scalp), ("range", f_range), ("grid", f_grid), ("swing", f_swing), ("pa", f_pa), ("sd", f_sd), ("mom", f_mom), ("brk", f_brk), ("smc", f_smc), ("ict", f_ict), ("trend", f_trend), ("pos", f_pos)): run(k, fn)
    return V, {"er": float(er), "session": Su["session"], "pos": float(pos), "Su": Su}

_CV = {"t": 0.0, "key": None, "V": None, "meta": None}
def _votes_cached(now, price):
    key = (round(float(now.c), 4), ASSET)
    if _CV["V"] is not None and _CV["key"] == key and time.time() - _CV["t"] < 20: return _CV["V"], _CV["meta"]
    V, meta = _style_votes(now, price); _CV.update(t=time.time(), key=key, V=V, meta=meta); return V, meta

COUNCIL_PROMPT = """You are the STRATEGY COUNCIL of a professional scalp desk trading <<ASSET>>: 13 world-class specialists, each an expert of ONE style. Every specialist judges ONLY with the rules of his own playbook and ONLY with the data below. The desk trades only setups that can realistically reach 3R (scalp stop about 0.8 ATR(15m), or just beyond liquidity), so a specialist votes LONG/SHORT when his style's trigger is present RIGHT NOW; otherwise NONE. Each specialist is a proud, confident professional: he commits to a view when his playbook supports it and speaks with conviction. Never invent prices or levels. SCALP HORIZON (the owner's hard rule): the owner scalps with a relatively large position, so every trade must be settled within 1-2 hours: the limit order lives 30 minutes, and if TP1 (1.5R) is not reached within 2 hours after the fill the trade is closed at market. The stop is scalp-sized (about 0.8 ATR of the 15m chart, up to 1.3 when a liquidity pool must be cleared). Judge every setup by REACH: can TP1 and TP2 (3R) realistically be hit inside two hours given the ATR, the session and the nearest opposing liquidity? If the structural stop is wider than about 1.3 ATR the setup is too slow for this desk: lower the grade or WAIT and name the tighter entry (after sweep + MSS, at the FVG/OB) that would make the stop tight. Never choose a wide stop just to be safe. OWNER'S LIVE EVIDENCE (v11): in the owner's last three live trades (BTC, ETH and Gold SHORTS, all 5m, entered at a premium after a sweep of the highs and a displacement leg down, stop beyond the swept high, limit order) EVERY ONE reached 3R (BTC 62272 -> 61362, ETH 1762.7 -> 1729.8, Gold 3615 -> 3537) although this desk had estimated a low probability and the owner took them anyway. Small sample, but the lesson is real: over-cautious probability estimates cost money, and a setup with a clear structural reason and 1:3 room is a GOOD trade even at 35-45%. Be confident, decisive and energetic; present risks as a management plan, never as discouragement. Stay honest: never invent levels or evidence.
PLAYBOOKS:
<<PLAYBOOKS>>

ENGINE CHECKS (deterministic code votes; confirm or overrule each with a reason):
<<CODE>>

ENGINE REPORT:
<<REPORT>>

LESSONS FROM THE DESK JOURNAL (do not repeat these mistakes):
<<LESSONS>>

Reply with ONE JSON object only (no markdown): {"votes":{"meanrev":{"v":"LONG|SHORT|NONE","c":<1-10>,"why":"<Persian, max 22 words, confident voice, name the concrete trigger>"}, ... all 13 keys: meanrev, scalp, range, grid, swing, pa, sd, mom, brk, smc, ict, trend, pos ...},"best_styles":["<key>","<key>"],"teach":"<Persian, one sentence: the most important lesson for the team right now>"}"""

def council_prepare(pr=None, force=False):
    """قسمت مدلی شورا (یک تماس واحد برای هر ۱۳ سبک)؛ ۲۰ دقیقه کش می‌شود. اگر خطا بدهد شورا فقط با رأی‌های کدِ قطعی کار می‌کند."""
    if not (COUNCIL_ON and COUNCIL_LLM and USE_AGENTS and AG["ok"]): return
    L = AG.get("council_llm")
    if L and not force and (utcnow() - L["t"]).total_seconds() / 60 < COUNCIL_REFRESH_MIN: return
    try:
        now, age = snapshot()
        if age > MAX_AGE_MIN: return
        a = float(now.atr); price = pr if pr is not None else live_price(now.c)[0]; V, meta = _votes_cached(now, price)
        S = smc_engine(DATA[0], DATA[1], a, price, AG["side"] or 1, extras=True); rep = _smc_report(S)
        print("شورای سبک‌ها در حال بررسی (۱۳ متخصص، یک تماس) ...")
        code = "\n".join(f"{k}: {'LONG' if v > 0 else 'SHORT' if v < 0 else 'NONE'} (conf {cf:.2f}) {why}" for k, (v, cf, why) in V.items())
        prompt = (COUNCIL_PROMPT.replace("<<ASSET>>", ASSET_DESC.get(ASSET, ASSET)).replace("<<PLAYBOOKS>>", "\n".join(f"- {PLAYBOOKS[k]}" for k, _, _ in [x_ for x_ in STYLES if x_[0] != "macro"]))
                  .replace("<<CODE>>", code).replace("<<REPORT>>", rep).replace("<<LESSONS>>", _lessons()))
        deep, quick = _models(); j = None; last = ""
        for k_, model in enumerate((deep, quick)):
            try:
                j, _ = _llm_json(prompt, model)
                if not isinstance(j.get("votes"), dict): raise ValueError("votes نامعتبر")
                break
            except Exception as e: last = f"{type(e).__name__}: {str(e)[:160]}"; j = None; print(f"⚠ شورای سبک‌ها تلاش {k_ + 1}: {last}"); time.sleep(4)
        if j is None: AG["council_err"] = last; return
        vt = {}
        for k, _, _ in [x_ for x_ in STYLES if x_[0] != "macro"]:
            x = j["votes"].get(k) or {}; sv = str(x.get("v", "NONE")).upper()
            try: cf = float(x.get("c", 5)) / 10.0
            except Exception: cf = 0.5
            vt[k] = ({"LONG": 1, "SHORT": -1}.get(sv, 0), max(0.0, min(1.0, cf)), str(x.get("why") or ""))
        AG["council_llm"] = {"t": utcnow(), "votes": vt, "best": [b for b in (j.get("best_styles") or []) if b in _SNAME][:2], "teach": str(j.get("teach") or "")}
    except Exception as e: AG["council_err"] = f"{type(e).__name__}: {str(e)[:200]}"; print("⚠ شورای سبک‌ها خطا داد:", AG["council_err"])

def _merge_llm_v11(V):
    """کد و مدل هم‌نظر = اطمینان بالاتر | مخالف = رأی صفر (تعارض) | فقط مدل = نصف اطمینان | فقط کد (وقتی مدل «هیچ» گفته) = صفر."""
    L = AG.get("council_llm")
    if not L: return {k: (v, cf, why, "code") for k, (v, cf, why) in V.items()}
    out = {}
    for k, (v, cf, why) in V.items():
        lv, lc, lw = L["votes"].get(k, (0, 0.0, ""))
        if v != 0 and lv == v: out[k] = (v, min(1.0, (cf + lc) / 2 + 0.15), f"{why} | مدل: {lw}", "both")
        elif v != 0 and lv != v: out[k] = (0, 0.0, f"تعارض کد و مدل (کد: {why} | مدل: {lw or 'نظری نداد'})", "conflict")
        elif v == 0 and lv != 0 and k not in ("grid", "meanrev", "range", "pos"): out[k] = (lv, lc * 0.5, f"فقط نظر مدل (نصف وزن): {lw}", "llm")
        else: out[k] = (0, 0.0, why, "code")
    return out

def council_pack(V2, meta, side):
    """جمع‌بندی شورا نسبت به جهت سیگنال: وزن اولیه (ترتیب عکس) × رژیم بازار × کالیبراسیون ژورنال × اطمینان."""
    er = meta["er"]; cal = _style_calib(); trendy, rangy = er >= 0.45, er <= 0.28; ch = chair_board() if CHAIR_ON else {"k": None}; fm = _style_form()
    RM = {k: 1.0 for k, _, _ in STYLES}
    if trendy: RM.update(trend=1.25, mom=1.25, brk=1.25, swing=1.2, pos=1.1, meanrev=0.5, range=0.5)
    if rangy: RM.update(meanrev=1.25, range=1.25, sd=1.15, trend=0.6, mom=0.6, brk=0.6)
    rows = []; tf = ta = net = 0.0; nf = na = nn = 0
    for k, name, emo in STYLES:
        v, cf, why, src = V2[k]; w = W0[k] * RM[k] * cal.get(k, 1.0); rows.append({"k": k, "name": name, "emo": emo, "v": v, "cf": cf, "why": why, "w": w, "src": src}); net += v * w * cf
        if v == 0: nn += 1
        elif v == side: nf += 1; tf += w * cf
        else: na += 1; ta += w * cf
    agree = tf / (tf + ta) if (tf + ta) > 0 else 0.0
    best = (AG.get("council_llm") or {}).get("best") or [r["k"] for r in sorted([r for r in rows if r["v"] == side], key=lambda r: -r["w"] * r["cf"])[:2]]
    return {"rows": rows, "nf": nf, "na": na, "nn": nn, "agree": agree, "net": net, "regime": "روندی" if trendy else "رنج" if rangy else "مختلط", "er": er,
            "pts": 15.0 * agree * min(1.0, nf / 5.0), "best": best, "teach": (AG.get("council_llm") or {}).get("teach", "")}

def council_state(now, price, side):
    V, meta = _votes_cached(now, price); Cp = council_pack(_merge_llm(V), meta, side); AG["council_net"] = Cp["net"]; AG["council"] = Cp; return Cp

CEO_PROMPT = """You are the CEO of a professional scalp-trading desk. Under you: 14 specialists (they no longer vote on direction: they choose WHICH playbook strategy fits the setup), an ICT/SMC specialist, a tactical x fundamental debate desk and a portfolio overseer. You know every style better than any of them and you are responsible for everything: strategy, risk, discipline, execution and coaching. You are a brave, professional leader who thinks in expectancy and backs good setups with conviction.

TRADE MANAGEMENT IS FIXED AND NEVER IMPROVISED: discipline and consistency in how positions are taken are the main source of long-term profit, so do NOT suggest extra partial profit-taking (for example at +1R), early exits or any new management trick; the only management is TP1 closes half and the stop moves to break-even, TP2 closes the rest. Also always weigh RSI (5m/15m/1h and divergence) and the CROWD STOP MAP in your verdict. THE DESK'S ECONOMICS: every trade has reward:risk of at least 1:<<MINRR>>. Main card: TP1 = 1.5R closes half and moves the stop to break-even, TP2 = 3R closes the rest (win = +0.75R after TP1 or +2.25R at TP2, loss = -1R). Runner card: 3R / 5R. Break-even hit-rate is only about 25-33%, so a setup with a real structural reason and 35-45% chance of reaching TP1 (1.5R) is a profitable trade. The owner wants a strong, confident desk: you approve good setups with conviction, you use grades (A/B/C) to express quality instead of saying no, and you reserve WAIT/NO for real invalidations. OWNER'S LIVE EVIDENCE (v11): in the owner's last three live trades (BTC, ETH and Gold SHORTS, all 5m, entered at a premium after a sweep of the highs and a displacement leg down, stop beyond the swept high, limit order) EVERY ONE reached 3R (BTC 62272 -> 61362, ETH 1762.7 -> 1729.8, Gold 3615 -> 3537) although this desk had estimated a low probability and the owner took them anyway. Small sample, but the lesson is real: over-cautious probability estimates cost money, and a setup with a clear structural reason and 1:3 room is a GOOD trade even at 35-45%. Be confident, decisive and energetic; present risks as a management plan, never as discouragement. Stay honest: never invent levels or evidence.
SCALP HORIZON (the owner's hard rule): the owner scalps with a relatively large position, so every trade must be settled within 1-2 hours: the limit order lives 30 minutes, and if TP1 (1.5R) is not reached within 2 hours after the fill the trade is closed at market. The stop is scalp-sized (about 0.8 ATR of the 15m chart, up to 1.3 when a liquidity pool must be cleared). Judge every setup by REACH: can TP1 and TP2 (3R) realistically be hit inside two hours given the ATR, the session and the nearest opposing liquidity? If the structural stop is wider than about 1.3 ATR the setup is too slow for this desk: lower the grade or WAIT and name the tighter entry (after sweep + MSS, at the FVG/OB) that would make the stop tight. Never choose a wide stop just to be safe. 
GO when the key conditions hold: (1) the trade comes from an ACTIVE playbook strategy (see PLAYBOOK STRATEGY DESK) whose backtest in the CURRENT session is not negative, and the specialists' strategy preference supports it, (2) there is a structural reason for the entry (sweep/zone/pullback/breakout retest), (3) the stop sits behind liquidity and 1R is manageable, (4) there is room to 3R before strong opposing liquidity, (5) NO High/Medium-impact scheduled release within the next 30 minutes or the last 15 minutes (see SCHEDULED NEWS; if one is there, the verdict can only be WAIT or NO) and the chief economist does not strongly contradict the trade, (6) discipline limits are fine. One missing secondary condition lowers the grade to B or C; it does not turn GO into WAIT. WAIT = valid idea but wrong moment (give the exact trigger). NO = invalidated, against HTF structure with no reversal sequence, no room to 3R, or a discipline limit is hit.
Grades: A = rare and excellent (a playbook strategy with positive backtest in this session + >=3 independent confirmations + structure + clear room to 3R). B = valid with one notable gap. C = marginal.
p_tp1 = your honest, calibrated probability (0-100) that price reaches 1.5R before the stop. Typical valid structural setups are 35-55%. Do not lowball out of caution and do not inflate either; it is checked against the journal later.

PROPOSED TRADE: <<SIDE>> limit order on <<ASSET>>; team rating: <<RATING>>
PLAYBOOK STRATEGY DESK (the ONLY trade tools of this desk; the desk trades nothing outside these strategies; judge by the backtest of THIS session; win-rate alone is misleading, expectancy decides):
<<STRAT>>
ADVISORY STYLE VIEWS, NOT DECISIVE (regime: <<REGIME>>, ER=<<ER>>; weighted agreement with the trade: <<AGREE>>%; agree <<NF>> / against <<NA>> / no view <<NN>>):
<<COUNCIL>>
ICT/SMC SPECIALIST: <<SMC>>
PORTFOLIO OVERSEER: <<DESK>>
ROOM TO TARGETS: <<ROOM>>
TIMEFRAME TREND VOTES (15m, 30m, 1h, 1d): <<VOTES>> | session: <<SESSION>>
CHIEF ECONOMIST (PhD, fundamentals only): <<ECON>>
SCHEDULED NEWS (Forex Factory): <<NEWS>>
DISCIPLINE: today's closed R = <<TODAYR>> over <<TODAYN>> trades; current losing streak = <<STREAK>>
JOURNAL BY TIER (n, win-rate): <<TIERS>>
LESSONS FROM THE JOURNAL: <<LESSONS>>
ENGINE REPORT:
<<REPORT>>

Reply with ONE JSON object only (no markdown): {"verdict":"GO|WAIT|NO","grade":"A|B|C","p_tp1":<0-100>,"p_tp2":<0-100>,"eta_min":<10-120: honest minutes until TP1 if the setup works>,"primary_style":"<one of the 13 keys>","support":["<key>","<key>"],"rr_ok":true|false,
"why":"<Persian, two short confident sentences in a decisive, encouraging leader's voice>","trigger":"<Persian: exact trigger to wait for if WAIT/NO, else empty>",
"ops":{"before":"<Persian max 20 words: how to place/manage the order>","after_tp1":"<Persian max 20 words>","invalid":"<Persian max 20 words: what cancels the trade>","session":"<Persian max 20 words: timing/news/session note>"},
"coach":"<Persian, one sentence: an instruction or lesson for the whole team>",
"growth":"<Persian, 2 short sentences: your progress review of the staff - name 1-2 specialists by their Persian style name, praise what worked and give each one a concrete skill to upgrade this week>"}"""

def ceo_prepare(pr=None):
    """مدیرعامل: بعد از شورا، ایجنت ICT، مناظره و مدیر سبد، حکم نهایی + برنامهٔ اجرایی + درس تیم را می‌دهد. نتیجه در AG['ceo']."""
    AG["ceo_tried"] = True; AG["ceo"] = None; AG["ceo_err"] = ""
    if not (CEO_ON and USE_AGENTS and AG["ok"]): return
    try:
        now, age = snapshot(); side = AG["side"]
        if side == 0 or age > MAX_AGE_MIN: return
        print("مدیرعامل در حال جمع‌بندی نهایی (شورا + ICT + مدیر سبد + انضباط) ...")
        a = float(now.atr); price = pr if pr is not None else live_price(now.c)[0]; S = smc_engine(DATA[0], DATA[1], a, price, side, extras=True); rep = _smc_report(S)
        Cp = council_state(now, price, side); e20 = float(now.ema20) + (2 / 21) * (price - float(now.ema20)); e = float(entry_price(price, e20, a, side)); rr = _rr_room(S, e, SL_ATR * a, side)
        cl = "\n".join(f"- {r['emo']} {r['k']}: {'AGREES' if r['v'] == side else 'AGAINST' if r['v'] == -side else 'no view'} (conf {r['cf']:.2f}, weight {r['w']:.2f}) {r['why']}" for r in Cp["rows"])
        smc = AG.get("smc"); dk = AG.get("desk"); tr, tn, stk = _today_stats()
        smc_t = f"{smc['verdict']} (conf {smc['confidence']}): {smc['summary']}" if smc else "not available"
        dk_t = f"{dk['decision']} grade {dk['grade']} p_tp1={dk['p_tp1']}%: {dk['summary']} | risks: {dk['risks']}" if dk else "not available"
        ts = ", ".join(f"{t}: n={_tier_stat(t)[0]} wr={_tier_stat(t)[1]:.0%}" for t in ("GOLD", "STANDARD", "RISKY"))
        prompt = (CEO_PROMPT.replace("<<STRAT>>", _strat_txt()).replace("<<MINRR>>", f"{MIN_RR:g}").replace("<<SIDE>>", "LONG (buy)" if side == 1 else "SHORT (sell)").replace("<<ASSET>>", ASSET_DESC.get(ASSET, ASSET)).replace("<<RATING>>", str(AG["rating"]))
                  .replace("<<REGIME>>", Cp["regime"]).replace("<<ER>>", f"{Cp['er']:.2f}").replace("<<AGREE>>", f"{Cp['agree'] * 100:.0f}").replace("<<NF>>", str(Cp["nf"])).replace("<<NA>>", str(Cp["na"])).replace("<<NN>>", str(Cp["nn"]))
                  .replace("<<COUNCIL>>", cl).replace("<<SMC>>", smc_t).replace("<<DESK>>", dk_t).replace("<<ROOM>>", (f"nearest strong opposing liquidity {rr[1]} ({rr[2]}) is {rr[0]:.1f}R away (R measured with a 1 ATR stop)" if rr else "no strong opposing liquidity found in range"))
                  .replace("<<VOTES>>", f"{now.d15m:+.0f}, {now.d30m:+.0f}, {now.d1h:+.0f}, {now.d1d:+.0f}").replace("<<SESSION>>", S["session"]).replace("<<ECON>>", _econ_txt()).replace("<<CHAIR>>", _chair_txt()).replace("<<NEWS>>", _news_txt()).replace("<<TODAYR>>", f"{tr:+.1f}").replace("<<TODAYN>>", str(tn)).replace("<<STREAK>>", str(stk))
                  .replace("<<TIERS>>", ts).replace("<<LESSONS>>", _lessons()).replace("<<REPORT>>", _cut(rep, 3500)))
        deep, quick = _models(); j = None; last = ""
        for k_, model in enumerate((deep, deep, quick)):
            try:
                j, _ = _llm_json(prompt, model)
                if str(j.get("verdict", "")).upper() not in ("GO", "WAIT", "NO") or str(j.get("grade", "")).upper() not in ("A", "B", "C"): raise ValueError("verdict/grade نامعتبر")
                break
            except Exception as ex: last = f"{type(ex).__name__}: {str(ex)[:200]}"; j = None; print(f"⚠ مدیرعامل تلاش {k_ + 1}: {last}"); time.sleep(5)
        if j is None: AG["ceo_err"] = last; return
        def _i(x):
            try: return int(float(x))
            except Exception: return None
        ops = j.get("ops") if isinstance(j.get("ops"), dict) else {}
        AG["ceo"] = {"verdict": str(j["verdict"]).upper(), "grade": str(j["grade"]).upper(), "p_tp1": _i(j.get("p_tp1")), "p_tp2": _i(j.get("p_tp2")), "primary": str(j.get("primary_style") or ""),
                       "support": [x for x in (j.get("support") or []) if x in _SNAME][:3], "rr_ok": str(j.get("rr_ok", True)).lower() not in ("false", "0", "no"), "why": str(j.get("why") or ""),
                       "trigger": str(j.get("trigger") or ""), "ops": {k: str(ops.get(k) or "") for k in ("before", "after_tp1", "invalid", "session")}, "coach": str(j.get("coach") or ""), "growth": str(j.get("growth") or ""), "t": utcnow()}
        _eta = _i(j.get("eta_min")); AG["ceo"]["ops"]["eta"] = (f"حدود {_eta} دقیقه" if _eta else "")
    except Exception as e: AG["ceo_err"] = f"{type(e).__name__}: {str(e)[:250]}"; print("⚠ مدیرعامل خطا داد:", AG["ceo_err"])

def _desk_prepare_v11(pr=None):      # v11: شورای سبک‌ها (کش) ← ایجنت ICT/SMC + مناظره + مدیر سبد (نسخهٔ قبلی) ← مدیرعامل
    council_prepare(pr); _desk_prepare0(pr); ceo_prepare(pr)

_CSS += """<style>
.ta-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:8px;margin:8px 0}
.ta-tile{border:1px solid var(--c);border-radius:12px;padding:7px 6px;text-align:center;background:rgba(128,128,128,.07);position:relative;overflow:hidden}
.ta-tile:before{content:'';position:absolute;inset:0 0 auto 0;height:3px;background:var(--c)}
.ta-tile .te{font-size:22px;line-height:1.2}.ta-tile .tn{font-size:12.5px;font-weight:600}.ta-tile .tv{font-weight:800;font-size:14px;color:var(--c);direction:ltr}.ta-tile .tw{font-size:11px;opacity:.65}.ta-tile .ty{font-size:11px;opacity:.9;margin-top:4px;line-height:1.5;text-align:center}
.ta-ceo{border-radius:16px;padding:14px 16px;margin:8px 0;color:#fff;box-shadow:0 3px 14px rgba(0,0,0,.35);background:linear-gradient(120deg,#1b1530,#3a2a6b 55%,#7a5c10)}
.ta-ceo b.t{font-size:18px;font-weight:800}.ta-ceo .pill{display:inline-block;border-radius:999px;padding:1px 12px;margin:3px 0 0 6px;font-size:12.5px;background:rgba(255,255,255,.18)}
.ta-ceo ul{margin:6px 0 0;padding:0 18px 0 0;font-size:13px}.ta-ceo .sub{opacity:.85;font-size:12.5px;margin-top:6px}
.ta-bar{height:10px;border-radius:6px;overflow:hidden;background:rgba(229,72,77,.55);margin:6px 0}.ta-bar>div{height:100%;background:#30a46c}
.ta-ladder{display:flex;align-items:center;gap:0;margin:2px 14px 8px;font-size:11.5px;direction:ltr}
.ta-ladder span{flex:1;text-align:center;padding:2px 0;color:#fff;font-weight:700}
.ta-card.gold{border:1.5px solid #d4af37;background:linear-gradient(160deg,rgba(212,175,55,.13),rgba(60,40,0,.10));box-shadow:0 0 16px rgba(212,175,55,.35)}
.ta-card.gold .ph{background:linear-gradient(110deg,#7a5c10 0%,#f3d36b 30%,#fff3b0 50%,#d4af37 70%,#8d6b12 100%)!important;background-size:200% 100%;animation:taShine 3.5s linear infinite;color:#2b1d00!important}
.ta-card.gold td.v{color:#e9c64f}.ta-card.gold tr.sl td.v{color:#ff6b6b}.ta-card.gold tr.tp td.v{color:#f3d36b;text-shadow:0 0 8px rgba(243,211,107,.45)}
.ta-card.gold .ps,.ta-card.gold .pf{color:#e9c64f;opacity:.95}
.ta-goldtxt{background:linear-gradient(100deg,#b8860b,#f3d36b 30%,#fff7c2 50%,#f3d36b 70%,#b8860b);background-size:200% 100%;-webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent;color:#f3d36b;animation:taShine 3s linear infinite;text-shadow:none}
.ta-dim{opacity:1;filter:none}   /* v11: کم‌رنگی حذف شد */
@media (max-width:520px){.ta-grid{grid-template-columns:repeat(2,1fr)}.ta-card td.v{font-size:15px}}
</style>"""

def _council_panel_v11(Cp, ck, side):
    """پنل «تیم»: مدیرعامل در بالا، ۱۳ ایجنت سبک به‌صورت کاشی (سبز = هم‌جهت، قرمز = مخالف، خاکستری = بی‌نظر) و نوار توافق."""
    out = ""
    if ck:
        vc = {"GO": "#30a46c", "WAIT": "#d99a00", "NO": "#e5484d"}[ck["verdict"]]; sup = " ، ".join(f"{_SNAME[k][1]} {_SNAME[k][0]}" for k in ([ck["primary"]] if ck["primary"] in _SNAME else []) + ck["support"])
        ops = "".join(f"<li><b>{lab}:</b> {_h(ck['ops'][k])}</li>" for lab, k in (("قبل از ورود", "before"), ("⏱ تخمین زمان تا TP1", "eta"), ("بعد از تارگت ۱", "after_tp1"), ("باطل‌شدن", "invalid"), ("زمان‌بندی/خبر", "session")) if ck["ops"].get(k))
        out += (f"<div class='ta-ceo'><b class='t'>👔 مدیرعامل</b> <span class='pill' style='background:{vc}'>{ck['verdict']}</span><span class='pill'>درجه {ck['grade']}</span>"
                f"<span class='pill'>احتمال TP1 ≈ {ck['p_tp1'] if ck['p_tp1'] is not None else '؟'}٪</span><span class='pill'>{'✅ ۱:۳ ممکن' if ck['rr_ok'] else '⚠ ۱:۳ مشکوک'}</span>"
                f"<div style='margin-top:8px'>{_h(ck['why'])}</div>" + (f"<div class='sub'>🎯 سبک‌های محرک: {_h(sup)}</div>" if sup else "")
                + (f"<div class='sub'>⏳ منتظر: {_h(ck['trigger'])}</div>" if ck["trigger"] else "") + (f"<ul>{ops}</ul>" if ops else "") + (f"<div class='sub'>🎓 درس به تیم: {_h(ck['coach'])}</div>" if ck["coach"] else "") + (f"<div class='sub'>📈 ارزیابی رشد پرسنل: {_h(ck['growth'])}</div>" if ck.get("growth") else "") + "</div>")
    if not COUNCIL_ON or Cp is None: ui(out); return      # v15: شورا فقط مشاور است؛ کاشی‌های ۱۴ سبک نمایش داده نمی‌شود
    tiles = ""
    for r in Cp["rows"]:
        col = "#30a46c" if r["v"] == side else "#e5484d" if r["v"] == -side else "#8a8f98"; vv = (f"{'▲' if r['v'] > 0 else '▼'} {r['cf'] * 100:.0f}٪" if r["v"] else "بی‌نظر")
        tiles += f"<div class='ta-tile' style='--c:{col}' title='{_h(r['why'])}'><div class='te'>{r['emo']}</div><div class='tn'>{_h(r['name'])}</div><div class='tv'>{vv}</div><div class='tw'>وزن {r['w']:.2f}</div><div class='ty'>{_h(r['why'])}</div></div>"
    out += (f"<div style='font-weight:800;margin:10px 0 2px'>🏛 شورای ۱۴ نفره (پرسنل میز) · رژیم بازار: {Cp['regime']} (ER={Cp['er']:.2f}) · هم‌جهت {Cp['nf']} | مخالف {Cp['na']} | بی‌نظر {Cp['nn']}</div>"
            f"<div class='ta-bar'><div style='width:{Cp['agree'] * 100:.0f}%'></div></div><div style='font-size:12.5px;opacity:.85'>توافق وزنی با جهت سیگنال: <b>{Cp['agree'] * 100:.0f}٪</b> (وزن اولیه از ترتیب عکس شما، اصلاح‌شده با رژیم بازار و ژورنال)</div><div class='ta-grid'>{tiles}</div>")
    ui(out)
    ui_fold("📋 دلیل رأی هر سبک", "\n".join(f"{r['emo']} {r['name']}: {'هم‌جهت' if r['v'] == side else 'مخالف' if r['v'] == -side else 'بی‌نظر'} — {r['why']}" for r in Cp["rows"]) + (f"\n\n🎓 درس شورا: {Cp['teach']}" if Cp["teach"] else ""), open_=True)

def style_stats():
    rows = [x for x in _jread() if x.get("R") is not None and x.get("styles")]
    if not rows: return
    df = pd.DataFrame([{"style": _SNAME.get(s_, (s_, ""))[0], "R": x["R"]} for x in rows for s_ in x["styles"]])
    g = df.groupby("style").R.agg(["count", "mean", lambda s: (s > 0).mean()]); g.columns = ["تعداد", "میانگین R", "نرخ برد"]; ui_table(g.round(2), "به تفکیک سبک (هر سبکی که هم‌جهت رأی داده بود؛ وزن شورا از همین‌ها اصلاح می‌شود)")


# ================= v12: تقویم خبری فارکس‌فکتوری + اقتصاددان ارشد (PhD) + شورای ۱۴ نفره (ICT یکی از اعضا) + نفت‌شناس =================
# ---------- ۱) نگهبان خبر: هر بار که سیگنال ساخته یا قیمت تازه می‌شود، تقویم فارکس‌فکتوری چک می‌شود ----------
_NEWS = {"t": None, "tf": None, "ev": [], "err": ""}
_NEWS_CCY = {"USOIL": ("USD", "CNY"), "Gold": ("USD", "CNY"), "BTC": ("USD",), "ETH": ("USD",), "DOGE": ("USD",), "SHIB": ("USD",), "EURUSD": ("EUR", "USD"), "GBPUSD": ("GBP", "USD"), "US30": ("USD",), "NAS100": ("USD",)}

def news_events(force=False):
    """رویدادهای این هفتهٔ فارکس‌فکتوری (فید رسمی خودشان). ۱۰ دقیقه کش می‌شود؛ اگر فید جواب نداد، کش قبلی و در نبودش None برمی‌گردد."""
    import requests
    nw = utcnow()
    if not force and _NEWS["t"] and (nw - _NEWS["t"]).total_seconds() / 60 < NEWS_REFRESH_MIN: return _NEWS["ev"]
    if not force and _NEWS["tf"] and (nw - _NEWS["tf"]).total_seconds() < 120: return _NEWS["ev"] or None      # بعد از خطا ۲ دقیقه فید را اذیت نکن (محدودیت نرخ)
    last = ""
    for url in ("https://nfs.faireconomy.media/ff_calendar_thisweek.json", "https://cdn-nfs.faireconomy.media/ff_calendar_thisweek.json"):
        try:
            r = requests.get(url, timeout=12, headers={"User-Agent": "Mozilla/5.0"})
            if r.status_code != 200: last = f"HTTP {r.status_code}"; continue
            ev = []
            for x in r.json():
                t = pd.Timestamp(x["date"]); t = (t.tz_convert("UTC") if t.tzinfo else t.tz_localize("UTC")).tz_localize(None)
                ev.append(dict(t=t.to_pydatetime(), title=str(x.get("title", "")), ccy=str(x.get("country", "")), impact=str(x.get("impact", "")),
                               forecast=str(x.get("forecast", "") or ""), previous=str(x.get("previous", "") or "")))
            _NEWS.update(t=nw, tf=None, ev=ev, err=""); return ev
        except Exception as e: last = f"{type(e).__name__}: {str(e)[:100]}"
    _NEWS["err"] = last; _NEWS["tf"] = nw
    return _NEWS["ev"] or None

def news_guard():
    """{ok, near (از NEWS_AFTER_MIN دقیقهٔ پیش تا NEWS_WINDOW_MIN دقیقهٔ دیگر)، soon (تا ۴ ساعت بعد)، day (۲۴ ساعت آینده)، err}؛ فقط اثر High/Medium ارزهای مرتبط با دارایی."""
    out = {"ok": False, "near": [], "soon": [], "day": [], "err": ""}
    if not NEWS_GUARD_ON: out["ok"] = True; return out
    try: ev = news_events()
    except Exception as e: ev = None; _NEWS["err"] = f"{type(e).__name__}: {str(e)[:100]}"
    if ev is None: out["err"] = _NEWS["err"] or "نامشخص"; return out
    out["ok"] = True; ccy = _NEWS_CCY.get(ASSET, ("USD",)); nw = utcnow()
    for x in ev:
        if x["impact"] not in ("High", "Medium") or x["ccy"] not in ccy: continue
        m = (x["t"] - nw).total_seconds() / 60; y = {**x, "mins": m, "tl": x["t"] + dt.timedelta(hours=TZ_HOURS)}
        if -NEWS_AFTER_MIN <= m <= NEWS_WINDOW_MIN: out["near"].append(y)
        elif NEWS_WINDOW_MIN < m <= 240: out["soon"].append(y)
        if -NEWS_AFTER_MIN <= m <= 24 * 60: out["day"].append(y)
    for k in ("near", "soon", "day"): out[k].sort(key=lambda z: z["t"])
    return out

def _when(m): return f"{m:.0f} دقیقهٔ دیگر" if m >= 0 else f"{-m:.0f} دقیقه پیش"

def _news_html(g, always=False):
    if not g["ok"]:
        return _note(f"📅 تقویم فارکس‌فکتوری گرفته نشد ({g['err']}). قبل از ورود خودتان forexfactory.com/calendar را ببینید.", "#d99a00") if always or NEWS_GUARD_ON else ""
    out = ""
    for x in g["near"]:
        hi = x["impact"] == "High"; c = "#e5484d" if hi else "#d99a00"
        out += (f"<div class='ta-note' style='--c:{c};--b:{c}22;font-weight:700;font-size:15px'>{'🚨' if hi else '⚠'} خبر {'مهم (High)' if hi else 'متوسط (Medium)'} فارکس‌فکتوری: {_h(x['title'])} ({_h(x['ccy'])}) · {_when(x['mins'])} · ساعت {x['tl']:%H:%M} به وقت شما"
                f"<br><span style='font-weight:400;font-size:13px'>پیش‌بینی {_h(x['forecast'] or '-')} | قبلی {_h(x['previous'] or '-')} — تا ۱۵ دقیقه بعد از انتشار سفارش نگذارید؛ اسپرد باز می‌شود و استاپ‌ها شکار می‌شوند. سفارش لیمیتِ باز را هم لغو یا دور کنید.</span></div>")
    if not g["near"] and g["soon"]:
        x = g["soon"][0]; out += _note(f"📅 خبر بعدی: {x['title']} ({x['ccy']}، {x['impact']}) {_when(x['mins'])} · ساعت {x['tl']:%H:%M} به وقت شما", "#2b8fd6")
    if not g["near"] and not g["soon"] and always: out += _note("📅 تا ۴ ساعت آینده خبر High/Medium مرتبط با این دارایی در فارکس‌فکتوری نیست.", "#30a46c")
    return out

def _news_txt():
    g = news_guard()
    if not g["ok"]: return "calendar unavailable (could not be checked)"
    ls = [f"{x['title']} ({x['ccy']}, {x['impact']}) {'in %d min' % x['mins'] if x['mins'] >= 0 else '%d min ago' % -x['mins']}; forecast {x['forecast'] or '-'}, previous {x['previous'] or '-'}" for x in g["near"] + g["soon"][:3]]
    return "; ".join(ls) or "no High/Medium release in the next 4 hours (calendar checked)"

# ---------- ۲) اقتصاددان ارشد ----------
_MACRO_T = {"USOIL": {"DXY": "DX-Y.NYB", "US10Y yield": "^TNX", "VIX": "^VIX", "OVX (oil vol)": "^OVX", "WTI": "CL=F", "Brent": "BZ=F", "RBOB gasoline": "RB=F", "Heating oil": "HO=F", "S&P500": "^GSPC"},
            "Gold": {"DXY": "DX-Y.NYB", "US10Y yield": "^TNX", "VIX": "^VIX", "Silver": "SI=F", "S&P500": "^GSPC"},
            "DOGE": {"BTC": "BTC-USD", "DXY": "DX-Y.NYB", "VIX": "^VIX"}, "SHIB": {"BTC": "BTC-USD", "DOGE": "DOGE-USD", "DXY": "DX-Y.NYB", "VIX": "^VIX"}, "EURUSD": {"DXY": "DX-Y.NYB", "US10Y yield": "^TNX", "Euro": "EURUSD=X"}, "GBPUSD": {"DXY": "DX-Y.NYB", "US10Y yield": "^TNX", "GBP": "GBPUSD=X"}, "BTC": {"DXY": "DX-Y.NYB", "US10Y yield": "^TNX", "VIX": "^VIX", "Nasdaq": "^IXIC", "Gold": "GC=F"},
            "ETH": {"DXY": "DX-Y.NYB", "US10Y yield": "^TNX", "VIX": "^VIX", "Nasdaq": "^IXIC", "BTC": "BTC-USD"},
            "US30": {"DXY": "DX-Y.NYB", "US10Y yield": "^TNX", "VIX": "^VIX", "S&P500": "^GSPC", "Nasdaq": "^IXIC"},
            "NAS100": {"DXY": "DX-Y.NYB", "US10Y yield": "^TNX", "VIX": "^VIX", "S&P500": "^GSPC", "Semis SOXX": "SOXX"}}
_FRAME = {"USOIL": "OPEC+ quotas/compliance; EIA (Wed 10:30 NY) and API (Tue) inventories versus consensus and the 5-year seasonal; Cushing stocks; refinery runs and crack spreads (3-2-1); USD and real yields; global PMI and China demand; geopolitical risk premium (Gulf/Hormuz, Iran, Russia sanctions) which creates headline spikes in BOTH directions; Brent-WTI spread; term structure (backwardation = tight); positioning; seasonality.",
          "Gold": "US real yields and Fed pricing, USD, central-bank buying, ETF flows, geopolitical safe-haven demand, inflation surprises.",
          "DOGE": "Crypto beta, BTC direction, liquidity, sentiment, meme-token volatility; avoid treating DOGE as independent from BTC.", "SHIB": "Crypto beta, BTC and DOGE direction, liquidity, social-media sentiment, exchange listings and burn news; do not treat SHIB as independent from BTC.", "EURUSD": "ECB/Fed policy divergence, euro-area and US data, yields, DXY, risk sentiment.", "GBPUSD": "BoE/Fed policy divergence, UK and US inflation/jobs data, yields, DXY and risk sentiment.", "BTC": "Global liquidity (Fed, DXY, yields), spot-ETF flows, risk appetite (Nasdaq), leverage (funding/OI), regulation and large-holder flows.",
          "ETH": "Global liquidity, ETF flows, risk appetite (Nasdaq), ETH/BTC relative strength, on-chain activity and staking/supply dynamics.",
          "US30": "Fed path and yields, US macro data (NFP, CPI, PMI, claims), earnings of industrials/financials, risk sentiment (VIX), USD.",
          "NAS100": "Fed path and real yields, mega-cap tech earnings and AI capex narrative, semiconductor cycle, VIX, USD."}
ECON_PROMPT = """You are the CHIEF ECONOMIST of a professional trading desk: a PhD macroeconomist (monetary economics, commodity and energy markets) with 20 years at a central bank and a global-macro fund. You do NOT read charts. From fundamentals only, you tell the desk which way the macro/fundamental forces lean for the next 4-24 hours on <<ASSET>> and how dangerous the event calendar is. Be rigorous: separate what the data shows from what you infer, never invent numbers, say so when data is missing or contradictory. A mixed or already-priced-in picture must be NEUTRAL; never force a view.
FRAMEWORK for this asset: <<FRAME>>
MARKET DATA (daily closes; yields in bp):
<<MACRO>>
SCHEDULED RELEASES (Forex Factory, UTC, relevant currencies, High/Medium, next 24h):
<<CAL>>
THE DESK'S OWN REPORTS (may be partial):
NEWS: <<NEWS>>
SENTIMENT: <<SENT>>
FUNDAMENTALS: <<FUND>>
Reply with ONE JSON object only (no markdown): {"bias":"LONG|SHORT|NEUTRAL","conviction":<1-10>,"horizon":"intraday|1-3 days|weeks","regime":"<Persian, one sentence: the fundamental regime>","drivers":[{"factor":"<short>","effect":"bullish|bearish|neutral","evidence":"<Persian; cite a number from the data or a named event>"}, ... 3 to 5 items ...],"catalysts":["<Persian: next relevant release/event and why it matters>"],"event_risk":"low|medium|high","intraday_note":"<Persian, max 30 words: what this means for a scalp today, e.g. which side is likelier to be stop-hunted by a headline>","invalidation":"<Persian: what would flip your view>","data_confidence":<1-10>}"""

def _macro_snapshot():
    tk = _MACRO_T.get(ASSET, _MACRO_T["Gold"]); d = yf.download(list(tk.values()), period="3mo", interval="1d", progress=False, auto_adjust=True)
    cl = d["Close"] if isinstance(d.columns, pd.MultiIndex) else d; ls = []; px = {}
    for name, t in tk.items():
        try:
            s = cl[t].dropna(); last = float(s.iloc[-1]); px[name] = last
            if "yield" in name: ch = lambda n: (last - float(s.iloc[-1 - n])) * 100; ls.append(f"{name}: {last:.3f}% | 1d {ch(1):+.0f}bp | 5d {ch(5):+.0f}bp | 20d {ch(20):+.0f}bp")
            else: ch = lambda n: (last / float(s.iloc[-1 - n]) - 1) * 100; ls.append(f"{name}: {last:,.3f} | 1d {ch(1):+.2f}% | 5d {ch(5):+.2f}% | 20d {ch(20):+.2f}%")
        except Exception: ls.append(f"{name}: n/a")
    try:
        if ASSET == "USOIL" and all(k in px for k in ("WTI", "RBOB gasoline", "Heating oil", "Brent")): ls.append(f"3-2-1 crack spread: {(2 * px['RBOB gasoline'] * 42 + px['Heating oil'] * 42 - 3 * px['WTI']) / 3:.1f} $/bbl | Brent-WTI: {px['Brent'] - px['WTI']:.2f} $")
    except Exception: pass
    try:
        _sh1 = shock_state()
        if _sh1: ls.append("CROSS-ASSET: " + ", ".join(f"{k} {v:+.1f}%" for k, v in _sh1["ch"].items()) + f" (daily move) -> synchronized {'selloff' if _sh1['dir'] == -1 else 'rally'}; treat correlated assets as one macro bet and expect trend-day behavior")
    except Exception: pass
    return "\n".join(ls)

def econ_prepare(pr=None, force=False):
    """اقتصاددان ارشد (دکترای اقتصاد): یک تماس مدل؛ ۶۰ دقیقه کش می‌شود (فاندامنتال سریع عوض نمی‌شود). نتیجه در AG['econ']."""
    if not (ECON_ON and USE_AGENTS and AG["ok"]): return
    L = AG.get("econ")
    if L and not force and (utcnow() - L["t"]).total_seconds() / 60 < ECON_REFRESH_MIN: return
    AG["econ_err"] = ""
    try:
        print("اقتصاددان ارشد (PhD) در حال ارزیابی فاندامنتال (داده‌های کلان، تقویم، گزارش تحلیلگران) ...")
        st = AG.get("state") or {}; g = news_guard()
        cal = "\n".join(f"{x['t']:%a %H:%M} UTC {x['ccy']} {x['impact']}: {x['title']} (forecast {x['forecast'] or '-'}, previous {x['previous'] or '-'})" for x in g["day"][:14]) or ("(calendar unavailable)" if not g["ok"] else "(no High/Medium release in the next 24h)")
        try: macro = _macro_snapshot()
        except Exception as e: macro = f"(macro data unavailable: {type(e).__name__})"
        prompt = (ECON_PROMPT.replace("<<ASSET>>", ASSET_DESC.get(ASSET, ASSET)).replace("<<FRAME>>", _FRAME.get(ASSET, "")).replace("<<MACRO>>", macro).replace("<<CAL>>", cal)
                  .replace("<<NEWS>>", _cut(st.get("news_report"), 1500) or "(empty)").replace("<<SENT>>", _cut(st.get("sentiment_report"), 1000) or "(empty)").replace("<<FUND>>", _cut(st.get("fundamentals_report"), 1000) or "(empty)"))
        deep, quick = _models(); j = None; last = ""
        for k_, model in enumerate((deep, deep, quick)):
            try:
                j, _ = _llm_json(prompt, model)
                if str(j.get("bias", "")).upper() not in ("LONG", "SHORT", "NEUTRAL"): raise ValueError("bias نامعتبر")
                break
            except Exception as ex: last = f"{type(ex).__name__}: {str(ex)[:200]}"; j = None; print(f"⚠ اقتصاددان تلاش {k_ + 1}: {last}"); time.sleep(5)
        if j is None: AG["econ_err"] = last; return
        def _n(x, d):
            try: return max(0, min(10, int(float(x))))
            except Exception: return d
        dr = [{"factor": str(x.get("factor", "")), "effect": str(x.get("effect", "neutral")).lower(), "evidence": str(x.get("evidence", ""))} for x in (j.get("drivers") or []) if isinstance(x, dict)][:5]
        AG["econ"] = {"bias": {"LONG": 1, "SHORT": -1}.get(str(j["bias"]).upper(), 0), "conv": _n(j.get("conviction"), 5), "horizon": str(j.get("horizon") or ""), "regime": str(j.get("regime") or ""), "drivers": dr,
                      "catalysts": [str(c) for c in (j.get("catalysts") or [])][:3], "event_risk": str(j.get("event_risk") or "low").lower(), "intraday": str(j.get("intraday_note") or ""),
                      "invalid": str(j.get("invalidation") or ""), "data_conf": _n(j.get("data_confidence"), 5), "t": utcnow()}
    except Exception as e: AG["econ_err"] = f"{type(e).__name__}: {str(e)[:250]}"; print("⚠ اقتصاددان خطا داد:", AG["econ_err"])

def _econ_txt():
    ec = AG.get("econ")
    if not ec: return "not available"
    return (f"bias {'LONG' if ec['bias'] == 1 else 'SHORT' if ec['bias'] == -1 else 'NEUTRAL'} (conviction {ec['conv']}/10, data confidence {ec['data_conf']}/10, event risk {ec['event_risk']}); regime: {ec['regime']}; intraday: {ec['intraday']}; invalidation: {ec['invalid']}")

def _econ_panel():
    ec = AG.get("econ")
    if not ec: return
    col = "#30a46c" if ec["bias"] == 1 else "#e5484d" if ec["bias"] == -1 else "#8a8f98"; lab = "صعودی" if ec["bias"] == 1 else "نزولی" if ec["bias"] == -1 else "خنثی"
    dr = "".join(f"<li>{'▲' if d['effect'] == 'bullish' else '▼' if d['effect'] == 'bearish' else '•'} <b>{_h(d['factor'])}</b>: {_h(d['evidence'])}</li>" for d in ec["drivers"])
    ui(f"<div class='ta-ceo' style='background:linear-gradient(120deg,#062a33,#0f5c6b 60%,#1b7a5a)'><b class='t'>🎓 اقتصاددان ارشد (PhD)</b> <span class='pill' style='background:{col}'>سوگیری فاندامنتال: {lab}</span><span class='pill'>اطمینان {ec['conv']}/10</span><span class='pill'>ریسک رویداد: {_h(ec['event_risk'])}</span><span class='pill'>کیفیت داده {ec['data_conf']}/10</span>"
       f"<div style='margin-top:8px'>{_h(ec['regime'])}</div><ul>{dr}</ul>" + (f"<div class='sub'>📅 کاتالیزورها: {_h(' | '.join(ec['catalysts']))}</div>" if ec["catalysts"] else "")
       + (f"<div class='sub'>🎯 برای اسکالپ امروز: {_h(ec['intraday'])}</div>" if ec["intraday"] else "") + (f"<div class='sub'>❌ نظرش عوض می‌شود اگر: {_h(ec['invalid'])}</div>" if ec["invalid"] else "") + "</div>")

# ---------- ۳) شورای ۱۴ نفره: اقتصاددان عضو اول؛ ICT فقط یکی از اعضا (ردیف ۱۳ از ۱۴) و بدون حق وتو ----------
STYLES = [("macro", "اقتصاددان (PhD)", "🎓"), ("meanrev", "بازگشت به میانگین", "🧲"), ("scalp", "اسکالپینگ", "⚡"), ("range", "رنج‌تریدینگ", "📦"), ("grid", "گرید", "🕸"),
          ("swing", "سوینگ", "🌊"), ("pa", "پرایس‌اکشن", "🕯"), ("sd", "عرضه و تقاضا", "⚖"), ("mom", "مومنتوم", "🚀"), ("brk", "بریک‌اوت", "💥"),
          ("trend", "روندپیرو", "📈"), ("smc", "اسمارت‌مانی", "🧠"), ("ict", "ICT", "🎯"), ("pos", "پوزیشن‌تریدینگ", "🏔")]
_core = [k for k, _, _ in STYLES if k != "macro"]
W0 = {k: round(1.30 - 0.5 * i / (len(_core) - 1), 3) for i, k in enumerate(_core)}; W0["macro"] = 1.25      # وزن سبک‌ها از ترتیب عکس؛ اقتصاددان وزن ثابت (فاندامنتال فیلتر است نه سبک)
_SNAME = {k: (n, e) for k, n, e in STYLES}
PLAYBOOKS["macro"] = "Chief Economist (PhD): fundamentals only (macro data, central-bank path, inventories/supply-demand, event calendar). Votes only when the fundamental picture is clear and not priced in; otherwise NONE."
PLAYBOOKS["ict"] += " One member of the council among others: it must not be double-counted with SMC and Supply&Demand (they overlap), so vote only if the full ICT sequence is present."

def _merge_llm(V):
    out = _merge_llm_v11(V); ec = AG.get("econ")
    if ec and ec["bias"] != 0: out["macro"] = (ec["bias"], min(1.0, ec["conv"] / 10 * (0.5 + 0.5 * ec["data_conf"] / 10)), ec["intraday"] or ec["regime"], "econ")
    else: out["macro"] = (0, 0.0, ("نظر خنثی یا نامطمئن: " + ec["regime"]) if ec else "اقتصاددان اجرا نشده", "econ")
    ai = AG.get("smc") if ICT_AS_MEMBER else None
    if ai and AG.get("side"):       # عامل ICT/SMC (تحلیل عمیق) حالا مغزِ عضو «ICT» شورا است؛ دیگر حکم جدا و وتو ندارد
        try: cf = float(ai["confidence"]) / 10
        except Exception: cf = 0.5
        s_ = AG["side"]
        if ai["verdict"] == "GO": out["ict"] = (s_, max(0.0, min(1.0, cf)), "عامل ICT: " + ai["summary"][:130], "ict-agent")
        elif ai["verdict"] == "NO": out["ict"] = (-s_, max(0.0, min(1.0, cf)) * 0.5, "عامل ICT ستاپ را نپذیرفت: " + ai["summary"][:110], "ict-agent")
        else: out["ict"] = (0, 0.0, "عامل ICT: هنوز زود است — " + (ai["trigger"] or ai["summary"])[:110], "ict-agent")
    return out

def council_pack(V2, meta, side):
    """جمع‌بندی شورا: وزن اولیه × رژیم بازار × کالیبراسیون ژورنال × اطمینان؛ خانوادهٔ هم‌پوشان SMC/ICT/عرضه‌وتقاضا یک‌بار و با تخفیف شمرده می‌شود (جلوگیری از چندبار شمردن یک ایده)."""
    er = meta["er"]; cal = _style_calib(); trendy, rangy = er >= 0.45, er <= 0.28; ch = chair_board() if CHAIR_ON else {"k": None}; fm = _style_form()
    RM = {k: 1.0 for k, _, _ in STYLES}
    if trendy: RM.update(trend=1.25, mom=1.25, brk=1.25, swing=1.2, pos=1.1, meanrev=0.5, range=0.5)
    if rangy: RM.update(meanrev=1.25, range=1.25, sd=1.15, trend=0.6, mom=0.6, brk=0.6)
    rows = []
    for k, name, emo in STYLES:
        v, cf, why, src = V2[k]; rows.append({"k": k, "name": name + (" (رئیس)" if k == ch["k"] else ""), "emo": "👑" if k == ch["k"] else emo, "v": v, "cf": cf, "why": why, "w": W0[k] * RM[k] * cal.get(k, 1.0) * fm.get(k, 1.0) * (CHAIR_W if k == ch["k"] else 1.0), "src": src})
    for d_ in (1, -1):
        fam = [r for r in rows if r["k"] in ("smc", "ict", "sd") and r["v"] == d_]
        if len(fam) >= 2:
            for r in fam: r["w"] *= 0.75 if len(fam) == 2 else 0.65
    tf = ta = net = 0.0; nf = na = nn = 0
    for r in rows:
        net += r["v"] * r["w"] * r["cf"]
        if r["v"] == 0: nn += 1
        elif r["v"] == side: nf += 1; tf += r["w"] * r["cf"]
        else: na += 1; ta += r["w"] * r["cf"]
    agree = tf / (tf + ta) if (tf + ta) > 0 else 0.0
    best = (AG.get("council_llm") or {}).get("best") or [r["k"] for r in sorted([r for r in rows if r["v"] == side], key=lambda r: -r["w"] * r["cf"])[:2]]
    for r in rows: r["w"] = round(r["w"], 3)
    return {"rows": rows, "nf": nf, "na": na, "nn": nn, "agree": agree, "net": net, "regime": "روندی" if trendy else "رنج" if rangy else "مختلط", "er": er,
            "pts": 15.0 * agree * min(1.0, nf / 5.0), "best": best, "teach": (AG.get("council_llm") or {}).get("teach", "")}

def _council_panel(Cp, ck, side):
    if CHAIR_ON:
        try: ui(_note(_chair_note(), "#d4af37"))
        except Exception as e: print("⚠ جدول رئیس شورا نمایش داده نشد:", str(e)[:120])
    try: _econ_panel()
    except Exception as e: print("⚠ پنل اقتصاددان نمایش داده نشد:", str(e)[:120])
    _council_panel_v11(Cp, ck, side)

def desk_prepare(pr=None):      # v12: اقتصاددان (کش) ← شورای ۱۴ نفره (کش) ← عامل ICT/SMC + مناظره + مدیر سبد ← مدیرعامل
    econ_prepare(pr); council_prepare(pr); _desk_prepare0(pr); ceo_prepare(pr)

# ---------- ۴) نفت‌شناس: عیب‌یابی دادهٔ واقعیِ ۶۰ روز گذشته (خودتان در کولب اجرا کنید) ----------
def oil_doctor(days=58, ks=(1.0, 1.5), horizon=72, step=3):
    """سه سؤال را با دادهٔ ۵ دقیقه‌ای CL=F جواب می‌دهد: (۱) اسپرد چند درصد ریسک است؟ (۲) در هر بازهٔ ساعتی (UTC) ورود تصادفی با SL برابر k×ATR چند درصد وقت قبل از استاپ به ۱:۲ و ۱:۳ می‌رسد
    (مقایسه با نقطهٔ سربه‌سر ۳۳٪ و ۲۵٪) (۳) شکست‌های کاذب: بعد از عبور قیمت از سقف/کف سوینگ، چند درصد برمی‌گردد و تا چه عمقی بیرون می‌زند (پایهٔ انتخاب بافر SL). بدون تماس مدل."""
    sp = float(SPREADS.get("USOIL", 0.06))
    d = _clean(yf.download("CL=F", start=utcnow() - dt.timedelta(days=days), interval="5m", progress=False, auto_adjust=True)).iloc[:-1]
    r15 = d.resample("15min").agg(OHLC).dropna(); A = atr(r15).reindex(d.index, method="ffill").values
    H, L, C = d.High.values, d.Low.values, d.Close.values; hr = (d.index.hour + d.index.minute / 60).values; n = len(d)
    fi = lambda m: int(m.argmax()) if m.any() else 10 ** 9
    rows = []
    for i in range(30, n - horizon - 1, step):
        if not A[i] == A[i] or A[i] <= 0: continue
        h, l = H[i + 1:i + 1 + horizon], L[i + 1:i + 1 + horizon]; e = C[i]; b = int(hr[i] // 3) * 3
        for k in ks:
            rk = k * A[i]
            for side in (1, -1):
                sl_hit = fi(l <= e - rk) if side == 1 else fi(h + sp >= e + rk)
                for R in (2, 3):
                    tp_hit = fi(h - sp >= e + R * rk) if side == 1 else fi(l + sp <= e - R * rk)
                    rows.append((b, k, R, int(tp_hit < sl_hit)))
    df = pd.DataFrame(rows, columns=["utc", "k", "R", "win"])
    ui(f"<div class='ta-note' style='--c:#2b8fd6;--b:#2b8fd61a'>📏 اسپرد {sp:g} روی ATR(15م) میانگین {np.nanmean(A):.3f} = {sp / np.nanmean(A) * 100:.0f}٪ ریسکِ ۱ ATR. اگر بالای ۱۵٪ باشد، سربار اسپرد تنها نصف لبهٔ ۱:۳ را می‌خورد.</div>")
    for R in (2, 3):
        t = df[df.R == R].pivot_table(index="utc", columns="k", values="win", aggfunc="mean") * 100; t.columns = [f"SL={c:g}×ATR" for c in t.columns]
        t["نمونه"] = df[(df.R == R) & (df.k == ks[0])].groupby("utc").size()
        ui_table(t.round(1), f"درصد رسیدن به ۱:{R} قبل از استاپ (ورود تصادفی، بعد از اسپرد) · سربه‌سر = {100 / (1 + R):.0f}٪ · ساعت UTC (ایران = +۳٫۵)")
    fo = []
    for kind in ("high", "low"):
        arr = H if kind == "high" else L
        for i in range(8, n - 70):
            w = arr[i - 5:i + 6]
            if len(w) < 11 or not (arr[i] == (w.max() if kind == "high" else w.min())) or not A[i] == A[i]: continue
            br = [j for j in range(i + 6, min(i + 66, n - 7)) if (arr[j] > arr[i] if kind == "high" else arr[j] < arr[i])]
            if not br: continue
            j = br[0]; ex = (arr[j:j + 6].max() - arr[i]) if kind == "high" else (arr[i] - arr[j:j + 6].min()); back = (C[j + 5] < arr[i]) if kind == "high" else (C[j + 5] > arr[i])
            fo.append((kind, back, ex / A[i]))
    f = pd.DataFrame(fo, columns=["kind", "fake", "ex"])
    if len(f):
        p = f[f.fake].ex.quantile([.5, .75, .9]).values if f.fake.any() else [float("nan")] * 3
        ui(f"<div class='ta-note' style='--c:#7c4dff;--b:#7c4dff1a'>🎣 {len(f)} بار قیمت از سقف/کف سوینگ ۱۵م رد شد؛ در {f.fake.mean() * 100:.0f}٪ موارد ظرف ۳۰ دقیقه برگشت (شکست کاذب). عمقی که پیش از برگشت بیرون زد: میانه {p[0]:.2f} ATR، ۷۵٪ {p[1]:.2f}، ۹۰٪ {p[2]:.2f}. "
           f"پیشنهاد: SL_BUFFER_ATR حداقل {p[1]:.2f} تا {p[2]:.2f} (الان {SL_BUFFER_ATR:g}) تا استاپ پشت‌ِ عمقِ معمولِ شکار بیفتد.</div>")
    return df, f


def _sim_geom(h, l, c_end, e, side, rk, sp, r1=None, r2=None, frac=None):
    """یک ورود فرضی با همین ساختار ثابت: SL، TP1 (نصف حجم و SL به ورود)، TP2؛ اگر در پنجره تکلیف نشد با قیمت بازار بسته می‌شود. خروجی (برچسب، R). اسپرد مثل oil_doctor."""
    r1 = SAFE_R1 if r1 is None else r1; r2 = SAFE_R2 if r2 is None else r2; frac = TP1_FRAC if frac is None else frac
    sl, t1, t2 = e - side * rk, e + side * r1 * rk, e + side * r2 * rk; st = 0
    for hi, lo in zip(h, l):
        if side == 1: hit = lo <= (sl if st == 0 else e); a1 = hi - sp >= t1; a2 = hi - sp >= t2
        else: hit = hi + sp >= (sl if st == 0 else e); a1 = lo + sp <= t1; a2 = lo + sp <= t2
        if hit: return ("sl", -1.0) if st == 0 else ("be", frac * r1)
        if st == 0 and a1: st = 1
        if st == 1 and a2: return "tp2", frac * r1 + (1 - frac) * r2
    mtm = side * (c_end - e) / rk
    return ("tp1", frac * r1 + (1 - frac) * max(mtm, 0.0)) if st else ("none", mtm)

_RS = {"key": None, "v": None}
def reach_stats(side, risk, n=900, step=2):
    """آمارِ همین هندسه روی n کندل ۵م اخیر (حدود ۳ روز): ورود فرضی در هر کندل. فقط راهنماست، نه وین‌ریت واقعی."""
    d5 = DATA[0]; key = (side, round(float(risk), 5), len(d5), str(d5.index[-1]), ASSET)
    if _RS["key"] == key: return _RS["v"]
    H, L, C = d5.High.values[-n:], d5.Low.values[-n:], d5.Close.values[-n:]; B = MAX_HOLD; sp = _spr(); c = {"sl": 0, "be": 0, "tp1": 0, "tp2": 0, "none": 0}; Rs = []
    for i in range(0, len(C) - B - 1, step):
        o, R = _sim_geom(H[i + 1:i + 1 + B], L[i + 1:i + 1 + B], C[i + B], C[i], side, float(risk), sp); c[o] += 1; Rs.append(R)
    N = max(1, sum(c.values())); v = {k: x / N for k, x in c.items()}; v["p_tp1"] = v["be"] + v["tp1"] + v["tp2"]; v["avgR"] = float(np.mean(Rs)) if Rs else 0.0; v["n"] = N
    _RS.update(key=key, v=v); return v

def chase_check(S, side, a, price):
    """دو اشتباهِ کوچک ولی گران: (۱) سفارش وقتی قیمت از EMA20 ۵م در جهت سیگنال کشیده شده (دنبال‌کردن حرکت)؛ (۲) ورود دوباره در همان جهت روی تارگتِ ترید برندهٔ ساعات اخیر (معمولاً ریتریس)."""
    out = []; ext = side * float(S["ext"])
    if ext >= CHASE_EXT_ATR: out.append(f"قیمت {ext:.1f} ATR از EMA20 ۵م در جهت سیگنال کشیده شده؛ این ورود دنبال‌کردنِ حرکت است و ریتریس‌های تند استاپ‌خورند. لیمیت را روی پولبک بگذارید، نه نزدیک قیمت.")
    now = utcnow(); D = lambda x: x + PRICE_OFFSET
    for x in reversed(_jread()):
        try:
            if x.get("asset") != ASSET or x.get("side") != side or x.get("outcome") not in ("TP2", "TP1+BE"): continue
            age_h = (now - pd.Timestamp(x["t"]).tz_localize(None)).total_seconds() / 3600
            if age_h > CHASE_HOURS: break
            tg = float(x["tp2"] if x["outcome"] == "TP2" else x["tp1"])
            if abs(D(price) - tg) <= CHASE_NEAR_ATR * a: out.append(f"قیمت دوباره نزدیک تارگتِ ترید برندهٔ {age_h:.1f} ساعت پیش (همین جهت، {tg:g}) است؛ بعد از چنین حرکتی ریتریس شایع است و دنبال‌کردنش استاپ می‌خورد.")
            break
        except Exception: continue
    return out

def scalp_doctor(days=58, ks=(0.5, 0.65, 0.8, 1.0, 1.25), step=3):
    """برای دارایی فعلی (ASSET) روی دادهٔ ۵م ۲ ماه اخیر امتحان می‌کند: با SL = k×ATR(۱۵م) و همین ساختار ثابت (TP1 و TP2 + اسپرد) در سقف MAX_HOLD کندل، چند درصد استاپ/BE/TP2/بی‌نتیجه و میانگین R. بدون تماس مدل؛ بهترین k را نشان می‌دهد."""
    sp = float(SPREADS.get(ASSET, 0.0) or 0.0)
    d = _clean(yf.download(sym, start=utcnow() - dt.timedelta(days=days), interval="5m", progress=False, auto_adjust=True)).iloc[:-1]
    r15 = d.resample("15min").agg(OHLC).dropna(); A = atr(r15).reindex(d.index, method="ffill").values; H, L, C = d.High.values, d.Low.values, d.Close.values; n = len(d); B = MAX_HOLD
    rows = []
    for k in ks:
        c = {"sl": 0, "be": 0, "tp1": 0, "tp2": 0, "none": 0}; Rs = []
        for i in range(30, n - B - 1, step):
            if not (A[i] == A[i]) or A[i] <= 0: continue
            for side in (1, -1):
                o, R = _sim_geom(H[i + 1:i + 1 + B], L[i + 1:i + 1 + B], C[i + B], C[i], side, k * A[i], sp); c[o] += 1; Rs.append(R)
        N = max(1, sum(c.values())); rows.append({"SL (×ATR ۱۵م)": k, "استاپ ٪": 100 * c["sl"] / N, "TP1 سپس BE ٪": 100 * c["be"] / N, "TP1 و خروج زمانی ٪": 100 * c["tp1"] / N, "TP2 ٪": 100 * c["tp2"] / N, "بی‌نتیجه ٪": 100 * c["none"] / N, "میانگین R": float(np.mean(Rs)), "نمونه": N})
    t = pd.DataFrame(rows).set_index("SL (×ATR ۱۵م)").round(2); ui_table(t, f"{ASSET}: ورودِ تصادفی (بدون هیچ فیلتر)، ساختار ثابت TP1={SAFE_R1:g}R نصف حجم و SL به ورود، TP2={SAFE_R2:g}R، سقف {B * 5 / 60:g} ساعت، اسپرد {sp:g}")
    best = t["میانگین R"].idxmax(); ui(_note(f"📌 در این داده بهترین میانگین R مربوط به SL = {best:g}×ATR است (الان SL_ATR = {SL_ATR:g}). این ورودِ تصادفی است؛ فیلتر و ساختار تیم لبه را بهتر می‌کند، پس عددها پایهٔ مقایسه‌اند نه وین‌ریت واقعی.", "#2b8fd6"))
    return t

def journal_seed_v13():
    """سه ترید دیشب/امروز از روی اسکرین‌شات (تقریبی؛ اگر عدد دقیق دارید جایگزین کنید): نفتِ دوم TP2، داو و طلای دوم استاپ. NAS100 هنوز باز است و ثبت نشد."""
    if any(x.get("source") == "seed13" for x in _jread()): print("نمونه‌های v13 قبلاً ثبت شده‌اند."); return
    base = dict(side=-1, rating="Sell (screenshot)", source="seed13", agents_ok=True)
    for d in ({"asset": "USOIL", "entry": 84.29, "sl": 84.85, "tp1": 83.17, "tp2": 82.61, "outcome": "TP2", "R": 2.5, "note": "نفت SELL بعد از سوییپ سقف ۸۴٫۵؛ SL بالای عدد رند و سقف قبلی بود و TP2 خورد، ولی ریسک ۰٫۵۶ بود و ترید حدود ۳ ساعت طول کشید"},
              {"asset": "US30", "entry": 49123.47, "sl": 49244.99, "tp1": 48880.5, "tp2": 48759.1, "outcome": "SL", "R": -1.0, "note": "داو: حدود +۱٫۳R در ۲٫۵ ساعت اول، TP1 نخورد، بعد از حدود ۸ ساعت برگشت و استاپ خورد؛ ترید خیلی طولانی بود (باید زمان‌بندی ۲ ساعته داشت)"},
              {"asset": "Gold", "entry": 3537.96, "sl": 3568.85, "tp1": 3476.18, "tp2": 3444.79, "outcome": "SL", "R": -1.0, "note": "طلا: ورود SELL دقیقاً روی تارگت ۳R ترید قبلی (۳۵۳۷٫۲۵) بعد از ریزش بلند؛ ریتریس تند و استاپ در حدود ۲ ساعت. درس: دنبال‌کردن حرکت و ورود روی تارگت قبلی"}):
        journal_add({**base, **d, "t": "from-screenshot-v13"})



def _style_form(last=5):
    """فرم اخیر هر سبک: از ۴ ترید به بالا، درصد بردِ ۵ ترید آخرِ همان سبک وزنش را تا -۱۵٪ و +۲۰٪ جابه‌جا می‌کند (سبک داغ، وزن بیشتر)."""
    st = {}
    for x in _jread():
        if x.get("R") is None or not x.get("styles") or str(x.get("source", "")).startswith("seed"): continue
        for s_ in x["styles"]: st.setdefault(s_, []).append(float(x["R"]))
    return {k: 1.0 + float(np.clip((np.mean([r > 0 for r in v[-last:]]) - 0.5) * 0.4, -0.15, 0.2)) for k, v in st.items() if len(v) >= 4}

def chair_board(show=False):
    """جدول رقابت ماهانه: برای هر سبک، تعداد تریدهای مثبتی که آن سبک با آن هم‌جهت بود (ماه جاریِ UTC). رئیس شورا = بیشترین ترید مثبت؛ مساوی = میانگین R بالاتر. اگر این ماه هنوز ترید مثبتی نیست، رئیس ماه قبل می‌ماند."""
    now = utcnow(); ym = f"{now.year}-{now.month:02d}"; py = f"{now.year - 1}-12" if now.month == 1 else f"{now.year}-{now.month - 1:02d}"
    def board(m):
        st = {}
        for x in _jread():
            try:
                if x.get("R") is None or not x.get("styles") or str(x.get("source", "")).startswith("seed") or str(x.get("t", ""))[:7] != m: continue
                for k in x["styles"]:
                    s_ = st.setdefault(k, {"pos": 0, "n": 0, "R": []}); s_["n"] += 1; s_["R"].append(float(x["R"])); s_["pos"] += int(float(x["R"]) > 0)
            except Exception: continue
        return sorted(([k, v["pos"], v["n"], float(np.mean(v["R"]))] for k, v in st.items()), key=lambda r: (-r[1], -r[3], -W0.get(r[0], 1.0)))
    cur, prev = board(ym), board(py)
    lead, label = (cur, ym) if (cur and cur[0][1] >= CHAIR_MIN_POS) else (prev, py) if (prev and prev[0][1] >= CHAIR_MIN_POS) else (cur, ym)
    res = {"ym": label, "rows": lead, "k": lead[0][0] if lead and lead[0][1] >= CHAIR_MIN_POS else None}
    if show:
        if not lead: ui(_note("👑 هنوز هیچ ترید ثبت‌شده‌ای با سبک‌ها نیست؛ بعد از ثبت نتیجه با trade_result جدول رقابت پر می‌شود.", "#d4af37")); return res
        t = pd.DataFrame([{"سبک": f"{_SNAME[k][1]} {_SNAME[k][0]}", "ترید مثبت": p, "کل تریدها": n, "میانگین R": round(r, 2)} for k, p, n, r in lead]).set_index("سبک")
        ui_table(t, f"👑 رقابت رئیس شورا · ماه {label}")
    return res

def _chair_txt():
    c = chair_board()
    if not c["k"]: return "no chair yet (no winning journal trade with a style this month)"
    r = c["rows"][0]; return f"{c['k']} ({_SNAME[c['k']][0]}): {r[1]} winning trades of {r[2]}, avg R {r[3]:+.2f} in {c['ym']}"

def _chair_note():
    c = chair_board()
    if not c["k"]: return f"👑 رئیس شورای {c['ym']} هنوز انتخاب نشده؛ اولین سبکی که با آن ترید مثبت ثبت شود رئیس می‌شود (رأیش {CHAIR_W:g} برابر وزن می‌گیرد)."
    r = c["rows"]; top = r[0]; rest = " · ".join(f"{_SNAME[k][1]}{_SNAME[k][0]} {p}" for k, p, n, _ in r[1:4])
    return f"👑 رئیس شورای {c['ym']}: {_SNAME[top[0]][1]} {_SNAME[top[0]][0]} با {top[1]} ترید مثبت از {top[2]} (میانگین {top[3]:+.2f}R؛ رأیش {CHAIR_W:g}×)" + (f"\nرقبا: {rest}" if rest else "")



_SIGSEEN = set()
def _sigread():
    if not os.path.exists(SIGNALS_PATH): return []
    out = []
    for ln in open(SIGNALS_PATH, encoding="utf-8"):
        try: out.append(json.loads(ln))
        except Exception: pass
    return out

def _siglog_once():
    """هر سیگنالِ نمایش‌داده‌شده یک‌بار در لاگ می‌ماند، تا بعداً بتوان نتیجه را از روی عکس چارت به آن وصل کرد."""
    try:
        x = dict(LAST_SIG); rk = abs(x["entry"] - x["sl"]) or 1.0
        key = (x["asset"], x["side"], str(x["t"])[:13], round(x["entry"] / (0.25 * rk)))
        if key in _SIGSEEN: return
        _SIGSEEN.add(key); x["sid"] = f'{x["asset"]}|{x["side"]}|{x["t"]}'
        with open(SIGNALS_PATH, "a", encoding="utf-8") as fh: fh.write(json.dumps(x, ensure_ascii=False, default=str) + "\n")
    except Exception: pass

def settle(asset, side, outcome, entry=None, note="", variant="safe", hours=48):
    """ثبت نتیجه از روی عکس چارت: سیگنال متناظر (همان دارایی و جهت، تا ۴۸ ساعت قبل؛ با entry نزدیک‌ترین ورود) از لاگ پیدا می‌شود و در ژورنال ثبت می‌شود.
    asset مثل "Gold" یا "USOIL" ؛ side = 1 (BUY) یا -1 (SELL) ؛ outcome = TP2 | TP1+BE | SL | BE ؛ entry به قیمت چارت."""
    side = {"SELL": -1, "SHORT": -1, "BUY": 1, "LONG": 1}.get(str(side).upper(), side)
    now = utcnow(); c = []
    for x in _sigread():
        try:
            if x.get("asset") != asset or x.get("side") != side: continue
            age = (now - pd.Timestamp(x["t"]).tz_localize(None)).total_seconds() / 3600
            if age <= hours: c.append((x, age))
        except Exception: continue
    if not c: print(f"⚠ سیگنالی برای {asset} در {hours} ساعت اخیر در لاگ نیست (لاگ از نسخهٔ v15 شروع می‌شود)؛ ثبت دستی: journal_add({{...}})."); return
    x = min(c, key=lambda z: abs(z[0]["entry"] - entry) if entry is not None else z[1])[0]
    if any(j.get("sid") == x["sid"] and j.get("variant") == variant for j in _jread()): print("ℹ نتیجهٔ این سیگنال قبلاً ثبت شده."); return
    r = {**x, **({"tp1": x.get("rtp1"), "tp2": x.get("rtp2")} if variant == "run" else {}), "variant": variant, "outcome": outcome, "R": (R_OF_RUN if variant == "run" else R_OF).get(outcome), "note": note, "source": "photo", "logged": utcnow().isoformat(timespec="seconds")}
    journal_add(r)


# ================= v9: جهتِ حداقلی، امتیاز و رده‌بندی سیگنال =================
def lean(now):
    """وقتی هم‌جهتی ≥۳ از ۴ نیست: اکثریت تایم‌فریم‌ها؛ اگر مساوی بود جهت ۱۵م+۱س. اگر باز هم صفر بود ۰ (واقعاً جهتی وجود ندارد)."""
    v = int(now.votes); cn = AG.get("council_net") if COUNCIL_ON else None
    if v != 0 and cn is not None and abs(cn) >= COUNCIL_LEAN_NET and (1 if cn > 0 else -1) != (1 if v > 0 else -1) and abs(v) <= 1: return 1 if cn > 0 else -1   # شورا قوی و برخلاف اکثریتِ ضعیف تایم‌فریم‌ها
    if v != 0: return 1 if v > 0 else -1
    if cn is not None and abs(cn) >= COUNCIL_LEAN_NET: return 1 if cn > 0 else -1
    t = int(now.d15m) + int(now.d1h)
    return 1 if t > 0 else -1 if t < 0 else 0

def _tier_stat(tier):
    rows = [x for x in _jread() if x.get("tier") == tier and x.get("R") is not None]
    return (len(rows), float(np.mean([x["R"] > 0 for x in rows])), float(np.mean([x["R"] for x in rows]))) if rows else (0, 0.0, 0.0)

def grade_signal(now, side, plan):
    """امتیاز ۰ تا ۱۰۰ فقط از عوامل قابل‌اندازه‌گیری (نه ادعای مدل دربارهٔ «درصد برد») + رده. هیچ‌چیز سیگنال را حذف نمی‌کند؛ فقط رده و پرچم‌ها را تعیین می‌کند.
    ترکیب امتیاز: درجهٔ مدیر سبد تا ۲۸ | حکم و اطمینان ایجنت ICT تا ۲۲ | هم‌جهتی تایم‌فریم‌ها تا ۲۰ | احتمال TP1 مدیر سبد تا ۱۵ | سوییپ+MSS هم‌جهت ۱۰ | بدون پرچم ۵ | هر پرچم ۶- و هر پرچم سخت ۱۰- (اضافه)"""
    plan = plan or {}; ai = AG.get("smc") or {}; dk = (AG.get("desk") if (DESK_ON and USE_AGENTS) else None) or {}
    al = int(now.votes * side); flags = list(plan.get("flags") or []); hard = list(plan.get("hard") or []); parts = []; sc = 0
    g = str(dk.get("grade", "")).upper(); take = dk.get("decision") == "TAKE"
    if dk: v_ = ({"A": 28, "B": 16, "C": 6}.get(g, 0) if take else 0); sc += v_; parts.append(f"مدیر سبد {dk.get('decision')}/{g}: +{v_}")
    v = ai.get("verdict")
    if ai:
        try: cf = float(ai.get("confidence"))
        except Exception: cf = 0.0
        v_ = (((4 + min(10.0, cf) * 0.4) if v == "GO" else 2 if v == "WAIT" else 0) if ICT_AS_MEMBER else ((12 + min(10.0, cf)) if v == "GO" else 6 if v == "WAIT" else 0)); sc += v_; parts.append(f"ایجنت ICT {v} (اطمینان {cf:g}): +{v_:.0f}")
    v_ = max(0, al) * 5; sc += v_; parts.append(f"هم‌جهتی تایم‌فریم‌ها {al:+d}: +{v_}")
    try: p1 = float(dk.get("p_tp1"))
    except Exception: p1 = None
    if p1 is not None: v_ = max(0.0, min(15.0, (p1 - 40) / 60 * 15)); sc += v_; parts.append(f"احتمال TP1 مدیر سبد {p1:.0f}٪: +{v_:.0f}")
    if plan.get("rev"): sc += 10; parts.append("سوییپ+MSS هم‌جهت: +10")
    if AG["wanted"] and not AG["ok"]: flags.append("تیم عامل‌ها اجرا نشد؛ جهت فقط از اکثریت تایم‌فریم‌هاست")
    if al < MIN_ALIGN: flags.append(f"هم‌جهتی تایم‌فریم‌ها کم است ({al:+d})")
    if not flags: sc += 5
    cp = plan.get("council") or {}; ck = AG.get("ceo") or {}; rr_ = plan.get("rr_room"); sp_ = plan.get("strat") or {}
    if COUNCIL_ON and cp: sc = sc * 0.85 + cp.get("pts", 0.0); parts.append(f"شورای سبک‌ها ({cp.get('nf', 0)} هم‌جهت، توافق {cp.get('agree', 0):.0%}): +{cp.get('pts', 0.0):.0f}")
    try:      # v14: اگر سبکِ رئیس شورا هم‌جهت با ترید است، امتیاز بیشتر
        _ch = chair_board() if (CHAIR_ON and COUNCIL_ON and cp) else {"k": None}
        _row = next((r_ for r_ in cp.get("rows", []) if r_["k"] == _ch["k"]), None) if _ch["k"] else None
        if _row and _row["v"] == side and _row["cf"] >= 0.5: sc += 5; parts.append(f"رئیس شورا ({_row['name']}) هم‌جهت است: +5")
    except Exception: pass
    if STRAT_ON and sp_:      # v15: کیفیت استراتژی در بک‌تست همین سشن (تا ۱۵) + رأی ۱۴ عضو (تا ۵)
        v_ = (0.0 if sp_.get("score") is None else max(0.0, min(15.0, (sp_["score"] + 0.1) / 0.5 * 15.0))) + 5.0 * min(1.0, sp_.get("team", 0.0) * 1.5); sc += v_; parts.append(f"استراتژی «{sp_.get('n')}» (بک‌تست سشن + رأی تیم): +{v_:.0f}")
    sc = max(0.0, min(100.0, sc - 6 * len(flags) - 10 * len(hard)))
    gold = (sc >= GOLD_MIN and not hard and len(flags) <= GOLD_MAX_FLAGS and take and g in ("A", "B") and (v == "GO" or ICT_AS_MEMBER) and al >= max(2, MIN_ALIGN)
            and (not COUNCIL_ON or (cp.get("nf", 0) >= 3 and cp.get("agree", 0.0) >= 0.6))
            and (not STRAT_ON or bool(sp_.get("gold_ok")))
            and (not (CEO_ON and USE_AGENTS) or (ck.get("verdict") == "GO" and ck.get("grade") in ("A", "B")))
            and (rr_ is None or rr_ >= MIN_RR * 0.9))
    risky = bool(hard) or len(flags) >= 2 or sc < STD_MIN or (AG["wanted"] and not AG["ok"]) or (not dk and not ai) or (STRAT_ON and not sp_)
    tier = "GOLD" if gold else "RISKY" if risky else "STANDARD"
    return {"tier": tier, "score": int(round(sc)), "al": al, "flags": flags, "hard": hard, "parts": parts, "cal": _tier_stat(tier), "ceo": ck or None}

_TIER_UI = {"GOLD": ("🥇 GOLD SIGNAL", "linear-gradient(110deg,#7a5c10 0%,#f3d36b 22%,#fff3b0 38%,#d4af37 55%,#fff0a0 72%,#8d6b12 100%)", "#2b1d00", "ستاپ ممتاز: بهترین فرصت‌های این لحظه؛ شورا، مدیرعامل و ساختار هم‌جهت‌اند 🥇"),
            "STANDARD": ("✅ STANDARD SIGNAL", "linear-gradient(110deg,#0b4a30,#1f9d63)", "#ffffff", "ستاپ سالم: نقص جدی ندارد"),
            "RISKY": ("🔥 BOLD SIGNAL · HIGH-RISK", "linear-gradient(110deg,#1e1b4b 0%,#6d28d9 55%,#c026d3 100%)", "#ffffff", "ستاپ جسورانه: ریسکش بالاتر است ولی پتانسیل ۱ به ۳ سر جایش است؛ با حجم هوشمند و SL سرِ جایش وارد شوید 💪")}

def _banner(G, side):
    """بنر رستهٔ ستاپ (فقط یک‌بار بالای سیگنال): رده + امتیاز + دلایل ریسک"""
    t = G["tier"]; name, bg, fg, sub = _TIER_UI[t]; n, wr, ar = G["cal"]; gold = t == "GOLD"
    cal = f"نرخ برد واقعی این رده در ژورنال شما: {wr:.0%} از {n} ترید" if n >= CALIB_MIN else f"نرخ برد واقعی این رده هنوز کالیبره نشده ({n}/{CALIB_MIN} ترید)"
    sh = "box-shadow:0 0 26px rgba(255,205,70,.55),inset 0 0 0 1px rgba(243,211,107,.55);border:2px solid #d4af37;" if gold else ""
    chips = "".join(f"<span class='ta-chip'>🎯 {_h(f)}</span>" for f in G["flags"][:2])
    if gold: bg, fg = "linear-gradient(120deg,#120c02,#2b1d00 50%,#120c02)", "#f3d36b"
    ttl = f"<b class='ta-goldtxt' style='font-size:22px'>{name} · {'BUY' if side == 1 else 'SELL'} {_h(_asset_label())}</b>" if gold else f"<b>{name} · {'BUY' if side == 1 else 'SELL'} {_h(_asset_label())}</b>"
    return (f"<div class='ta-hd' style='background:{bg};color:{fg};{sh}'>{ttl}<small>{sub}</small>"
            f"<div style='margin-top:8px;background:rgba(0,0,0,.25);border-radius:8px;height:9px;overflow:hidden'><div style='width:{G['score']}%;height:100%;background:{'linear-gradient(90deg,#b8860b,#fff3b0,#d4af37)' if gold else '#fff'}'></div></div>"
            f"<div style='font-size:13px;margin-top:4px'>امتیاز {G['score']}/100 (رتبه‌بندی، نه درصد برد) · {cal}</div>"
            + (f"<div style='font-size:13.5px;margin-top:4px'>👔 مدیرعامل: <b>{G['ceo']['verdict']}</b> · درجه {G['ceo']['grade']} · احتمال TP1 ≈ {G['ceo']['p_tp1'] if G['ceo']['p_tp1'] is not None else '؟'}٪ · ریوارد ۱ به {MIN_RR:g}</div>" if G.get("ceo") else f"<div style='font-size:13px;margin-top:4px'>ریوارد ثابت ۱ به {MIN_RR:g}</div>")
            + "</div>")

def _spr(): return float(SPREADS.get(ASSET, 0.0) or 0.0)

# ================= v19: کارت‌های جدید (سبز زمردی) با نماد/اسم ارز، فاصله به پیپ/پوینت، نوار نردبانی و دکمهٔ کپی =================
_CSS += """<style>
.tc{flex:1 1 320px;border-radius:20px;overflow:hidden;border:1px solid rgba(52,211,153,.5);background:linear-gradient(170deg,rgba(16,185,129,.12),rgba(128,128,128,.05));box-shadow:0 8px 26px rgba(0,0,0,.30);position:relative}
.tc.run{border-color:rgba(139,92,246,.55);background:linear-gradient(170deg,rgba(124,77,255,.14),rgba(128,128,128,.05))}
.tc.gold{border:1.5px solid #d4af37;background:linear-gradient(160deg,rgba(212,175,55,.14),rgba(60,40,0,.10));box-shadow:0 0 22px rgba(212,175,55,.40)}
.tc-h{padding:12px 16px;color:#fff;display:flex;align-items:center;gap:8px;flex-wrap:wrap;position:relative;overflow:hidden}
.tc-h::after{content:"";position:absolute;inset:0;background:linear-gradient(100deg,transparent 30%,rgba(255,255,255,.20) 50%,transparent 70%);background-size:200% 100%;animation:taShine 4.5s linear infinite;pointer-events:none}
.tc-t{font-weight:800;font-size:16px;flex:1 1 100%;position:relative;z-index:1}
.tc-pair{background:rgba(0,0,0,.30);border-radius:999px;padding:2px 13px;font-size:14px;direction:ltr;display:inline-flex;gap:7px;align-items:center;position:relative;z-index:1}
.tc-pair i{opacity:.55;font-style:normal}
.tc-dir{border-radius:999px;padding:2px 13px;font-weight:800;font-size:13px;direction:ltr;position:relative;z-index:1;letter-spacing:.3px}
.tc-dir.buy{background:#16a34a;box-shadow:0 0 12px rgba(22,163,74,.6)}.tc-dir.sell{background:#e11d48;box-shadow:0 0 12px rgba(225,29,72,.6)}
.tc-s{padding:8px 16px 2px;font-size:12.5px;opacity:.85}
.tc-r{display:flex;align-items:center;gap:11px;padding:9px 16px;border-top:1px solid rgba(128,128,128,.2)}
.tc-i{width:32px;height:32px;border-radius:10px;display:flex;align-items:center;justify-content:center;font-size:16px;background:rgba(128,128,128,.2);flex:none}
.tc-l{flex:1;font-weight:700}.tc-l small{display:block;opacity:.7;font-weight:400;font-size:11.5px}
.tc-vw{text-align:right}
.tc-v{direction:ltr;font-weight:800;font-size:21px;font-variant-numeric:tabular-nums;white-space:nowrap}
.tc-v .cs{opacity:.6;font-weight:600;font-size:15px;margin-right:3px}.tc-v .un{opacity:.6;font-weight:600;font-size:13px;margin-left:4px}
.tc-d{font-size:11.5px;opacity:.75;direction:ltr}
.tc-cp{cursor:pointer;margin-left:8px;opacity:.5;font-size:14px;user-select:none}.tc-cp:hover{opacity:1}
.tc-r.sl .tc-v{color:#f87171}.tc-r.tp .tc-v{color:#34d399}
.tc-r.sl .tc-i{background:rgba(239,68,68,.24)}.tc-r.tp .tc-i{background:rgba(16,185,129,.26)}.tc-r.en .tc-i{background:rgba(59,130,246,.26)}
.tc-bar{display:flex;margin:10px 16px 4px;border-radius:10px;overflow:hidden;direction:ltr;font-size:11px;font-weight:700;color:#fff}
.tc-bar span{padding:4px 0;text-align:center;white-space:nowrap}
.tc-f{padding:6px 16px 13px;font-size:12.5px;opacity:.92}
</style>"""
ASSET_BADGE = {"EURUSD": ("🇪🇺", "EUR", "🇺🇸", "USD"), "GBPUSD": ("🇬🇧", "GBP", "🇺🇸", "USD"), "Gold": ("🥇", "XAU", "🇺🇸", "USD"), "BTC": ("₿", "BTC", "🇺🇸", "USD"), "ETH": ("Ξ", "ETH", "🇺🇸", "USD"),
               "DOGE": ("Ð", "DOGE", "🇺🇸", "USD"), "SHIB": ("🐕", "SHIB", "🇺🇸", "USD"), "XRP": ("✕", "XRP", "🇺🇸", "USD"), "SOL": ("◎", "SOL", "🇺🇸", "USD"), "BNB": ("🔶", "BNB", "🇺🇸", "USD"), "ADA": ("🔷", "ADA", "🇺🇸", "USD"),
               "TRX": ("🔺", "TRX", "🇺🇸", "USD"), "LINK": ("🔗", "LINK", "🇺🇸", "USD"), "AVAX": ("🔺", "AVAX", "🇺🇸", "USD"),
               "USOIL": ("🛢", "WTI", "🇺🇸", "USD"), "US30": ("🏛", "US30", "", ""), "NAS100": ("💻", "NAS100", "", "")}
PIP = {"EURUSD": 1e-4, "GBPUSD": 1e-4}
def _asset_label():
    b = ASSET_BADGE.get(ASSET)
    return ASSET if not b else (f"{b[1]}/{b[3]} {b[0]}{b[2]}" if b[3] else f"{b[1]} {b[0]}")
def _pair_badge():
    b = ASSET_BADGE.get(ASSET)
    if not b: return f"<span class='tc-pair'>{_h(ASSET)}</span>"
    return f"<span class='tc-pair'><b>{b[0]} {b[1]}</b>" + (f"<i>/</i><b>{b[2]} {b[3]}</b>" if b[3] else "") + "</span>"
def _val_html(x):
    sy = CCY_SYMBOL.get(ASSET, "") if SHOW_SYMBOL else ""; un = PX_UNIT.get(ASSET, "") if SHOW_SYMBOL else ""
    return (f"<span class='cs'>{_h(sy)}</span>" if sy else "") + f"{x:,.{PXD}f}" + (f"<span class='un'>{_h(un)}</span>" if un else "")
def _dist_txt(d, e):
    d = abs(d)
    if ASSET in PIP: t = f"{d / PIP[ASSET]:.1f} pips"
    elif ASSET in ("US30", "NAS100"): t = f"{d:,.1f} pts"
    elif PXD > 2: t = f"{d:.{PXD}f}"
    else: t = f"{CCY_SYMBOL.get(ASSET, '') if SHOW_SYMBOL else ''}{d:,.2f}"
    return f"{t} · {d / max(abs(e), 1e-9) * 100:.2f}%"
def _cp(x):
    return f"<span class='tc-cp' title='کپی' onclick=\"try{{navigator.clipboard.writeText('{x:.{PXD}f}');this.textContent='✓'}}catch(e){{}}\">⧉</span>" if COPY_BTN else ""
def _card(kind, D, e, sl, t1, t2, R1, R2, a, side, frac, extra="", gold=False):
    if kind == "safe": hd, bg, sub, cls = f"🎯 سیگنال اصلی · ریوارد ۱ به {R2:g}", "linear-gradient(115deg,#064e3b,#059669 55%,#34d399)", f"تارگت اول ۱ به {R1:g} (نصف حجم + SL به ورود) و تارگت دوم ۱ به {R2:g}؛ وین‌ریتِ بالاتر از رانر", ""
    else: hd, bg, sub, cls = f"🚀 رانر · ریوارد ۱ به {R2:g}", "linear-gradient(115deg,#312e81,#6d28d9 55%,#a78bfa)", f"همان ورود و همان SL، ولی تارگت‌ها دورترند (۱ به {R1:g} و ۱ به {R2:g}): احتمال رسیدن کمتر، سود بیشتر", " run"
    be = D(e - side * BE_BUFFER_ATR * a); E_ = D(e)
    rows = (("en", "🎯", "ورود (Entry)", "سفارش لیمیت", E_, 0.0), ("sl", "🛑", "حد ضرر (SL)", "= ۱R", D(sl), D(sl) - E_),
            ("tp", "✅", "تارگت ۱", f"۱:{R1:g} · {frac:.0%} حجم", D(t1), D(t1) - E_), ("tp", "🏁", "تارگت ۲", f"۱:{R2:g} · بقیهٔ حجم", D(t2), D(t2) - E_))
    rh = "".join(f"<div class='tc-r {c_}'><div class='tc-i'>{ic}</div><div class='tc-l'>{lb}<small>{sb}</small></div><div class='tc-vw'><div class='tc-v'>{_val_html(v)}{_cp(v)}</div>" + (f"<div class='tc-d'>{_h(_dist_txt(dd, E_))}</div>" if dd else "") + "</div></div>" for c_, ic, lb, sb, v, dd in rows)
    bar = "".join(f"<span style='flex:{w};background:{c_}'>{t_}</span>" for w, c_, t_ in ((1, "#dc2626", "SL −1R"), (0.45, "#64748b", "ENTRY"), (R1, "#16a34a", f"TP1 +{R1:g}R"), (max(R2 - R1, 0.3), "#059669", f"TP2 +{R2:g}R")))
    dr = f"<span class='tc-dir {'buy' if side == 1 else 'sell'}'>{'BUY ▲' if side == 1 else 'SELL ▼'}</span>"
    return (f"<div class='tc{cls}{' gold' if gold else ''}'><div class='tc-h' style='background:{bg}'><div class='tc-t'>{hd}</div>{_pair_badge()}{dr}</div><div class='tc-s'>{sub}</div>{rh}"
            f"<div class='tc-bar'>{bar}</div><div class='tc-f'>بعد از تارگت ۱: {frac:.0%} حجم را ببندید و SL بقیه را ببرید روی <b dir='ltr'>{_val_html(be)}</b>.{extra}</div></div>")

def show_live(now, side, age, seconds, chart=None, rating="", plan=None):
    """بنر رده (یک‌بار) ← نوار وضعیت + دو کارت (هر REFRESH_EVERY ثانیه با قیمت زنده دوباره ساخته می‌شود) ← تحلیل کامل (بازشونده، یک‌بار)."""
    a, off = float(now.atr), PRICE_OFFSET; frac = TP1_FRAC
    cp = CHART_PRICE if chart is None else chart
    if cp is not None: seconds = 0
    if TIERS_ON and plan is None: plan = {"ok": True, "why": "", "lines": [], "entry": None, "sl": None, "opp": None, "size": 1.0, "size_why": [], "flags": [], "hard": [], "rev": False}
    G = grade_signal(now, side, plan) if TIERS_ON else None
    if G: ui(_banner(G, side))
    end, h, folded = time.time() + seconds, None, False
    while True:
        if cp is not None: p, src, lat = float(cp) - off, "قیمت چارت (دستی)", 0.0
        else: p, src, lat = live_price(now.c)
        e20 = float(now.ema20) + (2 / 21) * (p - float(now.ema20))      # EMA20 با کندل در حال تشکیل (همه‌چیز در فضای خود منبع)
        e = float(entry_price(p, e20, a, side))
        if plan and plan.get("entry") is not None: e = float(plan["entry"])        # ناحیهٔ FVG/OB انتخاب‌شده توسط ایجنت
        risk = SL_ATR * a
        if plan and plan.get("sl") is not None: risk = max(risk, side * (e - float(plan["sl"])))   # SL پشت نقدینگی
        if SPREAD_ON and side == -1: risk += _spr()                      # v11.1: SELL با Ask بسته می‌شود؛ اسپرد از جیب ریسک نخورد
        sl = e - side * risk; tp1, tp2 = e + side * SAFE_R1 * risk, e + side * SAFE_R2 * risk; rt1, rt2 = e + side * RUN_R1 * risk, e + side * RUN_R2 * risk
        try: _rs = reach_stats(side, risk) if HORIZON_ON else None
        except Exception: _rs = None
        _rs_line = (f"📊 همین فاصله‌ها در حدود ۳ روز اخیر (ورود فرضی، سقف {MAX_HOLD * 5 / 60:g} ساعت): استاپ {_rs['sl'] * 100:.0f}٪ · به TP1 رسید {_rs['p_tp1'] * 100:.0f}٪ · TP2 {_rs['tp2'] * 100:.0f}٪ · بی‌نتیجه {_rs['none'] * 100:.0f}٪ · میانگین {_rs['avgR']:+.2f}R (فقط راهنما؛ نمونهٔ کوچک)\n") if _rs else ""
        D = lambda x: x + off                                           # افست فقط روی اعداد نمایش داده‌شده اعمال می‌شود
        ts = utcnow() + dt.timedelta(hours=TZ_HOURS); exp = ts + dt.timedelta(minutes=ORDER_TTL * 5)
        remain = end - time.time(); last = remain <= 0
        _ai = AG.get("smc") or {}; _dk = AG.get("desk") or {}
        LAST_SIG.clear(); LAST_SIG.update(asset=ASSET, side=side, t=utcnow().isoformat(timespec="seconds"), entry=round(D(e), PXD), sl=round(D(sl), PXD), tp1=round(D(tp1), PXD), tp2=round(D(tp2), PXD),
            risk_atr=round(risk / a, 2), rating=str(rating), align=int(now.votes * side), agents_ok=bool(AG["ok"]), session=_session(), smc_verdict=_ai.get("verdict"), smc_conf=_ai.get("confidence"),
            smc_confluence=_ai.get("confluence"), smc_schools=_ai.get("schools"), smc_report=_ai.get("report"),
            size=(plan or {}).get("size", 1.0), size_adv=(plan or {}).get("size_adv"), desk_grade=_dk.get("grade"), desk_p_tp1=_dk.get("p_tp1"), mode=MODE,
            tier=(G or {}).get("tier"), score=(G or {}).get("score"), flags=(G or {}).get("flags"), rtp1=round(D(rt1), PXD), rtp2=round(D(rt2), PXD),
            styles=[r_["k"] for r_ in ((plan or {}).get("council") or {}).get("rows", []) if r_["v"] == side], council_agree=round(((plan or {}).get("council") or {}).get("agree", 0.0), 2),
            ceo_verdict=(AG.get("ceo") or {}).get("verdict"), ceo_grade=(AG.get("ceo") or {}).get("grade"), primary_style=(AG.get("ceo") or {}).get("primary"), ceo_p_tp1=(AG.get("ceo") or {}).get("p_tp1"),
            strat=((AG.get("strat_sel") or {}).get("pick") or {}).get("k"), strat_name=((AG.get("strat_sel") or {}).get("pick") or {}).get("n"))
        _siglog_once()
        N = []; Q = []      # N = هشدار ضروری روی کارت | Q = نکته‌های جانبی (فقط داخل بخش بازشونده)
        try: _cr = corr_info(side); _sh = shock_state(); _sig_log(side)
        except Exception: _cr, _sh = {"same": [], "opp": []}, None
        LAST_SIG["corr"] = _cr["same"]
        if _cr["same"]: (N if len(_cr["same"]) >= 2 else Q).append(f"🔗 در {CORR_HOURS} ساعت اخیر روی {'، '.join(_cr['same'])} هم سیگنال هم‌جهت داده شده؛ در روزهای شوک این‌ها عملاً یک شرط‌اند نه چند معاملهٔ مستقل (فقط اطلاع؛ حجم خودکار کم نمی‌شود).")
        if _cr["opp"]: Q.append(f"روی {'، '.join(_cr['opp'])} سیگنال خلاف جهتِ این یکی داده شده؛ یا تناقض بازار یا پوشش ریسک.")
        if _sh: (Q if side == _sh["dir"] else N).append(_shock_txt(_sh) + (" این سیگنال همسو با شوک است؛ در روز روند رانر معمولاً بیشتر می‌ماند، ولی دنبال‌کردنِ حرکتِ انجام‌شده ریسک برگشت دارد." if side == _sh["dir"] else " این سیگنال خلافِ شوک سراسری است؛ احتیاط بیشتر."))
        if now.votes * side <= -3: Q.append("این سیگنال خلاف جهت اکثر تایم‌فریم‌هاست.")
        if plan and plan.get("opp") is not None and side * (plan["opp"] - e) > 0 and side * (plan["opp"] - tp1) < 0: Q.append(f"📍 نقدینگی مقابل در {D(plan['opp']):.{PXD}f} قبل از تارگت ۱ قرار دارد؛ ممکن است قیمت از آنجا واکنش نشان دهد (مدیریت ترید طبق ساختار ثابت می‌ماند).")
        if _rs and _rs["p_tp1"] < 0.25: Q.append(f"با این فاصله‌ها در ۳ روز اخیر فقط {_rs['p_tp1'] * 100:.0f}٪ وقت‌ها قیمت ظرف {MAX_HOLD * 5 / 60:g} ساعت به TP1 رسیده.")
        if _rs and _rs["none"] > 0.5: Q.append(f"در {_rs['none'] * 100:.0f}٪ موارد قیمت ظرف {MAX_HOLD * 5 / 60:g} ساعت نه به استاپ رسیده نه به TP1: بازار کند است.")
        if AG["ok"] and AG["p0"] is not None and (p - AG["p0"]) * side / a <= -DRIFT_WARN_ATR: Q.append("از شروع تحلیل قیمت خلاف جهت سیگنال رفته؛ نظر عامل‌ها ممکن است کهنه باشد.")
        if AG["wanted"] and not AG["ok"]: N.append(f"تیم عامل‌ها اجرا نشد: جهت فقط از هم‌جهتی ۴ تایم‌فریم آمده و تحلیلگرها، مناظره و مدیر سبد نقشی نداشتند. علت: {AG['err'] or 'نامشخص'}")
        if SMC_GATES and not TIERS_ON and risk > M()["risk_hard"] * a + 1e-9: N.append(f"ریسک {risk / a:.2f} ATR از سقف {M()['risk_hard']:g} ATR بیشتر شد؛ سفارش نگذارید.")
        if AG["ok"] and AG["p0"] is not None:
            mv = (p - AG["p0"]) * side / a; mins = (utcnow() - AG["t0"]).total_seconds() / 60
            if mv >= DRIFT_WARN_ATR: N.append(f"از شروع تحلیل ({mins:.0f} دقیقه پیش) قیمت {mv:.1f} ATR در جهت سیگنال رفته؛ بخشی از حرکت انجام شده، دنبالش ندوید.")
        if abs(p - float(now.c)) > 3 * a and "⚠" not in src: N.append("قیمت زنده بیش از ۳ ATR با آخرین کندل فاصله دارد؛ منبع قیمت یا داده را چک کنید.")
        if AG["ok"] and (utcnow() - AG["t"]).total_seconds() / 60 > AGENT_MAX_AGE: N.append(f"جهتِ عامل‌ها {(utcnow() - AG['t']).total_seconds() / 60:.0f} دقیقه پیش تعیین شده؛ اگر بازار عوض شده تحلیل کامل را دوباره اجرا کنید.")
        if "⚠" in src: N.append("قیمت زنده گرفته نشد؛ این عدد قدیمی است. اینترنت/دسترسی صرافی‌ها را چک کنید.")
        live = "⏹ آپدیت زنده تمام شد؛ اگر ثبت سفارش دیرتر از چند ده ثانیه شد، سلول ۲ را دوباره اجرا کنید" if last else f"🔄 آپدیت زنده فعال (هر {REFRESH_EVERY} ثانیه، حدود {remain:.0f} ثانیهٔ دیگر): سفارش را با اعداد همین لحظه ثبت کنید"
        _nb = nobitex_price() if atype == "crypto" else None
        _nb_span = ""
        if _nb is not None:
            _nb_diff = (p - _nb) / _nb * 100 if _nb else 0.0
            _nb_span = f"<span>💹 نوبیتکس (تتر) <b dir='ltr'>{_nb:,.{PXD}f}</b> <small>({'↑' if _nb_diff > 0 else '↓' if _nb_diff < 0 else '='}{abs(_nb_diff):.2f}٪ با منبع)</small></span>"
            if abs(_nb_diff) >= 1.0: Q.append(f"💹 اختلاف قیمت منبع با نوبیتکس حدود {abs(_nb_diff):.1f}٪ است؛ قبل از ثبت سفارش قیمت را از اپ نوبیتکس هم چک کنید.")
        strip = (f"<div class='ta-strip'><span><b>{'🟢 BUY (خرید)' if side == 1 else '🔴 SELL (فروش)'}</b> · {_h(ASSET)} · سفارش لیمیت</span><span>⏱ {ts:%H:%M:%S}</span>"
                 f"<span>💰 قیمت زنده <b dir='ltr'>{D(p):.{PXD}f}</b> <small>({_h(src)} · {lat:.1f}ث)</small></span>{_nb_span}<span>🗳 رأی تیم: {_h(rating)}</span><span>{live}</span></div>")
        px = ""
        if _dk.get("p_tp1") not in (None, "?") and abs(SAFE_R1 - TP1_R) < 1e-9: px = f" برآورد مدیر سبد برای رسیدن به {TP1_R:g}R: حدود {_dk['p_tp1']}٪."
        _g = bool(G and G["tier"] == "GOLD")
        cards = _card("safe", D, e, sl, tp1, tp2, SAFE_R1, SAFE_R2, a, side, frac, px, _g) + (_card("run", D, e, sl, rt1, rt2, RUN_R1, RUN_R2, a, side, frac, "", _g) if RUNNER_ON else "")
        sz = ("💼 حجم: همان حجم معمول شما؛ ربات حجم را خودکار کم نمی‌کند، ریسک‌ها در بنر آمده." + (f" ℹ فقط اطلاع: با این پرچم‌ها سیستم ریسک {plan['size_adv']:.0%} را پیشنهاد می‌کرد؛ تصمیمش با شماست." if plan and plan.get("size_adv") is not None and plan["size_adv"] < 1.0 else "")) if (TIERS_ON and KEEP_SIZE) else (f"💼 حجم پیشنهادی: {plan['size']:.0%} از ریسک معمول‌تان (" + " ، ".join(plan["size_why"]) + ")." if plan and plan["size"] < 1.0 else "💼 حجم پیشنهادی: ۱۰۰٪ ریسک معمول‌تان.")
        mg = (f"📌 ورود {abs(e - p):.{PXD}f} {'پایین‌تر' if side == 1 else 'بالاتر'} از قیمت زنده؛ سفارش لیمیت تا ساعت {exp:%H:%M} معتبر است. اگر تا آن موقع پر نشد، یا قیمت قبل از پر شدن به تارگت ۱ کارت اصلی ({D(tp1):.{PXD}f}) رسید، لغوش کنید.\n"
              f"📏 حد ضرر {risk:.{PXD}f} از ورود = {risk / e * 100:.2f}٪ (همان ۱R)" + (f" · شامل اسپرد {_spr():g}" if (SPREAD_ON and side == -1 and _spr() > 0) else "") + (" — پشت نقدینگی" if plan and plan.get("sl") is not None and risk > SL_ATR * a + 1e-9 else "") + ".\n"
              f"⏳ سقف نگه‌داری {MAX_HOLD * 5 / 60:g} ساعت بعد از فیل‌شدن: اگر تا آن موقع به TP1 نرسید، به قیمت بازار ببندید (اسکلپ؛ تکلیف زود معلوم شود).\n" f"{_rs_line}"
              f"{sz} اگر هر دو کارت را می‌گیرید، ریسک کل دو برابر می‌شود.\n"
              + ((plan.get("rsi_line") + "\n") if plan and plan.get("rsi_line") else "") + ((plan.get("crowd_txt") + "\n") if plan and plan.get("crowd_txt") else "")
              + "🕒 تایم‌فریم‌ها  15m:%+d  30m:%+d  1h:%+d  1d:%+d" % (now.d15m, now.d30m, now.d1h, now.d1d))
        dim = bool(G and G["tier"] == "RISKY" and HIDE_RISKY)
        if dim: N = [f"💪 ستاپ جسورانه: با حجم هوشمند و مدیریت ریسک وارد شوید. کارت‌ها کامل و پررنگ‌اند. {'دلیل: ' + ' | '.join(G['flags'][:2]) if G['flags'] else ''}"] + N
        htm = strip + _news_html(news_guard()) + "".join(_note(n_, "#d99a00") for n_ in N) + f"<div class='ta-flex{' ta-dim' if dim else ''}'>{cards}</div>" + _note(mg, "#2b8fd6")
        o = ui(htm, out=False)
        if h is None: h = display(o, display_id=True)
        else: h.update(o)
        if not folded:
            folded = True
            if plan and ((COUNCIL_ON and plan.get("council")) or STRAT_ON):
                try: _council_panel(plan.get("council"), AG.get("ceo"), side)
                except Exception as _e: print("⚠ پنل شورا نمایش داده نشد:", str(_e)[:150])
            body = "\n".join(list(Q) + ([("🎯 نکات مدیریتی: " + " | ".join(list(G["flags"]) + list(G["hard"])))] if G and (G["flags"] or G["hard"]) else []) + ((plan or {}).get("lines") or []) + ([("تفکیک امتیاز: " + " ، ".join(G["parts"]))] if G else []))
            if body.strip(): ui_fold("🔍 تحلیل کامل میز و نکات مدیریتی (ایجنت ICT/SMC، مدیر سبد، نقدینگی، ساختار)", body)
        if last: break
        time.sleep(REFRESH_EVERY)

AG = {"wanted": False, "err": "", "ok": False, "side": 0, "rating": None, "state": {}, "t": None, "t0": None, "p0": None, "smc": None, "smc_err": "", "smc_tried": False, "smc_t": None, "desk": None, "desk_tried": False, "desk_err": "", "desk_t": None, "debate": None, "override": False, "council": None, "council_llm": None, "council_net": None, "council_err": "", "ceo": None, "ceo_tried": False, "ceo_err": "", "econ": None, "econ_err": ""}   # نتیجهٔ آخرین اجرای موفق عامل‌ها

_OFF_AUTO = [False]
def _auto_basis(chart, now):
    """فقط طلا (منبع زنده ندارد و GC=F فیوچرز است نه اسپات): از قیمت چارتی که می‌دهید اختلاف را حساب و در PRICE_OFFSET نگه می‌دارد تا سطوح ساختاری و ورود/SL هم در فضای چارت شما بیایند. در ترید واقعی این اختلاف حدود ۶٫۵ دلار بود (حدود ۰٫۷ ATR)."""
    global PRICE_OFFSET
    if not (AUTO_BASIS and ASSET in FUT_BASIS and chart is not None): return
    if PRICE_OFFSET != 0 and not _OFF_AUTO[0]: return            # افست دستی شما محترم است
    p, src, _ = live_price(now.c)
    if "⚠" in src or _LAST_LAG[0] > BASIS_MAX_LAG.get(ASSET, 3): print(f"⚠ اختلاف فیوچرز با چارت شما حساب نشد: آخرین معاملهٔ {sym} {'در دسترس نبود' if '⚠' in src else f'{_LAST_LAG[0]:.0f} دقیقه پیش بوده (ساعت کم‌معامله یا تأخیر داده)'}. افست قبلی ({PRICE_OFFSET:+.2f}) می‌ماند؛ اگر لازم شد PRICE_OFFSET را دستی (چارت − فیوچرز) بنویسید."); return
    off = round(float(chart) - p, max(PXD, 2))
    if abs(off) > 0.011 * max(p, 1.0): print(f"⚠ اختلاف {off:+.2f} غیرعادی است؛ اعمال نشد (قیمت چارت را چک کنید)."); return
    PRICE_OFFSET = off; _OFF_AUTO[0] = True; print(f"ℹ اختلاف خودکار چارت شما − منبع داده ({sym}): {off:+.2f}؛ همهٔ اعداد زیر در فضای چارت شما هستند.")

LAST_SIG = {}

def requote(seconds=None, chart=None):
    """بدون اجرای دوبارهٔ عامل‌ها (چند ثانیه): داده و قیمت را تازه می‌کند و ورود/SL/TP را دوباره از روی قیمت زنده می‌سازد.
    chart=عدد → به‌جای قیمت زنده از قیمت چارت خودتان (هر مرجعی) استفاده می‌شود، فقط یک‌بار و فوری."""
    seconds = LIVE_SECONDS if seconds is None else seconds
    now, age = snapshot(max_age=40)
    _auto_basis(CHART_PRICE if chart is None else chart, now)
    if AG["ok"]: side, rating = AG["side"], AG["rating"]
    else:   # عامل‌ها اجرا نشدند/شکست خوردند: جهت = اکثریت تایم‌فریم‌ها
        side = decide(now) or (lean(now) if TIERS_ON else 0); rating = ("Buy" if side == 1 else "Sell" if side == -1 else "Hold") + " (فقط تکنیکال)"
    hdr = f"دارایی: {ASSET} | رأی: {rating}"
    SEL = None
    if STRAT_ON and age <= MAX_AGE_MIN:      # v15: جهت از استراتژیِ فعالِ کتابچه می‌آید
        try:
            SEL = _strat_live(now); _pk = SEL.get("pick")
            if _pk:
                side = _pk["side"]; rating = f"{rating} → {_pk['e']} {_pk['n']}"; hdr = f"دارایی: {ASSET} | رأی: {rating}"
                if AG["ok"]: AG["side"] = side
            elif STRAT_REQUIRED:
                print(hdr); _strat_panel(SEL, 0)
                print("\nهیچ استراتژیِ فعالِ کتابچه‌ای در این لحظه نیست؛ ربات فقط با این استراتژی‌ها ترید می‌دهد، پس سیگنالی صادر نشد." + (" (استراتژی انتخاب‌شدهٔ قبلی دیگر معتبر نیست.)" if SEL.get("pin") else ""))
                print("فهرست «در حال شکل‌گیری» بالا را ببینید؛ بعد از چند دقیقه سلول ۲ را دوباره اجرا کنید یا برای ماندن در سیگنال‌های بدون استراتژی STRAT_REQUIRED=False بگذارید."); return
        except Exception as _ex: print(f"⚠ مرحلهٔ استراتژی خطا داد ({type(_ex).__name__}: {str(_ex)[:120]})؛ با جهت تیم ادامه می‌دهم."); SEL = None
    if age > MAX_AGE_MIN:
        print(hdr)
        print(f"\nداده کهنه است ({age:.0f} دقیقه). احتمالاً بازار بسته است (مثلاً طلا آخر هفته). سیگنال داده نمی‌شود."); return
    if AG["wanted"] and not AG["ok"] and not ALLOW_TECH_FALLBACK and not TIERS_ON:
        print(hdr); print(f"\nتیم عامل‌ها اجرا نشد و ALLOW_TECH_FALLBACK=False است؛ سیگنال داده نمی‌شود.\nعلت: {AG['err'] or 'نامشخص'}"); return
    if side == 0 and TIERS_ON and lean(now) != 0:      # v9: «نگه‌دار» یعنی سیگنال ریسک‌بالا، نه بی‌سیگنال
        side = lean(now)
        if AG["ok"]: AG["side"] = side; AG["override"] = True; rating = f"{rating} → {'Buy' if side == 1 else 'Sell'} (v9: جهت از اکثریت تایم‌فریم‌ها)"; hdr = f"دارایی: {ASSET} | رأی: {rating}"
    if side == 0:
        print(hdr)
        print("\nنتیجه «نگه‌دار» است و تایم‌فریم‌ها هم دقیقاً بین خرید و فروش مساوی‌اند؛ واقعاً هیچ جهتی برای پیشنهاد وجود ندارد (این تنها حالتی است که v9 سیگنال نمی‌دهد). چند دقیقه بعد سلول ۲ را دوباره اجرا کنید.")
        if SHADOW_ON and decide(now) == 0 and now.votes != 0: _shadow("hold", "تیم نگه‌دار گفت و هم‌جهتی کافی نبود", 1 if now.votes > 0 else -1, now)
        return
    cap = None
    if AG["ok"] and now.votes * side < MIN_ALIGN and not TIERS_ON:
        rev = False
        if M()["reversal"]:
            try: _S = smc_engine(DATA[0], DATA[1], float(now.atr), live_price(now.c)[0], side); rev = any(s["bias"] == side and s["mss"] and s["disp"] for s in _S["sweeps"])
            except Exception: pass
        if not rev:
            print(hdr)
            print(f"\nترید داده نمی‌شود: عامل‌ها «{rating}» گفتند ولی تایم‌فریم‌ها هم‌جهت نیستند (امتیاز هم‌جهتی {int(now.votes * side):+d}؛ حداقل {MIN_ALIGN} لازم است). فقط الگوی برگشتی کامل (سوییپ ← دیس‌پلیسمنت ← MSS هم‌جهت) می‌تواند این فیلتر را با نصف حجم رد کند و الان دیده نشد.")
            print("تایم‌فریم‌ها  15m:%+d  30m:%+d  1h:%+d  1d:%+d" % (now.d15m, now.d30m, now.d1h, now.d1d)); _shadow("align", "هم‌جهتی کم", side, now); return
        cap = 0.5
    plan = None
    if SMC_GATES:
        cp = CHART_PRICE if chart is None else chart
        pr = float(cp) - PRICE_OFFSET if cp is not None else live_price(now.c)[0]
        if USE_AGENTS and AG["ok"] and (SMC_AGENT or DESK_ON) and _smc_stale(): desk_prepare(pr)      # حکم SKIP/WAIT یا کهنه دوباره سنجیده می‌شود (ایجنت ICT/SMC + مدیر سبد؛ مناظره دوباره اجرا نمی‌شود)
        plan = smc_plan(now, side, pr)
        if plan["ok"] and cap:
            _w = "تایم‌فریم‌ها هم‌جهت نیستند؛ ورود برگشتی با الگوی کامل سوییپ+دیس‌پلیسمنت+MSS"
            if TIERS_ON and KEEP_SIZE: plan["flags"].append(_w); plan["size_adv"] = min(plan.get("size_adv", 1.0), cap)
            else: plan["size"] = min(plan["size"], cap); plan["size_why"].append(_w)
        if not plan["ok"]:
            _shadow("gate", plan["why"].splitlines()[0] if plan["why"] else "گیت", side, now, pr, plan)
            print(hdr); print("\n" + plan["why"])
            if plan["lines"]: print("\n" + "\n".join(plan["lines"]))
            print("\nسیگنال عمداً داده نشد: این همان فیلتری است که جلوی استاپ‌های بی‌دلیل را می‌گیرد. شرط بالا برقرار شد، سلول ۲ را دوباره اجرا کنید. این رد شدن در ثبت سایه ذخیره شد؛ بعداً shadow_check() نشان می‌دهد اگر داده می‌شد چه می‌شد."); return
    show_live(now, side, age, seconds, chart, rating, plan)

def _cut(s, n):
    s = (s or "").strip()
    return s if len(s) <= n else s[:n] + " …"

def show_details():
    """گزارش‌های تیم عامل‌ها زیر سیگنال، همه بازشونده (پیش‌فرض بسته) تا صفحه شلوغ نشود."""
    st = AG["state"]; deb = st.get("investment_debate_state") or {}
    ui(f"<div class='ta-hd' style='background:linear-gradient(110deg,{_STEPS[3][2]},{_STEPS[3][1]})'><b>📚 گزارش‌های کامل (برای مطالعه)</b><small>هر بخش را با کلیک باز کنید</small></div>")
    ui_fold("🧭 تصمیم نهایی مدیر سبد (تیم عامل‌ها)", _cut(st.get("final_trade_decision"), 3500) or "(خالی)")
    if AG.get("smc"): ui_fold("🧱 ورودی ایجنت ICT/SMC (گزارش موتور ساختار)", AG["smc"]["report"])
    if AG.get("debate"):
        d_ = AG["debate"]; ui_fold("🔧 مناظره: تکنیکال (افتتاحیه)", d_["tact"]); ui_fold("📰 مناظره: بنیادی (افتتاحیه)", d_["fund"])
        for i, (t_, f_) in enumerate(d_["rounds"], 1): ui_fold(f"🔧 تکنیکال، نقد دور {i}", t_); ui_fold(f"📰 بنیادی، نقد دور {i}", f_)
    if not SHOW_DETAILS: return
    parts = [("تحلیلگر بازار/تکنیکال", st.get("market_report"), 1800), ("تحلیلگر احساسات (خبر/توییتر/Reddit)", st.get("sentiment_report"), 1800),
             ("تحلیلگر اخبار", st.get("news_report"), 1800), ("تحلیلگر بنیادی", st.get("fundamentals_report"), 1200),
             ("مباحثهٔ خوش‌بین", deb.get("bull_history"), 1800), ("مباحثهٔ بدبین", deb.get("bear_history"), 1800),
             ("نتیجهٔ مدیر تحقیقات پس از مباحثه", st.get("investment_plan"), 1800), ("پیشنهاد معامله‌گر", st.get("trader_investment_plan"), 1500)]
    for title, txt, n in parts: ui_fold(f"📄 {title}", _cut(txt, n) or "(خالی)")

# ================= ژورنال معاملات (v8): برای اینکه ربات با ترید مثبت و منفی واقعی کالیبره شود =================
R_OF = {"TP2": TP1_FRAC * SAFE_R1 + (1 - TP1_FRAC) * SAFE_R2, "TP1+BE": TP1_FRAC * SAFE_R1, "SL": -1.0, "BE": 0.0, "TIME": 0.0}     # کارت 🎯 اصلی با تقسیم ۵۰/۵۰: TP1=1.5R و TP2=3R؛ نتیجهٔ TP2 برابر 2.25R و TP1+BE برابر 0.75R است
R_OF_RUN = {"TP2": TP1_FRAC * RUN_R1 + (1 - TP1_FRAC) * RUN_R2, "TP1+BE": TP1_FRAC * RUN_R1, "SL": -1.0, "BE": 0.0, "TIME": 0.0}   # کارت رانر: TP2 = ۴R و TP1+BE = ۱٫۵R (با تقسیم ۵۰/۵۰)
def _jread():
    if not os.path.exists(JOURNAL_PATH): return []
    out = []
    for ln in open(JOURNAL_PATH, encoding="utf-8"):
        try: out.append(json.loads(ln))
        except Exception: pass
    return out

def trade_result(outcome, note="", variant="safe"):
    """نتیجهٔ آخرین سیگنالی که نمایش داده شد را ثبت می‌کند. outcome: TP2 | TP1+BE | SL | BE | لغو (سفارش پر نشد). variant: "safe" = کارت 🎯 اصلی | "run" = کارت 🚀 ریوارد بالا. اگر هر دو را گرفتید، برای هرکدام جدا ثبت کنید."""
    if not LAST_SIG: print("هنوز سیگنالی در این نشست نمایش داده نشده؛ ثبت دستی: journal_add({...})."); return
    r = {**LAST_SIG, **({"tp1": LAST_SIG.get("rtp1"), "tp2": LAST_SIG.get("rtp2")} if variant == "run" else {}), "variant": variant, "outcome": outcome, "R": (R_OF_RUN if variant == "run" else R_OF).get(outcome), "note": note, "logged": utcnow().isoformat(timespec="seconds")}
    journal_add(r)

def journal_add(r):
    with open(JOURNAL_PATH, "a", encoding="utf-8") as fh: fh.write(json.dumps(r, ensure_ascii=False, default=str) + "\n")
    print(f"✅ ثبت شد: {r.get('asset')} {'BUY' if r.get('side') == 1 else 'SELL'} → {r.get('outcome')} ({r.get('R')}R) | مسیر ژورنال: {JOURNAL_PATH}")

# ================= ثبت سیگنال‌های ردشده (سایه) تا مشخص شود محافظه‌کاری هزینه داشته یا نه =================
def _sread():
    if not os.path.exists(SHADOW_PATH): return []
    out = []
    for ln in open(SHADOW_PATH, encoding="utf-8"):
        try: out.append(json.loads(ln))
        except Exception: pass
    return out

def _shadow(kind, why, side, now, price=None, plan=None):
    if not SHADOW_ON or side == 0: return
    try:
        a = float(now.atr); p = price if price is not None else live_price(now.c)[0]; e20 = float(now.ema20) + (2 / 21) * (p - float(now.ema20)); e = float(entry_price(p, e20, a, side))
        if plan and plan.get("entry") is not None: e = float(plan["entry"])
        risk = SL_ATR * a
        if plan and plan.get("sl") is not None: risk = max(risk, side * (e - float(plan["sl"])))
        rows = _sread(); last = rows[-1] if rows else None
        if last and last.get("asset") == ASSET and last.get("side") == side and not last.get("done") and (utcnow() - dt.datetime.fromisoformat(last["t"])).total_seconds() < 1200: return    # تکراری نشود
        r = {"t": utcnow().isoformat(timespec="seconds"), "asset": ASSET, "side": side, "kind": kind, "why": str(why)[:220], "entry": round(e, 4), "sl": round(e - side * risk, 4), "tp1": round(e + side * SAFE_R1 * risk, 4),
             "tp2": round(e + side * SAFE_R2 * risk, 4), "atr": round(a, 4), "done": False}
        with open(SHADOW_PATH, "a", encoding="utf-8") as fh: fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    except Exception: pass

def _sim(r, bars):
    """شبیهٔ محافظه‌کارانه: فیل لیمیت تا ORDER_TTL کندل؛ اگر در یک کندل هم SL هم TP لمس شد، SL اول حساب می‌شود. خروجی None = هنوز کندل کافی نیست."""
    s, e, sl, t1, t2 = r["side"], r["entry"], r["sl"], r["tp1"], r["tp2"]; H, L = bars.High.values, bars.Low.values; n = len(bars); fill = None
    for i in range(min(n, ORDER_TTL)):
        if (s == 1 and L[i] <= e) or (s == -1 and H[i] >= e): fill = i; break
        if (s == 1 and H[i] >= t1) or (s == -1 and L[i] <= t1): return "لغو"
    if fill is None: return "لغو" if n >= ORDER_TTL else None
    be = e - s * BE_BUFFER_ATR * r["atr"]; stage = 0; end = min(n, fill + 96)
    for i in range(fill, end):
        stop = sl if stage == 0 else be
        if (s == 1 and L[i] <= stop) or (s == -1 and H[i] >= stop): return "SL" if stage == 0 else "TP1+BE"
        if i == fill: continue
        if stage == 0 and ((s == 1 and H[i] >= t1) or (s == -1 and L[i] <= t1)): stage = 1; continue
        if stage == 1 and ((s == 1 and H[i] >= t2) or (s == -1 and L[i] <= t2)): return "TP2"
    if n >= fill + 96: return "TP1+BE" if stage else "TIME"
    return None

def shadow_check():
    """نتیجهٔ فرضی سیگنال‌های ردشده را با کندل‌های بعدش می‌سنجد: اگر میانگین R مثبت است، آن فیلتر بیش‌ازحد محافظه‌کار بوده."""
    rows = _sread()
    if not rows: print("هنوز سیگنال ردشده‌ای ثبت نشده."); return
    cache = {}; changed = 0
    for r in rows:
        if r.get("done"): continue
        try:
            sy = SYMS[r["asset"]][0]
            if sy not in cache: cache[sy] = load(sy)[0]
            d5_ = cache[sy]; bars = d5_[d5_.index > pd.Timestamp(r["t"])]; o = _sim(r, bars)
            if o: r.update(done=True, outcome=o, R=R_OF.get(o)); changed += 1
        except Exception as e: print("⚠", r.get("asset"), type(e).__name__, str(e)[:100])
    if changed:
        with open(SHADOW_PATH, "w", encoding="utf-8") as fh:
            for r in rows: fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    dn = [r for r in rows if r.get("done") and r.get("R") is not None]; pend = sum(1 for r in rows if not r.get("done"))
    print(f"سیگنال‌های ردشده: {len(rows)} | بررسی‌شده با نتیجه: {len(dn)} | در انتظار کندل کافی: {pend} | لغو (پر نشد): {sum(1 for r in rows if r.get('outcome') == 'لغو')}")
    if not dn: return
    df = pd.DataFrame(dn); print(f"اگر همهٔ این‌ها (با حجم کامل) گرفته می‌شد: جمع {df.R.sum():+.1f}R | میانگین {df.R.mean():+.2f}R | نرخ برد {(df.R > 0).mean():.0%}")
    g = df.groupby("kind").R.agg(["count", "mean", lambda s: (s > 0).mean()]); g.columns = ["تعداد", "میانگین R", "نرخ برد"]; ui_table(g.round(2), "به تفکیک علت رد شدن")
    if len(dn) < 20: print("\n⚠ نمونه هنوز کم است؛ قبل از شل کردن هر فیلتر دست‌کم ۲۰ مورد جمع کنید.")

def journal_seed():
    """چهار ترید نمونه از اسکرین‌شات‌ها (ETH، BTC، طلا ×۲)؛ فقط یک‌بار. نتیجه‌ها «حدس از روی چارت» هستند: قیمت از TP2 هم رد شد، ولی فیل واقعی و مدیریت معامله چک نشده."""
    if any(x.get("source") == "seed" for x in _jread()): print("نمونه‌ها قبلاً ثبت شده‌اند."); return
    base = dict(side=-1, rating="Sell", source="seed", outcome="TP2", R=2.5, agents_ok=True)
    for d in ({"asset": "BTC", "entry": 63730.97, "sl": 63905.05, "tp1": 63382.80, "tp2": 63208.71, "note": "قیمت تا ۶۳۱۲۱ رفت (پایین‌تر از TP2)"},
              {"asset": "ETH", "entry": 1812.68, "sl": 1819.20, "tp1": 1799.64, "tp2": 1793.12, "note": "بعد از TP1 یک V برگشتی تا نزدیک خود ورود آمد؛ SL دقیقاً روی ورود در آستانهٔ استاپ بود. بعدش تا ۱۷۷۹ ریخت"},
              {"asset": "Gold", "entry": 3722.54, "sl": 3731.22, "tp1": 3705.17, "tp2": 3696.48, "note": "فضای قیمت فیوچرز؛ روی چارت اسپات حدود ۶٫۵ پایین‌تر بود. بعدش تا ۳۶۲۵ ریخت"},
              {"asset": "Gold", "entry": 3684.75, "sl": 3695.51, "tp1": 3663.59, "tp2": 3652.49, "note": "حدود ۴٫۵ ساعت تا TP1 (تایم‌استاپ ۳ ساعتهٔ v7 زودتر بسته‌اش می‌کرد)؛ ویک سوییپ به ~۰٫۳R تا SL رسید"}):
        journal_add({**base, **d, "t": "from-screenshot"})

def gold_demo():
    """پیش‌نمایش ظاهر سیگنال 🥇 GOLD با اعداد نمونه (بدون تماس مدل و بدون مصرف سهمیه)."""
    G = {"tier": "GOLD", "score": 86, "al": 4, "flags": [], "hard": [], "parts": [], "cal": (0, 0.0, 0.0), "ceo": {"verdict": "GO", "grade": "A", "p_tp1": 52}}
    side = -1; e, sl = 62272.43, 62575.22; r = abs(sl - e); D = lambda x: x
    ui(_banner(G, side))
    ui(f"<div class='ta-flex'>{_card('safe', D, e, sl, e - 2 * r, e - 3 * r, 2.0, 3.0, 1.0, side, 0.5, '', True)}{_card('run', D, e, sl, e - 3 * r, e - 5 * r, 3.0, 5.0, 1.0, side, 0.5, '', True)}</div>")

AUTOPSY_NOTE = [""]
POSTMORTEM_PROMPT = """You are the CEO of a scalp-trading desk running a blameless post-mortem with your 13 style specialists after a LOSING trade. Goal: find the ROOT CAUSES and turn them into concrete, testable improvements that raise the desk's real win rate. Separate bad PROCESS from bad LUCK: with a 1:3 reward the break-even win rate is only ~25-33%, so a single loss can be normal variance; blame the process only where the facts show a fixable flaw. Be sharp, supportive and specific. Never invent prices; use only the FACTS.

FACTS (computed from the candles by code):
<<FACTS>>

SIGNAL CONTEXT: <<CTX>>
STYLES THAT VOTED WITH THE TRADE: <<STYLES>>
EARLIER LESSONS: <<LESSONS>>

Reply with ONE JSON object only (no markdown): {"root_causes":["<Persian, max 20 words each, at most 3, ordered by importance>"],"fault_by_style":{"<style key>":"<Persian, max 14 words: what that specialist should have caught or must upgrade>"},"rule_changes":["<Persian, max 22 words: a concrete rule that can be tested on the journal>"],"keep_doing":"<Persian, one sentence: what was right in this trade>","coach":"<Persian, one confident, encouraging sentence for the whole team>"}"""

def _autopsy_facts(d5, side, e, sl, tp1, t0, a, look_after=48):
    """بخش قطعی (بدون مدل): فیل، بیشترین سود شناور قبل از استاپ (MFE)، میزان بیرون‌زدن از SL، ادامهٔ حرکت بعد از استاپ و وضعیت بازار قبل از ورود."""
    risk = abs(e - sl); seg = d5[d5.index >= t0 - pd.Timedelta("5min")]; F = {"risk": risk}
    fi = next((i for i in range(len(seg)) if (side == 1 and seg.Low.iloc[i] <= e) or (side == -1 and seg.High.iloc[i] >= e)), None)
    if fi is None: F["filled"] = False; return F
    F["filled"] = True; F["fill_t"] = seg.index[fi]; mfe = 0.0; sl_i = None; tp_i = None
    fav = lambda r_: (r_.High - e) if side == 1 else (e - r_.Low)
    adv = lambda r_: (e - r_.Low) if side == 1 else (r_.High - e)
    for i in range(fi + 1, len(seg)):
        r_ = seg.iloc[i]
        if adv(r_) >= risk: sl_i = i; break
        mfe = max(mfe, fav(r_) / risk)
        if fav(r_) >= abs(tp1 - e): tp_i = i; break
    F["mfe"] = mfe; F["hit_sl"] = sl_i is not None; F["hit_tp1"] = tp_i is not None
    if sl_i is not None:
        r_ = seg.iloc[sl_i]; F["sl_t"] = seg.index[sl_i]; F["bars_to_sl"] = sl_i - fi; F["overshoot_R"] = (adv(r_) - risk) / risk
        aft = seg.iloc[sl_i + 1: sl_i + 1 + look_after]; F["after_bars"] = len(aft)
        F["tp1_after_sl"] = bool(len(aft) and ((aft.Low.min() <= tp1) if side == -1 else (aft.High.max() >= tp1)))
    pre = d5[d5.index < t0].tail(IMPULSE_BARS + 1)
    if len(pre) > 2 and a > 0:
        F["pre_move_atr"] = side * (pre.Close.iloc[-1] - pre.Close.iloc[0]) / a; F["against_atr"] = -F["pre_move_atr"]
        try: F["rsi"] = _rsi(d5[d5.index < t0].Close.values)
        except Exception: pass
    return F

def autopsy(entry=None, sl=None, tp1=None, side=None, since=None):
    """کالبدشکافی آخرین سیگنال بعد از استاپ (یا هر نتیجه): کد حقایق را از روی کندل‌ها درمی‌آورد، بعد مدیرعامل و شورا ریشه‌یابی می‌کنند و درس‌ها در ژورنال می‌روند.
    اگر خودتان عددهای ثبت‌شده را می‌دانید: entry و sl و tp1 را به قیمت چارت بنویسید، side=1 برای BUY و -1 برای SELL، since=«زمان UTC سفارش» مثل '2026-11-20 02:00'."""
    AUTOPSY_NOTE[0] = ""
    s = dict(LAST_SIG) if LAST_SIG else {}
    side = int(side if side is not None else s.get("side", 0))
    if not side or (entry is None and not s): print("⚠ سیگنالی در این نشست نیست؛ entry و sl و tp1 و side را دستی بدهید."); return
    off = PRICE_OFFSET
    e = (entry if entry is not None else s["entry"]) - off; sl_ = (sl if sl is not None else s["sl"]) - off; t1 = (tp1 if tp1 is not None else s["tp1"]) - off
    try: snapshot(); d5 = DATA[0]
    except Exception as ex: print("⚠ دادهٔ تازه گرفته نشد:", str(ex)[:120]); return
    t0 = pd.Timestamp(since) if since else pd.Timestamp(s.get("t") or d5.index[-1])
    a = abs(e - sl_) / float(s.get("risk_atr") or 1.0) if s.get("risk_atr") else float(DATA[0].Close.diff().abs().tail(60).mean() * 3.5)
    F = _autopsy_facts(d5, side, e, sl_, t1, t0, a)
    if not F.get("filled"): ui(_note("ℹ در داده‌های بعد از این زمان، قیمت به نقطهٔ ورود نرسید؛ سفارش پر نشده بود.", "#2b8fd6")); return
    R = F["risk"]; spr = _spr(); L = []; causes = []
    L.append(f"ورود {F['fill_t']:%H:%M} UTC فیل شد. ریسک ۱R = {R:.3f}" + (f" (اسپرد {spr:g} ≈ {spr / R:.0%} از ریسک)" if spr else ""))
    L.append(f"بیشترین سود شناور قبل از پایان ترید: +{F['mfe']:.2f}R")
    if F.get("hit_sl"):
        L.append(f"استاپ بعد از {F['bars_to_sl'] * 5} دقیقه خورد؛ قیمت {F['overshoot_R'] * R:.3f} ({F['overshoot_R']:.2f}R) بیرون از SL رفت")
        if F["overshoot_R"] <= 0.25: causes.append(f"استاپ فقط {F['overshoot_R']:.2f}R بیرون زده شد: بافر پشت نقدینگی/سقف کم بود")
        if F.get("tp1_after_sl"): causes.append("بعد از استاپ، قیمت دوباره به تارگت ۱ رسید: شکار استاپ، نه اشتباه جهت")
        elif F.get("after_bars", 0) >= 6: L.append("بعد از استاپ قیمت به تارگت ۱ نرسید: برگشت واقعی")
    elif F.get("hit_tp1"): L.append("این ترید به تارگت ۱ رسید.")
    if F.get("against_atr") is not None:
        L.append(f"قبل از سفارش: حرکت {IMPULSE_BARS} کندل اخیر {F['pre_move_atr']:+.1f} ATR نسبت به جهت سیگنال" + (f" · RSI {F['rsi']:.0f}" if F.get("rsi") is not None else ""))
        if F["against_atr"] >= IMPULSE_ATR: causes.append(f"سفارش جلوی ایمپالس خلاف جهت ({F['against_atr']:.1f} ATR) گذاشته شده بود")
    if spr and spr / R >= 0.15: causes.append(f"اسپرد {spr / R:.0%} از ریسک را می‌خورد")
    ui(_note("🔬 کالبدشکافی (حقایق از روی کندل‌ها)\n" + "\n".join("• " + x for x in L) + ("\n\nنشانه‌های قطعی:\n" + "\n".join("• " + x for x in causes) if causes else ""), "#c2417a"))
    note = " | ".join(causes[:3]) if causes else "علت قطعی از کندل‌ها پیدا نشد؛ احتمالاً واریانس عادی"
    try:
        ck = AG.get("ceo") or {}; deep, quick = _models()
        ctx = f"asset {ASSET}, side {'LONG' if side == 1 else 'SHORT'}, tier {s.get('tier')}, score {s.get('score')}, CEO {ck.get('verdict')}/{ck.get('grade')} p_tp1={ck.get('p_tp1')}, flags {s.get('flags')}, council agree {s.get('council_agree')}, session {s.get('session')}"
        sty = ", ".join(s.get("styles") or []) or "unknown"
        prompt = POSTMORTEM_PROMPT.replace("<<FACTS>>", "\n".join(L + ["Code-detected causes: " + "; ".join(causes)] )).replace("<<CTX>>", ctx).replace("<<STYLES>>", sty).replace("<<LESSONS>>", _lessons())
        j, _ = _llm_json(prompt, deep)
        rc = [str(x) for x in (j.get("root_causes") or [])][:3]; rl = [str(x) for x in (j.get("rule_changes") or [])][:3]; fb = j.get("fault_by_style") or {}
        body = "🧭 ریشه‌یابی مدیرعامل و شورا\n" + "\n".join("• " + x for x in rc)
        if fb: body += "\n\n🏛 سهم هر عضو برای ارتقا:\n" + "\n".join(f"• {_SNAME[k][1]} {_SNAME[k][0]}: {v}" for k, v in fb.items() if k in _SNAME)
        if rl: body += "\n\n🛠 قانون پیشنهادی برای تست:\n" + "\n".join("• " + x for x in rl)
        if j.get("keep_doing"): body += "\n\n✅ درست بود: " + str(j["keep_doing"])
        if j.get("coach"): body += "\n\n🎓 " + str(j["coach"])
        ui(_note(body, "#7c4dff")); note = (" | ".join(rc[:2]) + (" || قانون: " + rl[0] if rl else ""))[:420] or note
    except Exception as ex: print("⚠ ریشه‌یابی مدلی انجام نشد (حقایق بالا کامل است):", str(ex)[:150])
    AUTOPSY_NOTE[0] = note
    return F

def journal_seed_v11():
    """چهار ترید زندهٔ شب اخیر: سه برد (BTC، ETH، طلا؛ هر سه SELL با ریوارد ۱ به ۳) و یک باخت (نفت، استاپ بعد از +۱٫۳R)؛ فقط یک‌بار. نتیجه از روی چارت است (۲٫۵R مطابق قاعدهٔ کارت اصلی)."""
    if any(x.get("source") == "seed11" for x in _jread()): print("نمونه‌های v11 قبلاً ثبت شده‌اند."); return
    base = dict(side=-1, rating="Sell (owner conviction)", source="seed11", outcome="TP2", R=2.5, agents_ok=True)
    for d in ({"asset": "BTC", "entry": 62272.43, "sl": 62575.22, "tp1": 61666.85, "tp2": 61362.17, "note": "تیم احتمال کم داد ولی مالک ریسک کرد: سوییپ سقف + دیسپلیسمنت، ورود در پریمیوم، به ۳R رسید"},
              {"asset": "ETH", "entry": 1762.67, "sl": 1773.87, "tp1": 1740.27, "tp2": 1729.78, "note": "همان الگو: سوییپ سقف و ریزش؛ ریسک کردن با اعتماد به ساختار جواب داد"},
              {"asset": "Gold", "entry": 3615.35, "sl": 3641.46, "tp1": 3563.13, "tp2": 3537.25, "note": "ریزش قوی ۵م؛ ورود در پریمیوم، SL پشت نقدینگی، ۳R کامل (فضای قیمت اسپات)"},
              {"asset": "USOIL", "entry": 84.210, "sl": 84.483, "tp1": 83.664, "tp2": 83.391, "outcome": "SL", "R": -1.0,
               "note": "باخت نفت: ترید حدود +۱٫۳R (تا ۸۳٫۸۵) به نفع رفت، به ۲R نرسید، بعد ایمپالس صعودی ۵م برگشت و استاپ خورد. SL فقط ۰٫۰۲۵ (حدود ۰٫۰۹R) بیرون زده شد؛ اسپرد ۰٫۰۶ حدود ۲۲٪ ریسک بود. درس: استاپ باید پشت نقاط استاپ عموم (سقف/کف و عدد رند) با بافر کافی باشد، حساب اسپرد، و دقت به ایمپالس خلاف جهت"}):
        journal_add({**base, **d, "t": "from-screenshot-v11"})

def journal_stats():
    rows = [x for x in _jread() if x.get("R") is not None]
    if not rows: print("ژورنال خالی است (یا فقط «لغو»)."); return
    df = pd.DataFrame(rows); n = len(df); w = (df.R > 0).mean()
    print(f"کل: {n} معامله | نرخ برد {w:.0%} | میانگین {df.R.mean():+.2f}R | جمع {df.R.sum():+.1f}R")
    aw, al = df[df.R > 0].R.mean(), -df[df.R < 0].R.mean()
    if aw == aw and al == al and (aw + al) > 0: print(f"میانگین برد {aw:.2f}R | میانگین باخت {al:.2f}R | نرخ برد سربه‌سر ≈ {al / (aw + al):.0%} (هرچه نرخ برد واقعی‌تان بالاتر از این باشد سودده‌اید؛ کارمزد/اسلیپیج را هم حساب کنید)")
    if n < 20: print(f"⚠ فقط {n} معامله؛ هر نتیجه‌ای از این آمار هنوز نویز است (برای قضاوت دربارهٔ یک فیلتر دست‌کم ۲۰–۳۰ معامله لازم است).")
    for col in ("asset", "side", "session", "smc_verdict", "desk_grade", "mode", "align", "tier", "variant", "ceo_grade", "primary_style", "source"):
        if col in df.columns and df[col].notna().any():
            g = df.groupby(col).R.agg(["count", "mean", lambda s: (s > 0).mean()]); g.columns = ["تعداد", "میانگین R", "نرخ برد"]
            ui_table(g.round(2), f"به تفکیک {col}")
    style_stats()


# ================= v14c: اعلان پوش روی گوشی (ntfy) =================
_NTFY = {"err": "", "why": "", "ok": 0, "fail": 0, "last": ""}
def _topic():
    t = (NOTIFY_TOPIC or "").strip(); _NTFY["why"] = ""
    if not t:
        try:
            from google.colab import userdata
            t = (userdata.get("NTFY_TOPIC") or "").strip()
        except Exception as e:
            n_ = type(e).__name__
            _NTFY["why"] = "این Secret در Colab ساخته نشده (نام دقیق: NTFY_TOPIC)" if "NotFound" in n_ else "دسترسی این نوت‌بوک به Secret خاموش است (کلید کنار NTFY_TOPIC را روشن کنید)" if "Access" in n_ else f"خواندن Secret ممکن نشد ({n_})"
            t = ""
    if t and not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", t): _NTFY["why"] = "نام تاپیک فقط حروف انگلیسی، عدد، _ و - باشد (بدون فاصله و فارسی)"; return ""
    return t

def notify(title, msg, prio=3, tags="", delay=None, seq=None):
    """اعلان به گوشی از طریق ntfy.sh. v21: علت شکست ثبت و نمایش داده می‌شود؛ اگر حالت JSON نشد، حالت ساده (با عنوان UTF-8 کدشده) امتحان می‌شود."""
    tp = _topic()
    if not tp: return False
    body = {"topic": tp, "title": title[:120], "message": msg[:1800], "priority": int(prio), "tags": [x for x in tags.split(",") if x]}
    if delay: body["delay"] = delay
    if seq: body["sequence_id"] = seq
    err = ""
    for k in range(3):
        try:
            r = requests.post("https://ntfy.sh/", json=body, timeout=10)
            if r.status_code == 200: _NTFY["ok"] += 1; _NTFY["last"] = utcnow().isoformat(timespec="seconds"); return True
            err = f"HTTP {r.status_code}: {(r.text or '')[:140]}"
            if r.status_code == 429: err += " (سقف پیام روزانهٔ ntfy.sh پر شده؛ فردا یا با سرور شخصی)"; break
        except Exception as e: err = f"{type(e).__name__}: {str(e)[:100]}"
        time.sleep(2 + 3 * k)
    try:      # راه دوم: متن ساده + عنوان MIME/UTF-8
        import base64 as _b64
        h = {"Title": "=?UTF-8?B?" + _b64.b64encode(title[:100].encode("utf-8")).decode() + "?=", "Priority": str(int(prio)), "Tags": tags}
        r = requests.post(f"https://ntfy.sh/{tp}", data=msg[:1800].encode("utf-8"), headers=h, timeout=10)
        if r.status_code == 200: _NTFY["ok"] += 1; _NTFY["last"] = utcnow().isoformat(timespec="seconds"); return True
        err += f" | راه دوم HTTP {r.status_code}"
    except Exception as e: err += f" | راه دوم {type(e).__name__}"
    _NTFY["fail"] += 1; _NTFY["err"] = err; print(f"⚠ اعلان ارسال نشد ({err})"); return False

def notify_test():
    """تست یک‌دستوره: وضعیت تاپیک را می‌گوید و یک اعلان آزمایشی می‌فرستد؛ اگر نرسید دقیقاً می‌گوید کجا گیر کرده."""
    tp = _topic()
    if not tp:
        print("⚠ اعلان خاموش است: " + (_NTFY["why"] or "NTFY_TOPIC خالی است") + ".\nراه‌حل: Colab ← 🔑 Secrets ← Add new secret ← نام: NTFY_TOPIC ← مقدار: یک نام انگلیسیِ خاص (مثلاً ta-k7x92qmf3d) ← کلید «Notebook access» را روشن کنید. بعد در اپ ntfy همان نام را Subscribe کنید."); return False
    ok = notify("✅ تست اعلان", f"اگر این پیام را می‌بینید اعلان کار می‌کند.\nتاپیک: {tp}", 3, "white_check_mark")
    if ok: print(f"✅ پیام آزمایشی به تاپیک «{tp}» ارسال شد. اگر روی گوشی نیامد: ۱) در اپ ntfy دقیقاً همین نام را Subscribe کرده باشید ۲) اگر در ایران هستید، گوشی بدون VPN ممکن است به ntfy.sh نرسد؛ VPN را روشن کنید ۳) اجازهٔ نوتیفیکیشن اپ را بررسی کنید.")
    return ok

# ---- v15b: اعلان ضدّ‌قطعی: (۱) نتیجه فقط یک‌بار و فوراً از یک نخ جدا فرستاده می‌شود (نه بعد از آپدیت‌های زندهٔ صفحه)؛ (۲) هر نوع توقف (حتی Stop/KeyboardInterrupt) اعلان می‌دهد؛
# (۳) «کلید مرگ» زمان‌بندی‌شده روی سرور ntfy: اگر خود Colab کاملاً بمیرد و هیچ کدی اجرا نشود، سرور ntfy خودش بعد از چند دقیقه به شما هشدار می‌دهد ----
_RUN = {"since": "", "sent": False, "done": False, "dm": None}
_RUN_LOCK = threading.Lock()
def _send_once(title, msg, prio=3, tags=""):
    with _RUN_LOCK:
        if _RUN["sent"]: return False
        _RUN["sent"] = True
    ok = notify(title, msg, prio, tags)
    if not ok: _RUN["sent"] = False      # ارسال نشد؛ اجازهٔ تلاش دوباره
    return ok

_HB_LOCK = threading.Lock()
def _hb_post_new():
    import uuid
    seq = "ta-dm-" + uuid.uuid4().hex[:10]
    if notify(f"⚠ اجرای ربات قطع شد · {ASSET}", "بیش از ۶ دقیقه است Colab علامت حیات نداده؛ احتمالاً قفل‌شدن گوشی یا بستن تب جلسه را قطع کرده. Colab را باز کنید؛ اگر ران‌تایم پریده، سلول‌های ۱ و ۲ را دوباره اجرا کنید (کلید را در Secrets بگذارید تا تایپ نخواهد).", 5, "warning", delay="6m", seq=seq): return seq
    return None

def _hb_delete(seq):
    tp = _topic()
    if not seq or not tp: return True
    try: return requests.delete(f"https://ntfy.sh/{tp}/{seq}", timeout=10).status_code in (200, 204)
    except Exception: return False

def _deadman_arm(mins=None):
    """v15c: کلید مرگ چرخان: هر ۶۰ ثانیه هشدار «اجرای ربات قطع شد» روی سرور ntfy با ۴ دقیقه تأخیر دوباره زمان‌بندی می‌شود. تا وقتی ران‌تایم زنده است هیچ‌وقت نمی‌رسد؛ اگر ران‌تایم بمیرد، حداکثر ۴ دقیقه بعد از آخرین علامت حیات به گوشی می‌رسد."""
    if not _topic(): return
    with _HB_LOCK: _RUN["dm"] = _hb_post_new()
    def loop():
        while True:
            time.sleep(150)      # v21: ۶۰←۱۵۰ ثانیه؛ سقف روزانهٔ پیام ntfy.sh (۲۵۰) با کلید مرگ هر دقیقه خیلی زود پر می‌شد و اعلان‌های اصلی ۴۲۹ می‌گرفتند
            with _HB_LOCK:
                if _RUN["done"]: return
                old = _RUN.get("dm"); new = _hb_post_new()
                if new:
                    _RUN["dm"] = new
                    _hb_delete(old)
    threading.Thread(target=loop, daemon=True).start()

def _deadman_cancel():
    with _HB_LOCK:
        seq = _RUN.get("dm"); _RUN["dm"] = None
    if not seq or not _topic(): return
    if not _hb_delete(seq): notify("ℹ هشدار «اجرای ربات قطع شد» را نادیده بگیرید", "تحلیل در واقع تمام شد؛ آن هشدار زمان‌بندی‌شده لغو نشد.", 2, "information_source")

def _sig_watch_start(since, max_min):
    """نخ مستقل: به‌محض ساخته‌شدن سیگنال (قبل از ۳۰ ثانیه آپدیت زنده و قبل از نمایش‌ها) نتیجه را به گوشی می‌فرستد."""
    def loop():
        end = time.time() + max_min * 60
        while time.time() < end and not _RUN["done"] and not _RUN["sent"]:
            try:
                g = dict(LAST_SIG) if LAST_SIG else {}
                if g.get("entry") is not None and g.get("tp1") is not None and str(g.get("t", "")) >= since:
                    time.sleep(1.5); _notify_signal(since, from_watch=True); return
            except Exception: pass
            time.sleep(3)
    threading.Thread(target=loop, daemon=True).start()

_NW = {"on": False, "sent": set()}
def news_watch_start():
    """نخ پس‌زمینه: هر ۶۰ ثانیه تقویم را می‌سنجد و ۳۰ دقیقه و ۵ دقیقه قبل از هر خبر High/Medium اعلان می‌فرستد؛ تا وقتی ران‌تایم Colab زنده است ادامه دارد."""
    if _NW["on"] or not NOTIFY_NEWS or not _topic(): return
    _NW["on"] = True
    def loop():
        while True:
            try:
                g = news_guard()
                for x in (g["near"] if g["ok"] else []):
                    m = x["mins"]
                    for stage, lim in (("30", NEWS_WINDOW_MIN), ("5", 5)):
                        k = (x["title"], x["t"], stage)
                        if 0 < m <= lim and k not in _NW["sent"]:
                            _NW["sent"].add(k)
                            notify(f"⛔ ترید ممنوع · خبر {m:.0f} دقیقهٔ دیگر", f"{x['title']} ({x['ccy']}, {x['impact']}) ساعت {x['tl']:%H:%M} به وقت شما.\nتا {NEWS_AFTER_MIN} دقیقه بعد از انتشار ورود جدید نگذارید و سفارش لیمیت باز را لغو کنید.", 5 if x["impact"] == "High" else 4, "rotating_light" if x["impact"] == "High" else "warning")
            except Exception: pass
            time.sleep(60)
    threading.Thread(target=loop, daemon=True).start()

def _notify_signal(since, from_watch=False):
    """بعد از پایان تحلیل: نتیجه (سیگنال یا نبودنش) را به گوشی می‌فرستد."""
    try:
        g = dict(LAST_SIG) if LAST_SIG else {}
        if g and str(g.get("t", "")) >= since:
            sd = "🟢 BUY (خرید)" if g.get("side") == 1 else "🔴 SELL (فروش)"
            _tier_emo = {"GOLD": "🥇", "STANDARD": "✅", "RISKY": "🔥"}.get(g.get("tier"), "🔷")
            line = "─" * 18
            try: _rrv = f"{abs(float(g['tp2']) - float(g['entry'])) / abs(float(g['entry']) - float(g['sl'])):.1f}".rstrip("0").rstrip(".")
            except Exception: _rrv = "؟"
            msg = (f"{_tier_emo} {_asset_label()}  {sd}\n{line}\n"
                   f"🏅 رده: {g.get('tier') or '-'}   ·   📊 امتیاز: {g.get('score')}/100\n"
                   f"🧭 استراتژی: {g.get('strat_name') or '-'}\n"
                   f"👔 مدیرعامل: {g.get('ceo_verdict') or '-'} {('· درجه ' + str(g.get('ceo_grade'))) if g.get('ceo_grade') else ''}\n{line}\n"
                   f"🎯 ورود: {g.get('entry')}\n🛑 حد ضرر: {g.get('sl')}\n✅ تارگت ۱: {g.get('tp1')}\n🏁 تارگت ۲: {g.get('tp2')}\n{line}\n"
                   f"⚖ ریوارد نهایی: ۱ به {_rrv}\n⏳ سفارش لیمیت تا ۱ ساعت معتبر است؛ بعد از آن لغو کنید. قیمت لحظه‌ای را با چارت خودتان بسنجید.")
            _fl = [str(x_) for x_ in (g.get("flags") or [])][:3]
            if _fl: msg += "\n⚠️ پرچم‌های ریسک: " + " | ".join(_fl)
            if g.get("size_adv") is not None and g["size_adv"] < 1.0: msg += f"\nℹ️ فقط اطلاع: با این پرچم‌ها سیستم ریسک {g['size_adv']:.0%} را پیشنهاد می‌کرد؛ خودکار کم نشد (حجم با خودتان)."
            if g.get("corr"): msg += "\n🔗 هم‌جهت با: " + "، ".join(g["corr"]) + " (عملاً یک شرط بزرگ؛ حجم با خودتان)"
            _sh0 = shock_state()
            if _sh0: msg += "\n" + _shock_txt(_sh0)
            ng = news_guard()
            if ng["ok"] and ng["near"]: msg = f"🚨🚨 خبر نزدیک است ({ng['near'][0]['title']}); ورود نگذارید! 🚨🚨\n" + msg
            _send_once(f"{_tier_emo} سیگنال جدید · {g.get('asset')} · {sd}", msg, 5, "rotating_light" if g.get("tier") == "GOLD" else "chart_with_upwards_trend")
        elif not from_watch: _send_once(f"ℹ تحلیل {ASSET} تمام شد؛ سیگنالی نداد", "ممکن است «نگه‌دار» یا ممنوعیت خبر بوده؛ جزئیات در لاگ.", 3, "information_source")
    except Exception as e: print(f"⚠ اعلان نتیجه ساخته نشد ({type(e).__name__})")

# ================= v19.1: ثبت سیگنال‌ها برای تشخیص هم‌جهتی + تشخیص شوک سراسری =================
SIG_LOG_PATH = JOURNAL_PATH.rsplit(".", 1)[0] + "_signals.jsonl"
_SIG_SEEN = set()
def _sig_log(side):
    k = (ASSET, int(side), int(time.time() // 1200))
    if k in _SIG_SEEN: return
    _SIG_SEEN.add(k)
    try:
        with open(SIG_LOG_PATH, "a", encoding="utf-8") as fh: fh.write(json.dumps({"asset": ASSET, "side": int(side), "t": utcnow().isoformat(timespec="seconds")}) + "\n")
    except Exception: pass
def corr_info(side):
    out = {"same": [], "opp": []}
    if not (CORR_ON and os.path.exists(SIG_LOG_PATH)): return out
    lim = utcnow() - dt.timedelta(hours=CORR_HOURS); last = {}
    for ln in open(SIG_LOG_PATH, encoding="utf-8"):
        try: r = json.loads(ln); t = dt.datetime.fromisoformat(r["t"])
        except Exception: continue
        if r.get("asset") != ASSET and t >= lim and (r["asset"] not in last or t >= last[r["asset"]][0]): last[r["asset"]] = (t, int(r["side"]))
    for a_, (_, sd_) in sorted(last.items()): out["same" if sd_ == side else "opp"].append(a_)
    return out
SHOCK_T = {"BTC": "BTC-USD", "ETH": "ETH-USD", "Gold": "GC=F", "US30": "YM=F", "NAS100": "NQ=F", "USOIL": "CL=F"}
_SHOCK = {"t": 0.0, "v": None}
def shock_state():
    if not SHOCK_ON: return None
    if time.time() - _SHOCK["t"] < 600: return _SHOCK["v"]
    _SHOCK["t"] = time.time(); _SHOCK["v"] = None
    try:
        d = yf.download(list(SHOCK_T.values()), period="5d", interval="1d", progress=False, auto_adjust=True); cl = d["Close"]; ch = {}
        for k, t in SHOCK_T.items():
            x = cl[t].dropna()
            if len(x) >= 2: ch[k] = (float(x.iloc[-1]) / float(x.iloc[-2]) - 1) * 100
        dn = [k for k, v in ch.items() if v <= -SHOCK_PCT]; up = [k for k, v in ch.items() if v >= SHOCK_PCT]
        if len(ch) >= 4 and len(dn) >= SHOCK_MIN: _SHOCK["v"] = {"dir": -1, "assets": dn, "ch": ch}
        elif len(ch) >= 4 and len(up) >= SHOCK_MIN: _SHOCK["v"] = {"dir": 1, "assets": up, "ch": ch}
    except Exception: pass
    return _SHOCK["v"]
def _shock_txt(sh):
    return f"🌐 شوک هم‌زمان بازارها: {len(sh['assets'])} دارایی ({'، '.join(sh['assets'])}) امروز بیش از {SHOCK_PCT:g}٪ {'ریزش' if sh['dir'] == -1 else 'صعود'} کرده‌اند."


# ================= v15: ابزار معاملاتی = ۱۰ استراتژیِ PDF · بک‌تست هر سشن · ۱۴ عضو انتخاب‌گر · آزمون تیم =================
# تغییر نقش: شورا دیگر دربارهٔ «جهت» رأی نمی‌دهد. سیگنال فقط از یک استراتژیِ فعالِ کتابچهٔ ۱۰ استراتژی می‌آید؛ ۱۴ عضو تیم (شامل اقتصاددان و ICT)
# با تجربهٔ خودشان انتخاب می‌کنند «کدام استراتژی به این ستاپ / این نماد / این سشن می‌خورد». قاضیِ آخر بک‌تستِ همین دارایی روی ۲ ماه داده است.
STRATS = {
    "trend": dict(n="روندپیرو (تقاطع میانگین‌ها)", e="📈", run=True, tf="۱۵م",
                  rule="EMA20 از EMA50 به سمت بالا (پایین) عبور کند و ADX≥20 و رو به افزایش باشد → خرید (فروش). مناسب بازارهای روندی؛ وین‌ریت پایین ولی سود بزرگ؛ در رنج ضربه می‌خورد."),
    "meanrev": dict(n="بازگشت به میانگین (بولینگر + RSI)", e="🧲", run=True, tf="۱۵م",
                    rule="کلوز زیر باند پایین بولینگر(۲۰،۲) بود و دوباره به داخل برگشت و RSI در ۳ کندل اخیر زیر ۳۵ رفت (ADX<28) → خرید؛ برعکسش فروش. مناسب رنج؛ وین‌ریت متوسط‌بالا؛ در روند قوی خطرناک."),
    "brk": dict(n="شکست قیمت (کانال دونچین)", e="💥", run=True, tf="۱۵م",
                rule="کلوز بالای سقف ۴۰ کندل قبل (یا زیر کف) با حجم ≥۱٫۲ برابر میانگین (اگر حجم هست) → ورود در جهت شکست. شکست‌های کاذب زیاد؛ ریوارد خوب."),
    "vol": dict(n="شکست نوسان (فشردگی ← انفجار)", e="🌋", run=True, tf="۱۵م",
                rule="پهنای باند بولینگر در ۲۰٪ پایین ۲۰۰ کندل اخیر بوده (فشردگی) و بعد کندلی با رنج ≥۱٫۵ ATR که از باند بیرون بسته شود → ورود هم‌جهت. مناسب شروع حرکات اخبار/سشن."),
    "mom": dict(n="مومنتوم/اسیلاتور (RSI + استوکاستیک)", e="🚀", run=True, tf="۱۵م",
                rule="RSI14 از زیر ۳۰ به بالا (یا از بالای ۷۰ به پایین) برگردد و استوکاستیک ۱۴،۳،۳ هم‌جهت تقاطع کرده باشد → خرید (فروش). وین‌ریت متوسط؛ مناسب بازارهای نوسانی."),
    "scalp": dict(n="اسکالپینگ سریع (EMA5/10 روی ۵م)", e="⚡", run=True, tf="۵م",
                  rule="تقاطع EMA5 و EMA10 روی ۵م + RSI7 هم‌جهت (>۵۵ یا <۴۵) + جهت ۱۵م هم‌سو؛ فقط در سشن‌های پرنقدینگی (لندن و همپوشانی). نیاز به اسپرد کم."),
    "pairs": dict(n="جفت‌معامله / آربیتراژ آماری", e="🔗", run=True, tf="۱۵م",
                  rule="نسبت قیمت دارایی به جفت همبسته‌اش (BTC↔ETH، طلا↔نقره، داو↔نزدک، WTI↔برنت) Z-score ۲۴ ساعته؛ Z>۲ = دارایی گران‌تر شده → فروش؛ Z<−۲ → خرید. (در این ربات فقط پای همین دارایی معامله می‌شود)."),
    "grid": dict(n="گرید", e="🕸", run=False, tf="-",
                 rule="سفارش‌های چندپله‌ای در رنج. با مدیریت ثابت «یک ورود، یک SL، ۱R» سازگار نیست (مارتینگل‌گونه، در روند قوی ضرر انباشته). فقط به‌عنوان نشانهٔ «بازار رنج است» گزارش می‌شود."),
    "carry": dict(n="کری ترید (اختلاف نرخ بهره)", e="🏦", run=False, tf="-",
                  rule="افق هفته/ماه و سود سواپ؛ برای اسکالپ ۱ تا ۲ ساعته ورود نمی‌دهد. اقتصاددان PhD از آن به‌عنوان فیلتر جهت کلان استفاده می‌کند."),
    "ml": dict(n="یادگیری ماشین / کمّی", e="🤖", run=False, tf="-",
               rule="نیاز به داده و آموزش/اعتبارسنجی خارج از این نوت‌بوک و خطر اورفیت دارد. جایگزین عملی: بک‌تستِ زنده و آزمون تیم که هر بار انجام می‌شود."),
}
RUNNABLE = [k for k, v in STRATS.items() if v["run"]]
SESS_FA = {"ASIA": "آسیا", "LONDON": "لندن", "OVERLAP": "همپوشانی لندن/نیویورک", "NY_LATE": "نیویورک عصر", "WKND": "آخر هفته"}
SESS_UTC = {"ASIA": "22–07", "LONDON": "07–12", "OVERLAP": "12–17", "NY_LATE": "17–22", "WKND": "شنبه/یکشنبه"}
SESS_PRIOR = {   # دانش عمومیِ منابع تحقیق (غیرقطعی؛ قاضی بک‌تست است نه این جمله‌ها)
    "ASIA": "range/mean-reversion tends to work; breakouts out of the Asian range are often liquidity grabs; thin liquidity, avoid scalping",
    "LONDON": "highest volume of the day, trends start and ranges break: breakout, volatility-breakout, trend-following; the first push can be a trap, structure matters more than direction",
    "OVERLAP": "deepest liquidity: trend-following, breakout and scalping work best; US data 12:30-13:30 UTC; gold most violent 13:30-15:00 UTC; US index cash open 09:30 NY (opening-range breakout); WTI EIA release Wed 10:30 NY (reaction lasts ~25 min then reverts fast)",
    "NY_LATE": "liquidity thins after London close, follow-through fades, fresh entries have worse odds: mean-reversion at most; avoid rollover 21:55-23:00 UTC",
    "WKND": "crypto only: thin liquidity, spikes revert; mean-reversion",
}
ASSET_PRIOR = {"BTC": "academic work finds negative autocorrelation (mean reversion) of 1-4h returns, stronger after big moves (leverage liquidations)", "ETH": "behaves like BTC (mean reversion of big intraday moves) but with higher beta",
               "Gold": "the overlap window is the prime time for trends; Asian breakouts are mostly liquidity grabs", "US30": "09:30 NY opening-range breakout is the classic index setup; midday NY is choppy",
               "NAS100": "09:30 NY opening-range breakout; most volatile index, tech earnings/AI sentiment", "USOIL": "inventory (EIA Wed) spikes revert quickly; thin outside 07-20 UTC"}

ASSET_PRIOR.update({"SHIB": "meme-coin with tiny unit price: follows DOGE and BTC with extra social-media spikes; moves reverse fast, treat BTC direction as the real driver", "DOGE": "meme-coin beta to BTC with extra spikes on social-media news; moves reverse fast, treat BTC direction as the real driver",
                    "EURUSD": "most liquid pair: trends and breakouts work best in LONDON and OVERLAP (07-17 UTC); Asian session is a range (mean reversion); ECB/Fed/US data spikes fade or extend within minutes",
                    "GBPUSD": "more volatile than EURUSD with London-open stop runs; breakouts and trend in LONDON/OVERLAP; UK data (CPI/jobs) and BoE are the big movers; Asian range often swept at London open"})
def _sess_arr(idx):
    h = np.asarray(idx.hour); wd = np.asarray(idx.dayofweek)
    s = np.where((h >= 7) & (h < 12), "LONDON", np.where((h >= 12) & (h < 17), "OVERLAP", np.where((h >= 17) & (h < 22), "NY_LATE", "ASIA")))
    if atype == "crypto": s = np.where(wd >= 5, "WKND", s)
    return s
def sess_now(): return str(_sess_arr(pd.DatetimeIndex([utcnow()]))[0])

def _adx(h, l, c, n=14):
    up, dn = h.diff(), -l.diff()
    pdm = pd.Series(np.where((up > dn) & (up > 0), up, 0.0), index=h.index); mdm = pd.Series(np.where((dn > up) & (dn > 0), dn, 0.0), index=h.index)
    tr = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1); at = tr.ewm(alpha=1 / n, adjust=False).mean()
    pdi = 100 * pdm.ewm(alpha=1 / n, adjust=False).mean() / at; mdi = 100 * mdm.ewm(alpha=1 / n, adjust=False).mean() / at
    dx = 100 * (pdi - mdi).abs() / (pdi + mdi).replace(0, np.nan)
    return dx.ewm(alpha=1 / n, adjust=False).mean()

def _edge(x):
    x = x.fillna(False).astype(bool); return x & ~x.shift(1, fill_value=False)

def _events_from(sig, av, px, a, cool):
    """سری +1/-1/0 → جدول رویدادها با خنک‌شدن (cool کندل) تا یک حرکتِ واحد چند بار شمرده نشود."""
    v = np.nan_to_num(np.asarray(sig, dtype=float)).astype(int); out = []; last = -10 ** 9
    for i in np.flatnonzero(v):
        if i - last > cool: out.append((av[i], int(v[i]), float(px[i]), float(a[i]))); last = i
    return pd.DataFrame(out, columns=["av", "side", "px", "a"])

def _strat_signals(d5, pair5=None):
    """همهٔ قوانین PDF روی دادهٔ ۵م. خروجی: رویدادها، زمینهٔ هر کندل ۱۵م (برای آزمون) و وضعیتِ «در حال شکل‌گیری» برای کندل آخر."""
    has_v = "Volume" in d5.columns and float(d5["Volume"].sum()) > 0
    agg = dict(OHLC); agg["Volume"] = "sum" if has_v else "last"
    r = d5.resample("15min", label="left", closed="left").agg({k_: v_ for k_, v_ in agg.items() if k_ in d5.columns}).dropna(subset=["Close"])
    if len(r) and r.index[-1] + pd.Timedelta("15min") > d5.index[-1] + pd.Timedelta("5min"): r = r.iloc[:-1]      # کندل ۱۵م ناقص حذف
    if len(r) < 260: raise ValueError("داده کم است (کمتر از ۲۶۰ کندل ۱۵م)")
    c, h, l, o = r.Close, r.High, r.Low, r.Open; a = atr(r); e20, e50 = ema(c, 20), ema(c, 50); adx = _adx(h, l, c); rsi = pd.Series(_rsi_series(c.values, 14), index=r.index)
    mid = c.rolling(20).mean(); sd_ = c.rolling(20).std(ddof=0); up, lo = mid + 2 * sd_, mid - 2 * sd_; bw = (up - lo) / mid
    bwp = bw.rolling(200, min_periods=80).apply(lambda x_: float((x_[:-1] < x_[-1]).mean()), raw=True)
    av = r.index + pd.Timedelta("15min"); S = {}; ARM = {}; z = None
    st = np.sign(e20 - e50); flip = (st != st.shift(1)) & (st != 0) & st.shift(1).notna(); okt = (adx >= 20) & (adx > adx.shift(3))
    S["trend"] = st.where(flip & okt, 0).fillna(0)
    S["meanrev"] = ((c.shift(1) < lo.shift(1)) & (c >= lo) & (rsi.rolling(3).min() < 35) & (adx < 28)).astype(int) - ((c.shift(1) > up.shift(1)) & (c <= up) & (rsi.rolling(3).max() > 65) & (adx < 28)).astype(int)
    hh, ll = h.rolling(40).max().shift(1), l.rolling(40).min().shift(1); vok = (r.Volume > 1.2 * r.Volume.rolling(20).mean()) if has_v else pd.Series(True, index=r.index)
    S["brk"] = ((c > hh + 0.1 * a) & (c.shift(1) <= hh.shift(1)) & vok).astype(int) - ((c < ll - 0.1 * a) & (c.shift(1) >= ll.shift(1)) & vok).astype(int)
    sq = (bwp <= 0.2).astype(float).rolling(8).max().shift(1) > 0; big = (h - l) >= 1.5 * a.shift(1)
    S["vol"] = (sq & big & (c > o) & (c > up.shift(1))).astype(int) - (sq & big & (c < o) & (c < lo.shift(1))).astype(int)
    ll14, hh14 = l.rolling(14).min(), h.rolling(14).max(); K = (100 * (c - ll14) / (hh14 - ll14).replace(0, np.nan)).rolling(3).mean(); Dd = K.rolling(3).mean()
    rU = ((rsi.shift(1) < 30) & (rsi >= 30)).astype(float).rolling(3).max() > 0; rD = ((rsi.shift(1) > 70) & (rsi <= 70)).astype(float).rolling(3).max() > 0
    sU = (K > Dd) & (K.rolling(6).min() < 30); sD = (K < Dd) & (K.rolling(6).max() > 70)
    S["mom"] = _edge(rU & sU).astype(int) - _edge(rD & sD).astype(int)
    if pair5 is not None and len(pair5) > 600:
        pc = pair5.Close.resample("15min", label="left", closed="left").last().reindex(r.index).ffill(limit=3)
        ratio = c / pc; z = (ratio - ratio.rolling(96).mean()) / ratio.rolling(96).std(ddof=0)
        S["pairs"] = _edge(z < -2).astype(int) - _edge(z > 2).astype(int)
    pb = (c - lo) / (up - lo).replace(0, np.nan)
    CTX = pd.DataFrame({"adx": adx, "rsi": rsi, "pb": pb, "bwp": bwp, "d50": (c - e50) / a, "z": z if z is not None else np.nan, "atrp": a / c * 100}, index=av)
    EV = {k_: _events_from(S[k_].values, av, c.values, a.values, 4) for k_ in S}
    c5 = d5.Close; e5, e10 = ema(c5, 5), ema(c5, 10); rs7 = pd.Series(_rsi_series(c5.values, 7), index=d5.index); av5 = d5.index + pd.Timedelta("5min")
    t5 = pd.Series(st.values, index=av).reindex(av5, method="ffill").values; liq = np.isin(_sess_arr(av5), ["LONDON", "OVERLAP"])
    cu, cd = (e5 > e10) & (e5.shift(1) <= e10.shift(1)), (e5 < e10) & (e5.shift(1) >= e10.shift(1))
    sc_ = (cu & (rs7 > 55) & (t5 > 0) & liq).astype(int) - (cd & (rs7 < 45) & (t5 < 0) & liq).astype(int)
    a5 = pd.Series(a.values, index=av).reindex(av5, method="ffill").values; EV["scalp"] = _events_from(sc_.values, av5, c5.values, a5, 6)
    cl, ul, ll_, hh_ = float(c.iloc[-1]), float(up.iloc[-1]), float(lo.iloc[-1]), float(a.iloc[-1])
    if cl < ll_: ARM["meanrev"] = (1, "قیمت زیر باند پایین بولینگر است؛ منتظر بازگشت به داخل باند")
    elif cl > ul: ARM["meanrev"] = (-1, "قیمت بالای باند بالای بولینگر است؛ منتظر بازگشت به داخل باند")
    if float(hh.iloc[-1]) - cl <= 0.3 * hh_ and cl <= float(hh.iloc[-1]): ARM["brk"] = (1, f"نزدیک سقف ۴۰ کندل ({float(hh.iloc[-1]):,.{PXD}f}) است؛ منتظر کلوز بالای آن")
    elif cl - float(ll.iloc[-1]) <= 0.3 * hh_ and cl >= float(ll.iloc[-1]): ARM["brk"] = (-1, f"نزدیک کف ۴۰ کندل ({float(ll.iloc[-1]):,.{PXD}f}) است؛ منتظر کلوز زیر آن")
    if float(bwp.iloc[-1]) <= 0.2: ARM["vol"] = (0, f"فشردگی نوسان (باند تنگ، صدک {float(bwp.iloc[-1]):.0%}); منتظر کندل انفجاری")
    if float(rsi.iloc[-1]) < 35: ARM["mom"] = (1, f"RSI روی {float(rsi.iloc[-1]):.0f} (اشباع فروش)؛ منتظر برگشت از ۳۰")
    elif float(rsi.iloc[-1]) > 65: ARM["mom"] = (-1, f"RSI روی {float(rsi.iloc[-1]):.0f} (اشباع خرید)؛ منتظر برگشت از ۷۰")
    if z is not None and abs(float(z.iloc[-1])) >= 1.5: ARM["pairs"] = (-int(np.sign(float(z.iloc[-1]))), f"Z نسبت جفت {float(z.iloc[-1]):+.1f}؛ منتظر عبور از ±۲")
    meta = {"adx": float(adx.iloc[-1]), "bwp": float(bwp.iloc[-1]), "rsi": float(rsi.iloc[-1]), "z": (float(z.iloc[-1]) if z is not None and z.iloc[-1] == z.iloc[-1] else None), "n15": len(r), "has_vol": has_v}
    return EV, CTX, ARM, meta

# ---------------- بک‌تست ----------------
def _simulate(d5, EV, CTX, sp):
    _rr_reset()
    """Ultimate: هر رویداد با همان هندسهٔ ثابت ربات (SL=SL_ATR×ATR۱۵م، TP1 نصف حجم+BE، TP2، سقف نگه‌داری MAX_HOLD). ورود = سفارش لیمیت MIN_PULL×ATR بهتر از کلوز سیگنال؛ فقط اگر قیمت تا ORDER_TTL کندل به آن برسد پر می‌شود (وگرنه رویداد شمرده نمی‌شود). اگر در کندلِ پرشدن هم SL لمس شده باشد، SL حساب می‌شود (محافظه‌کارانه). اسپرد و کارمزد رفت‌وبرگشت (بر حسب R) کم می‌شود."""
    H, L, C = d5.High.values, d5.Low.values, d5.Close.values; B = MAX_HOLD; T = ORDER_TTL; idx = d5.index; out = {}; fee = float(FEE_RATE.get(ASSET, 0.0) or 0.0)
    for k, ev in EV.items():
        rows = []
        for av_, sd, px, a in ev.itertuples(index=False):
            j = int(idx.searchsorted(av_ - pd.Timedelta("5min")))
            if j + T + B + 2 >= len(C) or not (a == a) or a <= 0: continue
            rk = SL_ATR * a
            if BT_LIMIT_ENTRY:
                e = float(C[j]) - sd * MIN_PULL * a; f = None
                for i_ in range(j + 1, j + 1 + T):
                    if (sd == 1 and L[i_] <= e) or (sd == -1 and H[i_] >= e): f = i_; break
                if f is None: continue
                sl0 = e - sd * rk
                if (sd == 1 and L[f] <= sl0) or (sd == -1 and H[f] >= sl0): o, R = "sl", -1.0
                else: o, R = _sim_geom(H[f + 1:f + 1 + B], L[f + 1:f + 1 + B], C[f + B], e, sd, rk, sp)
            else:
                e = float(C[j]); o, R = _sim_geom(H[j + 1:j + 1 + B], L[j + 1:j + 1 + B], C[j + B], e, sd, rk, sp)
            if fee > 0: R = float(R) - 2 * fee * e / rk
            cx = CTX.reindex([av_], method="ffill").iloc[0] if len(CTX) else None
            rows.append({"t": str(av_), "side": sd, "s": str(_sess_arr(pd.DatetimeIndex([av_]))[0]), "o": o, "R": float(R), "px": float(C[j]),
                         "ctx": ({c_: (round(float(cx[c_]), 3) if cx[c_] == cx[c_] else None) for c_ in ("adx", "rsi", "pb", "bwp", "d50", "z", "atrp")} if cx is not None else {})})
        out[k] = rows
    return out

def _stat(R):
    R = np.asarray(R, dtype=float); n = len(R)
    if n == 0: return {"n": 0, "wr": 0.0, "E": 0.0, "pf": 0.0}
    gp, gl = float(R[R > 0].sum()), float(-R[R < 0].sum())
    return {"n": n, "wr": float((R > 0).mean()), "E": float(R.mean()), "pf": (gp / gl if gl > 0 else (9.99 if gp > 0 else 0.0))}

def _wilson_lb(p, n, z=1.28):
    if n <= 0: return 0.0
    d = 1 + z * z / n; c0 = p + z * z / (2 * n); m = z * np.sqrt(max(p * (1 - p), 0) / n + z * z / (4 * n * n)); return float((c0 - m) / d)

_LAB = {"v": None}
LAB_VER = 3      # Ultimate: نسخهٔ منطق بک‌تست؛ کش قدیمی (ورود با کلوز و بدون کارمزد) خودکار کنار گذاشته می‌شود
def _lab_days(): return STRAT_DAYS_ALL if ALL_MODE else STRAT_DAYS      # حالت ALL بک‌تست کوتاه‌تر
def _min_n(): return STRAT_MIN_N if not ALL_MODE else max(5, int(round(STRAT_MIN_N * STRAT_DAYS_ALL / max(1, STRAT_DAYS))))
def _lab_path(): return JOURNAL_PATH.rsplit(".", 1)[0] + f"_strat_lab_{ASSET}_{_lab_days()}d.json"
def strat_lab(force=False, quiet=False):
    """بک‌تست ۷ استراتژیِ قابل‌اجرا روی ۲ ماه دادهٔ ۵م همین دارایی، به تفکیک سشن. هر ۱۲ ساعت (یا با force) دوباره؛ نتیجه در فایل هم ذخیره می‌شود."""
    L = _LAB["v"]
    if L and not force and L.get("asset") == ASSET and L.get("days") == _lab_days() and L.get("ver") == LAB_VER and (time.time() - L["ts"]) / 3600 < STRAT_LAB_HOURS: return L
    if not force and time.time() - _LAB.get("fail", 0) < 600: return None      # بعد از خطا ۱۰ دقیقه دوباره تلاش نمی‌کند
    if not force and os.path.exists(_lab_path()):
        try:
            L = json.load(open(_lab_path(), encoding="utf-8"))
            if L.get("asset") == ASSET and L.get("days") == _lab_days() and L.get("ver") == LAB_VER and (time.time() - L["ts"]) / 3600 < STRAT_LAB_HOURS: _LAB["v"] = L; return L
        except Exception: pass
    try:
        if not quiet: print(f"آزمایشگاه استراتژی: بک‌تست {len(RUNNABLE)} استراتژی روی {_lab_days()} روز داده‌ٔ ۵م {ASSET} (به تفکیک سشن) ...")
        d5 = _clean(yf.download(sym, start=utcnow() - dt.timedelta(days=_lab_days()), interval="5m", progress=False, auto_adjust=True)).iloc[:-1]
        pair5 = None
        if SMT_PAIR.get(ASSET):
            try: pair5 = _clean(yf.download(SMT_PAIR[ASSET], start=utcnow() - dt.timedelta(days=_lab_days()), interval="5m", progress=False, auto_adjust=True))
            except Exception: pair5 = None
        EV, CTX, _, meta = _strat_signals(d5, pair5); sim = _simulate(d5, EV, CTX, _spr()); st = {}; cases = []
        for k in RUNNABLE:
            rows = sim.get(k, []); rs_ = sorted(rows, key=lambda x_: x_["t"]); cut_ = int(len(rs_) * (1 - OOS_FRAC))
            st[k] = {"all": _stat([x["R"] for x in rows]), "ses": {s_: _stat([x["R"] for x in rows if x["s"] == s_]) for s_ in SESS_FA},
                     "train": _stat([x["R"] for x in rs_[:cut_]]), "oos": _stat([x["R"] for x in rs_[cut_:]])}
            for x in rows: cases.append({**x, "k": k})
        L = {"ver": LAB_VER, "asset": ASSET, "ts": time.time(), "t": utcnow().isoformat(timespec="minutes"), "days": _lab_days(), "bars": len(d5), "stats": st, "cases": cases, "pairs_ok": pair5 is not None and "pairs" in EV and len(EV["pairs"]) > 0}
        _LAB["v"] = L
        try: json.dump(L, open(_lab_path(), "w", encoding="utf-8"), ensure_ascii=False)
        except Exception: pass
        return L
    except Exception as e:
        _LAB["fail"] = time.time(); print(f"⚠ بک‌تست استراتژی‌ها انجام نشد ({type(e).__name__}: {str(e)[:140]}). امتیاز استراتژی‌ها بدون بک‌تست خنثی حساب می‌شود."); return None

def strat_score(L, k, ses):
    """امتیاز استراتژی در سشن فعلی: میانگین R (و حد پایین وین‌ریت) با انقباض به سمت کل داده تا نمونهٔ کم فریب ندهد. None = کم‌نمونه."""
    if not L or k not in L["stats"]: return None
    sa, ss = L["stats"][k]["all"], L["stats"][k]["ses"].get(ses, {"n": 0, "wr": 0.0, "E": 0.0, "pf": 0.0})
    if sa["n"] < _min_n(): return None
    so = L["stats"][k].get("oos") or {"n": 0, "wr": 0.0, "E": 0.0, "pf": 0.0}
    K = STRAT_SHRINK; n = ss["n"]; E = (n * ss["E"] + K * sa["E"]) / (n + K); wr = (n * ss["wr"] + K * sa["wr"]) / (n + K); lb = _wilson_lb(wr, n + K)
    sc = E if STRAT_RANK == "expectancy" else (lb - 0.5) if STRAT_RANK == "winrate" else E + (lb - 0.5)
    return {"E": E, "wr": wr, "lb": lb, "score": float(sc), "n_all": sa["n"], "n_ses": n, "wr_all": sa["wr"], "E_all": sa["E"], "pf_all": sa["pf"], "wr_ses": ss["wr"], "E_ses": ss["E"], "pf_ses": ss["pf"],
            "n_oos": so["n"], "E_oos": so["E"], "wr_oos": so["wr"], "oos_ok": (None if so["n"] < OOS_MIN_N else bool(so["E"] > 0))}

# ---------------- اسکن زنده و انتخاب ----------------
def strat_scan(now, price):
    d5 = DATA[0]; pr = _pair_df() if SMT_PAIR.get(ASSET) else None
    EV, CTX, ARM, meta = _strat_signals(d5, pr); now_av = d5.index[-1] + pd.Timedelta("5min"); a = float(now.atr); ses = sess_now(); rows = []
    for k, v in STRATS.items():
        r_ = {"k": k, "n": v["n"], "e": v["e"], "run": v["run"], "state": "IDLE", "side": 0, "age": None, "detail": "", "px": None}
        if not v["run"]:
            r_["state"] = "INFO"
            if k == "grid": r_["detail"] = ("بازار رنج است (ADX پایین)؛ گرید به‌کار می‌آمد ولی این ربات گرید معامله نمی‌کند." if meta["adx"] < 18 else "بازار رنج نیست؛ گرید خطرناک می‌شد.")
            elif k == "carry": ec = AG.get("econ"); r_["detail"] = ("جهت کلان از نگاه اقتصاددان: " + ("صعودی" if ec["bias"] == 1 else "نزولی" if ec["bias"] == -1 else "خنثی")) if ec else "فیلتر کلان: اقتصاددان اجرا نشده."
            else: r_["detail"] = "جایگزین: بک‌تست زنده و آزمون تیم."
            rows.append(r_); continue
        if k == "pairs" and (k not in EV or pr is None): r_["state"] = "NA"; r_["detail"] = "داده جفت‌ارز در دسترس نیست"; rows.append(r_); continue
        if k == "scalp" and ses not in ("LONDON", "OVERLAP"): r_["state"] = "OFF"; r_["detail"] = "خارج از ساعات پرنقدینگی (فقط لندن و همپوشانی)"; rows.append(r_); continue
        ev = EV.get(k)
        if ev is not None and len(ev):
            x = ev.iloc[-1]; age = (now_av - x["av"]).total_seconds() / 60; fresh = STRAT_FRESH_MIN if k != "scalp" else 20
            if 0 <= age <= fresh + STRAT_PIN_GRACE:
                mv = x["side"] * (price - x["px"]) / max(x["a"], 1e-9); r_.update(side=int(x["side"]), age=age, px=float(x["px"]))
                if mv >= 1.2: r_["state"] = "LATE"; r_["detail"] = f"{age:.0f} دقیقه پیش فعال شد ولی قیمت {mv:.1f} ATR رفته؛ دنبال‌کردن است."
                elif mv <= -SL_ATR: r_["state"] = "BROKEN"; r_["detail"] = f"{age:.0f} دقیقه پیش فعال شد ولی قیمت {abs(mv):.1f} ATR برخلاف رفته؛ ستاپ باطل شد."
                elif age <= fresh: r_["state"] = "ACTIVE"; r_["detail"] = f"{age:.0f} دقیقه پیش فعال شد (قیمت سیگنال {x['px']:,.{PXD}f})."
                else: r_["state"] = "STALE"; r_["detail"] = f"{age:.0f} دقیقه پیش فعال شد؛ کهنه است."
        if r_["state"] == "IDLE" and k in ARM:
            sd, tx = ARM[k]; r_.update(state="ARMING", side=sd, detail=tx)
        if r_["state"] == "IDLE": r_["detail"] = "شرط ورود فعلاً برقرار نیست."
        rows.append(r_)
    return rows, meta

def strat_select(now, price, pin=None):
    L = strat_lab(quiet=True); ses = sess_now(); rows, meta = strat_scan(now, price); dsk = AG.get("strat_desk") or {}; pref = dsk.get("pref", {}); sels = []
    for r in rows:
        r["sc"] = strat_score(L, r["k"], ses) if r["run"] else None; r["team"] = float(pref.get(r["k"], 0.0))
        if r["state"] == "ACTIVE": sels.append(r)
    def key(r): return (0.0 if r["sc"] is None else r["sc"]["score"]) + STRAT_TEAM_W * r["team"]
    sels.sort(key=key, reverse=True); pick = None; stale = False
    if pin:
        pr_ = next((r for r in rows if r["k"] == pin), None)
        if pr_ and pr_["side"] != 0 and pr_["age"] is not None and pr_["state"] in ("ACTIVE", "STALE"): pick = pr_
        elif pr_:
            pick = pr_; stale = True
    if pick is None and sels: pick = sels[0]
    P = None
    if pick:
        sc = pick["sc"]; P = {"k": pick["k"], "n": pick["n"], "e": pick["e"], "side": pick["side"] or 0, "age": pick["age"], "state": pick["state"], "stale": bool(stale or pick["state"] in ("BROKEN", "LATE")), "detail": pick["detail"], "team": pick["team"],
                              "score": None if sc is None else sc["score"], "sc": sc, "gold_ok": bool(sc is not None and sc["score"] >= STRAT_GOLD_SCORE and not stale and pick["state"] == "ACTIVE")}
        if P["side"] == 0: P = None
    alts = [r for r in sels if not P or r["k"] != P["k"]][:2]
    return {"rows": rows, "pick": P, "alts": alts, "session": ses, "meta": meta, "t": utcnow(), "lab": L is not None, "pin": pin}

def _strat_txt():
    S = AG.get("strat_sel")
    if not S: return "not available"
    ses = S["session"]; L = _LAB["v"]; o = [f"session now (UTC): {ses}"]
    P = S.get("pick")
    if P:
        sc = P.get("sc"); o.append(f"SELECTED: {P['k']} ({STRATS[P['k']]['n']}) {'LONG' if P['side'] == 1 else 'SHORT'}, fired {P['age']:.0f} min ago" + (f"; backtest this session n={sc['n_ses']} win-rate {sc['wr_ses']:.0%} expectancy {sc['E_ses']:+.2f}R; all sessions n={sc['n_all']} win-rate {sc['wr_all']:.0%} {sc['E_all']:+.2f}R PF {sc['pf_all']:.2f}; blended score {sc['score']:+.2f}" if sc else "; backtest unavailable or too few trades") + f"; team preference {P['team']:.0%}")
    else: o.append("SELECTED: none (no playbook strategy is active)")
    for r in S["rows"]:
        if r["run"] and r["state"] in ("ACTIVE", "ARMING", "LATE", "BROKEN"): o.append(f"- {r['k']}: {r['state']} {('LONG' if r['side'] == 1 else 'SHORT' if r['side'] == -1 else '')} {r['detail']}")
    return "\n".join(o)

# ---------------- ۱۴ عضو: کدام استراتژی به این ستاپ می‌خورد؟ ----------------
STRAT_PROMPT = """You are the STRATEGY DESK of a professional scalp-trading desk trading <<ASSET>>. 14 specialists (keys listed below, each with a different expertise and experience) must decide WHICH PLAYBOOK STRATEGY fits the current setup, instrument, session and regime. The desk's ONLY trading tools are the playbook strategies below (taken from a research dossier). Nobody votes on direction from gut feeling: the direction is the strategy's own signal.

SESSION NOW (UTC hour buckets: ASIA 22-07, LONDON 07-12, OVERLAP 12-17, NY_LATE 17-22): <<SESSION>>
PLAYBOOK STRATEGIES (rules):
<<RULES>>

SESSION KNOWLEDGE (practitioner sources, NOT proven; the backtest below is the judge):
<<PRIOR>>

LIVE SCAN (evaluated by code on closed candles; states: ACTIVE = fired recently and still valid, ARMING = forming, LATE/BROKEN = missed or invalidated):
<<SCAN>>

BACKTEST of THIS asset on the last <<DAYS>> days of 5m data with the desk's fixed geometry (stop ~<<SL>> ATR, TP1 <<R1>>R half + break-even, TP2 <<R2>>R, max hold 2h; win = R>0). Per strategy: all sessions | current session (n trades, win-rate, expectancy in R):
<<LAB>>

CHIEF ECONOMIST: <<ECON>>
SCHEDULED NEWS: <<NEWS>>
ANALYST TEAM RATING (context only): <<RATING>>
LESSONS: <<LESSONS>>

Rules: pick only strategies that are ACTIVE in the scan (the side must equal the scan's side). A strategy with ARMING state may be named only as "alt". Do NOT pick a strategy whose backtest in the current session is clearly negative unless you can name a concrete reason. If nothing fits, say NONE. Use each specialist's own expertise (e.g. the economist judges macro/event fit, ICT/SMC judges structure and liquidity, the range trader judges mean-reversion fit).
Reply with ONE JSON object only (no markdown): {"members":{"<member key>":{"pick":"<strategy key or NONE>","alt":"<strategy key or empty>","side":"LONG|SHORT|NONE","c":<1-10>,"why":"<Persian, max 22 words, name the concrete trigger and session logic>"}, ... all 14 member keys: <<KEYS>>},"best_fit":"<strategy key or NONE>","session_note":"<Persian, max 35 words: which playbook strategies suit this instrument in this session and why>","teach":"<Persian, one sentence lesson for the whole team>"}"""

def _lab_txt(L, ses):
    if not L: return "(backtest unavailable)"
    o = []
    for k in RUNNABLE:
        s = L["stats"].get(k)
        if not s: continue
        a, c_ = s["all"], s["ses"].get(ses, {"n": 0, "wr": 0, "E": 0})
        o.append(f"{k}: all n={a['n']} wr={a['wr']:.0%} E={a['E']:+.2f}R PF={a['pf']:.2f} | {ses} n={c_['n']} wr={c_['wr']:.0%} E={c_['E']:+.2f}R")
    return "\n".join(o)

def _exam_w(): return (AG.get("strat_exam") or {}).get("w", {})

def strat_desk_prepare(pr=None, force=False):
    """۱۴ عضو، با یک تماس مدل، انتخاب می‌کنند هر استراتژیِ فعال به این ستاپ می‌خورد یا نه. ۲۰ دقیقه کش؛ نتیجه: AG['strat_desk']['pref'] = سهم موافقت وزنی هر استراتژی (۰ تا ۱)."""
    if not (STRAT_ON and STRAT_DESK_LLM and USE_AGENTS and AG["ok"]): return
    D0 = AG.get("strat_desk")
    if D0 and not force and (utcnow() - D0["t"]).total_seconds() / 60 < COUNCIL_REFRESH_MIN: return
    try:
        now, age = snapshot()
        if age > MAX_AGE_MIN: return
        price = pr if pr is not None else live_price(now.c)[0]; AG["strat_desk"] = None; S = strat_select(now, price); AG["strat_sel"] = S; L = _LAB["v"]; ses = S["session"]
        live = [r for r in S["rows"] if r["run"] and r["state"] in ("ACTIVE", "ARMING")]
        if not any(r["state"] == "ACTIVE" for r in live): AG["strat_desk"] = {"t": utcnow(), "members": {}, "pref": {}, "note": "هیچ استراتژی فعال نبود؛ بدون تماس مدل.", "teach": ""}; return
        print("۱۴ عضو تیم در حال انتخاب استراتژیِ مناسب این ستاپ، نماد و سشن‌اند (یک تماس) ...")
        scan = "\n".join(f"- {r['k']}: {r['state']} {('LONG' if r['side'] == 1 else 'SHORT' if r['side'] == -1 else '')} | {r['detail']}" for r in S["rows"] if r["run"])
        rules = "\n".join(f"- {k} ({v['n']}, {v['tf']}): {v['rule']}" for k, v in STRATS.items() if v["run"])
        prior = "\n".join(f"{s_}: {t_}" for s_, t_ in SESS_PRIOR.items()) + f"\nINSTRUMENT: {ASSET_PRIOR.get(ASSET, '')}"
        ec = AG.get("econ"); ect = (f"bias {ec['bias']:+d}, conviction {ec['conv']}/10, event risk {ec['event_risk']}; {ec['intraday']}") if ec else "not available"
        try: nw = _news_txt()
        except Exception: nw = "n/a"
        keys = [k for k, _, _ in STYLES]
        prompt = (STRAT_PROMPT.replace("<<ASSET>>", ASSET_DESC.get(ASSET, ASSET)).replace("<<SESSION>>", ses).replace("<<RULES>>", rules).replace("<<PRIOR>>", prior).replace("<<SCAN>>", scan).replace("<<DAYS>>", str(STRAT_DAYS))
                  .replace("<<SL>>", f"{SL_ATR:g}").replace("<<R1>>", f"{SAFE_R1:g}").replace("<<R2>>", f"{SAFE_R2:g}").replace("<<LAB>>", _lab_txt(L, ses)).replace("<<ECON>>", ect).replace("<<NEWS>>", _cut(nw, 600))
                  .replace("<<RATING>>", str(AG.get("rating"))).replace("<<LESSONS>>", _cut(_lessons(), 700)).replace("<<KEYS>>", ", ".join(keys)))
        deep, quick = _models(); j = None; last = ""
        for k_, model in enumerate((deep, quick)):
            try:
                j, _ = _llm_json(prompt, model)
                if not isinstance(j.get("members"), dict): raise ValueError("members نامعتبر")
                break
            except Exception as e: last = f"{type(e).__name__}: {str(e)[:160]}"; j = None; print(f"⚠ انتخاب استراتژی توسط تیم، تلاش {k_ + 1}: {last}"); time.sleep(4)
        if j is None: AG["strat_desk"] = {"t": utcnow(), "members": {}, "pref": {}, "note": "", "teach": "", "err": last}; return
        sd_of = {r["k"]: r["side"] for r in S["rows"]}; ew = _exam_w(); pref = {}; mem = {}; tot = 0.0
        for k, _, _ in STYLES:
            x = j["members"].get(k) or {}; pk = str(x.get("pick", "NONE")).strip(); alt = str(x.get("alt", "")).strip(); sv = {"LONG": 1, "SHORT": -1}.get(str(x.get("side", "NONE")).upper(), 0)
            try: cf = max(0.0, min(1.0, float(x.get("c", 5)) / 10))
            except Exception: cf = 0.5
            w = W0.get(k, 1.0) * ew.get(k, 1.0); tot += w; mem[k] = {"pick": pk if pk in RUNNABLE else "NONE", "alt": alt if alt in RUNNABLE else "", "side": sv, "c": cf, "why": str(x.get("why") or "")}
            if mem[k]["pick"] != "NONE" and (sv == 0 or sv == sd_of.get(pk)): pref[pk] = pref.get(pk, 0.0) + w * cf
            if mem[k]["alt"] and sd_of.get(alt): pref[alt] = pref.get(alt, 0.0) + 0.5 * w * cf * 0.6
        pref = {k: min(1.0, v / tot) for k, v in pref.items()} if tot else {}
        AG["strat_desk"] = {"t": utcnow(), "members": mem, "pref": pref, "note": str(j.get("session_note") or ""), "teach": str(j.get("teach") or ""), "best": str(j.get("best_fit") or "")}
    except Exception as e: AG["strat_desk"] = {"t": utcnow(), "members": {}, "pref": {}, "note": "", "teach": "", "err": f"{type(e).__name__}: {str(e)[:200]}"}; print("⚠ میز انتخاب استراتژی خطا داد:", AG["strat_desk"]["err"])

# ---------------- آزمون تیم ----------------
EXAM_PATH = JOURNAL_PATH.rsplit(".", 1)[0] + "_exam.jsonl"
EXAM_PROMPT = """EXAM for the 14 specialists of a scalp desk trading <<ASSET>>. Below are <<N>> HISTORICAL setups: at each moment one playbook strategy fired. For each case every specialist must decide TAKE (T) or SKIP (S) using only what is shown (strategy rules, context numbers, session, instrument knowledge). The outcome is hidden; you are graded on the realized result later. Think like an experienced trader: a fired strategy in the wrong session/regime should be skipped.

PLAYBOOK RULES:
<<RULES>>
SESSION KNOWLEDGE: <<PRIOR>>

CASES (adx: trend strength, rsi, pb: position inside the Bollinger band 0=lower 1=upper, bwp: bandwidth percentile 0-1, d50: distance from EMA50 in ATR, z: pair z-score, atr%: 15m ATR as % of price):
<<CASES>>

Reply with ONE JSON object only: {"answers":{"1":{<<KEYS>>}, "2":{...}, ...}} where every inner value is "T" or "S" and the inner objects contain all 14 member keys (<<MEMBERS>>)."""

def strat_exam(force=False, show=True):
    """آزمون: چند موقعیتِ واقعیِ گذشته (استراتژی فعال شده، نتیجه مخفی) به هر ۱۴ عضو داده می‌شود؛ هر کس TAKE/SKIP می‌گوید و با نتیجهٔ واقعی نمره می‌گیرد. وزن اعضا در انتخاب استراتژی به نمرهٔ آزمون وابسته می‌شود."""
    E0 = AG.get("strat_exam")
    if E0 and not force and E0.get("asset") == ASSET and (time.time() - E0["ts"]) / 3600 < EXAM_REFRESH_H: return E0
    L = strat_lab(quiet=True)
    if not L or not L["cases"]: print("⚠ آزمون انجام نشد: بک‌تست در دسترس نیست."); return None
    try:
        cs = sorted(L["cases"], key=lambda x: x["t"]); by = {}
        for x in cs: by.setdefault(x["k"], []).append(x)
        rng = np.random.default_rng(int(time.time() // 86400)); pick = []; keys = [k for k in RUNNABLE if by.get(k)]
        while len(pick) < EXAM_CASES and keys:
            for k in list(keys):
                if not by[k]: keys.remove(k); continue
                x = by[k].pop(int(rng.integers(len(by[k]))));
                if all(abs(pd.Timestamp(x["t"]) - pd.Timestamp(y["t"])) >= pd.Timedelta("3h") for y in pick): pick.append(x)
                if len(pick) >= EXAM_CASES: break
        pick.sort(key=lambda x: x["t"]); n = len(pick)
        if n < 4: print("⚠ آزمون: موقعیت کافی نبود."); return None
        print(f"آزمون تیم: {n} موقعیت واقعیِ گذشته به ۱۴ عضو داده شد (نتیجه مخفی) ...")
        def cl(x):
            c_ = x["ctx"]; return ", ".join(f"{a_}={c_.get(a_)}" for a_ in ("adx", "rsi", "pb", "bwp", "d50", "z", "atrp") if c_.get(a_) is not None)
        cases = "\n".join(f"{i + 1}) {x['t'][:16]} UTC, session {x['s']}: {x['k']} fired {'LONG' if x['side'] == 1 else 'SHORT'} | {cl(x)}" for i, x in enumerate(pick))
        mk = [k for k, _, _ in STYLES]
        prompt = (EXAM_PROMPT.replace("<<ASSET>>", ASSET_DESC.get(ASSET, ASSET)).replace("<<N>>", str(n)).replace("<<RULES>>", "\n".join(f"- {k}: {v['rule']}" for k, v in STRATS.items() if v["run"]))
                  .replace("<<PRIOR>>", " | ".join(f"{s_}: {t_}" for s_, t_ in SESS_PRIOR.items()) + f" | {ASSET_PRIOR.get(ASSET, '')}").replace("<<CASES>>", cases).replace("<<KEYS>>", ", ".join(f'"{k}":"T|S"' for k in mk[:3]) + ", ...").replace("<<MEMBERS>>", ", ".join(mk)))
        deep, quick = _models(); j = None; last = ""
        for k_, model in enumerate((deep, quick)):
            try:
                j, _ = _llm_json(prompt, model)
                if not isinstance(j.get("answers"), dict): raise ValueError("answers نامعتبر")
                break
            except Exception as e: last = f"{type(e).__name__}: {str(e)[:160]}"; j = None; time.sleep(4)
        if j is None: print(f"⚠ آزمون انجام نشد: {last}"); return None
        Rs = np.array([x["R"] for x in pick]); base = float(Rs.mean()); rows = []; skill = {}
        for k in mk:
            tk = [i for i in range(n) if str((j["answers"].get(str(i + 1)) or {}).get(k, "S")).upper().startswith("T")]
            sR = float(sum(Rs[i] for i in tk)); sk = sR - len(tk) * base; skill[k] = sk
            rows.append({"k": k, "name": _SNAME[k][0], "emo": _SNAME[k][1], "takes": len(tk), "wins": int(sum(Rs[i] > 0 for i in tk)), "R": sR, "skill": sk})
        order = sorted(mk, key=lambda k: -skill[k]); w = {k: round(1.25 - 0.5 * i / (len(mk) - 1), 3) for i, k in enumerate(order)}
        cons = [i for i in range(n) if sum(str((j["answers"].get(str(i + 1)) or {}).get(k, "S")).upper().startswith("T") for k in mk) > len(mk) / 2]
        E = {"asset": ASSET, "ts": time.time(), "t": utcnow().isoformat(timespec="minutes"), "n": n, "base": base, "take_all_R": float(Rs.sum()), "cons_takes": len(cons), "cons_R": float(sum(Rs[i] for i in cons)), "rows": rows, "w": w}
        AG["strat_exam"] = E
        try:
            with open(EXAM_PATH, "a", encoding="utf-8") as fh: fh.write(json.dumps({k: v for k, v in E.items() if k != "rows"}, ensure_ascii=False) + "\n")
        except Exception: pass
        if show: _exam_panel(E)
        return E
    except Exception as e: print(f"⚠ آزمون خطا داد: {type(e).__name__}: {str(e)[:160]}"); return None

def _exam_panel(E):
    df = pd.DataFrame([{"عضو": f"{r['emo']} {r['name']}", "TAKE": r["takes"], "برنده": r["wins"], "جمع R": f"{r['R']:+.1f}", "ارزش افزوده نسبت به «همه را بگیر»": f"{r['skill']:+.1f}", "وزن بعدی": f"{E['w'][r['k']]:.2f}"} for r in sorted(E["rows"], key=lambda r: -r["skill"])]).set_index("عضو")
    ui_table(df, f"📝 آزمون تیم: {E['n']} موقعیت واقعی {ASSET} (نتیجه مخفی). «همه را بگیر» = {E['take_all_R']:+.1f}R | رأی اکثریتِ تیم: {E['cons_takes']} TAKE = {E['cons_R']:+.1f}R")
    ui(_note("نمونهٔ آزمون کوچک است، پس وزن اعضا فقط بین ۰٫۷۵ تا ۱٫۲۵ جابه‌جا می‌شود؛ نتیجه هر ۱۲ ساعت دوباره گرفته می‌شود. «ارزش افزوده» = جمع R تصمیم‌های TAKE منهای (تعداد TAKE × میانگین R همهٔ موقعیت‌ها).", "#7c4dff"))

# ---------------- نمایش ----------------
_SFA = {"ACTIVE": "فعال ✅", "LATE": "دیر شد", "BROKEN": "باطل شد", "STALE": "کهنه", "ARMING": "در حال شکل‌گیری", "IDLE": "منتظر", "INFO": "اطلاعاتی", "OFF": "خارج از ساعت", "NA": "ناموجود"}
def _strat_panel(S, side=0):
    if not S: return
    L = _LAB["v"]; ses = S["session"]; P = S.get("pick"); tiles = ""
    for r in S["rows"]:
        col = ("#30a46c" if r["side"] == 1 else "#e5484d") if r["state"] == "ACTIVE" else "#d99a00" if r["state"] in ("ARMING", "LATE") else "#2b8fd6" if r["state"] == "INFO" else "#8a8f98"
        sd = {1: " ▲ خرید", -1: " ▼ فروش"}.get(r["side"], ""); st = ""
        if r["run"] and L and r["k"] in L["stats"]:
            a_, s_ = L["stats"][r["k"]]["all"], L["stats"][r["k"]]["ses"].get(ses, {"n": 0, "wr": 0, "E": 0})
            st = f"<div class='tw'>سشن: n={s_['n']} · وین {s_['wr']:.0%} · {s_['E']:+.2f}R<br>کل: n={a_['n']} · وین {a_['wr']:.0%} · {a_['E']:+.2f}R</div>"
        tm = f"<div class='tw'>رأی تیم {r['team']:.0%}</div>" if r.get("team") else ""
        tiles += f"<div class='ta-tile' style='--c:{col}' title='{_h(STRATS[r['k']]['rule'])}'><div class='te'>{r['e']}</div><div class='tn'>{_h(r['n'])}</div><div class='tv'>{_SFA.get(r['state'], r['state'])}{sd}</div>{st}{tm}<div class='ty'>{_h(r['detail'])}</div></div>"
    if P:
        sc = P.get("sc"); sdn = "BUY 🟢" if P["side"] == 1 else "SELL 🔴"
        stat = (f"<span class='ta-chip'>سشن {SESS_FA.get(ses, ses)}: n={sc['n_ses']} · وین‌ریت {sc['wr_ses']:.0%} · میانگین {sc['E_ses']:+.2f}R</span><span class='ta-chip'>۲ ماه: n={sc['n_all']} · وین {sc['wr_all']:.0%} · {sc['E_all']:+.2f}R · PF {sc['pf_all']:.2f}</span><span class='ta-chip'>امتیاز {sc['score']:+.2f}</span>" if sc else "<span class='ta-chip'>بک‌تست در دسترس نیست یا کم‌نمونه</span>")
        hd = (f"<div class='ta-ceo' style='background:linear-gradient(120deg,#0e2a47,#1d5f8a 60%,#0f7a5a)'><b class='t'>🛠 استراتژی انتخاب‌شده: {P['e']} {_h(P['n'])} · {sdn}</b>{'<span class=ta-chip>⚠ دیگر معتبر نیست</span>' if P.get('stale') else ''}"
              f"<div class='sub'>{_h(P['detail'])}</div><div style='margin-top:6px'>{stat}<span class='ta-chip'>رأی تیم {P['team']:.0%}</span><span class='ta-chip'>سشن: {SESS_FA.get(ses, ses)} ({SESS_UTC.get(ses, '')} UTC)</span></div></div>")
    else: hd = f"<div class='ta-ceo' style='background:linear-gradient(120deg,#2b2b33,#4a4a55)'><b class='t'>🛠 هیچ استراتژی فعالی نیست</b><div class='sub'>سشن {SESS_FA.get(ses, ses)}؛ ربات فقط با استراتژی‌های کتابچه ترید می‌دهد. فهرست پایین نشان می‌دهد کدام‌ها در حال شکل‌گیری‌اند.</div></div>"
    ui(hd + "<div style='font-weight:800;margin:10px 0 2px'>📚 ۱۰ استراتژی کتابچه · وضعیت لحظه‌ای</div><div class='ta-grid'>" + tiles + "</div>")
    D = AG.get("strat_desk") or {}
    if D.get("members"):
        txt = "\n".join(f"{_SNAME[k][1]} {_SNAME[k][0]}: " + (f"{STRATS[m['pick']]['e']} {STRATS[m['pick']]['n']}" + (f" (+ جایگزین {STRATS[m['alt']]['n']})" if m["alt"] else "") + f" · {m['c'] * 100:.0f}٪ — {m['why']}" if m["pick"] != "NONE" else "هیچ‌کدام — " + m["why"]) for k, m in D["members"].items())
        ui_fold("👥 انتخابِ هر عضو تیم: کدام استراتژی به این ستاپ می‌خورد؟", (D.get("note") and ("🕒 " + D["note"] + "\n\n") or "") + txt + (("\n\n🎓 درس: " + D["teach"]) if D.get("teach") else ""))
    elif D.get("note"): ui(_note(D["note"], "#8a8f98"))

def _oos_txt(s):
    o = s.get("oos") or {"n": 0}
    return f"n={o['n']} · {o['wr']:.0%} · {o['E']:+.2f}R" if o.get("n") else "—"

def strat_board():
    """جدول کامل بک‌تست: هر استراتژی × هر سشن (n / وین‌ریت / میانگین R)."""
    L = strat_lab(force=False)
    if not L: return
    cols = list(SESS_FA); rows = {}
    for k in RUNNABLE:
        s = L["stats"][k]; rows[f"{STRATS[k]['e']} {STRATS[k]['n']}"] = [f"n={s['all']['n']} · {s['all']['wr']:.0%} · {s['all']['E']:+.2f}R", _oos_txt(s)] + [(f"n={s['ses'][c]['n']} · {s['ses'][c]['wr']:.0%} · {s['ses'][c]['E']:+.2f}R" if s["ses"][c]["n"] else "—") for c in cols]
    ui_table(pd.DataFrame(rows, index=["کل", f"خارج‌ازنمونه ({OOS_FRAC:.0%} آخر)"] + [f"{SESS_FA[c]} ({SESS_UTC[c]} UTC)" for c in cols]).T, f"🧪 بک‌تست {ASSET}: {L['days']} روز، {L['bars']:,} کندل ۵م (ورود لیمیت با پر شدن واقعی + کارمزد کریپتو، SL={SL_ATR:g}ATR، TP1={SAFE_R1:g}R نصف حجم + BE، TP2={SAFE_R2:g}R، سقف ۲ ساعت؛ برد = R>0). فقط راهنماست، نه وعدهٔ سود.")
    ui(_note("خواندن جدول: این اعداد گذشته‌اند و نمونهٔ هر سشن کوچک است؛ امتیاز زنده با انقباض به سمت کل داده محاسبه می‌شود. وین‌ریت بالا بدون میانگین R مثبت یعنی چیزی نیست (PDF هم همین را می‌گوید: ملاک «انتظار معامله» است).", "#2b8fd6"))

def strat_prepare(pr=None):
    """مرحلهٔ جدید تحلیل: بک‌تست ← آزمون ← انتخاب استراتژی توسط ۱۴ عضو ← تعیین جهت. قبل از ایجنت ICT/میز/مدیرعامل اجرا می‌شود تا همه روی همین ستاپ کار کنند."""
    if not STRAT_ON: return
    try:
        AG["strat_sel"] = None; AG["strat_desk"] = None; AG["team_side"] = AG.get("side") if AG["ok"] else None
        L = strat_lab()
        if L:
            try: strat_board()
            except Exception as e: print("⚠ جدول بک‌تست نمایش داده نشد:", str(e)[:100])
        if EXAM_ON and USE_AGENTS and AG["ok"]: strat_exam()
        now, age = snapshot()
        if age > MAX_AGE_MIN: return
        pr = pr if pr is not None else live_price(now.c)[0]; AG["strat_sel"] = strat_select(now, pr)
        strat_desk_prepare(pr, force=True)
        S = strat_select(now, pr); AG["strat_sel"] = S; P = S.get("pick")
        if P and AG["ok"]:
            if AG["side"] != P["side"]: print(f"ℹ جهت از «استراتژی {P['n']}» آمد ({'خرید' if P['side'] == 1 else 'فروش'})؛ رأی تحلیلگران تیم ({AG['rating']}) فقط به‌عنوان زمینه حساب می‌شود.")
            AG["side"] = P["side"]; AG["override"] = False
    except Exception as e: print(f"⚠ مرحلهٔ استراتژی خطا داد ({type(e).__name__}: {str(e)[:160]})؛ بدون آن ادامه می‌دهم."); AG["strat_sel"] = None

def _strat_live(now):
    prev = AG.get("strat_sel"); pin = ((prev or {}).get("pick") or {}).get("k") if (prev and AG["ok"]) else None
    pr = live_price(now.c)[0]; S = strat_select(now, pr, pin=pin); AG["strat_sel"] = S; return S

_council_panel_orig = _council_panel
def _council_panel(Cp, ck, side):      # v15: ابتدا پنل استراتژی‌ها، بعد اقتصاددان و مدیرعامل؛ کاشی‌های ۱۴ سبک فقط وقتی COUNCIL_ON باشد
    if STRAT_ON:
        try: _strat_panel(AG.get("strat_sel"), side)
        except Exception as e: print("⚠ پنل استراتژی‌ها نمایش داده نشد:", str(e)[:140])
    if CHAIR_ON and COUNCIL_ON:
        try: ui(_note(_chair_note(), "#d4af37"))
        except Exception: pass
    try: _econ_panel()
    except Exception as e: print("⚠ پنل اقتصاددان نمایش داده نشد:", str(e)[:120])
    _council_panel_v11(Cp, ck, side)

def strat_stats():
    rows = [x for x in _jread() if x.get("R") is not None and x.get("strat")]
    if not rows: return
    df = pd.DataFrame(rows); df["strat"] = df.strat.map(lambda k: STRATS.get(k, {"n": k})["n"])
    g = df.groupby("strat").R.agg(["count", "mean", lambda s: (s > 0).mean()]); g.columns = ["تعداد", "میانگین R", "نرخ برد"]; ui_table(g.round(2), "به تفکیک استراتژیِ کتابچه (معاملات واقعیِ ثبت‌شدهٔ شما)")
    if "session" in df.columns: pass

_js_orig = journal_stats
def journal_stats():
    _js_orig()
    try: strat_stats()
    except Exception as e: print("⚠ آمار استراتژی‌ها:", str(e)[:100])


# ---------------- حالت ALL: اسکن همهٔ دارایی‌ها و انتخاب بهترین موقعیت ----------------
_LABS = {}; _ALL = {"rows": [], "win": None, "mode": ""}
def _all_one(a):
    """اسکن سریع یک دارایی بدون مدل زبانی: داده ← بک‌تست کوتاه ← استراتژی‌های فعال همین لحظه."""
    _apply_asset(a); _LAB["fail"] = 0; _SNAP.update(t=0.0, v=None); _PAIR.update(t=0.0, df=None, sym=None)
    now, age = snapshot()
    if age > MAX_AGE_MIN: return {"a": a, "tier": -1, "sc": -9.0, "why": f"بازار بسته یا داده کهنه ({age:.0f} دقیقه)"}
    L = strat_lab(quiet=True)
    if not L: return {"a": a, "tier": -1, "sc": -9.0, "why": "بک‌تست انجام نشد"}
    _LABS[a] = L
    try: pr = live_price(now.c)[0]
    except Exception: pr = float(now.c)
    S = strat_select(now, pr); ses = S["session"]; best = None
    for r in S["rows"]:
        if not r["run"] or r["state"] not in ("ACTIVE", "ARMING") or not r["side"]: continue
        sc = r.get("sc"); s_ = sc["score"] if sc else 0.0
        key = (2 if (r["state"] == "ACTIVE" and s_ >= STRAT_NEG_SCORE) else 1, s_)      # ستاپ فعالِ دارای بک‌تست ضعیف با بقیه رقابت می‌کند، نه جلوتر از همه
        if best is None or key > best[0]: best = (key, r, sc)
    if best is None:      # v21: بدون ستاپ، رتبه از «آمادگی لحظه‌ای بازار» می‌آید (نه امتیاز ثابت بک‌تست که همیشه یک ارز را جلو می‌انداخت)
        mt_ = S.get("meta") or {}; rs_ = mt_.get("rsi", 50.0); bw_ = mt_.get("bwp", 0.5)
        rd = 0.30 * min(abs(rs_ - 50.0) / 30.0, 1.0) + 0.25 * min(float(mt_.get("adx", 0.0)) / 35.0, 1.0) + 0.25 * min(abs((bw_ if bw_ == bw_ else 0.5) - 0.5) * 2.0, 1.0) + 0.20 * abs(float(now.votes)) / 4.0
        return {"a": a, "tier": 0, "sc": float(rd), "rd": float(rd), "why": f"هیچ ستاپی فعال نیست؛ آمادگی بازار {rd:.0%} (RSI {rs_:.0f}، ADX {float(mt_.get('adx', 0.0)):.0f})"}
    (tier, s), r, sc = best
    return {"a": a, "tier": tier, "sc": float(s), "k": r["k"], "n": r["n"], "side": r["side"], "state": r["state"], "ns": (sc or {}).get("n_ses"), "wr": (sc or {}).get("wr_ses"), "why": ""}

def _lbl(r): return "ستاپ فعال" if r["tier"] == 2 else ("ستاپ فعال (بک‌تست ضعیف)" if r.get("state") == "ACTIVE" else "در حال شکل‌گیری" if r["tier"] == 1 else "بدون ستاپ")
def _all_txt():
    o = []
    for r in _ALL["rows"]:
        if r["tier"] < 0: o.append(f"⛔ {r['a']}: {r['why']}"); continue
        mark = "🏆" if r["a"] == _ALL["win"] else "•"; st = _lbl(r)
        if r.get("rd") is not None: o.append(f"{mark} {r['a']}: {st} · {r['why']}"); continue
        d = f" · {r['n']} ({'خرید' if r['side'] == 1 else 'فروش'})" if r.get("n") else ""
        w = f" · وین‌ریت سشن {r['wr']:.0%} (n={r['ns']})" if r.get("ns") else ""
        o.append(f"{mark} {r['a']}: {st}{d} · امتیاز بک‌تست {r['sc']:+.2f}{w}")
    return "\n".join(o)

_ALLBOARD = {"shown": False}
def _lt(sec=0): return (utcnow() + dt.timedelta(hours=TZ_HOURS + sec / 3600.0)).strftime("%H:%M")
def _mmss(s): s = max(0, int(s)); return f"{s // 60}:{s % 60:02d}"
def _board_show(html, did):
    o = HTML(_CSS + "<div class='ta'>" + html + "</div>")
    try:
        from IPython.display import update_display
        if _ALLBOARD.get(did): update_display(o, display_id=did)
        else: display(o, display_id=did); _ALLBOARD[did] = True
    except Exception: pass
def _tile(a, s, r, win=False):
    b = ASSET_BADGE.get(a); em = b[0] if b else "•"
    if s == "wait": col, txt, extra = "#8a8f98", "⏳ در صف", ""
    elif s == "scan": col, txt, extra = "#3b82f6", "🔎 در حال اسکن...", ""
    else:
        t = r.get("tier", -1)
        if t < 0: col, txt, extra = "#64748b", "⛔ " + str(r.get("why", ""))[:40], ""
        elif t == 2: col, txt, extra = "#30a46c", f"🟢 ستاپ فعال: {_h(r.get('n', ''))} ({'خرید' if r.get('side') == 1 else 'فروش'})", f"<div class='m'><i style='width:{max(8, min(100, 50 + r['sc'] * 60)):.0f}%'></i></div>"
        elif t == 1: col, txt, extra = "#06b6d4", f"🔵 در حال شکل‌گیری: {_h(r.get('n', ''))}", f"<div class='m'><i style='width:{max(8, min(100, 40 + r['sc'] * 50)):.0f}%'></i></div>"
        else: col, txt, extra = "#8b5cf6", f"🟣 بدون ستاپ · آمادگی {r.get('rd', 0):.0%}", f"<div class='m'><i style='width:{r.get('rd', 0) * 100:.0f}%'></i></div>"
    return f"<div class='al-t{' win' if win else ''}{' scan' if s == 'scan' else ''}' style='--c:{col}'><b>{em} {_h(a)}</b>{' 🏆' if win else ''}<div class='s'>{txt}</div>{extra}</div>"
def _all_html(st, N, t0s, rem, cur=None, final=False):
    done = sum(1 for v in st.values() if v["s"] == "done"); pct = done / max(N, 1) * 100
    tiles = "".join(_tile(a, v["s"], v.get("r") or {}, win=(final and a == _ALL.get("win"))) for a, v in st.items())
    eta = f"⏱ اسکن: {_mmss(time.time() - t0s)} گذشته" + ("" if final else f" · حدود {_mmss(rem)} مانده") + (f" · 🧠 تحلیل کامل ۶ تا ۱۲ دقیقه بعد از اسکن ⇒ <b>جواب نهایی حدود ساعت {_lt(rem + 9 * 60)}</b> (به وقت شما)" if not final else "")
    return f"<div class='al-wrap'><div class='al-top'><span>🔎 اسکن ALL · {done}/{N} دارایی" + (f" · الان: {_h(cur)}" if cur else "") + f"</span><span>{pct:.0f}٪</span></div><div class='al-bar'><i style='width:{pct:.0f}%'></i></div><div class='al-eta'>{eta}</div><div class='al-grid'>{tiles}</div></div>"
def _all_show():
    if not _ALL["win"]: return
    st = {r["a"]: {"s": "done", "r": r} for r in _ALL["rows"]}
    ui(_all_html(st, len(st), time.time() - _ALL.get("dur", 0), 0, final=True) + _note(f"🏆 حالت ALL ← بهترین موقعیت: {_ALL['win']} ({_ALL['mode']}). ترتیب کارت‌ها همان رتبه‌بندی است؛ اگر دارایی دیگری را می‌خواهید، ASSET را روی همان بگذارید.", "#d4af37"))

def all_scan():
    global STRAT_REQUIRED
    ui_step(3, "اسکن همهٔ دارایی‌ها (ALL)", f"{len(ALL_ASSETS)} دارایی · بک‌تست {STRAT_DAYS_ALL} روزه · بدون مدل زبانی؛ بعد تیم کامل فقط روی بهترین گزینه")
    N = len(ALL_ASSETS); st = {a: {"s": "wait"} for a in ALL_ASSETS}; t0s = time.time(); durs = []; rows = []; _ALLBOARD["ta_all"] = False
    def render(cur=None):
        avg = (sum(durs) / len(durs)) if durs else 9.0; done = sum(1 for v in st.values() if v["s"] == "done")
        _board_show(_all_html(st, N, t0s, avg * (N - done), cur), "ta_all")
    render()
    for a in ALL_ASSETS:
        st[a]["s"] = "scan"; render(a); t1 = time.time()
        try: r = _all_one(a)
        except Exception as e: r = {"a": a, "tier": -1, "sc": -9.0, "why": f"خطا ({type(e).__name__}: {str(e)[:70]})"}
        durs.append(time.time() - t1); st[a].update(s="done", r=r); rows.append(r); render()
    rec = set()      # v21: دارایی‌هایی که تازه سیگنال گرفته‌اند کمی عقب می‌افتند تا هر بار همان یکی انتخاب نشود
    try:
        lim = utcnow() - dt.timedelta(hours=ALL_REPEAT_HOURS)
        for ln in open(SIG_LOG_PATH, encoding="utf-8"):
            try: x_ = json.loads(ln); rec.add(x_["asset"]) if dt.datetime.fromisoformat(x_["t"]) >= lim else None
            except Exception: pass
    except Exception: pass
    def _wrb(r):
        try: return (_wilson_lb(float(r["wr"]), int(r["ns"])) - 0.5) if r.get("ns") else 0.0
        except Exception: return 0.0
    for r in rows: r["adj"] = r["sc"] - (ALL_REPEAT_PEN if (r["a"] in rec and r["tier"] >= 0) else 0.0) + (_WR_W * _wrb(r) if (_HEADLESS and r["tier"] >= 2) else 0.0)      # GitHub: حد پایین وین‌ریت وزن اضافه دارد
    rows.sort(key=lambda r: (r["tier"], r["adj"]), reverse=True)
    ok = [r for r in rows if r["tier"] >= 0]
    if not ok: raise RuntimeError("هیچ داراییِ دارای داده تازه پیدا نشد (بازارها بسته‌اند یا اینترنت/Yahoo قطع است).")
    w = ok[0]; _ALL.update(rows=rows, win=w["a"], dur=time.time() - t0s, mode=_lbl(w) + ("؛ آماده‌ترین بازار" if w["tier"] == 0 else "") + (" · بعد از جریمهٔ تکرار" if w["a"] not in rec and rec else ""))
    if w["tier"] < 2 and ALL_FALLBACK: STRAT_REQUIRED = False      # بی‌سیگنال نمی‌مانیم: بهترین گزینه با پرچم ریسک
    _apply_asset(w["a"]); _LAB["v"] = _LABS.get(w["a"]); _LAB["fail"] = 0; _SNAP.update(t=0.0, v=None); _PAIR.update(t=0.0, df=None, sym=None)
    print(f"✅ ALL ← {w['a']} انتخاب شد ({_ALL['mode']}). حالا تحلیل کامل روی همین دارایی اجرا می‌شود.")


_notify_orig = notify
def notify(title, msg, prio=3, tags="", delay=None, seq=None):      # GitHub: پیام‌های «شروع/میانه» نمی‌روند؛ فقط سیگنال و خطا
    if _HEADLESS and str(title).startswith(("🧠 تحلیل", "🧩 تیم عامل‌ها")): return True
    return _notify_orig(title, msg, prio, tags, delay, seq)

# ---------------- اجرا ----------------
t0 = time.time(); _run_start = utcnow().isoformat(timespec="seconds")
if not _topic(): print("⚠ اعلان گوشی خاموش است" + (f" ({_NTFY['why']})" if _NTFY["why"] else "") + ". برای راه‌اندازی در یک خط: notify_test() را اجرا کنید؛ مراحل را دقیق می‌گوید.")
if _HEADLESS and not ALL_MODE:      # تک‌دارایی هم با همان حلقهٔ جست‌وجو؛ بک‌تست همان ۵۸ روز می‌ماند
    ALL_MODE = True; ALL_ASSETS = [ASSET]; STRAT_DAYS_ALL = STRAT_DAYS
if ALL_MODE and _HEADLESS:
    # GitHub: تا پیدا شدن ستاپ فعالِ معتبر (۱:۳ اولویت) همهٔ دارایی‌ها را دوباره و دوباره می‌گردد؛ زمان مهم نیست.
    def _is_dup(w):
        try:
            lim = utcnow() - dt.timedelta(hours=_COOLDOWN_H)
            for ln in open(SIG_LOG_PATH, encoding="utf-8"):
                try: x = json.loads(ln); t_ = dt.datetime.fromisoformat(str(x["t"])[:19])
                except Exception: continue
                if t_ >= lim and w.get("n") and x.get("asset") == w["a"] and x.get("side") == w.get("side") and x.get("strat_name") == w["n"]: return True
        except FileNotFoundError: pass
        return False
    _deadline = time.time() + _SEARCH_MIN * 60; _scans = 0; _final = False
    while True:
        _scans += 1; _err = ""; _w = {}
        try: all_scan(); _w = next((r for r in _ALL["rows"] if r["a"] == _ALL["win"]), {})
        except Exception as _e: _err = f"{type(_e).__name__}: {str(_e)[:120]}"
        if not _err:
            _dup = _is_dup(_w)
            if _w.get("tier", -1) >= 2 and not _dup: print(f"✅ ستاپ فعالِ معتبر بعد از {_scans} اسکن پیدا شد."); break
            if _final and _w.get("tier", -1) >= 0 and not _dup: print("ℹ ستاپ معتبر پیدا نشد؛ بهترین گزینهٔ موجود با پرچم ریسک."); break
            print(f"ℹ اسکن {_scans}: ستاپ معتبر نیست{' (تکراری)' if _dup else ''}؛ {int(max(0, _deadline - time.time()) / 60)} دقیقه تا پایان جست‌وجو.")
        else: print(f"⚠ اسکن {_scans} خطا داد ({_err}).")
        if _final: raise _HeadlessStop("nothing-found")
        if time.time() >= _deadline:
            if _FINAL_FALLBACK: ALL_FALLBACK = True; _final = True; continue
            raise _HeadlessStop("no-setup-in-window")
        time.sleep(max(5.0, min(float(_RESCAN_SEC), _deadline - time.time())))
elif ALL_MODE: all_scan()
if not _HEADLESS: news_watch_start()
_RUN.update(since=_run_start, sent=False, done=False, dm=None)
_dm_min = int(AGENT_TIMEOUT_MIN) + 15
notify(f"🧠 تحلیل {ASSET} شروع شد", f"حدود ۶ تا ۱۲ دقیقه طول می‌کشد؛ نتیجه همین‌جا اعلان می‌شود. اگر Colab وسط کار قطع شود (قفل‌شدن گوشی)، تا ۶ دقیقه بعد خود ntfy هشدار «قطع شد» می‌دهد.", 2, "hourglass_flowing_sand")
_sig_watch_start(_run_start, _dm_min) if _HEADLESS else (_deadman_arm(_dm_min), _sig_watch_start(_run_start, _dm_min))
try:
    ui(_news_html(news_guard(), always=True))      # v12: قبل از ۱۰ دقیقه انتظار، وضعیت خبر را ببینید
    ui_step(3, "تحلیل کامل", f"{ASSET}{' (انتخاب‌شده از ALL)' if ALL_MODE else ''} · تیم عامل‌ها + اقتصاددان PhD + بک‌تست و انتخاب استراتژی (۱۴ عضو) + میز مناظره + مدیر سبد + مدیرعامل · ۶ تا ۱۲ دقیقه")
    if USE_AGENTS:
        AG["wanted"] = True; AG["err"] = ""; AG.update(smc=None, smc_err="", smc_tried=False, desk=None, desk_tried=False, desk_err="", debate=None, override=False, council=None, council_llm=None, council_net=None, council_err="", ceo=None, ceo_tried=False, ceo_err="", strat_sel=None, strat_desk=None, team_side=None)
        AG["t0"] = utcnow(); _p0, _s0, _ = live_price(float("nan"))      # قیمت لحظهٔ شروع تحلیل (برای هشدار حرکت قیمت)
        AG["p0"] = None if (_p0 != _p0 or "⚠" in _s0) else _p0
        _agent_live(time.time())      # v21: کارت زندهٔ پیشرفت + پیش‌بینی زمان جواب (بدون چاپ‌های پشت‌سرهم)
        res = run_agents_safe(AGENT_TIMEOUT_MIN)
        if res:
            side, rating, state = res; AG.update(ok=True, side=side, rating=rating, state=state, t=utcnow())
            print(f"عامل‌ها تمام کردند ({(time.time()-t0)/60:.1f} دقیقه). حالا داده و قیمت زنده گرفته می‌شود ...")
            notify(f"🧩 تیم عامل‌ها تمام شد · {ASSET}", "در حال ساخت سیگنال نهایی؛ چند دقیقهٔ دیگر.", 1, "gear")
        else: print("ادامه با تحلیل تکنیکال چندتایم‌فریم به‌جای عامل‌ها.")
        econ_prepare(); council_prepare(); strat_prepare()    # v15: بک‌تست ← آزمون ← انتخاب استراتژی؛ v12: اقتصاددان + v11: شورای ۱۴ نفره (برای اینکه اگر تیم «نگه‌دار» گفت، جهت از شورا هم بیاید)
        if AG["ok"] and AG["side"] == 0 and (M()["hold_override"] or TIERS_ON) and not (STRAT_ON and (AG.get("strat_sel") or {}).get("pick")): _hold_override()
        if not (STRAT_ON and STRAT_REQUIRED and not (AG.get("strat_sel") or {}).get("pick")): desk_prepare()    # (v15: بدون استراتژی فعال، تماس‌های گران مدل انجام نمی‌شود) ایجنت ICT/SMC ← مناظرهٔ تکنیکال×بنیادی ← مدیر سبد (قبل از پاک‌شدن خروجی، تا بلوک سیگنال بالا بماند)
        clear_output(wait=True)   # گزارش‌های «هنوز مشغولم» پاک می‌شوند تا بلوک سیگنال بالای خروجی باشد
    requote()
    if ALL_MODE: _all_show()
    _notify_signal(_run_start)
    if USE_AGENTS and AG["ok"]:
        show_details()
    if USE_AGENTS:
        try:
            ev = [x for x in PROG.events if x.startswith("🔧")]; er = [x for x in PROG.events if x.startswith("⚠")]
            body = "\n".join(["  " + x for x in ev[:40]] + ["  " + x for x in er[:10]]) or "هیچ ابزاری ثبت نشد (تحلیلگرها داده‌ای نگرفتند یا گزارش پیشرفت خاموش بود)."
            ui_fold(f"🛠 ممیزی منابع و ابزارها ({len(ev)} ابزار اجرا شد، {len(er)} خطا)", body)
        except Exception: pass
        try: ui_fold("⏱ کندترین بخش‌های تیم عامل‌ها", PROG.summary())
        except Exception: pass

except BaseException as _e:      # شامل Stop دستی / KeyboardInterrupt / قطع ارتباط؛ قبلاً فقط Exception گرفته می‌شد و در این حالت‌ها اعلانی نمی‌آمد
    _RUN["done"] = True
    _send_once(f"❌ تحلیل {ASSET} {'قطع شد' if isinstance(_e, KeyboardInterrupt) else 'با خطا متوقف شد'}", f"{type(_e).__name__}: {str(_e)[:300]}", 5, "x")
    _deadman_cancel()
    raise
_RUN["done"] = True; _deadman_cancel()
_extra = f" | تماس مدل: {PROG.llm}، ابزار: {PROG.tools}، خطای مدل: {PROG.errs}" if USE_AGENTS else ""
ui(_note(("📲 اعلان: " + (f"{_NTFY['ok']} پیام ارسال شد" + (f"، {_NTFY['fail']} ناموفق ({_NTFY['err'][:90]})" if _NTFY["fail"] else "")) if _topic() else "📲 اعلان خاموش است؛ notify_test() را اجرا کنید"), "#22c55e" if (_topic() and not _NTFY["fail"]) else "#d99a00"))
ui(f"<div style='opacity:.72;font-size:12.5px;margin:8px 0'>زمان اجرا: {(time.time()-t0)/60:.1f} دقیقه{_h(_extra)} · این خروجی تحلیل است، نه توصیهٔ مالی.</div>")

