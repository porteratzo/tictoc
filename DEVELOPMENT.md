# Development Guide

This document describes the code quality tools and pre-commit infrastructure set up for this repository.

## Code Quality Tools

This repository uses the following tools to maintain code quality:

### 1. Formatting
- **Black**: Opinionated Python code formatter (line length: 88)
- **isort**: Import statement sorter (configured to work with Black)

### 2. Linting
- **Flake8**: Style guide enforcement and basic linting
- **Pylint**: Comprehensive Python linter

### 3. Type Checking
- **mypy**: Static type checker for Python

## Pre-commit Hooks

Pre-commit hooks are configured to run automatically before each commit. The hooks will:

1. Remove trailing whitespace
2. Fix end of file issues
3. Check YAML, JSON, and TOML syntax
4. Check for large files
5. Check for merge conflicts
6. Check for debug statements
7. Format code with Black
8. Sort imports with isort
9. Run Flake8 linting
10. Run mypy type checking

## Installation

Install the development dependencies:

```bash
pip install -r requirements-dev.txt
```

Install pre-commit hooks:

```bash
pre-commit install
```

## Usage

### Automatic (Recommended)

Once pre-commit is installed, the hooks will run automatically on `git commit`. If any hook fails or modifies files, the commit will be aborted. Review the changes, stage them, and commit again.

### Manual

You can run the tools manually at any time:

```bash
# Run all pre-commit hooks on all files
pre-commit run --all-files

# Run specific tools
black .
isort .
flake8
mypy tictoc/
pylint tictoc/
```

### Individual Tool Usage

```bash
# Format code with Black
black tictoc/ example.py plot.py

# Sort imports
isort tictoc/ example.py plot.py

# Run Flake8
flake8 tictoc/ example.py plot.py

# Run mypy
mypy tictoc/

# Run Pylint
pylint tictoc/
```

## Configuration Files

- `pyproject.toml`: Configuration for Black, isort, mypy, and Pylint
- `.flake8`: Configuration for Flake8
- `.pre-commit-config.yaml`: Pre-commit hook configuration

## Disabling Hooks Temporarily

If you need to commit without running the hooks (not recommended):

```bash
git commit --no-verify
```

## Updating Pre-commit Hooks

To update the pre-commit hook versions:

```bash
pre-commit autoupdate
```

## CI/CD Integration

These tools can be integrated into your CI/CD pipeline. Example for GitHub Actions:

```yaml
- name: Run pre-commit
  run: pre-commit run --all-files
```
