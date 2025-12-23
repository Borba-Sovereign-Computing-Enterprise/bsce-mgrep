# Industrial-Grade Grep Built on Functional Programming

> A functional, type-safe grep implementation in pure Python 3.12+

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Functional](https://img.shields.io/badge/paradigm-functional-purple.svg)](https://en.wikipedia.org/wiki/Functional_programming)
[![Architecture](https://img.shields.io/badge/architecture-hexagonal-green.svg)](https://alistair.cockburn.us/hexagonal-architecture/)
[![License](https://img.shields.io/badge/license-MIT-orange.svg)](LICENSE)

---

## Overview

**bsce-mgrep** is a modern, industrial-grade grep alternative built with functional programming principles. Unlike traditional grep, it provides semantic filtering capabilities through a safe expression language, making it ideal for complex log analysis and data processing workflows.

### Key Features

- **🔍 Powerful Matching**: Literal strings and regular expressions with named capture groups
- **🧮 Semantic Filtering**: Filter matched lines using safe expression evaluation (no `eval()`)
- **🛡️ Type-Safe**: Full Python 3.12+ type hints with mypy strict mode compliance
- **⚡ Functional Core**: Pure functions, immutability, and Railway-Oriented Programming
- **🏗️ Hexagonal Architecture**: Clean separation of concerns, highly testable
- **📦 Zero Dependencies**: Only stdlib + `result` library for error handling

---

## Quick Start

### Installation

```bash
# Clone repository
git clone https://github.com/borba-sovereign/bsce-mgrep.git
cd bsce-mgrep

# Install dependencies
pip install -r requirements.txt

# Install package
pip install -e .
```

### Basic Usage

```bash
# Simple literal match
mgrep app.log --match 'ERROR'

# Regex with named groups
mgrep app.log --match '/status=(?<code>\d+)/'

# Semantic filtering
mgrep app.log \
  --match 'ERROR' \
  --where 'line.length > 120' \
  --where 'line.contains("timeout")'

# Pipeline from stdin
cat app.log | mgrep --match 'ERROR'

# Case-insensitive matching
mgrep app.log --match 'error' --case insensitive
```

---

## Documentation

- **[Usage Guide](docs/USAGE.md)** - Complete CLI reference with examples
- **[Architecture](docs/ARCHITECTURE.md)** - Technical deep-dive into design
- **[Contributing](docs/CONTRIBUTING.md)** - Development guidelines
- **[Design Decisions](docs/DESIGN_DECISIONS.md)** - Rationale behind key choices

---

## Philosophy

### Functional Programming First

Every component is built with FP principles:

- **Immutability**: All data structures are frozen
- **Pure Functions**: No side effects outside I/O boundaries
- **Composition**: Complex behavior emerges from simple functions
- **Railway-Oriented Programming**: Explicit error handling via `Result` type

### Type Safety

Leverages Python 3.12+ features extensively:

```python
type LineNumber = int
type MatchResult = Result[MatchContext, ErrorMessage]

@dataclass(frozen=True)
class Line:
    number: LineNumber
    content: str
```

### Security By Design

The `--where` clause uses a **manual expression parser** (no `eval()`), preventing code injection while providing powerful filtering capabilities.

---

## Example Workflows

### Log Analysis

```bash
# Find all 5xx errors with request details
mgrep access.log \
  --match '/status=(?<code>\d+)/' \
  --where 'group("code") >= 500'

# Find long error messages
mgrep app.log \
  --match 'ERROR' \
  --where 'line.length > 200'
```

### Data Processing

```bash
# Extract user activity from logs
cat user-events.log | \
  mgrep --match '/user=(?<id>\w+)/' \
  --where 'line.contains("login")'

# Filter by line position
mgrep data.csv \
  --match ',' \
  --where 'line.number > 1'  # Skip header
```

---

## Requirements

- **Python**: 3.12 or higher
- **Dependencies**: `result` (Railway-Oriented Programming)

---

## Project Status

**Current Version**: 0.1.0 (MVP)

### Implemented
- ✅ Literal and regex matching
- ✅ Named capture groups
- ✅ Semantic filtering (`--where`)
- ✅ Case sensitivity control
- ✅ File and stdin input

### Roadmap
- 🔲 `--emit json` output format
- 🔲 Performance optimizations (compiled patterns caching)
- 🔲 Colorized output
- 🔲 Multi-file processing
- 🔲 Watch mode for live logs

---

## Contributing

We welcome contributions! Please read our [Contributing Guide](docs/CONTRIBUTING.md) for:

- Code style guidelines
- Development setup
- Testing requirements
- Pull request process

---

## Credits

**Author**: Borba Sovereign Computing House
**Maintainer**: André Borba

Inspired by functional programming practices from Bloomberg and Jane Street.

---

## License

MIT License - see [LICENSE](LICENSE) file for details.

---

## Support

- **Issues**: [GitHub Issues](https://github.com/borba-sovereign/bsce-mgrep/issues)
- **Discussions**: [GitHub Discussions](https://github.com/borba-sovereign/bsce-mgrep/discussions)

---

*Built with ❤️ using Functional Programming principles*