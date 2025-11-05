# PhishSim360 — Phishing Awareness Simulator (ETHICAL USE ONLY)

**Status:** Demo / Educational  
**IMPORTANT:** This repository is intended **only** for lawful, ethical use: internal security training, consented red-team exercises, or academic research with explicit written permission from all affected parties. **Do not** use this project to send real phishing emails to uninformed or non-consenting recipients.

---

## Table of contents
- [Overview](#overview)  
- [Features (Safe / Demo)](#features-safe--demo)  
- [Architecture](#architecture)  
- [Quick start (Demo Mode)](#quick-start-demo-mode)  
- [Configuration and Safety Controls](#configuration-and-safety-controls)  
- [Usage Scenarios (Ethical)](#usage-scenarios-ethical)  
- [What NOT to do](#what-not-to-do)  
- [Contributing](#contributing)  
- [Legal & Ethical Notice](#legal--ethical-notice)  
- [Credits & License](#credits--license)

---

## Overview
**Phish-Aware** is a *simulator* designed to help security teams and educators build phishing awareness programs in a controlled, auditable way. It includes modules to:

- generate mock email templates (HTML) for training,
- build campaigns using CSV test lists,
- simulate delivery in **demo (dry-run)** mode and produce reports,
- integrate with logging/telemetry for analysis.

**This repo intentionally disables/omits instructions to send unsolicited real emails.** Any functionality capable of sending real mail is restricted behind explicit configuration flags, and should only be enabled after legal review and written consent from the target organization.

---

## Features (Safe / Demo)
- Create campaigns from CSV input (names, emails, departments) — **demo simulation only**.  
- Generate sample HTML email templates and view saved email bodies in `sent_emails/`.  
- AI image generation support for benign training visuals (optional).  
- Scheduler for recurring demo campaign runs (simulated only).  
- Reporting view that reads example click/log events (mocked).  
- Dry-run mode that writes output files but never attempts to connect to SMTP by default.

---

## Architecture
- `app.py` — Flask web app (demo and simulation UI).  
- `uploads/` — uploaded CSVs and assets.  
- `sent_emails/` — saved email bodies created during simulation (never actually sent).  
- `templates/` — Jinja2 templates for UI.  
- `requirements.txt` — Python dependencies.

> NOTE: The repository includes sample modules for generating email HTML and subjects. These are for training and visualization only.

---

## Quick start (Demo Mode)

> The default configuration runs the app in **demo** mode. Real SMTP sending is disabled unless you explicitly and knowingly reconfigure it for an authorized, legal test.

1. **Create a virtual environment**
```bash
python -m venv venv
source venv/bin/activate   # macOS / Linux
venv\Scripts\activate      # Windows
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Prepare demo CSV**  
Place a CSV in `uploads/` (example file `uploads/demo_list.csv`) with headers:
```csv
email,name,address,department
alice@example.com,Alice,Office 1,HR
bob@example.com,Bob,Office 2,Engineering
```
> Use only test or consented addresses.

4. **Run the app**
```bash
python app.py
```
Open `http://127.0.0.1:5000` in your browser.  
Use the UI to upload CSVs and run **demo** campaigns. The application will create HTML files under `sent_emails/` instead of sending real emails.

---

## Configuration and Safety Controls

The repository includes multiple safety mechanisms — please keep or strengthen these when deploying:

- **Demo / dry-run default**: SMTP send functionality is disabled by default. The app writes email bodies to `sent_emails/`.  
- **Explicit SMTP opt-in**: To enable SMTP you must:
  1. Have explicit written authorization.
  2. Update a single, clearly documented configuration file (do not commit credentials).
  3. Provide an environment variable `ENABLE_REAL_SEND=true`.  
- **No default credentials committed**: Remove or rotate any placeholder credentials before use.  
- **Logging & auditing**: All demo sends create logs. Keep audit trails of any real tests.  
- **Rate limits and guardrails**: Add limits to avoid accidental mass sends.  
- **Legal review required**: Always obtain legal approval and written consent from the organization and targets.

---

## Usage Scenarios (Ethical)
- Internal security training where targets are consenting employees who were notified ahead of, or have consented to, periodic exercises.  
- Classroom demonstration of common phishing tactics (safe examples, anonymized data).  
- Research and analysis into phishing detection strategies using synthetic datasets.  
- Red-team engagements where targets have provided documented, explicit authorization.

---

## What NOT to do
- Never use this project to send unsolicited emails to people who haven't consented.  
- Never deploy with SMTP credentials in source control.  
- Do not attempt to use this tool to impersonate or defraud organizations or individuals.  
- Do not use data obtained during simulations for anything other than training and research within legal boundaries.

---

## Contributing
Contributions are welcome for defensive, educational, and safety improvements:
- Add unit/integration tests.  
- Improve the demo templates to make simulated phishing more realistic for training without being malicious.  
- Add consent workflows and reporting to show which users have opted in/out.  
- Add anonymized sample datasets for training and detection model development.

Please open issues or PRs describing the ethical purpose and testing constraints for your changes.

---

## Legal & Ethical Notice (MUST READ)
This software can be dangerous if misused. Contributors and users must ensure:

1. They have explicit, **written authorization** from the organisation and any individuals targeted by a real campaign.  
2. Compliance with applicable local, national, and international laws and organizational policies.  
3. Notifications or opt-out mechanisms for participants where required.  
4. That the simulation cannot be used to harvest credentials in real environments.

The authors and maintainers are not responsible for misuse.

---

## Credits & License
- Built by: NGIT CG360  
- Libraries: Flask, Flask-SQLAlchemy, Flask-APScheduler, Pillow, requests, pandas, etc. (see `requirements.txt`)  
- License: Choose a license appropriate to your project (e.g., MIT) — include explicit restrictions in your `LICENSE` about prohibited uses if desired.
