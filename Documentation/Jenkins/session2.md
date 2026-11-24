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

```

<FollowUp label="Ready for me to generate Session 3 (Hours 5–6): Enterprise Agents, Secrets Management & Build Triggers?" query="Generate Session 3 (Hours 5–6): Enterprise Agents, Secrets Management & Build Triggers in clean GitHub Markdown without time-block durations, keeping all other sections from the Master Prompt."/>

<ElicitationsGroup message="Continue your 10-hour Jenkins & GitHub curriculum:">
  <Elicitation label="Generate Session 3 (Hours 5–6) now" query="Generate Session 3 (Hours 5–6): Enterprise Agents, Secrets Management & Build Triggers in clean GitHub Markdown without time-block durations."/>
  <Elicitation label="Generate Session 4 (Hours 7–8): DevSecOps & Registry Integration" query="Generate Session 4 (Hours 7–8): DevSecOps Quality Gates & Artifact Registry Integration in clean GitHub Markdown without time-block durations."/>
  <Elicitation label="Generate complete solution Jenkinsfile for Session 2 Mini-Project" query="Write the complete GitFlow Multibranch Jenkinsfile solution for the Session 2 Take-Home Mini-Project."/>
</ElicitationsGroup>

```
