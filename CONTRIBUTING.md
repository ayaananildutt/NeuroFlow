# Contributing to NeuroFlow

Thank you for considering contributing to NeuroFlow! This document outlines the guidelines and workflow for contributing.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Coding Standards](#coding-standards)
- [Pull Request Process](#pull-request-process)

## Code of Conduct

This project adheres to the [Contributor Covenant](https://www.contributor-covenant.org/) Code of Conduct. By participating, you are expected to uphold this code.

## Getting Started

1. **Fork** the repository on GitHub.
2. **Clone** your fork locally:
   ```bash
   git clone https://github.com/<your-username>/neuroflow.git
   cd neuroflow
   ```
3. **Create a branch** for your feature or fix:
   ```bash
   git checkout -b feature/your-feature-name
   ```
4. **Set up the development environment**:
   ```bash
   cp .env.example .env
   docker compose up -d
   ```

## Development Workflow

### Edge Layer (Python)

```bash
cd edge
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
```

### Server (Python / FastAPI)

```bash
cd server
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

### Dashboard (React)

```bash
cd dashboard
npm install
npm start
```

## Coding Standards

### Python
- Follow [PEP 8](https://peps.python.org/pep-0008/) style guidelines.
- Use type hints for all function signatures.
- Write docstrings for all public modules, classes, and functions.
- Maximum line length: 100 characters.
- Use `flake8` for linting:
  ```bash
  flake8 --max-line-length=100
  ```

### JavaScript / React
- Use functional components with hooks.
- Use `const` and `let` — never `var`.
- Follow the [Airbnb JavaScript Style Guide](https://github.com/airbnb/javascript).
- Use ESLint for linting:
  ```bash
  npx eslint src/
  ```

### Commits
- Use [Conventional Commits](https://www.conventionalcommits.org/):
  ```
  feat: add vehicle density heatmap to dashboard
  fix: resolve MQTT reconnection timeout issue
  docs: update API endpoint documentation
  ```

## Pull Request Process

1. Ensure your code passes all linting checks and tests.
2. Update `CHANGELOG.md` with a summary of your changes under `[Unreleased]`.
3. Update `README.md` or `docs/` if your changes affect usage or architecture.
4. Submit your PR against the `main` branch.
5. Request a review from at least one maintainer.
6. PRs require at least **1 approval** before merging.
7. Squash commits on merge to keep history clean.

## Reporting Issues

- Use the [GitHub Issues](https://github.com/your-org/neuroflow/issues) tab.
- Include steps to reproduce, expected behavior, and actual behavior.
- Attach logs or screenshots when applicable.

---

Thank you for helping make NeuroFlow better! 🚦
