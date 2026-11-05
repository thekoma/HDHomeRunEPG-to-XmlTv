# Deploying to Kubernetes

The examples in [`deploy/`](deploy/) install the service with the [bjw-s app-template](https://bjw-s-labs.github.io/helm-charts/docs/app-template/) chart, version 5.3.0, which needs Kubernetes 1.28 or later. The Helm, Argo CD and Flux examples use the same values.

## Before you start

- Set `HDHOMERUN_HOST` to your tuner's address. The pod must be able to reach the tuner on your network.
- The examples use the `latest` image with `pullPolicy: Always`, so a pod gets the newest release when it starts. Run `kubectl rollout restart` to update a running pod. To choose when you upgrade, set `tag` to a [release](https://github.com/thekoma/HDHomeRunEPG-to-XmlTv/releases) such as `2026.11.1`.
- The pod runs as user 1001 with a read-only root filesystem. Two `emptyDir` volumes are writable: `/data` for the SQLite cache and `/tmp` for SQLite's temporary files.
- After a restart the cache fills up again on the first requests. To keep it across restarts, replace the `data` volume with a claim:

  ```yaml
  persistence:
    data:
      type: persistentVolumeClaim
      accessMode: ReadWriteOnce
      size: 1Gi
  ```

- The pod requests 192 MiB of memory with a 512 MiB limit. On a tuner with 162 channels it uses about 180 MiB once it has built the feed and the guide.
- The liveness and readiness probes call `/healthcheck` on port 8000.

## Helm

```bash
helm repo add bjw-s https://bjw-s-labs.github.io/helm-charts
helm repo update

helm upgrade --install hdhomerun-epg bjw-s/app-template --version 5.3.0 \
  --namespace media --create-namespace \
  --values deploy/helm/values.yaml
```

## Argo CD

[`deploy/argocd/`](deploy/argocd/) holds the `tvguide` namespace and an `Application` that installs the chart from the bjw-s Helm repository, with the values in `valuesObject`.

```bash
kubectl apply -k deploy/argocd
```

## Flux

[`deploy/flux/`](deploy/flux/) holds the `media` namespace, a `HelmRepository` for the bjw-s charts and the `HelmRelease`. It uses `source.toolkit.fluxcd.io/v1` and `helm.toolkit.fluxcd.io/v2`, so it needs Flux 2.3 or later.

```bash
kubectl apply -k deploy/flux
```

## Reaching the guide from outside the cluster

The values include an `ingress` entry that is turned off. The service has no authentication, so expose it only on your own network or behind an authenticating proxy. To turn the ingress on, set `enabled: true`, your ingress class and your host name:

```yaml
ingress:
  main:
    enabled: true
    className: nginx
    hosts:
      - host: tvguide.example.com
        paths:
          - path: /
            pathType: Prefix
            service:
              identifier: main
              port: http
```

## Moving from the Stakater chart

Earlier versions of these examples used the Stakater `application` chart. The two charts give the Deployment different selector labels, and Kubernetes does not let you change the selector of an existing Deployment. Delete the old Deployment, or uninstall the old release, before you install app-template under the same name.
