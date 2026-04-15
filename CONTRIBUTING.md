# Contributing to Clawra Engine

Thank you for your interest in contributing to Clawra Engine! 🎉

## What is Clawra?

Clawra is a **neuro-symbolic cognitive agent framework** that enables AI agents to autonomously learn rules from text — instead of requiring developers to hardcode them. It's built for production AI systems where rules change frequently, domain expertise matters, and safety is non-negotiable.

## How Can I Help?

### 🐛 Reporting Bugs
- Search existing [issues](https://github.com/wu-xiaochen/clawra-engine/issues) first
- Open a new issue with a clear title and description
- Include: Python version, error message, and minimal reproduction case

### 💡 Suggesting Features
- Open a discussion in [GitHub Discussions](https://github.com/wu-xiaochen/clawra-engine/discussions)
- Describe the use case and why it would benefit the community
- Check if similar suggestions already exist

### 🛠️ Contributing Code

**Step 1: Fork & Clone**
```bash
git clone https://github.com/wu-xiaochen/clawra-engine.git
cd clawra-engine
pip install -e .[dev]
```

**Step 2: Create a Branch**
```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/your-bug-fix
```

**Step 3: Write Code**
- Follow the existing code style (PEP 8, ruff for linting)
- Add tests for new functionality (minimum: happy path + edge case)
- Run tests before committing:
  ```bash
  pytest tests/ -q
  ```

**Step 4: Commit & Push**
```bash
git commit -m "feat: add new feature"
git push origin feature/your-feature-name
```

**Step 5: Open a Pull Request**
- Fill out the PR template
- Link to related issues
- Wait for review (we aim to respond within 48 hours)

## 📋 Development Setup

### Prerequisites
- Python 3.10+
- pip

### Install Dependencies
```bash
pip install -e .        # Core package
pip install -e ".[dev]" # Dev dependencies (includes pytest)
```

### Run Tests
```bash
# All tests
pytest tests/ -q

# With coverage
pytest tests/ --cov=src --cov-report=term-missing

# Specific test file
pytest tests/core/test_reasoner.py -q
```

### Run Demos
```bash
python examples/demo_basic.py                  # Basic demo (no API key needed)
python examples/demo_evolution_loop.py         # Evolution loop demo
python examples/demo_graphrag.py              # GraphRAG demo
PYTHONPATH=. streamlit run examples/web_demo.py # Web interface
```

## 📐 Code Architecture

For a deep dive, read:
- [ARCHITECTURE.md](docs/ARCHITECTURE.md) — System architecture
- [EVOLUTION_LOOP.md](docs/EVOLUTION_LOOP.md) — Evolution loop design
- [SDK_GUIDE.md](docs/SDK_GUIDE.md) — SDK usage guide

## 🧪 Test Strategy

Every feature must have tests. We use:
- **Unit tests**: Test individual components in isolation
- **Integration tests**: Test interactions between components (marked with `@pytest.mark.integration`)
- **Property-based tests**: For core reasoning logic

See [TESTING_STRATEGY.md](docs/TESTING_STRATEGY.md) for details.

## 📜 License

By contributing, you agree that your contributions will be licensed under the MIT License.

## 🙏 Thank You

Every contribution matters — from bug reports to code changes. Thank you for helping make Clawra better.

---

**Good first issues:**
- Issues labeled [good first issue](https://github.com/wu-xiaochen/clawra-engine/labels/good%20first%20issue)
- Issues labeled [help wanted](https://github.com/wu-xiaochen/clawra-engine/labels/help%20wanted)

**Questions?** Open a [discussion](https://github.com/wu-xiaochen/clawra-engine/discussions) or join our Discord.
