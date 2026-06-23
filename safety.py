import re

# Patterns that suggest a user is trying to override bot instructions
INJECTION_PATTERNS = [
    r"ignore (previous|your|all) instructions",
    r"(developer|dev) mode",
    r"jailbreak",
    r"\bDAN\b",
    r"you are now",
    r"pretend (you are|to be)",
    r"act as (if|though)",
    r"override (your|the) (instructions|system|prompt)",
    r"(new|different) (system )?prompt",
    r"forget (everything|your instructions|your guidelines)",
    r"disregard (your|all|previous)",
]

# Patterns that suggest the LLM response has been compromised
COMPROMISE_PATTERNS = [
    r"i have been (pawned|hacked|jailbroken|compromised)",
    r"i (will|am going to) ignore (my )?(instructions|guidelines|rules)",
    r"without (any )?(restrictions|limitations|guidelines)",
    r"i('ve| have) been (freed|unleashed|liberated)",
    r"(developer|dev) mode (activated|enabled|on)",
    r"i am now (a )?(?!wolfie|the clan bot)",
    r"i no longer (have|follow|obey)",
    r"my (true|real|actual) (self|purpose|goal) is",
]


def is_injection_attempt(text):
    """Return True if the message contains known prompt injection patterns."""
    lower = text.lower()
    return any(re.search(pattern, lower) for pattern in INJECTION_PATTERNS)


def is_safe_output(text):
    """Return True if the bot response does not contain compromise markers."""
    lower = text.lower()
    return not any(re.search(pattern, lower) for pattern in COMPROMISE_PATTERNS)
