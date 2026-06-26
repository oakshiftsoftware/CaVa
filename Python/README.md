# CaVa

**CaVa (Case Vault)** is a secure, offline-first investigation and case management application designed for the storage, organisation, and management of sensitive investigative information.

The project is being developed as a desktop application with a strong emphasis on privacy, data ownership, encryption, auditability, and operational security.

---

## Overview

CaVa provides investigators, analysts, researchers, and intelligence professionals with a local-only environment in which they can manage:

* Cases
* Notes
* Documents
* Evidence records
* Attachments
* Audit logs
* Investigative timelines

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

## Planned Features

### Case Management
* Create and organise investigations
* Categorise cases by status
* Link related cases together
* Store case metadata

### Secure Notes
* Rich-text note editor
* Case-linked notes
* Searchable content
* Revision history

### Document Storage
* Secure document management
* Optional encrypted storage
* Metadata protection

### Evidence Management
* Attachment support
* Images
* PDFs
* Audio files
* Video files
* Digital evidence records

### Audit Logging
* User activity tracking
* Tamper-evident audit records
* Historical event review

### Security Features
* Password-protected vault access
* Encryption of stored data
* Automatic session locking
* Secure key derivation
* Encrypted audit records

---

## Current Development Status

CaVa is currently under active development.

The current prototype includes:

* Application framework
* Separate login / initialization dialog
* Dashboard interface
* Case management with metadata, notes, and files
* Encrypted vault key derivation with a Windows-friendly SQLite payload encryption fallback
* Audit logging support

The current implementation does not yet include full cloud sync, versioned evidence tracking, or a complete revision history UI.

---

## Technology Stack

| Component           | Technology                   |
| ------------------- | ---------------------------- |
| Language            | Python 3                     |
| GUI Framework       | PySide6                      |
| Cryptography        | cryptography                 |
| Key derivation      | argon2-cffi                  |

## Error Codes

The current prototype uses a small set of vault authentication error codes:

| Code | Meaning |
| ---- | ------- |
| E100 | Vault already initialized |
| E101 | Vault has not been initialized |
| E102 | Incorrect password |
| E103 | Argon2 is not available; install `argon2-cffi` |
| E104 | Unable to derive vault key |
| E199 | General failure or unexpected error |

| Password Derivation | Argon2                       |
| Storage             | SQLite with optional application-layer payload encryption |
| Formatting          | Black                        |

---

## Project Structure

```text
CaVa/
│
├── assets/
│
├── data/
│   └── config.py
│
├── ui/
│   ├── dashboard.py
│   ├── editor.py
│   ├── login.py
│   ├── note_editor.py
│   └── settings.py
│
├── vault/
│   ├── auth.py
│   ├── crypto.py
│   ├── db.py
│   └── storage.py
│
├── main.py
│
├── README.md
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

License information will be defined prior to public release.

---

## Disclaimer

CaVa is intended to assist with the organisation and management of investigative information.

Users remain responsible for ensuring compliance with all applicable local and international laws, regulations, organisational policies, and data protection requirements relevant to their jurisdiction and use case.
