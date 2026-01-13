# Dependency Audit Report

**Date**: 2026-01-13
**Project**: porter_bench v0.1.0

## Executive Summary

This audit identified 7 security vulnerabilities, 1 critical missing dependency, and several recommendations for improving dependency management.

## Critical Issues

### 1. Security Vulnerabilities (7 found)

#### cryptography 41.0.7
- **PYSEC-2024-225** → Fix: Upgrade to ≥42.0.4
- **CVE-2023-50782** → Fix: Upgrade to ≥42.0.0
- **CVE-2024-0727** → Fix: Upgrade to ≥42.0.2
- **GHSA-h4gh-qq45-vh27** → Fix: Upgrade to ≥43.0.1
- **Recommendation**: Update system cryptography to ≥43.0.1

#### pip 24.0
- **CVE-2025-8869** → Fix: Upgrade to ≥25.3
- **Recommendation**: Update in CI/CD and development environments

#### setuptools 68.1.2
- **PYSEC-2025-49** → Fix: Upgrade to ≥78.1.1
- **CVE-2024-6345** → Fix: Upgrade to ≥70.0.0
- **Recommendation**: Update build system requirement to ≥78.1.1

### 2. Missing Production Dependency

**pandas** is used in `porter_bench/utils.py` but not declared in `setup.py`:
```python
# porter_bench/utils.py:6
import pandas as pd
```

**Impact**: Installation will fail when users try to use data loading functions.

**Locations used**:
- `utils.py:54` - `get_absolutes()`
- `utils.py:63` - `get_calls()`
- `utils.py:72` - `get_infos()`

### 3. Undeclared Example Dependencies

`example.py` requires packages not in setup.py:
- **torch** (line 4) - CUDA memory tracking
- **tqdm** (line 5) - Progress bars

**Impact**: Examples fail without additional manual installation.

## Production Dependencies Analysis

Current dependencies in `setup.py`:

| Package | Status | Usage | Files |
|---------|--------|-------|-------|
| matplotlib | ✅ Required | Plotting & visualization | 4 files |
| numpy | ✅ Required | Numerical operations | 3 files |
| scipy | ✅ Required | Gaussian filtering | TimeBenchmarker.py |
| psutil | ✅ Required | Memory profiling | MemoryBenchmarker.py |

**Issue**: No version constraints specified → potential compatibility issues

## Development Dependencies Analysis

Current dev dependencies in `requirements-dev.txt`:

| Package | Status | Purpose |
|---------|--------|---------|
| black | ✅ Good | Code formatting |
| isort | ✅ Good | Import sorting |
| flake8 + plugins | ✅ Good | Linting |
| pylint | ✅ Good | Advanced linting |
| mypy | ✅ Good | Type checking |
| pytest + cov | ✅ Good | Testing |
| pre-commit | ✅ Good | Git hooks |

All development dependencies are necessary and appropriately versioned.

## Build System Dependencies

Current in `pyproject.toml`:
```toml
requires = ["setuptools>=45", "wheel", "setuptools_scm[toml]>=6.2"]
```

**Issue**: setuptools minimum version (45) is too old and has vulnerabilities.

## Outdated Packages

21 packages have available updates. Key updates:
- setuptools: 68.1.2 → 80.9.0 (security fixes)
- pip: 24.0 → 25.3 (security fix)
- packaging: 24.0 → 25.0

## Recommendations

### Priority 1: Critical Fixes

1. **Add missing pandas dependency to setup.py**:
```python
install_requires=[
    "matplotlib",
    "numpy",
    "scipy",
    "psutil",
    "pandas",  # ADD THIS
],
```

2. **Update build system requirements in pyproject.toml**:
```toml
requires = ["setuptools>=78.1.1", "wheel", "setuptools_scm[toml]>=6.2"]
```

3. **Update system packages**:
```bash
pip install --upgrade pip>=25.3 setuptools>=78.1.1
```

### Priority 2: Version Pinning

Add minimum version constraints for production dependencies:
```python
install_requires=[
    "matplotlib>=3.8.0,<4.0.0",
    "numpy>=1.24.0,<3.0.0",
    "scipy>=1.10.0,<2.0.0",
    "psutil>=5.9.0,<6.0.0",
    "pandas>=2.0.0,<3.0.0",
],
```

**Rationale**:
- Ensures compatibility
- Prevents breaking changes from major version updates
- Documents tested/supported versions

### Priority 3: Optional Dependencies

Create extras for example dependencies:
```python
extras_require={
    "examples": [
        "torch>=2.0.0",
        "tqdm>=4.65.0",
    ],
    "dev": [
        "black>=24.1.1",
        "isort>=5.13.2",
        # ... (move from requirements-dev.txt)
    ],
},
```

**Benefits**:
- Core package remains lightweight
- Users can opt-in: `pip install porter_bench[examples]`
- Clearer separation of concerns

### Priority 4: Lock File

Create a `requirements.txt` with pinned versions:
```bash
pip freeze > requirements.txt
```

**Benefits**:
- Reproducible builds
- CI/CD consistency
- Easier debugging

## No Bloat Detected

All dependencies are actively used in the codebase:
- Production: 4/4 dependencies used (1 missing)
- Development: 8/8 tools are appropriate
- No unnecessary or duplicate dependencies

## Action Items

- [ ] Add pandas to setup.py install_requires
- [ ] Update setuptools requirement in pyproject.toml to >=78.1.1
- [ ] Add version constraints to all production dependencies
- [ ] Move torch and tqdm to extras_require["examples"]
- [ ] Consider moving dev dependencies to extras_require["dev"]
- [ ] Update pip and setuptools in CI/CD pipelines
- [ ] Create requirements.txt lock file
- [ ] Run `pip-audit` regularly in CI/CD
- [ ] Document example requirements in README.md

## Testing Commands

```bash
# Security audit
pip install pip-audit
pip-audit

# Check outdated
pip list --outdated

# Validate installation
pip install -e .
python -c "from porter_bench import utils"  # Should not fail
```

## References

- pip-audit: https://github.com/pypa/pip-audit
- CVE Details: https://cve.mitre.org/
- Python Packaging Guide: https://packaging.python.org/
