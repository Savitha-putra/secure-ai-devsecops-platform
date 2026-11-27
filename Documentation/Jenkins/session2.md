```markdown
# Session 2 (Hours 3–4): Modern Pipeline Configuration & Git Integration

> **Course:** Enterprise Jenkins & GitHub CI/CD Engineering  
> **Target Audience:** Freshers & Aspiring DevOps / Platform Engineers  
> **Prerequisites:** Completion of Session 1 (Jenkins Controller + Agent setup, Git basics, Maven/JDK global tools configured).

---

## 1. Real-World Analogies & Architecture Diagrams

### Analogy 1: Freestyle Jobs vs. Pipeline-as-Code (`Jenkinsfile`)
* **Freestyle Jobs (Manual Point-and-Click):** Imagine giving a new chef verbal instructions over the phone every single day on how to cook a 5-course meal, and writing those notes on sticky notes taped to the kitchen wall. If a sticky note falls off (someone accidentally edits a UI checkbox) or the kitchen catches fire (server crashes), nobody remembers the exact recipe, and you cannot track who changed the salt measurement.
* **Pipeline-as-Code (`Jenkinsfile` in Git):** Imagine writing the exact recipe in a version-controlled cookbook stored in a fireproof vault (**GitHub**). Every time a chef wants to tweak the recipe, they open a Pull Request, another chef reviews it, and Git records the exact author, timestamp, and diff. Even if the entire kitchen burns down, you spin up a new Jenkins Controller, point it to GitHub, and your entire CI/CD workflow is instantly restored.

### Analogy 2: Multibranch Pipelines (Airport Runways)
* **Multibranch Pipeline:** Think of an international airport with automated air traffic control.
  * Small private planes (**`feature/*` branches**) land on short runways: they only get basic safety checks (Compile + Unit Tests).
  * Commercial flights (**`staging` branch**) go through full customs and baggage checks (Compile + Unit Tests + Integration Tests + Staging Artifact Build).
  * Flagship international jets (**`main` / `production` branch**) get VIP clearance, full security inspection, and final release approval (Full Build + Release Tagging + Production Deployment).
  * When a new flight appears in the sky (a developer pushes a new Git branch), Air Traffic Control (**Jenkins Multibranch**) automatically creates a runway for it—and removes the runway when the branch is merged and deleted!

---

### ASCII Architecture Diagram: GitHub + Multibranch Declarative Pipeline Flow

```text
+-----------------------------------------------------------------------------------+
|                            GITHUB REPOSITORY (my-java-app)                        |
|                                                                                   |
|   [Branch: feature/login] ---> Contains Jenkinsfile                               |
|   [Branch: staging]       ---> Contains Jenkinsfile                               |
|   [Branch: main]          ---> Contains Jenkinsfile                               |
+-----------------------------------------|-----------------------------------------+
                                          |
                                          | 1. Branch Indexing / Git Scan
                                          v
+-----------------------------------------------------------------------------------+
|                    JENKINS MULTIBRANCH PIPELINE CONTROLLER                        |
|                                                                                   |
|   +----------------------------+   +------------------------+   +--------------+  |
|   | Sub-Job: feature/login     |   | Sub-Job: staging       |   | Sub-Job: main|  |
|   | (Runs: Build + Unit Test)  |   | (Runs: + Integration)  |   | (Runs: +Prod)|  |
|   +-------------|--------------+   +-----------|------------+   +------|-------+  |
+-----------------|------------------------------|-----------------------|----------+
                  |                              |                       |
                  +------------------------------+-----------------------+
                                                 | 2. Dispatches to Labeled Agent
                                                 v
+-----------------------------------------------------------------------------------+
|                        JENKINS BUILD AGENT (Label: linux)                         |
|                                                                                   |
|   Stage 1: Checkout  -->  Stage 2: Build  -->  Stage 3: Test  -->  Post Actions   |
|   (git clone branch)      (mvn compile)        (mvn test)          (always/fail)  |
+-----------------------------------------------------------------------------------+

```

---

## 2. Deep-Dive Concepts with Production Examples

### 2.1 Freestyle Jobs vs. Declarative Pipeline-as-Code

| Feature / Dimension | Legacy Freestyle Jobs | Modern Declarative Pipeline (`Jenkinsfile`) |
| --- | --- | --- |
| **Configuration Storage** | Stored as hidden `config.xml` inside Jenkins UI | Stored as a text file (`Jenkinsfile`) inside your Git repository |
| **Audit Trail & Code Review** | Poor—anyone with UI access can change steps silently | Full Git history (`git blame`, Pull Request reviews) |
| **Complex Workflows** | Clunky—requires chaining multiple jobs together | Native support for parallel stages, conditionals (`when`), and retries |
| **Crash Recovery** | Lost unless `$JENKINS_HOME` was backed up | Zero data loss—re-importing the Git repo recreates everything |
| **Branch Awareness** | Requires cloning the job manually for every branch | Native via **Multibranch Pipeline** |

---

### 2.2 Declarative Pipeline Anatomy (`Jenkinsfile`)

A **Declarative Pipeline** always starts with the `pipeline { ... }` block and enforces a strict, predictable structure that is easy for teams to read and validate.

#### Core Building Blocks

1. **`agent`**: Tells Jenkins *where* to execute the pipeline (`any`, `none`, or `{ label 'linux' }`).
2. **`environment`**: Defines key-value environment variables accessible across stages (or scoped to a single stage).
3. **`tools`**: Automatically injects pre-configured global tools (`maven 'Maven-3.9'`, `jdk 'JDK-17'`) into `$PATH`.
4. **`stages` & `stage**`: Logical phases of your CI workflow (e.g., `Checkout`, `Build`, `Unit Test`, `Package`).
5. **`steps`**: The actual commands (`sh`, `echo`, `checkout`, `junit`) executed inside a stage.
6. **`when`**: Conditional logic controlling whether a stage runs (e.g., `branch 'main'`).
7. **`post`**: Cleanup and reporting actions that execute *after* stages finish (`always`, `success`, `failure`, `unstable`).

---

### 2.3 Complete Production `Jenkinsfile` Example (With Branch Conditions & Post-Actions)

Create this file at the **root** of your GitHub repository (`./Jenkinsfile`):

```groovy
pipeline {
    // 1. Run on any available agent tagged with 'linux' (never on Controller!)
    agent {
        label 'linux'
    }

    // 2. Inject global tools configured in Manage Jenkins -> Tools
    tools {
        maven 'Maven-3.9'
    }

    // 3. Pipeline-wide environment variables
    environment {
        APP_NAME    = 'payment-microservice'
        DEPLOY_ENV  = "${env.BRANCH_NAME == 'main' ? 'production' : 'non-prod'}"
        BUILD_TAG   = "${env.BRANCH_NAME}-${env.BUILD_NUMBER}"
    }

    // 4. Optional pipeline safeguards (prevent hung builds & save disk space)
    options {
        timeout(time: 15, unit: 'MINUTES')
        buildDiscarder(logRotator(numToKeepStr: '10'))
        timestamps()
    }

    stages {
        stage('1. Checkout & Metadata') {
            steps {
                echo "Building ${APP_NAME} | Branch: ${env.BRANCH_NAME} \vert{} Tag:${BUILD_TAG}"
                sh 'git log -1 --oneline'
            }
        }

        stage('2. Compile & Static Check') {
            steps {
                echo "Compiling Java source code..."
                sh 'mvn clean compile'
            }
        }

        stage('3. Run Unit Tests') {
            steps {
                echo "Executing JUnit test suite..."
                sh 'mvn test'
            }
            post {
                always {
                    // Publish JUnit XML test reports even if tests fail
                    junit allowEmptyResults: true, testResults: '**/target/surefire-reports/*.xml'
                }
            }
        }

        stage('4. Package Artifact') {
            steps {
                echo "Packaging JAR artifact (skipping tests already run in Stage 3)..."
                sh 'mvn package -DskipTests'
            }
        }

        stage('5. Staging Verification') {
            when {
                branch 'staging'
            }
            steps {
                echo "Deploying ${BUILD_TAG} to STAGING environment..."
                sh './scripts/deploy-staging.sh || echo "Staging smoke test simulated"'
            }
        }

        stage('6. Production Release Gate') {
            when {
                branch 'main'
            }
            steps {
                echo "Preparing PRODUCTION release artifact for ${APP_NAME}..."
                archiveArtifacts artifacts: 'target/*.jar', fingerprint: true
            }
        }
    }

    // 5. Post-Pipeline Actions (Executed after all stages finish)
    post {
        always {
            echo "Pipeline execution finished for ${BUILD_TAG}. Cleaning workspace..."
            cleanWs()
        }
        success {
            echo "SUCCESS: ${APP_NAME} (${BUILD_TAG}) passed all CI checks!"
        }
        failure {
            echo "FAILURE: Build #${env.BUILD_NUMBER} failed on branch${env.BRANCH_NAME}. Check console logs!"
        }
    }
}

```

---

### 2.4 Line-by-Line Highlights for Beginners

* **`scm` in Multibranch:** Notice there is no `git url: '...'` step inside Stage 1! In a **Multibranch Pipeline** or **Pipeline script from SCM**, Jenkins automatically checks out the exact repository and branch that triggered the build before Stage 1 starts.
* **`env.BRANCH_NAME`:** Built-in Jenkins environment variable populated automatically by Multibranch Pipelines (`feature/auth`, `staging`, `main`). Note: Standard single-branch Pipeline jobs do **not** populate `BRANCH_NAME`—only Multibranch jobs do!
* **`cleanWs()`:** Provided by the *Workspace Cleanup* plugin. Deletes temporary files on the agent after every build so leftover artifacts from an old build never corrupt the next build.

---

## 3. Industry Scenarios, Common Production Failures & DevOps Fixes

### How Enterprises Structure Branching with Multibranch Pipelines

In real enterprise engineering teams (e.g., GitHub Flow or Trunk-Based Development):

1. Developers cut a branch from `main`: `git checkout -b feature/JIRA-104-upi-payment`.
2. Every push triggers the `feature/JIRA-104-upi-payment` sub-pipeline in Jenkins, running Stages 1–4.
3. GitHub Branch Protection rules block merging the Pull Request unless Jenkins reports a green checkmark (`Status Check Passed`).
4. Once merged into `main`, Jenkins detects the commit on `main`, unlocks **Stage 6 (`when { branch 'main' }`)**, archives the signed artifact, and prepares it for deployment.
5. When the feature branch is deleted on GitHub after merge, Jenkins' **Orphaned Item Strategy** automatically deletes the stale sub-job so the dashboard stays clean.

### 4 Common Production Failures & How DevOps Fixes Them

| # | Real-World Failure / Symptom | Root Cause in Industry | Step-by-Step DevOps Fix |
| --- | --- | --- | --- |
| **1** | **`WorkflowScript: 12: Expected a step @ line 12`** (Groovy Syntax Error) | A developer edited `Jenkinsfile` directly on GitHub with a missing closing brace `}` or put Groovy code outside a `script { }` block inside Declarative syntax. | 1. Wrap complex Groovy loops/variables inside a `script { ... }` block.<br>

<br>2. Validate syntax before pushing using the **Jenkins Declarative Linter** (`curl -X POST -F "jenkinsfile=<Jenkinsfile" http://jenkins:8080/pipeline-model-converter/validate`). |
| **2** | **`env.BRANCH_NAME` evaluates to `null**` | The engineer created a standard **Pipeline** job instead of a **Multibranch Pipeline** job. | 1. Standard Pipeline jobs only set `GIT_BRANCH` (e.g., `origin/main`), not `BRANCH_NAME`.<br>

<br>2. Migrate the job to a **Multibranch Pipeline** or use `env.GIT_BRANCH` in single-branch jobs. |
| **3** | **Multibranch Dashboard has 300 dead branches from last year** | **Orphaned Item Strategy** was left unchecked or set to keep old branches forever. | 1. Open Multibranch Job $\rightarrow$ **Configure** $\rightarrow$ **Orphaned Item Strategy**.<br>

<br>2. Check **Discard old items** and set *Days to keep old items* = `3` and *Max # of old items to keep* = `10`. |
| **4** | **`ERROR: Couldn't find any revision to build. Verify the repository and branch configuration`** | Jenkins looked for `*/master` by default, whereas modern GitHub repositories use `main` as the default branch. | 1. In single-branch SCM config, change **Branch Specifier** from `*/master` to `*/main`.<br>

<br>2. Or switch to **Multibranch Pipeline**, which auto-discovers all branches regardless of name. |

---

## 4. Guided Hands-On Lab (Classroom Practical)

### Objective

Push a sample Maven/Java (or shell-simulated) project with a `Jenkinsfile` to GitHub, configure a **Pipeline from SCM**, and upgrade it to a **Multibranch Pipeline** managing `feature/*`, `staging`, and `main` branches.

### Step-by-Step Instructions

1. **Create a GitHub Repository (`jenkins-pipeline-demo`):**
* Log into GitHub and create a new public repository named `jenkins-pipeline-demo` initialized with a `README.md`.


2. **Clone Locally & Add `Jenkinsfile` + App Structure:**
```bash
git clone [https://github.com/](https://github.com/)<YOUR-USERNAME>/jenkins-pipeline-demo.git
cd jenkins-pipeline-demo

# Create a lightweight Maven pom.xml and sample Java class (or shell scripts)
mkdir -p src/main/java/com/edgex src/test/java/com/edgex scripts

```


* Copy the **Production `Jenkinsfile**` from **Section 2.3** into `./Jenkinsfile`.
* *(Tip: If you don't have a full Java project yet, replace `mvn clean compile` with `echo "Compiling..." && mkdir -p target && touch target/app.jar` and `mvn test` with `echo "All 12 unit tests passed!"` so you can test the pipeline mechanics immediately!)*
* Commit and push to `main`:
```bash
git add .
git commit -m "feat: add declarative Jenkinsfile"
git push origin main

```




3. **Create a Multibranch Pipeline in Jenkins:**
* Open Jenkins UI $\rightarrow$ **New Item**.
* Enter name: `payment-service-multibranch` $\rightarrow$ Select **Multibranch Pipeline** $\rightarrow$ Click **OK**.
* Under **Branch Sources**, click **Add source** $\rightarrow$ Select **GitHub** (or **Git**).
* Paste your repository HTTPS URL: `https://github.com/<YOUR-USERNAME>/jenkins-pipeline-demo.git`.
* Under **Build Configuration**, verify **Mode** = `by Jenkinsfile` and **Script Path** = `Jenkinsfile`.
* Under **Orphaned Item Strategy**, check **Discard old items** (Days: `5`, Max items: `10`).
* Click **Save**. Jenkins will immediately scan GitHub and trigger a build for `main`!


4. **Test Branch-Specific Behavior (`feature/login` vs. `staging` vs. `main`):**
```bash
# Create a feature branch and push
git checkout -b feature/login
echo "Feature login work" >> README.md
git commit -am "feat: add login logic"
git push origin feature/login

# Create a staging branch and push
git checkout -b staging
git push origin staging

```


* In Jenkins UI, click **Scan Repository Now** inside `payment-service-multibranch`.
* Observe how Jenkins discovers all 3 branches, runs Stage 5 **only** on `staging`, and runs Stage 6 **only** on `main`!



---

## 5. Take-Home Mini-Project (Portfolio / LinkedIn Ready)

### Project Title: *"GitFlow Multibranch CI Pipeline with Automated Quality & Branch Gates"*

#### Scenario

You are onboarding a 3-tier web application onto Jenkins. Developers work across `feature/*`, `staging`, and `main` branches. You must design a single `Jenkinsfile` that adapts its behavior dynamically based on the active branch without duplicating pipeline code.

#### Project Deliverables (Push to GitHub Repository `jenkins-multibranch-cicd`)

1. **Repository Branch Architecture:**
* Maintain three active branches in your GitHub repository: `main`, `staging`, and `feature/dashboard-ui`.


2. **Dynamic `Jenkinsfile` Requirements:**
* Must run on an agent labeled `linux` (never `agent any` if the Controller has executors).
* Must include at least **5 stages**: `Checkout & Info`, `Build`, `Test`, `Staging Deploy` (`when { branch 'staging' }`), and `Production Package` (`when { branch 'main' }`).
* Must implement a `post` block with `always` (workspace cleanup), `success`, and `failure` handlers.
* Must archive the built artifact (`target/*.jar` or `dist/*.tar.gz`) **only** on the `main` branch.


3. **Documentation (`README.md`):**
* Include a comparison table explaining why your team chose Declarative Multibranch Pipelines over Freestyle jobs.
* Include screenshots of the Jenkins Multibranch dashboard showing all 3 branches built with green status badges, highlighting skipped stages (`when` conditions) on `feature/dashboard-ui`.



---

## 6. Knowledge Check: 10 Multiple-Choice Questions (MCQs)

1. **What is the biggest operational disadvantage of Jenkins Freestyle jobs compared to Pipeline-as-Code (`Jenkinsfile`)?**
* A) Freestyle jobs cannot run shell commands on Linux
* B) Freestyle job configurations are stored in Jenkins UI XML rather than Git, making version control, code review, and disaster recovery difficult
* C) Freestyle jobs require a paid Enterprise license
* D) Freestyle jobs only support Windows agents


2. **In a Declarative `Jenkinsfile`, which top-level block is mandatory to define where the pipeline executes?**
* A) `node`
* B) `agent`
* C) `executor`
* D) `server`


3. **Which `post` condition runs regardless of whether the pipeline succeeded, failed, or was aborted?**
* A) `cleanup`
* B) `finally`
* C) `always`
* D) `unconditional`


4. **You want Stage 5 (`Deploy to Production`) to execute ONLY when Jenkins builds the `main` branch. Which directive should you use inside the stage?**
* A) `if (branch == 'main')`
* B) `when { branch 'main' }`
* C) `only { branch: 'main' }`
* D) `filter { gitBranch 'main' }`


5. **Why does `echo "${env.BRANCH_NAME}"` print `null` in a standard single-branch Pipeline job?**
* A) `BRANCH_NAME` is a deprecated variable removed in Jenkins 2.x
* B) `BRANCH_NAME` is populated automatically only by **Multibranch Pipeline** (and Organization Folder) jobs
* C) Environment variables must be wrapped in single quotes `'${env.BRANCH_NAME}'`
* D) You must install the Blue Ocean plugin first


6. **In Groovy / `Jenkinsfile` syntax, what is the difference between double quotes `"Hello ${BUILD_NUMBER}"` and single quotes `'Hello ${BUILD_NUMBER}'`?**
* A) There is no difference in Groovy
* B) Double quotes perform string interpolation (expanding variables), whereas single quotes treat `${BUILD_NUMBER}` as literal text
* C) Single quotes execute shell commands, while double quotes print comments
* D) Double quotes are only valid inside `post` blocks


7. **What happens in a Jenkins Multibranch Pipeline when a developer deletes a merged `feature/xyz` branch from GitHub?**
* A) Jenkins crashes with a `404 Repository Not Found` error
* B) Jenkins marks the sub-job as disabled/orphaned and removes it according to the **Orphaned Item Strategy**
* C) Jenkins automatically deletes the `main` branch as well
* D) Jenkins recreates the branch on GitHub


8. **Which `options` directive prevents a hung test suite from locking up a Jenkins build agent forever?**
* A) `retry(3)`
* B) `timeout(time: 15, unit: 'MINUTES')`
* C) `disableConcurrentBuilds()`
* D) `skipDefaultCheckout()`


9. **What is the purpose of the `archiveArtifacts` step in a `Jenkinsfile`?**
* A) To compress and push Docker images to Docker Hub
* B) To copy generated build outputs (like `.jar`, `.war`, or `.zip` files) from the temporary Agent workspace onto the Controller so they can be downloaded later
* C) To delete old Git commits
* D) To back up `/var/lib/jenkins/plugins`


10. **How can you validate a `Jenkinsfile` for syntax errors from your local terminal before pushing it to GitHub?**
* A) Run `bash -n Jenkinsfile`
* B) Send the file to the Jenkins Controller's `/pipeline-model-converter/validate` REST API endpoint using `curl`
* C) Run `mvn validate Jenkinsfile`
* D) Rename it to `Jenkinsfile.json` and run `jq`



1. **B** — Storing CI/CD definitions in Git (`Jenkinsfile`) treats build logic just like application source code with full PR reviews and history.
2. **B** — Every Declarative Pipeline requires a top-level `agent` directive (even if set to `agent none` when individual stages define their own agents).
3. **C** — `always` executes at the end of a pipeline or stage regardless of build outcome, making it ideal for cleanup and reporting.
4. **B** — The `when { branch 'main' }` block is the native Declarative construct for branch-based stage execution.
5. **B** — Only Multibranch Pipelines and GitHub Organization Folders populate `env.BRANCH_NAME`. Standard pipelines use `env.GIT_BRANCH`.
6. **B** — In Groovy, double-quoted strings (`GString`) interpolate `${...}` variables, while single-quoted strings are plain `java.lang.String` literals.
7. **B** — Multibranch Pipelines track branch lifecycles and prune deleted branches based on your configured Orphaned Item Strategy.
8. **B** — `timeout(time: 15, unit: 'MINUTES')` aborts the pipeline and frees the agent executor if execution exceeds 15 minutes.
9. **B** — Because agent workspaces are temporary (and often wiped by `cleanWs()`), `archiveArtifacts` preserves important build binaries on the Controller.
10. **B** — Jenkins provides a built-in CLI/HTTP linter endpoint (`/pipeline-model-converter/validate`) to catch Declarative syntax errors pre-commit.

---

## 7. Deep-Dive Research & Homework Questions (10 Investigative Prompts)

Complete these investigations at home before **Session 3** to sharpen your pipeline engineering skills:

1. **Declarative vs. Scripted Pipelines:** Research the historical and architectural differences between **Declarative Pipelines** (`pipeline { ... }`) and legacy **Scripted Pipelines** (`node { ... }`). When would you use a `script { ... }` block inside a Declarative Pipeline?
2. **Stage-Level Agents (`agent none`):** How do you configure a `Jenkinsfile` with `agent none` at the top level so Stage 1 runs on a `maven` agent and Stage 2 runs on a `docker` agent? Write a 15-line snippet demonstrating this.
3. **Parallel Stage Execution:** Suppose your microservice has 3 independent test suites (`Unit Tests`, `Linting`, `API Contract Tests`) taking 4 minutes each. Research the Declarative `parallel { ... }` block and calculate how much total pipeline time it saves.
4. **Groovy String Interpolation Security Warning:** Why does Jenkins log a warning *"Insecure interpolation of sensitive variables"* if you write `sh "echo ${SECRET_TOKEN}"` with double quotes instead of single quotes `sh 'echo $SECRET_TOKEN'`?
5. **Input Step for Manual Production Approvals:** Research the `input` step (`input message: 'Approve Production Deployment?', ok: 'Deploy'`). What happens to the build agent executor if you put `input` *inside* a stage that already holds an `agent` lock while a manager takes 4 hours to click Approve?
6. **Git Shallow Clone Optimization:** For a massive enterprise monorepo (5 GB Git history), `git clone` takes 8 minutes per build. Research how to configure **Shallow Clone** (`depth: 1`) in a Multibranch Pipeline to cut checkout time to 10 seconds.
7. **Blue Ocean Visual Editor:** Open your Multibranch Pipeline in **Blue Ocean** (`http://localhost:8080/blue`). Compare how skipped `when` stages and stage logs are visualized compared to the classic UI.
8. **Environment Variable Precedence:** If `APP_ENV = 'dev'` is defined at the top-level `environment` block, and `APP_ENV = 'prod'` is defined inside a specific `stage('Deploy')` `environment` block, which value wins inside that stage?
9. **Retry & CatchError Steps:** Research the difference between `retry(3) { sh './flaky-network-call.sh' }` and `catchError(buildResult: 'SUCCESS', stageResult: 'FAILURE')`. Give one real-world DevOps use case for each.
10. **Preparation for Session 3:** Look up **Docker-in-Docker (DinD)** vs. **Docker Socket Mounting (`/var/run/docker.sock`)** on Jenkins agents—we will use Docker containers as ephemeral build agents in Session 3!

# **Session 3: Jenkins and GitHub Integration**

**GitHub filename:** `03-jenkins-github-integration.md`

**Training platform:** Prepare.sh Jenkins Playground\
**Level:** Beginner to Intermediate\
**Duration:** 2 Hours\
**Prerequisite:** Session 2 – Declarative Jenkins Pipeline + 25 practical exercises.

## **1. Session Objectives**

By the end of this session, students should understand:

1. What is GitHub integration with Jenkins?
2. How Jenkins communicates with GitHub.
3. What is a Git repository?
4. What is source-code checkout?
5. What is the Jenkins Git plugin?
6. How to configure a GitHub repository in Jenkins.
7. How to retrieve source code using a Pipeline.
8. What is a branch?
9. What are GitHub credentials and why are they required?
10. What are webhooks?
11. How code changes can trigger Jenkins builds.

**Today's practical goal:** Build a Jenkins Pipeline that retrieves application source code from GitHub and displays its files.

# **2. What Is GitHub Integration with Jenkins?**

Imagine a developer is working on a Java application.

After making code changes, the developer pushes the changes to GitHub.

The DevOps team wants Jenkins to automatically download the latest source code and start the build process.

This is called Jenkins and GitHub integration.

## **Jenkins + GitHub workflow**

**Developer**

Writes application code

git push

**GitHub Repository**

Stores application source code

Checkout source code

**Jenkins**

Automates CI/CD pipeline

**Build**

**Testing**

**Security Scan**

**Deployment**

# **3. Important Git and GitHub Concepts**

Before connecting Jenkins to GitHub, students must understand these terms.

| Term       | Simple explanation                             |
| ---------- | ---------------------------------------------- |
| Git        | Version control system                         |
| GitHub     | Cloud platform for hosting Git repositories    |
| Repository | Storage location for project files and history |
| Clone      | Download a repository                          |
| Commit     | Save a snapshot of changes in Git              |
| Push       | Upload commits to a remote repository          |
| Pull       | Fetch and integrate remote changes             |
| Branch     | Separate line of development                   |
| Checkout   | Switch to a branch or retrieve source code     |
| Remote URL | Address of a Git repository                    |

## **4. Understand Public and Private Repositories**

GitHub repositories can be public or private.

[Yaak Is Now Open Source | Sarah Conway](https://images.openai.com/static-rsc-4/1A7ISj_N0m_fA-E6fgw6iep23q1LR2iAAgWkqv5WSYeUKvh2B2MSkoLKyfTW30a7y89_AEhWY3w11kKF1fxNmG5nWuEocWVGAYgv2o0A7pQU6TGVhqDyM4wYB2aGwFO5TD7uEY3-EU-fZkU2Jx-SyO9eqWQAokueN6NxGIkhR-M?purpose=inline)

**Public repository**

Anyone can access and clone the repository, subject to its settings.

[Optimizing GitHub security at Sendbird: Challenges & key takeaways | Sendbird](https://images.openai.com/static-rsc-4/htyN7Gh_DYACWXSwd8zoLtRZp_cFklx7Se6bivTeEnQLnIKtH9v_I9H455fisZPA7ASNGmx6xS7CHlTBJdYaxM45NHU42OwC0z6LVWyUCXFbYyXXWk_N7GMCeZVVEF0vqLSm4doQN6MuwoRpy7I1Vi1FIcQgA85BKy1ck3zHtZM?purpose=inline)

**Private repository**

Access is restricted to authorized users and applications.

For today's training, start with a public repository. This avoids credential configuration initially.

# **5. Practical 1 – Create Your First GitHub Repository**

Students will create a repository to store their Jenkins training application.

### **Step 1: Open GitHub**

Visit: [GitHub](https://github.com/?utm_source=chatgpt.com)

1. Sign in to GitHub.
2. Click New Repository.
3. Repository name:

```
jenkins-github-training
```

4. Select Public.
5. Select Add a README file.
6. Click Create Repository.

### **Step 2: Create Sample Application Files**

Inside the repository, create the following files.

**File 1:&#x20;**`app.txt`

```
Application Name: Banking Application
Version: 1.0
Environment: Development
Developer: Jenkins Training Student
```

**File 2:&#x20;**`build.sh`

```
#!/bin/bash

echo "Starting Application Build"
echo "Application: Banking Application"
echo "Version: 1.0"
echo "Build Completed Successfully"
```

**File 3:&#x20;**`README.md`

```
# Jenkins GitHub Integration

This repository is created for Jenkins training.

## Application Details

- Application: Banking Application
- Version: 1.0
- Environment: Development

## Purpose

Practice Jenkins source code checkout
and automated CI/CD pipelines.
```

Commit the files to your repository.

# **6. Practical 2 – Understand Git Clone**

Before configuring Jenkins, understand how Git downloads source code.

If you have Git installed on your Linux machine, execute:

```
git clone https://github.com/YOUR-USERNAME/jenkins-github-training.git
```

Replace `YOUR-USERNAME` with your actual GitHub username.

Move inside the repository:

```
cd jenkins-github-training
```

List files:

```
ls -l
```

Read the application details:

```
cat app.txt
```

Check Git repository information:

```
git status
```

Check the current branch:

```
git branch
```

Check the remote repository:

```
git remote -v
```

**Understand the difference:**

- `git clone`: Downloads a repository.
- `git checkout`: Switches branches or restores files.
- Jenkins `git` pipeline step: Checks out source code into the Jenkins workspace.

# **7. Practical 3 – Connect Jenkins to a Public GitHub Repository**

This is the most important exercise of today's session.

### **Step 1: Open Jenkins**

Open your Prepare.sh Jenkins Playground.

Create a new Pipeline job:

```
jenkins-github-checkout
```

### **Step 2: Configure Pipeline Script**

Use the following Jenkinsfile.

Replace the repository URL with your own public GitHub repository URL.

```
pipeline {
    agent any

    stages {

        stage('Checkout') {
            steps {
                echo 'Downloading Source Code from GitHub'

                git branch: 'main',
                    url: 'https://github.com/YOUR-USERNAME/jenkins-github-training.git'
            }
        }

        stage('List Files') {
            steps {
                sh 'pwd'
                sh 'ls -l'
            }
        }

        stage('Read Application Details') {
            steps {
                sh 'cat app.txt'
            }
        }

        stage('Build') {
            steps {
                sh 'bash build.sh'
            }
        }
    }
}
```

### **Step 3: Execute the Pipeline**

1. Save the pipeline.
2. Click Build Now.
3. Open Console Output.
4. Observe the Checkout stage.
5. Verify that Jenkins downloads the GitHub files.
6. Verify that the Build stage executes.

Expected output (illustrative):

```
Downloading Source Code from GitHub

Checking out Revision ...

Application Name: Banking Application
Version: 1.0
Environment: Development

Starting Application Build
Application: Banking Application
Version: 1.0
Build Completed Successfully

Finished: SUCCESS
```

Success criteria

Jenkins should retrieve the files from GitHub and execute `build.sh`.

**Important:** This requires the Jenkins Git plugin, a compatible Git installation and a Linux/Unix agent for the shell commands.

# **8. Understand Jenkins Workspace**

What happens after Jenkins downloads the GitHub repository?

Jenkins stores the checked-out files in its workspace for that job.

The workspace is the working directory where Jenkins performs its build operations.

Example:

```
Jenkins
   |
   +--- Workspace
           |
           +--- app.txt
           |
           +--- build.sh
           |
           +--- README.md
```

Execute the following pipeline commands:

```
pipeline {
    agent any

    stages {
        stage('Workspace Information') {
            steps {
                echo "Workspace: ${WORKSPACE}"

                sh '''
                    echo "Files inside workspace:"
                    ls -la

                    echo "Current directory:"
                    pwd
                '''
            }
        }
    }
}
```

**Student task:**

1. Execute the pipeline.
2. Identify the workspace location.
3. Find the downloaded application files.
4. Explain why Jenkins needs a workspace.

# **9. Practical 4 – Checkout a Specific GitHub Branch**

In real organizations, developers work with different branches.

Example:

```
main
  |
  +--- development
  |
  +--- feature-login
  |
  +--- bugfix-payment
```

Jenkins can retrieve a particular branch.

Example:

```
pipeline {
    agent any

    stages {
        stage('Checkout Development') {
            steps {
                git branch: 'development',
                    url: 'https://github.com/YOUR-USERNAME/jenkins-github-training.git'
            }
        }

        stage('Verify Branch') {
            steps {
                sh 'git branch --show-current'
                sh 'git log -1 --oneline'
            }
        }
    }
}
```

Before executing, create the `development` branch in your GitHub repository.

**Student task:**

1. Create a branch called `development`.
2. Add a file called `development.txt`.
3. Commit the file.
4. Modify Jenkinsfile to checkout `development`.
5. Verify that Jenkins retrieves the correct branch.

# **10. Practical 5 – Checkout and Build Automatically**

Let's combine GitHub checkout with the Declarative Pipeline knowledge from Session 2.

```
pipeline {
    agent any

    environment {
        APP_NAME = 'BankingApplication'
        VERSION = '1.0'
    }

    stages {

        stage('Checkout') {
            steps {
                git branch: 'main',
                    url: 'https://github.com/YOUR-USERNAME/jenkins-github-training.git'
            }
        }

        stage('Verify Source Code') {
            steps {
                sh '''
                    echo "Checking source code"

                    ls -la

                    test -f app.txt
                    test -f build.sh
                '''
            }
        }

        stage('Build') {
            steps {
                sh 'bash build.sh'
            }
        }

        stage('Testing') {
            steps {
                echo 'Executing Application Tests'
                sh 'test -f app.txt'
            }
        }

        stage('Deployment Simulation') {
            steps {
                echo "Deploying ${APP_NAME} version ${VERSION}"
            }
        }
    }

    post {
        success {
            echo 'GitHub Integration Pipeline Successful'
        }

        failure {
            echo 'GitHub Integration Pipeline Failed'
        }

        always {
            echo 'Pipeline Execution Completed'
        }
    }
}
```

**Student task:** Add a stage named `Code Quality Check` between Build and Testing.

# **11. GitHub Authentication – Public vs Private Repositories**

For a public repository, Jenkins can generally clone source code without authentication.

For private repositories, Jenkins needs authorized access.

The recommended approach is to use Jenkins Credentials.

## **What is a GitHub Personal Access Token?**

A Personal Access Token (PAT) is an authentication token that can be used to access GitHub resources.

It is commonly used for Git operations requiring authentication.

For private repository access, a fine-grained token can be configured with access to the selected repository and the necessary repository permissions, such as Contents: Read-only.

GitHub documentation: [Managing Personal Access Tokens](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens?utm_source=chatgpt.com).

## **Step 1: Create a GitHub Token**

For this exercise:

1. Open GitHub.
2. Go to Settings.
3. Open Developer Settings.
4. Select Personal Access Tokens.
5. Select Fine-grained tokens.
6. Create a token.
7. Restrict repository access to your training repository.
8. Grant the minimum required permissions.
9. Generate and copy the token.

Security rule

Never paste the token into a Jenkinsfile, GitHub repository, screenshot or Console Output.

## **Step 2: Configure Jenkins Credentials**

In Jenkins:

1. Open Manage Jenkins.
2. Open Credentials.
3. Select the appropriate credential store and domain.
4. Add Credentials.
5. Select Username with password.
6. Enter your GitHub username.
7. Use the PAT as the password.
8. Set the ID:

```
github-training-credentials
```

9\. Save.

## **Step 3: Use Credentials in Jenkinsfile**

```
pipeline {
    agent any

    stages {

        stage('Checkout Private Repository') {
            steps {
                git branch: 'main',

                    credentialsId: 'github-training-credentials',

                    url: 'https://github.com/YOUR-USERNAME/PRIVATE-REPOSITORY.git'
            }
        }

        stage('Verify Checkout') {
            steps {
                sh 'ls -la'
            }
        }
    }
}
```

**Student task:** If your playground supports credentials, configure a private repository and test the checkout.

If credential management is unavailable, complete the public repository exercise and document this as a playground limitation.

# **12. What Is a GitHub Webhook?**

So far, we have manually clicked Build Now to start a Jenkins pipeline.

In a production CI/CD environment, we want Jenkins to start automatically when a developer pushes code.

This is where GitHub Webhooks are useful.

A webhook is a mechanism through which GitHub sends an HTTP event notification to an external application such as Jenkins.

## **Webhook workflow**

**Developer**

Changes application code

git push

**GitHub**

Sends webhook notification

HTTP POST event

**Jenkins**

Receives event and triggers build

**CI/CD Pipeline**

Checkout → Build → Test → Deploy

## **Why use Webhooks?**

Without webhooks:

- Engineers may need to manually start builds.
- Jenkins may periodically check GitHub for changes.
- Build initiation may be delayed.

With webhooks:

- GitHub notifies Jenkins when configured events occur.
- Jenkins can start builds based on those notifications.
- It supports event-driven CI/CD automation.

## **Practical webhook configuration**

This requires a Jenkins endpoint that GitHub can reach over the network.

### **Step 1: Configure Jenkins**

Open your Pipeline job.

Under Build Triggers, select:

```
GitHub hook trigger for GITScm polling
```

Save the job.

### **Step 2: Configure GitHub**

Open your GitHub repository.

1. Go to Settings.
2. Select Webhooks.
3. Click Add webhook.
4. Enter the publicly reachable Jenkins webhook endpoint.

For a standard Jenkins GitHub plugin configuration, the endpoint is:

```
https://YOUR-JENKINS-URL/github-webhook/
```

5. Select application/json as the content type.
6. Select the push event.
7. Save the webhook.

### **Step 3: Test**

1. Modify `app.txt` in GitHub.
2. Commit the change.
3. Push the change.
4. Check the GitHub webhook delivery.
5. Check Jenkins build history.

**Important:** A browser-based playground may not expose a publicly reachable Jenkins endpoint. In that case, you can learn and configure the job trigger if supported, but cannot complete an external GitHub webhook delivery test. Do not assume a successful manual build proves webhook integration.

# **13. Webhook vs Poll SCM**

These are two different ways Jenkins can detect source-code changes.

| Feature             | Webhook                             | Poll SCM                                 |
| ------------------- | ----------------------------------- | ---------------------------------------- |
| Communication       | GitHub sends notification           | Jenkins checks GitHub                    |
| Trigger             | Event-driven                        | Scheduled checking                       |
| Speed               | Usually faster                      | Depends on schedule                      |
| Network requirement | Jenkins must be reachable by GitHub | Jenkins needs outbound repository access |
| Production usage    | Commonly preferred                  | Useful alternative                       |

Example Poll SCM configuration:

```
H/5 * * * *
```

This tells Jenkins to check approximately every five minutes, with Jenkins distributing the polling interval.

In a Pipeline, you can configure polling using:

```
pipeline {
    agent any

    triggers {
        pollSCM('H/5 * * * *')
    }

    stages {
        stage('Build') {
            steps {
                echo 'Checking source code changes'
            }
        }
    }
}
```

Note: Polling requires a suitable SCM configuration. For GitHub webhooks, the GitHub integration and job trigger must also be configured correctly.

# **14. Troubleshooting Common Jenkins and GitHub Errors**

A DevOps engineer must know how to troubleshoot integration problems.

| Error                  | Possible reason                     | Troubleshooting                       |
| ---------------------- | ----------------------------------- | ------------------------------------- |
| Repository not found   | Incorrect URL or private repository | Verify repository URL and permissions |
| Authentication failed  | Incorrect credentials               | Verify Jenkins credentials            |
| Branch not found       | Incorrect branch name               | Check GitHub branches                 |
| Git command not found  | Git missing on agent                | Install/configure Git                 |
| Permission denied      | Insufficient repository access      | Verify token permissions              |
| Checkout failed        | Network or Git plugin issue         | Check agent connectivity and logs     |
| Webhook not triggering | Jenkins endpoint inaccessible       | Check webhook delivery                |
| File not found         | Incorrect workspace or filename     | Check `pwd` and `ls -la`              |

### **Troubleshooting Exercise**

Intentionally modify your Jenkinsfile:

```
git branch: 'wrong-branch',
    url: 'https://github.com/YOUR-USERNAME/jenkins-github-training.git'
```

Execute the pipeline.

Students must answer:

1. Why did checkout fail?
2. How did you identify the error?
3. What is the correct branch?
4. How did you fix it?

# **15. Additional Production Concept – Pipeline from SCM**

Until now, we have written the pipeline script directly inside Jenkins.

In production, teams often store the Jenkinsfile in GitHub itself.

For example:

```
jenkins-github-training/
│
├── Jenkinsfile
├── app.txt
├── build.sh
├── README.md
│
└── src/
    └── app.py
```

Jenkins can retrieve the Jenkinsfile from the Git repository and execute it.

In a Pipeline job:

1. Select New Item.
2. Enter a job name.
3. Select Pipeline.
4. Find Pipeline Definition.
5. Select Pipeline script from SCM.
6. Select Git.
7. Enter the repository URL.
8. Select the branch.
9. Enter `Jenkinsfile` as the Script Path.
10. Save and execute.

This approach is useful because the application code and CI/CD pipeline configuration can be maintained together.

# **16. Complete Practical Challenge**

Today's final assignment

**Scenario: Banking Application CI/CD**

You are a DevOps Engineer responsible for integrating a developer's GitHub repository with Jenkins.

Your requirement:

Whenever Jenkins executes the pipeline, it must:

1. Download source code from GitHub.
2. Display repository files.
3. Read application information.
4. Execute the build script.
5. Perform basic validation.
6. Display build information.
7. Report pipeline success or failure.

### **Final Jenkinsfile**

```
pipeline {
    agent any

    environment {
        APP_NAME = 'BankingApplication'
        VERSION = '1.0'
        DEPLOY_ENV = 'Development'
    }

    stages {

        stage('Checkout Source Code') {
            steps {
                echo 'Connecting to GitHub'

                git branch: 'main',
                    url: 'https://github.com/YOUR-USERNAME/jenkins-github-training.git'
            }
        }

        stage('Repository Validation') {
            steps {
                sh '''
                    echo "Checking repository files"

                    pwd
                    ls -la

                    test -f app.txt
                    test -f build.sh
                '''
            }
        }

        stage('Application Information') {
            steps {
                sh 'cat app.txt'
            }
        }

        stage('Build') {
            steps {
                echo "Building ${APP_NAME}"

                sh 'bash build.sh'
            }
        }

        stage('Testing') {
            steps {
                echo 'Running Application Validation'

                sh 'test -f app.txt'
            }
        }

        stage('Deployment Simulation') {
            steps {
                echo "Deploying ${APP_NAME}"
                echo "Version: ${VERSION}"
                echo "Environment: ${DEPLOY_ENV}"
            }
        }
    }

    post {
        success {
            echo 'Banking Application Pipeline Successful'
        }

        failure {
            echo 'Banking Application Pipeline Failed'
        }

        always {
            echo 'Jenkins GitHub Integration Completed'
        }
    }
}
```

**Expected result:** A successful Jenkins build that retrieves the repository and executes the application build script.

# **17. Student Homework – 10 Exercises**

| No. | Assignment                                                                               | Difficulty |
| --- | ---------------------------------------------------------------------------------------- | ---------- |
| 1   | Create a public GitHub repository                                                        | Easy       |
| 2   | Upload three application files                                                           | Easy       |
| 3   | Clone the repository using Git                                                           | Easy       |
| 4   | Configure Jenkins GitHub checkout                                                        | Easy       |
| 5   | Display all repository files in Jenkins                                                  | Easy       |
| 6   | Checkout a specific branch                                                               | Medium     |
| 7   | Execute a shell script downloaded from GitHub                                            | Medium     |
| 8   | Configure private repository credentials                                                 | Medium     |
| 9   | Store Jenkinsfile in GitHub and configure Pipeline from SCM                              | Advanced   |
| 10  | Configure GitHub webhook and test automatic triggering, where the playground supports it | Advanced   |

# **18. Interview Questions**

**Q1. What is GitHub integration with Jenkins?**

It is the process of connecting Jenkins with GitHub to retrieve source code and automate software delivery.

**Q2. What is source-code checkout?**

It is retrieving source code from a version control repository into a working directory.

**Q3. What is the Git plugin in Jenkins?**

It enables Jenkins jobs to interact with Git repositories for operations such as source-code checkout.

**Q4. What is the difference between Git and GitHub?**

Git is a version control system. GitHub is a platform that hosts Git repositories and provides collaboration features.

**Q5. What is a GitHub webhook?**

A webhook sends an HTTP event notification to Jenkins when a configured repository event occurs.

**Q6. What is a Personal Access Token?**

A token used to authenticate and authorize access to GitHub resources.

**Q7. How do you connect Jenkins to a private GitHub repository?**

Configure appropriate Jenkins Credentials and reference the credential ID in the Git checkout configuration.

**Q8. What is Pipeline from SCM?**

It allows Jenkins to retrieve the Jenkinsfile from a source-code management repository such as GitHub.

**Q9. What is the Jenkins workspace?**

The working directory where Jenkins checks out source code and executes build operations.

**Q10. What is the difference between webhook and Poll SCM?**

Webhook is event-driven notification from GitHub. Poll SCM is periodic checking initiated by Jenkins.

# **19. GitHub Training Repository Structure**

Ask students to maintain the following structure:

```
jenkins-training/
│
├── 01-jenkins-architecture.md
│
├── 02-declarative-pipeline.md
│
├── 02A-25-pipeline-examples.md
│
├── 03-jenkins-github-integration.md
│
├── application/
│   ├── app.txt
│   ├── build.sh
│   ├── README.md
│   └── Jenkinsfile
│
├── screenshots/
│   ├── github-repository.png
│   ├── checkout-success.png
│   ├── workspace-files.png
│   ├── build-success.png
│   └── webhook-configuration.png
│
└── README.md
```

# **20. Session Completion Checklist**

**Student progress**

# **0%**

0 of 13 completed

Understand Git and GitHub concepts

Create a GitHub repository

Create application files

Understand git clone and checkout

Configure Jenkins GitHub checkout

Retrieve source code from GitHub

Understand Jenkins workspace

Checkout a specific branch

Understand private repository credentials

Understand GitHub webhooks

Understand Poll SCM

Complete final banking application pipeline

Upload Jenkinsfile and screenshots to GitHub

## **Trainer's instructions**

Do not move to the next session until students can independently:

- Connect Jenkins to a public GitHub repository.
- Retrieve source code.
- Execute a downloaded shell script.
- Explain Jenkins workspace.
- Identify and troubleshoot checkout failures.
- Explain how webhooks trigger builds.

**Important:** Prepare.sh is the training playground. If it does not support external webhooks, private credentials or particular plugins, demonstrate the concepts and document the limitations rather than pretending the integrations were successful.

## **Next session**

Session 4

# **Jenkins Build Parameters, Environment Variables and Credentials**

Students will learn:

- String, Boolean and Choice parameters.
- Passing values into Jenkins pipelines.
- Environment variables in production pipelines.
- Secure credentials management.
- Parameterized deployments.
- Building reusable CI/CD workflows.

**Trainer recommendation:** Before Session 4, give students time to complete the GitHub checkout exercises and upload their working Jenkinsfiles to GitHub.
