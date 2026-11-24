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

```

<FollowUp label="Ready for me to generate Session 2 (Hours 3–4): Modern Pipeline Configuration & Git Integration without time-block durations?" query="Generate Session 2 (Hours 3–4): Modern Pipeline Configuration & Git Integration in clean GitHub Markdown without time-block durations, keeping all other sections from the Master Prompt."/>

<ElicitationsGroup message="Continue your 10-hour Jenkins & GitHub curriculum:">
  <Elicitation label="Generate Session 2 (Hours 3–4) now" query="Generate Session 2 (Hours 3–4): Modern Pipeline Configuration & Git Integration in clean GitHub Markdown without time-block durations."/>
  <Elicitation label="Generate Session 3 (Hours 5–6): Secrets, Docker Agents & Triggers" query="Generate Session 3 (Hours 5–6): Enterprise Agents, Secrets Management & Build Triggers in clean GitHub Markdown without time-block durations."/>
  <Elicitation label="Generate complete solution scripts for Session 1 Mini-Project" query="Write the complete setup-controller.sh and health-check.sh scripts for the Session 1 Take-Home Mini-Project."/>
</ElicitationsGroup>

```
