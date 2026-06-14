import requests, re, html, json, os, time
from datetime import datetime, timezone, timedelta

# كلمات مفتاحية مناسبة لباك إند Laravel — عدّل/زوّد زي ما تحب
KEYWORDS = [
    "Laravel",
    "PHP Laravel",
    "PHP Developer",
    "Backend Developer",
    "Back end Developer",
    "Backend Engineer",
    "Web Developer",
    "Full Stack Developer",
    "API Developer",
]
LOCATION   = "Egypt"
MAX_PAGES  = 2        # لكل كلمة مفتاحية (كل صفحة ~25 وظيفة)
KEEP_DAYS  = 14       # الوظيفة تفضل في الكاش كام يوم
CACHE_FILE = "jobs_cache.json"

BASE = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}


def fetch_for_keyword(kw):
    found = {}
    for page in range(MAX_PAGES):
        params = {"keywords": kw, "location": LOCATION,
                  "f_TPR": "r86400", "start": page * 25}
        try:
            r = requests.get(BASE, headers=HEADERS, params=params, timeout=20)
        except requests.RequestException:
            break
        if r.status_code != 200 or not r.text.strip():
            break
        cards = re.findall(
            r'data-entity-urn="urn:li:jobPosting:(\d+)".*?'
            r'<h3[^>]*>(.*?)</h3>.*?'
            r'subtitle[^>]*>(.*?)</h4>.*?'
            r'job-search-card__location[^>]*>(.*?)</span>',
            r.text, re.S)
        if not cards:
            break
        clean = lambda s: html.unescape(re.sub("<.*?>", "", s).strip())
        for jid, title, company, loc in cards:
            found[jid] = {
                "id": jid,
                "title": clean(title),
                "company": clean(company),
                "location": clean(loc),
                "keyword": kw,
                "link": "https://www.linkedin.com/jobs/view/" + jid,
            }
        time.sleep(1)   # نكون مؤدبين مع الـ endpoint
    return found


def load_cache():
    if os.path.exists(CACHE_FILE):
        try:
            return json.load(open(CACHE_FILE, encoding="utf-8"))
        except Exception:
            return {}
    return {}


def build_html(jobs, now):
    data = {"builtAt": now.isoformat(), "jobs": jobs}
    page = TEMPLATE.replace("/*__DATA__*/", json.dumps(data, ensure_ascii=False))
    os.makedirs("public", exist_ok=True)
    with open("public/index.html", "w", encoding="utf-8") as f:
        f.write(page)


def main():
    now = datetime.now(timezone.utc)
    cache = load_cache()

    fetched = {}
    for kw in KEYWORDS:
        fetched.update(fetch_for_keyword(kw))

    new_count = 0
    for jid, job in fetched.items():
        if jid in cache:
            job["first_seen"] = cache[jid].get("first_seen", now.isoformat())
        else:
            job["first_seen"] = now.isoformat()
            new_count += 1
        cache[jid] = job

    # نشيل اللي أقدم من KEEP_DAYS من الكاش
    cutoff = now - timedelta(days=KEEP_DAYS)
    cache = {jid: j for jid, j in cache.items()
             if datetime.fromisoformat(j["first_seen"]) >= cutoff}

    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=1)

    jobs = sorted(cache.values(), key=lambda j: j["first_seen"], reverse=True)
    build_html(jobs, now)
    print("cached=" + str(len(jobs)) + " new=" + str(new_count))


TEMPLATE = """<!doctype html>
<html lang="ar" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>وظايف Laravel / Backend</title>
<style>
  :root{--bg:#0f1115;--card:#1b1e24;--border:#2a2e36;--text:#e8eaed;--muted:#9aa0a6;--accent:#8ab4f8;--new:#34d399;--chip:#262a31}
  [data-theme=light]{--bg:#f6f7f9;--card:#fff;--border:#e2e5ea;--text:#1b1e24;--muted:#5f6368;--accent:#1a73e8;--new:#0f9d58;--chip:#eceef1}
  *{box-sizing:border-box}
  body{font-family:system-ui,-apple-system,Segoe UI,Tahoma,Arial;background:var(--bg);color:var(--text);margin:0;line-height:1.6}
  .wrap{max-width:820px;margin:0 auto;padding:24px 16px 60px}
  header{display:flex;justify-content:space-between;align-items:flex-start;gap:12px;flex-wrap:wrap}
  h1{font-size:22px;margin:0}
  .sub{color:var(--muted);font-size:13px;margin:6px 0 18px}
  .toolbar{display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin-bottom:16px}
  input,select,button{font:inherit;color:var(--text);background:var(--card);border:1px solid var(--border);border-radius:10px;padding:9px 12px}
  input[type=search]{flex:1;min-width:180px}
  button{cursor:pointer}
  button:hover{border-color:var(--accent)}
  button.active{border-color:var(--accent);color:var(--accent)}
  .chips{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:18px}
  .chip{font-size:12px;padding:5px 10px;border-radius:999px;background:var(--chip);border:1px solid transparent;cursor:pointer;color:var(--muted)}
  .chip.active{border-color:var(--accent);color:var(--accent)}
  ul{list-style:none;padding:0;margin:0}
  .job{background:var(--card);border:1px solid var(--border);border-radius:14px;padding:14px 16px;margin-bottom:10px;position:relative}
  .job.is-new{border-color:var(--new)}
  .job h3{margin:0 0 4px;font-size:16px}
  .job a{color:var(--accent);text-decoration:none}
  .job a:hover{text-decoration:underline}
  .meta{color:var(--muted);font-size:13px}
  .tag{display:inline-block;font-size:11px;background:var(--chip);color:var(--muted);padding:2px 8px;border-radius:6px;margin-top:8px}
  .badge{position:absolute;inset-inline-start:14px;top:14px;background:var(--new);color:#04261a;font-size:11px;font-weight:700;padding:2px 8px;border-radius:6px}
  .empty{text-align:center;color:var(--muted);padding:40px 0}
</style>
</head>
<body>
<div class="wrap">
  <header>
    <div>
      <h1>💼 وظايف Laravel / Backend</h1>
      <div class="sub" id="sub"></div>
    </div>
    <div style="display:flex;gap:8px">
      <button id="theme" title="ثيم">🌗</button>
      <button id="markseen">علّم الكل كمقروء</button>
    </div>
  </header>
  <div class="toolbar">
    <input type="search" id="q" placeholder="ابحث بالعنوان أو الشركة…">
    <select id="sort">
      <option value="new">الأحدث أولاً</option>
      <option value="company">الشركة</option>
      <option value="title">العنوان</option>
    </select>
    <button id="newonly">الجديد فقط</button>
  </div>
  <div class="chips" id="chips"></div>
  <ul id="list"></ul>
  <div class="empty" id="empty" style="display:none">مفيش وظايف مطابقة.</div>
</div>
<script>
const DATA = /*__DATA__*/;
const SEEN_KEY = "seenJobs";
const seen = new Set(JSON.parse(localStorage.getItem(SEEN_KEY) || "[]"));
let state = { q:"", sort:"new", keyword:"", newOnly:false };

const themeBtn = document.getElementById("theme");
if (localStorage.getItem("theme") === "light") document.documentElement.setAttribute("data-theme","light");
themeBtn.onclick = () => {
  const light = document.documentElement.getAttribute("data-theme") !== "light";
  if (light) { document.documentElement.setAttribute("data-theme","light"); localStorage.setItem("theme","light"); }
  else { document.documentElement.removeAttribute("data-theme"); localStorage.setItem("theme",""); }
};

function timeAgo(iso){
  const m = (Date.now() - new Date(iso)) / 60000;
  if (m < 60) return "من " + Math.max(1, Math.round(m)) + " دقيقة";
  if (m < 1440) return "من " + Math.round(m/60) + " ساعة";
  return "من " + Math.round(m/1440) + " يوم";
}

const keywords = Array.from(new Set(DATA.jobs.map(j => j.keyword))).sort();
const chips = document.getElementById("chips");
function renderChips(){
  chips.innerHTML = "";
  const mk = (label, val) => {
    const c = document.createElement("span");
    c.className = "chip" + (state.keyword === val ? " active" : "");
    c.textContent = label;
    c.onclick = () => { state.keyword = state.keyword === val ? "" : val; renderChips(); render(); };
    chips.appendChild(c);
  };
  mk("الكل", "");
  keywords.forEach(k => mk(k, k));
}

document.getElementById("q").oninput = e => { state.q = e.target.value.toLowerCase(); render(); };
document.getElementById("sort").onchange = e => { state.sort = e.target.value; render(); };
const newBtn = document.getElementById("newonly");
newBtn.onclick = () => { state.newOnly = !state.newOnly; newBtn.classList.toggle("active", state.newOnly); render(); };
document.getElementById("markseen").onclick = () => {
  DATA.jobs.forEach(j => seen.add(j.id));
  localStorage.setItem(SEEN_KEY, JSON.stringify(Array.from(seen)));
  render();
};

function render(){
  let jobs = DATA.jobs.slice();
  if (state.keyword) jobs = jobs.filter(j => j.keyword === state.keyword);
  if (state.q) jobs = jobs.filter(j => (j.title + " " + j.company).toLowerCase().includes(state.q));
  if (state.newOnly) jobs = jobs.filter(j => !seen.has(j.id));
  if (state.sort === "company") jobs.sort((a,b) => a.company.localeCompare(b.company));
  else if (state.sort === "title") jobs.sort((a,b) => a.title.localeCompare(b.title));
  else jobs.sort((a,b) => new Date(b.first_seen) - new Date(a.first_seen));

  const list = document.getElementById("list");
  list.innerHTML = "";
  document.getElementById("empty").style.display = jobs.length ? "none" : "block";
  jobs.forEach(j => {
    const isNew = !seen.has(j.id);
    const li = document.createElement("li");
    li.className = "job" + (isNew ? " is-new" : "");
    li.innerHTML =
      (isNew ? '<span class="badge">جديد</span>' : '') +
      '<h3><a href="' + j.link + '" target="_blank" rel="noopener">' + j.title + '</a></h3>' +
      '<div class="meta">' + j.company + ' · ' + j.location + ' · ' + timeAgo(j.first_seen) + '</div>' +
      '<span class="tag">' + j.keyword + '</span>';
    list.appendChild(li);
  });

  const newCount = DATA.jobs.filter(j => !seen.has(j.id)).length;
  document.getElementById("sub").textContent =
    "الإجمالي: " + DATA.jobs.length + " · جديد عندك: " + newCount + " · آخر تحديث " + timeAgo(DATA.builtAt);
}

renderChips();
render();
</script>
</body>
</html>"""

if __name__ == "__main__":
    main()
