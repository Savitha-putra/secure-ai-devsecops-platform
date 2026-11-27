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

# **Session 4 – Jenkins Build Parameters, Environment Variables and Credentials**



Jenkins Training – Session 4

Beginner to Intermediate



**Duration:** 2 hours\
**Platform:** Prepare.sh Jenkins Playground (`prepare.sh/jenkins`)\
**Level:** Freshers / Beginners\
**Previous session:** Jenkins and GitHub Integration

## **1. Session objectives**

By the end of this session, students should understand:

1. What Jenkins build parameters are.
2. How to pass values to a Jenkins pipeline at runtime.
3. What environment variables are and why they are useful.
4. The difference between parameters and environment variables.
5. How Jenkins credentials work.
6. Why passwords, tokens and API keys must never be hardcoded.
7. How these concepts are used in real DevOps CI/CD pipelines.

## **2. What are Jenkins build parameters?**

Imagine you are running a software deployment pipeline.

Today, you want to deploy your application to the Development environment. Tomorrow, you want to deploy the same application to Testing.

Instead of creating two different pipelines, you can create one pipeline and ask the user to select the environment before starting the build.

That is the purpose of **Build Parameters**.

### **Real-world example**

**A deployment pipeline**

**User starts Jenkins build**

Select deployment environment

Development

Selected

Testing

Available

Production

Available

**Jenkins pipeline**

- Reads the selected environment
- Runs build and tests
- Executes the corresponding deployment stage

## **3. Types of Jenkins parameters**

Common parameter types include:

| Parameter      | Purpose                 | Example          |
| -------------- | ----------------------- | ---------------- |
| `string`       | Accepts text            | Application name |
| `booleanParam` | Accepts true/false      | Run tests?       |
| `choice`       | Select from options     | Dev, QA, Prod    |
| `password`     | Accepts sensitive input | Password         |
| `text`         | Accepts multiple lines  | Release notes    |

## **4. Practical 1 – Create your first parameterized pipeline**

**Objective:** Allow users to enter an application name when starting a build.

Create a Pipeline job and use this Jenkinsfile:

```
pipeline {
    agent any

    parameters {
        string(
            name: 'APP_NAME',
            defaultValue: 'my-java-app',
            description: 'Enter application name'
        )
    }

    stages {
        stage('Display Application') {
            steps {
                echo "Application Name: ${params.APP_NAME}"
            }
        }
    }
}
```

### **Understand the code**

- `parameters`: Defines inputs required before the build starts.
- `string`: Creates a text input.
- `name`: Defines the parameter name.
- `defaultValue`: Provides a default value.
- `params.APP_NAME`: Reads the value entered by the user.

**Student task:**

1. Run the pipeline.
2. Enter `student-management-app`.
3. Execute the build.
4. Check the Console Output.

Expected output:

```
Application Name: student-management-app
Finished: SUCCESS
```

## **5. Practical 2 – Environment selection using choice parameter**

**Objective:** Select Development, QA or Production at runtime.

```
pipeline {
    agent any

    parameters {
        choice(
            name: 'ENVIRONMENT',
            choices: ['DEV', 'QA', 'PROD'],
            description: 'Select deployment environment'
        )
    }

    stages {
        stage('Show Environment') {
            steps {
                echo "Selected environment: ${params.ENVIRONMENT}"
            }
        }

        stage('Deploy to DEV') {
            when {
                expression {
                    params.ENVIRONMENT == 'DEV'
                }
            }
            steps {
                echo 'Deploying application to Development'
            }
        }

        stage('Deploy to QA') {
            when {
                expression {
                    params.ENVIRONMENT == 'QA'
                }
            }
            steps {
                echo 'Deploying application to QA'
            }
        }

        stage('Deploy to PROD') {
            when {
                expression {
                    params.ENVIRONMENT == 'PROD'
                }
            }
            steps {
                echo 'Deploying application to Production'
            }
        }
    }
}
```

**Student task:**

Run the pipeline three times:

- First run: DEV
- Second run: QA
- Third run: PROD

Observe which stage executes in each build.

**Production understanding:** A single deployment pipeline can support multiple environments. Real production deployments should also include approval controls and access restrictions.

## **6. Practical 3 – Boolean parameter**

**Objective:** Allow users to decide whether automated tests should run.

```
pipeline {
    agent any

    parameters {
        booleanParam(
            name: 'RUN_TESTS',
            defaultValue: true,
            description: 'Should automated tests run?'
        )
    }

    stages {
        stage('Build') {
            steps {
                echo 'Building application...'
            }
        }

        stage('Testing') {
            when {
                expression {
                    params.RUN_TESTS == true
                }
            }
            steps {
                echo 'Executing automated tests...'
            }
        }

        stage('Complete') {
            steps {
                echo 'Pipeline completed'
            }
        }
    }
}
```

**Student task:** Execute it twice, once with the checkbox enabled and once disabled.

Understand how a boolean parameter controls pipeline execution.

## **7. What are environment variables?**

Environment variables are values that can be accessed by processes running during a build.

For example:

- Application name
- Build number
- Workspace directory
- Deployment environment
- Java installation path

Jenkins provides built-in environment variables.

| Variable       | Meaning                           |
| -------------- | --------------------------------- |
| `BUILD_NUMBER` | Current build number              |
| `BUILD_ID`     | Current build identifier          |
| `JOB_NAME`     | Jenkins job name                  |
| `WORKSPACE`    | Current workspace path            |
| `BUILD_URL`    | URL of the build                  |
| `JENKINS_URL`  | Jenkins server URL, if configured |

## **8. Practical 4 – Display Jenkins built-in environment variables**

```
pipeline {
    agent any

    stages {
        stage('Jenkins Environment') {
            steps {
                echo "Build Number: ${env.BUILD_NUMBER}"
                echo "Build ID: ${env.BUILD_ID}"
                echo "Job Name: ${env.JOB_NAME}"
                echo "Workspace: ${env.WORKSPACE}"
                echo "Build URL: ${env.BUILD_URL}"
            }
        }
    }
}
```

**Student task:**

1. Run the pipeline three times.
2. Observe the build number.
3. Compare the output between builds.
4. Identify which values change and which remain the same.

Note: Some environment variables may be empty or unavailable in a particular playground.

## **9. Practical 5 – Define custom environment variables**

You can define your own environment variables inside a Jenkins pipeline.

```
pipeline {
    agent any

    environment {
        APP_NAME = 'employee-portal'
        ENVIRONMENT = 'DEV'
        VERSION = '1.0'
    }

    stages {
        stage('Display Configuration') {
            steps {
                echo "Application: ${env.APP_NAME}"
                echo "Environment: ${env.ENVIRONMENT}"
                echo "Version: ${env.VERSION}"
            }
        }

        stage('Build') {
            steps {
                echo "Building ${env.APP_NAME} version ${env.VERSION}"
            }
        }
    }
}
```

**Understand this:**

- `environment` defines variables.
- `APP_NAME` stores the application name.
- `env.APP_NAME` reads the variable inside the pipeline.

## **10. Practical 6 – Combine parameters and environment variables**

**Objective:** Let users choose the deployment environment and application version.

```
pipeline {
    agent any

    parameters {
        choice(
            name: 'DEPLOY_ENV',
            choices: ['DEV', 'QA', 'PROD'],
            description: 'Select environment'
        )

        string(
            name: 'APP_VERSION',
            defaultValue: '1.0.0',
            description: 'Enter application version'
        )
    }

    environment {
        APP_NAME = 'payment-service'
    }

    stages {
        stage('Build Information') {
            steps {
                echo "Application: ${env.APP_NAME}"
                echo "Version: ${params.APP_VERSION}"
                echo "Environment: ${params.DEPLOY_ENV}"
            }
        }

        stage('Deployment Simulation') {
            steps {
                echo "Deploying ${env.APP_NAME}"
                echo "Version: ${params.APP_VERSION}"
                echo "Target: ${params.DEPLOY_ENV}"
            }
        }
    }
}
```

**Production relevance:** This is a simplified example of how release teams pass application versions and target environments into a shared deployment pipeline.

## **11. Jenkins Credentials – Why are they important?**

Imagine your Jenkins pipeline needs to download source code from a private GitHub repository.

GitHub requires authentication.

You could put your GitHub token directly into your Jenkinsfile, but this is dangerous.

Never do this:

```
// WRONG: Never hardcode secrets
GITHUB_TOKEN = 'ghp_your-secret-token'
```

Why is this dangerous?

- Anyone with repository access may see the token.
- The token may appear in logs.
- The token may be accidentally committed to GitHub.
- An attacker could use the token to access your repository.

Instead, Jenkins provides a Credentials feature.

[Jenkins For Test Automation Guide](https://images.openai.com/static-rsc-4/nGAquPGSY2SfSJHz9TLRLGAIbA5yJZbKM772dHD546ZE8pWchxTlFxtGXJMj3j8cruqcXS2XTPDud4nNP1nqBtfpth7XaU9YTN8ezcasTDjxAtF5b9OgrHZyEKjMBhZ63CzuM2mrp-pWcVerDH4B5GtKr2UVhhr94LEKU0QFFfw?purpose=inline)

[saucelabs.com](https://saucelabs.com/resources/blog/how-to-use-jenkins-for-test-automation?utm_source=chatgpt.com)

### **Common credential types**

| Type                          | Usage                                 |
| ----------------------------- | ------------------------------------- |
| Username with password        | Git authentication                    |
| Secret text                   | GitHub Personal Access Token          |
| Secret file                   | Certificates or configuration files   |
| SSH username with private key | SSH-based Git authentication          |
| Certificate                   | TLS/client certificate authentication |

## **12. Practical 7 – Understand credential IDs**

In a real Jenkins installation:

1. Open **Manage Jenkins**.
2. Open **Credentials**.
3. Select the appropriate credentials store and domain.
4. Click **Add Credentials**.
5. Select the credential type.
6. Enter the secret.
7. Assign an ID, such as `github-token`.
8. Save it.

The Jenkinsfile refers to the credential ID, not the actual secret.

Example:

```
pipeline {
    agent any

    stages {
        stage('Use GitHub Token') {
            steps {
                withCredentials([
                    string(
                        credentialsId: 'github-token',
                        variable: 'GITHUB_TOKEN'
                    )
                ]) {
                    echo 'GitHub credential has been loaded'
                }
            }
        }
    }
}
```

Important:

- The credential must exist in Jenkins.
- The Credentials Binding plugin is commonly required for `withCredentials`.
- This example deliberately does not print the token.
- Do not assume Prepare.sh provides credential-management access. If it does not, study the Jenkinsfile and perform this exercise on a separate Jenkins installation.

## **13. Practical 8 – Use credentials for GitHub authentication**

Example for a private GitHub repository using Jenkins username/password credentials, where the password field contains a GitHub Personal Access Token.

```
pipeline {
    agent any

    stages {
        stage('Checkout Private Repository') {
            steps {
                git branch: 'main',
                    credentialsId: 'github-credentials',
                    url: 'https://github.com/YOUR-USERNAME/private-repo.git'
            }
        }
    }
}
```

Replace:

- `YOUR-USERNAME` with your GitHub username.
- `private-repo` with your private repository name.
- `github-credentials` with your Jenkins credential ID.

Never place the real GitHub token in the Jenkinsfile.

## **14. Practical 9 – Create a build version using environment variables**

**Objective:** Generate a version identifier using Jenkins build information.

```
pipeline {
    agent any

    environment {
        APP_NAME = 'student-app'
    }

    stages {
        stage('Generate Build Version') {
            steps {
                script {
                    def version = "1.0.${env.BUILD_NUMBER}"

                    echo "Application: ${env.APP_NAME}"
                    echo "Generated Version: ${version}"
                }
            }
        }
    }
}
```

Expected example:

```
Application: student-app
Generated Version: 1.0.1
```

The build number will increase as new builds run.

## **15. Practical 10 – Mini DevOps CI/CD pipeline**

**Objective:** Combine parameters, environment variables and build stages into one pipeline.

```
pipeline {
    agent any

    parameters {
        choice(
            name: 'DEPLOY_ENV',
            choices: ['DEV', 'QA', 'PROD'],
            description: 'Select target environment'
        )

        string(
            name: 'APP_VERSION',
            defaultValue: '1.0.0',
            description: 'Application version'
        )

        booleanParam(
            name: 'RUN_SECURITY_SCAN',
            defaultValue: true,
            description: 'Run security scan simulation'
        )
    }

    environment {
        APP_NAME = 'banking-application'
        BUILD_OWNER = 'DevOps-Team'
    }

    stages {
        stage('Build Information') {
            steps {
                echo "Application: ${env.APP_NAME}"
                echo "Version: ${params.APP_VERSION}"
                echo "Environment: ${params.DEPLOY_ENV}"
                echo "Build Number: ${env.BUILD_NUMBER}"
                echo "Build Owner: ${env.BUILD_OWNER}"
            }
        }

        stage('Build') {
            steps {
                echo 'Building application...'
            }
        }

        stage('Security Scan') {
            when {
                expression {
                    params.RUN_SECURITY_SCAN == true
                }
            }
            steps {
                echo 'Running security scan simulation...'
                echo 'No real security scanner is connected.'
            }
        }

        stage('Deploy') {
            steps {
                echo "Deploying ${env.APP_NAME}"
                echo "Version: ${params.APP_VERSION}"
                echo "Target: ${params.DEPLOY_ENV}"
            }
        }

        stage('Final Status') {
            steps {
                echo 'CI/CD pipeline completed successfully.'
            }
        }
    }
}
```

**Important:** The security scan and deployment stages above are simulations. They do not connect to Checkmarx, SonarQube, Black Duck or an actual deployment environment.

## **16. Student assignment**

Ask each student to create a pipeline named:

`session-04-jenkins-parameters-credentials`

The pipeline must:

- Accept an application name.
- Accept an application version.
- Provide DEV, QA and PROD choices.
- Include a checkbox to enable or disable security scanning.
- Display Jenkins build number and job name.
- Display the selected application configuration.
- Execute only the selected deployment stage.
- Include a simulated security scan.
- Never expose credentials in the Jenkinsfile or Console Output.

## **17. Troubleshooting guide**

| Problem                       | Possible reason                                             | What to check                                          |
| ----------------------------- | ----------------------------------------------------------- | ------------------------------------------------------ |
| Parameter not displayed       | Pipeline has not been saved or run to initialize parameters | Run the job again                                      |
| `params` value is empty       | Incorrect parameter name                                    | Check spelling and capitalization                      |
| Environment variable is empty | Variable is unavailable or incorrectly referenced           | Check `env.VARIABLE_NAME`                              |
| `withCredentials` fails       | Missing credential ID or plugin                             | Check Jenkins Credentials and plugin                   |
| GitHub checkout fails         | Invalid token or insufficient permissions                   | Check token and repository access                      |
| Secret appears in logs        | Secret was printed or exposed                               | Remove secret output and rotate the exposed credential |

## **18. Interview questions**

1. What are Jenkins build parameters?
2. What is the difference between a string and choice parameter?
3. What is a boolean parameter?
4. What are environment variables?
5. What is the difference between `params` and `env`?
6. Name five Jenkins built-in environment variables.
7. What is Jenkins Credentials?
8. Why should we never hardcode passwords in a Jenkinsfile?
9. What is a credentials ID?
10. What is the purpose of `withCredentials`?
11. How do you deploy the same application to DEV, QA and PROD?
12. How can you skip a pipeline stage based on a parameter?
13. What is the difference between a Jenkins parameter and a credential?
14. What is a GitHub Personal Access Token?
15. How would you secure a production deployment pipeline?

## **19. GitHub repository structure**

Save the lesson and your completed exercises in your training repository:

```
jenkins-training/
│
├── Session-01-Jenkins-Basics/
├── Session-02-Declarative-Pipeline/
├── Session-03-Jenkins-GitHub-Integration/
│
└── Session-04-Parameters-Environment-Credentials/
    ├── README.md
    ├── 01-string-parameter.Jenkinsfile
    ├── 02-choice-parameter.Jenkinsfile
    ├── 03-boolean-parameter.Jenkinsfile
    ├── 04-built-in-environment.Jenkinsfile
    ├── 05-custom-environment.Jenkinsfile
    ├── 06-parameters-and-environment.Jenkinsfile
    ├── 07-credentials-example.Jenkinsfile
    ├── 08-private-github-checkout.Jenkinsfile
    ├── 09-build-version.Jenkinsfile
    └── 10-mini-cicd-pipeline.Jenkinsfile
```

## **20. Session completion checklist**

Students should be able to explain and demonstrate:

- Create a string parameter.
- Create a choice parameter.
- Create a boolean parameter.
- Read parameter values using `params`.
- Read environment variables using `env`.
- Create custom environment variables.
- Understand Jenkins built-in variables.
- Explain Jenkins Credentials.
- Explain why hardcoded secrets are dangerous.
- Understand credential IDs and `withCredentials`.
- Build a parameter-driven CI/CD pipeline.

**End of Session **

**Next session:** Session  – Jenkins Agents and Distributed Builds: Controller, Agents, Executors, Labels and Running Jobs on Different Machines.
