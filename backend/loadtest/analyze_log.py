import os, collections, sys

LOG = os.path.join(os.path.dirname(__file__), "results", "server.log")
data = open(LOG, "rb").read().decode("utf-8", "replace")
lines = data.split("\n")

SIGS = {
    "tasks.number UNIQUE race": "UNIQUE constraint failed: tasks.number",
    "companies.work_directions missing col": "no such column: companies.work_directions",
    "commit while statements in progress": "cannot commit transaction - SQL statements in progress",
    "session in 'prepared' state": "session is in 'prepared' state",
    "could not refresh instance": "Could not refresh instance",
    "database is locked": "database is locked",
}
BACK = chr(92)


def asc(s):
    return s.encode("ascii", "replace").decode("ascii")


def app_frame(ln):
    if '.py", line ' not in ln:
        return None
    if "site-packages" in ln or "WindowsApps" in ln or "Python3" in ln:
        return None
    if "loadtest" in ln:
        return None
    if ("backend" + BACK + "app") in ln or ("backend/app") in ln or (BACK + "app" + BACK) in ln or "/app/" in ln:
        p = ln.strip()
        k = p.find('File "')
        return asc(p[k:k + 165]) if k >= 0 else asc(p[:165])
    return None


for label, sig in SIGS.items():
    idx = [i for i, l in enumerate(lines) if sig in l]
    print("\n###### %s   count=%d" % (label, len(idx)))
    if not idx:
        continue
    frames = collections.Counter()
    for i in idx[:400]:
        for j in range(max(0, i - 70), i):
            f = app_frame(lines[j])
            if f:
                frames[f] += 1
    for f, c in frames.most_common(7):
        print("   [%d] %s" % (c, f))

codes = collections.Counter()
for l in lines:
    m = l.find('HTTP/1.1" 5')
    if m != -1:
        codes[l[m + 10:m + 13]] += 1
print("\n###### access-log 5xx counts:", dict(codes))
