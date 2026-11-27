```markdown
# Session 5 (Hours 9–10): Enterprise Architecture (Shared Libraries) & End-to-End Capstone

> **Course:** Enterprise Jenkins & GitHub CI/CD Engineering  
> **Target Audience:** Freshers & Aspiring DevOps / Platform Engineers  
> **Prerequisites:** Completion of Sessions 1–4 (Controller/Agent setup, Declarative `Jenkinsfile`, Multibranch Pipelines, Docker agents, Secrets Binding, SonarQube, Trivy, and Amazon ECR/Docker Hub).

---

## 1. Real-World Analogies & Architecture Diagrams

### Analogy 1: Jenkins Shared Libraries (Franchise Recipe Book vs. Handwritten Notes in Every Store)
* **Without Shared Libraries (Copy-Paste Hell):** Imagine a fast-food chain with 100 restaurants (`payment-service`, `auth-service`, `cart-service`, `notification-service`). Every single restaurant manager writes their own 150-line cooking manual (`Jenkinsfile`). When corporate headquarters decides to change the frying temperature (updating a Trivy scan flag or Amazon ECR registry URL), 100 managers have to edit 100 manuals manually—and 20 of them make typos!
* **With Jenkins Shared Libraries (`@Library('enterprise-ci-lib')`):** Corporate headquarters maintains **one master recipe book** in a dedicated Git repository (`jenkins-shared-library`). Each microservice's `Jenkinsfile` is reduced to **5 clean lines**: *"Use the standard Java microservice recipe, and pass in `appName: 'payment-service'`."* When the Platform Engineering team upgrades the Trivy scanner or Slack alert format in the Shared Library, all 100 microservices inherit the improvement automatically on their next build!

---

### ASCII Architecture Diagram: Shared Library + End-to-End Enterprise CI Capstone

```text
+-----------------------------------------------------------------------------------+
|                   1. PLATFORM TEAM REPO: jenkins-shared-library                   |
|                                                                                   |
|   ├── vars/                                                                       |
|   │    ├── standardJavaPipeline.groovy   <-- Reusable 7-Stage Pipeline Template   |
|   │    └── trivyScan.groovy              <-- Reusable Security Scan Step          |
|   ├── src/com/edgex/devops/Validator.groovy  <-- Helper Groovy Classes            |
|   └── resources/scripts/notify-slack.sh      <-- Non-Groovy Shell/JSON Templates  |
+-----------------------------------------|-----------------------------------------+
                                          | @Library('edgex-shared-lib@v1.0.0')
                                          v
+-----------------------------------------------------------------------------------+
|              2. APPLICATION REPO: order-service (5-Line Jenkinsfile!)             |
|                                                                                   |
|   @Library('edgex-shared-lib@v1.0.0') _                                           |
|   standardJavaPipeline(appName: 'order-service', ecrRepo: 'order-service')        |
+-----------------------------------------|-----------------------------------------+
                                          | GitHub Webhook (Push / PR)
                                          v
+-----------------------------------------------------------------------------------+
|               3. END-TO-END ENTERPRISE CAPSTONE EXECUTION FLOW                    |
|                                                                                   |
|  [Git Webhook] -> [Ephemeral Docker Agent] -> [Maven Build] -> [SonarQube Gate]   |
|                                                                       |           |
|  [Slack Alert] <- [Push to Amazon ECR] <- [Trivy CVE Scan] <- [Docker Build] <----+
+-----------------------------------------------------------------------------------+

```

---

## 2. Deep-Dive Concepts with Production Examples

### 2.1 Anatomy of a Jenkins Shared Library Repository

A Jenkins Shared Library is simply a separate Git repository with a strict, standardized directory layout:

```text
jenkins-shared-library/
├── vars/
│   ├── standardJavaPipeline.groovy   # Global variables/pipelines callable in any Jenkinsfile
│   └── sendSlackAlert.groovy         # Reusable notification helper function
├── src/
│   └── com/
│       └── edgex/
│           └── ci/
│               └── ImageTagHelper.groovy  # Object-oriented Groovy utility classes
└── resources/
    └── com/
        └── edgex/
            └── ci/
                └── slack-payload.json     # Static templates loaded via libraryResource()

```

* **`vars/` (Most Important):** Every `.groovy` file inside `vars/` becomes a global step name in Jenkins! For example, `vars/sendSlackAlert.groovy` allows any `Jenkinsfile` to call `sendSlackAlert(status: 'SUCCESS')`.
* **`src/`:** Standard Java/Groovy package structure (`com.edgex.ci.*`) for complex business logic, version parsing, or API clients.
* **`resources/`:** Stores external helper scripts, SQL templates, or JSON payloads loaded via `libraryResource('com/edgex/ci/slack-payload.json')`.

---

### 2.2 Building the Shared Library (`vars/standardJavaPipeline.groovy`)

In your `jenkins-shared-library` GitHub repository, create `vars/standardJavaPipeline.groovy`. Notice the special `def call(Map config = [:])` entry point—Jenkins executes `call()` automatically whenever a `Jenkinsfile` invokes `standardJavaPipeline(...)`:

```groovy
// File: vars/standardJavaPipeline.groovy
def call(Map config = [:]) {
    // Validate required parameters passed from the microservice Jenkinsfile
    def appName     = config.appName ?: error("Parameter 'appName' is required!")
    def awsRegion   = config.awsRegion ?: 'ap-south-1'
    def awsAccount  = config.awsAccount ?: '123456789012'
    def slackChan   = config.slackChannel ?: '#devops-ci-alerts'

    pipeline {
        agent {
            label 'docker-agent'
        }

        tools {
            maven 'Maven-3.9'
        }

        environment {
            GIT_SHORT_SHA   = sh(script: 'git rev-parse --short HEAD', returnStdout: true).trim()
            IMAGE_TAG       = "${env.BRANCH_NAME}-${env.BUILD_NUMBER}-${GIT_SHORT_SHA}"
            ECR_REGISTRY    = "${awsAccount}.dkr.ecr.${awsRegion}.amazonaws.com"
            FULL_IMAGE_NAME = "${ECR_REGISTRY}/${appName}:${IMAGE_TAG}"
        }

        options {
            timeout(time: 20, unit: 'MINUTES')
            buildDiscarder(logRotator(numToKeepStr: '10'))
            timestamps()
        }

        stages {
            stage('1. Maven Build & Unit Test') {
                steps {
                    echo "[SharedLib] Building ${appName} (${IMAGE_TAG})..."
                    sh 'mvn clean verify'
                }
            }

            stage('2. SonarQube Static Analysis') {
                steps {
                    withSonarQubeEnv('SonarQube-Server') {
                        sh "mvn sonar:sonar -Dsonar.projectKey=${appName}"
                    }
                }
            }

            stage('3. SonarQube Quality Gate') {
                steps {
                    timeout(time: 5, unit: 'MINUTES') {
                        waitForQualityGate abortPipeline: true
                    }
                }
            }

            stage('4. Docker Image Build') {
                steps {
                    sh 'docker build -t "$FULL_IMAGE_NAME" .'
                }
            }

            stage('5. Trivy Container Vulnerability Scan') {
                steps {
                    sh '''
                        trivy image --severity HIGH,CRITICAL --no-progress "$FULL_IMAGE_NAME"
                        trivy image --exit-code 1 --severity CRITICAL --ignore-unfixed --no-progress "$FULL_IMAGE_NAME"
                    '''
                }
            }

            stage('6. Push Verified Artifact to Amazon ECR') {
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
                            aws ecr get-login-password --region "$awsRegion" | \
                              docker login --username AWS --password-stdin "$ECR_REGISTRY"
                            docker push "$FULL_IMAGE_NAME"
                        '''
                    }
                }
            }
        }

        post {
            always {
                sh 'docker rmi "$FULL_IMAGE_NAME" || true'
                cleanWs()
            }
            success {
                slackSend(
                    channel: slackChan,
                    color: 'good',
                    message: "✅ *CI PASSED*: `${appName}` | Tag: `${IMAGE_TAG}` | Branch: `${env.BRANCH_NAME}` (<${env.BUILD_URL}|View Build>)"
                )
            }
            failure {
                slackSend(
                    channel: slackChan,
                    color: 'danger',
                    message: "🚨 *CI FAILED*: `${appName}` | Branch: `${env.BRANCH_NAME}` (<${env.BUILD_URL}console|Inspect Logs>)"
                )
            }
        }
    }
}

```

---

### 2.3 The Microservice `Jenkinsfile` (Reduced from 130 Lines to 7 Lines!)

Now, across all 40 microservices in your company, the `Jenkinsfile` inside each application repository looks like this:

```groovy
// File: Jenkinsfile (inside order-service, payment-service, user-service, etc.)
@Library('edgex-shared-lib@v1.0.0') _

standardJavaPipeline(
    appName: 'order-service',
    awsRegion: 'ap-south-1',
    slackChannel: '#order-service-ci'
)

```

> **Why `@v1.0.0` (Git Tag Pinning) Matters in Enterprise:**
> Never let production microservices blindly load `@main` of a Shared Library! If a Platform Engineer pushes a breaking change to `@main`, 50 pipelines break simultaneously. Instead, tag stable releases (`v1.0.0`, `v1.1.0`) in Git so teams upgrade deliberately and safely.

---

## 3. Industry Scenarios, Common Production Failures & DevOps Fixes

### How Platform Teams Operate Shared Libraries at Scale

* **Golden Path Engineering:** Platform teams provide "Golden Path" Shared Libraries (`standardJavaPipeline`, `standardNodePipeline`, `standardPythonPipeline`) with security gates (SonarQube + Trivy) baked in by default. Application developers focus on writing features rather than debugging Groovy syntax.
* **Implicit vs. Explicit Loading:** In `Manage Jenkins` $\rightarrow$ `System` $\rightarrow$ `Global Trusted Pipeline Libraries`, administrators can either mark a library as **Load implicitly** (available to every job without `@Library`) or require explicit `@Library('name@version') _` declarations so teams control version upgrades.

### 4 Common Production Failures & How DevOps Fixes Them

| # | Real-World Failure / Symptom | Root Cause in Industry | Step-by-Step DevOps Fix |
| --- | --- | --- | --- |
| **1** | **`org.jenkinsci.plugins.scriptsecurity.sandbox.RejectedAccessException: Scripts not permitted to use method...`** | An untrusted library (configured at Folder level rather than Global Trusted level) called restricted Java/Groovy APIs (`new File()`, `JsonSlurperClassic`) inside the Groovy Sandbox. | 1. Register core Platform Shared Libraries under **Manage Jenkins $\rightarrow$ System $\rightarrow$ Global Trusted Pipeline Libraries** (which runs outside the restricted sandbox).<br>

<br>2. Or approve specific safe signatures in **Manage Jenkins $\rightarrow$ In-process Script Approval**. |
| **2** | **`ERROR: Could not find library edgex-shared-lib` or `Library version v1.0.0 not found**` | The library name in `@Library('...')` didn't match the exact Name configured in Jenkins System settings, or the Git tag `v1.0.0` wasn't pushed to GitHub. | 1. Verify exact spelling under **Global Trusted Pipeline Libraries**.<br>

<br>2. Run `git tag v1.0.0 && git push origin v1.0.0` inside the Shared Library repository. |
| **3** | **Variable interpolation failure inside `sh '''...'''` when using Shared Library Groovy variables** | Inside `vars/standardJavaPipeline.groovy`, `awsRegion` is a **Groovy local variable** (`def awsRegion`), NOT a Bash environment variable, so `sh '''echo $awsRegion'''` prints empty! | 1. Either pass Groovy variables into the `environment { AWS_REGION = "${awsRegion}" }` block so Bash can read `$AWS_REGION`, or use double quotes carefully for non-secret variables. |
| **4** | **All 30 microservice pipelines break simultaneously after a Shared Library update** | All microservice `Jenkinsfile`s referenced `@Library('edgex-shared-lib@main')` instead of an immutable version tag, and a buggy commit landed on `main`. | 1. Revert the bad commit on `main`.<br>

<br>2. Enforce semantic version Git tags (`@v1.0.0`, `@v1.0.1`) across all microservice repositories. |

---

## 4. Guided Hands-On Lab: End-to-End Enterprise Capstone Practical

### Objective

Build and wire together the complete end-to-end production CI pipeline:

**GitHub Webhook Trigger $\rightarrow$ Ephemeral Docker Agent $\rightarrow$ Maven Build $\rightarrow$ SonarQube Quality Gate $\rightarrow$ Docker Image Build $\rightarrow$ Trivy Vulnerability Scan $\rightarrow$ Amazon ECR (or Docker Hub) Push $\rightarrow$ Slack Status Alert**—powered by a versioned **Jenkins Shared Library**.

### Step-by-Step Execution Guide

1. **Create the Shared Library Repository (`jenkins-shared-library`):**
* Create a new GitHub repository named `jenkins-shared-library`.
* Create `vars/standardJavaPipeline.groovy` using the code in **Section 2.2** (adjusting registry/SonarQube settings to match your lab environment).
* Commit, tag `v1.0.0`, and push:
```bash
git add .
git commit -m "feat: add standardJavaPipeline v1.0.0"
git tag v1.0.0
git push origin main --tags

```




2. **Register the Shared Library in Jenkins:**
* Navigate to **Manage Jenkins** $\rightarrow$ **System** $\rightarrow$ Scroll to **Global Trusted Pipeline Libraries**.
* Click **Add**:
* **Name:** `edgex-shared-lib`
* **Default version:** `v1.0.0`
* **Retrieval method:** `Modern SCM` $\rightarrow$ `Git` $\rightarrow$ Paste `https://github.com/<YOUR-USERNAME>/jenkins-shared-library.git`.


* Click **Save**.


3. **Update Your Application Repository (`order-service`):**
* Replace your 130-line `Jenkinsfile` with the 7-line Shared Library call from **Section 2.3**.
* Verify your application repository contains:
* `pom.xml` & `src/`
* `Dockerfile` (`FROM eclipse-temurin:17-jre-alpine`)
* `Jenkinsfile` (7 lines)


* Ensure your GitHub Webhook (`http://<JENKINS-URL>:8080/github-webhook/`) is active.


4. **Trigger the End-to-End Capstone Run:**
* Make a code change in `order-service`, commit, and run `git push origin main`.
* Watch the entire automated symphony execute end-to-end:
1. GitHub Webhook triggers Jenkins within 2 seconds.
2. Ephemeral Docker build container spins up dynamically.
3. Maven compiles and runs unit tests.
4. SonarQube analyzes source code and passes the Quality Gate.
5. Docker builds the tagged container image (`main-<build>-<sha>`).
6. Trivy scans the image and confirms 0 `CRITICAL` CVEs.
7. Image is pushed to Amazon ECR / Docker Hub.
8. Slack channel receives a green `✅ CI PASSED` alert with the build link, and the ephemeral container terminates!





---

## 5. Final Course Capstone Project (Portfolio & LinkedIn Showcase)

### Project Title: *"Enterprise Multi-Microservice DevSecOps Platform with Jenkins Shared Libraries, Trivy, SonarQube & Amazon ECR"*

#### Scenario

You are hired as a DevOps Engineer to standardize CI/CD across two microservices (`order-service` and `payment-service`). Instead of duplicating pipeline code, you must engineer a reusable, versioned **Jenkins Shared Library** that enforces SonarQube Quality Gates, Trivy container CVE blocking, immutable Amazon ECR (or Docker Hub) image tagging, and real-time Slack ChatOps notifications.

#### Complete Deliverables (Push to GitHub & Share on LinkedIn)

1. **Repository 1 (`jenkins-shared-library`):**
* Contains `vars/standardJavaPipeline.groovy` and a helper function `vars/scanContainerImage.groovy` tagged at `v1.0.0`.
* Includes a detailed `README.md` documenting input parameters (`appName`, `awsRegion`, `slackChannel`) for developer teams.


2. **Repository 2 (`order-service` & `payment-service`):**
* Two separate repositories (or branches) both using the exact same 7-line `Jenkinsfile` importing `@Library('edgex-shared-lib@v1.0.0') _`.


3. **Capstone Verification Portfolio (`README.md` Screenshots):**
* Architecture diagram of your end-to-end flow.
* Jenkins **Stage View / Blue Ocean** screenshot showing all 6 stages green.
* SonarQube Quality Gate `PASSED` badge screenshot.
* Trivy clean scan log + Amazon ECR / Docker Hub published tag screenshot.
* Slack channel notification screenshot.



---

## 6. Knowledge Check: 10 Multiple-Choice Questions (MCQs)

1. **What is the primary architectural purpose of a Jenkins Shared Library?**
* A) To store compiled `.jar` and `.docker` binary artifacts permanently
* B) To centralize reusable pipeline logic (`vars/*.groovy`) in a version-controlled Git repository so multiple microservices share standardized CI/CD workflows without code duplication (DRY)
* C) To replace Docker Engine on build agents
* D) To host the SonarQube PostgreSQL database


2. **Which directory inside a Jenkins Shared Library repository holds `.groovy` files that become directly callable as global steps (e.g., `standardJavaPipeline(...)`) inside a `Jenkinsfile`?**
* A) `src/`
* B) `resources/`
* C) `vars/`
* D) `lib/`


3. **In a Shared Library file like `vars/deployApp.groovy`, which method signature is automatically invoked by Jenkins when a pipeline calls `deployApp(env: 'prod')`?**
* A) `def main(String[] args)`
* B) `def execute(Object params)`
* C) `def call(Map config = [:])`
* D) `def runPipeline()`


4. **Why should microservice `Jenkinsfile`s pin a specific Git tag (`@Library('edgex-shared-lib@v1.0.0') _`) rather than using `@main`?**
* A) Jenkins throws a syntax error if `@main` is used
* B) Pinning immutable version tags prevents breaking changes pushed to `main` by Platform Engineers from simultaneously breaking all application teams' builds
* C) `@v1.0.0` skips SonarQube analysis to make builds faster
* D) GitHub Webhooks only trigger on tagged Shared Libraries


5. **What is the purpose of the trailing underscore `_` in `@Library('edgex-shared-lib@v1.0.0') _`?**
* A) It comments out the library import
* B) In Groovy, annotations like `@Library` must annotate a statement or import; the underscore `_` acts as a dummy placeholder when you aren't importing a specific `src/` class immediately below it
* C) It forces Jenkins to run the build on the Controller
* D) It deletes old workspace files before loading the library


6. **What is the difference between configuring a Shared Library under `Global Trusted Pipeline Libraries` versus `Folder-level Pipeline Libraries`?**
* A) Global Trusted libraries run outside the Groovy Sandbox (allowing full Groovy/Java methods) and are available across the entire Jenkins instance, whereas Folder libraries run inside the restricted Groovy Sandbox
* B) Folder libraries do not support Git repositories
* C) Global libraries only work with Freestyle jobs
* D) There is no difference between the two


7. **In the end-to-end capstone pipeline, what happens if SonarQube reports `Quality Gate: FAILED`?**
* A) Jenkins still builds the Docker image and pushes it to Amazon ECR with a `warning` tag
* B) `waitForQualityGate abortPipeline: true` halts the pipeline immediately before Docker build or ECR push occurs, and triggers the `post { failure { ... } }` Slack alert
* C) Trivy automatically fixes the Java code bugs
* D) Jenkins deletes the GitHub repository


8. **Which sequence represents the correct enterprise DevSecOps "Shift-Left" ordering in our capstone pipeline?**
* A) Push to ECR $\rightarrow$ Trivy Scan $\rightarrow$ Docker Build $\rightarrow$ Maven Build $\rightarrow$ SonarQube
* B) Maven Build & Test $\rightarrow$ SonarQube SAST & Quality Gate $\rightarrow$ Docker Build $\rightarrow$ Trivy CVE Scan $\rightarrow$ Push to ECR $\rightarrow$ Slack Notification
* C) Slack Notification $\rightarrow$ Push to ECR $\rightarrow$ Maven Build $\rightarrow$ Trivy Scan
* D) Docker Build $\rightarrow$ Push to ECR $\rightarrow$ SonarQube Quality Gate


9. **Why did we pass `def awsRegion = config.awsRegion ?: 'ap-south-1'` inside `vars/standardJavaPipeline.groovy`?**
* A) To force every team to deploy only to Mumbai (`ap-south-1`)
* B) Using Groovy's Elvis operator (`?:`) provides a sensible default value (`ap-south-1`) if the calling `Jenkinsfile` omits the `awsRegion` parameter
* C) To encrypt the AWS region string in console logs
* D) To disable Amazon ECR authentication


10. **What is the role of the `resources/` directory inside a Jenkins Shared Library?**
* A) Storing compiled `.jar` files produced by Maven
* B) Storing non-Groovy helper files (such as JSON templates, shell scripts, or YAML configs) that can be loaded at runtime using `libraryResource(...)`
* C) Storing Jenkins user passwords
* D) Storing Docker daemon socket files



1. **B** — Shared Libraries eliminate copy-pasted `Jenkinsfile`s across dozens of repositories, enforcing DRY (Don't Repeat Yourself) engineering and centralized security standards.
2. **C** — Files inside `vars/` (like `vars/standardJavaPipeline.groovy`) are exposed directly as global DSL steps in Declarative and Scripted pipelines.
3. **C** — Jenkins looks for the `call(...)` method inside `vars/<stepName>.groovy` whenever that step is invoked in a `Jenkinsfile`.
4. **B** — Versioning Shared Libraries with semantic Git tags (`v1.0.0`, `v1.1.0`) gives application teams stability and controlled upgrade paths.
5. **B** — Groovy annotations require a target element; `_` satisfies the compiler when loading global `vars/` steps without an explicit `import` statement.
6. **A** — Global Trusted libraries are managed by Jenkins administrators and bypass Groovy Sandbox restrictions, whereas Folder libraries are sandboxed for multi-tenant safety.
7. **B** — Failing fast at the Quality Gate prevents vulnerable or buggy code from ever being packaged into a container or uploaded to your registry.
8. **B** — Each stage acts as a progressive gate: compile/test code $\rightarrow$ verify code quality/SAST $\rightarrow$ package container $\rightarrow$ scan container CVEs $\rightarrow$ publish verified artifact $\rightarrow$ notify team.
9. **B** — Groovy's Elvis operator (`?:`) cleanly supplies default configuration values while still allowing individual teams to override them.
10. **B** — `resources/` holds static scripts, JSON payloads, or config templates retrieved via the built-in `libraryResource` step.

---

## 7. Deep-Dive Research & Post-Course Mastery Prompts (10 Investigative Prompts)

Continue building your portfolio after completing this 10-hour curriculum with these real-world DevOps challenges:

1. **Extend the Shared Library with `src/` Groovy Classes:** Create `src/com/edgex/ci/TagGenerator.groovy` with a static method `generateTag(String branch, String buildNum, String sha)` and import it inside `vars/standardJavaPipeline.groovy` to keep pipeline logic clean and unit-testable.
2. **Unit Testing Jenkins Shared Libraries (`JenkinsPipelineUnit`):** How do Platform Engineers test changes to `vars/standardJavaPipeline.groovy` before tagging `v1.1.0`? Research the open-source **JenkinsPipelineUnit** framework (Gradle/Maven + JUnit) to mock Jenkins steps and run automated tests on your Shared Library!
3. **Adding CD (Continuous Deployment) with Argo CD (GitOps):** Our capstone ended at pushing a verified container image to Amazon ECR. Research how **GitOps** works: instead of Jenkins running `kubectl apply` directly against production EKS, how does Jenkins update an image tag in a separate `k8s-manifests` Git repo so **Argo CD** automatically syncs the new release to Kubernetes?
4. **Jenkins Configuration as Code (JCasC):** In Session 1, we configured Jenkins tools, clouds, and credentials through the Web UI. Research the **JCasC (`configuration-as-code`)** plugin—how do enterprises define the *entire* Jenkins Controller setup inside a single `jenkins.yaml` file so a brand-new Jenkins server boots up 100% pre-configured?
5. **Kubernetes Ephemeral Agents (`kubernetes` Plugin):** In Session 3, we used Docker containers on a single VM as ephemeral agents. Research how the **Jenkins Kubernetes Plugin** dynamically provisions **Kubernetes Pods** (with multi-container sidecars for `maven`, `trivy`, and `kaniko`) inside an EKS/AKS cluster!
6. **Building Container Images Without Docker Daemon (`Kaniko` / `Buildah`):** Research why running `docker build` inside a Kubernetes Pod is blocked by modern cluster security policies (privileged mode risk), and how **Google Kaniko** builds and pushes images to Amazon ECR completely in userspace without a Docker daemon.
7. **Pipeline Matrix Builds (`matrix` Directive):** Suppose your library needs to be tested across **3 Java versions** (`JDK 11`, `JDK 17`, `JDK 21`) and **2 OS platforms** (`Ubuntu`, `Alpine`) simultaneously. Research the Declarative `matrix { axes { ... } }` directive to run all 6 combinations automatically.
8. **Automated Semantic Versioning & Changelog Generation:** Research how CI pipelines inspect Conventional Commits (`feat:`, `fix:`, `BREAKING CHANGE:`) to automatically bump Git tags (`v1.0.0` $\rightarrow$ `v1.1.0`) and generate GitHub Release notes upon merging to `main`.
9. **Observability for Jenkins (`Prometheus` + `Grafana`):** How do SREs monitor Jenkins Controller health, build queue wait times, and executor saturation? Install the **Prometheus Metrics Plugin** (`/prometheus` endpoint) and explore the official Grafana dashboard for Jenkins.
10. **Portfolio & Interview Readiness:** Update your LinkedIn profile and GitHub `README.md` with your **Capstone Architecture Diagram**, explaining how you reduced 130-line `Jenkinsfile`s to 7 lines using Shared Libraries while enforcing SonarQube and Trivy DevSecOps gates!
# **Jenkins Training – Session 6**

## **End-to-End Jenkins CI/CD Project for Beginners**

**Course:** Practical Jenkins Training for Freshers\
**Session:** 6 of 6\
**Level:** Beginner to Intermediate\
**Platform:** Prepare.sh Jenkins Playground (`prepare.sh/jenkins`)\
**Duration:** 2 hours\
**Goal:** Build a complete CI/CD pipeline and understand how Jenkins automates application delivery in a real DevOps environment.

# **1. What Will We Build Today?**

In the previous sessions, we learned Jenkins jobs, pipelines, GitHub integration, parameters, credentials, agents, and Docker integration.

Today, we will combine those concepts into one project.

Imagine a developer has written a Python application and pushed the code to GitHub.

Our job as DevOps engineers is to automate the process:

1. Get the latest code from GitHub.
2. Inspect the source code.
3. Build the application.
4. Run tests.
5. Perform a simulated security check.
6. Package the application.
7. Archive the build artifact.
8. Simulate deployment.
9. Generate a final pipeline report.

**End-to-end CI/CD workflow**

**Developer pushes code to GitHub**

**Jenkins Checkout**

**Build Application**

**Run Unit Tests**

**Security Scan Simulation**

**Package and Archive Artifact**

**Deployment Simulation**

**Pipeline Success**

**Important:** We will build a pipeline that can be practised in Prepare.sh. Security scanning and deployment will initially be simulations. Actual Checkmarx, SonarQube, Docker builds, and server deployments require their respective tools, plugins, credentials, and infrastructure.

# **2. Understand the Project**

We will use a simple Python application.

**Project name:** `jenkins-cicd-training`

The application will have:

- A Python source file.
- A basic test file.
- A Jenkins pipeline.
- A README file.

Our target repository structure:

```
jenkins-cicd-training/
│
├── Jenkinsfile
├── app.py
├── test_app.py
└── README.md
```

### **What does each file do?**

| File          | Purpose                          |
| ------------- | -------------------------------- |
| `Jenkinsfile` | Defines the CI/CD pipeline       |
| `app.py`      | Contains application code        |
| `test_app.py` | Contains basic application tests |
| `README.md`   | Explains the project             |

# **3. Create the Python Application**

Create a GitHub repository named:

```
jenkins-cicd-training
```

Inside the repository, create `app.py`.

### **app.py**

```
def welcome_message():    return "Welcome to Jenkins CI/CD Training!"def add_numbers(a, b):    return a + bif __name__ == "__main__":    print(welcome_message())    print("Addition Result:", add_numbers(10, 20))
```

### **Understand the code**

`welcome_message()` returns a welcome message.

`add_numbers(a, b)` accepts two numbers and returns their sum.

The last section executes when we run the Python file directly.

Expected output:

```
Welcome to Jenkins CI/CD Training!
Addition Result: 30
```

# **4. Create the Test File**

Create another file called `test_app.py`.

```
from app import welcome_message, add_numbersdef test_welcome_message():    assert welcome_message() == "Welcome to Jenkins CI/CD Training!"def test_add_numbers():    assert add_numbers(10, 20) == 30def test_add_zero():    assert add_numbers(10, 0) == 10print("All application tests passed!")
```

### **What is testing?**

Testing checks whether our application behaves as expected.

For example:

```
assert add_numbers(10, 20) == 30
```

This checks whether adding 10 and 20 returns 30.

If the result is incorrect, the assertion fails.

**Production relevance:** Automated tests help detect application defects before code reaches production.

# **5. Create the Jenkinsfile**

This is the main part of today's session.

Create a file named exactly:

```
Jenkinsfile
```

Add the following pipeline:

```
pipeline {

    agent any

    environment {
        APP_NAME = 'jenkins-cicd-training'
        BUILD_VERSION = '1.0'
    }

    stages {

        stage('Checkout') {
            steps {
                echo 'Checking out application source code'
                checkout scm
            }
        }

        stage('Inspect Repository') {
            steps {
                echo 'Inspecting repository files'
                sh 'ls -la'
            }
        }

        stage('Build') {
            steps {
                echo 'Building Python application'
                sh 'python3 -m py_compile app.py'
                echo 'Build completed successfully'
            }
        }

        stage('Test') {
            steps {
                echo 'Running application tests'
                sh 'python3 test_app.py'
            }
        }

        stage('Security Scan Simulation') {
            steps {
                echo 'Starting security scan simulation'
                echo 'Checking source code for security issues'
                echo 'Security scan simulation completed'
            }
        }

        stage('Package') {
            steps {
                echo 'Packaging application'
                sh 'mkdir -p build'
                sh 'cp app.py build/'
                sh 'cp test_app.py build/'
                sh 'echo Jenkins CI/CD package created > build/build-info.txt'
                sh 'cat build/build-info.txt'
            }
        }

        stage('Archive Artifact') {
            steps {
                echo 'Archiving application package'
                archiveArtifacts artifacts: 'build/*', fingerprint: true
            }
        }

        stage('Deploy Simulation') {
            steps {
                echo 'Starting deployment simulation'
                echo 'Application package is ready for deployment'
                echo 'Deployment simulation completed'
            }
        }
    }

    post {

        success {
            echo 'CI/CD Pipeline completed successfully!'
        }

        failure {
            echo 'CI/CD Pipeline failed. Check the console output.'
        }

        always {
            echo 'Pipeline execution finished'
            echo 'Application: jenkins-cicd-training'
        }
    }
}
```

## **6. Understand Each Pipeline Stage**

| Stage                    | What happens?              | Real-world DevOps purpose         |
| ------------------------ | -------------------------- | --------------------------------- |
| Checkout                 | Downloads source code      | Gets latest developer changes     |
| Inspect Repository       | Lists project files        | Checks workspace contents         |
| Build                    | Validates Python syntax    | Finds build or compilation errors |
| Test                     | Executes tests             | Detects application defects       |
| Security Scan Simulation | Prints scan messages       | Represents security scanning      |
| Package                  | Creates build directory    | Prepares deployable files         |
| Archive Artifact         | Stores build files         | Preserves build output            |
| Deploy Simulation        | Prints deployment messages | Represents application deployment |

### **Important Jenkins concepts**

`pipeline`

Defines the entire Jenkins Declarative Pipeline.

`agent any`

Allows Jenkins to select any available agent to run the pipeline.

`environment`

Defines environment variables available to pipeline steps.

`stages`

Groups the pipeline into logical stages.

`steps`

Contains the actual commands or Jenkins steps.

`post`

Defines actions to execute after pipeline completion.

# **7. Execute the Pipeline in Prepare.sh**

Follow these steps:

1. Open the Prepare.sh Jenkins playground.
2. Open the Jenkins dashboard.
3. Create a new Pipeline job.
4. Give it the name `jenkins-cicd-training`.
5. Select the Pipeline configuration option.
6. Choose the Pipeline script option if available.
7. Paste the Jenkinsfile content into the script editor.
8. Save the pipeline.
9. Click **Build Now**.
10. Open the build number.
11. Open **Console Output**.
12. Observe each stage.

**Prepare.sh compatibility note:** This pipeline uses `checkout scm`, shell commands, and artifact archiving. Their availability depends on the playground's Jenkins configuration. If Git checkout is not configured, use a repository configured for that job or temporarily remove the Checkout stage and use the playground's available source files. If `python3` or `archiveArtifacts` is unavailable, note that limitation rather than treating the simulation as a real execution.

# **8. Understand the Expected Pipeline Result**

A successful execution should show stages similar to:

```
Checkout
Inspect Repository
Build
Test
Security Scan Simulation
Package
Archive Artifact
Deploy Simulation
```

The final console output should include:

```
CI/CD Pipeline completed successfully!
Pipeline execution finished
Application: jenkins-cicd-training
```



Expected result

&#x20;The Jenkins build status should be SUCCESS if all required steps execute successfully.



# **9. Troubleshooting Common Failures**

| Error                    | Possible reason                              | What to check                            |
| ------------------------ | -------------------------------------------- | ---------------------------------------- |
| `python3: not found`     | Python is not installed on the agent         | Check available runtime                  |
| `app.py not found`       | Repository files are missing                 | Check checkout and workspace             |
| `checkout scm` fails     | SCM is not configured                        | Check Pipeline job configuration         |
| `archiveArtifacts` fails | Artifact archiving unavailable or wrong path | Check generated `build` directory        |
| Permission denied        | Agent user lacks permission                  | Check workspace permissions              |
| Pipeline syntax error    | Incorrect Groovy/Jenkins syntax              | Check braces, quotes and stage structure |

### **Practical troubleshooting exercise**

Introduce a failure intentionally:

Change:

```
return a + b
```

To:

```
return a - b
```

Run the pipeline again.

The test should fail because the expected answer is 30, but the application returns -10.

This is how automated testing prevents incorrect code from progressing through a CI/CD pipeline.

After observing the failure, restore the original code and rerun the pipeline.

# **10. Production DevOps: What Would Change?**

The training pipeline uses simple commands and simulations. A production pipeline would connect to real services.

| Training pipeline        | Production implementation                        |
| ------------------------ | ------------------------------------------------ |
| Security scan simulation | SonarQube, Checkmarx, Black Duck                 |
| Python syntax validation | Application-specific build process               |
| Basic test script        | Pytest or another test framework                 |
| Package directory        | Versioned package or container image             |
| Archive artifact         | Artifact repository such as Nexus or Artifactory |
| Deployment simulation    | Kubernetes, OpenShift, VM or cloud deployment    |
| Manual Build Now         | GitHub webhook or automated trigger              |

For example, a production DevSecOps pipeline might follow:

```
GitHub
   |
   v
Jenkins
   |
   v
Gitleaks Secret Scan
   |
   v
SonarQube Code Quality
   |
   v
Checkmarx SAST
   |
   v
Black Duck SCA
   |
   v
Docker Build
   |
   v
Container Image Scan
   |
   v
Container Registry
   |
   v
OpenShift Deployment
   |
   v
Application Verification
```

These are real integrations, not features automatically provided by the Prepare.sh playground.

# **11. Student DIY Assignment**

Ask students to complete these tasks independently.

## **Task 1 – Application changes**

- Change the welcome message.
- Add a subtraction function.
- Add a multiplication function.
- Add tests for both functions.
- Run the pipeline again.

## **Task 2 – Jenkins pipeline changes**

- Add a new stage called `Application Information`.
- Print the application name.
- Print the build version.
- Add a stage called `Quality Check`.
- Add a stage called `Deployment Verification`.

## **Task 3 – Failure scenarios**

- Introduce an incorrect test expectation.
- Run the pipeline.
- Observe the failed stage.
- Fix the issue.
- Run the pipeline again.
- Confirm SUCCESS.

## **Task 4 – GitHub practice**

- Push the application to GitHub.
- Push the Jenkinsfile.
- Make one application code change.
- Commit and push the changes.
- Run Jenkins again.
- Verify the latest code is being used.

# **12. Interview Questions**

1. What is CI/CD?
2. What is the difference between Continuous Integration and Continuous Deployment?
3. What is a Jenkinsfile?
4. What is the difference between Declarative and Scripted Pipeline?
5. What does `agent any` mean?
6. What is the purpose of the `environment` block?
7. What is the difference between a stage and a step?
8. What is the purpose of the `post` block?
9. What is `checkout scm`?
10. What is an artifact in Jenkins?
11. Why do we archive build artifacts?
12. What happens when a pipeline stage fails?
13. How can Jenkins integrate with GitHub?
14. How can Jenkins execute security scans?
15. How can Jenkins deploy an application to Kubernetes?
16. What is the difference between Jenkins controller and agent?
17. What are Jenkins credentials?
18. Why should passwords not be hardcoded in a Jenkinsfile?
19. How can we implement parallel execution?
20. How do you troubleshoot a failed Jenkins pipeline?

# **13. GitHub Portfolio Submission**

Create this folder structure in your training repository:

```
jenkins-training/
│
├── session-01-jenkins-basics/
├── session-02-declarative-pipeline/
├── session-03-github-integration/
├── session-04-parameters-credentials/
├── session-05-agents-docker/
│
└── session-06-end-to-end-cicd/
    ├── Jenkinsfile
    ├── app.py
    ├── test_app.py
    ├── README.md
    └── screenshots/
```

Save screenshots of:

1. Jenkins pipeline configuration.
2. Successful pipeline stage view.
3. Console output.
4. Failed test execution.
5. Successful execution after fixing the test.
6. Archived artifacts, if supported.

Suggested Git commit:

```
git add .
git commit -m "Completed Jenkins Session 6 end-to-end CI/CD project"
git push origin main
```

# **14. Final Course Completion Checklist**

Jenkins beginner course – 6 sessions

| Session | Topic                                             | Status          |
| ------- | ------------------------------------------------- | --------------- |
| 1       | Jenkins Architecture and Basics                   | Completed       |
| 2       | Declarative Jenkins Pipeline                      | Completed       |
| 3       | Jenkins and GitHub Integration                    | Completed       |
| 4       | Parameters, Environment Variables and Credentials | Completed       |
| 5       | Agents, Distributed Builds and Docker             | Completed       |
| 6       | End-to-End Jenkins CI/CD Project                  | Today's session |

## **What students should be able to explain after this course**

By the end of the six sessions, students should be able to:

- Explain Jenkins architecture.
- Create and execute Jenkins jobs.
- Write basic Declarative Pipelines.
- Integrate Jenkins with GitHub.
- Understand parameters and environment variables.
- Explain Jenkins credentials and secret handling.
- Understand controllers, agents, and executors.
- Explain Docker integration concepts.
- Build a multi-stage CI/CD pipeline.
- Troubleshoot common pipeline failures.
- Explain how Jenkins fits into a DevSecOps workflow.

**Trainer's final activity:** Ask each student to explain the complete CI/CD pipeline from a developer's GitHub commit to application deployment, using their own Jenkinsfile as the example.

**Course complete.** The next useful step is a separate advanced practical project: integrate Jenkins with GitHub, SonarQube, Checkmarx, Docker, a container registry, and Kubernetes/OpenShift using real infrastructure.
