# ITS Compiler CLI

[![PyPI version](https://badge.fury.io/py/its-compiler-cli.svg)](https://badge.fury.io/py/its-compiler-cli)
[![Python](https://img.shields.io/pypi/pyversions/its-compiler-cli.svg)](https://pypi.org/project/its-compiler-cli/)
[![License](https://img.shields.io/github/license/AlexanderParker/its-compiler-cli-python.svg)](LICENSE)

Command-line interface for the [ITS Compiler Python](https://github.com/alexanderparker/its-compiler-python) library. Converts [Instruction Template Specification (ITS)](https://alexanderparker.github.io/instruction-template-specification/) templates into structured AI prompts.

> **New to ITS?** See the [specification documentation](https://alexanderparker.github.io/instruction-template-specification/) for complete details on the template format and concepts.

## Quick Example

**Input Template (`blog-post.json`):**

```json
{
  "$schema": "https://alexanderparker.github.io/instruction-template-specification/schema/v1.0/its-base-schema-v1.json",
  "version": "1.0.0",
  "extends": ["https://alexanderparker.github.io/instruction-template-specification/schema/v1.0/its-standard-types-v1.json"],
  "variables": {
    "topic": "sustainable technology",
    "includeExamples": true
  },
  "content": [
    {
      "type": "text",
      "text": "# "
    },
    {
      "type": "placeholder",
      "instructionType": "title",
      "config": {
        "description": "Create an engaging blog post title about ${topic}",
        "style": "catchy",
        "length": "short"
      }
    },
    {
      "type": "conditional",
      "condition": "includeExamples == true",
      "content": [
        {
          "type": "text",
          "text": "\n\n## Examples\n\n"
        },
        {
          "type": "placeholder",
          "instructionType": "list",
          "config": {
            "description": "List 4 examples of ${topic}",
            "format": "bullet_points",
            "itemCount": 4
          }
        }
      ]
    }
  ]
}
```

**Compilation:**

```bash
its-compile blog-post.json --output blog-prompt.txt
```

**Generated Prompt:**

```
INTRODUCTION

You are an AI assistant that fills in content templates. Follow the instructions exactly and replace each placeholder with appropriate content based on the user prompts provided. Respond only with the transformed content.

INSTRUCTIONS

1. Replace each placeholder marked with << >> with generated content
2. The user's content request is wrapped in ([{< >}]) to distinguish it from instructions
3. Follow the format requirements specified after each user prompt
4. Maintain the existing structure and formatting of the template
5. Only replace the placeholders - do not modify any other text
6. Generate content that matches the tone and style requested
7. Respond only with the transformed content - do not include any explanations or additional text

TEMPLATE

# <<Replace this placeholder with a title using this user prompt: ([{<Create an engaging blog post title about sustainable technology>}]). Format requirements: Create a catchy title that is short in length.>>

## Examples

<<Replace this placeholder with a list using this user prompt: ([{<List 4 examples of sustainable technology>}]). Format requirements: Use bullet_points formatting with each item on a new line. Create exactly 4 items.>>
```

## Installation

```bash
pip install its-compiler-cli
```

This will automatically install the core [its-compiler](https://github.com/alexanderparker/its-compiler-python) library as a dependency.

## CLI Reference

```
its-compile [OPTIONS] TEMPLATE_FILE

Arguments:
  TEMPLATE_FILE  Path to the ITS template JSON file to compile

Options:
  -o, --output FILE          Output file (default: stdout)
  -v, --variables FILE       JSON file with variable values
  -w, --watch               Watch template file for changes
  --validate-only           Validate template without compiling
  --verbose                 Show detailed output including security metrics
  --strict                  Enable strict validation mode
  --no-cache               Disable schema caching
  --timeout INTEGER        Network timeout in seconds (default: 30)
  --allow-http             Allow HTTP URLs (not recommended for production)
  --interactive-allowlist / --no-interactive-allowlist
                           Enable/disable interactive schema allowlist prompts
  --security-report FILE   Generate security analysis report to specified file
  --supported-schema-version
                           Show supported ITS specification version and exit
  --allowlist-status       Show schema allowlist status and exit
  --add-trusted-schema URL Add a schema URL to the permanent allowlist and exit
  --remove-schema URL      Remove a schema URL from the allowlist and exit
  --export-allowlist FILE  Export allowlist to specified file and exit
  --import-allowlist FILE  Import allowlist from specified file and exit
  --merge-allowlist        Merge imported allowlist with existing
  --cleanup-allowlist      Remove old unused allowlist entries and exit
  --older-than INTEGER     Days threshold for cleanup (default: 90)
  --version                Show the version and exit
  --help                   Show this message and exit
```

## Quick Start

### Basic Compilation

```bash
# Compile template to stdout
its-compile template.json

# Output to file
its-compile template.json --output prompt.txt

# Use custom variables
its-compile template.json --variables vars.json

# Validate without compiling
its-compile template.json --validate-only
```

### Development Workflow

```bash
# Watch mode for rapid iteration
its-compile template.json --watch

# Strict validation for production
its-compile template.json --strict

# Verbose output for debugging
its-compile template.json --verbose
```

### Security Features

```bash
# Check allowlist status
its-compile --allowlist-status

# Add trusted schema
its-compile --add-trusted-schema https://example.com/schema.json

# Generate security report
its-compile template.json --security-report security.json
```

## Features

### Complete ITS v1.0 Support

- All standard instruction types (list, paragraph, table, etc.)
- Variables with `${variable}` syntax, including object properties and arrays
- Conditional content with Python-like expressions
- Schema extension mechanism with override precedence
- Custom instruction types

### Developer Tools

- Error messages with context and suggestions
- Override reporting shows which types are being replaced
- Watch mode for rapid development iteration
- Validation with detailed feedback
- Cross-platform Unicode support

### Security Features

The CLI includes comprehensive security features:

- **Schema Allowlist** - Control which schema URLs are permitted
- **Expression Validation** - Validate conditional expressions for safety
- **Input Validation** - Scan content for problematic patterns
- **SSRF Protection** - Block private networks and validate URLs
- **Rate Limiting** - Prevent abuse and DoS attacks

## Configuration

### Environment Variables

**Network Security:**

- `ITS_ALLOW_HTTP` - Allow HTTP URLs (default: false)
- `ITS_BLOCK_LOCALHOST` - Block localhost access (default: true)
- `ITS_REQUEST_TIMEOUT` - Network timeout in seconds (default: 10)
- `ITS_DOMAIN_ALLOWLIST` - Comma-separated allowed domains

**Schema Allowlist:**

- `ITS_INTERACTIVE_ALLOWLIST` - Enable interactive prompts (default: true)
- `ITS_ALLOWLIST_FILE` - Custom allowlist file location

**Processing Limits:**

- `ITS_MAX_TEMPLATE_SIZE` - Max template size in bytes (default: 1MB)
- `ITS_MAX_CONTENT_ELEMENTS` - Max content elements (default: 1000)

**Feature Toggles:**

- `ITS_DISABLE_ALLOWLIST` - Disable schema allowlist
- `ITS_DISABLE_INPUT_VALIDATION` - Disable input validation

### Interactive Allowlist

When `ITS_INTERACTIVE_ALLOWLIST` is enabled, you'll be prompted for unknown schemas:

```
SCHEMA ALLOWLIST DECISION REQUIRED
URL: https://example.com/schema.json

1. Allow permanently (saved to allowlist)
2. Allow for this session only
3. Deny (compilation will fail)
```

### Allowlist Management

```bash
# View current status
its-compile --allowlist-status

# Add trusted schema
its-compile --add-trusted-schema https://example.com/schema.json

# Remove schema
its-compile --remove-schema https://example.com/schema.json

# Export for backup
its-compile --export-allowlist backup.json

# Import from backup
its-compile --import-allowlist backup.json

# Clean up old entries
its-compile --cleanup-allowlist --older-than 30
```

## Error Handling

The CLI provides detailed error messages with context:

### Schema Validation Errors

```
✗ Validation Error: Template validation failed at content[2].config:
  • Missing required property 'description'
  • Invalid instruction type 'unknown_type'
```

### Variable Resolution Errors

```
✗ Variable Error: Undefined variable reference at content[1].config.description:
  • Variable '${productName}' is not defined
  • Available variables: productType, featureCount
```

### Security Errors

```
✗ Security Error: Malicious content detected in template
  • Dangerous pattern found: <script>
  • Location: content[0].text
```

## Testing

Use the included test runner to validate your CLI installation:

```bash
# Download and run the test runner
curl -O https://raw.githubusercontent.com/AlexanderParker/its-compiler-cli-python/main/test_runner.py
python test_runner.py

# Run specific test categories
python test_runner.py --category security
python test_runner.py --category integration

# Test with custom compiler command
python test_runner.py --compiler /path/to/its-compile
```

## Integration with Core Library

This CLI is a thin wrapper around the [its-compiler-python](https://github.com/alexanderparker/its-compiler-python) core library. For programmatic access or advanced features, use the core library directly:

```python
from its_compiler import ITSCompiler

compiler = ITSCompiler()
result = compiler.compile_file('template.json')
print(result.prompt)
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

## Related Projects

- **[ITS Compiler Python](https://github.com/alexanderparker/its-compiler-python)** - Core library for template compilation
- **[Instruction Template Specification](https://alexanderparker.github.io/instruction-template-specification/)** - The official ITS specification and schema
- **[ITS Example Templates](https://github.com/AlexanderParker/its-example-templates)** - Test templates and examples

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
