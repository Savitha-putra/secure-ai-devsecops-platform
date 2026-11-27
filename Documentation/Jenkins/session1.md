```markdown
# Session 1 (Hours 1–2): CI Fundamentals, Jenkins Architecture & Setup

> **Course:** Enterprise Jenkins & GitHub CI/CD Engineering  
> **Target Audience:** Freshers & Aspiring DevOps / Platform Engineers  
> **Prerequisites:** Basic Linux CLI navigation (`cd`, `ls`, `sudo`, `systemctl`) and basic Git familiarity (`clone`, `commit`, `push`).

---

## 1. Real-World Analogies & Architecture Diagrams

### Analogy 1: Traditional Integration vs. Continuous Integration (The Wedding Banquet)
* **Traditional Integration ("Integration Hell"):** Imagine 20 chefs cooking different dishes for a wedding in separate kitchens for 3 months without ever tasting each other's food or checking if the dishes fit on the serving platters. On the morning of the wedding, they bring everything together—the curry is too salty for the rice, the plates don't fit the warmers, and nobody knows who broke what.
* **Continuous Integration (CI):** Every time a chef finishes chopping a vegetable or making a sauce (a **Git commit**), a food critic (the **CI Server / Jenkins**) immediately tastes it, checks hygiene standards, and verifies it pairs well with the rest of the menu within 5 minutes. Bugs are caught while the code is still fresh in the developer's mind.

### Analogy 2: Jenkins Controller & Agent Topology (The Restaurant Head Chef & Line Cooks)
* **Jenkins Controller (formerly Master):** The **Head Chef**. The Head Chef does **not** chop onions or wash dishes. The Head Chef reads incoming orders (Git commits), checks the recipe (`Jenkinsfile`), assigns tasks to specialized cooks, tracks progress on the dashboard, and notifies the customer when the meal is ready.
* **Jenkins Agents (formerly Slaves/Workers):** The **Line Cooks**. One cook specializes in grilling (Linux + Docker agent), another in pastry (Windows + .NET agent), and another in sushi (macOS + iOS agent). They do all the heavy lifting and report results back to the Head Chef.

---

### ASCII Architecture Diagram: Jenkins Controller & Distributed Agents

```text
+-----------------------------------------------------------------------------------+
|                                DEVELOPER WORKFLOW                                 |
|   [Developer Laptop] --- git push ---> [GitHub Repository]                        |
+-------------------------------------------------|---------------------------------+
                                                  | (Poll / Webhook Trigger)
                                                  v
+-----------------------------------------------------------------------------------+
|                        JENKINS CONTROLLER (Brain / Orchestrator)                  |
|  +-----------------------+   +-----------------------+   +---------------------+  |
|  |   Web UI & REST API   |   |  Pipeline Scheduler   |   | Credentials & State |  |
|  |      (Port 8080)      |   |    & Plugin Engine    |   |  (/var/lib/jenkins) |  |
|  +-----------------------+   +-----------------------+   +---------------------+  |
|  * Best Practice: Set Executors = 0 on Controller (Never run builds here!)        |
+-------------------|-------------------------------------|-------------------------+
                    | JNLP / Inbound WebSocket (Port 50000) or Outbound SSH (Port 22)
        +-----------+                                     +-----------+
        v                                                 v
+-----------------------------------+   +-----------------------------------+
|      JENKINS AGENT 01 (Linux)     |   |      JENKINS AGENT 02 (Docker)    |
|  Labels: [linux, java17, maven]   |   |  Labels: [docker, trivy, aws-cli] |
|  +-----------------------------+  |   |  +-----------------------------+  |
|  | Workspace: /home/jenkins/ws |  |   |  | Workspace: /var/jenkins_ws  |  |
|  | Executes: mvn clean package |  |   |  | Executes: docker build/push |  |
|  +-----------------------------+  |   |  +-----------------------------+  |
+-----------------------------------+   +-----------------------------------+

```

---

## 2. Deep-Dive Concepts with Production Examples

### 2.1 Traditional Integration vs. Continuous Integration

| Dimension | Traditional Integration (Waterfall / Legacy) | Continuous Integration (Modern DevOps) |
| --- | --- | --- |
| **Integration Frequency** | Once every few weeks or months before release | Multiple times per day per developer |
| **Build & Test Execution** | Manual builds on a developer's local machine | Automated builds on isolated, clean CI agents |
| **Feedback Loop** | Days or weeks later (QA finds broken merges) | 2 to 10 minutes after `git push` |
| **Root Cause Isolation** | Painful—hundreds of commits mixed together | Trivial—tied to a single commit hash & author |
| **Release Readiness** | High stress ("Integration Hell") | Always in a deployable, tested state |

---

### 2.2 Jenkins Controller & Agent Topology (Modern Terminology)

In 2020, the Jenkins project officially replaced legacy *master/slave* terminology with **Controller** and **Agent** (or **Node**).

* **Controller Responsibilities:**
* Serves the Jenkins Web UI (default port `8080`) and REST API.
* Stores global configuration, plugin binaries, job definitions, build history logs, and encrypted secrets inside `$JENKINS_HOME` (`/var/lib/jenkins`).
* Schedules builds and dispatches execution instructions to Agents.


* **Agent Responsibilities:**
* Requires **only Java (JRE/JDK)** installed on the machine to run the `agent.jar` remoting process.
* Executes the actual build steps (`mvn`, `npm`, `pytest`, `docker build`) inside its local workspace directory.
* Streams console output back to the Controller in real time.



#### How Controller & Agent Connect (2 Enterprise Protocols)

1. **SSH Launch Agent (Controller $\rightarrow$ Agent over Port 22):** Controller initiates an SSH connection into a static Linux VM using an SSH private key, copies `agent.jar`, and starts it.
2. **Inbound Agent via WebSocket / JNLP (Agent $\rightarrow$ Controller over Port 8080 or 50000):** The Agent initiates an outbound connection to the Controller. **Preferred in enterprise firewalls and Docker/Kubernetes environments** because the Controller does not need SSH access into private subnets.

---

### 2.3 Installing Jenkins on Ubuntu 22.04/24.04 LTS (Production Method)

Jenkins is a Java application (distributed as `jenkins.war`). Always install the **LTS (Long-Term Support)** release in production—never the Weekly release.

```bash
# Step 1: Update OS packages and install Java 17 (Required runtime for modern Jenkins)
sudo apt update && sudo apt upgrade -y
sudo apt install -y fontconfig openjdk-17-jre git curl unzip

# Verify Java installation
java -version

# Step 2: Add the official Jenkins LTS GPG key and APT repository
sudo wget -O /usr/share/keyrings/jenkins-keyring.asc \
  [https://pkg.jenkins.io/debian-stable/jenkins.io-2023.key](https://pkg.jenkins.io/debian-stable/jenkins.io-2023.key)

echo "deb [signed-by=/usr/share/keyrings/jenkins-keyring.asc]" \
  [https://pkg.jenkins.io/debian-stable](https://pkg.jenkins.io/debian-stable) binary/ | sudo tee \
  /etc/apt/sources.list.d/jenkins.list > /dev/null

# Step 3: Install Jenkins LTS
sudo apt update
sudo apt install -y jenkins

# Step 4: Enable and start the systemd service
sudo systemctl enable --now jenkins
sudo systemctl status jenkins --no-pager

# Step 5: Retrieve the initial auto-generated Admin unlock password
sudo cat /var/lib/jenkins/secrets/initialAdminPassword

```

---

### 2.4 Global Tool Configuration & Plugin Management

In an enterprise environment, 50 microservices might require different versions of Java or Maven (e.g., legacy services on JDK 11, new services on JDK 21). Instead of hardcoding paths, DevOps engineers configure **Named Tools** in Jenkins:

* **Path in UI:** `Manage Jenkins` $\rightarrow$ `Tools`
* **JDK Installations:** Name: `JDK-17` (Auto-install or `JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64`)
* **Git Installations:** Name: `Default` (`Path to Git executable: /usr/bin/git`)
* **Maven Installations:** Name: `Maven-3.9` (Install automatically from Apache)


* **Essential Enterprise Plugins (`Manage Jenkins` $\rightarrow$ `Plugins`):**
1. `Pipeline` (workflow-aggregator) — Core engine for Declarative Pipelines
2. `Git` & `GitHub` — SCM checkout and webhook handling
3. `Credentials Binding` — Secure injection of tokens/passwords
4. `Docker Pipeline` — Running steps inside Docker containers
5. `Blue Ocean` or `Pipeline: Stage View` — Visual pipeline execution graphs



---

## 3. Industry Scenarios, Common Production Failures & DevOps Fixes

### How Enterprises Run Jenkins in Production

* **Zero-Executor Controller Policy:** Enterprise Platform teams always set **Number of Executors = `0**` on the Controller (`Manage Jenkins` $\rightarrow$ `Nodes` $\rightarrow$ `Built-In Node` $\rightarrow$ `Configure`). All workloads are routed to labeled Agents (`linux-maven`, `docker-builder`).
* **Automated Backups of `$JENKINS_HOME`:** Because Jenkins stores configuration as XML files in `/var/lib/jenkins`, teams snapshot the EBS volume nightly or use the **ThinBackup** plugin to push XML configs to an S3 bucket.

### 4 Common Production Failures & How DevOps Fixes Them

| # | Real-World Failure / Symptom | Root Cause in Industry | Step-by-Step DevOps Fix |
| --- | --- | --- | --- |
| **1** | **Controller crashes with `java.lang.OutOfMemoryError: Java heap space**` | Developers ran heavy Maven/Docker builds directly on the Controller, or JVM heap size wasn't tuned. | 1. Set Built-In Node executors to `0`.<br>

<br>2. Edit `/etc/default/jenkins` (or systemd override `systemctl edit jenkins`) and set `JAVA_OPTS="-Xms2g -Xmx4g -XX:+UseG1GC"`.<br>

<br>3. Restart Jenkins. |
| **2** | **`No space left on device` on `/var/lib/jenkins**` | Build workspaces, old build artifacts, and verbose logs filled the root disk to 100%. | 1. Run `df -h` and `du -sh /var/lib/jenkins/*` to locate bloated jobs.<br>

<br>2. Configure **Discard Old Builds** (keep last 10 builds / 7 days) on every job.<br>

<br>3. Mount a dedicated 100GB+ disk at `/var/lib/jenkins`. |
| **3** | **Jenkins fails to start after a bulk plugin update (Dependency Hell)** | Updating 30 plugins at once introduced an incompatible plugin API version. | 1. Never update all plugins blindly in production.<br>

<br>2. SSH into the Controller, navigate to `/var/lib/jenkins/plugins/`, rename the broken `.jpi` to `.jpi.disabled`, restore the `.bak` file, and run `sudo systemctl restart jenkins`. |
| **4** | **Agent shows `Offline: Disk space is below threshold` or `ClockDifference**` | Agent `/tmp` or workspace disk crossed 90% full, or NTP time drifted between Controller and Agent. | 1. Clean `/tmp` and stale workspaces on the Agent.<br>

<br>2. Synchronize system clocks on both nodes using `sudo timedatectl set-ntp true`. |

---

## 4. Guided Hands-On Lab (Classroom Practical)

### Objective

Install Jenkins on a Linux VM (or local Ubuntu/WSL2 instance), harden the Built-In Node, configure global tools (`JDK-17`, `Maven-3.9`), and attach a local/remote Linux Build Agent.

### Step-by-Step Instructions

1. **Install and Verify Jenkins:**
Run the installation commands from **Section 2.3** and verify port `8080` is listening:
```bash
sudo ss -tulpn | grep 8080

```


2. **Complete the Setup Wizard:**
* Open `http://<YOUR-SERVER-IP>:8080` in your browser.
* Paste the password from `/var/lib/jenkins/secrets/initialAdminPassword`.
* Select **Install suggested plugins** and wait for completion.
* Create your first Admin user (`admin` / `Admin@1234`).


3. **Apply Enterprise Security Hardening (Zero Executors on Controller):**
* Navigate to **Manage Jenkins** $\rightarrow$ **Nodes**.
* Click the gear icon next to **Built-In Node**.
* Change **Number of executors** from `2` to `0` and click **Save**.


4. **Configure Global Tools:**
* Navigate to **Manage Jenkins** $\rightarrow$ **Tools**.
* Under **Maven installations**, click **Add Maven**, set Name = `Maven-3.9`, check **Install automatically**, and click **Save**.


5. **Provision & Connect an Inbound Agent (Simulated on Same VM or Second VM):**
* Create a dedicated agent workspace directory:
```bash
sudo mkdir -p /opt/jenkins-agent
sudo chown -R $USER:$USER /opt/jenkins-agent

```


* In Jenkins UI: **Manage Jenkins** $\rightarrow$ **Nodes** $\rightarrow$ **New Node**.
* Node name: `linux-agent-01` $\rightarrow$ Select **Permanent Agent** $\rightarrow$ **Create**.
* Configure:
* **Number of executors:** `2`
* **Remote root directory:** `/opt/jenkins-agent`
* **Labels:** `linux java maven`
* **Usage:** `Use this node as much as possible`
* **Launch method:** `Launch agent by connecting it to the controller` (Enable WebSocket if prompted).


* Click **Save**, click on `linux-agent-01`, and run the `curl` + `java -jar agent.jar` command displayed on screen inside your terminal.
* Confirm the agent status turns **Online (Idle)** in the UI!



---

## 5. Take-Home Mini-Project (Portfolio / LinkedIn Ready)

### Project Title: *"Production-Hardened Jenkins Controller-Agent Lab with Automated Health Audit"*

#### Scenario

Your startup's engineering team currently runs builds on a developer's laptop. Your manager asked you to stand up a clean, production-grade Jenkins Controller + Agent architecture where the Controller never executes builds directly, and write a Bash health-check script to validate the setup.

#### Project Deliverables (Push to a GitHub Repository `jenkins-architecture-lab`)

1. **`setup-controller.sh`**: An idempotent Bash script that installs Java 17, installs Jenkins LTS, and outputs the service status and listening port.
2. **`health-check.sh`**: A Bash script using `systemctl`, `ss`, `df`, and `curl` that checks:
* Is `jenkins.service` active?
* Is port `8080` listening?
* Does `curl -I http://localhost:8080/login` return HTTP `200 OK`?
* Is free disk space on `/var/lib/jenkins` above 20%?


3. **`README.md` with Architecture Proof**:
* Include your own ASCII diagram showing your Controller and Agent labels.
* Attach screenshots of your **Nodes dashboard** proving `Built-In Node` has `0` executors and `linux-agent-01` is online and idle.



---

## 6. Knowledge Check: 10 Multiple-Choice Questions (MCQs)

1. **What is the primary goal of Continuous Integration (CI)?**
* A) Deploying code directly to production servers without human approval
* B) Merging developer code changes frequently into a shared repository with automated builds and tests
* C) Replacing Git version control with automated file backups
* D) Manually testing all features once at the end of a 3-month release cycle


2. **Why did Jenkins replace the legacy "Master-Slave" terminology?**
* A) To introduce a paid enterprise licensing tier
* B) To accurately reflect the architectural roles of orchestration (`Controller`) and workload execution (`Agent`) using inclusive industry terminology
* C) Because Jenkins dropped support for distributed builds
* D) To merge Jenkins with GitHub Actions


3. **Why do enterprise DevOps teams set the Number of Executors on the Jenkins Built-In Node (Controller) to `0`?**
* A) To disable all scheduled cron jobs
* B) To prevent builds from consuming Controller CPU/RAM and protect sensitive files inside `$JENKINS_HOME`
* C) Because Java 17 does not support executors on Linux
* D) To force all builds to run on Windows agents


4. **Which file path stores all Jenkins configurations, plugins, jobs, and secrets by default on Linux?**
* A) `/etc/jenkins/config`
* B) `/opt/jenkins/home`
* C) `/var/lib/jenkins`
* D) `/usr/local/bin/jenkins`


5. **What is the ONLY software prerequisite required on a Linux machine to act as a Jenkins Build Agent?**
* A) Full Jenkins WAR package and Apache Tomcat
* B) A compatible Java Runtime Environment (JRE/JDK)
* C) Docker Desktop and Kubernetes
* D) MySQL Database


6. **Which protocol allows a Jenkins Agent behind a corporate NAT firewall to connect to the Controller without opening inbound SSH port 22 on the Agent?**
* A) Inbound Agent via WebSocket / JNLP
* B) FTP Passive Mode
* C) SNMP Trap
* D) Telnet


7. **A Jenkins job fails with `ERROR: No space left on device` on the Controller. Which Jenkins feature prevents historical builds from exhausting disk space?**
* A) Poll SCM
* B) Discard Old Builds (Log Rotation)
* C) Throttle Concurrent Builds
* D) Quiet Period


8. **Which Jenkins release track should be installed for enterprise production environments?**
* A) Weekly Release
* B) Nightly Alpha Snapshot
* C) LTS (Long-Term Support)
* D) Beta Release Candidate


9. **You updated 15 plugins on Jenkins and now the web UI throws a `503 Service Unavailable` error. What is the fastest CLI recovery method?**
* A) Reinstall the entire Linux operating system
* B) Rename the problematic `.jpi` file in `/var/lib/jenkins/plugins/` to `.jpi.disabled` and restart the `jenkins` systemd service
* C) Delete `/var/lib/jenkins/secrets/`
* D) Run `git reset --hard` inside `/etc/jenkins`


10. **What are Agent "Labels" used for in Jenkins?**
* A) Coloring the Jenkins UI theme
* B) Tagging agents by capability (e.g., `linux`, `docker`, `jdk17`) so pipelines run only on compatible nodes
* C) Encrypting passwords in console logs
* D) Naming GitHub branches



1. **B** — CI focuses on frequent code integration backed by automated builds and tests to catch integration bugs early.
2. **B** — `Controller` and `Agent` accurately describe orchestration vs. execution and align with modern inclusive engineering standards.
3. **B** — Running arbitrary build scripts on the Controller risks Out-Of-Memory crashes and gives build scripts direct read access to `/var/lib/jenkins/secrets/`.
4. **C** — `/var/lib/jenkins` is the default `$JENKINS_HOME` directory on Debian/Ubuntu and RHEL/CentOS installations.
5. **B** — Because `agent.jar` is a Java archive, the Agent only requires Java (JRE/JDK) plus whatever build tools (Git, Maven, Docker) your specific project needs.
6. **A** — Inbound WebSocket/JNLP agents initiate an outbound connection from the Agent to the Controller, traversing NAT/firewalls cleanly.
7. **B** — Configuring **Discard Old Builds** automatically purges old build logs and artifacts based on days or max build count.
8. **C** — LTS releases are stabilized every 12 weeks with backported security patches, making them standard for production.
9. **B** — Disabling the offending plugin binary (`.jpi.disabled`) and restarting the service allows Jenkins to boot cleanly without losing job configs.
10. **B** — Labels group agents by OS, architecture, or installed toolchains so jobs target the exact environment they need.

---

## 7. Deep-Dive Research & Homework Questions (10 Investigative Prompts)

Complete these investigations at home before **Session 2** to deepen your architectural understanding:

1. **Inspect `$JENKINS_HOME` Internals:** SSH into your Jenkins server and run `sudo ls -la /var/lib/jenkins`. Document the purpose of the `jobs/`, `nodes/`, `plugins/`, `secrets/`, and `users/` directories.
2. **Java Heap Tuning:** Inspect `/lib/systemd/system/jenkins.service`. How would you safely override `Environment="JAVA_OPTS=..."` using `sudo systemctl edit jenkins` without your changes being overwritten during an `apt upgrade`?
3. **SSH vs. Inbound WebSocket Agents:** Research the security and firewall differences between launching an agent over SSH (`ssh-slaves` plugin) versus Inbound WebSocket agents. Which is preferred in AWS VPC private subnets and why?
4. **Jenkins CLI Exploration:** Download `jenkins-cli.jar` from `http://localhost:8080/jnlpJars/jenkins-cli.jar` and test listing all installed plugins from your terminal using an API token.
5. **Master Key & Secret Encryption:** Look inside `/var/lib/jenkins/secrets/`. What is the role of `master.key` and `hudson.util.Secret`? Why should you never commit `/var/lib/jenkins/secrets/` to a public GitHub repository?
6. **Agent Workspace Cleanup:** What happens to files inside `/opt/jenkins-agent/workspace/` after a build finishes? Research the **Workspace Cleanup Plugin (`ws-cleanup`)** and why stale files cause "works on my machine" CI bugs.
7. **Jenkins Safe Restart vs. Hard Restart:** Append `/safeRestart` to your Jenkins URL (`http://localhost:8080/safeRestart`). How does Safe Restart differ from `sudo systemctl restart jenkins` when builds are actively running?
8. **Reverse Proxy Architecture:** In production, companies rarely expose port `8080` directly. Sketch how **Nginx** acts as a reverse proxy in front of Jenkins on port `443` (HTTPS) and which headers (`X-Forwarded-For`, `X-Forwarded-Proto`) Jenkins requires to avoid the *"Reverse proxy setup is broken"* warning.
9. **Blue Ocean & Pipeline Stage View:** Install the **Pipeline: Stage View** plugin and inspect what new UI metrics it adds to pipeline jobs.
10. **Preparation for Session 2:** Read the official Jenkins documentation on **Declarative Pipeline Syntax** (`pipeline`, `agent`, `stages`, `steps`, `post`) and list 3 limitations of legacy Freestyle jobs compared to a `Jenkinsfile`.

# **File:&#x20;**`01-jenkins-architecture.md`

# **SESSION 1: JENKINS ARCHITECTURE AND EXECUTION**

**Training:** Jenkins Hands-on Training for Freshers\
**Platform:** [Prepare.sh Jenkins Workspace](https://prepare.sh/workspaces/jenkins?utm_source=chatgpt.com)\
**Duration:** 50 Minutes\
**Level:** Beginner to Intermediate\
**Practical approach:** Learn → Execute → Break → Troubleshoot → Fix

## **1. Session Learning Objectives**

By the end of this session, students should be able to:

1. Understand Jenkins architecture.
2. Explain the difference between Jenkins Controller and Agent.
3. Understand Jenkins Jobs and Builds.
4. Understand Jenkins Workspace.
5. Navigate the Jenkins Dashboard.
6. Execute a Jenkins job.
7. Read Jenkins Console Output.
8. Identify successful and failed builds.
9. Understand how Jenkins executes jobs in production.
10. Explain basic Jenkins architecture during interviews.

## **2. What Is Jenkins Architecture?**

### **2.1 Simple Explanation**

Jenkins is an automation server.

It helps organizations automate repetitive software development activities.

For example, imagine a developer writes Java application code and pushes it to GitHub.

Normally, someone would need to:

1. Download the source code.
2. Compile the application.
3. Run tests.
4. Package the application.
5. Prepare it for deployment.

Jenkins can automate these activities.

Instead of performing everything manually, Jenkins executes predefined instructions.

### **2.2 Real-Life Example**

Imagine a manufacturing company.

The company has:

- One manager.
- Multiple workers.
- Different workstations.
- Different production tasks.
- A quality-checking department.

The manager distributes work to workers and monitors the results.

Jenkins works in a similar way.

| Manufacturing example   | Jenkins equivalent |
| ----------------------- | ------------------ |
| Manager                 | Jenkins Controller |
| Workers                 | Jenkins Agents     |
| Work assignment         | Jenkins Job        |
| Production activity     | Jenkins Build      |
| Production instructions | Jenkins Pipeline   |
| Workstation             | Jenkins Workspace  |
| Quality inspection      | Automated Testing  |
| Production report       | Console Output     |

**Remember:**

Jenkins Controller manages the automation environment. Jenkins Agents execute assigned work when configured.

In our default Prepare.sh environment, builds execute on the controller.

# **3. Understanding Jenkins Controller**

### **3.1 What is a Jenkins Controller?**

The Jenkins Controller is the central component responsible for managing Jenkins.

It manages:

- Jenkins configuration.
- User access.
- Jobs and pipelines.
- Build scheduling.
- Build history.
- Plugins.
- Credentials.
- Agent connections.
- Build execution coordination.

In a basic Jenkins environment, the controller can also execute build tasks.

### **3.2 Real-Life Example**

Consider a company with 100 developers.

Every developer pushes code to GitHub.

The Jenkins Controller manages the pipelines and coordinates build execution.

```
              DEVELOPERS
                   |
                   |
                   v
                GITHUB
                   |
                   v
          JENKINS CONTROLLER
                   |
          +--------+--------+
          |                 |
          v                 v
      Pipeline 1        Pipeline 2
          |                 |
          v                 v
       Build 1           Build 2
          |                 |
          v                 v
       Testing            Testing
```

### **3.3 Important Controller Responsibilities**

| Responsibility      | Explanation                       |
| ------------------- | --------------------------------- |
| Job Management      | Creates and manages Jenkins jobs  |
| Build Scheduling    | Decides when jobs should run      |
| Pipeline Management | Manages pipeline execution        |
| Credentials         | Stores authentication information |
| Plugin Management   | Manages Jenkins extensions        |
| User Management     | Controls access                   |
| Build History       | Maintains build records           |
| Agent Management    | Connects and manages agents       |

### **3.4 Practical: Explore Jenkins Dashboard**

**Objective:** Identify the main components of Jenkins.

**Environment:** Prepare.sh Jenkins workspace.

**Steps:**

1. Open [https://prepare.sh/workspaces/jenkins](https://prepare.sh/workspaces/jenkins?utm_source=chatgpt.com).
2. Launch your Jenkins workspace.
3. Open the Jenkins Dashboard.
4. Examine the available menus.

Look for:

- New Item
- Build History
- Manage Jenkins
- My Views
- Credentials, if available

**Student activity:**

Write down what each menu does.

| Menu           | Student explanation |
| -------------- | ------------------- |
| New Item       |                     |
| Build History  |                     |
| Manage Jenkins |                     |
| My Views       |                     |
| Credentials    |                     |

**Expected learning:** Students should understand where Jenkins jobs are created and where Jenkins configuration is managed.

# **4. Understanding Jenkins Agent**

### **4.1 What is a Jenkins Agent?**

A Jenkins Agent is a machine or execution environment that performs build tasks assigned by the Jenkins Controller.

For example, a company may have:

- One Jenkins Controller.
- Three Linux Agents.
- Two Windows Agents.
- One Docker-based Agent.

The controller coordinates the work, while agents execute the assigned tasks.

### **4.2 Real-Life Example**

Imagine a college with one principal and multiple teachers.

The principal manages the college.

Teachers conduct classes.

Similarly:

- Controller = Principal.
- Agents = Teachers.
- Build tasks = Classes.

### **4.3 Jenkins Controller and Agent Architecture**

```
                 JENKINS CONTROLLER
                         |
             +-----------+-----------+
             |           |           |
             v           v           v
          Agent 1     Agent 2     Agent 3
          Linux       Windows     Linux
             |           |           |
             v           v           v
          Java App    .NET App    Python App
          Build       Build       Build
             |           |           |
             v           v           v
           Result      Result      Result
```

### **4.4 Why Do We Need Multiple Agents?**

Consider a large organization.

Different applications require different build environments.

| Application         | Required environment       |
| ------------------- | -------------------------- |
| Java application    | Linux + Java + Maven       |
| .NET application    | Windows + .NET SDK         |
| Python application  | Linux + Python             |
| Android application | Android SDK                |
| Docker application  | Docker-enabled environment |

Instead of installing everything on one machine, organizations can distribute work across agents.

### **4.5 Controller vs Agent**

| Feature                  | Controller              | Agent                                |
| ------------------------ | ----------------------- | ------------------------------------ |
| Main responsibility      | Manage Jenkins          | Execute assigned tasks               |
| Job management           | Yes                     | No central job management            |
| Build scheduling         | Yes                     | No                                   |
| Build execution          | Possible                | Yes                                  |
| Build history management | Yes                     | No central history management        |
| Workspace                | Can have one            | Has its own workspace                |
| Plugins                  | Manages Jenkins plugins | May require relevant execution tools |
| Connection               | Central component       | Connects to controller               |

### **4.6 Important Production Concept**

In production environments, organizations generally avoid running heavy builds directly on the Jenkins Controller.

Why?

Suppose 50 developers trigger builds simultaneously.

If all builds execute on the controller:

- CPU utilization may increase.
- Memory usage may increase.
- Jenkins responsiveness may decrease.
- Builds may compete for resources.
- Administration becomes difficult.

A distributed architecture allows build workloads to run on dedicated agents.

**Prepare.sh limitation:** Our default training topology uses a single controller, so students should understand the separate-agent architecture conceptually. Do not assume that separate agents are already configured.

# **5. Understanding Jenkins Jobs**

### **5.1 What is a Jenkins Job?**

A Jenkins Job is a configured task that Jenkins can execute.

Examples:

- Build a Java application.
- Run a Python script.
- Execute shell commands.
- Run automated tests.
- Build a Docker image.
- Deploy an application.

### **5.2 Real-Life Example**

Imagine you are working in a software company.

Your manager asks you to perform three activities:

1. Download application source code.
2. Build the application.
3. Run application tests.

You can configure these activities as a Jenkins Job.

Whenever the job is executed, Jenkins performs the configured tasks.

### **5.3 Different Types of Jenkins Jobs**

| Job type             | Purpose                                         |
| -------------------- | ----------------------------------------------- |
| Freestyle Project    | Configure jobs through Jenkins UI               |
| Pipeline             | Execute automation using pipeline code          |
| Multibranch Pipeline | Discover and build multiple repository branches |
| Folder               | Organize Jenkins jobs                           |
| Organization Folder  | Discover repositories within an organization    |

For this training, we will primarily focus on Pipeline jobs.

### **5.4 Job Execution Workflow**

```
        CREATE JENKINS JOB
                |
                v
        CONFIGURE JOB
                |
                v
        SAVE CONFIGURATION
                |
                v
        CLICK BUILD NOW
                |
                v
        JENKINS EXECUTES JOB
                |
                v
        BUILD COMPLETED
                |
                v
        SUCCESS / FAILURE
```

# **6. Understanding Jenkins Builds**

### **6.1 What is a Build?**

A Build represents one execution of a Jenkins Job.

For example:

You create a Jenkins Job named:

```
java-application-build
```

You execute it three times.

Jenkins creates three build records:

```
java-application-build
|
|-- Build #1
|-- Build #2
|-- Build #3
```

Each build has its own:

- Build number.
- Execution status.
- Console output.
- Build duration.
- Build details.

### **6.2 Jenkins Build Status**

| Status    | Meaning                                                            |
| --------- | ------------------------------------------------------------------ |
| SUCCESS   | All required pipeline operations completed successfully            |
| FAILURE   | An operation failed                                                |
| UNSTABLE  | Build completed but some results, such as tests, indicate problems |
| ABORTED   | Build was stopped before normal completion                         |
| NOT BUILT | Build was not executed                                             |

### **6.3 Example**

Imagine a Jenkins job that executes three operations.

```
Build #1
   |
   +---- Checkout Source Code
   |
   +---- Build Application
   |
   +---- Run Tests
   |
   v
  SUCCESS
```

Now imagine the test stage fails.

```
Build #2
   |
   +---- Checkout Source Code
   |
   +---- Build Application
   |
   +---- Run Tests
              |
              v
           FAILURE
```

Jenkins records the result of each execution.

### **6.4 Why Is Build History Important?**

In production environments, engineers investigate build history to understand:

- When did the failure start?
- Which build was successful?
- Which code change introduced the problem?
- How many builds failed?
- Did the previous build pass?

This information is useful during production troubleshooting.

# **7. Understanding Jenkins Workspace**

### **7.1 What is a Workspace?**

A Jenkins Workspace is a directory where Jenkins performs job-related operations.

For example, Jenkins may:

1. Download source code.
2. Create temporary files.
3. Execute build commands.
4. Generate application packages.
5. Store intermediate build outputs.

### **7.2 Real-Life Example**

Imagine a student performing an assignment.

The student needs a desk to keep:

- Books.
- Documents.
- Notes.
- Completed assignments.

A Jenkins Workspace is similar to that working desk.

### **7.3 Workspace Structure Example**

```
workspace/
    |
    +-- application/
    |
    +-- Jenkinsfile
    |
    +-- src/
    |
    +-- target/
    |
    +-- reports/
    |
    +-- logs/
```

This is an illustrative application workspace structure, not a guaranteed Prepare.sh directory layout.

### **7.4 Important Workspace Concepts**

| Concept         | Explanation                      |
| --------------- | -------------------------------- |
| Workspace       | Directory used for job execution |
| Source Code     | Files retrieved from Git         |
| Build Artifacts | Files generated during builds    |
| Temporary Files | Files used during execution      |
| Cleanup         | Removing unnecessary files       |

**Important:** Workspace files are not automatically a permanent backup. Students must commit required source code and Jenkinsfiles to GitHub.

# **8. Understanding Jenkins Console Output**

### **8.1 What is Console Output?**

Console Output displays the execution logs of a Jenkins build.

It helps engineers understand what happened during pipeline execution.

For example:

```
Started by user admin

[Pipeline] Start of Pipeline

[Pipeline] stage
[Pipeline] { (Build)

Building application...

[Pipeline] }

[Pipeline] End of Pipeline

Finished: SUCCESS
```

### **8.2 Why Is Console Output Important?**

Suppose your Jenkins pipeline fails.

The dashboard only shows:

```
FAILURE
```

But this does not explain the root cause.

Console Output provides the detailed execution logs.

For example:

```
ERROR: Java command not found

Finished: FAILURE
```

Now you know the issue is related to Java availability or PATH configuration.

### **8.3 Practical: Open Console Output**

1. Open Jenkins Dashboard.
2. Select an existing job.
3. Open a build number.
4. Click Console Output.
5. Read the execution logs.
6. Identify the final build result.

Students must understand that reading logs is one of the most important responsibilities of a DevOps Engineer.

# **9. Practical Exercise 1: Create Your First Jenkins Job**

### **Objective**

Create a basic Jenkins job and execute a simple message.

### **Business Scenario**

Imagine a company wants to verify that its Jenkins environment is working.

The company creates a job that prints a message.

We will implement the same exercise.

### **Prerequisites**

- Prepare.sh Jenkins workspace.
- Jenkins Dashboard access.
- Basic browser navigation.

### **Step 1: Open Jenkins Dashboard**

Open:

[https://prepare.sh/workspaces/jenkins](https://prepare.sh/workspaces/jenkins?utm_source=chatgpt.com)

Launch the workspace and access Jenkins.

### **Step 2: Create a New Job**

Follow these steps:

1. Click **New Item**.
2. Enter the job name:

```
first-jenkins-job
```

3. Select **Freestyle Project**.
4. Click OK.

### **Step 3: Configure the Job**

1. Scroll to the Build Steps section.
2. Click Add build step.
3. Select Execute shell, if available.
4. Enter the following command:

```
echo "Welcome to Jenkins Training"

echo "My first Jenkins job"

echo "Learning Jenkins step by step"
```

5\. Click Save.

### **Step 4: Execute the Job**

1. Open the job.
2. Click Build Now.
3. Wait for the build to complete.
4. Open Build History.
5. Select Build #1.
6. Click Console Output.

### **Expected Output**

```
Started by user admin

Building in workspace ...

Welcome to Jenkins Training
My first Jenkins job
Learning Jenkins step by step

Finished: SUCCESS
```

The exact user and workspace path may differ.

### **Step 5: Verify**

Check the following:

- Job is visible in Jenkins.
- Build #1 is created.
- Build status is SUCCESS.
- Console Output displays the messages.

### **Step 6: Modify the Job**

Change the command to:

```
echo "Student Name: Your Name"

echo "Course: Jenkins"

echo "Environment: Prepare.sh"

echo "Status: Learning in Progress"
```

Save and execute the job again.

Expected result:

```
Build #2
SUCCESS
```

### **Learning Outcome**

Students have successfully:

- Created a Jenkins Job.
- Configured a build step.
- Executed a job.
- Viewed build history.
- Read Console Output.

# **10. Practical Exercise 2: Understand Build Numbers**

### **Objective**

Understand how Jenkins tracks multiple executions of the same job.

### **Scenario**

A developer executes the same Jenkins job multiple times.

The DevOps Engineer must identify each execution.

### **Steps**

Use the existing job:

```
first-jenkins-job
```

Execute it three times.

After each execution:

1. Open the Jenkins job.
2. Click Build Now.
3. Wait for completion.
4. Open Build History.

### **Expected Build History**

```
first-jenkins-job

Build #1 - SUCCESS
Build #2 - SUCCESS
Build #3 - SUCCESS
```

### **Student Task**

Answer these questions:

1. Why does Jenkins create different build numbers?
2. Does Build #3 replace Build #1?
3. Where can you view the execution logs of Build #1?
4. What happens if Build #2 fails but Build #3 succeeds?

### **Expected Understanding**

Each execution receives its own build number and execution record.

A later build does not automatically overwrite the earlier build's console log.

# **11. Practical Exercise 3: Execute Linux Commands Through Jenkins**

### **Objective**

Understand how Jenkins executes shell commands.

### **Business Scenario**

A DevOps Engineer wants to verify the Jenkins execution environment.

Instead of manually logging into the terminal, the engineer wants Jenkins to execute Linux commands.

### **Step 1: Create a Job**

Create a Freestyle Project:

```
linux-system-information
```

### **Step 2: Configure Execute Shell**

Enter:

```
echo "===== SYSTEM INFORMATION ====="

whoami

echo "===== CURRENT DIRECTORY ====="

pwd

echo "===== DATE ====="

date

echo "===== HOSTNAME ====="

hostname

echo "===== DISK INFORMATION ====="

df -h

echo "===== MEMORY INFORMATION ====="

free -h
```

### **Step 3: Execute**

Click Build Now.

### **Expected Output**

The output will contain information similar to:

```
===== SYSTEM INFORMATION =====

jenkins

===== CURRENT DIRECTORY =====

/path/to/jenkins/workspace/linux-system-information

===== DATE =====

Thu Nov 27 ...

===== HOSTNAME =====

jenkins-host

===== DISK INFORMATION =====

Filesystem      Size  Used Avail Use%

===== MEMORY INFORMATION =====

Mem: ...
```

The actual username, directory, hostname and resource values depend on the workspace.

### **Step 4: Troubleshooting**

If Jenkins reports:

```
/tmp/script.sh: line 1: free: command not found
```

The command is unavailable in the execution environment.

Check whether the command exists:

```
command -v free
```

Do not assume all Linux utilities are installed.

# **12. Practical Exercise 4: Understand Jenkins Workspace**

### **Objective**

Identify the working directory used by Jenkins.

### **Step 1: Create a Job**

Job name:

```
workspace-learning
```

### **Step 2: Configure Shell Commands**

```
echo "===== WORKSPACE LOCATION ====="

pwd

echo "===== CREATE FILE ====="

echo "Jenkins workspace practical" > student.txt

echo "===== DISPLAY FILE ====="

cat student.txt

echo "===== LIST FILES ====="

ls -l
```

### **Step 3: Execute the Job**

Click Build Now.

### **Expected Output**

```
===== WORKSPACE LOCATION =====

/path/to/jenkins/workspace/workspace-learning

===== CREATE FILE =====

===== DISPLAY FILE =====

Jenkins workspace practical

===== LIST FILES =====

-rw-r--r-- ... student.txt
```

### **Step 4: Modify the Job**

Add:

```
echo "Second line added" >> student.txt

cat student.txt
```

Execute the job again.

### **Expected Output**

```
Jenkins workspace practical
Second line added
```

### **Important Learning**

The same job generally uses its own workspace across builds.

Files may remain between executions unless cleaned or overwritten.

Workspace persistence is not guaranteed across workspace resets or cleanup operations.

# **13. Break-and-Learn: Five Failure and Fix Exercises**

This section is mandatory.

Students must learn how to investigate failures rather than simply copy working commands.

## **Failure 1: Incorrect Linux Command**

### **Objective**

Understand what happens when Jenkins executes an invalid command.

**Step 1: Modify the job**

```
ech "Welcome to Jenkins"
```

**Step 2: Execute**

Click Build Now.

### **Expected Failure**

```
/tmp/script.sh: line 1: ech: command not found

Finished: FAILURE
```

### **Ask Students**

- Why did Jenkins fail?
- Is Jenkins itself broken?
- Which command caused the problem?

### **Root Cause**

The command `ech` does not exist.

### **Fix**

```
echo "Welcome to Jenkins"
```

Execute again.

Expected:

```
Finished: SUCCESS
```

## **Failure 2: Missing File**

### **Objective**

Understand file-related failures.

**Step 1: Execute**

```
cat application.txt
```

### **Expected Failure**

```
cat: application.txt: No such file or directory
```

### **Root Cause**

The requested file does not exist in the current directory.

### **Troubleshooting**

```
pwd

ls -l
```

### **Fix**

```
echo "My Jenkins Application" > application.txt

cat application.txt
```

Expected:

```
My Jenkins Application
```

## **Failure 3: Permission Denied**

### **Objective**

Understand Linux file permissions.

**Step 1: Execute**

```
touch deployment.sh

chmod 644 deployment.sh

./deployment.sh
```

### **Expected Failure**

On a typical Linux environment, the execution fails because the file does not have execute permission.

```
Permission denied
```

### **Root Cause**

The file does not have execute permission.

### **Fix**

```
chmod +x deployment.sh

./deployment.sh
```

For a meaningful test, put the following content into the script:

```
#!/bin/bash

echo "Deployment script executed"
```

Expected:

```
Deployment script executed
```

## **Failure 4: Incorrect File Path**

### **Objective**

Understand why commands fail when the path is incorrect.

**Step 1: Execute**

```
cat /wrong/location/student.txt
```

### **Expected Failure**

```
No such file or directory
```

### **Root Cause**

The file path is incorrect.

### **Troubleshooting**

```
pwd

find . -name student.txt
```

### **Fix**

Use the correct path returned by `find`.

For example:

```
cat ./student.txt
```

The exact path depends on where the file was created.

## **Failure 5: Jenkins Build Failure Through Exit Code**

### **Objective**

Understand how Linux exit codes affect Jenkins execution.

**Step 1: Execute**

```
echo "Starting build"

exit 1

echo "Build completed"
```

### **Expected Output**

```
Starting build

Finished: FAILURE
```

The final message is not printed because the shell exits at `exit 1`.

### **Root Cause**

In Linux, exit code `0` normally indicates success, while a non-zero exit code indicates failure.

### **Fix**

```
echo "Starting build"

exit 0

echo "This line will not execute"
```

Expected:

```
Starting build

Finished: SUCCESS
```

**Important:** The final echo does not execute because `exit` terminates the shell, even when its argument is `0`.

To execute both messages successfully, use:

```
echo "Starting build"

echo "Build completed"

exit 0
```

# **14. Production-Level Jenkins Architecture**

Now let's understand how Jenkins is used in a real company.

### **14.1 Small Company Architecture**

A small company may have:

- One Jenkins Controller.
- One build environment.
- GitHub repository.
- Basic CI pipeline.

```
              DEVELOPERS
                   |
                   v
                GITHUB
                   |
                   v
          JENKINS CONTROLLER
                   |
                   v
             BUILD EXECUTION
                   |
                   v
              UNIT TESTING
                   |
                   v
              BUILD RESULT
```

This is suitable for smaller environments and learning.

### **14.2 Enterprise Jenkins Architecture**

Large organizations may have multiple agents and dedicated infrastructure.

```
                  DEVELOPERS
                       |
                       v
                    GITHUB
                       |
                       v
               JENKINS CONTROLLER
                       |
          +------------+------------+
          |            |            |
          v            v            v
       LINUX        WINDOWS       DOCKER
       AGENT         AGENT        AGENT
          |            |            |
          v            v            v
       JAVA APP     .NET APP     MICROSERVICE
       BUILD        BUILD        BUILD
          |            |            |
          +------------+------------+
                       |
                       v
                 TEST AUTOMATION
                       |
                       v
                 SECURITY SCANS
                       |
                       v
                CONTAINER REGISTRY
                       |
                       v
                 DEPLOYMENT SYSTEM
```

### **14.3 Banking Production Example**

Imagine a bank developing an online banking application.

Whenever developers commit application code:

1. Source code is stored in GitHub.
2. Jenkins detects a new change through a configured trigger.
3. Jenkins checks out the source code.
4. Maven builds the Java application.
5. Unit tests execute.
6. SonarQube performs code quality analysis.
7. Security scanning tools inspect the application.
8. Docker builds the application image.
9. The image is pushed to a container registry.
10. Deployment automation deploys the application.

Example workflow:

```
Developer
    |
    v
GitHub
    |
    v
Jenkins
    |
    v
Git Checkout
    |
    v
Maven Build
    |
    v
Unit Testing
    |
    v
SonarQube
    |
    v
Security Scanning
    |
    v
Docker Build
    |
    v
Container Registry
    |
    v
Kubernetes / OpenShift
```

**Production note:** Not every organization uses Jenkins for every stage. Some responsibilities may be handled by separate tools and platforms.

# **15. Responsibilities of DevOps Engineers in Jenkins**

| Role                        | Responsibilities                                        |
| --------------------------- | ------------------------------------------------------- |
| Developer                   | Write application code and fix application defects      |
| Tester                      | Perform functional and automated testing                |
| DevOps Engineer             | Maintain CI/CD pipelines and automation                 |
| Build Engineer              | Manage application builds and artifacts                 |
| Release Engineer            | Coordinate application releases                         |
| Jenkins Administrator       | Manage Jenkins configuration, plugins, users and agents |
| Production Support Engineer | Investigate build and deployment-related incidents      |

### **Example Production Incident**

A developer reports:

"My application was building successfully yesterday. Today Jenkins is failing."

What should a DevOps Engineer investigate?

1. Open the failed Jenkins build.
2. Read Console Output.
3. Identify the failed stage.
4. Check recent code changes.
5. Check environment availability.
6. Verify dependencies.
7. Check credentials if authentication is involved.
8. Identify the root cause.
9. Fix the problem.
10. Execute the pipeline again.

This is the type of troubleshooting approach students must develop.

# **16. Student Assignments**

Do not provide the solutions immediately. Ask students to complete these independently.

## **Assignment A: Basic**

1. Create a Jenkins Freestyle job named `student-introduction`.
2. Print your name using Jenkins.
3. Print your current working directory.
4. Display the Linux hostname.
5. Execute the same job three times and identify the build numbers.

## **Assignment B: Intermediate**

1. Create a job named `linux-system-check`.
2. Display Linux operating system information.
3. Display disk utilization.
4. Display memory utilization.
5. Create a file and display its contents.
6. Modify the file during another build.
7. Investigate whether the file persists between builds.

## **Assignment C: Production Scenario**

1. Create a Jenkins job named `application-health-check`.
2. Print the application name.
3. Display the current date.
4. Verify that a required file exists.
5. Print a success message if the file exists.
6. Print an error message if the file is missing.
7. Configure the job to return an appropriate build result.

## **Assignment D: Troubleshooting**

1. Intentionally execute an invalid Linux command.
2. Execute a command against a missing file.
3. Execute a script without execute permission.
4. Use an incorrect file path.
5. Introduce a non-zero exit code and investigate the Jenkins result.

# **17. Interview Questions – Session 1**

### **Basic Questions**

**Q1. What is Jenkins?**

Jenkins is an open-source automation server used to automate software development activities such as building, testing and deploying applications.

**Q2. What is a Jenkins Controller?**

It is the central component responsible for managing Jenkins configuration, jobs, scheduling and build coordination.

**Q3. What is a Jenkins Agent?**

An agent is a machine or execution environment that performs build tasks assigned by the controller.

**Q4. What is a Jenkins Job?**

A Jenkins Job is a configured task that Jenkins executes.

**Q5. What is a Jenkins Build?**

A build is one execution of a Jenkins job.

**Q6. What is a Jenkins Workspace?**

A workspace is the directory where Jenkins performs job-related operations.

**Q7. What is Console Output?**

Console Output contains logs generated during job execution.

**Q8. What is Build History?**

Build History displays previous executions of a Jenkins job.

**Q9. Can Jenkins Controller execute builds?**

Yes. A Jenkins Controller can execute builds, although production environments commonly distribute build workloads to agents.

**Q10. Why are Jenkins Agents required?**

Agents distribute build workloads and provide different execution environments.

### **Scenario-Based Questions**

**Q11. A Jenkins build is failing. What will you check first?**

Open the failed build and examine Console Output to identify the error.

**Q12. A company has Java and .NET applications. How can Jenkins handle both?**

Configure suitable execution environments, such as Linux agents for Java and Windows agents for .NET, where required.

**Q13. Why should heavy builds not normally run on the Jenkins Controller?**

Heavy builds can consume CPU and memory resources and affect Jenkins responsiveness.

**Q14. What happens when a Jenkins job is executed multiple times?**

Jenkins creates separate build records with different build numbers.

**Q15. Why should we save Jenkinsfiles in GitHub?**

To maintain version-controlled, reusable copies of pipeline definitions independently of temporary Jenkins workspaces.

# **18. Session Completion Checklist**

Students must complete the following before moving to Session 2.

- Access Prepare.sh.
- Open Jenkins Dashboard.
- Understand Controller.
- Understand Agent.
- Understand Jenkins Job.
- Understand Jenkins Build.
- Understand Workspace.
- Create the first Jenkins Job.
- Execute Linux commands through Jenkins.
- View Build History.
- Read Console Output.
- Complete five failure-and-fix exercises.
- Complete the assignments.
- Document the learning in GitHub.

## **19. GitHub Submission**

Create the following files:

```
01-jenkins-architecture/
|
|-- README.md
|
|-- architecture.md
|
|-- assignments.md
|
|-- troubleshooting.md
|
|-- screenshots/
    |
    |-- jenkins-dashboard.png
    |-- first-jenkins-job.png
    |-- build-success.png
    |-- console-output.png
    |-- build-failure.png
    |-- build-fixed.png
```

### **Submission Requirements**

Every student must submit:

1. Jenkins Dashboard screenshot.
2. First Jenkins Job screenshot.
3. Successful build screenshot.
4. Failed build screenshot.
5. Fixed build screenshot.
6. Answers to interview questions.
7. Explanation of Controller vs Agent.
8. Troubleshooting notes.

Never upload passwords, tokens or private credentials.

# **20. Trainer Notes**

Before ending the class, ask each student these five questions:

1. What is the difference between Jenkins Controller and Agent?
2. What is the difference between a Job and a Build?
3. Where does Jenkins execute its commands?
4. How do you investigate a failed Jenkins build?
5. Why is GitHub important when using a temporary Jenkins environment?

**Trainer's final instruction:**

Do not move forward until students can create a basic Jenkins job, execute Linux commands and identify why a build has failed.

The objective is not simply to teach Jenkins terminology. Students must understand how Jenkins works through practical execution.


Topics to cover:

1. What is a Jenkinsfile?
2. Declarative vs Scripted Pipeline.
3. `pipeline` block.
4. `agent` directive.
5. `stages` and `stage`.
6. `steps`.
7. `echo` and `sh`.
8. `environment`.
9. `parameters`.
10. `post` conditions.
11. `when` conditions.
12. Five or more break-and-fix exercises.
13. Practical Jenkinsfile creation.
14. Production pipeline examples.
15. Assignments and interview questions.

**Waiting for your instruction:&#x20;**`NEXT SESSION`
