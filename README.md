# grafana-dashboards

Grafana dashboards as JSON, provisioned from a clone of this repo. Edit the
JSON (or edit in the UI, export, paste back — provisioned dashboards are
read-only in the UI), push, `git pull` on the Grafana host; the file provider
re-reads every 10 s.

```txt
poco.json    the Poco: probes, cert, alerts, haproxy traffic per backend, per-app anubis, cpu/load/memory, battery/thermal, storage
```

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
