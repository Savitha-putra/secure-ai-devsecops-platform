```markdown
# Session 4 (Hours 7–8): DevSecOps Quality Gates & Artifact Registry Integration

> **Course:** Enterprise Jenkins & GitHub CI/CD Engineering  
> **Target Audience:** Freshers & Aspiring DevOps / Platform Engineers  
> **Prerequisites:** Completion of Sessions 1–3 (Jenkins Controller/Agent setup, Declarative `Jenkinsfile`, Multibranch Pipelines, Docker agents, and Credentials Binding).

---

## 1. Real-World Analogies & Architecture Diagrams

### Analogy 1: SonarQube Quality Gate vs. Trivy Container Scan (Airport Security vs. Customs Cargo Inspection)
* **SonarQube Static Code Analysis (SAST — Passenger Security Check):** Before a passenger even boards the plane, airport security scans their carry-on bag for prohibited items, weapons, or liquids. Similarly, **SonarQube** scans your raw source code *before* packaging it into a container—catching hardcoded passwords, SQL injection flaws, spaghetti code ("code smells"), and low unit test coverage. If the code fails the **Quality Gate**, the build stops immediately ("Shift-Left Security").
* **Trivy Container Vulnerability Scan (Customs Cargo Inspection):** Even if the passenger is clean, what if the shipping crate they packed their goods into has termites or hidden contraband? Your application runs inside a **Docker image** built on top of an OS base image (`ubuntu`, `alpine`, `debian`) and dozens of OS libraries (`openssl`, `curl`, `glibc`). **Trivy** X-rays the entire compiled Docker image for known CVEs (Common Vulnerabilities and Exposures) in both OS packages and application dependencies (`pom.xml`, `package.json`) before allowing it into your production registry.

### Analogy 2: Container Registry — Docker Hub & Amazon ECR (The Certified Warehouse)
* **Artifact Registry (Docker Hub / Amazon ECR):** Think of a certified, climate-controlled pharmaceutical warehouse. Production Kubernetes clusters are strictly forbidden from pulling random software off a developer's laptop. They only pull **cryptographically tagged, scanned, and verified** container images (`myapp:1.0.42-a1b2c3d`) stored inside a private registry like **Amazon ECR** (Elastic Container Registry) or **Docker Hub**.

---

### ASCII Architecture Diagram: End-to-End DevSecOps CI & Registry Pipeline

```text
+-----------------------------------------------------------------------------------+
|                        JENKINS DEVSECOPS PIPELINE EXECUTION                       |
|                                                                                   |
|  [1. Maven Build] ---> [2. SonarQube SAST] ---> [3. Quality Gate]                 |
|   (mvn test/pkg)        (mvn sonar:sonar)        (Pass / Fail Webhook)            |
|                                                           |                       |
|                                                           v (If PASSED)           |
|  [6. Push to Registry] <--- [5. Trivy Scan] <--- [4. Docker Build]                |
|   (Amazon ECR / Hub)         (Fail on CRITICAL)   (docker build -t tag)           |
+-----------|-------------------------|---------------------------------------------+
            |                         |
            v                         v (If CRITICAL CVE Found -> Abort Build!)
+-----------------------+   +-----------------------+
|   AMAZON ECR / HUB    |   |  PIPELINE ABORTED     |
|  (Verified Immutable  |   |  (Unpatched Image     |
|   Production Image)   |   |   Blocked from Prod)  |
+-----------------------+   +-----------------------+

```

---

## 2. Deep-Dive Concepts with Production Examples

### 2.1 Static Application Security Testing (SAST) with SonarQube

SonarQube evaluates your code against a **Quality Profile** (rules for Bugs, Vulnerabilities, Security Hotspots, and Code Smells) and enforces a **Quality Gate** (a pass/fail threshold, e.g., *0 New Bugs, 0 New Vulnerabilities, Coverage > 80%*).

#### How Jenkins & SonarQube Communicate

1. Jenkins runs `mvn sonar:sonar` using the **SonarQube Scanner for Jenkins** plugin (`withSonarQubeEnv('SonarQube-Server')`).
2. SonarQube processes the report asynchronously on its server.
3. Jenkins pauses at `waitForQualityGate abortPipeline: true` until SonarQube sends a webhook callback (`http://<jenkins-url>:8080/sonarqube-webhook/`) confirming **PASSED** or **FAILED**.

---

### 2.2 Container Vulnerability Scanning with Aqua Trivy

**Trivy** is an open-source, zero-configuration vulnerability scanner widely used across enterprise DevSecOps pipelines because it requires no background database daemon—it downloads its vulnerability DB automatically and scans images in seconds.

#### Key Trivy CLI Flags Used in CI Pipelines

* `trivy image --exit-code 1 --severity CRITICAL <image:tag>`
* **`--exit-code 1`**: Forces Trivy to return a non-zero exit code (`1`) if vulnerabilities matching the severity are found, automatically failing the Jenkins stage!
* **`--severity HIGH,CRITICAL`**: Filters noise so builds only fail on actionable, severe vulnerabilities rather than low-priority warnings.
* **`--ignore-unfixed`**: Ignores CVEs for which the Linux distro vendor has not yet released a patch (prevents blocking teams on unfixable upstream issues).



---

### 2.3 Container Registry Integration (Docker Hub vs. Amazon ECR)

| Feature | Docker Hub | Amazon ECR (Elastic Container Registry) |
| --- | --- | --- |
| **Authentication Method** | Static Username + Personal Access Token (`docker login`) | Temporary 12-hour IAM token via `aws ecr get-login-password` (or IAM Instance Profile) |
| **Image Naming Format** | `<dockerhub-user>/<repo>:<tag>` | `<aws-account-id>.dkr.ecr.<region>.amazonaws.com/<repo>:<tag>` |
| **Enterprise Usage** | Public open-source images & small teams | AWS-native enterprise workloads (private VPC endpoints, IAM RBAC, KMS encryption) |
| **Tag Immutability** | Paid plans only | Native toggle (**Immutable Tags** prevents overwriting `v1.0.0`) |

---

### 2.4 Complete Production DevSecOps `Jenkinsfile` (SonarQube + Docker + Trivy + Amazon ECR / Docker Hub)

```groovy
pipeline {
    agent {
        label 'docker-agent'
    }

    tools {
        maven 'Maven-3.9'
    }

    environment {
        APP_NAME        = 'order-service'
        GIT_SHORT_SHA   = sh(script: 'git rev-parse --short HEAD', returnStdout: true).trim()
        IMAGE_TAG       = "${env.BRANCH_NAME}-${env.BUILD_NUMBER}-${GIT_SHORT_SHA}"

        // Option A: Amazon ECR Configuration
        AWS_REGION      = 'ap-south-1'
        AWS_ACCOUNT_ID  = '123456789012'
        ECR_REGISTRY    = "${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"
        FULL_IMAGE_NAME = "${ECR_REGISTRY}/${APP_NAME}:${IMAGE_TAG}"

        // Option B: Docker Hub Alternative (Uncomment if using Docker Hub)
        // DOCKERHUB_REPO  = 'edgexdevops/order-service'
        // FULL_IMAGE_NAME = "${DOCKERHUB_REPO}:${IMAGE_TAG}"
    }

    options {
        timeout(time: 20, unit: 'MINUTES')
        buildDiscarder(logRotator(numToKeepStr: '10'))
    }

    stages {
        stage('1. Build & Unit Test') {
            steps {
                echo "Compiling and running unit tests for ${APP_NAME}..."
                sh 'mvn clean verify'
            }
        }

        stage('2. SonarQube Static Analysis (SAST)') {
            steps {
                // Injects SONAR_HOST_URL and SONAR_AUTH_TOKEN configured in Manage Jenkins -> System
                withSonarQubeEnv('SonarQube-Server') {
                    sh '''
                        mvn sonar:sonar \
                          -Dsonar.projectKey=${APP_NAME} \
                          -Dsonar.projectName=${APP_NAME}
                    '''
                }
            }
        }

        stage('3. SonarQube Quality Gate') {
            steps {
                // Pauses pipeline until SonarQube webhook reports PASS/FAIL
                timeout(time: 5, unit: 'MINUTES') {
                    waitForQualityGate abortPipeline: true
                }
            }
        }

        stage('4. Build Container Image') {
            steps {
                echo "Building Docker image: ${FULL_IMAGE_NAME}"
                sh '''
                    docker build -t "$FULL_IMAGE_NAME" .
                    docker tag "$FULL_IMAGE_NAME" "${ECR_REGISTRY}/${APP_NAME}:latest"
                '''
            }
        }

        stage('5. Trivy Container Vulnerability Scan') {
            steps {
                echo "Scanning ${FULL_IMAGE_NAME} for CRITICAL & HIGH CVEs..."
                sh '''
                    # Step A: Generate a readable summary table for console logs (non-blocking)
                    trivy image --severity HIGH,CRITICAL --no-progress "$FULL_IMAGE_NAME"

                    # Step B: Enforce DevSecOps Gate - Fail build if CRITICAL unfixed/fixed CVEs exist
                    trivy image --exit-code 1 --severity CRITICAL --ignore-unfixed --no-progress "$FULL_IMAGE_NAME"
                '''
            }
        }

        stage('6. Push Verified Image to Amazon ECR') {
            when {
                anyOf {
                    branch 'main'
                    branch 'staging'
                }
            }
            steps {
                withCredentials([
                    usernamePassword(
                        credentialsId: 'aws-ecr-creds',
                        usernameVariable: 'AWS_ACCESS_KEY_ID',
                        passwordVariable: 'AWS_SECRET_ACCESS_KEY'
                    )
                ]) {
                    sh '''
                        aws ecr get-login-password --region "$AWS_REGION" | \
                          docker login --username AWS --password-stdin "$ECR_REGISTRY"

                        docker push "$FULL_IMAGE_NAME"
                        docker push "${ECR_REGISTRY}/${APP_NAME}:latest"
                    '''
                }
            }
        }
    }

    post {
        always {
            // Remove local built images from agent to prevent disk exhaustion
            sh 'docker rmi "$FULL_IMAGE_NAME" || true'
            cleanWs()
        }
        success {
            echo "DEVSECOPS GATE PASSED: Verified image pushed to ${FULL_IMAGE_NAME}"
        }
        failure {
            echo "DEVSECOPS GATE BLOCKED: Pipeline failed quality, security, or build checks."
        }
    }
}

```

---

## 3. Industry Scenarios, Common Production Failures & DevOps Fixes

### How Enterprises Enforce DevSecOps Gates

* **Never Tag Only `latest`:** In production, relying on `:latest` breaks rollbacks because you cannot tell which commit is running in Kubernetes. Enterprises always tag images with `${BRANCH_NAME}-${BUILD_NUMBER}-${GIT_SHORT_SHA}` and enable **Tag Immutability** in Amazon ECR.
* **Base Image Hardening:** To pass Trivy scans consistently, teams replace bloated `ubuntu:latest` or `openjdk:17` images with minimal **Distroless** or **Alpine** base images (`eclipse-temurin:17-jre-alpine`), cutting CVE counts by 80–90%.

### 4 Common Production Failures & How DevOps Fixes Them

| # | Real-World Failure / Symptom | Root Cause in Industry | Step-by-Step DevOps Fix |
| --- | --- | --- | --- |
| **1** | **`waitForQualityGate` hangs for 5 minutes and times out** | SonarQube finished scanning, but its webhook failed to reach Jenkins (wrong URL, missing trailing slash, or firewall blocking port 8080). | 1. Open SonarQube UI $\rightarrow$ **Administration** $\rightarrow$ **Configuration** $\rightarrow$ **Webhooks**.<br>

<br>2. Ensure URL is `http://<jenkins-host>:8080/sonarqube-webhook/` (must include trailing `/`).<br>

<br>3. Check **Recent Deliveries** in SonarQube to verify HTTP `200`. |
| **2** | **`no basic auth credentials` or `denied: requested access to the resource is denied` during `docker push**` | Either `aws ecr get-login-password` expired (12-hour TTL), the IAM user lacks `ecr:BatchCheckLayerAvailability` / `ecr:PutImage`, or the ECR repository wasn't created beforehand. | 1. Unlike Docker Hub, **Amazon ECR does not auto-create repositories on push**—run `aws ecr create-repository --repository-name order-service` first.<br>

<br>2. Attach the `AmazonEC2ContainerRegistryPowerUser` IAM policy to your CI role. |
| **3** | **Trivy scan fails every build due to `toomanyrequests: You have reached your pull rate limit` or slow DB downloads** | Ephemeral Docker agents re-download the 40 MB Trivy vulnerability database from GitHub Container Registry (`ghcr.io`) on every single build. | 1. Mount a persistent cache directory on the agent (`-v /opt/trivy-cache:/root/.cache/trivy`) so Trivy only downloads delta updates once every 6 hours. |
| **4** | **Build agent disk fills up (`100% /var/lib/docker`) after 20 pipeline runs** | Every pipeline run builds a 300 MB Docker image and pushes it, leaving dangling `<none>:<none>` layers on the agent disk. | 1. Add `docker rmi "$FULL_IMAGE_NAME" |

---

## 4. Guided Hands-On Lab (Classroom Practical)

### Objective

Spin up a local SonarQube container, install Aqua Trivy on your Jenkins agent, configure SonarQube webhooks + Docker Hub/ECR credentials, and run a complete DevSecOps pipeline that blocks insecure code/images and pushes verified images to a container registry.

### Step-by-Step Instructions

1. **Start SonarQube Community Edition via Docker (On Host or Lab VM):**
```bash
docker run -d --name sonarqube \
  -p 9000:9000 \
  sonarqube:lts-community

```


* Wait ~60 seconds, open `http://<YOUR-IP>:9000`, log in with `admin` / `admin`, and update the password.
* Generate a token: **My Account** (top right) $\rightarrow$ **Security** $\rightarrow$ **Generate Tokens** (Type: *Global Analysis Token*, Name: `jenkins-sonar`). Copy the token!


2. **Configure SonarQube Webhook to Notify Jenkins:**
* In SonarQube UI: **Administration** $\rightarrow$ **Configuration** $\rightarrow$ **Webhooks** $\rightarrow$ **Create**.
* **Name:** `Jenkins`
* **URL:** `http://<JENKINS-IP>:8080/sonarqube-webhook/`


3. **Install Trivy on Your Jenkins Agent:**
```bash
sudo apt-get install -y wget apt-transport-https gnupg lsb-release
wget -qO - [https://aquasecurity.github.io/trivy-repo/deb/public.key](https://aquasecurity.github.io/trivy-repo/deb/public.key) | gpg --dearmor | sudo tee /usr/share/keyrings/trivy.gpg > /dev/null
echo "deb [signed-by=/usr/share/keyrings/trivy.gpg] [https://aquasecurity.github.io/trivy-repo/deb](https://aquasecurity.github.io/trivy-repo/deb) $(lsb_release -sc) main" | sudo tee -a /etc/apt/sources.list.d/trivy.list
sudo apt-get update && sudo apt-get install -y trivy
trivy --version

```


4. **Configure Jenkins Plugin & Credentials:**
* Install the **SonarQube Scanner** plugin in Jenkins (`Manage Jenkins` $\rightarrow$ `Plugins`).
* Add two credentials in `Manage Jenkins` $\rightarrow$ `Credentials`:
1. **Secret text** with ID `sonarqube-token` (paste your SonarQube token).
2. **Username with password** with ID `dockerhub-creds` (or `aws-ecr-creds`).


* Configure SonarQube Server in `Manage Jenkins` $\rightarrow$ `System` $\rightarrow$ **SonarQube installations**:
* **Name:** `SonarQube-Server`
* **Server URL:** `http://<SONARQUBE-IP>:9000`
* **Server authentication token:** Select `sonarqube-token`.




5. **Run & Test Intentional DevSecOps Gate Failures:**
* Add a `Dockerfile` to your GitHub repo (`FROM openjdk:11-jre-slim` — an intentionally older base image with known CRITICAL CVEs).
* Run the pipeline and verify **Stage 5 (Trivy Scan)** fails the build and prevents **Stage 6 (Registry Push)** from executing!
* Update the `Dockerfile` base image to `FROM eclipse-temurin:17-jre-alpine`, push to GitHub, and watch the pipeline pass all gates and push the clean image to your registry!



---

## 5. Take-Home Mini-Project (Portfolio / LinkedIn Ready)

### Project Title: *"Shift-Left DevSecOps CI Pipeline with SonarQube Quality Gates, Trivy CVE Blocking & Immutable Registry Push"*

#### Scenario

Your company's security team recently discovered that vulnerable base images and unreviewed code were reaching production. You are tasked with building an automated DevSecOps gatekeeper pipeline that blocks any commit failing static analysis or carrying `CRITICAL` container vulnerabilities.

#### Project Deliverables (Push to GitHub Repository `jenkins-devsecops-gatekeeper`)

1. **Application + Hardened `Dockerfile`:**
* Include a sample Java/Maven (or Node/Python) app with unit tests and a multi-stage `Dockerfile` using an Alpine/slim runtime base image.


2. **Production `Jenkinsfile`:**
* Implements all 6 stages: `Build & Unit Test`, `SonarQube SAST`, `Quality Gate`, `Docker Build`, `Trivy Scan` (exporting a JSON/table report and failing on `CRITICAL` CVEs), and `Registry Push` (Docker Hub or Amazon ECR) using `${BRANCH_NAME}-${BUILD_NUMBER}-${GIT_SHORT_SHA}` tagging.


3. **Security Audit Evidence (`README.md`):**
* Include a screenshot of a **blocked pipeline run** where Trivy caught `CRITICAL` CVEs in an unpatched base image (`ubuntu:18.04` or `openjdk:8`), proving Stage 6 (`Push`) was skipped.
* Include a screenshot of the **remediated green pipeline run** after upgrading the base image, alongside the published image tag in Docker Hub or Amazon ECR.



---

## 6. Knowledge Check: 10 Multiple-Choice Questions (MCQs)

1. **What is the primary difference between SonarQube and Aqua Trivy in a DevSecOps pipeline?**
* A) SonarQube scans Docker containers, while Trivy compiles Java source code
* B) SonarQube performs Static Application Security Testing (SAST) and code quality analysis on source code, whereas Trivy scans built container images and dependencies for known CVEs
* C) SonarQube replaces GitHub, while Trivy replaces Jenkins
* D) Both tools perform identical network firewall penetration testing


2. **Why does the `waitForQualityGate` step in a `Jenkinsfile` require a webhook configured inside SonarQube?**
* A) Because SonarQube cannot store scan results in its own database
* B) Because SonarQube processes analysis reports asynchronously in the background and uses the webhook to notify Jenkins when the final PASS/FAIL status is ready
* C) Because Jenkins cannot make outbound HTTP requests to SonarQube
* D) To automatically delete old Docker images


3. **Which Trivy CLI flag forces the command to return a non-zero exit status so Jenkins automatically fails the pipeline stage when vulnerabilities are detected?**
* A) `--fail-on-error`
* B) `--exit-code 1`
* C) `--abort-build true`
* D) `--strict-mode`


4. **What does the `--ignore-unfixed` flag do during a Trivy container scan?**
* A) Ignores all CRITICAL vulnerabilities regardless of patch availability
* B) Skips reporting vulnerabilities for which the upstream OS/package maintainer has not yet released a fix
* C) Automatically patches the Dockerfile and rebuilds the image
* D) Disables scanning of `/etc/passwd`


5. **Why is tagging production Docker images ONLY with `:latest` considered an anti-pattern in DevOps?**
* A) Docker Hub blocks images tagged with `:latest`
* B) `:latest` is mutable and gets overwritten on every build, making it impossible to trace which Git commit is running in production or roll back cleanly
* C) Kubernetes refuses to pull images tagged `:latest`
* D) Trivy cannot scan images tagged `:latest`


6. **How long is an Amazon ECR authorization token generated by `aws ecr get-login-password` valid?**
* A) 15 minutes
* B) 12 hours
* C) 30 days
* D) Forever (never expires)


7. **A Jenkins pipeline fails during `docker push` to Amazon ECR with `name unknown: The repository with name 'order-service' does not exist in the registry`. Why did this happen?**
* A) Your AWS password is incorrect
* B) Unlike Docker Hub, Amazon ECR requires the target repository to be explicitly created (`aws ecr create-repository`) before pushing images to it
* C) Trivy deleted the ECR repository
* D) ECR only accepts images built on Windows


8. **What happens in a `Jenkinsfile` when `waitForQualityGate abortPipeline: true` receives a `FAILED` status from SonarQube?**
* A) Jenkins logs a warning and continues pushing the Docker image anyway
* B) Jenkins immediately aborts the pipeline and marks the build status as `FAILED` (or `UNSTABLE` depending on gate config), preventing artifact deployment
* C) Jenkins automatically reverts the developer's commit on GitHub
* D) Jenkins restarts the SonarQube Docker container


9. **Why do DevOps engineers include `docker rmi "$FULL_IMAGE_NAME" || true` in the `post { always { ... } }` block of a CI pipeline?**
* A) To delete the image from Amazon ECR after pushing
* B) To clean up locally built container images from the Jenkins agent's disk so repeated builds do not cause `No space left on device` errors
* C) To clear the SonarQube quality gate cache
* D) To revoke AWS IAM credentials


10. **Which base image strategy helps development teams pass Trivy container scans with the smallest attack surface?**
* A) Using `ubuntu:latest` and installing all development compilers inside the final runtime image
* B) Using multi-stage Docker builds paired with minimal runtime images like `alpine` or `distroless`
* C) Disabling Trivy scanning on the `main` branch
* D) Running containers as `root` user



1. **B** — SonarQube analyzes your application's source code (bugs, vulnerabilities, test coverage), while Trivy inspects the packaged OS layers and libraries inside your Docker image.
2. **B** — SonarQube's background Compute Engine processes reports asynchronously; the webhook (`/sonarqube-webhook/`) wakes up the paused Jenkins pipeline once evaluation finishes.
3. **B** — By default, Trivy exits with code `0` even when vulnerabilities are found. Passing `--exit-code 1` causes Jenkins `sh` steps to fail immediately.
4. **B** — `--ignore-unfixed` prevents CI pipelines from grinding to a halt over zero-day or upstream distro vulnerabilities where no patch exists yet.
5. **B** — Immutable tags combining branch, build number, and Git commit SHA (`main-42-8f91a2b`) guarantee full traceability and instant rollbacks.
6. **B** — `aws ecr get-login-password` issues temporary credentials valid for 12 hours, which is why CI pipelines run `docker login` dynamically during the push stage.
7. **B** — Docker Hub auto-creates repositories on first push, whereas Amazon ECR requires pre-creating the repository via AWS Console, CLI, or Terraform.
8. **B** — Setting `abortPipeline: true` enforces the Quality Gate as a hard security/quality blocker before packaging or deployment stages execute.
9. **B** — Removing local image tags after pushing to the remote registry prevents build agents from running out of `/var/lib/docker` storage.
10. **B** — Multi-stage builds leave compilers (Maven/GCC) behind in the builder stage and ship only the compiled binary inside a tiny `alpine` or `distroless` runtime image.

---

## 7. Deep-Dive Research & Homework Questions (10 Investigative Prompts)

Complete these investigations at home before **Session 5** (our final capstone session!):

1. **Multi-Stage `Dockerfile` Optimization:** Write a two-stage `Dockerfile` for a Spring Boot Maven app where Stage 1 uses `maven:3.9.6-eclipse-temurin-17` to build the `.jar` and Stage 2 copies only the `.jar` into `eclipse-temurin:17-jre-alpine`. Run `trivy image` on both the builder image and final image and compare the CVE counts.
2. **Trivy SBOM (Software Bill of Materials) Generation:** Enterprises are increasingly required by compliance laws to publish an SBOM for every release. Research how to run `trivy image --format cyclonedx --output sbom.json <image>` and archive `sbom.json` in Jenkins.
3. **Trivy Secret & Misconfiguration Scanning:** Beyond container images, Trivy can scan filesystems and Infrastructure-as-Code (`trivy fs .` and `trivy config .`). Test running `trivy config Dockerfile` on a `Dockerfile` that uses `USER root` or `ADD http://...` and observe what security warnings Trivy flags.
4. **SonarQube Pull Request Decoration:** Research how SonarQube integrates with GitHub Pull Requests so developers see inline code-smell and security comments directly on their GitHub PR diff without ever logging into Jenkins or SonarQube.
5. **Amazon ECR Lifecycle Policies:** If your Jenkins pipeline pushes 50 tagged images per day to Amazon ECR, your AWS bill will grow steadily. Research **Amazon ECR Lifecycle Policies** and write a JSON rule that automatically expires untagged images after 1 day and keeps only the last 20 tagged images.
6. **AWS IAM Roles for EC2 / EKS (IRSA) vs. Static Access Keys:** In Session 4's lab we used `aws-ecr-creds` (static IAM keys). Research why enterprise AWS teams attach an **IAM Instance Profile** directly to the Jenkins Agent EC2 instance so `aws ecr get-login-password` works with **zero stored AWS keys** in Jenkins!
7. **Container Image Signing with Sigstore Cosign:** Once Trivy verifies an image is clean, how does Kubernetes verify that an image in ECR wasn't tampered with by an attacker? Research **Cosign (`cosign sign`)** and admission controllers like **Kyverno** or **OPA Gatekeeper**.
8. **SonarQube `sonar-project.properties` vs. CLI Flags:** For non-Maven projects (Node.js, Python, Go), Maven's `mvn sonar:sonar` doesn't exist. Research how `sonar-scanner` reads a `sonar-project.properties` file in the repository root.
9. **Handling False Positives in Trivy (`.trivyignore`):** Suppose Trivy flags a CVE in an unused library and the security team approves an exception. Research how creating a `.trivyignore` file in your Git repository suppresses specific CVE IDs cleanly with audit comments.
10. **Preparation for Session 5 (Shared Libraries & Capstone):** Imagine your company has 40 microservices, and all 40 have the *exact same* 120-line `Jenkinsfile` we just wrote. If you need to update the Trivy command across all 40 repos, how painful is that? Research **Jenkins Shared Libraries (`vars/*.groovy`)**—in Session 5, we will compress that 120-line `Jenkinsfile` into 10 clean lines!

```

<FollowUp label="Ready for me to generate Session 5 (Hours 9–10): Enterprise Architecture (Shared Libraries) & End-to-End Capstone?" query="Generate Session 5 (Hours 9–10): Enterprise Architecture (Shared Libraries) & End-to-End Capstone in clean GitHub Markdown without time-block durations, keeping all other sections from the Master Prompt."/>

<ElicitationsGroup message="Complete your 10-hour Jenkins & GitHub curriculum:">
  <Elicitation label="Generate Session 5 (Hours 9–10): Shared Libraries & Capstone" query="Generate Session 5 (Hours 9–10): Enterprise Architecture (Shared Libraries) & End-to-End Capstone in clean GitHub Markdown without time-block durations."/>
  <Elicitation label="Create a multi-stage Dockerfile for Session 4 Lab" query="Provide a complete Spring Boot / Java multi-stage Dockerfile and sample pom.xml with SonarQube plugin config for the Session 4 DevSecOps lab."/>
  <Elicitation label="Compare Amazon ECR, Docker Hub, GHCR, and JFrog Artifactory" query="Create a comparison table of Amazon ECR, Docker Hub, GitHub Container Registry (GHCR), and JFrog Artifactory for enterprise DevOps teams."/>
</ElicitationsGroup>

```
