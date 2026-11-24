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

```

<FollowUp label="Want me to generate a complete GitHub repository starter pack (sample Java app, Dockerfile, Shared Library, and README) for your students' Capstone?" query="Generate a complete, ready-to-push GitHub repository starter pack for the Session 5 Capstone including a minimal pom.xml, Dockerfile, vars/standardJavaPipeline.groovy, and microservice Jenkinsfile."/>

<ElicitationsGroup message="Wrap up or expand your EdgeX Learning Jenkins & GitHub module:">
  <Elicitation label="Generate complete Capstone starter code files" query="Provide complete starter code files (pom.xml, HelloApp.java, Dockerfile, vars/standardJavaPipeline.groovy, and Jenkinsfile) so students can run the Session 5 Capstone immediately."/>
  <Elicitation label="Create a 25-question Final Assessment Exam for students" query="Create a 25-question comprehensive final exam covering all 5 sessions of the Jenkins & GitHub curriculum with an answer key for grading students."/>
  <Elicitation label="Build an interview prep Q&A sheet for Jenkins & DevSecOps" query="Create a top 20 real-world Jenkins & DevSecOps interview questions and answers guide tailored for freshers and junior DevOps engineers."/>
</ElicitationsGroup>

```
