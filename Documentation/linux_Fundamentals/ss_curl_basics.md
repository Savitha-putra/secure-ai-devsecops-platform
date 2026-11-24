# Linux Networking & DevOps Essentials: Deep Dive into `ss` and `curl`

Welcome to Linux networking! As a beginner stepping into Linux and DevOps, mastering **`ss`** and **`curl`** will give you superpowers. Almost every production outage, deployment failure, or microservice bug boils down to two questions:

1. *"Is my service running and listening on the right port?"* $\rightarrow$ Answered by **`ss`**
2. *"Can my service talk to other APIs/services over the network?"* $\rightarrow$ Answered by **`curl`**

---

## Part 1: The `ss` Command (Socket Statistics)

### What is `ss` and Why Do We Use It?

In Linux, when a program wants to communicate over a network (or even locally with another program), it opens a **socket**—an endpoint for sending and receiving data, usually tied to an IP address and a Port number.

`ss` stands for **Socket Statistics**. It is the modern, blazingly fast replacement for the older, deprecated `netstat` command. While `netstat` reads text files from `/proc` (which becomes painfully slow on busy servers with thousands of connections), `ss` talks directly to the Linux kernel's `tcp_diag` module, giving you instant, detailed insights.

### How is `ss` Useful in Day-to-Day DevOps?

* **Port Conflict Resolution:** Finding out which rogue process is already hogging port `80` or `8080` when your Docker container or Nginx server fails to start.
* **Service Health Verification:** Confirming if a newly deployed microservice is actually listening on `0.0.0.0` (all interfaces) vs `127.0.0.1` (localhost only).
* **Incident Response & Security:** Detecting unauthorized outbound connections (e.g., crypto-miners or malware) and identifying which Process ID (PID) owns them.
* **Performance & Bottleneck Debugging:** Spotting connection leaks (thousands of sockets stuck in `TIME-WAIT` or `CLOSE-WAIT` states) or full receive/send queues (`Recv-Q` / `Send-Q`).

### Understanding `ss` Output Columns

When you run `ss`, you typically see these columns:

* **`Netid`**: Protocol type (`tcp`, `udp`, `u_str` for Unix sockets).
* **`State`**: Connection state (`LISTEN`, `ESTAB`, `TIME-WAIT`, `SYN-SENT`, etc.).
* **`Recv-Q` / `Send-Q`**: Bytes waiting to be read by your app (`Recv-Q`) or waiting to be acknowledged by the remote peer (`Send-Q`). High numbers here mean a bottleneck!
* **`Local Address:Port`**: Your machine's IP and port.
* **`Peer Address:Port`**: The remote machine's IP and port (`*:*` if just listening).
* **`Process`**: The program name and PID using the socket (requires `-p` and `sudo`).

### Common `ss` Flags Cheat Sheet

| Flag            | Meaning     | Why use it?                                                                 |
| :-------------- | :---------- | :-------------------------------------------------------------------------- |
| `-t`          | TCP         | Show only TCP sockets                                                       |
| `-u`          | UDP         | Show only UDP sockets                                                       |
| `-l`          | Listening   | Show only ports waiting for incoming connections                            |
| `-a`          | All         | Show both listening and non-listening (active) sockets                      |
| `-n`          | Numeric     | Don't resolve IPs to domain names or ports to names (makes it fast & exact) |
| `-p`          | Processes   | Show the PID and process name (run with `sudo`)                           |
| `-s`          | Summary     | Show overall socket statistics                                              |
| `-4` / `-6` | IPv4 / IPv6 | Filter strictly by IP version                                               |

---

### 15 Practical `ss` Examples Explained

#### 1. The DevOps Holy Grail: List all listening TCP/UDP ports with process names

```bash
sudo ss -tulnp
```

* **Explanation:** Combines `-t` (TCP), `-u` (UDP), `-l` (Listening), `-n` (Numeric ports), and `-p` (Process info). This is the #1 command you will run on any server to see every service exposed on the network and which application owns it.

#### 2. Get a quick summary of all network connections

```bash
ss -s
```

* **Explanation:** Displays total sockets broken down by protocol (TCP, UDP, RAW) and state (`estab`, `closed`, `orphaned`, `timewait`). Great for a 2-second health check during high traffic spikes.

#### 3. List all active (established) TCP connections

```bash
ss -tn state established
```

* **Explanation:** Shows only ongoing, active TCP connections (`-t`) with raw IPs/ports (`-n`). Useful for seeing who is currently connected to your server or what external APIs your server is talking to.

#### 4. Find out what is running on a specific port (e.g., Port 8080)

```bash
sudo ss -tlnp sport = :8080
```

* **Explanation:** Filters listening TCP sockets (`-tlnp`) where the **source port** (`sport`) equals `8080`. Use this when your app crashes with `"Address already in use"`.

#### 5. Check all outbound connections to a specific remote port (e.g., PostgreSQL 5432)

```bash
ss -tnp dport = :5432
```

* **Explanation:** Filters by **destination port** (`dport`). Helps you verify if your application containers are actively connected to your database server.

#### 6. List all connections to or from a specific IP address

```bash
ss -an dst 10.0.1.50
```

* **Explanation:** Uses the `dst` (destination) filter to find every socket communicating with `10.0.1.50`. Replace `dst` with `src` to filter by local source IP.

#### 7. Filter connections by an entire subnet (CIDR block)

```bash
ss -tn dst 192.168.1.0/24
```

* **Explanation:** Shows all TCP connections going to any machine inside the `192.168.1.0/24` subnet. Ideal for checking traffic between microservices inside a private VPC.

#### 8. Hunt for connection leaks (`TIME-WAIT` or `CLOSE-WAIT`)

```bash
ss -tan state close-wait
```

* **Explanation:** Lists all TCP sockets stuck in `CLOSE-WAIT`. In DevOps, a high number of `CLOSE-WAIT` sockets means the remote server closed the connection, but your local application has a bug and forgot to close its socket.

#### 9. Inspect TCP internal timers (Keepalive, Retransmissions)

```bash
ss -to state established
```

* **Explanation:** The `-o` flag displays timer information (like `keepalive` or `on` for retransmission timers). If you see heavy retransmissions, you have packet loss or network congestion.

#### 10. Check detailed TCP performance metrics (Congestion control, RTT, Bandwidth)

```bash
ss -ti
```

* **Explanation:** The `-i` flag prints internal TCP info from the kernel: Round Trip Time (`rtt`), congestion control algorithm (`cubic` or `bbr`), and delivery rate. Essential for diagnosing slow network transfers.

#### 11. View socket memory usage

```bash
ss -tm
```

* **Explanation:** The `-m` flag shows how much kernel memory each socket buffer is consuming. Useful when troubleshooting Out-Of-Memory (OOM) issues on high-throughput proxies.

#### 12. List only IPv4 or only IPv6 listening sockets

```bash
ss -tl4
```

* **Explanation:** The `-4` flag restricts output strictly to IPv4 sockets (use `-6` for IPv6). Helps verify whether a service accidentally bound only to IPv6 (`[::]:80`) instead of IPv4 (`0.0.0.0:80`).

#### 13. Inspect Unix Domain Sockets (Local inter-process communication)

```bash
ss -xlp
```

* **Explanation:** The `-x` flag displays Unix sockets. Many DevOps tools (like Docker daemon `/var/run/docker.sock`, PHP-FPM, or PostgreSQL) communicate locally via Unix sockets rather than TCP ports.

#### 14. Combine conditions using logical operators (`and` / `or`)

```bash
ss -tn state established '( sport = :80 or sport = :443 )'
```

* **Explanation:** Uses parentheses and `or` to display all active HTTP and HTTPS connections simultaneously. Note the single quotes so Bash doesn't interpret the parentheses.

#### 15. Kill/Close a stuck socket manually (Emergency troubleshooting)

```bash
sudo ss -K dst 10.0.1.50 dport = :443
```

* **Explanation:** The `-K` flag forces the Linux kernel to forcefully close matching sockets (`RST` packet). Useful when an application is hung waiting on a dead remote connection that won't time out.

---

## Part 2: The `curl` Command (Client URL)

### What is `curl` and Why Do We Use It?

`curl` stands for **Client URL**. It is a command-line tool for transferring data to or from a server using URLs. While it supports dozens of protocols (HTTP, HTTPS, FTP, SFTP, SMTP, SCP), it is overwhelmingly used as a headless web browser and API client.

### How is `curl` Useful in Day-to-Day DevOps?

* **CI/CD Pipelines & Health Checks:** Docker `HEALTHCHECK` instructions, Kubernetes liveness probes, and GitHub Actions rely on `curl` to verify if an application is returning `200 OK`.
* **API Testing & Debugging:** Testing REST APIs, sending JSON payloads, and verifying authentication headers (JWT/Bearer tokens) directly from a terminal without needing Postman.
* **SSL/TLS & DNS Troubleshooting:** Inspecting expired SSL certificates, TLS handshake failures, HTTP redirects, and latency breakdowns.
* **Automation & Artifact Downloads:** Fetching installation scripts, binaries, or configuration files inside automated server provisioning scripts (Terraform/Ansible/Bash).

### Common `curl` Flags Cheat Sheet

| Flag            | Long Flag                        | Meaning                                                                     |
| :-------------- | :------------------------------- | :-------------------------------------------------------------------------- |
| `-I`          | `--head`                       | Fetch HTTP response headers only                                            |
| `-i`          | `--include`                    | Include HTTP response headers alongside the body                            |
| `-v`          | `--verbose`                    | Show full connection details (DNS, TLS handshake, request/response headers) |
| `-s`          | `--silent`                     | Hide progress bar and error messages (great for scripts)                    |
| `-S`          | `--show-error`                 | Used with `-s` (`-sS`) to hide progress bar *but still show errors*   |
| `-L`          | `--location`                   | Follow HTTP `301`/`302` redirects automatically                         |
| `-X`          | `--request`                    | Specify HTTP method (`GET`, `POST`, `PUT`, `DELETE`)                |
| `-H`          | `--header`                     | Pass custom HTTP headers (e.g., `Authorization`, `Content-Type`)        |
| `-d`          | `--data`                       | Send data in a `POST`/`PUT` request body                                |
| `-o` / `-O` | `--output` / `--remote-name` | Save output to a custom filename (`-o`) or original filename (`-O`)     |
| `-f`          | `--fail`                       | Fail silently with exit code `22` on HTTP errors (404, 500)               |

---

### 15 Practical `curl` Examples Explained

#### 1. Basic GET request (Fetch webpage or API response)

```bash
curl https://api.github.com/zen
```

* **Explanation:** Sends a standard HTTP `GET` request and prints the response body directly to your terminal.

#### 2. Fetch ONLY the HTTP response headers

```bash
curl -I https://example.com
```

* **Explanation:** Uses `-I` (sends an HTTP `HEAD` request) to view status codes (`200 OK`, `404 Not Found`), server type (`nginx`, `cloudflare`), and cache headers without downloading the entire page.

#### 3. Verbose debugging (The DevOps X-Ray Vision)

```bash
curl -v https://example.com
```

* **Explanation:** `-v` prints the entire lifecycle of the request: DNS resolution, TCP connection, TLS/SSL certificate details, outgoing request headers (`>`), and incoming response headers (`<`). Use this whenever a connection fails.

#### 4. Follow HTTP redirects automatically

```bash
curl -L http://github.com
```

* **Explanation:** Without `-L`, `curl` stops at a `301 Moved Permanently` response (e.g., HTTP redirecting to HTTPS). `-L` tells `curl` to follow the `Location` header until it reaches the final destination.

#### 5. Download a file and save it with its original name

```bash
curl -LO https://example.com/app-v1.2.0.tar.gz
```

* **Explanation:** `-O` saves the file using the filename from the URL (`app-v1.2.0.tar.gz`), and `-L` ensures it follows any download redirects. Use lowercase `-o custom_name.tar.gz` if you want to rename it.

#### 6. Resume an interrupted large download

```bash
curl -C - -O https://example.com/large-database-backup.sql.gz
```

* **Explanation:** `-C -` tells `curl` to automatically inspect the partially downloaded file on disk and resume from the exact byte where the network dropped.

#### 7. Send a POST request with JSON data (Testing REST APIs)

```bash
curl -X POST https://api.example.com/v1/users \
  -H "Content-Type: application/json" \
  -d '{"username": "devops_admin", "role": "engineer"}'
```

* **Explanation:** `-X POST` sets the HTTP method, `-H` informs the server we are sending JSON, and `-d` carries the JSON payload.

#### 8. Authenticate using a Bearer Token (JWT / API Keys)

```bash
curl -H "Authorization: Bearer YOUR_SECRET_TOKEN" https://api.example.com/v1/profile
```

* **Explanation:** Passes an `Authorization` header. This is how you interact with Kubernetes APIs, GitHub APIs, or secured microservices from the CLI.

#### 9. Basic Authentication (Username & Password)

```bash
curl -u admin:supersecret https://jenkins.example.com/api/json
```

* **Explanation:** `-u` automatically encodes `admin:supersecret` into Base64 and sends it in the `Authorization: Basic` header.

#### 10. Upload a file via `multipart/form-data`

```bash
curl -X POST https://api.example.com/upload \
  -F "file=@/path/to/report.pdf" \
  -F "description=Monthly Audit"
```

* **Explanation:** `-F` emulates submitting an HTML form. Notice the `@` symbol before the file path—that tells `curl` to read and upload the binary file contents rather than sending the literal string path.

#### 11. Ignore invalid or self-signed SSL certificates (Dev/Staging environments)

```bash
curl -k https://localhost:8443/health
```

* **Explanation:** `-k` (or `--insecure`) bypasses SSL certificate verification. Essential when testing internal services using self-signed certificates, though you should never use it blindly in production scripts.

#### 12. Test a website on a specific IP before updating DNS (`--resolve`)

```bash
curl --resolve myapp.com:443:10.0.2.15 https://myapp.com
```

* **Explanation:** Forces `curl` to resolve `myapp.com` on port `443` to `10.0.2.15` without editing `/etc/hosts`. Unlike passing a `Host` header, `--resolve` also ensures SSL SNI (Server Name Indication) works properly!

#### 13. Measure exact network latency breakdown (DNS, TCP, TLS, TTFB)

```bash
curl -s -o /dev/null -w "DNS: %{time_namelookup}s | Connect: %{time_connect}s | TLS: %{time_appconnect}s | TTFB: %{time_starttransfer}s | Total: %{time_total}s\n" https://example.com
```

* **Explanation:** Discards the body (`-o /dev/null`) and uses `-w` (`--write-out`) to print exact timing metrics. In 1 second, you can tell whether a slow API is caused by slow DNS, TLS handshake overhead, or slow backend code (Time To First Byte).

#### 14. CI/CD Safe Execution: Fail properly on HTTP 4xx/5xx errors

```bash
curl -fsSL https://example.com/install.sh -o install.sh
```

* **Explanation:** By default, `curl` exits with code `0` (success) even if the server returns `404 Not Found` or `500 Internal Server Error`! Adding `-f` (`--fail`) forces `curl` to return a non-zero exit code on HTTP errors so your CI/CD pipeline stops immediately instead of trying to execute a 404 HTML page as a script.

#### 15. Set timeouts so automated scripts never hang forever

```bash
curl --connect-timeout 5 --max-time 15 https://api.example.com/health
```

* **Explanation:** `--connect-timeout 5` gives up if the TCP connection isn't established within 5 seconds; `--max-time 15` kills the entire operation if it takes longer than 15 seconds. Crucial for cron jobs and health check scripts.
