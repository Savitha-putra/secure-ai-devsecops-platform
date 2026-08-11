# Session 02 — CI/CD + Shift-Left Security

> **Project:** Secure AI-Driven DevSecOps Platform  
> **Goal:** Move security checks into GitHub Actions so insecure code, leaked secrets, vulnerable dependencies, and vulnerable container images can be detected before deployment.

---

# 1. Learning Objectives

By the end of this session you will understand and implement:

- GitHub Actions workflow structure
- Pull Request validation
- CI pipeline stages
- Gitleaks secret scanning
- Trivy filesystem/dependency scanning
- Docker image build in CI
- Trivy container image scanning
- Security gates
- GitHub Actions artifacts
- Failure investigation
- CI/CD security design

Target pipeline:

```text
Developer
    |
    v
Pull Request
    |
    v
GitHub Actions
    |
    +---- Unit Tests
    |
    +---- Gitleaks
    |
    +---- Trivy Filesystem
    |
    +---- Docker Build
    |
    +---- Trivy Image
    |
    v
Security Gate
    |
    v
Future Session:
Registry → Cosign → Argo CD
```

---

# 2. Why Are We Doing This?

A production team should not discover basic security problems after deployment.

Bad model:

```text
Developer
   |
   v
Build
   |
   v
Production
   |
   v
Security discovers problem
```

Better model:

```text
Developer
   |
   v
Pull Request
   |
   v
Automated Security
   |
   +--> Secret scan
   +--> Dependency scan
   +--> Image scan
   |
   v
Human Review
   |
   v
Deployment
```

This is **shift-left security**.

---

# 3. First: Verify the Application

From the repository root:

```bash
git status
```

Verify:

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
curl http://localhost:8080/health
curl http://localhost:8080/ready
```

---

# 4. Create GitHub Actions Directory

```bash
mkdir -p .github/workflows
```

Repository:

```text
.github/
└── workflows/
```

GitHub automatically discovers workflow YAML files under:

```text
.github/workflows/
```

---

# 5. Create CI Workflow

Create:

```text
.github/workflows/ci.yaml
```

Use:

```yaml
name: CI

on:
  push:
    branches:
      - main
  pull_request:

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout source
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r app/requirements.txt

      - name: Syntax check
        run: |
          python -m compileall app

      - name: Docker build
        run: |
          docker build \
            -t secure-ai-devsecops-platform:${{ github.sha }} .
```

---

# 6. Understand the Pipeline

```text
checkout
   |
   v
Python setup
   |
   v
Dependencies
   |
   v
Syntax validation
   |
   v
Docker build
```

The important concept:

> A CI runner is a temporary machine executing your automation.

The workflow does not run on your Kubernetes nodes.

---

# 7. Commit the Workflow

```bash
git add .github/workflows/ci.yaml
```

```bash
git commit -m "ci: add initial GitHub Actions pipeline"
```

```bash
git push
```

Open GitHub:

```text
Repository
   |
   v
Actions
   |
   v
CI
```

Verify the workflow succeeds.

---

# 8. Add Gitleaks

Gitleaks searches repositories for secrets such as:

```text
API keys
Passwords
Tokens
Private keys
Cloud credentials
```

Create:

```text
.github/workflows/security.yaml
```

Initial workflow:

```yaml
name: Security

on:
  push:
    branches:
      - main
  pull_request:

jobs:
  gitleaks:
    name: Secret Scan
    runs-on: ubuntu-latest

    steps:
      - name: Checkout source
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Run Gitleaks
        uses: gitleaks/gitleaks-action@v2
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

---

# 9. Why `fetch-depth: 0`?

GitHub Actions normally performs a shallow checkout.

```yaml
fetch-depth: 0
```

retrieves complete Git history.

This is useful for secret scanning because a secret may have existed in an earlier commit even if it was removed from the latest source.

Important production lesson:

> Removing a secret from the latest file does not mean the secret has disappeared from Git history.

If a real credential is exposed, rotate/revoke it.

Do not rely on deleting the Git line.

---

# 10. Test Gitleaks

Create a deliberately fake test secret only if you are using a disposable test branch.

For example:

```text
test-secret-value
```

Do not commit real AWS credentials or production secrets.

A better approach is to use Gitleaks' own test patterns or a controlled test branch.

The expected pipeline behavior is:

```text
Secret detected
     |
     v
Gitleaks
     |
     v
FAIL
     |
     v
PR blocked
```

---

# 11. Trivy Filesystem Scan

Add:

```yaml
  trivy-fs:
    name: Trivy Filesystem Scan
    runs-on: ubuntu-latest

    steps:
      - name: Checkout source
        uses: actions/checkout@v4

      - name: Trivy filesystem scan
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: fs
          scan-ref: .
          severity: HIGH,CRITICAL
          exit-code: 1
```

The important controls are:

```yaml
severity: HIGH,CRITICAL
exit-code: 1
```

This means:

```text
HIGH/CRITICAL vulnerability
        |
        v
Trivy
        |
        v
exit code 1
        |
        v
GitHub Actions job fails
```

---

# 12. Why `exit-code: 1` Matters

A scan that only reports vulnerabilities but never fails the pipeline is not necessarily a security gate.

We want:

```text
Detection
   |
   v
Decision
   |
   v
Pipeline gate
```

This is an important DevSecOps engineering distinction.

---

# 13. Docker Image Scan

Add another job:

```yaml
  trivy-image:
    name: Trivy Container Image Scan
    runs-on: ubuntu-latest

    steps:
      - name: Checkout source
        uses: actions/checkout@v4

      - name: Build image
        run: |
          docker build \
            -t secure-ai-devsecops-platform:${{ github.sha }} .

      - name: Scan image
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: secure-ai-devsecops-platform:${{ github.sha }}
          severity: HIGH,CRITICAL
          exit-code: 1
```

Pipeline:

```text
Source
  |
  v
Trivy FS
  |
  v
Docker Build
  |
  v
Trivy Image
  |
  v
Security Gate
```

---

# 14. Complete Security Workflow

The logical workflow now becomes:

```text
Pull Request
     |
     +----------------+
     |                |
     v                v
 Gitleaks          Trivy FS
     |                |
     +-------+--------+
             |
             v
        Docker Build
             |
             v
        Trivy Image
             |
             v
        Security Gate
```

---

# 15. Commit

```bash
git add .github/workflows/security.yaml
```

```bash
git commit -m "ci: add secret and container security scans"
```

```bash
git push
```

---

# 16. Verify GitHub Actions

Open:

```text
GitHub
  → Actions
  → Security
```

You should see jobs similar to:

```text
Secret Scan              PASS
Trivy Filesystem Scan    PASS
Trivy Image Scan         PASS
```

If a scan fails, do not simply disable it.

Investigate why.

---

# 17. Troubleshooting CI

## Gitleaks fails

Look for:

```text
Secret detected
```

Investigate:

```text
Which file?
Which commit?
What type of credential?
```

If it is a real credential:

```text
1. Revoke credential
2. Rotate credential
3. Remove exposure
4. Investigate Git history
5. Re-run scan
```

---

## Trivy fails

Read:

```text
Package
Installed version
Vulnerability
Severity
Fixed version
```

Then determine whether:

```text
Upgrade dependency
Update base image
Accept temporarily with documented risk
Replace dependency
```

Do not blindly suppress every finding.

---

# 18. Production Architecture

Eventually the pipeline becomes:

```text
Developer
    |
    v
GitHub PR
    |
    v
GitHub Actions
    |
    +--> Unit Tests
    |
    +--> Gitleaks
    |
    +--> Trivy FS
    |
    +--> Docker Build
    |
    +--> Trivy Image
    |
    v
Approval
    |
    v
Registry
    |
    v
Cosign
    |
    v
Argo CD
    |
    v
Kubernetes
```

---

# 19. Important Production Improvements

This session creates the learning baseline.

Before calling this enterprise production-ready, improve:

- Pin third-party GitHub Actions to trusted versions/SHAs
- Use dependency pinning
- Generate SBOM
- Sign images
- Verify signatures
- Add SAST where appropriate
- Add IaC scanning
- Add Kubernetes manifest scanning
- Protect main branch
- Require PR reviews
- Configure required status checks
- Restrict GitHub Actions permissions
- Use OIDC instead of long-lived cloud credentials
- Separate build and deployment permissions
- Separate environments
- Add artifact retention controls

---

# 20. GitHub Actions Security

A workflow should follow least privilege.

Example:

```yaml
permissions:
  contents: read
```

Do not automatically grant:

```text
contents: write
administration
packages: write
id-token: write
```

unless the workflow actually requires them.

Later, Cosign/AWS authentication may require narrowly scoped OIDC permissions.

---

# 21. Lab Exercises

## Lab 1

Run the CI workflow successfully.

## Lab 2

Make a harmless code change and observe the workflow.

## Lab 3

Create a controlled secret-scanning test.

## Lab 4

Introduce a vulnerable dependency in a disposable branch and observe Trivy.

## Lab 5

Change the Docker base image and compare scan results.

## Lab 6

Break the Dockerfile intentionally and troubleshoot the CI failure.

## Lab 7

Inspect GitHub Actions logs.

## Lab 8

Add `permissions: contents: read`.

## Lab 9

Create a Pull Request and observe required checks.

## Lab 10

Document one security failure and its remediation.

---

# 22. Session 2 Acceptance Criteria

The session is complete when:

- [ ] CI workflow runs successfully
- [ ] Python validation works
- [ ] Docker image builds in GitHub Actions
- [ ] Gitleaks runs
- [ ] Trivy filesystem scan runs
- [ ] Trivy image scan runs
- [ ] Security failures cause pipeline failure
- [ ] Pull Request triggers security checks
- [ ] Main branch protection is configured
- [ ] GitHub Actions permissions are minimized
- [ ] At least one controlled failure has been investigated
- [ ] Documentation is committed to GitHub

---

# 23. LinkedIn Evidence

Capture:

1. GitHub Actions successful pipeline
2. Gitleaks successful scan
3. Trivy filesystem result
4. Trivy image result
5. Failed security gate from controlled test
6. Pull Request checks
7. Repository workflow YAML
8. Architecture diagram

Suggested LinkedIn message:

> Built the CI security layer of my Secure AI-Driven DevSecOps Platform.
>
> The pipeline now performs automated testing, secret detection with Gitleaks, filesystem/dependency scanning with Trivy, container image scanning, and security gating through GitHub Actions.
>
> The objective is to prevent insecure artifacts from reaching the Kubernetes/GitOps deployment stage rather than discovering problems after deployment.
>
> Next: container registry, Cosign image signing and Argo CD GitOps.

---

# 24. Session 2 Deliverable

Commit:

```text
.github/workflows/ci.yaml
.github/workflows/security.yaml
docs/session-02-ci-security.md
```

Recommended commit:

```bash
git add .
git commit -m "ci: implement DevSecOps security pipeline"
git push
```

---

# Session 2 Outcome

You now have:

```text
GitHub
   |
   v
GitHub Actions
   |
   +--> Tests
   +--> Gitleaks
   +--> Trivy FS
   +--> Docker Build
   +--> Trivy Image
   |
   v
Security Gate
```

**Next session:** Container Registry + Cosign Image Signing.
