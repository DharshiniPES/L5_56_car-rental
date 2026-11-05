# Lab 5: Static Code Analysis — Reflection Report

**Student Name:** Dharshini V  
**SRN:** PES1UG24AM428  
**Department:** Computer Science & Engineering (AIML), PES University  
**Subject:** Software Engineering Lab (SE Lab) — Lab 5  
**Assigned Project:** Car Rental System (`car_rental.py`)  

---

### Question 1: Differences in Tool Capabilities & Complementary Roles
**How do the findings of Pylint, Bandit, and Flake8 differ in terms of their scope, and how do they complement one another in a modern software engineering pipeline?**

* **Bandit (Security Specialist):** Bandit performs abstract syntax tree (AST) analysis focused purely on common security vulnerabilities (CWE catalog). It identified critical security hazards that neither Pylint nor Flake8 flagged, such as:
  - SQL injection vectors through raw string formatting in database queries (`B608`).
  - Insecure and deprecated temporary file generation via `tempfile.mktemp()` (`B306`), which is susceptible to race conditions.
  - World-writable file permissions `0o777` (`B103`).
  - Weak cryptographic hashing using SHA-1 (`B324`).
* **Pylint (Code Quality, Bugs & Complexity):** Pylint checks for design flaws, logic bugs, code smells, and structural anti-patterns that do not necessarily violate syntax or security rules. For example, Pylint flagged:
  - The infamous mutable default argument `features=[]` (`W0102`), where a single shared list is mutated across multiple function calls.
  - Inconsistent return statements (`R1710`), where some execution branches returned values while others fell through to implicit `None`.
  - Simplifiable boolean expressions (`R1703`) and dictionary iteration antipatterns (`C0206`).
* **Flake8 (Grammar & Style Enforcement):** Flake8 enforces PEP 8 layout, syntactic conventions, and dead code cleanup with minimal runtime overhead. It quickly flagged:
  - Unused library imports (`json` - `F401`).
  - Line-length violations exceeding PEP 8 limits (`E501`).
  - Deficient blank line spacing between top-level definitions (`E302`, `E305`).
  - Bad singleton comparisons (`== True` vs `is True` or truthiness - `E712`).

**Complementary Integration:** No single tool provides complete coverage. In a professional CI/CD pipeline, Flake8 runs first as a fast gatekeeper for formatting, Pylint enforces algorithmic quality and design standards, and Bandit acts as a specialized security barrier to prevent vulnerabilities from reaching production.

---

### Question 2: Severity and Prioritization of Findings
**Why is it vital to prioritize Bandit's high- and medium-severity findings over style/formatting warnings from Flake8? What would be the real-world impact of the issues found in `car_rental.py`?**

In software development, technical debt and defects follow a risk hierarchy. Formatting issues (such as an 85-character line or a missing blank line) cause minor friction in code readability but do not compromise system integrity, availability, or customer data. In contrast, Bandit findings represent active threat vectors:

1. **SQL Injection (`B608`):** The unescaped customer query allowed any user to input `' OR '1'='1` and dump the complete customer registry (names, driver's licence IDs, phone numbers) in plain text. In a production environment, this constitutes a severe data breach violating data privacy regulations (e.g., GDPR, DPDP Act), resulting in massive legal liabilities and reputational damage.
2. **Arbitrary Code Execution via `exec()` (`B102`):** The `applyPromo` function took a raw string from staff/input and passed it directly to `exec()`. An attacker or malicious user could submit `__import__('os').system('rm -rf /')` or open a reverse shell, compromising the host server entirely.
3. **World-Writable Receipts (`0o777` - `B103`):** Granting read/write/execute permissions to all system users allows unauthorized local processes or compromised system accounts to alter booking charges, tamper with invoices, or inject malicious payloads.

Therefore, security findings must always be prioritized and resolved before addressing stylistic linting.

---

### Question 3: False Positives, False Negatives, and Limitations of Static Analysis
**What are the limitations of static code analysis? Did you observe bugs or edge cases in `car_rental.py` that static analysis tools failed to catch?**

Static analysis tools examine code statically without runtime context, which leads to both false negatives (undetected domain bugs) and false positives:

* **Semantic Domain Bugs Missed by Tools (False Negatives):**
  1. **Negative Rental Pricing:** In `car_rental.py`, line 88 added a Nexon with `daily_rate = -500`. No static analysis tool flags this because negative integers are syntactically valid numbers. However, renting this car calculated a negative total cost, effectively paying the customer instead of charging them!
  2. **Inverted Date Logic:** Renting the Innova from `"2026-11-10"` to `"2026-11-07"` resulted in `days = -3` and a negative billing amount of `-9000`. Static analyzers cannot infer that a rental start date must precede the end date.
  3. **Fleet Concurrency / Availability Bug:** The original code rented the same vehicle ("Swift") twice on overlapping dates without checking if `fleet[plate]["available"]` was already `False` or flipping the flag.
* **Limitations:** Static analysis cannot verify business rules, transactional correctness, or dynamic runtime inputs. Comprehensive automated unit testing, integration tests, and manual peer reviews remain indispensable alongside static analysis.

---

### Question 4: Incorporating Static Analysis into the SDLC
**How would you automate and integrate static code analysis into a modern software team's daily development workflow to maintain high code quality continuously?**

To prevent issues from ever reaching the mainline repository, static analysis should be integrated into multiple layers of the Software Development Life Cycle (SDLC):

1. **Local Pre-Commit Hooks (`pre-commit` framework):**
   - Developers configure `.pre-commit-config.yaml` to run `flake8` and lightweight formatters (`black`, `isort`) automatically whenever `git commit` is executed.
   - Commits with syntax errors, unused imports, or bad formatting are rejected locally before code leaves the developer's workstation.
2. **Pull Request CI/CD Workflows (GitHub Actions / GitLab CI):**
   - On every pull request, an automated workflow executes:
     ```yaml
     - name: Run Flake8
       run: flake8 .
     - name: Run Pylint
       run: pylint --fail-under=9.5 src/
     - name: Run Bandit
       run: bandit -r src/ -ll -ii
     ```
   - Pull requests that introduce high-severity security vulnerabilities or drop the Pylint score below 9.5 are blocked from merging into `main`.
3. **Security Dashboards & Dependency Scanning:**
   - Periodic scheduled scans (e.g., SonarQube, GitHub CodeQL, Snyk) track technical debt trends, flag newly disclosed vulnerabilities in third-party libraries, and ensure long-term maintainability.
