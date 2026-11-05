# Static Code Analysis Issues Report — Car Rental System

**Student Name:** Dharshini V  
**SRN:** PES1UG24AM428  
**Department:** Computer Science & Engineering (AIML), PES University  
**Subject:** Software Engineering Lab (SE Lab) — Lab 5: Static Code Analysis  
**Repository:** `https://github.com/SETAPESU26/L5_56_car-rental`  
**File Analyzed:** `car_rental.py`

---

## 📊 Summary of Tools Used

1. **Bandit (v1.9.4)**: Security vulnerability scanner for Python.
   - Initial run detected **11 issues** (2 High Severity, 4 Medium Severity, 5 Low Severity).
   - Final run detected **0 issues** (100% clean).
2. **Pylint (v4.1.3)**: Code quality, complexity, logic bug, and convention checker.
   - Initial code rating: **4.94 / 10.00**.
   - Final code rating: **10.00 / 10.00** (Perfect score).
3. **Flake8 (v7.5.0)**: PEP 8 style, syntax, and formatting linter.
   - Initial run detected **25 violations** (unused imports, line length violations, bare except, missing blank lines, comparison to True).
   - Final run detected **0 violations** (100% clean).

---

## 📋 Documented Issues and Remediation Table

| Issue | Type | Tool | Line(s) | Severity | Description | Fix Approach |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **SQL Injection in Customer Registration** | Security (CWE-89) | Bandit (B608) | 23 | **Medium** | Raw string formatting (`'%s', '%s', '%s'` % ...) allowed malicious inputs to break SQL syntax or inject arbitrary commands into SQLite. | Converted to parameterized query `INSERT INTO customers VALUES (?, ?, ?)` with tuple binding. |
| **SQL Injection in Customer Lookup** | Security (CWE-89) | Bandit (B608) | 26 | **Medium** | String concatenation (`"WHERE name = '" + name + "'"`) permitted SQL injection bypasses (e.g. `' OR '1'='1`). | Used parameterized query `SELECT * FROM customers WHERE name = ?` passing `(name,)` parameter. |
| **Arbitrary Code Execution via `exec`** | Security (CWE-78) | Bandit (B102), Pylint (W0122) | 53 | **Medium** | Promotional discounts were evaluated using Python's `exec()` on untrusted input strings, allowing arbitrary system command execution. | Removed `exec()`. Replaced with safe regex pattern matching for percentage discounts and multiplier calculations. |
| **Weak Cryptographic Hash (SHA-1)** | Security (CWE-327) | Bandit (B324) | 48 | **High** | Used cryptographically broken SHA-1 hashing algorithm to store driver's licence identifiers. | Upgraded to secure `hashlib.sha256()` with explicit UTF-8 encoding. |
| **Insecure Temporary File Creation** | Security (CWE-377) | Bandit (B306) | 63 | **Medium** | `tempfile.mktemp()` is deprecated and vulnerable to race conditions (TOCTOU attacks) where an attacker can replace the file before creation. | Replaced with secure `tempfile.NamedTemporaryFile(..., delete=False)` with context management. |
| **Permissive File Permissions (0o777)** | Security (CWE-732) | Bandit (B103) | 67 | **High** | Receipt text files were chmodded with `0o777` (world-readable, world-writable), allowing any system user to tamper with booking receipts. | Restricted permissions to owner-only read/write (`0o600`) using `os.chmod(path, 0o600)`. |
| **Hardcoded Admin Password & Credentials** | Security (CWE-259) | Bandit (B107, B105) | 70-71 | **Low** | Hardcoded default admin password `'admin@rent'` in the function signature and comparison statement. | Removed hardcoded default parameter; retrieved credentials from environment variables using `secrets.compare_digest`. |
| **Mutable Default Argument (`features=[]`)** | Bug / Quality | Pylint (W0102) | 16 | **Medium** | Default list `features=[]` is evaluated once at function definition time, meaning all vehicles without explicit features shared the exact same list instance in memory. | Changed default to `features=None` and initialized a new list per vehicle (`features = list(features) if features is not None else []`). |
| **Bare `except:` Clause & Suppressed Errors** | Bug / Quality | Pylint (W0702), Flake8 (E722), Bandit (B110) | 41-42 | **Low** | Bare `except:` caught and silenced all exceptions including `KeyboardInterrupt` and `SystemExit`, causing unknown car returns to fail silently with `None`. | Caught specific `KeyError` and implemented consistent return integer values. |
| **Inconsistent Return Statements** | Bug / Quality | Pylint (R1710) | 16, 36 | **Medium** | Functions returned an expression on one branch and implicitly returned `None` on another. | Ensured explicit return types for all code paths (`return None` or integer return). |
| **Simplifiable Boolean & Singleton Comparison** | Style / Quality | Pylint (R1703, C0121), Flake8 (E712) | 57, 78 | **Low** | Redundant `if match: return True else: return False` and comparison `fleet[p]["available"] == True`. | Simplified to `return bool(match)` and dictionary comprehension checking truthiness `if data.get("available")`. |
| **Naming Conventions & Docstrings** | Style / Maintainability | Pylint (C0103, C0114, C0116) | Module | **Low** | CamelCase function names (`addCar`, `rentCar`), missing module docstring, and missing function docstrings. | Renamed functions to PEP 8 standard `snake_case`, added comprehensive docstrings, and provided backward-compatible aliases. |
| **PEP 8 Formatting & Line Lengths** | Style | Flake8 (E501, E302, E305, F401) | Multiple | **Low** | Lines exceeding 79 characters, missing double blank lines between functions, and unused import `json`. | Formatted lines under 79 characters, removed unused imports, and ensured standard function spacing. |
