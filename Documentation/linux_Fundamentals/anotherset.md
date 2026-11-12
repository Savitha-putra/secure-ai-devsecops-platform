**Reload systemd manager configuration after creating or editing a `.service` file**:
```bash
sudo systemctl daemon-reload
```

**View the full contents of a service unit file:**
```bash
systemctl cat nginx.service
```
19. **Create an override file to customize a service without editing the vendor file:**
```bash
sudo systemctl edit nginx.service ```
21. **Mask a service so it cannot be started manually or by other services:**
```bash
sudo systemctl mask bluetooth.service ```
22. **Unmask a previously masked service:**
```bash
sudo systemctl unmask bluetooth.service ```
23. **Show all low-level properties (memory limits, environment variables, restart policy) of a service:**
```bash
systemctl show nginx ```
24. **List dependencies required by a service:**
```bash
systemctl list-dependencies nginx ```
25. **List all active systemd timers (modern replacement for cron):**
```bash
systemctl list-timers --all ```
26. **Reset the failed state counter of a service after fixing a crash:**
```bash
sudo systemctl reset-failed nginx ```
```

4. journalctl (Systemd Log Viewer) — 25 Examples

1. View all system logs from oldest to newest:
   bash journalctl    
2. Jump straight to the newest log entries (-e = end):
   bash journalctl -xe    
3. Follow live log output in real time (like tail -f):
   bash journalctl -f    
4. View logs for a specific service (e.g., nginx or docker):
   bash journalctl -u nginx.service    
5. Follow live logs for a specific service:
   bash journalctl -u docker.service -f    
6. Combine logs from multiple services in chronological order:
   bash journalctl -u nginx.service -u php-fpm.service    
7. Show logs from the current boot session only:
   bash journalctl -b    
8. Show logs from the previous boot session (crucial after a server crash/reboot):
   bash journalctl -b -1    
9. List all recorded boot sessions with their timestamps:
   bash journalctl --list-boots    
10. Filter logs since a relative time window:bash
journalctl --since "15 minutes ago"
Use code with caution.
11. Filter logs between two exact timestamps:bash
journalctl --since "2026-11-12 10:00:00" --until "2026-11-12 11:30:00"
Use code with caution.
12. Filter logs from today only:bash
journalctl --since today
Use code with caution.
13. Show only error, critical, alert, and emergency messages (-p err):bash
journalctl -p err
Use code with caution.
14. Show errors for a specific service since 1 hour ago:bash
journalctl -u nginx -p err --since "1 hour ago"
Use code with caution.
15. Show kernel ring buffer messages (equivalent to dmesg):bash
journalctl -k
Use code with caution.
16. Filter logs by a specific Process ID (PID):bash
journalctl _PID=1234
Use code with caution.
17. Filter logs by a specific executable binary path:bash
journalctl /usr/sbin/sshd
Use code with caution.
18. Display the last 50 log lines:bash
journalctl -n 50
Use code with caution.
19. Output logs in JSON format for parsing with jq or log shippers:bash
journalctl -u nginx -o json-pretty -n 5
Use code with caution.
20. Disable line truncation so long stack traces wrap cleanly:bash
journalctl -u myapp --no-pager
Use code with caution.
21. Display timestamps in UTC instead of local time:bash
journalctl --utc
Use code with caution.
22. Check how much disk space journal logs are currently consuming:bash
journalctl --disk-usage
Use code with caution.
23. Delete old journal logs to keep disk usage under 500 MB:bash
sudo journalctl --vacuum-size=500M
Use code with caution.
24. Delete journal logs older than 7 days:bash
sudo journalctl --vacuum-time=7d
Use code with caution.
25. Filter journal entries matching a specific text pattern (systemd 237+):bash
journalctl -u sshd -g "Failed password"
Use code with caution.

5. jq (JSON Processor) — 25 Examples

(All examples below use the data.json file created at the top of this section.)
1. Pretty-print and colorize a JSON file:
   bash jq '.' data.json    
2. Compact JSON output onto a single line (remove whitespace):
   bash jq -c '.' data.json    
3. Extract a top-level string value:
   bash jq '.environment' data.json    
4. Extract a value without surrounding double quotes (-r = raw output):
   bash jq -r '.cluster' data.json    
5. Extract nested object fields:
   bash jq '.deployments.backend.image' data.json    
6. List all top-level keys in a JSON object:
   bash jq 'keys' data.json    
7. Get the first element of an array:
   bash jq '.nodes[0]' data.json    
8. Get the last element of an array:
   bash jq '.nodes[-1]' data.json    
9. Iterate over all elements in an array:
   bash jq '.nodes[]' data.json    
10. Extract a specific field (id) from every object in an array:bash
jq -r '.nodes[].id' data.json
Use code with caution.
11. Count the number of elements in an array:bash
jq '.nodes | length' data.json
Use code with caution.
12. Filter array objects where status equals "Ready":bash
jq '.nodes[] | select(.status == "Ready")' data.json
Use code with caution.
13. Filter nodes with CPU usage greater than 50 and print only their IDs:bash
jq -r '.nodes[] | select(.cpu > 50) | .id' data.json
Use code with caution.
14. Filter nodes that contain "db" in their tags array:bash
jq -r '.nodes[] | select(.tags | contains(["db"])) | .id' data.json
Use code with caution.
15. Construct a new simplified JSON object for each node:bash
jq '[.nodes[] | {node: .id, healthy: (.status == "Ready")}]' data.json
Use code with caution.
16. Format extracted JSON fields into a clean CSV string:bash
jq -r '.nodes[] | [.id, .cpu, .status] | @csv' data.json
Use code with caution.
17. Format extracted JSON fields into tab-separated values (@tsv):bash
jq -r '.nodes[] | [.id, .memory_gb, .status] | @tsv' data.json
Use code with caution.
18. Calculate the total memory_gb across all nodes:bash
jq '[.nodes[].memory_gb] | add' data.json
Use code with caution.
19. Find the node with the highest CPU usage:bash
jq '.nodes | max_by(.cpu)' data.json
Use code with caution.
20. Sort nodes by CPU usage in ascending order:bash
jq '.nodes | sort_by(.cpu)' data.json
Use code with caution.
21. Update a field value in the JSON output:bash
jq '.deployments.frontend.replicas = 6' data.json
Use code with caution.
22. Delete a key from the JSON output:bash
jq 'del(.active)' data.json
Use code with caution.
23. Provide a fallback default value if a key is missing or null (//):bash
jq -r '.region // "ap-south-1"' data.json
Use code with caution.
24. Pass a shell variable safely into a jq filter using --arg:bash
jq --arg st "NotReady" '.nodes[] | select(.status == $st)' data.json
Use code with caution.
25. Pipe live curl JSON API output directly into jq:bash
curl -s https://github.com | jq '{name: .full_name, stars: .stargazers_count}'
