# CLAUDE.md - AI Assistant Guidelines for dkapps

This document provides guidelines and conventions for AI assistants (like Claude) working on the dkapps project. It ensures consistency, quality, and efficient collaboration between human developers and AI tools.

## Table of Contents

1. [Project Overview](#project-overview)
2. [Development Workflow](#development-workflow)
3. [Code Style & Conventions](#code-style--conventions)
4. [Git Practices](#git-practices)
5. [Architecture & Structure](#architecture--structure)
6. [Key Technologies](#key-technologies)
7. [Testing & Quality](#testing--quality)
8. [Documentation Standards](#documentation-standards)
9. [Common Tasks](#common-tasks)
10. [Troubleshooting](#troubleshooting)

## Project Overview

**Project Name:** dkapps
**Repository:** zhion008/dkapps
**Primary Language:** [Specify primary language(s)]
**Type:** [Specify project type - e.g., web app, library, CLI tool, etc.]

### Quick Facts
- Status: Early development
- Repository is structured for collaborative development with AI assistance
- Documentation-first approach for maintainability

> **TODO:** Update this section with actual project details once the codebase structure is established.

## Development Workflow

### Branch Strategy

- **Primary Development Branch:** `main` or `develop` (will be clarified once established)
- **Feature Branches:** Created from the primary branch with descriptive names
- **AI-Assisted Branches:** Prefixed with `claude/` followed by a short description and session ID
- **Hotfix Branches:** Prefixed with `hotfix/` for urgent production fixes

### Standard Development Process

1. **Create a feature branch** from the primary branch:
   ```bash
   git checkout -b claude/feature-description-sessionid
   ```

2. **Make focused changes** related to the feature/fix:
   - One logical change per commit
   - Clear, descriptive commit messages
   - Reference issue numbers when applicable

3. **Commit frequently** with meaningful messages:
   ```bash
   git commit -m "type: Brief description (issue #123)"
   ```

4. **Push to remote** when changes are complete:
   ```bash
   git push -u origin claude/feature-description-sessionid
   ```

5. **Create a Pull Request** for code review before merging to main

### Commit Message Format

Follow conventional commits format when possible:

```
type(scope): subject

body (optional)

footer (optional)
```

**Types:**
- `feat:` New feature
- `fix:` Bug fix
- `refactor:` Code reorganization without behavior change
- `perf:` Performance improvement
- `test:` Test additions or modifications
- `docs:` Documentation changes
- `chore:` Build, dependency, or tooling changes
- `ci:` CI/CD configuration changes

**Example:**
```
feat(auth): add JWT token validation

Implement JWT token validation for API endpoints.
Validates signature, expiration, and required claims.

Closes #42
```

## Code Style & Conventions

### General Principles

1. **Readability First:** Code should be clear and self-documenting
2. **Consistency:** Follow existing patterns in the codebase
3. **Minimal Complexity:** Avoid over-engineering; keep solutions simple
4. **No Premature Optimization:** Only optimize bottlenecks after profiling
5. **Security by Default:** Never introduce OWASP vulnerabilities

### Language-Specific Guidelines

> **Note:** Add language-specific guidelines below as the project grows

#### [JavaScript/TypeScript]
- Use ESLint configuration (`eslintrc.json` or similar)
- Use Prettier for code formatting
- Prefer const/let over var
- Use async/await over Promise chains
- Type annotations required for public APIs

#### [Python]
- Follow PEP 8 style guide
- Use type hints for function signatures
- Docstrings for all public functions/classes
- Use Black for code formatting
- Lint with flake8/pylint

#### [Other Languages]
[Add guidelines as needed]

### Naming Conventions

- **Classes/Types:** PascalCase (e.g., `UserService`, `DatabaseConnection`)
- **Functions/Variables:** camelCase (e.g., `getUserById`, `isActive`)
- **Constants:** UPPER_SNAKE_CASE (e.g., `MAX_RETRIES`, `API_TIMEOUT`)
- **Files:** lowercase-with-dashes or lowercase_with_underscores (match language convention)
- **Directories:** lowercase-with-dashes

### Comments & Documentation

- Write comments for **why**, not **what** (code should show what it does)
- Avoid redundant comments that restate obvious code
- Update comments when you update code
- Use doc comments (JSDoc, docstrings, etc.) for public APIs
- Include usage examples for complex functions

### Error Handling

- Always validate input at system boundaries (user input, API responses)
- Don't add unnecessary try-catch blocks for internal code
- Use specific error types, not generic Error
- Log errors with sufficient context for debugging
- Don't suppress errors silently

## Git Practices

### Before Committing

1. Run linters and formatters
2. Run all applicable tests
3. Review your own changes first (`git diff`)
4. Ensure no debugging code or console.logs remain

### Pushing Code

- **Always use `git push -u origin <branch-name>`** for new branches
- Never force push unless explicitly authorized
- Push frequently to avoid losing work
- Pull latest changes before starting work on a branch

### Handling Merge Conflicts

1. Never blindly resolve conflicts without understanding both sides
2. Communicate with the other developer if needed
3. Run tests after resolving conflicts
4. Keep the simpler/correct version when uncertain

### Pull Request Process

1. Ensure all tests pass locally
2. Write a clear PR title and description
3. Link related issues/tickets
4. Request reviews from relevant team members
5. Address review feedback promptly
6. Do not merge your own PRs

## Architecture & Structure

> **TODO:** Update this section once the project structure is established

### Expected Directory Structure

```
dkapps/
├── src/                    # Source code
│   ├── components/        # [If applicable]
│   ├── lib/              # Utility functions
│   ├── config/           # Configuration files
│   └── types/            # Type definitions [if TypeScript]
├── tests/                 # Test files
├── docs/                  # Documentation
├── scripts/               # Build and utility scripts
├── public/                # Static assets [if web app]
├── .github/               # GitHub configuration
│   └── workflows/         # CI/CD workflows
├── package.json           # [If Node.js]
├── tsconfig.json          # [If TypeScript]
├── eslint.config.js       # [If JavaScript/TypeScript]
├── CLAUDE.md              # This file
├── README.md              # Project overview
├── CONTRIBUTING.md        # Contribution guidelines
└── LICENSE                # License file
```

### Key Architectural Decisions

> Add architectural decision records (ADRs) as the project evolves

## Key Technologies

> **TODO:** Update as project technologies are finalized

- **Runtime:** [Node.js, Python, etc.]
- **Language:** [JavaScript/TypeScript, Python, etc.]
- **Framework:** [React, Django, Express, etc.]
- **Database:** [PostgreSQL, MongoDB, SQLite, etc.]
- **Testing:** [Jest, pytest, Vitest, etc.]
- **CI/CD:** [GitHub Actions, other]

## Testing & Quality

### Testing Requirements

1. **Unit Tests:** All functions and components should have unit tests
2. **Integration Tests:** Critical workflows should have integration tests
3. **Coverage Goal:** Aim for 70%+ code coverage
4. **Before PR:** All tests must pass locally

### Running Tests

```bash
# Run all tests
npm test  # or appropriate command

# Run tests in watch mode
npm test -- --watch

# Run tests with coverage
npm test -- --coverage

# Run specific test file
npm test -- path/to/test.spec.js
```

### Quality Checks

1. **Linting:** `npm run lint` or equivalent
2. **Type Checking:** `npm run type-check` or equivalent
3. **Format Check:** `npm run format:check` or equivalent
4. **Security:** Regular dependency audits

### Debugging Tips

- Add `debugger;` statement and run with `node --inspect-brk`
- Use test framework's `.only()` or `.skip()` for specific tests
- Check test output for helpful error messages
- Review stack traces carefully for root causes

## Documentation Standards

### README Requirements

Every project should have a README.md that includes:
- Project description
- Quick start guide
- Installation instructions
- Usage examples
- Contributing guidelines
- License information

### Code Documentation

- **Public APIs:** Always document with examples
- **Complex Logic:** Explain the approach and why
- **Deprecated Code:** Mark clearly with reason and migration path
- **External Dependencies:** Note why each dependency is needed

### Updating Documentation

- Update docs when you update code
- Keep examples in docs up-to-date and tested
- Use clear, inclusive language
- Include troubleshooting sections for common issues

## Common Tasks

### Adding a New Feature

1. Create a feature branch: `git checkout -b claude/feature-name-sessionid`
2. Implement the feature with tests
3. Update documentation
4. Commit with clear messages
5. Push and create a PR

### Fixing a Bug

1. Create a test that reproduces the bug
2. Fix the code to make the test pass
3. Ensure no other tests are broken
4. Update relevant documentation
5. Reference the issue in the commit message

### Refactoring Code

- Always have tests in place before refactoring
- Refactor one logical unit at a time
- Don't mix refactoring with bug fixes or features
- Ensure all tests pass after refactoring

### Updating Dependencies

1. Review the changelog of the new version
2. Update package files
3. Run full test suite
4. Test with actual use cases if critical dependency
5. Document any breaking changes

## Troubleshooting

### Common Issues & Solutions

#### Git Issues

**Issue:** "fatal: your current branch has no commits yet"
**Solution:** Ensure you're making changes and committing before pushing

**Issue:** Merge conflicts
**Solution:** Review both versions, understand the change, and resolve carefully

**Issue:** Push rejected (403)
**Solution:** Verify branch name matches expected format (starts with `claude/`, ends with session ID)

#### Development Issues

**Issue:** Tests failing locally but not in CI
**Solution:** Check Node version, environment variables, and clean node_modules

**Issue:** Linting errors
**Solution:** Run formatter: `npm run format` or equivalent, then fix remaining lint issues

**Issue:** Performance problems
**Solution:** Profile the code, identify bottlenecks, make targeted improvements

### Getting Help

1. Check existing documentation and examples
2. Review similar implementations in the codebase
3. Check issue tracker for related problems
4. Ask in project discussions or team channels
5. Create an issue with detailed reproduction steps

### Reporting Issues

Include:
- What you were trying to do
- What happened instead
- Error messages or logs
- Steps to reproduce
- Environment details (OS, Node version, etc.)

## AI Assistant-Specific Guidelines

### For Claude Code Users

**Always:**
- Read existing code before proposing changes
- Test changes before committing
- Use descriptive commit messages with session context
- Ask clarifying questions when requirements are ambiguous
- Follow established patterns in the codebase

**Never:**
- Commit without explicit permission
- Push to main/master without approval
- Introduce unnecessary dependencies
- Remove or disable linting/testing
- Make assumptions about project conventions

### Session Tracking

Include session context in commit messages using:
```
https://claude.ai/code/session_<SESSION_ID>
```

### Code Review Expectations

AI-generated code should:
- Pass all tests without modification
- Follow project conventions
- Include comments for non-obvious logic
- Be production-ready, not throw-away code

## Updates to This Document

This CLAUDE.md should be updated:
- When new technologies are adopted
- When conventions change
- When major architectural decisions are made
- Quarterly to ensure accuracy
- After project retrospectives

**Last Updated:** March 11, 2026
**Maintained By:** [Project maintainers]

---

## Project-Specific Customization Checklist

- [ ] Update Project Overview section with actual details
- [ ] Confirm primary development branch
- [ ] Add language-specific code style guidelines
- [ ] Document actual directory structure
- [ ] List all key technologies used
- [ ] Add testing framework specifics
- [ ] Define coverage requirements
- [ ] Add project-specific URLs and resources
- [ ] Document any custom scripts or tools
- [ ] Review and approve by team before use
