```markdown
# Jenkins Lab — Starter Session: 1 Controller + 2 SSH Agents on Killercoda

> **Lab Goal:** Launch 1 Jenkins Controller and 2 pre-built official Jenkins SSH Agents in under 5 minutes without custom `Dockerfile` builds or `docker compose` errors, then run basic Freestyle jobs on each agent.

---

## Why Previous Setups Failed & How This Fixes Them

1. **No `docker compose` dependency:** Killercoda Ubuntu sandboxes do not always ship with the `docker compose` plugin pre-installed. We use standard `docker network` and `docker run` commands only.
2. **No custom `Dockerfile` builds:** Building custom Debian/Ubuntu images with `apt-get` during a 1-hour live class wastes 10–15 minutes and risks package mirror failures (`exit code 100`). Here, we use official pre-built `jenkins/ssh-agent` images so containers start in seconds.
3. **SSH Agent over JNLP/Inbound:** Official `jenkins/ssh-agent` containers automatically configure `sshd` using a single environment variable (`JENKINS_AGENT_SSH_PUBKEY`), eliminating secret-token copy-paste mistakes.

---

## Step 1: Open Killercoda Sandbox

1. Open [Killercoda Ubuntu Playground](https://killercoda.com/playgrounds/scenario/ubuntu).
2. Wait until the `root@ubuntu:~#` prompt appears.
3. Verify Docker is running:

```bash
docker --version

```

---

## Step 2: Spin Up the Entire Cluster (Single Copy-Paste Block)

Run this block in the Killercoda terminal. It creates a dedicated bridge network, generates an SSH key pair, starts **1 Controller** (`jenkins/jenkins:lts-jdk17`), and starts **2 Agents** (`agent-1` and `agent-2` using `jenkins/ssh-agent:latest-jdk17`).

```bash
mkdir -p ~/jenkins-lab && cd ~/jenkins-lab

# 1. Create dedicated Docker bridge network
docker network create jenkins-net

# 2. Generate passwordless SSH key pair for Controller -> Agent communication
ssh-keygen -t ed25519 -f ~/jenkins-lab/agent_key -N "" -q

# 3. Start Jenkins Controller (Port 8080 exposed)
docker run -d \
  --name jenkins-controller \
  --network jenkins-net \
  -p 8080:8080 \
  -v jenkins_home:/var/jenkins_home \
  jenkins/jenkins:lts-jdk17

# 4. Start Agent 1
docker run -d \
  --name agent-1 \
  --network jenkins-net \
  -e "JENKINS_AGENT_SSH_PUBKEY=$(cat ~/jenkins-lab/agent_key.pub)" \
  jenkins/ssh-agent:latest-jdk17

# 5. Start Agent 2
docker run -d \
  --name agent-2 \
  --network jenkins-net \
  -e "JENKINS_AGENT_SSH_PUBKEY=$(cat ~/jenkins-lab/agent_key.pub)" \
  jenkins/ssh-agent:latest-jdk17

# 6. Verify all 3 containers are Up
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

```

---

## Step 3: Access Jenkins UI & Unlock Controller

1. Wait ~20 seconds for Jenkins to initialize, then print the initial admin password and private SSH key:

```bash
echo "=== INITIAL ADMIN PASSWORD ==="
docker exec jenkins-controller cat /var/jenkins_home/secrets/initialAdminPassword

echo ""
echo "=== PRIVATE SSH KEY (Copy everything including BEGIN/END lines) ==="
cat ~/jenkins-lab/agent_key

```

2. In the Killercoda top menu bar, click **Traffic / Ports** (or the hamburger menu -> **Traffic / Ports**).
3. Under **Custom Ports**, enter `8080` and click **Access** to open the Jenkins UI in a new browser tab.
4. Paste the **Initial Admin Password** -> click **Continue**.
5. Select **Install suggested plugins** (takes ~45 seconds).
6. Create your admin user (e.g., `admin` / `admin123`) -> **Save and Continue** -> **Save and Finish** -> **Start using Jenkins**.

---

## Step 4: Add the SSH Private Key Credential in Jenkins

1. Go to **Manage Jenkins** -> **Credentials** -> **System** -> **Global credentials (unrestricted)** -> **+ Add Credentials**.
2. Fill in the fields:
* **Kind:** `SSH Username with private key`
* **ID:** `jenkins-agent-ssh`
* **Description:** `SSH key for Docker agents`
* **Username:** `jenkins`
* **Private Key:** Select **Enter directly** -> click **Add** -> paste the entire output of `cat ~/jenkins-lab/agent_key`.


3. Click **Create**.

---

## Step 5: Connect Agent 1 and Agent 2

### 5A. Register `agent-1`

1. Go to **Manage Jenkins** -> **Nodes** -> **+ New Node**.
2. **Node name:** `agent-1` -> select **Permanent Agent** -> click **Create**.
3. Configure the fields:
* **Number of executors:** `2`
* **Remote root directory:** `/home/jenkins/agent`
* **Labels:** `agent-1 linux`
* **Usage:** `Only build jobs with label expressions matching this node`
* **Launch method:** `Launch agents via SSH`
* **Host:** `agent-1`
* **Credentials:** `jenkins (SSH key for Docker agents)`
* **Host Key Verification Strategy:** `Non verifying Verification Strategy`




4. Click **Save**. Click `agent-1` -> **Log** to confirm `Agent successfully connected and online`.

### 5B. Register `agent-2`

1. Go to **Manage Jenkins** -> **Nodes** -> **+ New Node**.
2. **Node name:** `agent-2` -> select **Permanent Agent** -> click **Create**.
3. Configure the fields:
* **Number of executors:** `2`
* **Remote root directory:** `/home/jenkins/agent`
* **Labels:** `agent-2 linux`
* **Usage:** `Only build jobs with label expressions matching this node`
* **Launch method:** `Launch agents via SSH`
* **Host:** `agent-2`
* **Credentials:** `jenkins (SSH key for Docker agents)`
* **Host Key Verification Strategy:** `Non verifying Verification Strategy`




4. Click **Save**. Verify both `agent-1` and `agent-2` appear online under **Build Executor Status** on the left sidebar.

*(Optional Teaching Best Practice: Go to **Manage Jenkins** -> **Nodes** -> **Built-In Node** -> **Configure** -> set **Number of executors** to `0` so the Controller never runs jobs directly.)*

---

## Step 6: Run Basic Starter Jobs on Both Agents

### Job 1: Test `agent-1`

1. On Jenkins Dashboard, click **+ New Item** -> enter `hello-agent-1` -> select **Freestyle project** -> **OK**.
2. Check **Restrict where this project can be run** -> enter `agent-1` in **Label Expression**.
3. Under **Build Steps**, click **Add build step** -> **Execute shell**:

```bash
echo "Running on Node: $NODE_NAME"
echo "Container Hostname: $(hostname)"
java -version

```

4. Click **Save** -> **Build Now** -> open **Console Output** to show students it executed inside `agent-1`.

### Job 2: Test `agent-2`

1. Click **+ New Item** -> enter `hello-agent-2` -> select **Freestyle project** -> **OK**.
2. Check **Restrict where this project can be run** -> enter `agent-2` in **Label Expression**.
3. Under **Build Steps**, click **Add build step** -> **Execute shell**:

```bash
echo "Running on Node: $NODE_NAME"
echo "Container Hostname: $(hostname)"
uname -a

```

4. Click **Save** -> **Build Now** -> open **Console Output** to verify execution on `agent-2`.

---

## Troubleshooting Quick-Reference (During Class)

| Symptom | Fix |
| --- | --- |
| **Killercoda browser tab shows 502 Bad Gateway** | Jenkins is still booting; wait 10 seconds and refresh the port `8080` tab. |
| **Agent shows offline / SSH connection refused** | Ensure `--network jenkins-net` was attached to all 3 containers (`docker network inspect jenkins-net`). |
| **Wrong private key pasted** | Run `cat ~/jenkins-lab/agent_key` again and ensure no extra spaces exist before `-----BEGIN OPENSSH PRIVATE KEY-----`. |

```

<FollowUp label="Ready to move on to Session 1 (CI Architecture, Freestyle vs Pipeline & GitHub Checkout) on this Killercoda setup?" query="Give me the GitHub-ready Markdown guide for Session 1 (CI Architecture, Freestyle vs Pipeline, and GitHub Checkout) tailored for this 1-controller + 2-agent Killercoda Docker setup."/>

<ElicitationsGroup message="How would you like to proceed with your Killercoda Jenkins labs?">
  <Elicitation label="Generate Session 1 Markdown guide for Killercoda" query="Give me the GitHub-ready Markdown guide for Session 1 (CI Architecture, Freestyle vs Pipeline, and GitHub Checkout) tailored for this 1-controller + 2-agent Killercoda Docker setup."/>
  <Elicitation label="Add a zero-UI Groovy init script to automate setup" query="Provide a single bash + Groovy init script for Killercoda that automatically skips the unlock wizard, creates the admin user, adds the SSH credential, and registers agent-1 and agent-2 without UI clicks."/>
</ElicitationsGroup>

```
