
# DevOps Essentials: 125 Practical Command Examples

## Sample JSON Dataset Setup (`data.json`)

Run this command in your terminal to create `data.json` so you can test all 25 `jq` examples immediately:

```bash
cat << 'EOF' > data.json
{
  "environment": "production",
  "cluster": "eks-ap-south-1",
  "active": true,
  "nodes": [
    {"id": "node-1", "cpu": 45, "memory_gb": 16, "status": "Ready", "tags": ["web", "api"]},
    {"id": "node-2", "cpu": 82, "memory_gb": 32, "status": "Ready", "tags": ["db", "cache"]},
    {"id": "node-3", "cpu": 12, "memory_gb": 8, "status": "NotReady", "tags": ["worker"]}
  ],
  "deployments": {
    "frontend": {"replicas": 3, "image": "nginx:1.25"},
    "backend": {"replicas": 5, "image": "node:20-alpine"}
  }
}
EOF
```

---

## 1. `ss` (Socket Statistics) — 25 Examples

1. **List all active connections (established and listening):**
   ```bash
   ss -a
   ```
2. **List all listening sockets only:**
   ```bash
   ss -l
   ```
3. **List all listening TCP ports:**
   ```bash
   ss -lt
   ```
4. **List all listening UDP ports:**
   ```bash
   ss -lu
   ```
5. **Show listening TCP/UDP ports with numeric port numbers and process names (most common):**
   ```bash
   ss -tulnp
   ```
6. **Display a summary of all socket statistics by protocol:**
   ```bash
   ss -s
   ```
7. **List all established TCP connections:**
   ```bash
   ss -t state established
   ```
8. **List all connections in `TIME-WAIT` state:**
   ```bash
   ss -t state time-wait
   ```
9. **List all connections in `SYN-RECV` state (useful for spotting SYN flood attacks):**
   ```bash
   ss -t state syn-recv
   ```
10. **Filter connections by a specific destination or local port (e.g., port 443):**
    ```bash
    ss -tn '( dport = :443 or sport = :443 )'
    ```
11. **Find which process is using port 8080:**
    ```bash
    ss -tlpn 'sport = :8080'
    ```
12. **Filter connections to a specific remote IP address:**
    ```bash
    ss -tn dst 192.168.1.50
    ```
13. **Filter connections from a specific subnet (CIDR):**
    ```bash
    ss -tn src 10.0.0.0/8
    ```
14. **Show only IPv4 sockets:**
    ```bash
    ss -4 -tuln
    ```
15. **Show only IPv6 sockets:**
    ```bash
    ss -6 -tuln
    ```
16. **Show Unix domain sockets (used by Docker, databases, and systemd):**
    ```bash
    ss -x
    ```
17. **Display TCP internal information (RTT, congestion window, bitrate):**
    ```bash
    ss -ti
    ```
18. **Display socket memory usage:**
    ```bash
    ss -tm
    ```
19. **Display timer information for sockets (keepalive, retransmissions):**
    ```bash
    ss -to
    ```
20. **Show SELinux security contexts for sockets:**
    ```bash
    ss -Z
    ```
21. **Suppress header line in output (useful for scripting):**
    ```bash
    ss -H -tuln
    ```
22. **Monitor socket changes continuously every 2 seconds:**
    ```bash
    watch -n 2 "ss -tulnp"
    ```
23. **Count total established HTTP/HTTPS connections:**
    ```bash
    ss -tn state established '( dport = :80 or dport = :443 )' | wc -l
    ```
24. **List all established SSH connections:**
    ```bash
    ss -tn state established '( sport = :22 or dport = :22 )'
    ```
25. **Show extended socket information (UID, inode):**
    ```bash
    ss -te
    ```

---

## 2. `curl` (Client URL) — 25 Examples

1. **Fetch the body of a URL (basic GET request):**
   ```bash
   curl https://example.com
   ```
2. **Fetch only HTTP response headers (`HEAD` request):**
   ```bash
   curl -I https://example.com
   ```
3. **Follow HTTP redirects (`301`/`302`):**
   ```bash
   curl -L https://example.com
   ```
4. **Save output to a file using its remote filename:**
   ```bash
   curl -O https://example.com
   ```
5. **Save output to a custom local filename:**
   ```bash
   curl -o custom_name.html https://example.com
   ```
6. **Resume an interrupted file download:**
   ```bash
   curl -C - -O https://example.com
   ```
7. **Show verbose connection details (DNS, TLS handshake, request/response headers):**
   ```bash
   curl -v https://example.com
   ```
8. **Silent mode (hide progress bar and errors, ideal for scripts):**
   ```bash
   curl -s https://example.com
   ```
9. **Silent mode, but still display errors if the request fails:**
   ```bash
   curl -sS https://example.com
   ```
10. **Fail fast with exit code 22 on HTTP errors (`404`, `500`) in CI/CD pipelines:**
    ```bash
    curl -f https://example.com
    ```
11. **Send a POST request with form data:**
    ```bash
    curl -X POST -d "user=alice&role=admin" https://example.com
    ```
12. **Send a POST request with a JSON payload:**
    ```bash
    curl -X POST -H "Content-Type: application/json" -d '{"name":"alice","role":"admin"}' https://example.com
    ```
13. **Send JSON data loaded from a local file:**
    ```bash
    curl -X POST -H "Content-Type: application/json" -d @data.json https://example.com
    ```
14. **Send a PUT request to update a resource:**
    ```bash
    curl -X PUT -H "Content-Type: application/json" -d '{"replicas":5}' https://example.com
    ```
15. **Send a DELETE request:**
    ```bash
    curl -X DELETE https://example.com/1001
    ```
16. **Include a Bearer token for API authentication:**
    ```bash
    curl -H "Authorization: Bearer YOUR_TOKEN" https://example.com
    ```
17. **Authenticate using Basic Auth (`username:password`):**
    ```bash
    curl -u admin:secret123 https://example.com
    ```
18. **Ignore self-signed or expired SSL certificate warnings (dev/staging):**
    ```bash
    curl -k https://localhost:8443/health
    ```
19. **Set a strict connection timeout and max total request time (in seconds):**
    ```bash
    curl --connect-timeout 5 --max-time 15 https://example.com
    ```
20. **Print only the HTTP status code (e.g., `200`, `503`):**
    ```bash
    curl -s -o /dev/null -w "%{http_code}\n" https://example.com
    ```
21. **Measure DNS lookup, connection, and total response time:**
    ```bash
    curl -s -o /dev/null -w "DNS: %{time_namelookup}s | Connect: %{time_connect}s | Total: %{time_total}s\n" https://example.com
    ```
22. **Force resolution of a domain to a specific IP (test a new server before DNS switch):**
    ```bash
    curl --resolve example.com:443:192.168.1.100 https://example.com
    ```
23. **Upload a file using `multipart/form-data`:**
    ```bash
    curl -F "file=@report.pdf" https://example.com
    ```
24. **Route the request through an HTTP proxy:**
    ```bash
    curl -x http://proxy.local:3128 https://example.com
    ```
25. **Query a local Docker daemon or service over a Unix socket:**
    ```bash
    curl --unix-socket /var/run/docker.sock http://localhost/containers/json
    ```

---

## 3. `systemctl` (Systemd Service Manager) — 25 Examples

1. **Check the current status, PID, and recent logs of a service:**
   ```bash
   systemctl status nginx
   ```
2. **Start a service immediately:**
   ```bash
   sudo systemctl start nginx
   ```
3. **Stop a running service:**
   ```bash
   sudo systemctl stop nginx
   ```
4. **Restart a service (stops and starts it):**
   ```bash
   sudo systemctl restart nginx
   ```
5. **Reload configuration files without dropping active connections:**
   ```bash
   sudo systemctl reload nginx
   ```
6. **Reload if supported, otherwise restart the service:**
   ```bash
   sudo systemctl reload-or-restart nginx
   ```
7. **Enable a service to start automatically at boot:**
   ```bash
   sudo systemctl enable nginx
   ```
8. **Disable a service from starting at boot:**
   ```bash
   sudo systemctl disable nginx
   ```
9. **Enable and start a service in a single command:**
   ```bash
   sudo systemctl enable --now nginx
   ```
10. **Disable and stop a service in a single command:**
    ```bash
    sudo systemctl disable --now nginx
    ```
11. **Check if a service is currently active (returns exit code 0 if active):**
    ```bash
    systemctl is-active nginx
    ```
12. **Check if a service is enabled at boot:**
    ```bash
    systemctl is-enabled nginx
    ```
13. **Check if a service has entered a failed state:**
    ```bash
    systemctl is-failed nginx
    ```
14. **List all currently running services:**
    ```bash
    systemctl list-units --type=service --state=running
    ```
15. **List all failed services across the system:**
    ```bash
    systemctl --failed
    ```
16. **List all installed unit files and their boot states (`enabled`/`disabled`):**
    ```bash
    systemctl list-unit-files --type=service
