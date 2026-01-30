# Changelog

All notable changes to this project will be documented in this file.

## [3.0.0] - 2026-01-25

### 🎉 Major Release: Commit SHA-Based Tracking

#### Added
- **Commit SHA tracking**: Precise change detection based on commit SHA instead of `pushed_at` timestamps
- **Commit metadata**: Full commit information including SHA, message, author, and date
- **Organization labels**: Notifications now show which organization each change belongs to
- **Rich notifications**: Enhanced notification format with commit details
- **Test suite**: Added comprehensive test scripts for validation
  - `test_commit_tracking.py` - Validates commit info retrieval
  - `test_change_detection.py` - Validates change detection logic

#### Changed
- **State file format**: Now stores `last_commit` object instead of `pushed_at` timestamp
- **GitHub API usage**: Increased from 1 to ~32 requests per check cycle
- **Notification format**: Now displays commit SHA, message, and author
- **Change detection logic**: Now compares commit SHAs for accurate detection

#### Improved
- **Accuracy**: Eliminated false positives from non-commit operations (releases, tags, etc.)
- **Information richness**: Users now see exactly what changed and who made the change
- **Traceability**: Each notification provides full commit context
- **Multi-org support**: Organization name displayed in notifications

#### Documentation
- Added `COMMIT_SHA_IMPLEMENTATION_REPORT.md` - Detailed technical implementation report
- Added `UPGRADE_GUIDE.md` - Step-by-step upgrade instructions
- Updated `README.md` - Reflects new features and requirements
- Added `CHANGELOG.md` - This file

#### Breaking Changes
- State file format changed - old state files need to be cleared on upgrade
- **GitHub Token now strongly recommended** (not optional) due to increased API usage
- Without token: Rate limit of 60/hour is insufficient for commit tracking

#### Migration Path
See [UPGRADE_GUIDE.md](UPGRADE_GUIDE.md) for detailed upgrade instructions.

---

## [2.0.0] - 2026-01-25

### Fixed
- Fixed duplicate notification issue caused by rate limits
- Repos now saved to state even when commit fetch fails
- Prevents false "new repository" notifications

### Changed
- Always save repository info regardless of commit fetch success
- Improved error handling for rate limit scenarios

---

## [1.0.0] - 2026-01-24

### Initial Release
- GitHub organization monitoring
- HuggingFace organization monitoring
- Multi-organization support
- WeChat Work notifications
- Docker deployment
- YAML configuration
- State persistence
- Change detection based on `pushed_at` timestamps
