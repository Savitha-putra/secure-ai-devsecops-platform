# **Session 5 – 25 Practical Jenkins Examples**

## **Agents, Executors, Labels, Distributed Builds and Docker Integration**



25 Hands-on Exercises

Beginner to Intermediate



**Platform:** Prepare.sh Jenkins Playground (`prepare.sh/jenkins`)\
**Recommended duration:** 2–3 hours\
**Prerequisite:** Session 5 – Jenkins Agents and Distributed Builds

## **Learning objectives**

After completing these 25 examples, students should understand:

- Jenkins Controller and Agents.
- Executors and Labels.
- `agent any`, `agent none` and stage-level agents.
- Linux and Windows build agents.
- Docker-based build environments.
- Parallel builds.
- Artifact archiving and workspace management.
- Stash and unstash.
- Distributed CI/CD pipeline architecture.

**Important about Prepare.sh:** Examples using `echo` and basic Declarative Pipeline syntax are suitable for playground practice where Pipeline support is available. Examples requiring Linux/Windows agents, Docker, remote nodes or administrator permissions need a suitable Jenkins environment. Do not assume Prepare.sh provides those facilities.

# **Level 1 – Jenkins Agent Basics**

## **Example 1 – Run a pipeline using agent any**

**Objective:** Understand how Jenkins selects an available agent.

```
pipeline {
    agent any

    stages {
        stage('Build') {
            steps {
                echo 'Build started'
                echo 'Jenkins selected an available agent'
            }
        }

        stage('Test') {
            steps {
                echo 'Executing application tests'
            }
        }

        stage('Complete') {
            steps {
                echo 'Build completed successfully'
            }
        }
    }
}
```

**Try this:**

1. Create a Pipeline job.
2. Paste the Jenkinsfile.
3. Execute the build.
4. Check Console Output.

**Understand:** `agent any` allows Jenkins to select any eligible available agent.

## **Example 2 – Run a pipeline using a Linux agent**

**Objective:** Execute a pipeline on an agent with the `linux` label.

```
pipeline {
    agent {
        label 'linux'
    }

    stages {
        stage('Linux Build') {
            steps {
                echo 'Running on Linux agent'
                echo 'Preparing Linux build environment'
            }
        }
    }
}
```

**Production example:** A Java application may need to compile on a Linux build server.

**Requirement:** An online agent with the `linux` label must exist.

## **Example 3 – Run a pipeline using a Windows agent**

**Objective:** Select a Windows agent.

```
pipeline {
    agent {
        label 'windows'
    }

    stages {
        stage('Windows Build') {
            steps {
                echo 'Running on Windows agent'
                echo 'Preparing Windows build environment'
            }
        }
    }
}
```

**Production example:** .NET Framework applications may require Windows build agents.

## **Example 4 – Understand agent none**

**Objective:** Prevent Jenkins from reserving a global agent.

```
pipeline {
    agent none

    stages {
        stage('Build') {
            agent any

            steps {
                echo 'Build running on selected agent'
            }
        }

        stage('Test') {
            agent any

            steps {
                echo 'Test running on selected agent'
            }
        }
    }
}
```

**Understand:**

- `agent none` means no global agent is allocated.
- Each stage specifies its own agent.
- Different stages can execute on different agents.

## **Example 5 – Display agent and workspace information**

**Objective:** Understand where Jenkins executes a build.

```
pipeline {
    agent any

    stages {
        stage('Agent Information') {
            steps {
                echo "Job Name: ${env.JOB_NAME}"
                echo "Build Number: ${env.BUILD_NUMBER}"
                echo "Build ID: ${env.BUILD_ID}"
                echo "Workspace: ${env.WORKSPACE}"
                echo "Node Name: ${env.NODE_NAME}"
            }
        }
    }
}
```

**Student task:** Run this three times and compare the output.

Remember that the actual agent and workspace depend on the Jenkins environment.

## **Example 6 – Execute Linux commands on an agent**

**Objective:** Execute operating system commands from Jenkins.

```
pipeline {
    agent any

    stages {
        stage('Linux Commands') {
            steps {
                sh '''
                    echo "Current User"
                    whoami

                    echo "Hostname"
                    hostname

                    echo "Current Directory"
                    pwd

                    echo "Disk Usage"
                    df -h

                    echo "Memory Usage"
                    free -h
                '''
            }
        }
    }
}
```

**Commands explained:**

| Command    | Purpose           |
| ---------- | ----------------- |
| `whoami`   | Current user      |
| `hostname` | Machine name      |
| `pwd`      | Current directory |
| `df -h`    | Disk usage        |
| `free -h`  | Memory usage      |

Requires a Linux agent with shell support.

## **Example 7 – Execute Windows commands on an agent**

**Objective:** Execute Windows batch commands.

```
pipeline {
    agent any

    stages {
        stage('Windows Commands') {
            steps {
                bat '''
                    echo Current User
                    whoami

                    echo Computer Name
                    hostname

                    echo Current Directory
                    cd

                    echo Operating System
                    ver
                '''
            }
        }
    }
}
```

**Remember:**

- `sh` is used for Unix/Linux shell commands.
- `bat` is used for Windows batch commands.

# **Level 2 – Workspace and Agent Management**

## **Example 8 – Clean the Jenkins workspace**

**Objective:** Remove old workspace contents before a build.

```
pipeline {
    agent any

    stages {
        stage('Clean Workspace') {
            steps {
                deleteDir()
                echo 'Workspace cleaned successfully'
            }
        }

        stage('Build') {
            steps {
                echo 'Starting fresh build'
            }
        }
    }
}
```

**Understand:** `deleteDir()` deletes the current workspace contents.

Do not execute cleanup commands outside the intended workspace.

## **Example 9 – Create files in the workspace**

**Objective:** Understand how Jenkins creates build files.

```
pipeline {
    agent any

    stages {
        stage('Create Files') {
            steps {
                writeFile(
                    file: 'application.txt',
                    text: 'Welcome to Jenkins training'
                )

                writeFile(
                    file: 'version.txt',
                    text: 'Application Version 1.0'
                )

                echo 'Files created successfully'
            }
        }
    }
}
```

**Student task:** Modify the application name and version.

## **Example 10 – Read workspace files**

**Objective:** Read files generated during a Jenkins build.

```
pipeline {
    agent any

    stages {
        stage('Create File') {
            steps {
                writeFile(
                    file: 'app.txt',
                    text: 'Employee Management Application'
                )
            }
        }

        stage('Read File') {
            steps {
                script {
                    def content = readFile('app.txt')
                    echo "File Content: ${content}"
                }
            }
        }
    }
}
```

## **Example 11 – Generate a build report**

**Objective:** Create a report containing Jenkins build details.

```
pipeline {
    agent any

    stages {
        stage('Generate Report') {
            steps {
                script {
                    def report = """
Jenkins Build Report

Job Name: ${env.JOB_NAME}
Build Number: ${env.BUILD_NUMBER}
Build ID: ${env.BUILD_ID}
Node Name: ${env.NODE_NAME}
Result: Build Information Generated
"""

                    writeFile(
                        file: 'build-report.txt',
                        text: report
                    )

                    echo report
                }
            }
        }
    }
}
```

## **Example 12 – Archive build artifacts**

**Objective:** Store generated files as Jenkins build artifacts.

```
pipeline {
    agent any

    stages {
        stage('Create Artifact') {
            steps {
                writeFile(
                    file: 'application-build.txt',
                    text: 'Application build completed'
                )
            }
        }

        stage('Archive Artifact') {
            steps {
                archiveArtifacts artifacts: 'application-build.txt'
                echo 'Artifact archived'
            }
        }
    }
}
```

**Production relevance:** Jenkins can archive JAR, WAR, ZIP, reports and other build outputs.

# **Level 3 – Docker Integration**

## **Example 13 – Run a pipeline inside an Ubuntu Docker container**

**Objective:** Understand Docker-based build environments.

```
pipeline {
    agent {
        docker {
            image 'ubuntu:latest'
        }
    }

    stages {
        stage('Check Operating System') {
            steps {
                sh 'cat /etc/os-release'
            }
        }

        stage('Display Message') {
            steps {
                sh 'echo "Running inside Ubuntu container"'
            }
        }
    }
}
```

**Requirements:**

- Docker Pipeline plugin.
- Docker-capable Jenkins agent.
- Docker daemon access.
- Image pull access.

## **Example 14 – Use a Maven Docker image**

**Objective:** Run a Java build environment without installing Maven manually on the agent.

```
pipeline {
    agent {
        docker {
            image 'maven:3.9-eclipse-temurin-17'
        }
    }

    stages {
        stage('Check Java') {
            steps {
                sh 'java -version'
            }
        }

        stage('Check Maven') {
            steps {
                sh 'mvn -version'
            }
        }

        stage('Build Information') {
            steps {
                echo 'Maven environment is ready'
            }
        }
    }
}
```

**Understand:** The Maven Docker image contains Maven and a compatible Java runtime.

## **Example 15 – Use a Python Docker image**

**Objective:** Execute Python commands inside a container.

```
pipeline {
    agent {
        docker {
            image 'python:3.12'
        }
    }

    stages {
        stage('Check Python') {
            steps {
                sh 'python --version'
                sh 'pip --version'
            }
        }

        stage('Python Script') {
            steps {
                sh '''
                    python -c "print('Hello from Jenkins Docker agent')"
                '''
            }
        }
    }
}
```

## **Example 16 – Use different Docker images in different stages**

**Objective:** Use multiple build environments in one pipeline.

```
pipeline {
    agent none

    stages {
        stage('Java Environment') {
            agent {
                docker {
                    image 'maven:3.9-eclipse-temurin-17'
                }
            }

            steps {
                sh 'java -version'
                sh 'mvn -version'
            }
        }

        stage('Python Environment') {
            agent {
                docker {
                    image 'python:3.12'
                }
            }

            steps {
                sh 'python --version'
                sh 'pip --version'
            }
        }
    }
}
```

**Production relevance:** A single CI/CD pipeline can use different toolchains for different application components.

## **Example 17 – Build a Docker image using Jenkins**

**Objective:** Understand how Jenkins builds container images.

Create a `Dockerfile` in the project repository:

```
FROM nginx:alpine

COPY index.html /usr/share/nginx/html/index.html
```

Create `index.html`:

```
<h1>Hello from Jenkins Docker Build</h1>
```

Use this Jenkinsfile:

```
pipeline {
    agent any

    stages {
        stage('Build Docker Image') {
            steps {
                sh 'docker build -t student-app:1.0 .'
            }
        }

        stage('List Docker Images') {
            steps {
                sh 'docker images'
            }
        }
    }
}
```

**Student task:**

- Change the image name.
- Change the tag to `2.0`.
- Observe the image list.

Requires Docker CLI, Docker daemon access and a Dockerfile in the workspace.

# **Level 4 – Distributed Builds and Parallel Execution**

## **Example 18 – Run multiple stages in parallel**

**Objective:** Execute independent pipeline stages simultaneously.

```
pipeline {
    agent any

    stages {
        stage('Parallel Testing') {
            parallel {
                stage('Unit Tests') {
                    steps {
                        echo 'Executing unit tests'
                    }
                }

                stage('Integration Tests') {
                    steps {
                        echo 'Executing integration tests'
                    }
                }

                stage('Security Tests') {
                    steps {
                        echo 'Executing security scan simulation'
                    }
                }
            }
        }
    }
}
```

**Production relevance:** Parallel execution reduces pipeline duration when tasks are independent.

## **Example 19 – Run parallel stages on different agents**

**Objective:** Execute tests on Linux and Windows agents.

```
pipeline {
    agent none

    stages {
        stage('Cross Platform Testing') {
            parallel {
                stage('Linux Testing') {
                    agent {
                        label 'linux'
                    }

                    steps {
                        echo 'Running Linux tests'
                    }
                }

                stage('Windows Testing') {
                    agent {
                        label 'windows'
                    }

                    steps {
                        echo 'Running Windows tests'
                    }
                }
            }
        }
    }
}
```

Requires two configured, online agents.

## **Example 20 – Select an agent using a parameter**

**Objective:** Allow the user to select an execution environment.

```
pipeline {
    agent none

    parameters {
        choice(
            name: 'BUILD_PLATFORM',
            choices: ['linux', 'windows'],
            description: 'Choose build agent'
        )
    }

    stages {
        stage('Platform Build') {
            agent {
                label "${params.BUILD_PLATFORM}"
            }

            steps {
                echo "Selected agent: ${params.BUILD_PLATFORM}"
            }
        }
    }
}
```

**Student task:** Try both platform options if the corresponding agents exist.

## **Example 21 – Transfer files between agents using stash and unstash**

**Objective:** Share build files between different stages.

```
pipeline {
    agent none

    stages {
        stage('Build on Linux') {
            agent {
                label 'linux'
            }

            steps {
                writeFile(
                    file: 'application.txt',
                    text: 'Application build output'
                )

                stash(
                    name: 'application-files',
                    includes: 'application.txt'
                )

                echo 'Application files saved'
            }
        }

        stage('Test on Windows') {
            agent {
                label 'windows'
            }

            steps {
                unstash 'application-files'

                echo 'Application files received'
                echo readFile('application.txt')
            }
        }
    }
}
```

**Understand:**

- `stash` saves selected workspace files for the current pipeline run.
- `unstash` retrieves them in another stage.
- Both stages can use different agents.

For large files, prefer artifact repositories rather than relying on stash.

# **Level 5 – Advanced Agent and Production Scenarios**

## **Example 22 – Use multiple agent labels**

**Objective:** Select an agent that has both Linux and Docker capabilities.

```
pipeline {
    agent {
        label 'linux && docker'
    }

    stages {
        stage('Docker Build') {
            steps {
                echo 'Linux and Docker agent selected'
            }
        }
    }
}
```

**Understand:** The agent must have both labels.

## **Example 23 – Retry a failed operation**

**Objective:** Retry a step when a temporary failure occurs.

```
pipeline {
    agent any

    stages {
        stage('Download Dependencies') {
            steps {
                retry(3) {
                    echo 'Attempting dependency download'
                }
            }
        }
    }
}
```

This example demonstrates retry syntax only. It does not actually download dependencies.

**Production use:** Retry can help with temporary network errors, transient service failures and unstable external dependencies. Avoid retrying permanent failures blindly.

## **Example 24 – Build Docker image with dynamic version**

**Objective:** Generate a Docker image tag from a Jenkins parameter.

```
pipeline {
    agent any

    parameters {
        string(
            name: 'APP_VERSION',
            defaultValue: '1.0.0',
            description: 'Enter Docker image version'
        )
    }

    environment {
        IMAGE_NAME = 'student-application'
    }

    stages {
        stage('Generate Image Name') {
            steps {
                script {
                    def imageTag = "${env.IMAGE_NAME}:${params.APP_VERSION}"

                    echo "Docker image: ${imageTag}"
                }
            }
        }
    }
}
```

**Try these versions:**

```
1.0.0
1.0.1
2.0.0
2.1.0
```

This example generates the image tag as text; it does not build or push an image.

## **Example 25 – Complete distributed DevOps pipeline simulation**

**Objective:** Combine Jenkins agents, build stages, testing, Docker and security scanning concepts.

```
pipeline {
    agent any

    parameters {
        string(
            name: 'APP_VERSION',
            defaultValue: '1.0.0'
        )

        choice(
            name: 'DEPLOY_ENV',
            choices: ['DEV', 'QA', 'PROD']
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

        stage('Source Checkout') {
            steps {
                echo 'GitHub checkout simulation'
            }
        }

        stage('Application Build') {
            steps {
                echo 'Java application build simulation'
            }
        }

        stage('Parallel Testing') {
            parallel {
                stage('Unit Testing') {
                    steps {
                        echo 'Unit test simulation'
                    }
                }

                stage('Integration Testing') {
                    steps {
                        echo 'Integration test simulation'
                    }
                }

                stage('Security Scanning') {
                    steps {
                        echo 'Gitleaks simulation'
                        echo 'SonarQube simulation'
                        echo 'Checkmarx simulation'
                        echo 'Black Duck simulation'
                    }
                }
            }
        }

        stage('Docker Packaging') {
            steps {
                echo 'Docker image build simulation'
            }
        }

        stage('Deployment') {
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

**Important:** This is a learning simulation. It does not perform actual Git checkout, Docker image creation, security scanning or deployment. It uses one available agent and does not demonstrate real distributed execution.

# **Student assignment**

Create a repository folder:

`Session-05-Agents-Distributed-Builds-Docker`

Students must complete the following:

| No. | Task                           | Expected result             |
| --- | ------------------------------ | --------------------------- |
| 1   | Execute `agent any`            | Successful build            |
| 2   | Understand Linux agent label   | Agent selection             |
| 3   | Understand Windows agent label | Agent selection             |
| 4   | Execute `agent none`           | Stage-level allocation      |
| 5   | Display agent details          | Console output              |
| 6   | Execute Linux commands         | System information          |
| 7   | Execute Windows commands       | System information          |
| 8   | Clean workspace                | Workspace cleared           |
| 9   | Create workspace files         | Files generated             |
| 10  | Read workspace files           | File contents displayed     |
| 11  | Generate build report          | Report created              |
| 12  | Archive artifact               | Artifact stored             |
| 13  | Run Ubuntu Docker agent        | Container environment       |
| 14  | Run Maven Docker agent         | Maven version               |
| 15  | Run Python Docker agent        | Python version              |
| 16  | Use multiple Docker images     | Different environments      |
| 17  | Build Docker image             | Image generated             |
| 18  | Execute parallel stages        | Parallel build              |
| 19  | Execute cross-platform stages  | Linux and Windows execution |
| 20  | Select agent using parameter   | Dynamic agent selection     |
| 21  | Use stash and unstash          | File transfer               |
| 22  | Use multiple labels            | Agent filtering             |
| 23  | Implement retry                | Retry logic                 |
| 24  | Generate Docker image tag      | Dynamic version             |
| 25  | Complete DevOps pipeline       | Final pipeline              |

# **Interview questions**

1. What is a Jenkins Controller?
2. What is a Jenkins Agent?
3. What is the purpose of an Executor?
4. What is a Jenkins Label?
5. What is the difference between `agent any` and `agent none`?
6. What is a Jenkins workspace?
7. How can Jenkins execute Linux commands?
8. How can Jenkins execute Windows commands?
9. Why do we use Docker with Jenkins?
10. What is the Docker Pipeline plugin?
11. How do different stages use different agents?
12. What is distributed building?
13. What is parallel execution?
14. How do you transfer files between agents?
15. What is the difference between stash and archiveArtifacts?
16. What happens when an agent goes offline?
17. Why should we control the number of executors?
18. How do you assign a pipeline to a particular agent?
19. What is the difference between a Docker container and a Jenkins Agent?
20. How does distributed execution help large DevOps teams?

# **GitHub repository structure**

```
jenkins-training/
│
├── Session-01-Jenkins-Basics/
├── Session-02-Declarative-Pipeline/
├── Session-03-Jenkins-GitHub-Integration/
├── Session-04-Parameters-Environment-Credentials/
│
└── Session-05-Agents-Distributed-Builds-Docker/
    │
    ├── README.md
    │
    ├── Level-01-Agent-Basics/
    │   ├── 01-agent-any.Jenkinsfile
    │   ├── 02-linux-agent.Jenkinsfile
    │   ├── 03-windows-agent.Jenkinsfile
    │   ├── 04-agent-none.Jenkinsfile
    │   ├── 05-agent-information.Jenkinsfile
    │   ├── 06-linux-commands.Jenkinsfile
    │   └── 07-windows-commands.Jenkinsfile
    │
    ├── Level-02-Workspace/
    │   ├── 08-clean-workspace.Jenkinsfile
    │   ├── 09-create-files.Jenkinsfile
    │   ├── 10-read-files.Jenkinsfile
    │   ├── 11-build-report.Jenkinsfile
    │   └── 12-archive-artifacts.Jenkinsfile
    │
    ├── Level-03-Docker/
    │   ├── 13-ubuntu-docker-agent.Jenkinsfile
    │   ├── 14-maven-docker-agent.Jenkinsfile
    │   ├── 15-python-docker-agent.Jenkinsfile
    │   ├── 16-multiple-docker-images.Jenkinsfile
    │   └── 17-docker-image-build.Jenkinsfile
    │
    ├── Level-04-Distributed-Builds/
    │   ├── 18-parallel-stages.Jenkinsfile
    │   ├── 19-parallel-agents.Jenkinsfile
    │   ├── 20-parameter-agent-selection.Jenkinsfile
    │   └── 21-stash-unstash.Jenkinsfile
    │
    └── Level-05-Advanced/
        ├── 22-agent-labels.Jenkinsfile
        ├── 23-retry.Jenkinsfile
        ├── 24-docker-image-tagging.Jenkinsfile
        └── 25-distributed-devsecops-pipeline.Jenkinsfile
```

# **Student completion checklist**

**Student progress**

# **0/9**

Complete examples 1–7: Agent fundamentals

Complete examples 8–12: Workspace and artifacts

Complete examples 13–17: Docker integration

Complete examples 18–21: Distributed builds

Complete examples 22–25: Advanced practice

Capture Jenkins Console Output screenshots

Document errors and troubleshooting

Upload all 25 Jenkinsfiles to GitHub

Explain Controller, Agent and Executor in your own words

**Trainer's recommendation:** For Prepare.sh students, prioritize examples 1, 4, 5, 8–12, 18 and 23–25 where supported. Use a separate real Jenkins lab to demonstrate remote agent registration, Docker access and actual distributed builds.

**Next:** Session 6 – End-to-End Jenkins CI/CD Project, combining GitHub, Jenkins Pipeline, Docker, testing, DevSecOps scanning and deployment simulation.
