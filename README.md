# grafana-dashboards

Dashboards as code. `gen.py` is the source, `poco.json` is build output —
don't hand-edit the JSON, don't edit in the UI (provisioned dashboards are
read-only there anyway).

```sh
python3 gen.py && git commit -am "..." && git push
git -C ~/monitoring/dashboards pull      # on the Grafana host; file provider re-reads within 10 s
```

```txt
gen.py       panel definitions; CHAIN + EDGES at the top declare the service graph
poco.json    generated: probes, cert, alerts, service chain, haproxy traffic per backend,
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
