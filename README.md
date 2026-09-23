# grafana-dashboards

Grafana dashboard JSON, one directory per dashboard. Grafana provisions the
checkout read-only with `foldersFromFilesStructure`, so each directory
becomes a Grafana folder.

```txt
poco/    the Poco F5 Pro (Termux services, haproxy, host)
```

Deploy: the Grafana host is a push remote. Its `post-receive` hook checks
the tree out into the provisioned directory and Grafana reloads within 10 s.
Hook and provisioning config live in `sandravwc/monitoring` (`deploy/`).

```sh
git remote set-url --add --push origin https://github.com/sandravwc/grafana-dashboards.git
git remote set-url --add --push origin poco_f5_pro-phone-hyperos:git/grafana-dashboards.git
git push    # github + phone
```

Dashboards here are build output; each directory's README names its source.
