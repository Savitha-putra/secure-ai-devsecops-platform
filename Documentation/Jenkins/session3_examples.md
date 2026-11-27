# **Session 4 – 25 Practical Jenkins Examples**

## **Build Parameters, Environment Variables and Credentials**



Hands-on Practice

25 Examples



**Platform:** Prepare.sh Jenkins Playground (`prepare.sh/jenkins`)\
**Level:** Beginner to Intermediate\
**Recommended duration:** 2–3 hours\
**Prerequisite:** Session 4 – Jenkins Parameters, Environment Variables and Credentials

### **Learning objectives**

After completing these exercises, students should be able to:

- Create and use Jenkins build parameters.
- Work with string, choice, boolean, password and text parameters.
- Understand Jenkins built-in environment variables.
- Create custom environment variables.
- Combine parameters and environment variables.
- Use Jenkins credentials securely.
- Build a parameter-driven CI/CD pipeline.

**Important playground note:** Examples 1–20 are designed primarily for Pipeline jobs and can be tested in Prepare.sh if its Jenkins version supports the required syntax. Examples 21–25 involving Jenkins credentials require a Jenkins installation with credential-management access and the relevant plugins. Prepare.sh may not expose those features.

# **Level 1 – Jenkins Build Parameters**

## **Example 1 – Simple string parameter**

**Objective:** Accept an application name from the user.

```
pipeline {
    agent any

    parameters {
        string(
            name: 'APP_NAME',
            defaultValue: 'my-application',
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

**Try this:**

1. Run the pipeline.
2. Enter `employee-management`.
3. Check Console Output.

Expected output:

```
Application Name: employee-management
```

## **Example 2 – String parameter for application version**

**Objective:** Accept an application version dynamically.

```
pipeline {
    agent any

    parameters {
        string(
            name: 'APP_VERSION',
            defaultValue: '1.0.0',
            description: 'Enter application version'
        )
    }

    stages {
        stage('Version Information') {
            steps {
                echo "Application Version: ${params.APP_VERSION}"
            }
        }
    }
}
```

**Try these values:**

```
1.0.0
1.0.1
2.0.0
2.5.1
```

Observe how the output changes.

## **Example 3 – Choice parameter for deployment environment**

**Objective:** Select DEV, QA or PROD.

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
        stage('Display Environment') {
            steps {
                echo "Selected Environment: ${params.ENVIRONMENT}"
            }
        }
    }
}
```

**Production use:** A single Jenkins pipeline can deploy to different environments based on user selection.

## **Example 4 – Boolean parameter to enable testing**

**Objective:** Run tests only when the checkbox is selected.

```
pipeline {
    agent any

    parameters {
        booleanParam(
            name: 'RUN_TESTS',
            defaultValue: true,
            description: 'Enable automated testing'
        )
    }

    stages {
        stage('Build') {
            steps {
                echo 'Building application'
            }
        }

        stage('Testing') {
            when {
                expression {
                    params.RUN_TESTS == true
                }
            }

            steps {
                echo 'Executing automated tests'
            }
        }
    }
}
```

**Try this:**

- First run: Enable checkbox.
- Second run: Disable checkbox.

Observe whether the Testing stage executes.

## **Example 5 – Text parameter for release notes**

**Objective:** Accept multiple lines of release notes.

```
pipeline {
    agent any

    parameters {
        text(
            name: 'RELEASE_NOTES',
            defaultValue: 'Initial application release',
            description: 'Enter release notes'
        )
    }

    stages {
        stage('Display Release Notes') {
            steps {
                echo "Release Notes:"
                echo "${params.RELEASE_NOTES}"
            }
        }
    }
}
```

Try entering:

```
Version 2.0 release
Fixed login issue
Improved application performance
Added payment functionality
```

## **Example 6 – Multiple parameters in one pipeline**

**Objective:** Collect application name, version and environment.

```
pipeline {
    agent any

    parameters {
        string(
            name: 'APP_NAME',
            defaultValue: 'payment-service',
            description: 'Application name'
        )

        string(
            name: 'APP_VERSION',
            defaultValue: '1.0.0',
            description: 'Application version'
        )

        choice(
            name: 'ENVIRONMENT',
            choices: ['DEV', 'QA', 'PROD'],
            description: 'Deployment environment'
        )
    }

    stages {
        stage('Build Information') {
            steps {
                echo "Application: ${params.APP_NAME}"
                echo "Version: ${params.APP_VERSION}"
                echo "Environment: ${params.ENVIRONMENT}"
            }
        }
    }
}
```

**Student task:** Run the pipeline with three different combinations.

## **Example 7 – Parameter-driven conditional deployment**

**Objective:** Execute only the selected deployment stage.

```
pipeline {
    agent any

    parameters {
        choice(
            name: 'DEPLOY_ENV',
            choices: ['DEV', 'QA', 'PROD'],
            description: 'Choose deployment environment'
        )
    }

    stages {
        stage('Deploy DEV') {
            when {
                expression {
                    params.DEPLOY_ENV == 'DEV'
                }
            }

            steps {
                echo 'Deploying to DEV'
            }
        }

        stage('Deploy QA') {
            when {
                expression {
                    params.DEPLOY_ENV == 'QA'
                }
            }

            steps {
                echo 'Deploying to QA'
            }
        }

        stage('Deploy PROD') {
            when {
                expression {
                    params.DEPLOY_ENV == 'PROD'
                }
            }

            steps {
                echo 'Deploying to PROD'
            }
        }
    }
}
```

**Understand:** The `when` condition determines whether a stage should execute.

## **Example 8 – Boolean parameter for security scanning**

**Objective:** Enable or skip a security scan.

```
pipeline {
    agent any

    parameters {
        booleanParam(
            name: 'RUN_SECURITY_SCAN',
            defaultValue: true,
            description: 'Run security scan'
        )
    }

    stages {
        stage('Build') {
            steps {
                echo 'Application build completed'
            }
        }

        stage('Security Scan') {
            when {
                expression {
                    params.RUN_SECURITY_SCAN
                }
            }

            steps {
                echo 'Running security scan simulation'
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

**DevSecOps connection:** In a real pipeline, this stage could invoke tools such as SonarQube, Checkmarx or Black Duck. This example only simulates the scan.

## **Example 9 – Parameter validation**

**Objective:** Reject an empty application name.

```
pipeline {
    agent any

    parameters {
        string(
            name: 'APP_NAME',
            defaultValue: 'my-app',
            description: 'Application name'
        )
    }

    stages {
        stage('Validate Input') {
            steps {
                script {
                    if (params.APP_NAME.trim() == '') {
                        error('Application name cannot be empty')
                    }

                    echo "Valid application name: ${params.APP_NAME}"
                }
            }
        }
    }
}
```

**Try:** Remove the default value, submit an empty name and observe the build result.

## **Example 10 – Generate release information**

**Objective:** Combine parameters to generate a release message.

```
pipeline {
    agent any

    parameters {
        string(
            name: 'APP_NAME',
            defaultValue: 'banking-app'
        )

        string(
            name: 'VERSION',
            defaultValue: '2.0.0'
        )

        choice(
            name: 'ENVIRONMENT',
            choices: ['DEV', 'QA', 'PROD']
        )
    }

    stages {
        stage('Release Information') {
            steps {
                script {
                    echo "Release: ${params.APP_NAME}"
                    echo "Version: ${params.VERSION}"
                    echo "Target: ${params.ENVIRONMENT}"
                    echo "Release ID: ${params.APP_NAME}-${params.VERSION}-${params.ENVIRONMENT}"
                }
            }
        }
    }
}
```

# **Level 2 – Jenkins Environment Variables**

## **Example 11 – Display built-in environment variables**

**Objective:** Understand Jenkins-provided environment variables.

```
pipeline {
    agent any

    stages {
        stage('Environment Details') {
            steps {
                echo "BUILD_NUMBER: ${env.BUILD_NUMBER}"
                echo "BUILD_ID: ${env.BUILD_ID}"
                echo "JOB_NAME: ${env.JOB_NAME}"
                echo "WORKSPACE: ${env.WORKSPACE}"
                echo "BUILD_URL: ${env.BUILD_URL}"
            }
        }
    }
}
```

**Student task:** Execute the pipeline three times and compare the build numbers.

## **Example 12 – Create custom environment variables**

**Objective:** Define your own variables.

```
pipeline {
    agent any

    environment {
        APP_NAME = 'employee-service'
        APP_VERSION = '1.0.0'
        TEAM = 'DevOps'
    }

    stages {
        stage('Application Details') {
            steps {
                echo "Application: ${env.APP_NAME}"
                echo "Version: ${env.APP_VERSION}"
                echo "Team: ${env.TEAM}"
            }
        }
    }
}
```

## **Example 13 – Environment variables at stage level**

**Objective:** Define different variables for individual stages.

```
pipeline {
    agent any

    stages {
        stage('Development') {
            environment {
                DEPLOY_ENV = 'DEV'
            }

            steps {
                echo "Environment: ${env.DEPLOY_ENV}"
            }
        }

        stage('Testing') {
            environment {
                DEPLOY_ENV = 'QA'
            }

            steps {
                echo "Environment: ${env.DEPLOY_ENV}"
            }
        }

        stage('Production') {
            environment {
                DEPLOY_ENV = 'PROD'
            }

            steps {
                echo "Environment: ${env.DEPLOY_ENV}"
            }
        }
    }
}
```

**Understand:** A stage-level environment variable is available within its respective stage.

## **Example 14 – Display environment variables using shell**

**Objective:** Understand how Jenkins passes environment variables to shell commands.

```
pipeline {
    agent any

    environment {
        APP_NAME = 'inventory-service'
        VERSION = '2.1.0'
    }

    stages {
        stage('Display Using Shell') {
            steps {
                sh '''
                    echo "Application: $APP_NAME"
                    echo "Version: $VERSION"
                    echo "Build Number: $BUILD_NUMBER"
                '''
            }
        }
    }
}
```

**Important:** This example requires a Jenkins agent with a Unix/Linux shell and the `sh` step. If Prepare.sh does not provide one, skip execution and study the Jenkinsfile.

## **Example 15 – Generate application build version**

**Objective:** Create a version based on Jenkins build number.

```
pipeline {
    agent any

    environment {
        APP_NAME = 'student-app'
        VERSION_PREFIX = '1.0'
    }

    stages {
        stage('Generate Version') {
            steps {
                script {
                    def buildVersion = "${env.VERSION_PREFIX}.${env.BUILD_NUMBER}"

                    echo "Application: ${env.APP_NAME}"
                    echo "Generated Version: ${buildVersion}"
                }
            }
        }
    }
}
```

Example output:

```
Application: student-app
Generated Version: 1.0.1
```

The final number changes with each build.

## **Example 16 – Change environment variable dynamically**

**Objective:** Update an environment variable during pipeline execution.

```
pipeline {
    agent any

    environment {
        BUILD_STATUS = 'STARTED'
    }

    stages {
        stage('Build') {
            steps {
                script {
                    echo "Before Build: ${env.BUILD_STATUS}"

                    env.BUILD_STATUS = 'BUILD_COMPLETED'

                    echo "After Build: ${env.BUILD_STATUS}"
                }
            }
        }
    }
}
```

Understand how the value changes during pipeline execution.

## **Example 17 – Combine environment variables and parameters**

**Objective:** Use a runtime parameter with a custom environment variable.

```
pipeline {
    agent any

    parameters {
        string(
            name: 'APP_VERSION',
            defaultValue: '3.0.0'
        )
    }

    environment {
        APP_NAME = 'customer-portal'
    }

    stages {
        stage('Build') {
            steps {
                echo "Building ${env.APP_NAME}"
                echo "Version: ${params.APP_VERSION}"
                echo "Build: ${env.BUILD_NUMBER}"
            }
        }
    }
}
```

**Student task:** Change the version and compare the output.

# **Level 3 – Production-Oriented Jenkins Examples**

## **Example 18 – Build and deployment configuration**

**Objective:** Simulate a deployment pipeline using parameters.

```
pipeline {
    agent any

    parameters {
        choice(
            name: 'ENVIRONMENT',
            choices: ['DEV', 'QA', 'PROD']
        )

        string(
            name: 'APP_VERSION',
            defaultValue: '1.0.0'
        )
    }

    environment {
        APP_NAME = 'online-banking'
        REGION = 'ap-south-1'
    }

    stages {
        stage('Configuration') {
            steps {
                echo "Application: ${env.APP_NAME}"
                echo "Version: ${params.APP_VERSION}"
                echo "Environment: ${params.ENVIRONMENT}"
                echo "Region: ${env.REGION}"
            }
        }

        stage('Build') {
            steps {
                echo 'Building application'
            }
        }

        stage('Deploy Simulation') {
            steps {
                echo "Deploying to ${params.ENVIRONMENT}"
            }
        }
    }
}
```

## **Example 19 – Production deployment approval simulation**

**Objective:** Understand how production approval can be included.

```
pipeline {
    agent any

    parameters {
        choice(
            name: 'ENVIRONMENT',
            choices: ['DEV', 'QA', 'PROD']
        )
    }

    stages {
        stage('Build') {
            steps {
                echo 'Build completed'
            }
        }

        stage('Production Approval') {
            when {
                expression {
                    params.ENVIRONMENT == 'PROD'
                }
            }

            steps {
                input message: 'Approve production deployment?'
            }
        }

        stage('Deployment') {
            steps {
                echo "Deploying to ${params.ENVIRONMENT}"
            }
        }
    }
}
```

**Important:** This uses Jenkins' interactive `input` step. It may not work in every playground. Real production pipelines should restrict approval permissions and use appropriate authorization.

## **Example 20 – Generate a deployment report**

**Objective:** Generate a deployment report using parameters and environment variables.

```
pipeline {
    agent any

    parameters {
        choice(
            name: 'ENVIRONMENT',
            choices: ['DEV', 'QA', 'PROD']
        )

        string(
            name: 'VERSION',
            defaultValue: '1.0.0'
        )
    }

    environment {
        APP_NAME = 'insurance-portal'
    }

    stages {
        stage('Generate Report') {
            steps {
                script {
                    def report = """
Application: ${env.APP_NAME}
Version: ${params.VERSION}
Environment: ${params.ENVIRONMENT}
Build Number: ${env.BUILD_NUMBER}
Job Name: ${env.JOB_NAME}
Status: Deployment Simulation Completed
"""

                    writeFile(
                        file: 'deployment-report.txt',
                        text: report
                    )

                    echo report
                }
            }
        }

        stage('Archive Report') {
            steps {
                archiveArtifacts artifacts: 'deployment-report.txt'
            }
        }
    }
}
```

**Requirements:** The Jenkins Pipeline Basic Steps and artifact archiving functionality must be available.

# **Level 4 – Jenkins Credentials and Secret Management**

These five exercises teach credential handling. Use an actual Jenkins installation with Manage Jenkins → Credentials access. Prepare.sh may not expose the required configuration.

## **Example 21 – Load a secret text credential**

**Objective:** Retrieve a GitHub token from Jenkins Credentials without hardcoding it.

First create a Jenkins credential:

| Field  | Value             |
| ------ | ----------------- |
| Kind   | Secret text       |
| Secret | Your GitHub token |
| ID     | `github-token`    |

Jenkinsfile:

```
pipeline {
    agent any

    stages {
        stage('Load Credential') {
            steps {
                withCredentials([
                    string(
                        credentialsId: 'github-token',
                        variable: 'GITHUB_TOKEN'
                    )
                ]) {
                    echo 'GitHub token loaded successfully'
                    echo 'Token value is not displayed'
                }
            }
        }
    }
}
```

**Important:** Never print the token itself.

## **Example 22 – Use username and password credentials**

**Objective:** Load Git authentication credentials.

Create a Jenkins credential:

- Kind: Username with password
- ID: `github-credentials`
- Username: Your GitHub username
- Password: GitHub Personal Access Token

Jenkinsfile:

```
pipeline {
    agent any

    stages {
        stage('Load Git Credentials') {
            steps {
                withCredentials([
                    usernamePassword(
                        credentialsId: 'github-credentials',
                        usernameVariable: 'GIT_USER',
                        passwordVariable: 'GIT_TOKEN'
                    )
                ]) {
                    echo 'GitHub username credential loaded'
                    echo 'Authentication token loaded securely'
                }
            }
        }
    }
}
```

## **Example 23 – Checkout a private GitHub repository**

**Objective:** Use Jenkins credentials during source-code checkout.

```
pipeline {
    agent any

    stages {
        stage('Checkout') {
            steps {
                git branch: 'main',
                    credentialsId: 'github-credentials',
                    url: 'https://github.com/YOUR-USERNAME/private-repo.git'
            }
        }

        stage('Verify Source Code') {
            steps {
                echo 'Private repository checkout completed'
            }
        }
    }
}
```

Replace the repository details with your own.

**Production relevance:** Private repositories are commonly used in enterprise development environments.

## **Example 24 – Secret masking and safe handling**

**Objective:** Understand why secrets should never be exposed in console logs.

```
pipeline {
    agent any

    stages {
        stage('Secure Credential Handling') {
            steps {
                withCredentials([
                    string(
                        credentialsId: 'github-token',
                        variable: 'TOKEN'
                    )
                ]) {
                    echo 'Credential loaded'

                    sh '''
                        if [ -n "$TOKEN" ]; then
                            echo "Token is available"
                        else
                            echo "Token is missing"
                        fi
                    '''
                }
            }
        }
    }
}
```

**Understand:**

- `TOKEN` is populated from Jenkins Credentials.
- The shell checks whether the token exists.
- The token itself is never printed.
- Jenkins can mask recognized secret values in logs, but masking is not a substitute for safe handling.

## **Example 25 – Complete DevSecOps pipeline with credentials**

**Objective:** Combine parameters, environment variables, credentials and simulated security checks.

```
pipeline {
    agent any

    parameters {
        choice(
            name: 'DEPLOY_ENV',
            choices: ['DEV', 'QA', 'PROD']
        )

        string(
            name: 'APP_VERSION',
            defaultValue: '1.0.0'
        )

        booleanParam(
            name: 'RUN_SECURITY_SCAN',
            defaultValue: true
        )
    }

    environment {
        APP_NAME = 'secure-banking-app'
        BUILD_TEAM = 'DevSecOps'
    }

    stages {
        stage('Build Information') {
            steps {
                echo "Application: ${env.APP_NAME}"
                echo "Version: ${params.APP_VERSION}"
                echo "Environment: ${params.DEPLOY_ENV}"
                echo "Build Number: ${env.BUILD_NUMBER}"
                echo "Team: ${env.BUILD_TEAM}"
            }
        }

        stage('Checkout') {
            steps {
                echo 'Source code checkout simulation'
            }
        }

        stage('Build') {
            steps {
                echo 'Application build simulation'
            }
        }

        stage('Security Scan') {
            when {
                expression {
                    params.RUN_SECURITY_SCAN
                }
            }

            steps {
                echo 'Gitleaks scan simulation'
                echo 'SonarQube scan simulation'
                echo 'Checkmarx scan simulation'
                echo 'Black Duck scan simulation'
            }
        }

        stage('Deploy') {
            steps {
                echo "Deployment simulation to ${params.DEPLOY_ENV}"
            }
        }

        stage('Final Report') {
            steps {
                echo 'DevSecOps pipeline completed'
            }
        }
    }
}
```

**Important:** This is a simulated DevSecOps pipeline. It does not perform real source checkout, security scans, credential retrieval or deployment. Those integrations require actual tools, credentials, plugins and infrastructure.

# **Student assessment**

## **Practical challenge**

Ask each student to build one pipeline using the following requirements:

| Requirement               | Expected implementation          |
| ------------------------- | -------------------------------- |
| Application name          | String parameter                 |
| Application version       | String parameter                 |
| Deployment environment    | Choice parameter                 |
| Security scanning         | Boolean parameter                |
| Build number              | Jenkins environment variable     |
| Application configuration | Custom environment variables     |
| GitHub authentication     | Jenkins Credentials              |
| Deployment                | Conditional stages               |
| Report                    | Generate build/deployment report |

## **10 interview questions**

1. What is a Jenkins build parameter?
2. What is the difference between `params` and `env`?
3. What is a choice parameter?
4. What is a boolean parameter?
5. What is the purpose of `BUILD_NUMBER`?
6. How do you define custom environment variables?
7. What is Jenkins Credentials?
8. What is the difference between Secret Text and Username with Password?
9. Why should we avoid hardcoding passwords in Jenkinsfiles?
10. How can Jenkins securely access a private GitHub repository?

## **GitHub repository structure**

Create the following structure and save each exercise as an individual Jenkinsfile.

```
jenkins-training/
│
└── Session-04-Parameters-Environment-Credentials/
    │
    ├── README.md
    │
    ├── Level-01-Parameters/
    │   ├── 01-string-parameter.Jenkinsfile
    │   ├── 02-version-parameter.Jenkinsfile
    │   ├── 03-choice-parameter.Jenkinsfile
    │   ├── 04-boolean-parameter.Jenkinsfile
    │   ├── 05-text-parameter.Jenkinsfile
    │   ├── 06-multiple-parameters.Jenkinsfile
    │   ├── 07-conditional-deployment.Jenkinsfile
    │   ├── 08-security-scan-parameter.Jenkinsfile
    │   ├── 09-parameter-validation.Jenkinsfile
    │   └── 10-release-information.Jenkinsfile
    │
    ├── Level-02-Environment-Variables/
    │   ├── 11-built-in-variables.Jenkinsfile
    │   ├── 12-custom-variables.Jenkinsfile
    │   ├── 13-stage-level-variables.Jenkinsfile
    │   ├── 14-shell-variables.Jenkinsfile
    │   ├── 15-build-version.Jenkinsfile
    │   ├── 16-dynamic-variable.Jenkinsfile
    │   └── 17-parameters-and-variables.Jenkinsfile
    │
    ├── Level-03-Production-Examples/
    │   ├── 18-deployment-configuration.Jenkinsfile
    │   ├── 19-production-approval.Jenkinsfile
    │   └── 20-deployment-report.Jenkinsfile
    │
    └── Level-04-Credentials/
        ├── 21-secret-text.Jenkinsfile
        ├── 22-username-password.Jenkinsfile
        ├── 23-private-github-checkout.Jenkinsfile
        ├── 24-secret-masking.Jenkinsfile
        └── 25-devsecops-pipeline.Jenkinsfile
```

## **Completion checklist**

**Student progress**

# **0/8**

Complete examples 1–10: Build Parameters

Complete examples 11–17: Environment Variables

Complete examples 18–20: Production Scenarios

Understand examples 21–24: Jenkins Credentials

Complete example 25: DevSecOps Pipeline

Upload all Jenkinsfiles to GitHub

Capture successful and failed build screenshots

Write down five errors encountered and their solutions

**Trainer's instruction:** Do not ask students to simply copy and paste all 25 Jenkinsfiles. Ask them to modify application names, versions, environments and conditions, execute the builds, inspect Console Output and explain what happened.

**Next session:** Session 5 – Jenkins Agents, Distributed Builds, Executors, Labels and Docker Integration.
