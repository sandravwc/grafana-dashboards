# grafana-dashboards

Dashboards as code. `gen.py` is the source, JSON is build output (gitignored,
generated where Grafana runs). No UI editing; provisioned dashboards are
read-only there anyway.

```sh
./dev                              # watch gen.py: every save regenerates + copies poco.json, live in ~10 s
git commit -am "..." && git push   # pushes to github and the phone; post-receive hook checks out + runs gen.py
```

Reload the browser tab after a change; Grafana does not hot-swap an open
dashboard.

Phone setup (once):

```sh
git init --bare ~/git/grafana-dashboards.git
cp deploy/post-receive ~/git/grafana-dashboards.git/hooks/     # from a checkout
# workstation: push to both
git remote set-url --add --push origin https://github.com/sandravwc/grafana-dashboards.git
git remote set-url --add --push origin poco_f5_pro-phone-hyperos:git/grafana-dashboards.git
```

```txt
gen.py       panel definitions; CHAIN + EDGES at the top declare the service graph
dev          save-to-deploy loop
deploy/      post-receive hook for the phone
poco.json    generated (not in git): probes, cert, alerts, service chain, haproxy traffic per backend,
             per-app anubis, cpu/load/memory, battery/thermal, storage, fuse latency
```

The service chain is a Canvas panel built from `CHAIN`/`EDGES`: box colour
from a 0/1 query, req/min printed inside, arrows from the edge list. Declared,
not discovered — no tracing involved, and the topology only changes when
`~/haproxy.d` does. Adding a service = one line in `CHAIN`, one in `EDGES`.

Provisioning (see `sandravwc/monitoring`, `deploy/grafana/provisioning/dashboards/`):

```yaml
providers:
  - name: dashboards
    type: file
    options: { path: /data/data/com.termux/files/home/monitoring/dashboards }
```

Datasource uid expected: `prom` (Prometheus). Metrics used come from
node_exporter, blackbox_exporter, haproxy_exporter, anubis, and
`monitoring/deploy/textfile.sh` (`termux_*`).
