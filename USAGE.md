# Usage Guide

Complete reference for `bsce-mgrep` command-line interface.

---

## Table of Contents

- [Synopsis](#synopsis)
- [Input Sources](#input-sources)
- [Pattern Matching](#pattern-matching)
- [Semantic Filtering](#semantic-filtering)
- [Case Sensitivity](#case-sensitivity)
- [Advanced Examples](#advanced-examples)
- [Expression Language Reference](#expression-language-reference)
- [Exit Codes](#exit-codes)

---

## Synopsis

```bash
mgrep <source> [options]
mgrep [options]  # reads from stdin if piped
```

### Required Arguments

- `--match PATTERN` - Pattern to match (literal or regex)

### Optional Arguments

- `source` - Input file path (omit to read from stdin)
- `--case {sensitive|insensitive}` - Case sensitivity control
- `--where EXPRESSION` - Semantic filter (can be repeated)

---

## Input Sources

### File Input

```bash
# Read from file
mgrep app.log --match 'ERROR'
mgrep /var/log/syslog --match '/kernel/'
```

### Stdin Input

```bash
# Pipe from command
cat app.log | mgrep --match 'ERROR'
tail -f app.log | mgrep --match 'WARN'

# Redirect from file
mgrep --match 'ERROR' < app.log
```

### Auto-Detection

If `source` argument is omitted, mgrep checks if stdin is piped:

```bash
# This works (stdin is piped)
echo "ERROR: test" | mgrep --match 'ERROR'

# This fails (no input source)
mgrep --match 'ERROR'
# Error: No input source (provide file or pipe stdin)
```

---

## Pattern Matching

### Literal Matching

Match exact strings anywhere in the line:

```bash
# Simple literal
mgrep app.log --match 'ERROR'

# With spaces
mgrep app.log --match 'connection timeout'

# Special characters are literal (not regex)
mgrep app.log --match '[ERROR]'  # Matches literal "[ERROR]"
```

**Default**: Case-insensitive for literal patterns

### Regex Matching

Wrap pattern in `/` slashes to enable regex:

```bash
# Basic regex
mgrep app.log --match '/ERR(OR|WARN)/'

# Match status codes
mgrep access.log --match '/status=[45]\d{2}/'

# Word boundaries
mgrep app.log --match '/\bfailed\b/'
```

**Default**: Case-sensitive for regex patterns

### Named Capture Groups

Extract data using regex named groups:

```bash
# Capture HTTP status code
mgrep access.log --match '/status=(?<code>\d+)/'

# Capture user ID
mgrep app.log --match '/user=(?<id>\w+)/'

# Multiple captures
mgrep app.log --match '/(?<level>\w+): (?<message>.*)/'
```

Named groups become available in `--where` expressions via `group("name")`.

---

## Semantic Filtering

### Basic Filtering

Use `--where` to filter matched lines based on properties:

```bash
# Filter by line length
mgrep app.log --match 'ERROR' --where 'line.length > 120'

# Filter by line number
mgrep data.csv --match ',' --where 'line.number > 1'

# Filter by content
mgrep app.log --match 'ERROR' --where 'line.contains("database")'
```

### Multiple Filters (AND Logic)

Multiple `--where` clauses are combined with logical AND:

```bash
mgrep app.log \
  --match 'ERROR' \
  --where 'line.length > 100' \
  --where 'line.contains("timeout")'
# Matches ERROR lines that are long AND contain "timeout"
```

### Using Captured Groups

Filter using regex named groups:

```bash
# Filter by captured status code
mgrep access.log \
  --match '/status=(?<code>\d+)/' \
  --where 'group("code") >= 500'

# Filter by user type
mgrep app.log \
  --match '/user=(?<id>\w+)/' \
  --where 'group("id").startswith("admin")'
```

---

## Case Sensitivity

### Default Behavior

```bash
# Literal patterns: case-insensitive by default
mgrep app.log --match 'error'
# Matches: "ERROR", "Error", "error"

# Regex patterns: case-sensitive by default
mgrep app.log --match '/error/'
# Matches: "error" only
```

### Explicit Control

```bash
# Force case-sensitive literal
mgrep app.log --match 'ERROR' --case sensitive
# Matches: "ERROR" only

# Force case-insensitive regex
mgrep app.log --match '/error/' --case insensitive
# Matches: "ERROR", "Error", "error"
```

---

## Advanced Examples

### Log Analysis

#### Find Critical Errors

```bash
# Long error messages (likely detailed)
mgrep app.log \
  --match 'ERROR' \
  --where 'line.length > 200'
```

#### Extract Failed Authentication

```bash
# Failed logins with user info
mgrep auth.log \
  --match '/user=(?<username>\w+).*failed/' \
  --where 'line.contains("authentication")'
```

#### Filter by HTTP Status

```bash
# Server errors (5xx)
mgrep access.log \
  --match '/status=(?<code>\d+)/' \
  --where 'group("code") >= 500'

# Client errors (4xx) excluding 404
mgrep access.log \
  --match '/status=(?<code>\d+)/' \
  --where 'group("code") >= 400' \
  --where 'group("code") < 500' \
  --where 'group("code") != 404'
```

### Data Processing

#### CSV Header Skipping

```bash
# Skip first line (header)
mgrep data.csv \
  --match ',' \
  --where 'line.number > 1'
```

#### Extract Specific Rows

```bash
# Even-numbered rows only
mgrep data.csv \
  --match ',' \
  --where 'line.number % 2 == 0'
```

### Real-Time Monitoring

```bash
# Watch logs for critical errors
tail -f /var/log/app.log | \
  mgrep --match 'CRITICAL' \
  --where 'line.contains("database") or line.contains("timeout")'
```

### Complex Pattern Matching

```bash
# Match timestamp + error level + message
mgrep app.log \
  --match '/(?<time>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}).*(?<level>ERROR|WARN).*(?<msg>.*)/' \
  --where 'line.length > 100' \
  --where 'group("level") == "ERROR"'
```

---

## Expression Language Reference

### Available in `--where` Expressions

#### Line Properties

| Property | Type | Description |
|----------|------|-------------|
| `line.number` | `int` | Line number (1-indexed) |
| `line.content` | `str` | Full line text |
| `line.length` | `int` | Character count |

#### Line Methods

| Method | Returns | Description |
|--------|---------|-------------|
| `line.contains(text)` | `bool` | Check substring presence |
| `line.startswith(text)` | `bool` | Check line prefix |
| `line.endswith(text)` | `bool` | Check line suffix |

#### Regex Group Access

| Function | Returns | Description |
|----------|---------|-------------|
| `group("name")` | `str` | Get named capture group value |

**Note**: Only available when pattern has named groups.

#### Operators

**Comparison**:
- `>`, `<`, `>=`, `<=`, `==`, `!=`

**Logical**:
- `and`, `or`, `not`

**Arithmetic** (on numeric values):
- `+`, `-`, `*`, `/`, `%` (modulo)

#### String Methods on Groups

```bash
# Captured groups are strings, so string methods work:
--where 'group("code").startswith("5")'
--where 'group("user").endswith("@admin")'
```

### Expression Examples

```python
# Numeric comparisons
'line.number > 100'
'line.length >= 80 and line.length <= 120'

# String operations
'line.contains("ERROR") and line.contains("database")'
'line.startswith("2024-")'

# Regex groups
'group("status") >= 500'
'group("user") == "admin"'

# Complex boolean logic
'(line.length > 100 or line.contains("CRITICAL")) and line.number % 10 == 0'

# Arithmetic
'line.number % 2 == 0'  # Even lines
'line.length / 10 > 12'  # More than 120 chars
```

---

## Exit Codes

| Code | Meaning |
|------|---------|
| `0` | Success (matches found or no matches) |
| `1` | Error (invalid arguments, file not found, parse error) |

### Examples

```bash
# Success
mgrep app.log --match 'ERROR'
echo $?  # 0

# Error: missing required argument
mgrep app.log
echo $?  # 1

# Error: file not found
mgrep nonexistent.log --match 'ERROR'
echo $?  # 1
```

---

## Tips & Best Practices

### Performance

1. **Use specific patterns**: `--match 'ERROR'` is faster than `--match '.*'`
2. **Order filters**: Put cheapest filters first (e.g., `line.number` before `line.contains`)
3. **Compile patterns once**: mgrep does this automatically

### Debugging

```bash
# Test pattern matching first
mgrep app.log --match 'ERROR'

# Then add filters incrementally
mgrep app.log --match 'ERROR' --where 'line.length > 100'
mgrep app.log --match 'ERROR' --where 'line.length > 100' --where 'line.contains("db")'
```

### Working with Named Groups

```bash
# Always test regex separately first
echo "status=503" | mgrep --match '/status=(?<code>\d+)/'

# Then add group-based filters
echo "status=503" | mgrep --match '/status=(?<code>\d+)/' --where 'group("code") >= 500'
```

### Common Patterns

```bash
# Find errors excluding known noise
mgrep app.log \
  --match 'ERROR' \
  --where 'not line.contains("ignorable")'

# Extract user actions
mgrep audit.log \
  --match '/user=(?<id>\w+).*action=(?<act>\w+)/' \
  --where 'group("act") == "delete"'

# Monitor rate of errors
tail -f app.log | \
  mgrep --match 'ERROR' | \
  wc -l  # Count per second
```

---

## Comparison with grep

| Feature | `grep` | `mgrep` |
|---------|--------|---------|
| Literal matching | ✅ | ✅ |
| Regex | ✅ | ✅ |
| Named groups | ❌ | ✅ |
| Semantic filtering | ❌ | ✅ |
| Type-safe | ❌ | ✅ |
| Safe expressions | N/A | ✅ (no `eval`) |

### When to Use mgrep

- ✅ Complex filtering logic (numeric, boolean)
- ✅ Working with structured logs
- ✅ Need to filter by line properties
- ✅ Extracting data with named groups

### When to Use grep

- ✅ Simple text matching
- ✅ Maximum performance on huge files
- ✅ Standard Unix tool availability

---

## Troubleshooting

### "Error: No input source"

```bash
# Wrong
mgrep --match 'ERROR'

# Right
mgrep app.log --match 'ERROR'
# OR
cat app.log | mgrep --match 'ERROR'
```

### "Parse error in --where expression"

Check expression syntax:

```bash
# Wrong: missing quotes
--where line.contains(test)

# Right
--where 'line.contains("test")'
```

### No matches found

1. Check case sensitivity: `--case insensitive`
2. Test pattern: `mgrep file --match 'pattern'` (no filters)
3. Verify file content: `head file`

---

## Further Reading

- [Architecture](ARCHITECTURE.md) - Technical implementation details
- [Design Decisions](DESIGN_DECISIONS.md) - Why we made specific choices
- [Contributing](CONTRIBUTING.md) - How to extend functionality