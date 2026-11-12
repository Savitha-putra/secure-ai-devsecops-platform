Global Regular Expression Print) designed specifically to work with the file.txt you created earlier.

25 Examples of grep


Basic Searching & Matching

1. Search for an exact string: ``` grep "user" file.txt ```
2. Case-insensitive search (matches old and OLD): ``` grep -i "old" file.txt ```
3. Match whole words only (prevents matching partial words): ``` grep -w "old" file.txt ```
4. Match an exact full line: ``` grep -x "# End of file" file.txt ```
5. Search for multiple patterns using -e: ``` grep -e "error" -e "debug" file.txt ```

Inverting & Counting Matches

6. Invert match (show lines that do NOT contain user): ``` grep -v "user" file.txt ```
7. Filter out comment lines and empty lines: ``` grep -v -e "^#" -e "^$" file.txt ```
8. Count how many lines match a pattern: ``` grep -c "user" file.txt ```
9. Show only the matched part of the line (not the whole line): ``` grep -o "[0-9]\+" file.txt ```
10. Stop searching after the first 2 matches: ``` grep -m 2 "user" file.txt ```

Line Numbers & Context

11. Display line numbers alongside matching lines: ``` grep -n "failed" file.txt ```
12. Show 2 lines AFTER each match (-A = After): ``` grep -A 2 "error" file.txt ```
13. Show 2 lines BEFORE each match (-B = Before): ``` grep -B 2 "status" file.txt ```
14. Show 1 line BEFORE and AFTER each match (-C = Context): ``` grep -C 1 "debug" file.txt ```
15. Highlight matched text in color: ``` grep --color=always "admin" file.txt ```

Regular Expressions (Anchors & Patterns)

16. Match lines starting with a specific word (^): ``` grep "^user" file.txt ```
17. Match lines ending with a specific word ($): ``` grep "bash$" file.txt ```
18. Match lines containing any 4-digit number (extended regex -E): ``` grep -E "[0-9]{4}" file.txt ```
19. Match either alice or bob using OR (|): ``` grep -E "alice|bob" file.txt ```
20. Match any line containing a file path: ``` grep -E "/[a-z]+/[a-z]+" file.txt ```

Multi-File & Pipeline Usage

21. Display only the filename if a match is found: ``` grep -l "failed" *.txt ```
22. Display filenames that do NOT contain the pattern: ``` grep -L "failed" *.txt ```
23. Search recursively through all files in the current directory: ``` grep -r "alice" . ```
24. Suppress error messages for unreadable/missing files: ``` grep -s "alice" file.txt missing.txt ```
25. Filter output from another command via pipe: ``` cat file.txt | grep "user" |  grep -v "guest" ```



Real-World grep Examples (Without file.txt)


1. System & Process Monitoring

• Find if a specific program (e.g., Nginx) is running: ps aux | grep nginx
• Check which process is listening on port 8080: ss -tulnp | grep 8080
• Check if a specific package is installed (Debian/Ubuntu): dpkg -l | grep python3
• Check if a specific package is installed (RHEL/CentOS): rpm -qa | grep openssl
• Check USB devices connected to the system: lsusb | grep -i "keyboard"

2. Log Analysis & Troubleshooting

• Find all critical errors in the system log: grep -i "error" /var/log/syslog
• Monitor a live log file in real time for failures: tail -f /var/log/nginx/access.log | grep "500"
• Find failed SSH login attempts in auth logs: grep "Failed password" /var/log/auth.log
• Count how many times a specific IP hit your web server: grep -c "192.168.1.50" /var/log/nginx/access.log
• See 5 lines before and after a kernel panic message: grep -C 5 "panic" /var/log/kern.log

3. Searching Codebases & Directories

• Find every file in a project containing a specific function: grep -rnw '/path/to/project' -e 'authenticateUser'
• Search for TODO comments while ignoring .git and node_modules: grep -rn --exclude-dir={.git,node_modules} "TODO" .
• Search only inside .py (Python) files: grep -rn --include="*.py" "import requests" .
• Find hardcoded IP addresses across a codebase: grep -rnE "[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}" src/

4. Reading Clean Configuration Files

• View active SSH server settings without comments or empty lines: grep -vE "^#|^$" /etc/ssh/sshd_config
• Check the exact CPU model name on a Linux machine: grep "model name" /proc/cpuinfo | head -n 1
• Check total RAM in /proc/meminfo: grep "MemTotal" /proc/meminfo
