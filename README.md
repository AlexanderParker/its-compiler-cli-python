# ITS Compiler CLI

[![PyPI version](https://img.shields.io/pypi/v/its-compiler-cli.svg)](https://pypi.org/project/its-compiler-cli/)
[![Python](https://img.shields.io/pypi/pyversions/its-compiler-cli.svg)](https://pypi.org/project/its-compiler-cli/)
[![License](https://img.shields.io/github/license/AlexanderParker/its-compiler-cli-python.svg)](LICENSE)

Command-line interface for the [ITS Compiler Python](https://github.com/alexanderparker/its-compiler-python) library. Converts [Instruction Template Specification (ITS)](https://alexanderparker.github.io/instruction-template-specification/) templates into structured AI prompts.

## Installation

```bash
pip install its-compiler-cli
```

This automatically installs the core [its-compiler](https://github.com/alexanderparker/its-compiler-python) library as a dependency.

## Quick Start

### Basic Usage

```bash
# Compile template to stdout
its-compile template.json

# Save output to file
its-compile template.json --output prompt.txt

# Use custom variables
its-compile template.json --variables vars.json

# Validate template without compiling
its-compile template.json --validate-only
```

### Example Template

Create `example.json`:

```json
{
  "version": "1.0.0",
  "extends": ["https://alexanderparker.github.io/instruction-template-specification/schema/v1.0/its-standard-types-v1.json"],
  "variables": {
    "topic": "renewable energy"
  },
  "content": [
    {
      "type": "placeholder",
      "instructionType": "paragraph",
      "config": {
        "description": "Write about ${topic}",
        "tone": "informative"
      }
    }
  ]
}
```

Compile it:

```bash
its-compile example.json
```

## Command Reference

```
its-compile [OPTIONS] TEMPLATE_FILE

Arguments:
  TEMPLATE_FILE             Path to the ITS template JSON file

Options:
  -o, --output FILE         Output file (default: stdout)
  -v, --variables FILE      JSON file with variable values
  -w, --watch              Watch template file for changes
  --validate-only          Validate template without compiling
  --verbose                Show detailed output
  --strict                 Enable strict validation mode
  --no-cache              Disable schema caching
  --timeout INTEGER       Network timeout in seconds (default: 30)
  --allow-http            Allow HTTP URLs (not recommended)
  --interactive-allowlist / --no-interactive-allowlist
                          Enable/disable interactive schema prompts
  --allowlist-status      Show schema allowlist status
  --version               Show version and exit
  --help                  Show help and exit
```

## Development Workflow

### Watch Mode

Automatically recompile when the template changes:

```bash
its-compile template.json --watch --output prompt.txt
```

### Validation

Check templates for errors without compiling:

```bash
its-compile template.json --validate-only --strict
```

### Variables

Use external variable files:

```bash
# vars.json
{
  "productName": "Widget Pro",
  "features": ["fast", "reliable", "secure"]
}

its-compile template.json --variables vars.json
```

## Schema Management

When templates reference external schemas, you may be prompted to allow them:

```
SCHEMA ALLOWLIST DECISION REQUIRED
URL: https://example.com/schema.json

1. Allow permanently (saved to allowlist)
2. Allow for this session only
3. Deny (compilation will fail)
```

### Allowlist Commands

```bash
# Check current allowlist status
its-compile --allowlist-status

# Non-interactive mode (useful for CI/CD)
its-compile template.json --no-interactive-allowlist
```

## Configuration

Set environment variables to configure default behaviour:

```bash
export ITS_INTERACTIVE_ALLOWLIST=false  # Disable prompts
export ITS_REQUEST_TIMEOUT=60           # Increase timeout
export ITS_ALLOWLIST_FILE=/path/to/allowlist.json
```

## Error Examples

### Missing Variable

```
✗ Variable Error: Undefined variable '${productName}'
  Available variables: topic, features
```

### Invalid Template

```
✗ Validation Error: Missing required field 'version'
  At: root
```

### Schema Issues

```
✗ Schema Error: Failed to load schema
  URL: https://example.com/schema.json
```

## Testing

Test your CLI installation:

```bash
# Basic functionality test
echo '{"version":"1.0.0","content":[{"type":"text","text":"Hello"}]}' | its-compile /dev/stdin

# Download test runner (optional)
curl -O https://raw.githubusercontent.com/AlexanderParker/its-compiler-cli-python/main/test_runner.py
python test_runner.py
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes and add tests
4. Ensure all tests pass (`python test_runner.py`)
5. Run linting (`black . && flake8`)
6. Commit your changes
7. Push to the branch and open a Pull Request

### Development Setup

```bash
# Clone and setup
git clone https://github.com/AlexanderParker/its-compiler-cli-python.git
cd its-compiler-cli-python

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e ".[dev]"

# Run tests
python test_runner.py
```

### For Maintainers

**Publishing to PyPI:**

This package is published to PyPI as `its-compiler-cli`. Releases are currently managed manually:

```bash
# Build the package
python -m build

# Test upload to TestPyPI first (recommended)
python -m twine upload --repository testpypi dist/*

# Upload to production PyPI (requires appropriate credentials)
python -m twine upload dist/*
```

**TestPyPI Testing:**

```bash
# Install from TestPyPI to verify the package
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ its-compiler-cli
```

## Related Projects

- **[ITS Compiler Python](https://github.com/alexanderparker/its-compiler-python)** - Core library
- **[Instruction Template Specification](https://alexanderparker.github.io/instruction-template-specification/)** - Official specification
- **[ITS Example Templates](https://github.com/AlexanderParker/its-example-templates)** - Example templates

## License

MIT License - see the [LICENSE](LICENSE) file for details.
