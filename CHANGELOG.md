# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2025-02-11

### Added

- DOCUMENTATION_ANALYSIS.md - Comprehensive documentation audit report
- hvac library upgraded from 1.1.0 to 2.3.0 (backward compatible)
- Python 3.14 compatibility confirmed
- Enhanced .env.example with detailed Vault configuration comments
- Modernized setup.sh and teardown.sh with improved error handling
- markdownlint configuration for consistent documentation formatting

### Changed

- **Updated requirements.txt**: All dependencies brought up to current stable versions
  - hvac: 1.1.0 → 2.3.0
  - pycryptodome: 3.17 → 3.23.0
  - certifi: 2022.12.7 → 2025.4.26
- Modernized Docker Compose commands: `docker-compose` → `docker compose`
- Updated VERSION_ANALYSIS.md to reflect completed hvac 2.x migration
- Removed outdated API migration warnings

### Fixed

- Corrected misleading version information in VERSION_ANALYSIS.md
- Fixed Python version discrepancy between Pipfile (3.13) and actual environment (3.14.2)

### Technical Details

- **hvac 2.x Migration**: Successfully tested with existing codebase
  - No breaking changes encountered
  - Transform FPE continues to work with existing `transformation` parameter
  - Vault Transit encryption fully compatible
- **Python Environment**: Tested on Python 3.13+ and 3.14.2

## [1.0.0] - 2024-07-XX

### Added

- Comprehensive README.md with improved structure and navigation
- Table of contents for easy access to all sections
- ASCII architecture diagrams showing encryption/decryption flows
- Detailed Quick Start guide with step-by-step instructions
- USER_GUIDE.md with step-by-step walkthroughs
- Expanded demo scenarios with expected outputs and key insights
- Troubleshooting section with common issues and solutions
- Security Considerations section with production deployment checklist
- CLAUDE.md with project-specific guidance for Claude Code

### Changed

- Improved documentation clarity and professionalism
- Enhanced demo instructions with numbered steps
- Added visual hierarchy with better section organization
- Fixed typos and improved explanations throughout
- Added code examples and sample outputs for all demos

### 1.0.0 Technical Details

- README.MD expanded from ~130 lines to 670 lines
- Added comprehensive coverage of:
  - Per-field encryption using Vault Transform and Transit engines
  - Envelope encryption pattern for large payloads
  - Key rotation demonstrations
  - Platform compatibility beyond Kafka
  - Production deployment best practices
