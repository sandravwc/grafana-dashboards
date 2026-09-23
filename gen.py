#!/usr/bin/env python3
"""Generate poco.json. Edit this, run it, commit both. Never touch the JSON by hand, never the GUI.

    python3 gen.py && git commit -am ... && git push      # then: git -C ~/monitoring/dashboards pull

CHAIN below is the service graph: one entry per box, `to` draws the arrows. `up` colours the box
(any 0/1 query), `rpm` is the number printed inside it. No traces involved -- the topology is
declared here because it changes when haproxy.d changes, not per request.
"""
import json

DS = {"type": "prometheus", "uid": "prom"}

CHAIN = [
    # id                col row  label                     up (0/1)                                          rpm
    ("internet",         0, 2,  "internet",                None,                                             None),
    ("haproxy",          1, 2,  "haproxy :8443",           'haproxy_up',                                     'sum(rate(haproxy_backend_sessions_total[5m])) * 60'),
    ("anubis-shoko",     2, 0,  "anubis :8924",            'up{job="anubis", app="shoko"}',                  'sum(rate(anubis_proxied_requests_total{app="shoko"}[5m])) * 60'),
    ("anubis-mealprep",  2, 1,  "anubis :8923",            'up{job="anubis", app="mealprep"}',               'sum(rate(anubis_proxied_requests_total{app="mealprep"}[5m])) * 60'),
    ("grafana",          2, 2,  "grafana :3000",           'haproxy_backend_up{backend="grafana"}',          'rate(haproxy_backend_sessions_total{backend="grafana"}[5m]) * 60'),
    ("prom",             2, 3,  "prometheus :9090",        'up{job="prometheus"}',                           'rate(haproxy_backend_sessions_total{backend="prom"}[5m]) * 60'),
    ("alerts",           2, 4,  "alertmanager :9093",      'haproxy_backend_up{backend="alerts"}',           'rate(haproxy_backend_sessions_total{backend="alerts"}[5m]) * 60'),
    ("shoko",            3, 0,  "shoko :8111",             'probe_success{name="shoko api"}',                'rate(haproxy_backend_sessions_total{backend="shoko"}[5m]) * 60'),
    ("mealprep",         3, 1,  "mealprep :8090",          'probe_success{name="mealprep app"}',             'rate(haproxy_backend_sessions_total{backend="mealprep"}[5m]) * 60'),
    # lan services, no haproxy in front
    ("nfs",              0, 5,  "nfs :2049",               'probe_success{name="nfs"}',                      None),
    ("sshd",             1, 5,  "sshd :8022",              'probe_success{name="sshd"}',                     None),
]
EDGES = [("internet", "haproxy"),
         ("haproxy", "anubis-shoko"), ("haproxy", "anubis-mealprep"),
         ("haproxy", "grafana"), ("haproxy", "prom"), ("haproxy", "alerts"),
         ("anubis-shoko", "shoko"), ("anubis-mealprep", "mealprep")]

BOX_W, BOX_H, COL_W, ROW_H, PAD = 150, 56, 185, 74, 16


def canvas(x, y, w, h):
    """Service chain. Boxes coloured by their `up` query, arrows from EDGES."""
    elements, targets = [], []
    for i, (eid, col, row, label, up, rpm) in enumerate(CHAIN):
        if up:
            targets.append({"refId": "u" + str(i), "expr": up, "legendFormat": eid, "instant": True, "range": False})
        if rpm:
            targets.append({"refId": "r" + str(i), "expr": rpm, "legendFormat": eid + " rpm", "instant": True, "range": False})
        left, top = PAD + col * COL_W, PAD + row * ROW_H
        bg = {"field": eid, "fixed": "#D9D9D9"} if up else {"fixed": "#5a5a5a"}
        elements.append({
            "name": eid, "type": "rectangle",
            "config": {"align": "center", "valign": "top", "size": 12,
                       "color": {"fixed": "#ffffff"},
                       "text": {"mode": "fixed", "fixed": label},
                       "backgroundColor": bg},
            "background": {"color": bg},
            "border": {"color": {"fixed": "transparent"}, "width": 1},
            "placement": {"top": top, "left": left, "width": BOX_W, "height": BOX_H, "rotation": 0},
            "constraint": {"vertical": "top", "horizontal": "left"},
            "links": [],
            "connections": [{"source": {"x": 1, "y": 0}, "target": {"x": -1, "y": 0}, "targetName": t,
                             "color": {"fixed": "#9e9e9e"}, "size": {"fixed": 2},
                             "path": "straight", "vertices": []}
                            for s, t in EDGES if s == eid],
        })
        if rpm:
            elements.append({
                "name": eid + " rpm", "type": "metric-value",
                "config": {"align": "center", "valign": "middle", "size": 16,
                           "color": {"fixed": "#ffffff"},
                           "text": {"mode": "field", "field": eid + " rpm"}},
                "background": {"color": {"fixed": "transparent"}},
                "border": {"color": {"fixed": "transparent"}, "width": 0},
                "placement": {"top": top + 22, "left": left, "width": BOX_W, "height": BOX_H - 22, "rotation": 0},
                "constraint": {"vertical": "top", "horizontal": "left"},
                "links": [], "connections": [],
            })
    return {
        "id": 0, "type": "canvas", "title": "service chain (req/min, colour = up)",
        "gridPos": {"x": x, "y": y, "w": w, "h": h}, "datasource": DS, "targets": targets,
        "options": {"inlineEditing": False, "showAdvancedTypes": True, "panZoom": False, "infinitePan": False,
                    "root": {"name": "chain", "type": "frame", "elements": elements,
                             "background": {"color": {"fixed": "transparent"}},
                             "border": {"color": {"fixed": "transparent"}},
                             "constraint": {"vertical": "top", "horizontal": "left"},
                             "placement": {"top": 0, "left": 0, "width": 100, "height": 100}}},
        "fieldConfig": {"defaults": {"decimals": 0, "unit": "reqpm",
                                     "thresholds": {"mode": "absolute",
                                                    "steps": [{"color": "red", "value": None}, {"color": "green", "value": 1}]}},
                        "overrides": []},
    }


def panel(typ, title, x, y, w, h, targets, unit=None, mn=None, mx=None, dec=None,
          steps=None, mappings=None, overrides=None, instant=False):
    d = {}
    if unit: d["unit"] = unit
    if mn is not None: d["min"] = mn
    if mx is not None: d["max"] = mx
    if dec is not None: d["decimals"] = dec
    if steps: d["thresholds"] = {"mode": "absolute", "steps": [{"color": c, "value": v} for c, v in steps]}
    if mappings: d["mappings"] = mappings
    p = {"id": 0, "type": typ, "title": title, "gridPos": {"x": x, "y": y, "w": w, "h": h}, "datasource": DS,
         "targets": [{"refId": chr(65 + i), "expr": e, "legendFormat": l, "instant": instant, "range": not instant}
                     for i, (e, l) in enumerate(targets)],
         "fieldConfig": {"defaults": d, "overrides": overrides or []}, "options": {}}
    if typ == "stat":
        p["options"] = {"reduceOptions": {"calcs": ["lastNotNull"]}, "colorMode": "background", "graphMode": "none",
                        "textMode": "value_and_name", "justifyMode": "center", "text": {"titleSize": 18, "valueSize": 34}}
    return p


UPDOWN = [{"type": "value", "options": {"0": {"text": "DOWN", "color": "red"}, "1": {"text": "UP", "color": "green"}}}]
FREE_PCT_OVERRIDE = [{"matcher": {"id": "byName", "options": "free %"}, "properties": [
    {"id": "unit", "value": "percentunit"}, {"id": "decimals", "value": 0}, {"id": "min", "value": 0}, {"id": "max", "value": 1},
    {"id": "thresholds", "value": {"mode": "absolute", "steps": [
        {"color": "red", "value": None}, {"color": "yellow", "value": 0.1}, {"color": "green", "value": 0.25}]}}]}]

P, Y = [], [0]


def row(title):
    P.append({"id": 0, "type": "row", "title": title, "collapsed": False,
              "gridPos": {"x": 0, "y": Y[0], "w": 24, "h": 1}, "panels": []})
    Y[0] += 1


def add(p, h):
    P.append(p); return h


def endrow(h):
    Y[0] += h


row("overview")
add(panel("stat", "probes", 0, Y[0], 24, 6, [("probe_success", "{{name}}")], instant=True,
          steps=[("red", None), ("green", 1)], mappings=UPDOWN), 6)
endrow(6)
add(panel("stat", "cert days left", 0, Y[0], 12, 5,
          [("min((probe_ssl_earliest_cert_expiry - time()) / 86400)", "wildcard")], instant=True, dec=0,
          steps=[("red", None), ("yellow", 3), ("green", 30)]), 5)
add(panel("stat", "firing", 12, Y[0], 12, 5,
          [('count(ALERTS{alertstate="firing", alertname!="Watchdog"}) or vector(0)', "alerts")], instant=True, dec=0,
          steps=[("green", None), ("red", 1)]), 5)
endrow(5)

row("service chain")
CH_H = 14
P.append(canvas(0, Y[0], 24, CH_H))
endrow(CH_H)

row("web traffic (haproxy :8443)")
add(panel("timeseries", "requests / min per backend", 0, Y[0], 12, 7,
          [("rate(haproxy_backend_sessions_total[5m]) * 60", "{{backend}}")], unit="reqpm"), 7)
add(panel("timeseries", "responses / min by status", 12, Y[0], 12, 7,
          [("sum by (code) (rate(haproxy_backend_http_responses_total[5m])) * 60", "{{code}}")], unit="reqpm"), 7)
endrow(7)
add(panel("stat", "requests today", 0, Y[0], 8, 5,
          [("sum by (backend) (increase(haproxy_backend_sessions_total[1d]))", "{{backend}}")], instant=True, dec=0,
          steps=[("blue", None)]), 5)
add(panel("stat", "requests this week", 8, Y[0], 8, 5,
          [("sum by (backend) (increase(haproxy_backend_sessions_total[7d]))", "{{backend}}")], instant=True, dec=0,
          steps=[("blue", None)]), 5)
add(panel("timeseries", "response bytes / min", 16, Y[0], 8, 5,
          [("sum by (backend) (rate(haproxy_backend_bytes_out_total[5m])) * 60", "{{backend}}")], unit="bytes"), 5)
endrow(5)

for app in ("shoko", "mealprep"):
    row(app)
    add(panel("timeseries", "anubis-%s: proxied / challenged per min" % app, 0, Y[0], 12, 5,
              [('sum(rate(anubis_proxied_requests_total{app="%s"}[5m])) * 60' % app, "proxied"),
               ('sum(rate(anubis_challenges_issued{app="%s"}[5m])) * 60' % app, "challenged")], unit="reqpm"), 5)
    add(panel("timeseries", "%s backend: requests / min" % app, 12, Y[0], 12, 5,
              [('rate(haproxy_backend_sessions_total{backend="%s"}[5m]) * 60' % app, app),
               ('rate(haproxy_backend_http_responses_total{backend="%s",code="5xx"}[5m]) * 60' % app, "5xx")], unit="reqpm"), 5)
    endrow(5)

row("host: cpu & memory")
add(panel("timeseries", "cpu busy per core", 0, Y[0], 8, 7, [("termux_cpu_busy_ratio", "cpu{{cpu}}")],
          unit="percentunit", mn=0, mx=1), 7)
add(panel("timeseries", "load", 8, Y[0], 8, 7,
          [("termux_load1", "1m"), ("termux_load5", "5m"), ("termux_load15", "15m")]), 7)
add(panel("timeseries", "memory", 16, Y[0], 8, 7,
          [("node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes", "used"),
           ("node_memory_SwapTotal_bytes - node_memory_SwapFree_bytes", "swap used")], unit="bytes"), 7)
endrow(7)

row("host: power & thermal")
add(panel("timeseries", "battery", 0, Y[0], 8, 6, [("termux_battery_percent", "%")], unit="percent", mn=0, mx=100), 6)
add(panel("timeseries", "battery current (neg = charging)", 8, Y[0], 8, 6,
          [("termux_battery_current_amps", "A")], unit="amp"), 6)
add(panel("timeseries", "temperature", 16, Y[0], 8, 6,
          [("max(termux_cpu_temperature_celsius)", "cpu max zone"),
           ("termux_battery_temperature_celsius", "battery")], unit="celsius"), 6)
endrow(6)

row("storage")
for mp, label in (("/data", "/data (termux, shoko db, models)"),
                  ("/storage/EABF-DEDA", "/storage/EABF-DEDA (usb ssd, anime)")):
    free = 'max by (mountpoint) (node_filesystem_avail_bytes{mountpoint="%s"})' % mp
    pct = ('max by (mountpoint) (node_filesystem_avail_bytes{mountpoint="%s"} '
           '/ node_filesystem_size_bytes{mountpoint="%s"})' % (mp, mp))
    add(panel("timeseries", label, 0, Y[0], 16, 6, [(free, "free")], unit="bytes", mn=0), 6)
    add(panel("stat", "free", 16, Y[0], 8, 6, [(free, "free"), (pct, "free %")], instant=True, unit="bytes", dec=0,
              steps=[("green", None)], overrides=FREE_PCT_OVERRIDE), 6)
    endrow(6)
add(panel("timeseries", "usb ssd fuse latency (listdir, 1 MiB read)", 0, Y[0], 24, 6,
          [("termux_fuse_listdir_seconds", "listdir"), ("termux_fuse_read1m_seconds", "read 1 MiB")], unit="s", mn=0), 6)
endrow(6)

for i, p in enumerate(P, 1):
    p["id"] = i
json.dump({"uid": "poco", "title": "poco", "timezone": "browser", "refresh": "1m",
           "time": {"from": "now-24h", "to": "now"}, "schemaVersion": 39,
           "panels": P, "templating": {"list": []}},
          open("poco.json", "w"), indent=1)
print(len(P), "panels,", len([p for p in P if p["type"] == "row"]), "rows")
