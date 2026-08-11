# Session 01 — Foundation: Application + Docker + Kubernetes

> **Project:** Secure AI-Driven DevSecOps Platform  
> **Goal:** Establish the application, container image, Git repository, and baseline Kubernetes deployment before adding security automation, GitOps, runtime security, and AI.

## Objectives

By the end of Session 1:

- [x] Create the project repository
- [x] Create the Python application
- [x] Create health/readiness endpoints
- [x] Containerize the application with Docker
- [x] Build and run the image locally
- [x] Create Kubernetes namespace
- [x] Create Deployment
- [x] Create Service
- [x] Deploy to the AWS Kubernetes cluster
- [x] Verify Pods, ReplicaSets, Deployment and Service
- [x] Perform basic Kubernetes troubleshooting
- [x] Push the foundation to GitHub

---

# 1. Target Architecture

```text
Developer
    |
    v
 GitHub
    |
    v
 Python Flask Application
    |
    v
   Docker
    |
    v
Container Image
    |
    v
Kubernetes
    |
    +--> Deployment
    |       |
    |       +--> ReplicaSet
    |               |
    |               +--> Pods
    |
    +--> Service
```

Session 1 intentionally keeps the platform simple.

Security automation and GitOps are introduced in later sessions.

---

# 2. Repository Structure

```text
secure-ai-devsecops-platform/
│
├── app/
│   ├── app.py
│   └── requirements.txt
│
├── k8s/
│   ├── namespace.yaml
│   ├── deployment.yaml
│   └── service.yaml
│
├── docs/
│   └── session-01-foundation.md
│
├── Dockerfile
├── .dockerignore
├── .gitignore
└── README.md
```

---

# 3. Python Application

Example application:

```python
from flask import Flask

app = Flask(__name__)

@app.route("/")
def home():
    return "Secure AI DevSecOps Platform"

@app.route("/health")
def health():
    return {"status": "healthy"}

@app.route("/ready")
def ready():
    return {"status": "ready"}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
```

## Why `0.0.0.0`?

A container has its own network namespace. Binding Flask only to `127.0.0.1` would make the application reachable only inside the container.

Binding to:

```text
0.0.0.0:8080
```

allows traffic arriving through the container network to reach the application.

---

# 4. Dependencies

`requirements.txt`:

```text
Flask
```

Install locally if testing outside Docker:

```bash
python -m pip install -r app/requirements.txt
```

Run:

```bash
python app/app.py
```

Test:

```bash
curl http://localhost:8080/
curl http://localhost:8080/health
curl http://localhost:8080/ready
```

---

# 5. Dockerfile

Example:

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY app/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY app/ .

EXPOSE 8080

CMD ["python", "app.py"]
```

Build:

```bash
docker build -t secure-ai-devsecops-platform:1.0.0 .
```

Run:

```bash
docker run --rm -p 8080:8080 \
  secure-ai-devsecops-platform:1.0.0
```

Test:

```bash
curl http://localhost:8080/
```

---

# 6. Kubernetes Namespace

`k8s/namespace.yaml`:

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: secure-platform
```

Apply:

```bash
kubectl apply -f k8s/namespace.yaml
```

Verify:

```bash
kubectl get namespaces
```

---

# 7. Deployment

`k8s/deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: secure-ai-app
  namespace: secure-platform
spec:
  replicas: 2
  selector:
    matchLabels:
      app: secure-ai-app
  template:
    metadata:
      labels:
        app: secure-ai-app
    spec:
      containers:
        - name: secure-ai-app
          image: secure-ai-devsecops-platform:1.0.0
          ports:
            - containerPort: 8080
```

Apply:

```bash
kubectl apply -f k8s/deployment.yaml
```

Verify:

```bash
kubectl get deployments -n secure-platform
kubectl get replicasets -n secure-platform
kubectl get pods -n secure-platform -o wide
```

---

# 8. Service

`k8s/service.yaml`:

```yaml
apiVersion: v1
kind: Service
metadata:
  name: secure-ai-service
  namespace: secure-platform
spec:
  selector:
    app: secure-ai-app
  ports:
    - port: 80
      targetPort: 8080
  type: ClusterIP
```

Apply:

```bash
kubectl apply -f k8s/service.yaml
```

Verify:

```bash
kubectl get service -n secure-platform
```

---

# 9. Understand the Request Path

```text
Client
  |
  v
Service :80
  |
  v
Pod :8080
  |
  v
Flask
```

The Service selects Pods using:

```yaml
selector:
  app: secure-ai-app
```

The Pod must therefore contain:

```yaml
labels:
  app: secure-ai-app
```

---

# 10. Important Kubernetes Verification

```bash
kubectl get all -n secure-platform
```

```bash
kubectl describe deployment secure-ai-app \
  -n secure-platform
```

```bash
kubectl describe pods \
  -n secure-platform
```

```bash
kubectl get events \
  -n secure-platform \
  --sort-by=.lastTimestamp
```

Logs:

```bash
kubectl logs \
  -n secure-platform \
  deployment/secure-ai-app
```

---

# 11. Test the Service

Because the Service is `ClusterIP`, use port forwarding:

```bash
kubectl port-forward \
  -n secure-platform \
  service/secure-ai-service 8080:80
```

Then:

```bash
curl http://localhost:8080/
curl http://localhost:8080/health
curl http://localhost:8080/ready
```

---

# 12. Basic Troubleshooting

## Pod is Pending

```bash
kubectl describe pod <pod-name> \
  -n secure-platform
```

Check:

```text
Events
Scheduling
Resources
Taints
```

---

## Pod is CrashLoopBackOff

```bash
kubectl logs <pod-name> \
  -n secure-platform
```

Previous container:

```bash
kubectl logs <pod-name> \
  -n secure-platform \
  --previous
```

---

## ImagePullBackOff

```bash
kubectl describe pod <pod-name> \
  -n secure-platform
```

Typical cause in this project:

```text
Image exists only on the developer machine,
but the Kubernetes node cannot pull it.
```

This is an important production lesson.

In the next stages the image will be pushed to a container registry.

---

# 13. Deployment Rollout

Check rollout:

```bash
kubectl rollout status \
  deployment/secure-ai-app \
  -n secure-platform
```

History:

```bash
kubectl rollout history \
  deployment/secure-ai-app \
  -n secure-platform
```

Scale:

```bash
kubectl scale deployment secure-ai-app \
  --replicas=3 \
  -n secure-platform
```

Verify:

```bash
kubectl get pods -n secure-platform
```

---

# 14. Cleanup

```bash
kubectl delete -f k8s/service.yaml
kubectl delete -f k8s/deployment.yaml
kubectl delete -f k8s/namespace.yaml
```

---

# 15. Production Lessons

Session 1 establishes the baseline, but it is intentionally **not production hardened**.

Missing controls include:

- Non-root container
- Read-only filesystem
- Resource requests/limits
- Liveness probe
- Readiness probe
- SecurityContext
- NetworkPolicy
- Image vulnerability scanning
- Secret scanning
- Signed images
- Admission policies
- GitOps
- Runtime security
- Monitoring
- Centralized logging

These will be introduced progressively.

---

# 16. Completion Checklist

- [x] Application created
- [x] Dockerfile created
- [x] Image built
- [x] Container tested
- [x] Kubernetes namespace created
- [x] Deployment created
- [x] Service created
- [x] Pods verified
- [x] Logs inspected
- [x] Events inspected
- [x] Service tested
- [x] Deployment scaled
- [x] Basic troubleshooting performed
- [x] Changes pushed to GitHub

---

# 17. Evidence to Capture for GitHub/LinkedIn

Recommended screenshots:

1. GitHub repository structure
2. Successful Docker build
3. Running container
4. `kubectl get nodes`
5. `kubectl get pods -n secure-platform -o wide`
6. `kubectl get all -n secure-platform`
7. Application `/health` response
8. Kubernetes Service
9. Deployment rollout
10. Repository README

---

# Session 1 Result

At the end of Session 1:

```text
Python Application
       |
       v
     Docker
       |
       v
Kubernetes Deployment
       |
       v
     Service
       |
       v
     Running
```

The foundation is complete.

**Next:** Session 2 — CI/CD Security Pipeline.
