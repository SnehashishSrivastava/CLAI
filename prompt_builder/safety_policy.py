SAFETY_POLICY = {
    "limits": {
        "cpu_seconds": 20,
        "memory_mb": 512,
        "network": False,
        "file_write": False,  # default read-only
    },
    "deny_keywords": [
        " rm ", " mkfs", " dd ", " shutdown", " reboot", ":(){:|:&};:"
    ],
}
