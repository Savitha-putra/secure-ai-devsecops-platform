# **25 Hands-on Jenkins Pipeline Examples for Students**

**GitHub filename:** `02A-25-jenkins-pipeline-practical-examples.md`

**Training platform:** Prepare.sh Jenkins Playground\
**Level:** Beginner to Intermediate\
**Duration:** 2–3 Hours\
**Prerequisite:** Session 2 – Declarative Jenkins Pipeline

## **Learning objective**

Students must practise writing, executing, debugging and modifying Jenkins Declarative Pipelines.

These 25 exercises progress from basic pipeline syntax to practical DevOps automation.

**Instructions for students:**

- Open your Prepare.sh Jenkins Playground.
- Create a Pipeline job for each exercise, or reuse an existing job.
- Copy the Jenkinsfile into the Pipeline script editor.
- Click Build Now.
- Check Console Output.
- Record the result and capture screenshots.
- Modify the examples wherever an exercise asks you to do so.

# **Level 1 – Basic Jenkins Pipeline (Examples 1–5)**

## **Example 1: Print a Welcome Message**

**Objective:** Understand `pipeline`, `agent`, `stages`, `stage` and `steps`.

```
pipeline {
    agent any

    stages {
        stage('Welcome') {
            steps {
                echo 'Welcome to Jenkins Training'
                echo 'My first Jenkins Pipeline'
            }
        }
    }
}
```

Expected output:

```
Welcome to Jenkins Training
My first Jenkins Pipeline
Finished: SUCCESS
```

**Student task:** Change the welcome message to your name and execute the pipeline.

## **Example 2: Create Multiple Stages**

**Objective:** Understand how Jenkins executes multiple stages.

```
pipeline {
    agent any

    stages {
        stage('Checkout') {
            steps {
                echo 'Downloading source code'
            }
        }

        stage('Build') {
            steps {
                echo 'Building application'
            }
        }

        stage('Testing') {
            steps {
                echo 'Running application tests'
            }
        }

        stage('Deployment') {
            steps {
                echo 'Deploying application'
            }
        }
    }
}
```

Expected execution order:

```
Checkout
   |
Build
   |
Testing
   |
Deployment
```

**Student task:** Add another stage called `Security Scan`.

## **Example 3: Display Application Information**

**Objective:** Print application information.

```
pipeline {
    agent any

    stages {
        stage('Application Information') {
            steps {
                echo 'Application Name: BankingApp'
                echo 'Application Version: 2.0'
                echo 'Environment: Development'
                echo 'Team: DevOps'
            }
        }
    }
}
```

**Student task:** Change the application name, version, environment and team.

## **Example 4: Use Environment Variables**

**Objective:** Understand the `environment` block.

```
pipeline {
    agent any

    environment {
        APP_NAME = 'PaymentService'
        VERSION = '1.0'
        ENVIRONMENT = 'Development'
    }

    stages {
        stage('Application Details') {
            steps {
                echo "Application: ${APP_NAME}"
                echo "Version: ${VERSION}"
                echo "Environment: ${ENVIRONMENT}"
            }
        }

        stage('Build') {
            steps {
                echo "Building ${APP_NAME} version ${VERSION}"
            }
        }
    }
}
```

**Student task:**

1. Add `DEVELOPER = 'Student'`.
2. Print the developer name.
3. Add a new stage called `Release`.

## **Example 5: Use Built-in Jenkins Variables**

**Objective:** Understand Jenkins-provided environment variables.

```
pipeline {
    agent any

    stages {
        stage('Build Information') {
            steps {
                echo "Build Number: ${BUILD_NUMBER}"
                echo "Job Name: ${JOB_NAME}"
                echo "Build URL: ${BUILD_URL}"
                echo "Workspace: ${WORKSPACE}"
            }
        }
    }
}
```

**Production relevance:** Build numbers and job names help engineers trace application releases.

Note: `BUILD_URL` may not be populated in every playground environment.

# **Level 2 – Linux Commands Inside Jenkins (Examples 6–10)**

These examples require a compatible Linux/Unix Jenkins agent.

The `sh` step executes shell commands on that agent.

## **Example 6: Execute Basic Linux Commands**

```
pipeline {
    agent any

    stages {
        stage('Linux Commands') {
            steps {
                sh 'whoami'
                sh 'pwd'
                sh 'date'
                sh 'hostname'
                sh 'uname -a'
            }
        }
    }
}
```

Understand these commands:

| Command    | Purpose            |
| ---------- | ------------------ |
| `whoami`   | Current user       |
| `pwd`      | Current directory  |
| `date`     | System date        |
| `hostname` | Machine hostname   |
| `uname -a` | System information |

**Student task:** Add `uptime`, `id` and `df -h`.

## **Example 7: Create Directories and Files**

```
pipeline {
    agent any

    stages {
        stage('Create Directories') {
            steps {
                sh '''
                    mkdir -p devops/project
                    mkdir -p devops/logs
                    mkdir -p devops/scripts

                    ls -R devops
                '''
            }
        }

        stage('Create Files') {
            steps {
                sh '''
                    touch devops/project/app.txt
                    touch devops/logs/app.log
                    touch devops/scripts/deploy.sh

                    ls -lR devops
                '''
            }
        }
    }
}
```

**Student task:** Create another directory called `backup` and create `backup.txt` inside it.

## **Example 8: Write and Read Files**

```
pipeline {
    agent any

    stages {
        stage('Write Application Details') {
            steps {
                sh '''
                    echo "Application Started" > app.log
                    echo "Build Completed" >> app.log
                    echo "Testing Completed" >> app.log
                '''
            }
        }

        stage('Read Application Logs') {
            steps {
                sh 'cat app.log'
            }
        }
    }
}
```

Understand:

- `>` overwrites file content.
- `>>` appends content.
- `cat` displays file content.

**Student task:** Add three more log messages and execute again.

## **Example 9: Check Disk Space**

```
pipeline {
    agent any

    stages {
        stage('System Health Check') {
            steps {
                sh '''
                    echo "Checking Disk Space"
                    df -h

                    echo "Checking Memory"
                    free -h

                    echo "Checking System Uptime"
                    uptime
                '''
            }
        }
    }
}
```

**Production relevance:** DevOps engineers monitor disk and memory availability on Jenkins agents.

**Student task:** Identify the filesystem with the highest usage from the output.

## **Example 10: Execute a Shell Script**

```
pipeline {
    agent any

    stages {
        stage('Create Shell Script') {
            steps {
                sh '''
                    cat > build.sh <<'EOF'
                    #!/bin/bash

                    echo "Starting Application Build"
                    echo "Compiling Source Code"
                    echo "Build Completed Successfully"
                    EOF

                    chmod +x build.sh
                '''
            }
        }

        stage('Execute Shell Script') {
            steps {
                sh './build.sh'
            }
        }
    }
}
```

**Student task:** Modify the shell script to print:

1. Application name.
2. Build version.
3. Current date.
4. Deployment environment.

# **Level 3 – Conditions, Build Status and Failure Handling (Examples 11–15)**

## **Example 11: Intentionally Fail a Pipeline**

**Objective:** Understand pipeline failures.

```
pipeline {
    agent any

    stages {
        stage('Build') {
            steps {
                echo 'Build Started'
                echo 'Build Successful'
            }
        }

        stage('Testing') {
            steps {
                echo 'Testing Started'
                sh 'exit 1'
            }
        }

        stage('Deployment') {
            steps {
                echo 'Deployment Started'
            }
        }
    }
}
```

**Questions:**

1. Which stage failed?
2. Why was the pipeline marked failed?
3. Did deployment execute?
4. How do you identify the failure in Console Output?

## **Example 12: Handle Failure Using&#x20;**`catchError`

**Objective:** Understand how to continue a pipeline after a failed step.

```
pipeline {
    agent any

    stages {
        stage('Build') {
            steps {
                echo 'Build Successful'
            }
        }

        stage('Testing') {
            steps {
                catchError(buildResult: 'UNSTABLE', stageResult: 'FAILURE') {
                    sh 'exit 1'
                }
            }
        }

        stage('Deployment') {
            steps {
                echo 'Deployment Stage Executed'
            }
        }
    }
}
```

Understand:

- `catchError` catches an error.
- The Testing stage is marked as failed.
- The overall build result becomes unstable.
- The next stage can execute.

**Student task:** Change `buildResult` to `FAILURE` and observe the overall build result.

## **Example 13: Use&#x20;**`post`**&#x20;Conditions**

**Objective:** Execute actions after pipeline completion.

```
pipeline {
    agent any

    stages {
        stage('Build') {
            steps {
                echo 'Building Application'
            }
        }
    }

    post {
        always {
            echo 'Pipeline Execution Completed'
        }

        success {
            echo 'Pipeline Successful'
        }

        failure {
            echo 'Pipeline Failed'
        }

        unstable {
            echo 'Pipeline Unstable'
        }
    }
}
```

**Student task:**

1. Execute a successful pipeline.
2. Change the stage to `sh 'exit 1'`.
3. Execute again.
4. Compare the output of `success` and `failure`.

## **Example 14: Conditional Stage Execution**

**Objective:** Understand the `when` condition.

```
pipeline {
    agent any

    environment {
        DEPLOY_ENV = 'Development'
    }

    stages {
        stage('Build') {
            steps {
                echo 'Building Application'
            }
        }

        stage('Development Deployment') {
            when {
                environment name: 'DEPLOY_ENV', value: 'Development'
            }

            steps {
                echo 'Deploying to Development'
            }
        }

        stage('Production Deployment') {
            when {
                environment name: 'DEPLOY_ENV', value: 'Production'
            }

            steps {
                echo 'Deploying to Production'
            }
        }
    }
}
```

**Student task:** Change `DEPLOY_ENV` to `Production` and observe which stage executes.

## **Example 15: Execute Stages Based on Build Parameters**

**Objective:** Understand parameterized pipelines.

```
pipeline {
    agent any

    parameters {
        choice(
            name: 'ENVIRONMENT',
            choices: ['Development', 'Testing', 'Production'],
            description: 'Select deployment environment'
        )
    }

    stages {
        stage('Build') {
            steps {
                echo 'Building Application'
            }
        }

        stage('Deployment') {
            steps {
                echo "Selected Environment: ${params.ENVIRONMENT}"
            }
        }
    }
}
```

**Student task:**

Execute the pipeline three times, selecting a different environment each time.

Observe how the parameter changes the pipeline output.

# **Level 4 – Real-World DevOps Pipeline Examples (Examples 16–20)**

## **Example 16: Application Build Pipeline**

**Scenario:** A developer wants to automate the application build process.

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
                echo 'Checking out source code'
            }
        }

        stage('Build') {
            steps {
                echo "Building ${APP_NAME}"
                echo "Version: ${VERSION}"
            }
        }

        stage('Test') {
            steps {
                echo 'Executing Unit Tests'
            }
        }

        stage('Package') {
            steps {
                echo 'Packaging Application'
            }
        }

        stage('Release') {
            steps {
                echo 'Application Ready for Release'
            }
        }
    }
}
```

**Student task:** Add a Security Scan stage between Test and Package.

## **Example 17: Validate Application Configuration**

**Scenario:** Before deploying an application, validate that its required configuration files exist.

```
pipeline {
    agent any

    stages {
        stage('Create Configuration') {
            steps {
                sh '''
                    mkdir -p config
                    echo "APP_NAME=PaymentService" > config/app.properties
                    echo "ENV=Development" >> config/app.properties
                '''
            }
        }

        stage('Validate Configuration') {
            steps {
                sh '''
                    test -f config/app.properties
                    echo "Configuration file exists"

                    cat config/app.properties
                '''
            }
        }
    }
}
```

**Student task:** Add another configuration file called `database.properties`.

## **Example 18: Archive Build Artifacts**

**Scenario:** A build generates files that need to be retained in Jenkins.

```
pipeline {
    agent any

    stages {
        stage('Create Build Artifact') {
            steps {
                sh '''
                    mkdir -p output
                    echo "Application Build 1.0" > output/app.txt
                    echo "Build completed" > output/build-info.txt
                '''
            }
        }

        stage('Archive Artifacts') {
            steps {
                archiveArtifacts artifacts: 'output/*.txt',
                                 fingerprint: true
            }
        }
    }
}
```

Expected result:

Jenkins archives the two text files as build artifacts.

**Student task:** Create a third file and verify that it is also archived.

Note: Artifact archiving requires the Jenkins artifact archiver functionality and a compatible workspace.

## **Example 19: Run Multiple Stages in Parallel**

**Scenario:** Application unit tests and security checks can run independently.

```
pipeline {
    agent any

    stages {
        stage('Build') {
            steps {
                echo 'Application Build Completed'
            }
        }

        stage('Parallel Testing') {
            parallel {
                stage('Unit Testing') {
                    steps {
                        echo 'Executing Unit Tests'
                    }
                }

                stage('Security Testing') {
                    steps {
                        echo 'Executing Security Tests'
                    }
                }

                stage('Code Quality') {
                    steps {
                        echo 'Checking Code Quality'
                    }
                }
            }
        }

        stage('Deployment') {
            steps {
                echo 'Deployment Started'
            }
        }
    }
}
```

**Student task:** Add another parallel stage called `Dependency Scan`.

Understand: Parallel execution can reduce pipeline duration when tasks are independent and sufficient executor capacity is available.

## **Example 20: Add Build Timeout and Retry**

**Scenario:** Sometimes external services or build operations fail temporarily.

```
pipeline {
    agent any

    options {
        timeout(time: 5, unit: 'MINUTES')
    }

    stages {
        stage('Build') {
            steps {
                retry(3) {
                    echo 'Attempting Application Build'
                }
            }
        }

        stage('Testing') {
            steps {
                echo 'Testing Completed'
            }
        }
    }
}
```

Understand:

- `timeout` limits pipeline execution time.
- `retry(3)` allows the enclosed steps to be attempted up to three times if they fail.

**Student task:** Replace the `echo` inside `retry` with `sh 'exit 1'` on a Linux agent. Observe how many attempts happen.

# **Level 5 – Advanced Practice (Examples 21–25)**

## **Example 21: Use a Workspace to Organize Build Files**

**Scenario:** A Jenkins job creates and manages application files.

```
pipeline {
    agent any

    stages {
        stage('Create Workspace Files') {
            steps {
                sh '''
                    mkdir -p application
                    mkdir -p logs
                    mkdir -p reports

                    echo "Application Started" > logs/app.log
                    echo "Build Version 1.0" > reports/build.txt
                    echo "Source Code" > application/app.py
                '''
            }
        }

        stage('Display Files') {
            steps {
                sh 'find . -maxdepth 2 -type f'
            }
        }

        stage('Read Logs') {
            steps {
                sh 'cat logs/app.log'
            }
        }
    }
}
```

**Student task:** Add a directory named `backup` and copy the log file into it.

## **Example 22: Use&#x20;**`script`**&#x20;for Groovy Logic**

**Scenario:** Sometimes a pipeline requires additional logic.

```
pipeline {
    agent any

    stages {
        stage('Application Validation') {
            steps {
                script {
                    def appName = 'PaymentService'
                    def version = '2.0'

                    echo "Application: ${appName}"
                    echo "Version: ${version}"

                    if (version == '2.0') {
                        echo 'Application Version Validated'
                    } else {
                        error 'Invalid Application Version'
                    }
                }
            }
        }
    }
}
```

**Student task:**

1. Change version to `3.0`.
2. Observe the output.
3. Change the condition to validate version `3.0`.

## **Example 23: Use Credentials Safely**

**Scenario:** A deployment process requires a username and password.

This example demonstrates Jenkins Credentials usage. It requires a credential configured in Jenkins with the ID `app-login`.

```
pipeline {
    agent any

    stages {
        stage('Credential Test') {
            steps {
                withCredentials([
                    usernamePassword(
                        credentialsId: 'app-login',
                        usernameVariable: 'APP_USER',
                        passwordVariable: 'APP_PASSWORD'
                    )
                ]) {
                    sh '''
                        echo "Deployment username is configured"
                        test -n "$APP_USER"
                        test -n "$APP_PASSWORD"
                    '''
                }
            }
        }
    }
}
```

**Important:**

- Do not hardcode passwords in Jenkinsfiles.
- Do not print passwords in Console Output.
- Create credentials through Jenkins credential management.
- Jenkins masking is helpful but should not be treated as a guarantee against accidental secret exposure.

**Student task:** If your playground supports credential management, configure a test credential and execute the pipeline.

If credentials cannot be configured, document the limitation.

## **Example 24: Build, Test and Deploy with Conditions**

**Scenario:** Deploy an application only after successful testing.

```
pipeline {
    agent any

    environment {
        APP_NAME = 'BankingApp'
        DEPLOY_ENV = 'Development'
    }

    stages {
        stage('Build') {
            steps {
                echo "Building ${APP_NAME}"
            }
        }

        stage('Testing') {
            steps {
                echo 'Unit Testing Successful'
            }
        }

        stage('Security Scan') {
            steps {
                echo 'Security Scan Completed'
            }
        }

        stage('Deployment') {
            when {
                environment name: 'DEPLOY_ENV', value: 'Development'
            }

            steps {
                echo "Deploying ${APP_NAME} to ${DEPLOY_ENV}"
            }
        }
    }

    post {
        success {
            echo 'Application Pipeline Completed Successfully'
        }

        failure {
            echo 'Application Pipeline Failed'
        }

        always {
            echo 'Pipeline Execution Finished'
        }
    }
}
```

**Student task:**

1. Change the environment to Production.
2. Execute the pipeline.
3. Introduce a failure in Testing.
4. Verify whether Deployment executes.
5. Explain your observations.

## **Example 25: Complete DevSecOps Simulation Pipeline**

Final practical challenge

**Scenario:**

You are working as a DevOps Engineer in a banking organization.

The application development team wants to automate its software delivery process.

Your task is to build a Jenkins Pipeline that simulates the following workflow.

## **Banking application CI/CD**

1. **Checkout**

   Simulate downloading application source code.
2. **Build**

   Simulate compiling the application.
3. **Unit Testing**

   Simulate execution of application tests.
4. **SonarQube**

   Simulate code quality scanning.
5. **Checkmarx**

   Simulate static application security testing.
6. **Black Duck**

   Simulate open-source dependency scanning.
7. **Docker Build**

   Simulate Docker image creation.
8. **OpenShift Deployment**

   Simulate deployment to OpenShift.

### **Student implementation**

```
pipeline {
    agent any

    environment {
        APP_NAME = 'BankingApplication'
        VERSION = '1.0'
        ENVIRONMENT = 'Development'
    }

    stages {

        stage('Checkout') {
            steps {
                echo 'Checking out application source code'
            }
        }

        stage('Build') {
            steps {
                echo "Building ${APP_NAME}"
                echo "Version: ${VERSION}"
            }
        }

        stage('Unit Testing') {
            steps {
                echo 'Executing Unit Tests'
            }
        }

        stage('SonarQube Scan') {
            steps {
                echo 'Executing SonarQube Scan'
            }
        }

        stage('Checkmarx Scan') {
            steps {
                echo 'Executing Checkmarx Security Scan'
            }
        }

        stage('Black Duck Scan') {
            steps {
                echo 'Executing Black Duck Dependency Scan'
            }
        }

        stage('Docker Build') {
            steps {
                echo 'Building Docker Image'
            }
        }

        stage('OpenShift Deployment') {
            steps {
                echo "Deploying ${APP_NAME} to ${ENVIRONMENT}"
            }
        }
    }

    post {
        success {
            echo 'Banking Application Deployment Successful'
        }

        failure {
            echo 'Banking Application Pipeline Failed'
        }

        always {
            echo 'DevSecOps Pipeline Execution Completed'
        }
    }
}
```

**Important production distinction:** This is a simulation. The `echo` statements do not actually execute SonarQube, Checkmarx, Black Duck, Docker or OpenShift operations. Those require the appropriate tools, plugins, credentials, agents and configurations.

**Student task:** Add a parameter to choose Development, QA or Production deployment environments.

# **26. Student Assessment**

Use this assessment after all 25 examples.

**10-question knowledge test**

0/10 answered

**1. Which Jenkinsfile keyword defines the pipeline?**

agent

pipeline

steps

stage



**2. What does agent any mean?**

Run on all servers simultaneously

Run on any available compatible agent

Run only on master

Run inside Docker



**3. Which command appends content to a file?**

\>

cat

\>>

touch



**4. What does exit 1 indicate?**

Success

Failure

Warning only

Restart



**5. Which block executes after pipeline completion?**

environment

stages

post

agent



**6. Which Jenkins feature stores passwords securely?**

echo

Jenkins Credentials

Jenkinsfile comments

Git commit



**7. Which directive controls conditional stage execution?**

when

retry

timeout

parallel



**8. What does retry(3) do?**

Runs three stages

Retries a failed block up to three attempts

Waits three minutes

Runs three agents



**9. Which step archives build artifacts?**

archiveArtifacts

echo

sh

pwd



**10. What is a Jenkins Pipeline?**

A Linux operating system

An automated workflow for software delivery

A programming language

A Git repository



Submit assessment

# **27. GitHub Submission Requirements**

Ask students to create the following repository structure:

```
jenkins-training/
│
├── 01-basic-pipelines/
│   ├── example-01.groovy
│   ├── example-02.groovy
│   └── ...
│
├── 02-linux-commands/
│   ├── example-06.groovy
│   └── ...
│
├── 03-error-handling/
│   └── ...
│
├── 04-devops-pipelines/
│   └── ...
│
├── 05-advanced-pipelines/
│   └── ...
│
├── screenshots/
│   ├── successful-build.png
│   ├── failed-build.png
│   ├── parallel-stages.png
│   └── devsecops-pipeline.png
│
└── README.md
```

Each student must document:

1. Example number and objective.
2. Jenkinsfile used.
3. Screenshot of execution.
4. Expected output.
5. Actual output.
6. Errors encountered and how they were resolved.
7. What they learned.

# **28. Trainer Evaluation Checklist**

| Evaluation area           | Marks   |
| ------------------------- | ------- |
| Basic Pipeline syntax     | 10      |
| Linux commands            | 10      |
| Environment variables     | 10      |
| Failure troubleshooting   | 15      |
| Conditional execution     | 10      |
| Parallel execution        | 10      |
| Artifact management       | 10      |
| Credentials understanding | 10      |
| DevSecOps simulation      | 15      |
| **Total**                 | **100** |

## **Important trainer notes: Prepare.sh limitations**

Prepare.sh is a browser-based Jenkins playground. The actual capabilities depend on the environment and plugins provided.

| Exercise       | Possible requirement                                      |
| -------------- | --------------------------------------------------------- |
| Examples 1–5   | Basic Pipeline support                                    |
| Examples 6–10  | Linux-compatible agent                                    |
| Examples 11–15 | Pipeline and supporting plugins                           |
| Example 18     | Artifact archiver                                         |
| Example 19     | Parallel execution support                                |
| Example 23     | Jenkins Credentials                                       |
| Example 25     | Simulation only; real integrations require external setup |

If a feature is unavailable, explain the concept and ask students to document what is missing. Do not mark a student wrong because the playground lacks a required plugin.

## **Trainer's final instruction**

Do not rush students through all 25 examples.

Recommended teaching sequence:

- Day 1: Examples 1–10
- Day 2: Examples 11–20
- Day 3: Examples 21–25 and assessment

**Expected outcome:** Students should be able to independently write a Declarative Jenkins Pipeline, execute Linux commands, troubleshoot failures, use environment variables and understand how Jenkins fits into a DevSecOps CI/CD workflow.

After completing these exercises, students will be ready for **Session 3 – Jenkins and GitHub Integration**.
