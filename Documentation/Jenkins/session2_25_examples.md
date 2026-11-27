# **25 Hands-on Jenkins + GitHub Integration Examples**

**GitHub filename:** `03A-25-jenkins-github-integration-examples.md`

**Training platform:** Prepare.sh Jenkins Playground\
**Level:** Beginner to Advanced\
**Duration:** 3–4 Hours\
**Prerequisite:** Session 3 – Jenkins and GitHub Integration.

## **Learning objectives**

After completing these 25 practical exercises, students should be able to:

1. Connect Jenkins to GitHub.
2. Clone public GitHub repositories.
3. Retrieve source code using Jenkins Pipeline.
4. Work with Git branches.
5. Understand Jenkins workspace.
6. Execute scripts downloaded from GitHub.
7. Handle private repository authentication.
8. Understand Jenkins credentials.
9. Configure Pipeline from SCM.
10. Understand GitHub webhooks and Poll SCM.
11. Troubleshoot real-world GitHub integration failures.

## **Before starting**

Create a public GitHub repository named:

```
jenkins-github-practical
```

Create the following files:

`app.txt`

```
Application=BankingApp
Version=1.0
Environment=Development
Developer=Student
```

`build.sh`

```
#!/bin/bash

echo "Starting Application Build"
echo "Application: BankingApp"
echo "Version: 1.0"
echo "Build Successful"
```

`README.md`

```
# Jenkins GitHub Practical

This repository is created for Jenkins training.

Purpose:
- GitHub checkout
- Jenkins pipeline
- Application build
- CI/CD automation
```

Replace `YOUR-USERNAME` in all examples with your GitHub username.

# **Level 1 – GitHub Repository and Basic Checkout (Examples 1–5)**

## **Example 1: Clone a Public GitHub Repository**

**Objective:** Retrieve source code from GitHub.

```
pipeline {
    agent any

    stages {
        stage('GitHub Checkout') {
            steps {
                git url: 'https://github.com/YOUR-USERNAME/jenkins-github-practical.git',
                    branch: 'main'
            }
        }
    }
}
```

Expected result:

```
Started by user
Checking out source code
Finished: SUCCESS
```

**Student tasks:**

- Execute the pipeline.
- Check Console Output.
- Identify the Git commit being checked out.
- Verify whether Jenkins downloaded the repository.

## **Example 2: Display All Downloaded Files**

**Objective:** Understand Jenkins workspace.

```
pipeline {
    agent any

    stages {
        stage('Checkout') {
            steps {
                git url: 'https://github.com/YOUR-USERNAME/jenkins-github-practical.git',
                    branch: 'main'
            }
        }

        stage('List Files') {
            steps {
                sh '''
                    echo "Current Workspace"
                    pwd

                    echo "Repository Files"
                    ls -la

                    echo "File Structure"
                    find . -maxdepth 2 -type f
                '''
            }
        }
    }
}
```

**Student tasks:**

1. Identify the workspace location.
2. Find `app.txt`.
3. Find `build.sh`.
4. Explain how Jenkins uses the workspace.

## **Example 3: Read Files Downloaded from GitHub**

**Objective:** Access repository files inside Jenkins.

```
pipeline {
    agent any

    stages {
        stage('Checkout') {
            steps {
                git url: 'https://github.com/YOUR-USERNAME/jenkins-github-practical.git',
                    branch: 'main'
            }
        }

        stage('Read Application Details') {
            steps {
                sh '''
                    echo "Application Information"
                    cat app.txt

                    echo "README Information"
                    cat README.md
                '''
            }
        }
    }
}
```

**Student tasks:**

- Add a new line to `app.txt`.
- Commit it to GitHub.
- Run the Jenkins pipeline again.
- Verify that Jenkins retrieves the updated content.

## **Example 4: Execute a Shell Script Downloaded from GitHub**

**Objective:** Execute application build scripts through Jenkins.

```
pipeline {
    agent any

    stages {
        stage('Checkout') {
            steps {
                git url: 'https://github.com/YOUR-USERNAME/jenkins-github-practical.git',
                    branch: 'main'
            }
        }

        stage('Execute Build Script') {
            steps {
                sh 'bash build.sh'
            }
        }
    }
}
```

Expected output:

```
Starting Application Build
Application: BankingApp
Version: 1.0
Build Successful
```

**Student task:** Modify `build.sh` in GitHub to print five additional application details and execute it again.

## **Example 5: Display Git Commit Information**

**Objective:** Identify which version of source code Jenkins downloaded.

```
pipeline {
    agent any

    stages {
        stage('Checkout') {
            steps {
                git url: 'https://github.com/YOUR-USERNAME/jenkins-github-practical.git',
                    branch: 'main'
            }
        }

        stage('Git Information') {
            steps {
                sh '''
                    echo "Latest Commit"
                    git log -1

                    echo "Commit ID"
                    git rev-parse HEAD

                    echo "Current Branch"
                    git branch --show-current

                    echo "Repository Status"
                    git status
                '''
            }
        }
    }
}
```

**Student task:** Record the commit ID. Make a new GitHub commit and compare the commit IDs after running the pipeline again.

# **Level 2 – Git Branch Management (Examples 6–10)**

## **Example 6: Checkout a Development Branch**

**Objective:** Retrieve code from a specific branch.

First create a branch called `development` in GitHub.

```
pipeline {
    agent any

    stages {
        stage('Checkout Development') {
            steps {
                git url: 'https://github.com/YOUR-USERNAME/jenkins-github-practical.git',
                    branch: 'development'
            }
        }

        stage('Verify Branch') {
            steps {
                sh '''
                    git branch --show-current
                    ls -la
                '''
            }
        }
    }
}
```

**Student task:** Add a file named `development.txt` to the development branch and verify that Jenkins downloads it.

## **Example 7: Checkout a Feature Branch**

**Objective:** Understand feature branch builds.

Create a branch named:

```
feature-login
```

Jenkinsfile:

```
pipeline {
    agent any

    stages {
        stage('Checkout Feature Branch') {
            steps {
                git url: 'https://github.com/YOUR-USERNAME/jenkins-github-practical.git',
                    branch: 'feature-login'
            }
        }

        stage('Feature Validation') {
            steps {
                sh '''
                    echo "Validating Login Feature"
                    ls -la
                '''
            }
        }
    }
}
```

**Student task:** Add `login.txt` to the feature branch and verify its presence in Jenkins.

## **Example 8: Build Different Branches Using Parameters**

**Objective:** Use Jenkins parameters to select a Git branch.

```
pipeline {
    agent any

    parameters {
        choice(
            name: 'BRANCH_NAME',
            choices: ['main', 'development', 'feature-login'],
            description: 'Select GitHub branch'
        )
    }

    stages {
        stage('Checkout') {
            steps {
                git url: 'https://github.com/YOUR-USERNAME/jenkins-github-practical.git',
                    branch: params.BRANCH_NAME
            }
        }

        stage('Branch Information') {
            steps {
                sh 'git branch --show-current'
                sh 'git log -1 --oneline'
            }
        }
    }
}
```

**Student task:** Execute the same job three times using three different branches.

## **Example 9: Compare Two Branches**

**Objective:** Understand differences between development and main branches.

```
pipeline {
    agent any

    stages {
        stage('Checkout Main') {
            steps {
                git url: 'https://github.com/YOUR-USERNAME/jenkins-github-practical.git',
                    branch: 'main'
            }
        }

        stage('Compare Branches') {
            steps {
                sh '''
                    git fetch origin development

                    echo "Comparing Main and Development"

                    git diff --stat origin/main origin/development
                '''
            }
        }
    }
}
```

**Student task:** Change a file in development and compare the branches again.

Note: This example assumes the `development` branch exists and the checkout includes the relevant Git history.

## **Example 10: Checkout a Specific Git Commit**

**Objective:** Retrieve a particular version of an application.

```
pipeline {
    agent any

    stages {
        stage('Checkout Repository') {
            steps {
                git url: 'https://github.com/YOUR-USERNAME/jenkins-github-practical.git',
                    branch: 'main'
            }
        }

        stage('Display Commit History') {
            steps {
                sh 'git log --oneline -5'
            }
        }
    }
}
```

**Student task:**

1. Identify a commit ID from the output.
2. Modify the pipeline to check out that commit using `checkout` and `scmGit` with the appropriate Git plugin configuration.
3. Verify the checked-out commit using `git rev-parse HEAD`.

# **Level 3 – Jenkins Workspace and Repository Operations (Examples 11–15)**

## **Example 11: Clean Workspace Before Checkout**

**Objective:** Understand workspace cleanup.

```
pipeline {
    agent any

    stages {
        stage('Clean Workspace') {
            steps {
                deleteDir()
                echo 'Workspace Cleaned'
            }
        }

        stage('Checkout') {
            steps {
                git url: 'https://github.com/YOUR-USERNAME/jenkins-github-practical.git',
                    branch: 'main'
            }
        }

        stage('Verify') {
            steps {
                sh 'ls -la'
            }
        }
    }
}
```

**Student task:** Create an additional file in the workspace during one build. Execute the pipeline again and observe what happens.

## **Example 12: Download Repository and Create a Backup**

**Objective:** Understand file management inside the workspace.

```
pipeline {
    agent any

    stages {
        stage('Checkout') {
            steps {
                git url: 'https://github.com/YOUR-USERNAME/jenkins-github-practical.git',
                    branch: 'main'
            }
        }

        stage('Backup Files') {
            steps {
                sh '''
                    mkdir -p backup

                    cp app.txt backup/

                    cp README.md backup/

                    echo "Backup Files"
                    ls -l backup
                '''
            }
        }
    }
}
```

**Student task:** Add `build.sh` to the backup directory.

## **Example 13: Validate Required Files**

**Objective:** Prevent builds when mandatory files are missing.

```
pipeline {
    agent any

    stages {
        stage('Checkout') {
            steps {
                git url: 'https://github.com/YOUR-USERNAME/jenkins-github-practical.git',
                    branch: 'main'
            }
        }

        stage('File Validation') {
            steps {
                sh '''
                    test -f app.txt
                    test -f build.sh
                    test -f README.md

                    echo "All Required Files Found"
                '''
            }
        }
    }
}
```

**Student task:** Rename `app.txt` in GitHub and observe how the Jenkins build behaves.

## **Example 14: Generate a Build Report**

**Objective:** Create a report containing GitHub repository information.

```
pipeline {
    agent any

    stages {
        stage('Checkout') {
            steps {
                git url: 'https://github.com/YOUR-USERNAME/jenkins-github-practical.git',
                    branch: 'main'
            }
        }

        stage('Generate Report') {
            steps {
                sh '''
                    mkdir -p reports

                    echo "Jenkins Build Report" > reports/build-report.txt

                    echo "Date: $(date)" >> reports/build-report.txt

                    echo "Commit: $(git rev-parse HEAD)" >> reports/build-report.txt

                    echo "Branch: $(git branch --show-current)" >> reports/build-report.txt

                    cat reports/build-report.txt
                '''

                archiveArtifacts artifacts: 'reports/*.txt'
            }
        }
    }
}
```

**Student task:** Add application name and build version to the report.

## **Example 15: Execute a Complete GitHub Build Pipeline**

**Objective:** Combine checkout, validation, build and testing.

```
pipeline {
    agent any

    stages {
        stage('Checkout') {
            steps {
                git url: 'https://github.com/YOUR-USERNAME/jenkins-github-practical.git',
                    branch: 'main'
            }
        }

        stage('Validate') {
            steps {
                sh 'test -f app.txt'
                sh 'test -f build.sh'
            }
        }

        stage('Build') {
            steps {
                sh 'bash build.sh'
            }
        }

        stage('Testing') {
            steps {
                sh '''
                    grep -q "BankingApp" app.txt

                    echo "Application Validation Successful"
                '''
            }
        }

        stage('Package') {
            steps {
                sh '''
                    mkdir -p package

                    cp app.txt package/
                    cp build.sh package/
                '''
            }
        }

        stage('Archive') {
            steps {
                archiveArtifacts artifacts: 'package/*'
            }
        }
    }
}
```

**Student task:** Add a Security Validation stage before Package.

# **Level 4 – Private Repository and Credentials (Examples 16–20)**

These examples require a private GitHub repository and Jenkins Credentials support.

## **Example 16: Checkout a Private GitHub Repository**

**Objective:** Understand authentication.

First:

1. Create a private GitHub repository.
2. Create a GitHub fine-grained Personal Access Token.
3. Give it access to the selected repository with Contents: Read-only permission.
4. Configure Jenkins Credentials.

Credential ID:

```
github-training-credentials
```

Jenkinsfile:

```
pipeline {
    agent any

    stages {
        stage('Private Repository Checkout') {
            steps {
                git branch: 'main',
                    credentialsId: 'github-training-credentials',
                    url: 'https://github.com/YOUR-USERNAME/PRIVATE-REPOSITORY.git'
            }
        }

        stage('Verify Files') {
            steps {
                sh 'ls -la'
            }
        }
    }
}
```

**Student task:** Explain why public repositories can generally be cloned without credentials but private repositories require authorization.

## **Example 17: Use Jenkins Credentials in a Git Checkout**

**Objective:** Understand credential references.

```
pipeline {
    agent any

    stages {
        stage('Checkout') {
            steps {
                script {
                    echo 'Using Jenkins-managed GitHub credentials'
                }

                git(
                    url: 'https://github.com/YOUR-USERNAME/PRIVATE-REPOSITORY.git',
                    branch: 'main',
                    credentialsId: 'github-training-credentials'
                )
            }
        }

        stage('Build') {
            steps {
                echo 'Private Repository Build Started'
            }
        }
    }
}
```

**Student task:**

1. Change the credential ID to an incorrect value.
2. Run the pipeline.
3. Observe the authentication failure.
4. Restore the correct credential ID.

Never display or print the actual token.

## **Example 18: Use a GitHub Token with&#x20;**`withCredentials`

**Objective:** Understand secure credential binding.

Configure a Jenkins Secret Text credential with ID:

```
github-token
```

Example:

```
pipeline {
    agent any

    stages {
        stage('Credential Validation') {
            steps {
                withCredentials([
                    string(
                        credentialsId: 'github-token',
                        variable: 'GITHUB_TOKEN'
                    )
                ]) {
                    sh '''
                        if [ -n "$GITHUB_TOKEN" ]; then
                            echo "GitHub token is configured"
                        else
                            echo "GitHub token is missing"
                            exit 1
                        fi
                    '''
                }
            }
        }
    }
}
```

**Student task:**

- Configure the secret.
- Execute the pipeline.
- Verify that the pipeline validates the credential without printing its value.

## **Example 19: Use Different Credentials for Different Repositories**

**Objective:** Understand how enterprise Jenkins environments manage multiple GitHub repositories.

Configure two Jenkins credential IDs:

```
github-app-credentials
github-infra-credentials
```

Jenkinsfile:

```
pipeline {
    agent any

    stages {
        stage('Checkout Application') {
            steps {
                dir('application') {
                    git(
                        url: 'https://github.com/YOUR-USERNAME/PRIVATE-APP.git',
                        branch: 'main',
                        credentialsId: 'github-app-credentials'
                    )
                }
            }
        }

        stage('Checkout Infrastructure') {
            steps {
                dir('infrastructure') {
                    git(
                        url: 'https://github.com/YOUR-USERNAME/PRIVATE-INFRA.git',
                        branch: 'main',
                        credentialsId: 'github-infra-credentials'
                    )
                }
            }
        }

        stage('List Repository Files') {
            steps {
                sh 'find . -maxdepth 3 -type f'
            }
        }
    }
}
```

**Student task:** Create two repositories and retrieve both into separate workspace directories.

## **Example 20: Secure Private Repository Build**

**Objective:** Combine private repository checkout, build and artifact archiving.

```
pipeline {
    agent any

    environment {
        APP_NAME = 'BankingApplication'
    }

    stages {
        stage('Checkout') {
            steps {
                git(
                    url: 'https://github.com/YOUR-USERNAME/PRIVATE-REPOSITORY.git',
                    branch: 'main',
                    credentialsId: 'github-training-credentials'
                )
            }
        }

        stage('Build') {
            steps {
                sh 'bash build.sh'
            }
        }

        stage('Generate Report') {
            steps {
                sh '''
                    mkdir -p reports

                    echo "Application: ${APP_NAME}" > reports/build.txt
                    echo "Build: Successful" >> reports/build.txt

                    cat reports/build.txt
                '''

                archiveArtifacts artifacts: 'reports/*'
            }
        }
    }
}
```

**Student task:** Add application version, Git commit ID and current date to the build report.

# **Level 5 – Advanced GitHub Integration and Automation (Examples 21–25)**

## **Example 21: Store Jenkinsfile Inside GitHub**

**Objective:** Understand Pipeline from SCM.

Create a file called `Jenkinsfile` inside your GitHub repository.

Use this content:

```
pipeline {
    agent any

    stages {
        stage('Checkout') {
            steps {
                echo 'Jenkinsfile Retrieved from GitHub'
            }
        }

        stage('Build') {
            steps {
                echo 'Application Build Started'
            }
        }

        stage('Testing') {
            steps {
                echo 'Application Testing Completed'
            }
        }
    }
}
```

### **Jenkins configuration**

1. Create a new Pipeline job.
2. Select Pipeline script from SCM.
3. Select Git.
4. Enter the GitHub repository URL.
5. Select branch `main`.
6. Set Script Path to `Jenkinsfile`.
7. Save and execute.

**Student task:** Modify the Jenkinsfile directly in GitHub, commit the change and execute Jenkins again.

## **Example 22: Configure Poll SCM**

**Objective:** Understand scheduled repository change detection.

```
pipeline {
    agent any

    triggers {
        pollSCM('H/5 * * * *')
    }

    stages {
        stage('Checkout') {
            steps {
                git(
                    url: 'https://github.com/YOUR-USERNAME/jenkins-github-practical.git',
                    branch: 'main'
                )
            }
        }

        stage('Build') {
            steps {
                echo 'Building Latest Application Version'
            }
        }
    }
}
```

**Student task:**

1. Configure Poll SCM.
2. Change `app.txt` in GitHub.
3. Commit the change.
4. Observe Jenkins build history.
5. Explain how polling detects repository changes.

Note: Polling is not guaranteed to trigger a build merely because a `git` checkout step exists. Jenkins needs an appropriate SCM polling configuration and a compatible job/plugin setup. The actual polling behavior should be verified in your environment.

## **Example 23: Configure GitHub Webhook Trigger**

**Objective:** Understand event-based build triggering.

Jenkinsfile:

```
pipeline {
    agent any

    triggers {
        githubPush()
    }

    stages {
        stage('Checkout') {
            steps {
                git(
                    url: 'https://github.com/YOUR-USERNAME/jenkins-github-practical.git',
                    branch: 'main'
                )
            }
        }

        stage('Build') {
            steps {
                echo 'GitHub Push Detected'
                echo 'Starting Application Build'
            }
        }
    }
}
```

### **GitHub webhook configuration**

Configure the webhook in:

GitHub Repository → Settings → Webhooks → Add webhook.

Use the publicly reachable Jenkins URL:

```
https://YOUR-JENKINS-URL/github-webhook/
```

Select:

```
Content type: application/json
Event: Just the push event
```

**Student task:**

1. Configure the Jenkins trigger.
2. Configure the GitHub webhook.
3. Push a new commit.
4. Check webhook delivery status.
5. Verify the Jenkins build.

Note: This example requires the Jenkins GitHub plugin and a reachable Jenkins endpoint. Prepare.sh may not expose the required network endpoint.

## **Example 24: Build Different Environments Using GitHub Branches**

**Objective:** Understand branch-based CI/CD deployment.

```
pipeline {
    agent any

    parameters {
        choice(
            name: 'BRANCH',
            choices: ['main', 'development', 'feature-login'],
            description: 'Select application branch'
        )
    }

    environment {
        APP_NAME = 'BankingApplication'
    }

    stages {
        stage('Checkout') {
            steps {
                git(
                    url: 'https://github.com/YOUR-USERNAME/jenkins-github-practical.git',
                    branch: params.BRANCH
                )
            }
        }

        stage('Build') {
            steps {
                echo "Building ${APP_NAME}"
                sh 'bash build.sh'
            }
        }

        stage('Deployment Simulation') {
            steps {
                script {
                    if (params.BRANCH == 'main') {
                        echo 'Production Deployment Selected'
                    } else if (params.BRANCH == 'development') {
                        echo 'Development Deployment Selected'
                    } else {
                        echo 'Feature Branch Validation'
                    }
                }
            }
        }
    }
}
```

**Student task:**

1. Execute with `main`.
2. Execute with `development`.
3. Execute with `feature-login`.
4. Compare the deployment messages.

Important: This is a training simulation, not an actual production deployment. Production deployment must include authorization, approval and environment-specific controls.

## **Example 25: Complete Enterprise-Style GitHub CI/CD Pipeline**

Final challenge

**Scenario:**

You are a DevOps Engineer working in a banking organization.

The development team has stored its application code in GitHub.

Your responsibility is to build an automated pipeline that retrieves the application, validates the repository, builds the application, executes testing, generates a report and simulates deployment.

**Enterprise GitHub CI/CD workflow**

1. GitHub source checkout
2. Branch and commit validation
3. Repository file validation
4. Application build
5. Unit testing
6. Code quality simulation
7. Security scan simulation
8. Build report generation
9. Artifact archiving
10. Deployment simulation

### **Final Jenkinsfile**

```
pipeline {
    agent any

    environment {
        APP_NAME = 'BankingApplication'
        VERSION = '1.0'
        DEPLOY_ENV = 'Development'
    }

    options {
        timeout(time: 10, unit: 'MINUTES')
    }

    stages {

        stage('GitHub Checkout') {
            steps {
                echo 'Connecting to GitHub'

                git(
                    url: 'https://github.com/YOUR-USERNAME/jenkins-github-practical.git',
                    branch: 'main'
                )
            }
        }

        stage('Repository Validation') {
            steps {
                sh '''
                    echo "Checking Repository"

                    pwd
                    ls -la

                    test -f app.txt
                    test -f build.sh
                    test -f README.md
                '''
            }
        }

        stage('Git Information') {
            steps {
                sh '''
                    echo "Latest Commit"

                    git log -1 --oneline

                    echo "Current Branch"

                    git branch --show-current

                    echo "Commit ID"

                    git rev-parse HEAD
                '''
            }
        }

        stage('Application Build') {
            steps {
                sh 'bash build.sh'
            }
        }

        stage('Unit Testing') {
            steps {
                sh '''
                    grep -q "BankingApp" app.txt

                    echo "Application Tests Successful"
                '''
            }
        }

        stage('Code Quality Simulation') {
            steps {
                echo 'Simulating SonarQube Code Quality Scan'
            }
        }

        stage('Security Scan Simulation') {
            steps {
                echo 'Simulating Checkmarx Security Scan'
                echo 'Simulating Black Duck Dependency Scan'
            }
        }

        stage('Generate Build Report') {
            steps {
                sh '''
                    mkdir -p reports

                    echo "Application: BankingApplication" > reports/build-report.txt

                    echo "Version: 1.0" >> reports/build-report.txt

                    echo "Branch: $(git branch --show-current)" >> reports/build-report.txt

                    echo "Commit: $(git rev-parse HEAD)" >> reports/build-report.txt

                    echo "Date: $(date)" >> reports/build-report.txt

                    cat reports/build-report.txt
                '''

                archiveArtifacts artifacts: 'reports/*',
                                 fingerprint: true
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
            echo 'GitHub CI/CD Pipeline Successful'
        }

        failure {
            echo 'GitHub CI/CD Pipeline Failed'
        }

        always {
            echo 'Pipeline Execution Completed'
        }
    }
}
```

### **Final challenge questions**

1. Which GitHub branch was checked out?
2. How can you identify the latest commit?
3. Where does Jenkins store the downloaded files?
4. What happens if `build.sh` is missing?
5. What happens if the unit test fails?
6. Where are the build reports stored?
7. How can you trigger this pipeline using a GitHub webhook?
8. How would you add SonarQube integration?
9. How would you securely retrieve GitHub credentials?
10. How would you deploy this application to OpenShift?

**Important:** The SonarQube, Checkmarx and Black Duck stages are simulations. Actual scanning requires their respective integrations. The deployment stage also only prints messages.

# **6. Student Assessment**

Use these questions after completing all 25 exercises.

**Jenkins + GitHub quiz**

0/10 answered

**1. Which Git command downloads a repository?**

git push

git clone

git commit

git status



**2. Where does Jenkins store checked-out source code?**

GitHub server

Jenkins workspace

Browser cache

README file



**3. Which plugin enables Git operations in Jenkins?**

Docker plugin

Git plugin

Maven plugin

Kubernetes plugin



**4. Which credential type can store a GitHub token?**

Secret Text

Boolean

Choice

String parameter



**5. What is a Git branch?**

A server

A separate line of development

A Jenkins plugin

A password



**6. What does git rev-parse HEAD display?**

Username

Current commit ID

Password

Repository URL



**7. What does Pipeline from SCM do?**

Deletes GitHub files

Retrieves Jenkinsfile from source control

Creates a Docker image

Restarts Jenkins



**8. What does a webhook do?**

Sends event notifications

Creates Git branches

Stores passwords

Archives artifacts



**9. What does Poll SCM do?**

Periodically checks source changes

Deletes old builds

Runs Docker

Creates credentials



**10. How should a GitHub token be stored?**

Inside Jenkinsfile

In README.md

In Jenkins Credentials

In Console Output



Submit answers

# **7. GitHub Submission Structure**

Students must maintain their practical work in GitHub.

```
jenkins-github-training/
│
├── session-03/
│   ├── example-01.groovy
│   ├── example-02.groovy
│   ├── example-03.groovy
│   ├── ...
│   └── example-25.groovy
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
│   ├── branch-checkout.png
│   ├── private-repository.png
│   ├── build-report.png
│   └── final-pipeline.png
│
└── README.md
```

# **8. Trainer Evaluation**

| Practical area                    | Marks   |
| --------------------------------- | ------- |
| Basic GitHub checkout             | 10      |
| Workspace operations              | 10      |
| Branch management                 | 15      |
| Git commit understanding          | 10      |
| Repository validation             | 10      |
| Private repository authentication | 10      |
| Jenkins Credentials               | 10      |
| Pipeline from SCM                 | 10      |
| Webhook / Poll SCM                | 5       |
| Final CI/CD pipeline              | 10      |
| **Total**                         | **100** |

# **9. Completion Checklist**

**Training progress**\
**0/16**

Created GitHub training repository

Completed public repository checkout

Retrieved and read application files

Executed build.sh from Jenkins

Understood Jenkins workspace

Practised Git branches

Compared Git commits

Cleaned workspace

Generated and archived build reports

Understood private repository access

Configured Jenkins credentials

Understood Pipeline from SCM

Studied Poll SCM

Studied GitHub webhooks

Completed final enterprise-style pipeline

Uploaded Jenkinsfiles and screenshots

## **Trainer's recommendation**

Divide these exercises into three practical classes:

| Class   | Examples | Focus                                   |
| ------- | -------- | --------------------------------------- |
| Class 1 | 1–10     | GitHub checkout and branches            |
| Class 2 | 11–20    | Workspace, credentials and repositories |
| Class 3 | 21–25    | SCM, webhooks and CI/CD                 |

**Do not proceed until students can independently retrieve source code from GitHub, identify the checked-out commit, execute the application build and troubleshoot authentication or branch errors.**

The next session will build on this foundation:

**Session 4 – Jenkins Build Parameters, Environment Variables and Credentials.**
