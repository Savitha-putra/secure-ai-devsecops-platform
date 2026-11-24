# Enterprise Linux & Platform Engineering Guide

> **Pre-Flight System & Environment Checklist**  
> Here are the exact commands you need to run in your shell to find out your license, shell environment, identity, operating system, administrative status, and sudo privileges before starting work.

---

## Pre-Flight Checks: System, Shell & Privileges

### 1. Which GNU License / Version Am I Using?
Bash (Bourne Again SHell) and core system tools are licensed under the GNU General Public License (GPL). To check the exact version of Bash and its licensing details:
```bash
bash --version
```
*(Alternatively, check the full license text on your system via `less /usr/share/common-licenses/GPL-3` or `cat /usr/share/doc/bash/copyright` depending on your Linux distribution).*

### 2. Which Shell Am I In?
To find out your current interactive shell and its path:
```bash
echo $SHELL
```
To verify the active shell process ID and name:
```bash
ps -p $$
```

### 3. Who Am I?
To find your effective username:
```bash
whoami
```
To get your full user identity, UID, GID, and all group memberships:
```bash
id
```

### 4. Which OS Am I Working On?
To get detailed operating system distribution and kernel release information:
```bash
cat /etc/os-release
```
To check the kernel version:
```bash
uname -r
```

### 5. Am I an Admin User or Normal User?
To check if your current user ID is `0` (root/admin):
```bash
[ $(id -u) -eq 0 ] && echo "Root Admin" || echo "Normal User"
```

### 6. What All Sudo Privileges Do I Have?
To list all commands and scripts you are authorized to run via `sudo` without password prompts (or with your password):
```bash
sudo -l
```

### 7. What Privileges Do I Not Have?
To quickly test if you have root execution rights (will output an error or prompt if you lack full sudo access):
```bash
sudo -v
```
*(If `sudo -l` returns `"may not run sudo"` or `"is not in the sudoers file"`, it means you do not have administrative privilege escalation rights on this host).*

> **Note on Environment Variables:**  
> Environmental variables define the shell environment. You can create new or update existing ones to customize the shell environment:
> * `/etc/profile` defines the default environmental variables for all users.
> * `/etc/profile.d/*` files override the default environmental variables for all users.
> * `~/.bash_profile` overrides the default environmental variables for the particular user.

---

## Session 1: Linux File System Hierarchy & Text Processing

Mastering the filesystem layout and text manipulation pipelines is non-negotiable. Here are 50 production-grade commands categorized by daily operational workflows, followed by 15 hands-on mini-projects designed for LinkedIn portfolios.

### Part 1: 50 Production Commands

#### Navigation & Environment (1–10)
1. `pwd` — Print absolute path of current working directory.
2. `cd /var/log` — Switch to system log directory.
3. `cd ~` — Jump directly to the current user's home directory.
4. `cd -` — Toggle back to the previous working directory.
5. `ls -la` — List all files including hidden ones with full permissions and timestamps.
6. `ls -lh` — List files with human-readable file sizes (K, M, G).
7. `ls -lt` — Sort files by modification time (newest first).
8. `tree -L 2 /etc` — Display directory tree structure up to 2 levels deep.
9. `pushd /opt` — Push current directory onto stack and change to `/opt`.
10. `popd` — Pop directory from stack and return to previous location.

#### File & Directory Management (11–20)
11. `mkdir -p /app/config/ssl` — Create nested directories recursively without errors.
12. `touch app.env` — Create an empty file or update its timestamp.
13. `cp -v app.env app.env.bak` — Copy file with verbose output confirmation.
14. `cp -r /etc/nginx/ /opt/backup/nginx` — Recursively copy configuration directories.
15. `mv app.env.bak /tmp/` — Move or rename files and directories safely.
16. `rm -i server.log` — Prompt before deleting critical files.
17. `rm -rf /tmp/cache/*` — Force-delete temporary files recursively.
18. `ln -s /usr/bin/python3 /usr/local/bin/py` — Create a symbolic link for quick access.
19. `stat /etc/passwd` — Display detailed file metadata, inode, and access timestamps.
20. `file /bin/bash` — Determine file type (binary, text, script).

#### File Inspection & Viewing (21–30)
21. `cat /etc/os-release` — Display entire operating system release details.
22. `less /var/log/syslog` — Scroll through large log files interactively.
23. `head -n 20 /var/log/auth.log` — View the first 20 lines of an authentication log.
24. `tail -n 50 /var/log/nginx/error.log` — View the last 50 lines of an error log.
25. `tail -f /var/log/syslog` — Stream live log updates in real time.
26. `grep "ERROR" /var/log/application.log` — Search for specific error strings in logs.
27. `grep -rn "DB_HOST" /opt/app/` — Recursively search for configuration keys across codebases.
28. `wc -l /var/log/nginx/access.log` — Count total number of HTTP requests in access log.
29. `diff app.conf.old app.conf.new` — Compare two configuration files line-by-line.
30. `sort /tmp/ip_list.txt` — Sort IP addresses alphabetically.

#### Advanced Text Processing & Filtering (31–40)
31. `uniq -c /tmp/sorted_ips.txt` — Count occurrences of adjacent duplicate lines.
32. `awk '{print $1}' /var/log/nginx/access.log` — Extract the first column (client IPs) from access logs.
33. `awk -F: '{print $1, $3}' /etc/passwd` — Extract usernames and UIDs using custom delimiter `:` in files.
34. `sed 's/localhost/127.0.0.1/g' config.json` — Replace strings inline or in-stream across files.
35. `sed -i 's/DEBUG=true/DEBUG=false/g' .env` — Modify configuration files directly in-place.
36. `cut -d',' -f1,3 users.csv` — Extract specific comma-separated CSV columns.
37. `tr '[:lower:]' '[:upper:]' < input.txt` — Convert text case from lowercase to uppercase.
38. `paste file1.txt file2.txt` — Merge files side-by-side horizontally.
39. `comm -12 file1.txt file2.txt` — Compare sorted files and show common lines.
40. `rev /tmp/tokens.txt` — Reverse character order on every line.

#### Compression, Archiving & Transfer (41–50)
41. `tar -czvf app_backup.tar.gz /opt/app` — Create a compressed gzip tarball archive.
42. `tar -xzvf app_backup.tar.gz -C /var/www/` — Extract a tarball to a specific directory.
43. `zip -r web_assets.zip /var/www/html` — Create a zip archive.
44. `unzip web_assets.zip -d /var/www/extracted/` — Extract a zip archive.
45. `gzip /var/log/old_app.log` — Compress a single file into `.gz` format.
46. `gunzip /var/log/old_app.log.gz` — Decompress a gzipped file.
47. `find /var/log -type f -name "*.log" -mtime +30` — Find log files older than 30 days.
48. `find /opt/app -name "*.py" -exec wc -l {} +` — Find Python files and count total lines of code.
49. `locate nginx.conf` — Quickly locate files using system prebuilt index database.
50. `xargs -a /tmp/error_pids.txt kill -9` — Build and execute command lines from standard input data.

### Part 2: 15 Mini-Projects for Students (LinkedIn Ready)
1. **Production Log Parser:** Write a pipeline combining `grep`, `awk`, `sort`, and `uniq` to output the top 10 unique IP addresses generating HTTP 403 errors from an Nginx log.
2. **Disk Space Audit Script:** Use `find`, `du`, and `sort` to generate a formatted report of the top 5 largest directories under `/var` exceeding 100MB.
3. **Automated Log Rotator & Archiver:** Build a command sequence that finds `.log` files older than 7 days in `/tmp/logs`, compresses them into a tarball stamped with the current date, and deletes the originals.
4. **Environment File Sanitizer:** Use `sed` to automatically strip all commented lines (`#`) and empty lines from a production `.env` file for auditing.
5. **CSV User Migration Report:** Use `awk` and `cut` to parse `/etc/passwd` and generate a clean report showing usernames and shell types for non-system accounts (`UID >= 1000`).
6. **Config Drift Checker:** Use `diff` and exit codes to compare a live production config (`/etc/ssh/sshd_config`) against a git-backed baseline template, outputting differences to a review file.
7. **Broken Symlink Hunter:** Use `find` with `-xtype l` to locate and report all broken symbolic links across `/usr/local/bin`.
8. **Secure Credential Redactor:** Use `sed` to mask API keys (`sk_live_...`) in application logs before sharing them with developers for debugging.
9. **Multi-File Word & Line Counter:** Combine `find`, `xargs`, and `wc` to calculate the total code line count across all Python files in a microservice repository.
10. **IP Address Extractor & Validator:** Use `grep` with extended regex (`-E`) to extract all valid IPv4 addresses from a firewall audit log.
11. **Temp File Cleaner Daemon One-Liner:** Construct a `find` command that targets files in `/tmp` accessed over 14 days ago and safely unlinks them.
12. **Database Backup Verifier:** Create a tarball of a local SQLite database directory, verify its structural integrity, and check compressed size ratios.
13. **User Access Matrix Generator:** Combine `cut`, `sort`, and `join` to map system usernames from `/etc/passwd` to their primary group names from `/etc/group`.
14. **CI/CD Build Artifact Packer:** Use `tar` with exclude flags (`--exclude='*.log' --exclude='node_modules'`) to bundle source code for deployment.
15. **System Inventory Snapshotter:** Create a diagnostic command pipeline capturing kernel release, OS version, disk mounts, and memory stats into an organized timestamped summary file.

---

## Session 2: System Performance & Process Troubleshooting

When production alerts fire for high CPU, memory exhaustion, disk I/O bottlenecks, or hung processes, platform engineers must isolate root causes within minutes. Here are 50 production-grade system performance and troubleshooting commands categorized by operational workflow, followed by 15 hands-on mini-projects for student portfolios.

### Part 1: 50 Production Commands

#### Process Management & Monitoring (1–12)
1. `ps aux` — List all running processes with detailed attributes (`USER`, `PID`, `%CPU`, `%MEM`).
2. `ps -ef` — Display full-format process listing including parent PIDs (`PPID`) and start times.
3. `top` — Launch interactive real-time view of system processes and resource consumption.
4. `htop` — Enhanced, color-coded interactive process and resource viewer with mouse support.
5. `ps aux --sort=-%cpu` — Sort all system processes by CPU utilization in descending order.
6. `ps aux --sort=-%mem` — Sort all system processes by memory utilization in descending order.
7. `pgrep -u nginx` — Look up process IDs belonging to a specific user or service account.
8. `pidof nginx` — Return the exact PID of a running daemon process.
9. `kill <PID>` — Send default `SIGTERM` signal to terminate a process gracefully.
10. `kill -9 <PID>` — Send `SIGKILL` signal for forceful, immediate process termination.
11. `pkill -f node` — Terminate all processes matching a specific command pattern string.
12. `killall nginx` — Kill all running processes matching the exact daemon name.

#### System Load, CPU & Kernel (13–22)
13. `uptime` — Display system runtime and 1, 5, and 15-minute load averages.
14. `w` — Show who is logged in and what load averages their user sessions are generating.
15. `vmstat 1 10` — Report virtual memory, CPU activity, and block I/O every 1 second for 10 iterations.
16. `mpstat -P ALL 1` — Display granular per-CPU core utilization statistics.
17. `sar -u 1 5` — Collect and report CPU utilization via system activity reporter.
18. `lscpu` — Display detailed CPU architecture, physical cores, threads, and cache specs.
19. `uname -r` — Print active Linux kernel release version.
20. `sysctl -a` — View all active tunable kernel parameters.
21. `cat /proc/cpuinfo` — Inspect raw CPU hardware flags, family, and model details.
22. `taskset -c 0,1 -p <PID>` — Bind or check process affinity to specific CPU cores.

#### Memory & Swap Management (23–32)
23. `free -h` — Display total, used, and free system memory in human-readable units (M/G).
24. `vmstat -s` — Display a comprehensive summary table of virtual memory statistics.
25. `cat /proc/meminfo` — Inspect granular kernel memory allocation details and buffers.
26. `swapon --show` — List active swap partitions, swap files, sizes, and priorities.
27. `sudo swapon -a` — Enable all swap areas defined in `/etc/fstab`.
28. `sudo swapoff /swapfile` — Disable a specific swap file safely without data loss.
29. `cat /proc/sys/vm/swappiness` — Check kernel swappiness preference value (tendency to use swap).
30. `smem -r` — Report Proportional Set Size (PSS) memory usage per process.
31. `oom_score_adj` — Adjust kernel Out-Of-Memory killer score for a critical service process.
32. `slabtop` — View kernel slab cache memory allocations in real time.

#### Disk Space, I/O & Inodes (33–42)
33. `df -h` — Report filesystem disk space usage in human-readable format.
34. `df -i` — Report inode usage and availability across all mounted filesystems.
35. `du -sh /var/log/*` — Summarize disk space consumed by individual files and directories.
36. `iostat -xz 1 5` — Report extended CPU and disk I/O throughput, await times, and utilization.
37. `iotop -o` — Display active processes performing heavy disk I/O operations.
38. `blkid` — Print block device UUIDs and filesystem types.
39. `lsblk -f` — List block devices with filesystem labels, UUIDs, and mount points.
40. `tune2fs -l /dev/sda1` — Inspect ext4 filesystem superblocks and tuning parameters.
41. `fuser -m /mnt/data` — Identify processes currently accessing a specific mount point.
42. `sync` — Flush dirty file system buffers from memory to persistent disk storage.

#### Process Open Files, Sockets & Debugging (43–50)
43. `lsof -i :80` — List processes listening on or connected to TCP port 80.
44. `lsof -u jim` — List all open files and network descriptors owned by user `jim`.
45. `strace -p <PID>` — Trace system calls and signals executed by a running process in real time.
46. `ltrace -p <PID>` — Trace dynamic library calls made by a running application process.
47. `perf top` — Interactive system profiling tool for performance analysis of live kernels.
48. `dmesg -T` — Print kernel ring buffer messages with human-readable timestamps.
49. `journalctl -k -b 0` — View kernel boot logs and hardware errors for the current boot session.
50. `ulimit -a` — Display current resource limits (open file descriptors, stack size) for the shell.

### Part 2: 15 Mini-Projects for Students (LinkedIn Ready)
1. **High CPU Process Isolation:** Identify and terminate a runaway background worker process consuming 99% CPU without impacting other services.
2. **Memory Leak Detector Script:** Track memory consumption trends of an application over 1 hour using `ps` and `awk`, outputting growth anomalies.
3. **Swap Pressure Auditor:** Evaluate system swappiness and swap usage metrics to determine if a production server requires RAM upgrades.
4. **Inode Exhaustion Finder:** Build a script using `find` and `df -i` to locate directories containing millions of tiny hidden files filling up inode tables.
5. **Zombie Process Killer:** Write a bash script that detects defunct (`Z`) processes and safely cleans up their parent processes.
6. **Disk I/O Bottleneck Analyzer:** Use `iostat` and `iotop` to identify which database or logging process is saturating disk write throughput.
7. **Port Conflict Resolver:** Use `lsof` and `ss` to detect a port collision on port 443 and terminate the conflicting rogue service.
8. **System Load Watchdog:** Create a cron-driven bash script that logs high load averages (`> 4.0`) alongside top CPU processes to `/var/log/load_alerts.log`.
9. **Kernel OOM Post-Mortem Tool:** Parse `/var/log/messages` or `dmesg` to extract Out-Of-Memory (OOM) killer events and identify the terminated process.
10. **File Descriptor Leak Tracer:** Use `lsof` to monitor a service leaking open file descriptors over time and alert when limits near 80%.
11. **Process CPU Affinity Tuner:** Bind an intensive batch processing script to dedicated CPU cores using `taskset` to protect web server responsiveness.
12. **Slab Memory Inspector:** Audit kernel slab allocations to diagnose kernel memory fragmentation issues on heavily loaded database nodes.
13. **Open Files Limit Extractor:** Audit all running system daemons to verify which services are approaching their maximum open file descriptor limits (`nofile`).
14. **System Health Snapshot Script:** Combine `uptime`, `free`, `df`, and `vmstat` into a single comprehensive JSON system health report.
15. **System Call Profiler:** Use `strace` to capture and analyze why a hanging web server process is stuck waiting on a socket read call.

---

## Session 3: User Management, SSH & Access Control

Managing least-privilege user access, hardening secure shell connections, and configuring file permissions are critical for security compliance and production stability. Here are 50 production-grade user management, SSH, and access control commands categorized by operational workflow, followed by 15 hands-on mini-projects for student portfolios.

### Part 1: 50 Production Commands

#### User & Group Management (1–12)
1. `sudo useradd -m -s /bin/bash -u 1833 jim` — Create a user with a specific UID, home directory, and default shell.
2. `sudo useradd -M -s /sbin/nologin app_svc` — Create a system service account without a home directory and no interactive login shell.
3. `sudo passwd jim` — Change or set the password for user `jim`.
4. `sudo passwd -l jim` — Lock a user account to prevent password-based logins.
5. `sudo passwd -u jim` — Unlock a locked user account.
6. `sudo usermod -aG nautilus_noc kano` — Append a user to a supplementary group safely.
7. `sudo userdel -r jim` — Delete a user account and remove their home directory and mail spool.
8. `sudo groupadd nautilus_noc` — Create a new system group.
9. `sudo groupdel nautilus_noc` — Delete an existing system group.
10. `id kano` — Display UID, GID, and group memberships for user `kano`.
11. `groups kano` — Print all groups associated with user `kano`.
12. `chage -l jim` — View password aging, expiration dates, and maximum validity policies for a user.

#### Identity, Auditing & Password Policies (13–22)
13. `whoami` — Print the username of the currently logged-in user.
14. `who` — List all users currently logged into the system.
15. `w` — Show who is logged in and what commands they are executing.
16. `last` — Display a history log of recent user logins and reboots.
17. `lastlog` — Report the last login timestamp for all system users.
18. `sudo chage -M 90 jim` — Enforce a 90-day password expiration policy for a user.
19. `sudo chage -d 0 jim` — Force a user to change their password on their next login.
20. `cat /etc/passwd` — Inspect system user accounts, UIDs, default shells, and home directories.
21. `cat /etc/group` — View all system groups and their member accounts.
22. `cat /etc/shadow` — Inspect encrypted user password hashes and aging parameters (requires root).

#### Sudoers & Privilege Escalation (23–32)
23. `sudo -i` — Switch to the root user shell session with root environment variables.
24. `sudo su -` — Alternative command to switch to an interactive root shell.
25. `sudo -u postgres psql` — Execute a command or shell session as another specific user.
26. `sudo visudo` — Safely edit the `/etc/sudoers` configuration file with syntax checking.
27. `sudo -l` — List allowed sudo privileges and commands for the current user.
28. `sudo visudo -c` — Check the syntax of `/etc/sudoers` for configuration errors.
29. `cat /etc/sudoers.d/nautilus` — Inspect modular sudo privilege configuration files.
30. `sudo groupmems -g nautilus_noc -l` — List members belonging to a specific group.
31. `su - kano` — Switch user session to `kano` (requires password).
32. `sudo -k` — Invalidate cached sudo credentials immediately.

#### File Permissions, Ownership & ACLs (33–42)
33. `chmod 755 /var/www/jim` — Set read, write, execute for owner and read, execute for group/others.
34. `chmod -R 644 /var/www/html/*` — Recursively set files to read-write for owner, read-only for others.
35. `chmod u+x deploy.sh` — Add executable permission for the file owner.
36. `chown -R jim:nautilus_noc /var/www/jim` — Recursively change file owner and group.
37. `chgrp nautilus_noc /opt/app` — Change the group ownership of a file or directory.
38. `umask 022` — Set default file permission mask for newly created files (755 for dirs, 644 for files).
39. `setfacl -m u:kano:rwx /shared/data` — Assign specific Access Control List (ACL) permissions to a user.
40. `getfacl /shared/data` — View granular Access Control List permissions on a file or directory.
41. `chmod +s /usr/bin/passwd` — Set the SUID bit on an executable file to run with owner privileges.
42. `lsattr /etc/passwd` — View immutable or special file system attributes.

#### SSH Key Management & Hardening (43–50)
43. `ssh-keygen -t rsa -b 4096 -C "admin@fusion.com"` — Generate a secure 4096-bit RSA SSH key pair.
44. `ssh-copy-id -i ~/.ssh/id_rsa.pub kano@app01` — Copy public key to a remote server for passwordless login.
45. `ssh -i ~/.ssh/id_rsa kano@app01` — Connect to a remote server using a specific private key file.
46. `ssh-add ~/.ssh/id_rsa` — Add private key identity to the SSH authentication agent.
47. `ssh-add -l` — List currently loaded SSH keys in the `ssh-agent`.
48. `sudo sshd -t` — Test SSH daemon configuration file for syntax errors before restarting.
49. `sudo systemctl restart sshd` — Restart the SSH daemon service to apply security changes.
50. `ssh -v -i ~/.ssh/id_rsa kano@app01` — Enable verbose debugging mode for troubleshooting SSH connection failures.

### Part 2: 15 Mini-Projects for Students (LinkedIn Ready)
1. **Least-Privilege Service Account Creator:** Write a script that provisions an isolated application user with `/sbin/nologin`, custom UID, and strict home directory permissions.
2. **Password Aging Audit Reporter:** Build a bash script that parses `/etc/shadow` and reports any user accounts with missing expiration policies.
3. **Sudoers Compliance Validator:** Create an automated script using `visudo -c` and file permissions checks to verify `/etc/sudoers` security posture.
4. **SSH Hardening Enforcer:** Write a script that updates `/etc/ssh/sshd_config` to disable root login and password authentication, enforcing key-only access.
5. **Group Access Matrix Generator:** Combine `cat /etc/passwd` and `getent group` to generate a CSV report mapping all users to their primary and secondary groups.
6. **Locked Account Cleaner:** Build a tool that identifies locked user accounts (`passwd -S`) inactive for over 90 days and archives their home directories.
7. **Advanced ACL Shared Workspace:** Configure a multi-user collaborative directory `/var/shared` using `setfacl` so group members automatically inherit write permissions.
8. **Automated SSH Key Distributor:** Write a bash loop that reads a list of server IPs and distributes a deployment engineer's public key securely.
9. **File Permission Drift Detector:** Create a baseline snapshot of critical file permissions (`/etc/passwd`, `/etc/shadow`, `/etc/sudoers`) and flag any unauthorized modifications.
10. **SUID/SGID Binary Auditor:** Use `find` with `-perm /6000` to locate all SUID/SGID binaries on the system and output an audit security report.
11. **SSH Agent Forwarding Tunnel:** Configure and test secure SSH agent forwarding across jump hosts to access internal staging databases.
12. **Interactive Shell Restrictor:** Provision a restricted shell environment (`rbash`) for third-party vendors with locked directory traversal limits.
13. **SSH Banner & Timeout Hardener:** Configure idle client timeout intervals and custom security warning banners in `sshd_config`.
14. **Directory Immutable Locker:** Use `chattr +i` to lock critical configuration files against accidental deletion or modification by standard users.
15. **User Onboarding Automation Pipeline:** Write a complete bash automation script that creates a user, assigns groups, generates an SSH key pair, and sets up authorized keys.

---

## Session 4: Service Management, Package Management & Log Debugging

Modern enterprise workloads rely on `systemd` to manage background daemons, package managers for software lifecycles, and persistent journaling for troubleshooting. Here are 50 production-grade commands categorized by operational workflow, followed by 15 hands-on mini-projects for student portfolios.

### Part 1: 50 Production Commands

#### systemd Service & Unit Control (1–12)
1. `sudo systemctl start nginx` — Start a background service immediately.
2. `sudo systemctl stop nginx` — Stop a running service safely.
3. `sudo systemctl restart nginx` — Restart a service (stop then start).
4. `sudo systemctl reload nginx` — Reload configuration files without dropping active connections.
5. `sudo systemctl status nginx` — Check current service state, PID, and recent log snippets.
6. `sudo systemctl enable nginx` — Configure a service to start automatically on system boot.
7. `sudo systemctl disable nginx` — Remove service symlinks to prevent automatic startup on boot.
8. `sudo systemctl enable --now nginx` — Enable and start a service in a single command.
9. `systemctl is-active nginx` — Check if a service is currently running (returns exit code).
10. `systemctl is-enabled nginx` — Verify if a service is enabled to start on boot.
11. `sudo systemctl daemon-reload` — Reload systemd manager configuration after modifying service unit files.
12. `systemctl list-units --type=service --state=failed` — List all failed system services needing attention.

#### Journal Logging & Diagnostics (13–24)
13. `journalctl -u nginx.service` — View all persistent journal logs associated with a specific service.
14. `journalctl -u nginx.service -e` — Jump directly to the end of the service log stream.
15. `journalctl -f` — Stream live system journal log entries in real time.
16. `journalctl --since "1 hour ago"` — Filter journal entries starting from a specific time window.
17. `journalctl -p err -b 0` — Show error-priority (`err`) logs for the current boot session.
18. `journalctl --disk-usage` — Display total disk space consumed by system journal logs.
19. `sudo journalctl --vacuum-time=7d` — Purge journal logs older than 7 days to free up disk space.
20. `sudo journalctl --vacuum-size=500M` — Limit journal log storage to a maximum size of 500 MB.
21. `cat /var/log/syslog` — Inspect legacy flat-file system event logs (Debian/Ubuntu).
22. `cat /var/log/messages` — Inspect general system and kernel logs (RHEL/CentOS).
23. `tail -n 100 /var/log/auth.log` — View recent authentication attempts and sudo executions.
24. `dmesg --level=err` — Print hardware and kernel error messages from the ring buffer.

#### Package Management: APT (Debian/Ubuntu) (25–37)
25. `sudo apt update` — Synchronize local package index files with remote repositories.
26. `sudo apt upgrade -y` — Upgrade all installed packages to their latest available versions.
27. `sudo apt install nginx -y` — Install a new software package non-interactively.
28. `sudo apt remove nginx` — Remove a software package while retaining configuration files.
29. `sudo apt purge nginx` — Completely remove a package and all associated configuration files.
30. `sudo apt autoremove -y` — Remove orphaned dependency packages no longer required by any application.
31. `apt-cache search postgresql` — Search available software repositories for matching package names.
32. `dpkg -l | grep nginx` — List installed Debian packages matching a specific keyword.
33. `dpkg -i package.deb` — Manually install a downloaded local `.deb` package file.
34. `dpkg -L nginx` — List all files installed on the system by a specific package.
35. `dpkg -S /usr/sbin/nginx` — Identify which installed package owns a specific file path.
36. `sudo apt-mark hold nginx` — Prevent a specific package from being upgraded during system updates.
37. `sudo apt clean` — Clear local package retrieval cache to reclaim disk space.

#### Package Management: YUM / DNF (RHEL/CentOS) (38–44)
38. `sudo dnf check-update` — Check for available software package updates.
39. `sudo dnf upgrade -y` — Upgrade all system packages to latest versions.
40. `sudo dnf install httpd -y` — Install a new package using the DNF package manager.
41. `sudo dnf remove httpd` — Remove an installed RPM package.
42. `dnf history` — View transactional history of package installations and removals.
43. `rpm -qa | grep httpd` — Query all installed RPM packages matching a keyword.
44. `rpm -ql httpd` — List all files installed by a specific RPM package.

#### System Targets, Boot States & Kernel Modules (45–50)
45. `systemctl get-default` — Print the current default system startup target (e.g., `multi-user.target`).
46. `sudo systemctl set-default multi-user.target` — Set default boot target to non-graphical server mode.
47. `sudo systemctl rescue` — Switch system into rescue mode for emergency single-user maintenance.
48. `lsmod` — List currently loaded Linux kernel modules and drivers.
49. `sudo modprobe overlay` — Load a specific kernel module dynamically into memory.
50. `sysctl --system` — Reload all kernel configuration parameters from `/etc/sysctl.d/`.

### Part 2: 15 Mini-Projects for Students (LinkedIn Ready)
1. **Custom Systemd Service Creator:** Write a custom systemd unit file (`/etc/systemd/system/myapp.service`) to run a Python background script with automatic restart policies.
2. **Failed Service Health Watchdog:** Build a bash script that checks for failed systemd units using `systemctl` and triggers an alert notification.
3. **Journal Log Rotator & Purger:** Create an automated script that evaluates journal disk usage and vacuums logs older than 14 days.
4. **Debian Package Audit Reporter:** Build a tool that lists all installed packages, flags packages on hold, and outputs a CSV system inventory.
5. **Orphaned Package Cleaner:** Use `apt autoremove` and package dependency checks to clean up unused library clutter on a test server.
6. **Kernel Module Inspector:** Write a script that checks if required security modules (`overlay`, `br_netfilter`) are loaded for Kubernetes prerequisites.
7. **Transactional Package Rollback:** Use `dnf history` to identify a faulty package update and execute a clean transactional rollback.
8. **Startup Target Auditor:** Inspect current runlevels and systemd targets to ensure production servers boot into headless multi-user mode.
9. **Service Crash Post-Mortem Tool:** Parse persistent journal logs using `journalctl -u` to extract the exact stack trace and exit code of a crashed service.
10. **Automated Security Updater:** Write a cron-driven script that performs safe package updates (`apt upgrade --security`) for critical security patches.
11. **Package File Ownership Finder:** Use `dpkg -S` and `rpm -qf` to build a utility that identifies package ownership for any arbitrary file on disk.
12. **Systemd Dependency Visualizer:** Use `systemctl list-dependencies` to map out initialization order and identify blocking service bottlenecks.
13. **Local Repository Mirror Cache Cleaner:** Automate the cleanup of local package caches (`apt clean` / `dnf clean all`) across multiple staging servers.
14. **Service Health Check API Wrapper:** Write a bash script combining `systemctl is-active` and `curl` to report service health status to a monitoring endpoint.
15. **Boot Performance Profiler:** Use `systemd-analyze blame` to identify which system services are slowing down server boot times.

---

## Session 5: Networking, Storage & Essential Bash Scripting

Platform engineers constantly interact with network sockets, DNS resolution, block storage volumes, and bash automation scripts. Here are 50 production-grade commands categorized by operational workflow, followed by 15 hands-on mini-projects for student portfolios.

### Part 1: 50 Production Commands

#### Networking & Diagnostic Tools (1–12)
1. `ip a` — Display all network interfaces, IP addresses, and MAC addresses.
2. `ip route` — View or modify the kernel routing table and default gateways.
3. `ss -tulpn` — List all listening TCP and UDP sockets with associated PIDs.
4. `netstat -anp` — Inspect legacy network socket connections and listening ports.
5. `curl -I https://api.fusion.com` — Fetch HTTP response headers from a web server endpoint.
6. `wget https://releases.fusion.com/app.tar.gz` — Download files from the web via HTTP/HTTPS.
7. `dig fusion.com` — Query DNS servers for domain records with detailed diagnostic output.
8. `nslookup fusion.com` — Query domain name resolution records interactively.
9. `nc -zv 192.168.1.50 5432` — Test TCP network connectivity to a specific host and port.
10. `ping -c 4 8.8.8.8` — Test ICMP network latency and packet loss to a target IP.
11. `traceroute google.com` — Trace the network packet path and hops to a destination.
12. `iptables -L -v -n` — List active firewall rules and packet counters.

#### Storage, Disks & Filesystems (13–24)
13. `lsblk` — List all available block storage devices and their partition hierarchy.
14. `fdisk -l` — Display disk partition tables for all attached storage drives.
15. `df -Th` — Report mounted filesystem types and disk space utilization.
16. `mount /dev/sdb1 /mnt/data` — Mount a block storage partition to a directory mount point.
17. `umount /mnt/data` — Safely unmount an attached filesystem.
18. `blkid` — Print block device UUIDs and filesystem formats.
19. `parted /dev/sda print` — View partition table and disk label type (GPT/MBR).
20. `mkfs.ext4 /dev/sdb1` — Format a block storage partition with the ext4 filesystem.
21. `tune2fs -c 30 /dev/sdb1` — Set filesystem check mount-count interval.
22. `cat /etc/fstab` — Inspect persistent filesystem mount configurations for system boot.
23. `du -sh /var/lib/docker` — Measure exact disk space consumed by a directory.
24. `dd if=/dev/zero of=/tmp/test.img bs=1M count=100` — Generate benchmark test files for I/O testing.

#### Essential Bash Scripting & Automation (25–38)
25. `#!/bin/bash` — Standard shebang header defining the bash interpreter for scripts.
26. `echo "Deployment started"` — Print text output to standard output (`stdout`).
27. `read -p "Enter username: " USERNAME` — Prompt user for interactive input and store in variable.
28. `if [ "$UID" -eq 0 ]; then ... fi` — Conditional statement checking if script is run as root.
29. `for server in app01 app02 app03; do echo $server; done` — Iterate through a list using a `for` loop.
30. `while true; do sleep 5; done` — Create an infinite polling loop with a 5-second delay.
31. `case "$1" in start) ... ;; stop) ... ;; esac` — Handle command-line service arguments cleanly.
32. `exit 0` — Terminate script execution successfully with exit code `0`.
33. `trap "echo 'Error occurred'; exit 1" ERR` — Catch script errors and execute cleanup routines.
34. `[[ -f /etc/passwd ]] && echo "Exists"` — Test if a file exists using advanced bash test operators.
35. `ARRAY=("nginx" "redis" "postgres")` — Declare a bash array variable.
36. `echo ${ARRAY[@]}` — Print all elements stored within a bash array.
37. `func_deploy() { echo "Deploying $1"; }` — Define a reusable bash function taking arguments.
38. `printf "%-10s %-10s\n" "USER" "UID"` — Format text output into structured columns.

#### Cron, Automation & System Maintenance (39–50)
39. `crontab -e` — Edit scheduled cron jobs for the current user account.
40. `crontab -l` — List all active scheduled cron jobs.
41. `sudo tail -n 50 /var/log/syslog | grep CRON` — Audit executed cron job logs.
42. `at now + 1 hour` — Schedule a one-time command execution in the future.
43. `export PATH=$PATH:/opt/bin` — Export environment variables in a shell session.
44. `source ~/.bashrc` — Reload shell configuration profile immediately.
45. `history` — Display previously executed shell command history.
46. `alias ll='ls -la'` — Create a custom command shortcut alias.
47. `timedatectl set-timezone Asia/Kolkata` — Configure system timezone settings.
48. `ntpdate pool.ntp.org` — Synchronize system clock with network time servers.
49. `logger "Deployment completed successfully"` — Write custom messages to the system syslog.
50. `nohup ./long_script.sh &` — Run a script in the background immune to terminal closure signals.

### Part 2: 15 Mini-Projects for Students (LinkedIn Ready)
1. **Multi-Server Port Availability Checker:** Write a bash script that iterates over a list of host IPs and ports using `nc` to verify network reachability.
2. **Automated EBS Volume Mounter:** Create a script that checks for unmounted block storage devices (`lsblk`), formats them, and updates `/etc/fstab`.
3. **Network Latency & Packet Loss Monitor:** Build a bash automation script that pings core gateways every minute and logs packet loss incidents.
4. **Interactive Linux User Provisioner:** Write a script that prompts for a username, creates the account with a custom UID, generates an SSH key pair, and assigns groups.
5. **Disk Space Emergency Alert Daemon:** Construct a cron-driven script that checks root partition usage and triggers an alert if usage exceeds 85%.
6. **DNS Resolution Health Auditor:** Use `dig` in a bash loop to check record propagation across public DNS resolvers (`8.8.8.8`, `1.1.1.1`).
7. **Automated Database Backup Archiver:** Write a script that dumps a database, compresses it with `tar -czvf`, and uploads it to remote storage.
8. **Cron Job Audit Reporter:** Build a script that parses all user crontabs across the system and generates a security compliance report.
9. **Firewall Rule Backup & Verifier:** Create a script that exports active `iptables` rules and verifies their integrity against unauthorized changes.
10. **System NTP Clock Drift Checker:** Write a script that monitors system time synchronization status and alerts if offset exceeds thresholds.
11. **Log File Rotation & Compression Tool:** Build a custom bash log rotator that compresses logs older than 7 days and moves them to archive storage.
12. **Service Port Health Check Wrapper:** Combine `ss` and `curl` to verify that all expected application ports are actively listening and responding.
13. **Batch File Renamer Utility:** Write a script that accepts file extensions and renames batches of configuration files with date stamps.
14. **System Environment Audit Snapshotter:** Create a script capturing active environment variables, network routes, disk mounts, and memory stats into an audit report.
15. **End-to-End DevOps Health Check Dashboard:** Combine networking, storage, and service checks into a single comprehensive health script outputting formatted status tables.

---

## Enterprise Linux Platform Engineering Capstone Project

* **Project Codename:** Project Nexus (Production Infrastructure Automation)
* **Target Audience:** Freshers & Junior Platform Engineers
* **Prerequisites:** Completion of Sessions 1 through 5 (Filesystem, Processes, Access Control, Services, Networking & Bash)

### Executive Summary & Business Objective
As a Junior Platform Engineer at **xFusionCorp Industries**, your team has been tasked with deploying, securing, hardening, and monitoring a microservice web application across three application servers (`app01`, `app02`, `app03`).

This capstone project simulates a real-world enterprise deployment. You will transition from manual configuration to writing an idempotent, end-to-end Bash automation pipeline that incorporates file hierarchy standards, process auditing, least-privilege security, systemd service management, and network storage configuration.

### Lab Architecture & Topology
```text
[Management Node / Bastion]
       │
       ├──────(SSH Key Auth)──────► [App Server 1 (app01)]
       ├──────(SSH Key Auth)──────► [App Server 2 (app02)]
       └──────(SSH Key Auth)──────► [App Server 3 (app03)]
```

### Project Requirements & Rubric
Your automation script and manual validation must satisfy the following 5 engineering milestones, directly corresponding to your 5 training sessions:

* **Milestone 1: Filesystem & Log Architecture (Session 1)**
  * Create a standardized directory structure on all app servers:
    * `/opt/nexus/app` (Application source code)
    * `/opt/nexus/config` (Configuration files)
    * `/var/log/nexus` (Persistent application logs)
  * Implement a log rotation and archiving function using `tar`, `find`, and `gzip` that compresses logs older than 7 days.
* **Milestone 2: Process & Resource Health Auditing (Session 2)**
  * Write a process monitoring check into your script that inspects CPU and memory utilization.
  * If load average exceeds `3.0` or memory usage exceeds `90%`, the script must log a warning to `/var/log/nexus/system_health.log` using `logger` and system diagnostics (`uptime`, `free`).
* **Milestone 3: Access Control & SSH Hardening (Session 3)**
  * Provision a dedicated service user named `nexus_svc` with UID `1984`, home directory `/opt/nexus`, and shell `/sbin/nologin`.
  * Create a group named `nautilus_devs` and add user `kano` to this group.
  * Configure secure file permissions (`chmod 750`) on `/opt/nexus` and set up ACLs (`setfacl`) so `nautilus_devs` has write access to the config directory.
* **Milestone 4: Service Management & Daemon Lifecycle (Session 4)**
  * Deploy a custom systemd unit file (`/etc/systemd/system/nexus.service`) that runs a background web service or mock script under the `nexus_svc` user account.
  * Ensure the service is enabled, started (`systemctl enable --now`), and configured with automatic restart policies (`Restart=always`).
* **Milestone 5: Networking, Storage & Automation Scripting (Session 5)**
  * Write an end-to-end Master Bash Script (`deploy_nexus.sh`) that orchestrates all steps across the 3 servers.
  * Include error handling (`trap`), logging functions, exit codes (`$?`), and network socket checks (`nc` or `ss`) to verify that the application port (`TCP 8080`) is actively listening.
  * Schedule a daily cron job (`crontab`) to execute a system health diagnostic script at midnight.

### Step-by-Step Implementation Guide

#### Step 1: Write the Master Bash Automation Script
Create a file named `deploy_nexus.sh` on your workstation or management node:

```bash
#!/bin/bash
# ==============================================================================
# Script Name: deploy_nexus.sh
# Description: End-to-end Enterprise Linux Capstone Deployment Script
# ==============================================================================

set -euo pipefail

APP_DIR="/opt/nexus"
LOG_DIR="/var/log/nexus"
SERVICE_NAME="nexus.service"

echo "=================================================="
echo "Starting Project Nexus Enterprise Deployment..."
echo "=================================================="

# 1. Filesystem Setup (Session 1)
echo "[1/5] Creating directory structures..."
sudo mkdir -p "$APP_DIR/app" "$APP_DIR/config" "$LOG_DIR"

# 2. Process & System Check (Session 2)
echo "[2/5] Running system resource check..."
CURRENT_LOAD=$(uptime | awk -F'load average:' '{print $2}' | awk '{print $1}' | sed 's/,//g')
echo "Current 1-min load average: $CURRENT_LOAD"

# 3. User & Access Control (Session 3)
echo "[3/5] Configuring users, groups, and permissions..."
if ! id "nexus_svc" &>/dev/null; then
    sudo useradd -u 1984 -d "$APP_DIR" -s /sbin/nologin -m nexus_svc
    echo "Created user nexus_svc."
fi

if ! getent group nautilus_devs &>/dev/null; then
    sudo groupadd nautilus_devs
    echo "Created group nautilus_devs."
fi

sudo usermod -aG nautilus_devs kano || true
sudo chown -R nexus_svc:nautilus_devs "$APP_DIR"
sudo chmod 750 "$APP_DIR"

# 4. systemd Service Deployment (Session 4)
echo "[4/5] Writing custom systemd unit file..."
sudo tee /etc/systemd/system/$SERVICE_NAME > /dev/null <<EOF
[Unit]
Description=Nexus Enterprise Microservice
After=network.target

[Service]
User=nexus_svc
Group=nautilus_devs
ExecStart=/usr/bin/python3 -m http.server 8080 --directory /opt/nexus/app
Restart=always
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable --now $SERVICE_NAME

# 5. Networking & Verification (Session 5)
echo "[5/5] Verifying network socket listeners..."
sleep 2
if ss -tulpn | grep -q ":8080"; then
    echo "[SUCCESS] Nexus service is successfully listening on port 8080."
else
    echo "[ERROR] Port 8080 is not active. Check journal logs."
    sudo journalctl -u $SERVICE_NAME -n 20
    exit 1
fi

echo "=================================================="
echo "Deployment Completed Successfully!"
echo "=================================================="
```

#### Step 2: Make Script Executable & Run
```bash
chmod +x deploy_nexus.sh
./deploy_nexus.sh
```

### Validation & Testing Checklists
Students must execute the following validation commands to prove their lab works:

1. **Session 1 Check:** Verify directory tree and permissions:
   ```bash
   ls -la /opt/nexus
   ```
2. **Session 2 Check:** Inspect process resource consumption:
   ```bash
   ps aux | grep http.server
   ```
3. **Session 3 Check:** Verify user UID and group membership:
   ```bash
   id nexus_svc
   groups kano
   ```
4. **Session 4 Check:** Confirm systemd service health status:
   ```bash
   sudo systemctl status nexus.service
   journalctl -u nexus.service -n 50 --no-pager
   ```
5. **Session 5 Check:** Test network port reachability:
   ```bash
   nc -zv localhost 8080
   curl -I http://localhost:8080
   ```

### LinkedIn Showcase & Portfolio Template
When you complete this capstone, post your achievement on LinkedIn using this professional template:

> 🚀 **Excited to share my latest DevOps & Linux Administration Capstone Project!**
>
> As part of my Platform Engineering training, I built **Project Nexus**—an automated deployment pipeline across multi-node Linux environments (`app01-03`).
>
> **Key Technical Highlights:**
> * ✅ **FHS & Text Processing:** Implemented strict Linux filesystem hierarchies and automated log rotation scripts.
> * ✅ **Process Troubleshooting:** Built resource monitoring checks tracking CPU load and memory thresholds.
> * ✅ **Security & RBAC:** Provisioned least-privilege service accounts (`nexus_svc`), custom UIDs (`1984`), and group-based ACLs.
> * ✅ **Systemd Automation:** Engineered custom background daemons with automatic restart policies.
> * ✅ **Networking & Bash Scripting:** Wrote idempotent deployment automation scripts validated via `ss`, `nc`, and system socket probes.
>
> Open-source code available on GitHub! Let’s connect as I continue my journey into Cloud & DevOps Engineering. 🌐👇
>
> `#DevOps` `#Linux` `#SystemAdministration` `#CloudEngineering` `#Automation` `#Bash` `#PlatformEngineering`
