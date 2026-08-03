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

### Published type libraries

Templates import instruction types through `extends`. The specification publishes these libraries under `https://alexanderparker.github.io/instruction-template-specification/schema/v1.0/`:

| Library        | File                         | Purpose                                                                                                                                |
| -------------- | ---------------------------- | -------------------------------------------------------------------------------------------------------------------------------------- |
| Standard Types | `its-standard-types-v1.json` | Prose content: titles, lists, paragraphs, tables, dialogue and more                                                                    |
| JSON Types     | `its-json-types-v1.json`     | Value fills inside JSON structure authored in the template: json_string, json_number, json_value, json_array_items, json_object_fields |
| HTML Types     | `its-html-types-v1.json`     | Fills inside literal markup: html_text, html_fragment, html_list_items, html_table_rows, html_form_fields                              |
| YAML Types     | `its-yaml-types-v1.json`     | Fills inside literal YAML: yaml_value, yaml_list_items, yaml_block                                                                     |

The structured-output libraries instruct the model to emit raw output with no markdown code fences and no commentary, for example:

```bash
# A template extending the JSON types library
its-compile api-response-template.json

# Developing an unpublished type library locally
its-compile template.json --allow-local-schemas
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
  --allow-local-schemas   Allow extends to resolve local file paths
                          relative to the template
  --interactive-allowlist / --no-interactive-allowlist
                          Enable/disable interactive schema prompts
  --security-report FILE  Generate security analysis report to specified file
  --supported-schema-version
                          Show the supported ITS specification version and exit
  --allowlist-status      Show schema allowlist status
  --add-trusted-schema URL
                          Add a schema URL to the permanent allowlist and exit
  --remove-schema URL     Remove a schema URL from the allowlist and exit
  --export-allowlist FILE
                          Export allowlist to specified file and exit
  --import-allowlist FILE
                          Import allowlist from specified file and exit
  --merge-allowlist       Merge imported allowlist with existing
                          (use with --import-allowlist)
  --cleanup-allowlist     Remove old unused allowlist entries and exit
  --older-than DAYS       Days threshold for cleanup (default: 90)
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

The CLI honours the core library's full `ITS_*` environment surface. Alongside the three above:

- `ITS_ALLOW_HTTP` - Allow HTTP URLs
- `ITS_ALLOW_LOCAL_SCHEMAS` - Allow extends to resolve local file paths relative to the template
- `ITS_BLOCK_LOCALHOST` - Block localhost access
- `ITS_DOMAIN_ALLOWLIST` - Comma-separated allowed domains
- `ITS_MAX_TEMPLATE_SIZE` - Max template size in bytes
- `ITS_MAX_CONTENT_ELEMENTS` - Max content elements
- `ITS_MAX_NESTING_DEPTH` - Max content/variable nesting depth
- `ITS_MAX_VARIABLE_COUNT` - Max total variables including nested values
- `ITS_MAX_VARIABLE_ARRAY_ITEMS` - Max items per variable array
- `ITS_MAX_TEXT_LENGTH` - Max length of a text element or string value
- `ITS_DISABLE_ALLOWLIST` - Disable schema allowlist
- `ITS_DISABLE_INPUT_VALIDATION` - Disable input validation

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

## ITS ecosystem

- [Specification](https://alexanderparker.github.io/instruction-template-specification/) - the ITS spec, schemas and documentation ([source](https://github.com/AlexanderParker/instruction-template-specification))
- [Template studio demo](https://alexanderparker.github.io/its-template-studio/) - build and compile templates in the browser ([source](https://github.com/AlexanderParker/its-template-studio))
- [its-template-editor](https://github.com/AlexanderParker/its-wysiwyg-common) - the WYSIWYG React editor component behind the studio
- [its-compiler-js](https://github.com/AlexanderParker/its-compiler-js) - JavaScript/TypeScript reference compiler ([npm](https://www.npmjs.com/package/its-compiler-js))
- [its-compiler-python](https://github.com/AlexanderParker/its-compiler-python) - Python reference compiler library ([PyPI](https://pypi.org/project/its-compiler/))
- [its-compiler-dotnet](https://github.com/AlexanderParker/its-compiler-dotnet) - .NET compiler with ASP.NET service and Azure Functions samples ([NuGet](https://www.nuget.org/packages/InstructionTemplateSpecification.Compiler))
- [its-example-templates](https://github.com/AlexanderParker/its-example-templates) - example and test templates exercising the published schemas

## License

MIT License - see the [LICENSE](LICENSE) file for details.
