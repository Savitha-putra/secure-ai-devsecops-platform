```markdown
# Session 3 (Hours 5–6): Enterprise Agents, Secrets Management & Build Triggers

> **Course:** Enterprise Jenkins & GitHub CI/CD Engineering  
> **Target Audience:** Freshers & Aspiring DevOps / Platform Engineers  
> **Prerequisites:** Completion of Sessions 1 & 2 (Jenkins Controller + Agent setup, Declarative `Jenkinsfile`, Multibranch Pipelines).

---

## 1. Real-World Analogies & Architecture Diagrams

### Analogy 1: Ephemeral Docker Build Agents (Disposable Surgical Gloves vs. Reusable Kitchen Towels)
* **Static VM Agents (Reusable Kitchen Towels):** Imagine 10 different developers sharing one permanent Linux VM agent. Developer A installs Node.js 16 and leaves temporary files in `/tmp`. Developer B runs a Python script that upgrades a system library. Suddenly, Developer C's Java build breaks because the shared machine is polluted—and even when nobody is building code at 2:00 AM, you are still paying cloud bills for that idle VM.
* **Ephemeral Docker Build Agents (Disposable Surgical Gloves):** Every time a build starts, Jenkins puts on a brand-new, sterile pair of surgical gloves (**spins up a fresh Docker container** with the exact Maven/JDK/Node version needed). It performs the build in complete isolation, and the instant the build finishes, it throws the gloves in the bin (**destroys the container**). Zero environment drift, zero leftover junk, and zero idle server costs!

### Analogy 2: Secrets Management & Credential Binding (Hotel Keycards vs. Writing Your PIN on a Sticky Note)
* **Hardcoding Secrets in `Jenkinsfile`:** Writing your AWS secret key or GitHub token inside a `Jenkinsfile` is like writing your ATM PIN on the front of your debit card—anyone who views the Git repo (or the console log) steals your keys.
* **Jenkins Credentials + `withCredentials`:** Think of a hotel front desk vault. You store your master key safely inside Jenkins' encrypted vault (`credentials.xml`). When a build needs to log into Docker Hub or GitHub, Jenkins issues a temporary, single-use session variable (`$DOCKER_PASS`), **automatically masks (`****`)** any accidental printing of that value in the console logs, and revokes the variable the millisecond the step finishes.

### Analogy 3: Polling vs. Webhooks (Are We There Yet? vs. Doorbell)
* **SCM Polling (`H/5 * * * *`):** Sitting in the backseat of a car asking *"Are we there yet?"* every 5 minutes—even when the car hasn't moved. It wastes Jenkins CPU and GitHub API rate limits.
* **GitHub Webhooks:** Installing a **doorbell**. Jenkins sits completely idle using zero resources until a developer executes `git push` or opens a Pull Request. GitHub immediately rings Jenkins' doorbell (`HTTP POST /github-webhook/`), triggering the build within 1–2 seconds!

---

### ASCII Architecture Diagram: Ephemeral Docker Agents, Secrets & Webhook Flow

```text
+-----------------------------------------------------------------------------------+
|                        1. EVENT TRIGGER & CHATOPS LOOP                            |
|                                                                                   |
|   [Developer] -- git push --> [GitHub Repo] -- HTTP POST /github-webhook/ --+     |
|                                                                             |     |
|   [Slack / MS Teams] <--- slackSend (Build Status & Link) ---+              |     |
+--------------------------------------------------------------|--------------|-----+
                                                               |              v
+--------------------------------------------------------------|--------------------+
|                        2. JENKINS CONTROLLER (Orchestrator)  |                    |
|                                                              |                    |
|  +-----------------------------+    +------------------------+-----------------+  |
|  | Encrypted Credentials Vault |    | Docker Cloud Plugin (unix:///var/run/    |  |
|  | - github-pat (Secret Text)  |    |                      docker.sock)        |  |
|  | - aws-creds  (User/Pass)    |    +------------------------|-----------------+  |
|  | - prod-ssh   (SSH Key)      |                             | 3. Spin up on-demand
|  +--------------|--------------+                             v                    |
+-----------------|-----------------------------------------------------------------+
                  | 4. Inject masked env vars ($TOKEN)         |
                  |    (Console output prints: ****)           |
                  v                                            v
+-----------------------------------------------------------------------------------+
|                     3. EPHEMERAL DOCKER BUILD AGENT (Container)                   |
|                                                                                   |
|   [Container: jenkins/inbound-agent + maven + docker-cli]                         |
|   1. Created dynamically when build starts                                        |
|   2. Runs build in clean, isolated filesystem                                     |
|   3. Destroyed automatically in post { always } -> Zero leftover state!           |
+-----------------------------------------------------------------------------------+

```

---

## 2. Deep-Dive Concepts with Production Examples

### 2.1 Enterprise Secrets & Credentials Management

Jenkins encrypts all credentials at rest inside `$JENKINS_HOME/credentials.xml` using `master.key` and `hudson.util.Secret`.

#### Supported Credential Types (`Manage Jenkins` $\rightarrow$ `Credentials`)

1. **Secret text:** API keys, GitHub Personal Access Tokens (PATs), Slack Bot Tokens, SonarQube tokens.
2. **Username with password:** Docker Hub logins, Nexus/Artifactory credentials, database users.
3. **SSH Username with private key:** Connecting to remote Linux servers or cloning private Git repositories via SSH.
4. **Secret file:** Kubernetes `kubeconfig` files, GCP JSON service account keys, `.env` files.

#### How to Bind Credentials Safely (Without Leaking Secrets!)

There are two ways to inject secrets in a Declarative `Jenkinsfile`:

1. **`credentials()` helper inside `environment {}`:** Best when a credential is needed across multiple stages.
2. **`withCredentials([])` block inside `steps {}`:** Best for **least-privilege scoping**—the secret only exists in memory for the exact 3 lines of shell code that need it!

```groovy
pipeline {
    agent { label 'docker-agent' }

    environment {
        // Method 1: Pipeline-wide credential binding
        // Automatically creates SONAR_TOKEN_USR and SONAR_TOKEN_PSW if Username/Password,
        // or injects the raw string if Secret Text.
        GITHUB_TOKEN = credentials('github-ci-pat')
    }

    stages {
        stage('1. Safe Secret Usage (No Log Exposure)') {
            steps {
                // SAFE: Single quotes ('...') let Bash expand $GITHUB_TOKEN directly.
                // Jenkins log masker automatically replaces the value with **** in console output!
                sh '''
                    echo "Authenticating with GitHub API..."
                    curl -s -H "Authorization: token $GITHUB_TOKEN" [https://api.github.com/user](https://api.github.com/user) | grep login
                '''
            }
        }

        stage('2. Scoped Credential Binding (withCredentials)') {
            steps {
                // Method 2: Least-privilege scoped binding (only alive inside this block)
                withCredentials([
                    usernamePassword(
                        credentialsId: 'dockerhub-creds',
                        usernameVariable: 'DOCKER_USER',
                        passwordVariable: 'DOCKER_PASS'
                    ),
                    sshUserPrivateKey(
                        credentialsId: 'staging-server-ssh',
                        keyFileVariable: 'SSH_KEY_PATH',
                        usernameVariable: 'SSH_USER'
                    )
                ]) {
                    sh '''
                        echo "$DOCKER_PASS" | docker login -u "$DOCKER_USER" --password-stdin
                        ssh -i "$SSH_KEY_PATH" -o StrictHostKeyChecking=no "$SSH_USER@10.0.1.25" "uptime"
                    '''
                }
            }
        }
    }
}

```

> **CRITICAL SECURITY RULE (Single vs. Double Quotes):**
> * **NEVER write:** `sh "docker login -p ${DOCKER_PASS}"` (Double quotes force Groovy to interpolate the secret *before* passing it to Bash, bypassing Jenkins' log masking and exposing the password in process lists `ps aux`!).
> * **ALWAYS write:** `sh 'echo "$DOCKER_PASS" | docker login --password-stdin'` (Single quotes keep the secret inside Bash environment variables where Jenkins masks it as `****`).
> 
> 

---

### 2.2 Ephemeral Build Agents Using Docker Containers

There are **two ways** enterprises use Docker for ephemeral build agents:

#### Approach A: Dynamic Docker Cloud Agents (Docker Plugin)

Jenkins connects to a Docker daemon (`unix:///var/run/docker.sock` or TCP `tcp://docker-host:2376`) and dynamically spins up full Jenkins agent containers (`jenkins/inbound-agent`) whenever a job with a matching label enters the build queue. Once the build completes, the container is terminated.

#### Approach B: Per-Stage Docker Containers (`docker { image '...' }`)

If you already have an agent with Docker installed (`Docker Pipeline` plugin), you can spin up specialized tool containers *per stage* while sharing the same workspace volume!

```groovy
pipeline {
    // Top-level agent 'none' means each stage spins up its own lightweight container!
    agent none

    stages {
        stage('1. Build Java App (Maven Container)') {
            agent {
                docker {
                    image 'maven:3.9.6-eclipse-temurin-17'
                    label 'docker-host'
                    // Mount local .m2 cache so Maven doesn't re-download dependencies every build!
                    args '-v /root/.m2:/root/.m2'
                }
            }
            steps {
                sh 'mvn -version'
                sh 'mvn clean package -DskipTests'
            }
        }

        stage('2. Run Frontend Linter (Node.js Container)') {
            agent {
                docker {
                    image 'node:20-alpine'
                    label 'docker-host'
                }
            }
            steps {
                sh 'node -v && npm -v'
                sh 'echo "Running ESLint checks in isolated Node container..."'
            }
        }
    }
}

```

---

### 2.3 Build Triggers (GitHub Webhooks) & ChatOps Notifications (Slack / Teams)

#### Configuring GitHub Webhooks

1. In Jenkins Job Config $\rightarrow$ **Triggers** $\rightarrow$ Check **GitHub hook trigger for GITScm polling** (or automatic in Multibranch Pipelines).
2. In GitHub Repository $\rightarrow$ **Settings** $\rightarrow$ **Webhooks** $\rightarrow$ **Add webhook**:
* **Payload URL:** `http://<JENKINS-PUBLIC-URL>:8080/github-webhook/` *(Trailing slash `/` is mandatory!)*
* **Content type:** `application/json`
* **Secret:** Shared webhook secret configured in Jenkins Global Config (`Manage Jenkins` $\rightarrow$ `System` $\rightarrow$ `GitHub`).
* **Events:** Select *Just the push event* or *Let me select individual events* (`Pushes` + `Pull requests`).



#### Sending Rich Slack & Email Alerts in `post {}`

Using the **Slack Notification Plugin** (`slackSend`) and **Email Extension Plugin** (`emailext`):

```groovy
    post {
        success {
            slackSend(
                channel: '#devops-ci-alerts',
                color: 'good',
                message: "✅ *BUILD PASSED*: `${env.JOB_NAME}` (#${env.BUILD_NUMBER})\n*Branch:* `${env.BRANCH_NAME}`\n*Console:* <${env.BUILD_URL}|View Build>"
            )
        }
        failure {
            slackSend(
                channel: '#devops-ci-alerts',
                color: 'danger',
                message: "🚨 *BUILD FAILED*: `${env.JOB_NAME}` (#${env.BUILD_NUMBER})\n*Branch:* `${env.BRANCH_NAME}`\n*Action Required:* <${env.BUILD_URL}console|Inspect Failure Logs>"
            )
            emailext(
                to: 'devops-oncall@company.com',
                subject: "ALERT: Jenkins Build Failed - ${env.JOB_NAME} #${env.BUILD_NUMBER}",
                body: "Build #${env.BUILD_NUMBER} failed on branch${env.BRANCH_NAME}. View logs: ${env.BUILD_URL}console"
            )
        }
    }

```

---

## 3. Industry Scenarios, Common Production Failures & DevOps Fixes

### How Enterprises Scale Agents & Notifications

* **Zero Permanent Build VMs:** Large engineering orgs run zero permanent static build VMs. Every PR triggers an ephemeral Docker container (or Kubernetes Pod) that lives for 3 minutes and vanishes.
* **Alert Fatigue Prevention:** Teams route `success` notifications only for `main`/`production` deployments, while sending `failure` notifications on all branches so Slack channels aren't flooded with noise.

### 4 Common Production Failures & How DevOps Fixes Them

| # | Real-World Failure / Symptom | Root Cause in Industry | Step-by-Step DevOps Fix |
| --- | --- | --- | --- |
| **1** | **GitHub Webhook shows `403 No valid crumb was included in the request` or `302 Redirect**` | The Payload URL missed the trailing slash (`/github-webhook/`), or Jenkins CSRF protection blocked an unconfigured endpoint. | 1. Ensure GitHub Webhook URL ends with `/github-webhook/` (with the trailing slash).<br>

<br>2. Verify the **GitHub plugin** is installed (it exposes `/github-webhook/` as CSRF-exempt for valid GitHub HMAC signatures). |
| **2** | **`Got permission denied while trying to connect to the Docker daemon socket`** | The `jenkins` Linux user is not a member of the `docker` group on the agent host. | 1. Run `sudo usermod -aG docker jenkins` on the agent.<br>

<br>2. Restart the Jenkins agent process (`sudo systemctl restart jenkins` or reconnect agent) so group membership reloads. |
| **3** | **Localhost Jenkins cannot receive GitHub Webhooks during training/dev** | GitHub's cloud servers cannot reach `http://localhost:8080` or a private laptop IP behind home NAT. | 1. Use a secure tunnel tool like **ngrok** (`ngrok http 8080`) or **Cloudflare Tunnel** (`cloudflared tunnel --url http://localhost:8080`) to get a temporary public HTTPS URL for GitHub webhooks. |
| **4** | **Secret token leaked in Console Output despite using `credentials()**` | Developer printed the secret via `sh "echo ${MY_TOKEN}"` (Groovy double-quote interpolation) or Base64-encoded/reversed it. | 1. Replace double-quoted `sh "..."` with single-quoted `sh '...'`.<br>

<br>2. Immediately **revoke and rotate** the leaked token in GitHub/AWS—never assume deleting the build log is enough! |

---

## 4. Guided Hands-On Lab (Classroom Practical)

### Objective

Configure a dynamic Docker Cloud in Jenkins to spin up ephemeral build containers on demand, bind a GitHub Personal Access Token securely without log exposure, and trigger builds via GitHub Webhooks with Slack alerts.

### Step-by-Step Instructions

1. **Install Docker & Grant Permissions on the Agent Host:**
```bash
sudo apt update && sudo apt install -y docker.io
sudo systemctl enable --now docker
sudo usermod -aG docker jenkins
sudo usermod -aG docker $USER
sudo systemctl restart jenkins

```


2. **Install Required Plugins in Jenkins:**
* Navigate to **Manage Jenkins** $\rightarrow$ **Plugins** $\rightarrow$ **Available plugins**.
* Install:
* `Docker` (`docker-plugin`)
* `Docker Pipeline` (`docker-workflow`)
* `Slack Notification` (`slack`)




3. **Configure Ephemeral Docker Cloud (`Manage Jenkins` $\rightarrow$ `Clouds`):**
* Click **New cloud** $\rightarrow$ Name: `local-docker-cloud` $\rightarrow$ Type: **Docker** $\rightarrow$ **Create**.
* Expand **Docker Cloud details**:
* **Docker Host URI:** `unix:///var/run/docker.sock`
* Click **Test Connection** (Should display Docker version & API version).
* Check **Enabled**.


* Expand **Docker Agent templates** $\rightarrow$ Click **Add Docker Template**:
* **Labels:** `ephemeral-docker`
* **Enabled:** Checked
* **Name:** `jenkins-ephemeral-agent`
* **Docker Image:** `jenkins/inbound-agent:latest-jdk17`
* **Remote File System Root:** `/home/jenkins/agent`
* **Connect method:** `Attach Docker container` (or `Connect with JNLP` with WebSocket checked).
* **Pull strategy:** `Pull once and update latest`


* Click **Save**.


4. **Create a Secret Credential (`Manage Jenkins` $\rightarrow$ `Credentials`):**
* Click `(global)` $\rightarrow$ **Add Credentials**.
* **Kind:** `Secret text`
* **Secret:** Paste a GitHub Personal Access Token (or a test secret string like `ghp_SuperSecretDemoToken98765`).
* **ID:** `github-ci-pat`
* Click **Create**.


5. **Test Ephemeral Container + Masked Secrets + Webhook:**
* Update your `Jenkinsfile` to use `agent { label 'ephemeral-docker' }` and bind `github-ci-pat` using `credentials('github-ci-pat')`.
* Run `docker ps` in your terminal while the job runs—watch Jenkins dynamically spin up the container, run the build, mask the secret as `****` in Console Output, and automatically destroy the container when finished!



---

## 5. Take-Home Mini-Project (Portfolio / LinkedIn Ready)

### Project Title: *"Zero-Idle Ephemeral CI Pipeline with Webhook Triggers, Secret Masking & ChatOps Alerts"*

#### Scenario

Your DevOps lead wants to eliminate static build servers to cut cloud costs by 60% and enforce strict credential hygiene across all repositories. You must build an automated CI pipeline that spins up an ephemeral Docker container per build, authenticates securely with GitHub/Docker Hub using masked credentials, triggers automatically on `git push` via webhook, and posts rich status cards to Slack (or Discord/Teams webhook).

#### Project Deliverables (Push to GitHub Repository `jenkins-ephemeral-chatops-ci`)

1. **Custom Ephemeral Agent `Dockerfile` (Bonus Skill):**
* Build a lightweight custom image extending `jenkins/inbound-agent:latest-jdk17` with `maven`, `curl`, and `jq` pre-installed.


2. **Production `Jenkinsfile`:**
* Uses `agent { label 'ephemeral-docker' }`.
* Demonstrates **both** `environment { VAR = credentials('...') }` and scoped `withCredentials([...])` blocks without exposing any plaintext secrets in logs.
* Implements `post { success { slackSend(...) } failure { slackSend(...) } }`.


3. **Proof of Execution (`README.md`):**
* Screenshot of **GitHub Webhook Recent Deliveries** showing HTTP `200 OK` response from Jenkins.
* Screenshot of **Jenkins Console Output** proving:
1. Dynamic Docker container provisioning & termination.
2. Secret values masked as `****`.


* Screenshot of the **Slack channel notification** triggered by a build success and a simulated build failure.



---

## 6. Knowledge Check: 10 Multiple-Choice Questions (MCQs)

1. **What is the primary operational benefit of using ephemeral Docker build agents instead of static permanent VM agents?**
* A) Ephemeral containers never require a Jenkins Controller
* B) Each build starts in a clean, isolated, reproducible environment and terminates upon completion—eliminating workspace pollution and idle server costs
* C) Docker containers automatically write unit tests for Java applications
* D) Ephemeral agents store build logs permanently inside the container


2. **Why is `sh "echo ${MY_SECRET}"` (using double quotes) considered a severe security anti-pattern in a `Jenkinsfile`?**
* A) Double quotes cause a Groovy syntax error in Linux
* B) Groovy interpolates the secret string *before* passing the command to the shell, which can bypass Jenkins' log masking and expose the secret in process arguments
* C) `echo` cannot read environment variables in Bash
* D) Jenkins deletes the credential after double-quote usage


3. **Which `withCredentials` binding type should you use when authenticating with Docker Hub using both a username and password/token?**
* A) `string(credentialsId: '...', variable: '...')`
* B) `usernamePassword(credentialsId: '...', usernameVariable: '...', passwordVariable: '...')`
* C) `file(credentialsId: '...', variable: '...')`
* D) `certificate(credentialsId: '...', keystoreVariable: '...')`


4. **What is the mandatory endpoint path for configuring a GitHub Repository Webhook to trigger Jenkins?**
* A) `http://<jenkins-url>:8080/build-now`
* B) `http://<jenkins-url>:8080/github-webhook/`
* C) `http://<jenkins-url>:8080/api/json/webhook`
* D) `http://<jenkins-url>:8080/git/notifyCommit`


5. **Why are GitHub Webhooks superior to `Poll SCM (H/5 * * * *)` in enterprise environments?**
* A) Poll SCM only works with Subversion (SVN), not Git
* B) Webhooks trigger builds instantly (event-driven) without wasting CPU cycles and GitHub API rate limits on empty checks
* C) Webhooks automatically fix merge conflicts before building
* D) Poll SCM cannot detect branches other than `main`


6. **When configuring the Jenkins Docker Cloud plugin on a single Linux host, which Docker Host URI connects directly to the local Docker daemon?**
* A) `http://localhost:8080`
* B) `unix:///var/run/docker.sock`
* C) `ssh://root@127.0.0.1:22`
* D) `tcp://0.0.0.0:50000`


7. **A Jenkins pipeline running inside a Docker agent fails with `docker: command not found` or `permission denied` on `/var/run/docker.sock`. What is the cause?**
* A) The Jenkins Controller has 0 executors
* B) The container lacks the Docker CLI binary, or the `jenkins` user lacks read/write permissions on the Docker socket (`docker` group)
* C) Groovy version 3.0 does not support Docker
* D) The GitHub repository is private


8. **What happens if you define `agent none` at the top level of a Declarative `Jenkinsfile`?**
* A) The pipeline is disabled and cannot run
* B) Jenkins will not allocate a global agent; instead, every individual `stage` must declare its own `agent` (such as a specific Docker image)
* C) The pipeline runs directly on the Controller's Built-In Node
* D) All stages run simultaneously in parallel


9. **In the Slack Notification plugin (`slackSend`), which `color` parameter value displays a green vertical bar beside the build alert?**
* A) `success`
* B) `good`
* C) `green`
* D) `passed`


10. **You accidentally committed an AWS Secret Access Key into a `Jenkinsfile` and pushed it to GitHub. Even though you deleted the commit in a follow-up push, what MUST you do immediately?**
* A) Run `cleanWs()` in Jenkins
* B) Revoke and rotate the AWS key immediately in AWS IAM, because Git history and public scrapers already captured it
* C) Restart the Jenkins systemd service
* D) Switch the job from Multibranch to Freestyle



1. **B** — Ephemeral containers eliminate "works on yesterday's build cache" bugs and free compute resources immediately when builds end.
2. **B** — Always use single quotes (`sh 'echo "$MY_SECRET"'`) so the shell reads the masked environment variable directly without Groovy string expansion.
3. **B** — `usernamePassword` binds two separate environment variables (`usernameVariable` and `passwordVariable`) from a single Jenkins credential entry.
4. **B** — The GitHub plugin listens specifically on `/github-webhook/` (including the trailing slash).
5. **B** — Webhooks are push-based and instantaneous, whereas polling wastes network calls and hits GitHub API rate limits at scale.
6. **B** — `unix:///var/run/docker.sock` communicates directly with the local Linux Docker daemon via Unix domain socket.
7. **B** — To execute Docker commands inside an agent, the Docker CLI must be installed and the user must have access to the Docker daemon socket.
8. **B** — `agent none` is an industry pattern used when Stage 1 needs a `maven` container, Stage 2 needs a `node` container, and Stage 3 needs a `python` container.
9. **B** — `slackSend` uses Slack attachment color keywords: `good` (green), `warning` (yellow), and `danger` (red).
10. **B** — Once a secret touches a Git commit, consider it permanently compromised—always revoke and rotate it immediately.

---

## 7. Deep-Dive Research & Homework Questions (10 Investigative Prompts)

Complete these investigations at home before **Session 4** to master enterprise agent isolation and security:

1. **Docker Socket Security Risks:** Mounting `/var/run/docker.sock` inside a build container gives that container root-equivalent control over the host machine. Research **Rootless Docker**, **Sysbox**, and **Kaniko**—how do enterprises build container images safely without exposing the host Docker socket?
2. **Maven Dependency Caching in Ephemeral Containers:** If a fresh Maven container is created for every build, `mvn package` re-downloads 500 MB of `.jar` files from Maven Central every single time. Research how mounting a shared host volume (`-v /opt/maven-cache:/root/.m2`) or running **JFrog Artifactory / Sonatype Nexus** solves this bottleneck.
3. **Jenkins Credentials Scope (`Global` vs. `Folder`):** In a 500-engineer company, Team A should not be able to read Team B's AWS production keys. Research the **Folders Plugin** in Jenkins and how **Folder-Scoped Credentials** enforce multi-tenant isolation.
4. **External Secret Managers (HashiCorp Vault & AWS Secrets Manager):** Instead of storing secrets inside Jenkins' local `credentials.xml`, how does the **HashiCorp Vault Plugin** or **AWS Secrets Manager Credentials Provider** dynamically fetch short-lived secrets at build runtime?
5. **GitHub Pull Request Builder / Merge Queue Triggers:** In a Multibranch Pipeline, what is the difference between discovering **Branches** (`feature/*`) versus discovering **Pull Requests (PRs)** (`PR-42`)? Why do teams build the *merged result* (`PR-42-merge`) before allowing a PR to merge?
6. **Webhook Replay & Debugging in GitHub:** Open any repository's **Settings $\rightarrow$ Webhooks $\rightarrow$ Recent Deliveries**. Inspect the `X-GitHub-Event` and `X-Hub-Signature-256` headers. How does Jenkins verify that an incoming webhook actually came from GitHub and not an attacker?
7. **Quiet Period & `disableConcurrentBuilds()`:** Suppose a developer pushes 4 rapid commits in 10 seconds. Research how `options { quietPeriod(15) }` and `disableConcurrentBuilds(abortPrevious: true)` prevent wasted builds and race conditions.
8. **Microsoft Teams & Custom Webhook Alerts:** If your organization uses Microsoft Teams instead of Slack, how can you send rich JSON Adaptive Cards from a `Jenkinsfile` using either the **Office 365 Connector Plugin** or a standard `curl -X POST` step in `post {}`?
9. **Container Resource Limits (`--memory` & `--cpus`):** How do you configure a Docker Agent Template in Jenkins so a runaway Java build cannot consume 100% of the host VM's RAM and crash neighboring containers?
10. **Preparation for Session 4:** Research **SonarQube Quality Gates** and **Aqua Trivy** (`trivy image --severity HIGH,CRITICAL`). Understand the difference between **SAST** (Static Application Security Testing on source code) and **Container Image Vulnerability Scanning**!

```

<FollowUp label="Ready for me to generate Session 4 (Hours 7–8): DevSecOps Quality Gates & Artifact Registry Integration?" query="Generate Session 4 (Hours 7–8): DevSecOps Quality Gates & Artifact Registry Integration in clean GitHub Markdown without time-block durations, keeping all other sections from the Master Prompt."/>

<ElicitationsGroup message="Continue your 10-hour Jenkins & GitHub curriculum:">
  <Elicitation label="Generate Session 4 (Hours 7–8) now" query="Generate Session 4 (Hours 7–8): DevSecOps Quality Gates & Artifact Registry Integration in clean GitHub Markdown without time-block durations."/>
  <Elicitation label="Generate Session 5 (Hours 9–10): Shared Libraries & Capstone" query="Generate Session 5 (Hours 9–10): Enterprise Architecture (Shared Libraries) & End-to-End Capstone in clean GitHub Markdown without time-block durations."/>
  <Elicitation label="Create a custom Dockerfile for Ephemeral Jenkins Agents" query="Provide a production-ready Dockerfile extending jenkins/inbound-agent with Maven, Docker CLI, Trivy, and AWS CLI pre-installed for Session 3 and 4 labs."/>
</ElicitationsGroup>

```
