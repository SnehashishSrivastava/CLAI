BINARIES_ALLOWLIST = {
    "bash", "sh",
    "find", "grep", "rg", "awk", "sed",
    "ls", "cat", "head", "tail", "wc",
    "du", "df", "cut", "sort", "uniq", "xargs", "printf", "echo",
}

DENY_KEYWORDS = {" rm ", " mkfs", " dd ", " shutdown", " reboot", ":(){:|:&};:"}
