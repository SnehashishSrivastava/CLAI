# Contributing to CLAI

Thank you for your interest in contributing to CLAI! This document provides guidelines and instructions.

## Getting Started

1. **Fork the repository**
2. **Clone your fork**
   ```bash
   git clone https://github.com/your-username/CLAI.git
   cd CLAI
   ```

3. **Create a branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

4. **Set up development environment**
   ```bash
   pip install -r requirements.txt
   python test_llm_integration.py  # Verify setup
   ```

## Development Guidelines

### Code Style

- Follow PEP 8
- Use type hints where possible
- Add docstrings to all public functions
- Keep functions focused and small

### Testing

- Add tests for new features
- Run existing tests before submitting
- Ensure all tests pass

```bash
python test_llm_integration.py
python test_hf_adapter.py
python test_sandbox_session.py --demo
```

### Commit Messages

Use clear, descriptive commit messages:

```
feat: Add Docker sandbox support
fix: Resolve change detection issue
docs: Update API documentation
refactor: Simplify session management
```

### Pull Request Process

1. **Update documentation** if needed
2. **Add tests** for new features
3. **Ensure all tests pass**
4. **Update CHANGELOG.md**
5. **Create pull request** with description

### PR Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Refactoring

## Testing
How was this tested?

## Checklist
- [ ] Code follows style guidelines
- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] CHANGELOG updated
```

## Areas for Contribution

### High Priority

- **Better error messages** - More helpful user feedback
- **Performance improvements** - Faster sandbox operations
- **Additional LLM providers** - Support for more models
- **Enhanced safety** - More robust command validation

### Feature Ideas

- Command history search
- Multi-session support
- Cloud log sync
- Web dashboard
- Plugin system
- Better Windows/Linux compatibility

### Documentation

- More examples
- Video tutorials
- API usage guides
- Architecture diagrams

## Code Structure

### Adding New LLM Adapter

1. Create `llm/adapter_<provider>.py`
2. Implement `chat_completions()` method
3. Return OpenAI-compatible format
4. Add to `llm/__init__.py`
5. Update documentation

### Adding New Safety Rules

1. Edit `prompt_builder/safety_policy.py`
2. Add deny patterns or limits
3. Update tests
4. Document changes

### Extending GUI

1. Edit `gui/app.py`
2. Follow existing component patterns
3. Use Theme colors
4. Test on Windows and Linux

## Questions?

- Open an issue for discussion
- Check existing issues first
- Be respectful and constructive

## License

By contributing, you agree that your contributions will be licensed under the same license as the project.

---

Thank you for contributing to CLAI! 🎉

