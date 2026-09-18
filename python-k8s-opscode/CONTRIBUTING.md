# Contributing to Opscode

Thank you for your interest in contributing to Opscode! This document provides guidelines for contributing to the project.

## Code of Conduct

By participating in this project, you agree to maintain a respectful and inclusive environment. Please refer to our [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) for details.

## How to Contribute

### Reporting Bugs

Before creating bug reports, please check the existing issues to avoid duplicates. When creating a bug report, include:

- A clear description of the problem
- Steps to reproduce the issue
- Expected behavior
- Actual behavior
- Environment details (OS, Python version, etc.)
- Relevant logs or error messages

### Suggesting Enhancements

Enhancement suggestions are welcome! Please provide:

- A clear description of the enhancement
- Use cases and benefits
- Potential implementation approach
- Examples or mockups if applicable

### Pull Requests

1. **Fork the repository** and create your branch from `main`
2. **Make your changes** following our coding standards
3. **Write tests** for new functionality
4. **Update documentation** as needed
5. **Run tests** to ensure everything works
6. **Submit a pull request** with a clear description

### Coding Standards

- Follow PEP 8 style guide
- Use type hints for all functions
- Write meaningful docstrings
- Keep functions small and focused
- Use descriptive variable names
- Add comments for complex logic
- Format code with `black`
- Lint code with `ruff`
- Type check with `mypy`

### Development Workflow

```bash
# Setup development environment
make install-dev

# Format code
make format

# Lint code
make lint

# Type check
make typecheck

# Run tests
make test

# Build Docker image
make docker-build
```

### Commit Messages

Use conventional commit format:

- `feat: add new feature`
- `fix: fix bug`
- `docs: update documentation`
- `test: add tests`
- `refactor: refactor code`
- `chore: maintenance tasks`

Example:
```
feat: add automatic remediation for high CPU usage

Implement automatic scaling when CPU usage exceeds threshold.
Add cooldown mechanism to prevent rapid scaling events.
```

## Testing

We value test coverage. Please ensure:

- Unit tests for new functions
- Integration tests for API endpoints
- Tests for edge cases
- Mock external dependencies
- Target 80%+ code coverage

## Documentation

Update documentation when:

- Adding new features
- Changing API endpoints
- Modifying configuration options
- Updating deployment procedures

## Questions?

Feel free to open an issue for questions or discussion. We're happy to help!

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
