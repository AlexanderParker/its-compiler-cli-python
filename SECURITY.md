# Security Policy

## Supported Versions

We actively support the following versions with security updates:

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |

## Reporting a Vulnerability

We take security vulnerabilities seriously. If you discover a security issue, please follow these steps:

### 1. Do Not Create a Public Issue

Please do not report security vulnerabilities through public GitHub issues, discussions, or pull requests.

### 2. Report Privately

Send details to: **pypi-security@parker.im**

Include:
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Any suggested fixes (if you have them)

### 3. Response Timeline

- **Initial Response**: Within 7 days
- **Status Update**: Within 2 weeks
- **Resolution**: Depends on severity and complexity

## Security Dependencies

This CLI tool is a thin wrapper around the [its-compiler-python](https://github.com/alexanderparker/its-compiler-python) core library. The majority of security validation and protection is handled by the core library.

**Important**: Security vulnerabilities in the core library directly affect this CLI. Always keep both packages updated.

## Security Updates

Security updates will be:
- Released as patch versions (e.g., 1.0.1)
- Announced in [GitHub Security Advisories](https://github.com/alexanderparker/its-compiler-cli-python/security/advisories)
- Coordinated with core library updates when applicable

## Acknowledgments

We appreciate security researchers who responsibly disclose vulnerabilities. Contributors will be acknowledged in our security advisories (unless they prefer to remain anonymous).
