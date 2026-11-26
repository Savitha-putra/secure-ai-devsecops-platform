# 🚀 Jenkins Learning Resources

Welcome! Below are curated official Jenkins documentation links and core pipeline concepts to help you get started with CI/CD pipelines and hands-on tutorials.

---

## 📚 Official Guides & Tutorials

| Resource | Description | Link |
| :--- | :--- | :--- |
| **Pipeline Tour: Hello World** | A quick-start guide to creating and running your first declarative Jenkins Pipeline using a `Jenkinsfile`. | [Read Guide](https://www.jenkins.io/doc/pipeline/tour/hello-world/) |
| **Jenkins Tutorials** | Step-by-step hands-on tutorials covering Docker, Maven, Node.js, Python, and multi-branch pipelines. | [Explore Tutorials](https://www.jenkins.io/doc/tutorials/) |

---

## ⚙️ Declarative vs. Scripted Pipelines

Understanding the two Jenkins Pipeline syntaxes will help you choose the right structure for your `Jenkinsfile`:

* **Declarative Pipeline:** A modern, structured syntax designed for simplicity and readability, enforcing a strict pre-defined structure with built-in error handling and validation.
* **Scripted Pipeline:** The original syntax, built on the full power of the Groovy programming language, offering maximum flexibility and imperative control for complex logic.

> **Performance Note:** Both run on the same Jenkins subsystem with identical performance, differing only in syntax and flexibility.

### 🎯 Which One Should You Use?

* **Use Declarative Pipeline** for **90% of cases**—especially for new projects, standard CI/CD workflows, and teams seeking ease of maintenance, readability, and built-in directives like `options` and `environment`.
* **Use Scripted Pipeline** only when you require dynamic stage generation, complex loops, or deep integration with Groovy APIs that exceed the capabilities of Declarative syntax.

💡 **Best Practice:** For most needs, the recommended approach is to use a **Declarative Pipeline** with a `script {}` block to inject specific Groovy logic when necessary, balancing structure with flexibility.

---

## ✅ Quick Checklist for Students

- [ ] Read the **Hello World** pipeline tour to understand basic `pipeline`, `agent`, and `stages` syntax.
- [ ] Review the differences between **Declarative** and **Scripted** pipelines above.
- [ ] Pick a stack-specific project from the **Jenkins Tutorials** page and run it locally or in your lab environment.
- [ ] Commit your working `Jenkinsfile` to your GitHub repository.


```markdown
# Jenkins Pipelines: Declarative vs Scripted

## Declarative Pipeline

A structured, opinionated DSL with a **fixed skeleton** that must follow a strict order. Introduced in Pipeline plugin 2.5. **Recommended for new projects.**

### Required Structure

```groovy
pipeline {
    agent any
    stages {
        stage('Build') {
            steps {
                sh 'make'
            }
        }
        stage('Test') {
            steps {
                sh 'make check'
                junit 'reports/**/*.xml'
            }
        }
    }
}
```

### Key Directives

| Directive | Scope | Purpose |
|---|---|---|
| `agent` | Pipeline or stage | Where to run: `any`, `label`, `docker`, `kubernetes`, `none` |
| `options` | Pipeline or stage | `timeout`, `retry`, `timestamps`, `disableConcurrentBuilds` |
| `environment` | Pipeline or stage | Set env vars, inject credentials |
| `parameters` | Pipeline only | Runtime user inputs (string, boolean, choice, text) |
| `triggers` | Pipeline only | Cron, SCM polling, upstream job triggers |
| `tools` | Pipeline or stage | Auto-install JDK, Maven, Node from Global Tool Config |
| `when` | Stage only | Conditional execution: `branch`, `expression`, `environment` |
| `parallel` | Inside stages | Run multiple stages simultaneously |
| `post` | Pipeline or stage | Cleanup: `always`, `success`, `failure`, `unstable`, `aborted` |
| `script` | Inside steps | Escape hatch for Groovy logic |

### Full Example

```groovy
pipeline {
    agent any

    options {
        timeout(time: 30, unit: 'MINUTES')
        retry(2)
        timestamps()
        disableConcurrentBuilds()
    }

    parameters {
        choice(name: 'ENV', choices: ['staging', 'production'])
        booleanParam(name: 'RUN_INTEGRATION_TESTS', defaultValue: true)
    }

    environment {
        APP_NAME = 'myapp'
    }

    stages {
        stage('Build') {
            steps {
                sh 'mvn clean package -DskipTests -q'
            }
        }
        stage('Unit Tests') {
            steps {
                sh 'mvn test -q'
            }
            post {
                always { junit '**/surefire-reports/*.xml' }
            }
        }
        stage('Integration Tests') {
            when {
                expression { return params.RUN_INTEGRATION_TESTS }
            }
            steps {
                sh 'mvn verify -q'
            }
        }
        stage('Deploy') {
            when {
                branch 'main'
            }
            steps {
                input message: "Deploy to ${params.ENV}?", ok: 'Deploy'
                sh "./deploy.sh ${params.ENV}"
            }
        }
    }

    post {
        success { echo "Build succeeded!" }
        failure { echo "Build failed - check logs" }
        always  { cleanWs() }
    }
}
```

### What Makes It Special

- **Automatic SCM checkout** — no need to write `checkout scm`
- **Built-in validation** — linter catches structural errors *before* the build runs
- **Restart from stage** — re-run any top-level stage of a completed build
- **`when`-skipped stages still appear** in the stage view as "skipped"
- **`post` replaces `try/catch/finally`** — declarative and can't be accidentally skipped

---

## Scripted Pipeline

A **general-purpose Groovy DSL** with no enforced structure. The original Pipeline syntax. Gives full power of the Groovy language.

### Minimal Structure

```groovy
node {
    stage('Build') {
        sh 'make'
    }
    stage('Test') {
        sh 'make check'
    }
    stage('Deploy') {
        sh 'make publish'
    }
}
```

### Full Example

```groovy
node('docker') {
    def notifySlack(String status) {
        def color = status == 'SUCCESS' ? 'good' : 'danger'
        slackSend(
            color: color,
            message: "${status}: Job ${env.JOB_NAME} [${env.BUILD_NUMBER}]"
        )
    }

    try {
        stage('Checkout') {
            checkout scm
        }

        stage('Build') {
            sh './gradlew clean build'
        }

        stage('Integration Tests') {
            timeout(time: 10, unit: 'MINUTES') {
                sh './run-integration-tests.sh'
            }
        }

        // Dynamic stage generation - NOT possible in Declarative
        def environments = ['dev', 'staging', 'production']
        for (env in environments) {
            stage("Deploy to ${env}") {
                if (env == 'production') {
                    input message: "Deploy to production?", ok: "Deploy"
                }
                sh "./deploy.sh ${env}"
            }
        }

    } catch (Exception e) {
        currentBuild.result = 'FAILURE'
        echo "Failed: ${e.getMessage()}"
        notifySlack('FAILURE')
        throw e
    } finally {
        notifySlack(currentBuild.result ?: 'SUCCESS')
        cleanWs()
    }
}
```

### What Makes It Special

- **Dynamic stage generation** — loop over a list and create stages at runtime
- **Full Groovy** — closures, functions, complex data structures, any Groovy API
- **`node('label')`** — allocate agents per-stage for cross-platform builds
- **Manual error handling** — `try/catch/finally` gives precise control but is easy to get wrong
- **No pre-run validation** — structural errors only surface at runtime

---

## Side-by-Side Comparison

| Feature | Declarative | Scripted |
|---|---|---|
| **Syntax** | Opinionated DSL (`pipeline {}`) | Free-form Groovy (`node {}`) |
| **Learning curve** | Gentle — fixed set of directives | Steeper — requires Groovy knowledge |
| **Readability** | High — same structure in every file | Depends on author's discipline |
| **Validation** | Linter catches errors before build | Only Groovy compile errors at build start |
| **Error handling** | `post` blocks (declarative, can't be skipped) | `try/catch/finally` (manual, easy to get wrong) |
| **Conditional stages** | `when` directive (stage shows as "skipped") | `if/else` (stage disappears entirely) |
| **Dynamic stages** | ❌ Not natively possible | ✅ Full Groovy loops |
| **SCM checkout** | Automatic | Must write `checkout scm` explicitly |
| **Restart from stage** | ✅ Supported | ❌ Not supported |
| **Blue Ocean UI** | Full support | Partial |
| **IDE auto-complete** | ✅ | Limited |

---

## When to Use Which

| Need | Use |
|---|---|
| Standard CI/CD pipeline (build → test → deploy) | **Declarative** |
| Team onboarding / readability matters | **Declarative** |
| Need syntax validation before running | **Declarative** |
| Conditional stages with visible "skipped" state | **Declarative** (`when`) |
| Dynamic stage names from a runtime list | **Scripted** |
| Complex Groovy logic (loops, data structures) | **Scripted** or `script {}` in Declarative |
| Legacy pipeline migration | Keep **Scripted** until refactored |

---

## Recommendation

Start with **Declarative**. When you hit a wall, use a `script {}` block inside a stage to inject Groovy logic — this gives full Groovy power while keeping the outer pipeline structured and validated. Only go fully Scripted when you genuinely need **dynamic stage generation from a runtime list**, which is the one thing `script {}` cannot do.
```

```markdown
# 25 Declarative Pipeline Examples for Beginners

> Work through these top to bottom. Each one builds on the previous. Copy each into a Jenkinsfile and run it.

---

## 1. The Absolute Minimum

```groovy
pipeline {
    agent any
    stages {
        stage('Hello') {
            steps {
                echo 'Hello, Jenkins!'
            }
        }
    }
}
```

**What you learn:** The required skeleton — `pipeline`, `agent`, `stages`, `stage`, `steps`.

---

## 2. Running a Shell Command

```groovy
pipeline {
    agent any
    stages {
        stage('Run Script') {
            steps {
                sh 'echo "Running on $(uname -a)"'
            }
        }
    }
}
```

**What you learn:** `sh` for Linux/macOS, `bat` for Windows.

---

## 3. Multiple Stages

```groovy
pipeline {
    agent any
    stages {
        stage('Build') {
            steps {
                echo 'Building...'
                sh 'make'
            }
        }
        stage('Test') {
            steps {
                echo 'Testing...'
                sh 'make test'
            }
        }
        stage('Package') {
            steps {
                echo 'Packaging...'
                sh 'make package'
            }
        }
    }
}
```

**What you learn:** Stages run sequentially by default.

---

## 4. Environment Variables

```groovy
pipeline {
    agent any
    environment {
        APP_NAME = 'my-app'
        VERSION  = '1.0.0'
    }
    stages {
        stage('Info') {
            steps {
                echo "Building ${APP_NAME} version ${VERSION}"
            }
        }
    }
}
```

**What you learn:** `environment` block, variable interpolation with `${}`.

---

## 5. Using Jenkins Built-in Variables

```groovy
pipeline {
    agent any
    stages {
        stage('Build Info') {
            steps {
                echo "Job: ${env.JOB_NAME}"
                echo "Build #${env.BUILD_NUMBER}"
                echo "Branch: ${env.BRANCH_NAME}"
                echo "Built by: ${env.BUILD_USER}"
            }
        }
    }
}
```

**What you learn:** `env.*` gives access to all Jenkins environment variables.

---

## 6. The `post` Block

```groovy
pipeline {
    agent any
    stages {
        stage('Build') {
            steps {
                echo 'Building'
            }
        }
    }
    post {
        success { echo '✅ Build succeeded' }
        failure { echo '❌ Build failed' }
        always  { echo '🔚 Build finished' }
    }
}
```

**What you learn:** `post` runs after the pipeline. `success`, `failure`, `always` are the most common conditions.

---

## 7. `post` at Stage Level

```groovy
pipeline {
    agent any
    stages {
        stage('Build') {
            steps {
                echo 'Building'
            }
        }
        stage('Test') {
            steps {
                echo 'Testing'
            }
            post {
                success { echo 'Tests passed!' }
                failure { echo 'Tests failed!' }
            }
        }
    }
}
```

**What you learn:** `post` can also go inside a stage for stage-level notifications.

---

## 8. `options` — Timeout

```groovy
pipeline {
    agent any
    options {
        timeout(time: 10, unit: 'MINUTES')
    }
    stages {
        stage('Long Task') {
            steps {
                sh 'sleep 600'   // This will be killed after 10 min
            }
        }
    }
}
```

**What you learn:** `options` at pipeline level. `timeout` prevents infinite builds.

---

## 9. `options` — Retry

```groovy
pipeline {
    agent any
    options {
        retry(2)   // Retry the entire pipeline up to 2 times on failure
    }
    stages {
        stage('Flaky Step') {
            steps {
                echo 'This might fail'
                sh 'exit 1'   // Uncomment to test retry
            }
        }
    }
}
```

**What you learn:** `retry` re-runs the entire pipeline on failure.

---

## 10. `options` — Timestamps

```groovy
pipeline {
    agent any
    options {
        timestamps()
    }
    stages {
        stage('Timed') {
            steps {
                echo 'First line'
                sleep 2
                echo 'Second line (2 seconds later)'
            }
        }
    }
}
```

**What you learn:** `timestamps()` adds a timestamp to every console log line.

---

## 11. `when` — Conditional Stage

```groovy
pipeline {
    agent any
    stages {
        stage('Build') {
            steps {
                echo 'Building'
            }
        }
        stage('Deploy to Prod') {
            when {
                branch 'main'
            }
            steps {
                echo 'Deploying to production'
            }
        }
    }
}
```

**What you learn:** `when { branch 'main' }` — stage only runs on the main branch. Skipped stages show as "skipped" in the UI.

---

## 12. `when` — Using `expression`

```groovy
pipeline {
    agent any
    environment {
        DEPLOY = 'false'
    }
    stages {
        stage('Build') {
            steps {
                echo 'Building'
            }
        }
        stage('Deploy') {
            when {
                expression { env.DEPLOY == 'true' }
            }
            steps {
                echo 'Deploying because DEPLOY is true'
            }
        }
    }
}
```

**What you learn:** `expression` for custom conditions using Groovy boolean logic.

---

## 13. `when` — Using `environment`

```groovy
pipeline {
    agent any
    stages {
        stage('Build') {
            steps {
                echo 'Building'
            }
        }
        stage('Nightly Test') {
            when {
                environment name: 'BUILD_CAUSE', value: 'SCHEDULED'
            }
            steps {
                echo 'Running nightly tests'
            }
        }
    }
}
```

**What you learn:** `environment` condition — matches when an env var equals a specific value.

---

## 14. Parallel Stages

```groovy
pipeline {
    agent any
    stages {
        stage('Build') {
            steps {
                echo 'Building'
            }
        }
        stage('Tests') {
            parallel {
                stage('Unit Tests') {
                    steps {
                        echo 'Running unit tests'
                        sleep 5
                    }
                }
                stage('Integration Tests') {
                    steps {
                        echo 'Running integration tests'
                        sleep 5
                    }
                }
                stage('Lint') {
                    steps {
                        echo 'Running linter'
                        sleep 3
                    }
                }
            }
        }
    }
}
```

**What you learn:** `parallel` runs child stages simultaneously. All must succeed for the parent to pass.

---

## 15. `input` — Manual Approval

```groovy
pipeline {
    agent any
    stages {
        stage('Build') {
            steps {
                echo 'Build complete'
            }
        }
        stage('Deploy') {
            steps {
                input message: 'Deploy to staging?', ok: 'Yes, deploy'
                echo 'Deploying to staging...'
            }
        }
    }
}
```

**What you learn:** `input` pauses the pipeline and waits for a human to click a button in the Jenkins UI.

---

## 16. `parameters` — User Input

```groovy
pipeline {
    agent any
    parameters {
        string(name: 'DEPLOY_ENV', defaultValue: 'staging', description: 'Target environment')
        choice(name: 'BUILD_TYPE', choices: ['release', 'debug'], description: 'Build type')
        booleanParam(name: 'SKIP_TESTS', defaultValue: false, description: 'Skip tests?')
    }
    stages {
        stage('Build') {
            steps {
                echo "Building ${params.BUILD_TYPE} for ${params.DEPLOY_ENV}"
            }
        }
        stage('Test') {
            when {
                expression { !params.SKIP_TESTS }
            }
            steps {
                echo 'Running tests'
            }
        }
    }
}
```

**What you learn:** `parameters` lets users fill in values before triggering the build. Access via `params.*`.

---

## 17. `tools` — Auto-Install JDK

```groovy
pipeline {
    agent {
        docker {
            image 'maven:3.9-eclipse-temurin-17'
        }
    }
    stages {
        stage('Build') {
            steps {
                sh 'mvn -version'
                sh 'mvn clean package -q'
            }
        }
    }
}
```

**What you learn:** `agent { docker { image '...' } }` runs the pipeline inside a Docker container.

---

## 18. `agent` with Labels

```groovy
pipeline {
    agent {
        label 'linux && docker'
    }
    stages {
        stage('Build') {
            steps {
                sh 'echo "Running on a node labeled linux with docker"'
            }
        }
    }
}
```

**What you learn:** `label` routes the build to specific agents. Use `&&` for AND, `||` for OR.

---

## 19. `agent none` — No Single Agent

```groovy
pipeline {
    agent none
    stages {
        stage('Build on Linux') {
            agent { label 'linux' }
            steps {
                sh 'echo "Building on Linux"'
            }
        }
        stage('Test on macOS') {
            agent { label 'macos' }
            steps {
                sh 'echo "Testing on macOS"'
            }
        }
    }
}
```

**What you learn:** `agent none` at pipeline level means each stage must declare its own agent. Useful for cross-platform builds.

---

## 20. `triggers` — Cron Schedule

```groovy
pipeline {
    agent any
    triggers {
        cron('H 2 * * *')   // Runs at a random minute past 2 AM every day
    }
    stages {
        stage('Nightly Build') {
            steps {
                echo "Running nightly build at ${new Date()}"
            }
        }
    }
}
```

**What you learn:** `triggers { cron(...) }` schedules the pipeline. `H` = random hash minute to avoid thundering herd.

---

## 21. `triggers` — SCM Polling

```groovy
pipeline {
    agent any
    triggers {
        pollSCM('H/5 * * * *')   // Check for new commits every 5 minutes
    }
    stages {
        stage('Build') {
            steps {
                echo "Building ${env.GIT_COMMIT}"
            }
        }
    }
}
```

**What you learn:** `pollSCM` checks the repository for changes and triggers a build only when new commits are found.

---

## 22. `script` Block — Groovy Escape Hatch

```groovy
pipeline {
    agent any
    stages {
        stage('Dynamic') {
            steps {
                script {
                    def day = new Date().dayOfWeek
                    if (day == 'Monday') {
                        echo "It's Monday! Running full test suite"
                    } else {
                        echo "Not Monday, running quick tests only"
                    }
                }
            }
        }
    }
}
```

**What you learn:** `script {}` lets you write full Groovy inside a declarative pipeline. Use it sparingly.

---

## 23. `stash` and `unstash` — Share Artifacts Between Stages

```groovy
pipeline {
    agent any
    stages {
        stage('Build') {
            steps {
                sh 'echo "binary data" > build-output.bin'
                stash name: 'artifacts', includes: 'build-output.bin'
            }
        }
        stage('Deploy') {
            steps {
                unstash 'artifacts'
                sh 'ls -la build-output.bin'
            }
        }
    }
}
```

**What you learn:** `stash` saves files; `unstash` restores them. Useful when stages run on different agents.

---

## 24. `archiveArtifacts` and `cleanWs`

```groovy
pipeline {
    agent any
    options {
        timestamps()
    }
    stages {
        stage('Build') {
            steps {
                sh 'mkdir -p dist && echo "app-v1.0" > dist/app.tar.gz'
                archiveArtifacts 'dist/*'
            }
        }
    }
    post {
        always {
            cleanWs()   // Delete workspace after build
        }
    }
}
```

**What you learn:** `archiveArtifacts` saves files as build artifacts (downloadable from Jenkins UI). `cleanWs()` cleans the workspace.

---

## 25. Complete Real-World Pipeline

```groovy
pipeline {
    agent {
        docker {
            image 'maven:3.9-eclipse-temurin-17'
        }
    }

    options {
        timestamps()
        timeout(time: 30, unit: 'MINUTES')
        disableConcurrentBuilds()
    }

    parameters {
        choice(name: 'ENV', choices: ['staging', 'production'], description: 'Deploy target')
        booleanParam(name: 'SKIP_TESTS', defaultValue: false, description: 'Skip tests')
    }

    environment {
        APP_NAME = 'my-service'
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Build') {
            steps {
                sh 'mvn clean package -DskipTests -q'
            }
        }

        stage('Test') {
            when {
                expression { !params.SKIP_TESTS }
            }
            parallel {
                stage('Unit Tests') {
                    steps {
                        sh 'mvn test -q'
                    }
                }
                stage('Static Analysis') {
                    steps {
                        sh 'mvn checkstyle:check -q'
                    }
                }
            }
            post {
                always { junit '**/target/surefire-reports/*.xml' }
            }
        }

        stage('Deploy') {
            when {
                branch 'main'
            }
            steps {
                if (params.ENV == 'production') {
                    input message: "Deploy to PRODUCTION?", ok: 'Deploy'
                }
                sh "./deploy.sh ${params.ENV}"
            }
        }
    }

    post {
        success {
            echo "✅ ${APP_NAME} deployed to ${params.ENV}"
        }
        failure {
            echo "❌ ${APP_NAME} build failed"
        }
        always {
            cleanWs()
        }
    }
}
```

**What you learn:** Everything combined — Docker agent, options, parameters, parallel tests, conditional deploy, `input` for production, `post` with all conditions.

---

## Quick Reference Cheat Sheet

```
pipeline {
    agent any / { docker {...} } / { label '...' } / none
    options { timeout(), retry(), timestamps(), disableConcurrentBuilds() }
    parameters { string(), choice(), booleanParam(), text() }
    environment { KEY = 'value' }
    triggers { cron(), pollSCM() }
    stages {
        stage('Name') {
            when { branch / expression / environment }
            agent { ... }          // per-stage override
            parallel { stage() {} stage() {} }
            steps { sh / echo / script / input / ... }
            post { success / failure / always }
        }
    }
    post { success / failure / always / unstable / aborted }
}
```
```

