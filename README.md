# CaVa

![Python](https://img.shields.io/badge/Python-3.13+-blue.svg)
![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey.svg)

**CaVa (Case Vault)** is a secure, offline-first investigation and case management application designed for the storage, organisation, and management of sensitive investigative information.

The project is being developed as a desktop application with a strong emphasis on privacy, data ownership, encryption, auditability, and operational security.

---

## Overview
CaVa provides investigators, analysts, researchers, and intelligence professionals with a local-only environment in which they can manage:

* Cases and case metadata
* Notes and research session records
* Attachments and secure evidence files
* Person profiles linked to cases
* Related case links and investigation networks
* Audit logs and action tracking

All information is intended to remain under the direct control of the user, with no cloud services, telemetry, or external dependencies required during operation.

---

## Design Philosophy

CaVa is built around five core principles:

### Security First
Sensitive information should remain protected at rest and inaccessible without proper authentication.

### Offline By Default
CaVa is designed to operate entirely without an internet connection.

### Data Ownership
Users retain complete ownership and control of their investigative data.

### Auditability
Actions performed within the application should be traceable and verifiable through secure audit records.

### Simplicity
The application should remain intuitive and easy to use without sacrificing security.

---

## Features

### Case Management
* Create and manage investigations in a secure local vault
* Store and update case metadata, status, location, suspect, victim, and category
* Link related cases to build investigation networks
* Bundle case actions into a dedicated Case Actions dialog for save/export/delete workflows

### Notes & Research
* Create, edit, and delete case-linked notes
* Preview notes inline in the case editor
* Group note actions into a compact Notes dialog for a cleaner editor layout
* Track research sessions and record session actions

### Attachments & Evidence
* Add and remove attachments directly from the case editor
* Support for files, documents, images, and other evidence attachments
* Attachment list refreshes immediately after changes
* Group attachment management into a dedicated Attachments dialog

### Person Profiles
* Store person profiles associated with a case
* Capture name, association type, role, contact details, and description
* Manage case-linked people through a dedicated Person Profiles dialog

### Related Cases & Session Control
* Maintain links between related cases
* View and manage related cases in the case editor
* Start and end research sessions while preserving case context
* Track session actions for improved workflow auditability

### Audit Logging
* User activity tracking and audit records
* Tamper-evident audit entries for key actions
* Reviewable history for investigation workflows

### Security Features
* Password-protected vault access
* Encryption of stored data
* Secure key derivation
* Encrypted audit records
* Offline-first operation with no cloud telemetry

---

## Current Development Status

CaVa is currently under active development.

The current prototype includes:

* Secure login and vault initialization
* Dashboard interface with case search and selection
* Case editor with metadata, notes, attachments, related cases, person profiles, and session controls
* Dialog-based workflow grouping for notes, attachments, case actions, profiles, and related cases
* Encrypted vault key derivation with a Windows-friendly SQLite payload encryption fallback
* Audit logging and session action tracking

The current implementation does not yet include full cloud sync, versioned evidence tracking, or a complete revision history UI.

---

## Technology Stack

| Component           | Technology                   |
| ------------------- | ---------------------------- |
| Language            | Python 3                     |
| GUI Framework       | PySide6                      |
| Cryptography        | cryptography                 |
| Key derivation      | argon2-cffi                  |



---
&nbsp;
# CaVa `Python`

This repository is intended to be run directly from source using Python 3.

---

## Python Project Structure

```text
CaVa/
│
├── assets/
│
├── data/
│   └── config.py
│
├── ui/
│   ├── audit.py
│   ├── case_profiles.py
│   ├── dashboard.py
│   ├── editor.py
│   ├── login.py
│   ├── note_editor.py
│   ├── settings.py
│   └── audit.py
│
├── vault/
│   ├── auth.py
│   ├── crypto.py
│   ├── db.py
│   └── storage.py
│
├── License.txt
│
├── main.py
│
└── requirements.txt

```

---

## Installation

Create a virtual environment:

```bash
python -m venv venv
```

Activate the environment:

### Windows

```bash
venv\Scripts\activate
```

### Linux

```bash
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

> Note: `pysqlcipher3` is not required for the default Windows-friendly build. CaVa uses standard SQLite plus application-layer encryption via `cryptography` by default. Install `pysqlcipher3` separately only if you want SQLCipher-backed database encryption.

Launch the application:

```bash
python main.py
```



---
&nbsp;
# CaVa `Installer`

This installer has been created for CaVa on Windows.

## Installer

- `CaVa_Setup_V_1_3_0.exe` is the generated Windows installer package.

## Expected Behavior

When run, the installer should:

1. Display the CaVa setup wizard.
2. Install the packaged application files into the chosen destination folder.
3. Optionally create desktop and Start menu shortcuts.
4. Register `CaVa.exe` as the installed application launcher.

## Notes

- The installer bundle is intended for Windows users who want a standard installation experience.
- The installer does not require source Python to be installed on the target machine.

## Troubleshooting

If the installer fails:

- Verify the target machine is running a supported Windows version.
- Ensure any antivirus or endpoint protection is not blocking the installer.
- Rebuild the PyInstaller executable before regenerating the installer to ensure the latest application binary is included.
- If all other troubleshooting has not resolved the issue, then contact oakshiftsoftware@gmail.com for additional support



---
&nbsp;
# Additional

## Error Codes

When an authentication or vault operation fails, CaVa displays an error code to help diagnose the issue.

| Code | Meaning |
| ---- | ------- |
| E100 | Vault already initialized |
| E101 | Vault not initialized |
| E102 | Incorrect password |
| E103 | Argon2 library unavailable |
| E104 | Failed to derive encryption key |
| E199 | General failure |

---

## Security Notice

CaVa is designed to provide strong protection for locally stored information; however, no software can guarantee absolute security.

The security of stored information depends on numerous factors including:

* Password strength
* Host operating system security
* Physical device security
* User operational practices

Users should follow appropriate operational security procedures when handling sensitive information.

---

## Contributing

This project is currently in early development and contribution guidelines may change as the architecture matures.

---

## License

License information can be found in the `License.txt` file.

---

## Disclaimer

CaVa is intended to assist with the organisation and management of investigative information.

Users remain responsible for ensuring compliance with all applicable local and international laws, regulations, organisational policies, and data protection requirements relevant to their jurisdiction and use case.

---

## Planned Features

Upcoming planned features include, but are not limited to:

- Enhanced Settings - Including the ability to change and edit your `Organisation` after initialisation.
- Research Sessions - Every action performed during a `Research Session` would be logged and timestamped, and when the `Research Session` is ended CaVa would generate a `Research Entry` within the specified case (shown in a timeline format).
- Case Functionality Expansion - Introduction of person `Profiles`, `locations`, `Evidence` and a drag and drop `Timeline` for `Key Events` worth noting within a Case. The idea being that linked and timelined items would make case analysis easier and simpler.