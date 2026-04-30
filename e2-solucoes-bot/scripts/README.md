# E2 Bot - Scripts Repository

**Last Updated**: 2026-04-29
**Status**: ✅ Organized - Scripts archived by workflow and purpose

---

## 📋 Overview

This directory contains all scripts for the E2 Bot workflows including workflow generation scripts, fixes, deployment automation, testing, and utilities. Scripts are organized by workflow (WF02, WF05, WF06, WF07) and purpose for easy navigation.

**Total Files**: 304 scripts organized in 13 categories

---

## 📁 Directory Structure

```
scripts/
├── README.md                           This file - Organization guide
│
├── wf02/                               WF02 scripts (159 files)
│   ├── state-machines/                 State machine versions (25 files)
│   ├── generators/                     Workflow generators (82 files)
│   └── fixes/                          Fix scripts (52 files)
│
├── wf05/                               WF05 scripts (16 files)
│   ├── generators/                     Workflow generators (8 files)
│   └── fixes/                          Fix scripts (8 files)
│
├── wf06/                               WF06 scripts (1 file)
├── wf07/                               WF07 scripts (17 files)
│   ├── generators/                     Workflow generators (17 files)
│   └── fixes/                          Fix scripts (0 files)
│
├── deployment/                         Deployment scripts (4 files)
├── testing/                            Testing scripts (20 files)
├── validation/                         Validation scripts (16 files)
├── migration/                          Migration scripts (8 files)
├── utilities/                          Utility scripts (49 files)
├── evolution/                          Evolution API scripts (7 files)
├── docker/                             Docker scripts (4 files)
└── deprecated/                         Deprecated/broken scripts (3 files)
```

---

## 🎯 Organization Principles

### By Workflow
**Purpose**: Group scripts by workflow for easy workflow-specific script navigation and development

### By Purpose
**Purpose**: Separate scripts into logical categories:
- **state-machines**: Versioned state machine implementations (WF02 V76-V114)
- **generators**: Workflow generation and creation scripts
- **fixes**: Bug fix and correction scripts
- **deployment**: Deployment automation and task execution
- **testing**: Test creation, execution, and validation
- **validation**: Validation and verification scripts
- **migration**: Database migrations and version upgrades
- **utilities**: General-purpose utility scripts
- **evolution**: Evolution API management scripts
- **docker**: Docker container management scripts
- **deprecated**: Obsolete or broken scripts (preserved for reference)

**Maintenance**: Add new scripts to appropriate workflow and purpose subdirectories

---

## 📊 Category Descriptions

### wf02/ (159 files total)
**Content**: WF02 AI Agent Conversation scripts
**Organization**: Three categories - state-machines, generators, fixes

#### wf02/state-machines/ (25 files)
**Timeline**: State machine versions V76-V114
**Key Scripts**:
- wf02-v76-state-machine-proactive-ux.js (V76 - Proactive UX foundation)
- wf02-v77-loop-fix.js (V77 - Loop fix)
- wf02-v78-state-machine-*.js (V78 - Multiple iteration attempts)
- wf02-v80-state-machine-complete.js (V80 - Complete states + WF06)
- wf02-v89-90-91-state-machine-*.js (V89-V91 - Refactored + state initialization)
- wf02-v104-database-state-update-fix.js (V104 - State sync) ⭐
- wf02-v111-build-sql-queries-row-locking.js (V111 - Database row locking) ⭐⭐⭐
- wf02-v113-build-update-queries1-wf06-next-dates.js (V113 - Date suggestions) ⭐
- wf02-v113-build-update-queries2-wf06-available-slots.js (V113 - Slot suggestions) ⭐
- wf02-v114-slot-time-fields-fix.js (V114 - PostgreSQL TIME fields) ⭐⭐⭐

#### wf02/generators/ (82 files)
**Timeline**: V70-V114 workflow generation scripts
**Key Scripts**:
- generate-workflow-wf02-v70-v79-*.py (Early versions)
- generate-workflow-wf02-v80-v99-*.py (Complete states + WF06 integration)
- generate-workflow-wf02-v100-v114-*.py (Recent versions with critical fixes)
- generate-workflow-v*.py (Versioned generators)

#### wf02/fixes/ (52 files)
**Timeline**: V63-V114 bug fixes and corrections
**Key Fixes**:
- fix-workflow-01-*.py (WF01 integration fixes)
- fix-workflow-02-*.py (WF02 workflow fixes)
- fix-workflow-*.py (General workflow fixes)
- fix-empty-options-v78_1_4.py (V78.1.4 empty options fix)

### wf05/ (16 files total)
**Content**: WF05 Appointment Scheduler scripts
**Organization**: Two categories - generators, fixes

#### wf05/generators/ (8 files)
**Timeline**: V4-V7 appointment scheduler development
**Key Scripts**:
- generate-workflow-wf05-v4-*.py (V4 series - title, timezone fixes)
- generate-workflow-wf05-v5-process-env-fix.py (V5 - $env fix attempt)
- generate-workflow-wf05-v6-expression-env-fix.py (V6 - $env expression fix)
- generate-workflow-wf05-v7-hardcoded-values.py (V7 - Hardcoded final solution) ⭐

#### wf05/fixes/ (8 files)
**Timeline**: V3-V8 bug fixes
**Key Fixes**:
- fix-wf05-*.py (Environment variable and configuration fixes)
- Various $env access workarounds

### wf06/ (1 file)
**Content**: WF06 Calendar Availability Service scripts
**Key Scripts**:
- wf06-v2_1-calculate-slot-fix.js (V2.1 - Complete fix) ⭐

### wf07/ (17 files total)
**Content**: WF07 Send Email scripts
**Organization**: Single category - generators

#### wf07/generators/ (17 files)
**Timeline**: V2-V13 email service development
**Key Scripts**:
- generate-workflow-wf07-v2-wf05-integration.py (V2 - WF05 integration)
- generate-workflow-wf07-v3-complete-fix.py (V3 - Complete fix)
- generate-workflow-wf07-v4-v6-*.py (V4-V6 - Filesystem access attempts)
- generate-workflow-wf07-v8-v9-*.py (V8-V9 - HTTP Request approach)
- generate-workflow-wf07-v10-starttls.py (V10 - STARTTLS)
- generate-workflow-wf07-v11-service-name-fix.py (V11 - Service name fix)
- generate-workflow-wf07-v12-address-and-db-fix.py (V12 - Address + DB fix)
- generate-workflow-wf07-v13-insert-select.py (V13 - INSERT...SELECT pattern) ⭐

### deployment/ (4 files)
**Content**: Deployment automation scripts
**Timeline**: Deployment execution and task implementation
**Key Scripts**:
- deploy-*.sh, deploy-*.py (Deployment automation)
- task-v32-implementation.sh (Task implementation)

### testing/ (20 files)
**Content**: Testing and test creation scripts
**Timeline**: Workflow creation, test generation, validation
**Key Scripts**:
- test-*.sh (Test execution scripts)
- create-simple-test.py (Simple test creation)
- create-ultra-simple.py (Ultra-simple test)
- create-workflow-v2.py, create-workflow-v3-simple.py (Workflow creation tests)

### validation/ (16 files)
**Content**: Validation and verification scripts
**Timeline**: Workflow validation, execution verification
**Key Scripts**:
- validate-*.sh, validate-*.py (Validation scripts)
- Execution validation and health checks

### migration/ (8 files)
**Content**: Database migrations and version management
**Timeline**: Migration execution, rollback, version upgrades
**Key Scripts**:
- run-migration-*.sh (Migration execution)
- rollback-migration-*.sh (Migration rollback)
- recreate-postgres-*.sh (Database recreation)
- rollback-to-v2.sh, upgrade-v1-to-v2.sh (Version management)
- cleanup-duplicates.sql (Database cleanup)

### utilities/ (49 files)
**Content**: General-purpose utility scripts
**Timeline**: Workflow fixes, data handling, performance monitoring
**Key Scripts**:
- activate-workflows.sh (Workflow activation)
- clean-n8n-executions.sh (Execution cleanup)
- cleanup-n8n-api.py (API cleanup)
- fix-*.py, fix-*.sh (Various utility fixes)
- ingest-knowledge.sh, ingest-simple.sh (Knowledge ingestion)
- monitor-performance.sh (Performance monitoring)
- backup.sh, restore.sh (Backup/restore)
- health-check.sh (Health checking)
- start-*.sh, stop.sh, logs.sh (Service management)

### evolution/ (7 files)
**Content**: Evolution API management scripts
**Timeline**: Evolution API operations, fixes, cleanup
**Key Scripts**:
- evolution-*.sh (Evolution API operations)
- fix-evolution-*.sh (Evolution API fixes)
- update-evolution-*.sh (Evolution API updates)
- nuclear-cleanup-evolution.sh (Complete Evolution API reset)

### docker/ (4 files)
**Content**: Docker container management scripts
**Timeline**: Docker fixes, container cleanup
**Key Scripts**:
- fix-docker-*.sh (Docker fixes)
- force-remove-containers.sh (Container cleanup)
- ultimate-docker-fix.sh (Complete Docker reset)

### deprecated/ (3 files)
**Content**: Obsolete or broken scripts preserved for reference
**Timeline**: Historical scripts no longer in use
**File Types**:
- *.BROKEN (Broken scripts)
- DEPRECATED_* (Deprecated scripts)
- *.DO_NOT_USE (Scripts marked as unusable)
- *.tmp (Temporary files)

---

## 🔍 Quick Reference

### For Current Production Scripts

```bash
# WF02 V114 - Current production version scripts
cat scripts/wf02/state-machines/wf02-v114-slot-time-fields-fix.js

# WF02 V111 - Database row locking (CRITICAL)
cat scripts/wf02/state-machines/wf02-v111-build-sql-queries-row-locking.js

# WF02 V113 - WF06 suggestions persistence
cat scripts/wf02/state-machines/wf02-v113-build-update-queries1-wf06-next-dates.js
cat scripts/wf02/state-machines/wf02-v113-build-update-queries2-wf06-available-slots.js

# WF05 V7 - Production appointment scheduler generator
cat scripts/wf05/generators/generate-workflow-wf05-v7-hardcoded-values.py

# WF06 V2.1 - Production calendar service
cat scripts/wf06/wf06-v2_1-calculate-slot-fix.js

# WF07 V13 - Production email service generator
cat scripts/wf07/generators/generate-workflow-wf07-v13-insert-select.py
```

### For Historical Scripts

```bash
# Browse WF02 state machine evolution
ls -l scripts/wf02/state-machines/

# Browse WF02 generators
ls -l scripts/wf02/generators/

# Browse WF05 development history
ls -l scripts/wf05/generators/

# View specific script
cat scripts/wf02/generators/generate-workflow-wf02-v80-complete.py
```

---

## 📈 Statistics

**Total Files**: 304 scripts
- **WF02 Scripts**: 159 files (52% of total)
  - state-machines: 25 files (WF02 V76-V114)
  - generators: 82 files (V70-V114)
  - fixes: 52 files (V63-V114)
- **WF05 Scripts**: 16 files (5%)
  - generators: 8 files (V4-V7)
  - fixes: 8 files
- **WF06 Scripts**: 1 file (<1%)
- **WF07 Scripts**: 17 files (6%)
  - generators: 17 files (V2-V13)
- **Deployment**: 4 files (1%)
- **Testing**: 20 files (7%)
- **Validation**: 16 files (5%)
- **Migration**: 8 files (3%)
- **Utilities**: 49 files (16%)
- **Evolution API**: 7 files (2%)
- **Docker**: 4 files (1%)
- **Deprecated**: 3 files (1%)

**Organization Date**: 2026-04-29
**Current Production**: V1 (WF01 V2.8.3, WF02 V114, WF05 V7, WF06 V2.2, WF07 V13)

---

## 🎯 Key Production Scripts

### Critical Production Scripts ⭐⭐⭐

**WF02 V111 - DATABASE ROW LOCKING**:
- **File**: `wf02/state-machines/wf02-v111-build-sql-queries-row-locking.js`
- **Status**: CRITICAL fix for race conditions in concurrent message processing
- **Impact**: Prevents stale state processing and WF06 integration issues
- **Deployment**: docs/deployment/wf02/v100-v114/DEPLOY_WF02_V111_DATABASE_ROW_LOCKING.md

**WF02 V114 - POSTGRESQL TIME FIELDS**:
- **File**: `wf02/state-machines/wf02-v114-slot-time-fields-fix.js`
- **Status**: CRITICAL fix for PostgreSQL TIME column compatibility
- **Impact**: Enables proper appointment time storage and retrieval
- **Deployment**: docs/WF02_V114_QUICK_DEPLOY.md

### Important Production Scripts ⭐

**WF02 V113 - WF06 SUGGESTIONS PERSISTENCE**:
- **Files**:
  - `wf02/state-machines/wf02-v113-build-update-queries1-wf06-next-dates.js` (date_suggestions)
  - `wf02/state-machines/wf02-v113-build-update-queries2-wf06-available-slots.js` (slot_suggestions)
- **Status**: Critical fix for date_suggestions and slot_suggestions persistence
- **Impact**: Enables proper WF06 data storage and retrieval
- **Deployment**: docs/fix/wf02/v100-v114/BUGFIX_WF02_V113_1_WF06_SUGGESTIONS_PERSISTENCE.md

**WF02 V104 - STATE SYNC**:
- **File**: `wf02/state-machines/wf02-v104-database-state-update-fix.js`
- **Status**: State synchronization fix for infinite loop prevention
- **Impact**: Proper state synchronization between state machine and database
- **Deployment**: docs/deployment/wf02/v100-v114/DEPLOY_WF02_V104_2_BUILD_UPDATE_QUERIES_COMPLETE_FIX.md

**WF05 V7 - HARDCODED FINAL**:
- **File**: `wf05/generators/generate-workflow-wf05-v7-hardcoded-values.py`
- **Status**: Production solution for n8n $env access limitation
- **Impact**: Enables appointment scheduler production deployment
- **Deployment**: docs/deployment/wf05/DEPLOY_WF05_V7_HARDCODED_FINAL.md

**WF06 V2.1 - COMPLETE FIX**:
- **File**: `wf06/wf06-v2_1-calculate-slot-fix.js`
- **Status**: Complete fix for OAuth, empty calendar, input data source
- **Impact**: Enables WF06 production deployment with calendar integration
- **Deployment**: docs/deployment/wf06/DEPLOY_WF06_V2_1_COMPLETE_FIX.md

**WF07 V13 - INSERT SELECT**:
- **File**: `wf07/generators/generate-workflow-wf07-v13-insert-select.py`
- **Status**: Solution for n8n queryReplacement limitation
- **Impact**: Enables proper database logging with RETURNING clause
- **Deployment**: docs/fix/wf07/BUGFIX_WF07_V13_INSERT_SELECT_FIX.md

---

## 🎯 Script Usage Recommendations

### For Production Deployment
1. **Review production scripts**: Check current production version scripts in state-machines/ and generators/
2. **Follow deployment guides**: Use deployment documentation in docs/deployment/
3. **Test thoroughly**: Validate scripts in development environment before production
4. **Document changes**: Create deployment documentation for new script versions

### For Development
1. **Check generators**: Review generator scripts for workflow creation patterns
2. **Study fixes**: Understand fix scripts for bug resolution approaches
3. **Follow versioning**: Maintain version naming convention (v##-description)
4. **Test incrementally**: Create test scripts for validation before deployment

### For Troubleshooting
1. **Review fix scripts**: Check fix/ directories for similar issue resolutions
2. **Check utilities**: Use utility scripts for common troubleshooting tasks
3. **Validate state**: Use validation scripts to verify system state
4. **Check migrations**: Review migration scripts for database state management

---

## 🔗 Cross-References

### By Script Type
- **State Machines**: WF02 state-machines/ (V76-V114 evolution)
- **Generators**: WF02, WF05, WF07 generators/ (workflow creation)
- **Fixes**: WF02, WF05 fixes/ (bug resolution)
- **Testing**: testing/ (test creation and execution)
- **Validation**: validation/ (verification scripts)

### By Workflow Phase
- **Early Development**: WF02 V70-V79 (proactive UX foundation)
- **Complete States**: WF02 V80-V99 (WF06 integration)
- **Critical Fixes**: WF02 V100-V114 (production readiness)
- **Production Solutions**: WF05 V7, WF06 V2.1, WF07 V13

### Related Documentation
- **Deployment Guides**: `../docs/deployment/` - Deployment procedures
- **Bug Reports**: `../docs/fix/` - Bug analysis and fixes
- **Analysis**: `../docs/analysis/` - Technical analysis
- **Implementation**: `../docs/implementation/` - Implementation guides

---

## 📝 Script File Naming Conventions

### Standard Format
- **wf##-v##-description.js**: State machine implementations (WF02)
- **generate-workflow-wf##-v##-description.py**: Workflow generators
- **fix-wf##-description.py**: Workflow-specific fixes
- **fix-description.py**: General fixes
- **test-description.sh**: Test scripts
- **validate-description.sh**: Validation scripts

### Version-Specific Patterns
- **V##**: Major version number following workflow version
- **v##.#**: Minor version for iterations within major version
- **v##_#**: Sub-version for specific fixes within minor version

### Script Type Indicators
- **.js**: JavaScript code (n8n Function nodes, state machines)
- **.py**: Python workflow generators and utilities
- **.sh**: Shell scripts (deployment, testing, utilities)
- **.sql**: SQL migration and cleanup scripts

---

## 🎯 Maintenance Guidelines

### Adding New Scripts
1. **Determine workflow and purpose**: Identify workflow (WF02/05/06/07) and script type
2. **Select appropriate subdirectory**:
   - State machines → `wf02/state-machines/`
   - Generators → `wf##/generators/`
   - Fixes → `wf##/fixes/`
   - Testing → `testing/`
   - Utilities → `utilities/`
3. **Follow naming conventions**: Use standard format for consistency
4. **Update README.md**: Add reference to new script

### Archiving Guidelines
- **Keep all scripts**: Historical scripts provide valuable development context
- **Maintain organization**: Ensure scripts remain in appropriate subdirectories
- **Move deprecated**: Transfer obsolete scripts to deprecated/ directory
- **Document deprecation**: Note reason for deprecation in script comments

---

## 📞 Related Documentation

- **Main Context**: `../CLAUDE.md`
- **Production Status**: `../docs/status/PRODUCTION_V1_DEPLOYMENT.md`
- **Current Status**: `../docs/status/DEPLOYMENT_STATUS.md`
- **Deployment Guides**: `../docs/deployment/`
- **Bug Reports**: `../docs/fix/`
- **Workflows**: `../n8n/workflows/`

---

**Project**: E2 Soluções WhatsApp Bot
**Maintained**: Claude Code
**Last Organization**: 2026-04-29
**Status**: ✅ Organized - All scripts categorized and accessible
