sed (short for Stream Editor) is a command-line utility in Unix and Linux used to parse, filter, and transform text streams or files automatically without opening them in a text editor.

How sed Works

sed processes text one line at a time using a continuous loop:
• Read: It reads a single line from an input file or pipeline into a temporary memory area called the pattern space.
• Execute: It applies your specified instructions (such as find-and-replace, delete, or insert) to that line.
• Print: It outputs the modified line to the screen (standard output) and clears the pattern space.
• Repeat: It moves to the next line until the entire file is processed. By default, sed does not change your original file unless you pass the -i (in-place) flag.

Where sed Is Most Commonly Used

• Bulk Find-and-Replace: Updating IP addresses, URLs, or passwords across dozens of configuration files in seconds without opening each file manually.
• Cleaning Log and Data Files: Stripping out blank lines, removing # comment lines, or deleting debug messages before feeding data into another script.
• Automated CI/CD & Deployment Scripts: Dynamically injecting version numbers, environment variables, or build tags into templates during software deployment.
• Extracting Specific Line Ranges: Pulling lines 500 to 600 out of a massive multi-gigabyte log file where standard text editors would freeze or crash.
• Pipeline Text Formatting: Cleaning up output on the fly between commands (for example, command1 | sed '...' | command2).
Create below file and then start running below commands
```bash
cat << 'EOF' > file.txt
# Configuration and Log File
user:alice:1001:admin:/home/alice:/bin/bash
user:bob:1002:developer:/home/bob:/bin/zsh
error: failed to load /var/www/html/index.php at line 10
debug: checking memory limit 512 and timeout 30

old value is old and another old word
OLD case check with foo and bar
status: failed connection on port 8080
user:charlie:1003:guest:/home/charlie:/bin/sh
# End of file
EOF
```

Basic Substitution

1. Replace the first occurrence per line:  ``` sed 's/old/new/' file.txt  ```
2. Replace all occurrences globally: ``` sed 's/old/new/g' file.txt ``` 
3. Case-insensitive replacement: ``` sed 's/old/new/gi' file.txt ``` 
4. Replace only the 2nd occurrence on each line: ``` sed 's/old/new/2' file.txt ``` 
5. Replace from the 2nd occurrence to the end of the line: ``` sed 's/old/new/2g' file.txt ``` 
6. Use an alternate delimiter (helpful for file paths): ``` sed 's|/var/www|/srv/http|g' file.txt ``` 
7. Replace a word only on a specific line (e.g., line 5): ``` sed '5s/old/new/' file.txt ``` 
8. Replace a word within a line range (lines 10 to 20): ``` sed '10,20s/old/new/g' file.txt ``` 
9. Replace a word only on lines matching a pattern: ``` sed '/error/s/old/new/g' file.txt ``` 
10. Append text to matched patterns using &: ``` sed 's/[0-9]*/&px/g' file.txt ``` 

Deleting Lines

11. Delete a specific line (line 3): ``` sed '3d' file.txt ``` 
12. Delete the last line: ``` sed '$d' file.txt ``` 
13. Delete a range of lines (lines 2 through 5): ``` sed '2,5d' file.txt ``` 
14. Delete lines matching a pattern: ``` sed '/debug/d' file.txt ``` 
15. Delete all empty lines: ``` sed '/^$/d' file.txt ``` 
16. Delete lines starting with a comment (#): ``` sed '/^#/d' file.txt ``` 

Printing & Viewing

17. Print only a specific line (suppress default output with -n): ``` sed -n '5p' file.txt ``` 
18. Print a range of lines (lines 10 to 15): ``` sed -n '10,15p' file.txt ``` 
19. Print lines matching a pattern: ``` sed -n '/failed/p' file.txt ``` 
20. Print every 2nd line starting from line 1: ``` sed -n '1~2p' file.txt ``` 

Inserting, Appending & File Editing

21. Insert a line before line 4: ``` sed '4i\New Header Line' file.txt ``` 
22. Append a line after line 4: ``` sed '4a\New Footer Line' file.txt ``` 
23. Edit a file in-place : ``` sed -i 's/foo/bar/g' file.txt ``` 
24. Edit in-place and create a backup file: ``` sed -i.bak 's/foo/bar/g' file.txt ``` 
25. Run multiple commands at once using -e: ``` sed -e 's/a/A/g' -e 's/b/B/g' file.txt ``` 
