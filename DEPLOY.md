# Deployment Guide

This guide describes how to deploy the **HDHomeRun EPG to XMLTV** service using Kubernetes.
We utilize the generic [Stakater Application Helm Chart](https://github.com/stakater/stakater-charts/tree/master/docs/application) to simplify deployment.

## Prerequisites

-   Kubernetes Cluster 1.19+
-   Helm 3.0+
-   (Optional) ArgoCD or FluxCD for GitOps

## Configuration

The application requires the following key environment variables:

| Variable | Description | Recommended Value |
| :--- | :--- | :--- |
| `HDHOMERUN_HOST` | IP address of your HDHomeRun device | `10.0.1.2` |
| `HDHOMERUN_CACHE_DB_PATH` | Path to store the SQLite cache | `/data/epg_cache.db` |
| `HDHOMERUN_CACHE_ENABLED` | Enable caching | `true` |

> [!IMPORTANT]
> **Persistence**: To persist the EPG cache across restarts, we mount a volume to `/data` and configure `HDHOMERUN_CACHE_DB_PATH` to point to it.

## 1. Manual Deployment (Helm CLI)

You can deploy directly using the configurations in `deploy/helm/values.yaml`.

```bash
# Add Stakater repo
helm repo add stakater https://stakater.github.io/stakater-charts
helm repo update

# Install/Upgrade
helm upgrade --install hdhomerun-epg stakater/application \
  --namespace media --create-namespace \
  --values deploy/helm/values.yaml \
  --set deployment.image.tag=2025.12.0 # Replace with desired version
```

## 2. ArgoCD Deployment

We support ArgoCD using the **App of Apps** pattern or direct Application manifests.
The configuration uses `valuesObject` to embed values directly in the manifest.

**File**: `deploy/argocd/application.yaml`

```bash
kubectl apply -f deploy/argocd/application.yaml
```

## 3. FluxCD Deployment

For FluxCD users, use the provided `HelmRepository` and `HelmRelease` resources.

**Files**:
-   `deploy/flux/repo.yaml`: Registers Stakater chart repo.
-   `deploy/flux/release.yaml`: Defines the release.

```bash
kubectl apply -f deploy/flux/repo.yaml
kubectl apply -f deploy/flux/release.yaml
```

## Customizing Values

To enable Ingress or change resources, modify the respective sections in the YAML files.
See the [Stakater Application Chart Documentation](https://github.com/stakater/stakater-charts/tree/master/docs/application) for all available options.
