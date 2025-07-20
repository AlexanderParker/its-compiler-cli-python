"""
Command-line interface for ITS Compiler with comprehensive security enhancements.
Fixed for cross-platform Unicode compatibility and URL template support.
"""

import json
import os
import platform
import sys
import tempfile
import time
import urllib.parse
import urllib.request
from pathlib import Path as PathType
from typing import Any, Dict, Optional, Tuple

import click

# Import from the core library
from its_compiler import (
    AllowlistManager,
    ITSCompilationError,
    ITSCompiler,
    ITSConfig,
    ITSError,
    ITSSecurityError,
    ITSValidationError,
    SecurityConfig,
    TrustLevel,
    __supported_schema_version__,
)
from its_compiler import __version__ as core_version
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

# CLI version
__version__ = "0.1.0"


def setup_safe_console() -> Tuple[Console, bool]:
    """Setup console with Windows compatibility."""
    is_windows = platform.system() == "Windows"
    console = Console(
        force_terminal=True,
        legacy_windows=is_windows,
        safe_box=is_windows,
        color_system="auto",
    )
    return console, not is_windows


def safe_print(message: Any, style: Optional[str] = None, highlight: Optional[bool] = None) -> None:
    """Print message safely with Rich formatting."""
    try:
        console.print(message, style=style, highlight=highlight)
    except Exception:
        # Fallback to plain print
        print(str(message))


def create_safe_progress_context(description: str, disable_on_windows: bool = True) -> Any:
    """Create a progress context that's safe for Windows."""
    if platform.system() == "Windows" and disable_on_windows:
        # On Windows, use a simple context manager that just prints status
        class SimpleProgress:
            def __init__(self, description: str):
                self.description = description
                self.started = False

            def __enter__(self) -> "SimpleProgress":
                safe_print(f"[blue]{self.description}[/blue]")
                self.started = True
                return self

            def __exit__(self, *args: Any) -> None:
                if self.started:
                    safe_print("[green]Complete[/green]")

            def add_task(self, description: str, total: Optional[int] = None) -> int:
                return 0  # Dummy task ID

            def update(self, task_id: int, **kwargs: Any) -> None:
                pass  # No-op

        return SimpleProgress(description)
    else:
        # On non-Windows or when Unicode is supported, use Rich Progress
        try:
            return Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
                disable=False,
            )
        except Exception:
            # Fallback to simple progress if Rich fails
            return create_safe_progress_context(description, disable_on_windows=True)


# Initialize console
try:
    console, CAN_USE_UNICODE = setup_safe_console()
except Exception:
    # Emergency fallback
    console = Console(force_terminal=True, legacy_windows=True)
    CAN_USE_UNICODE = False


def get_status_styles() -> Dict[str, str]:
    """Get Rich styles for status messages."""
    return {"success": "bold green", "error": "bold red", "warning": "bold yellow", "info": "bold blue", "dim": "dim"}


STATUS_STYLES = get_status_styles()


def is_url(path: str) -> bool:
    """Check if the path is a URL."""
    try:
        result = urllib.parse.urlparse(path)
        return all([result.scheme, result.netloc])
    except Exception:
        return False


def download_template(url: str, security_config: SecurityConfig) -> str:
    """Download template from URL and return local temp file path."""
    try:
        # Basic URL validation
        if not url.startswith(("https://", "http://")):
            raise ValueError("Only HTTP/HTTPS URLs are supported")

        if not security_config.network.allow_http and url.startswith("http://"):
            raise ValueError("HTTP URLs are not allowed. Use HTTPS or enable --allow-http")

        safe_print(f"[INFO] Downloading template from: {url}", style=STATUS_STYLES["info"])

        # Create a temporary file
        temp_file = tempfile.NamedTemporaryFile(mode="w+", suffix=".json", delete=False)
        temp_path = temp_file.name
        temp_file.close()

        # Download with timeout
        timeout = getattr(security_config.network, "request_timeout", 30)

        # Create request with validation - bandit B310 safe usage
        request = urllib.request.Request(url)
        with urllib.request.urlopen(request, timeout=timeout) as response:  # nosec B310
            if response.status != 200:
                raise ValueError(f"Failed to download: HTTP {response.status}")

            content = response.read().decode("utf-8")

            # Validate it's JSON
            try:
                json.loads(content)
            except json.JSONDecodeError:
                raise ValueError("Downloaded content is not valid JSON")

            # Write to temp file
            with open(temp_path, "w", encoding="utf-8") as f:
                f.write(content)

        safe_print("Template downloaded to temporary file", style=STATUS_STYLES["info"])
        return temp_path

    except Exception as e:
        safe_print(f"[ERROR] Failed to download template: {e}", style=STATUS_STYLES["error"])
        sys.exit(1)


class TemplateChangeHandler(FileSystemEventHandler):
    """Handler for template file changes in watch mode."""

    def __init__(
        self,
        template_path: str,
        output_path: Optional[str],
        variables_path: Optional[str],
        verbose: bool,
        security_config: SecurityConfig,
    ):
        self.template_path = PathType(template_path)
        self.output_path = output_path
        self.variables_path = variables_path
        self.verbose = verbose
        self.security_config = security_config

    def on_modified(self, event: Any) -> None:
        if event.is_directory:
            return

        changed_path = PathType(event.src_path)
        if changed_path.name == self.template_path.name:
            safe_print(f"[INFO] File changed: {changed_path}", style=STATUS_STYLES["info"])
            try:
                success = compile_template(
                    str(self.template_path),
                    self.output_path,
                    self.variables_path,
                    False,  # validate_only
                    self.verbose,
                    False,  # watch
                    False,  # no_cache
                    self.security_config,
                    None,  # security_report
                    watch_mode=True,  # Pass watch_mode=True
                )

                if success:
                    safe_print("[SUCCESS] Watch compilation successful", style=STATUS_STYLES["success"])
                else:
                    safe_print("[INFO] Waiting for fixes... (Ctrl+C to stop)", style=STATUS_STYLES["info"])
            except (
                ITSSecurityError,
                ITSValidationError,
                ITSCompilationError,
                ITSError,
            ) as e:
                # Handle ITS-specific errors gracefully in watch mode
                safe_print(f"[ERROR] Compilation failed: {e}", style=STATUS_STYLES["error"])
                if self.verbose:
                    if hasattr(e, "details") and e.details:
                        safe_print(f"Details: {e.details}", style=STATUS_STYLES["dim"])
                    if hasattr(e, "path") and e.path:
                        safe_print(f"Path: {e.path}", style=STATUS_STYLES["dim"])
                safe_print("[INFO] Continuing to watch for changes...", style=STATUS_STYLES["info"])
            except Exception as e:
                # Handle any other unexpected errors
                safe_print(f"[ERROR] Unexpected error: {e}", style=STATUS_STYLES["error"])
                if self.verbose:
                    import traceback

                    safe_print("Error details:", style=STATUS_STYLES["dim"])
                    for line in traceback.format_exc().splitlines():
                        safe_print(f"  {line}", style=STATUS_STYLES["dim"])
                safe_print("[INFO] Continuing to watch for changes...", style=STATUS_STYLES["info"])


def load_variables(variables_path: str) -> Dict[str, Any]:
    """Load variables from JSON file with security validation."""
    try:
        variables_file = PathType(variables_path)

        # Basic security checks on variables file
        if variables_file.stat().st_size > 10 * 1024 * 1024:  # 10MB limit
            safe_print(f"[ERROR] Variables file too large: {variables_path}", style=STATUS_STYLES["error"])
            sys.exit(1)

        with open(variables_path, "r", encoding="utf-8") as f:
            variables = json.load(f)

        if not isinstance(variables, dict):
            safe_print("[ERROR] Variables file must contain a JSON object", style=STATUS_STYLES["error"])
            sys.exit(1)

        return variables

    except FileNotFoundError:
        raise click.ClickException(f"Variables file not found: {variables_path}")
    except json.JSONDecodeError as e:
        raise click.ClickException(f"Invalid JSON in variables file: {e}")
    except PermissionError:
        raise click.ClickException(f"Permission denied accessing variables file: {variables_path}")


def create_security_config(
    allow_http: bool,
    interactive_allowlist: Optional[bool],
    strict_mode: bool,
) -> SecurityConfig:
    """Create security configuration from CLI options."""

    # Start with environment-based config
    config = SecurityConfig.from_environment()

    # Override with CLI options
    if allow_http:
        config.network.allowed_protocols.add("http")
        config.network.allow_http = True

    if interactive_allowlist is not None:
        config.allowlist.interactive_mode = interactive_allowlist

    if strict_mode:
        config.processing.max_template_size = 512 * 1024  # 512KB
        config.network.max_response_size = 5 * 1024 * 1024  # 5MB
        config.processing.max_content_elements = 500
        config.processing.max_nesting_depth = 8

    return config


def handle_allowlist_commands(
    security_config: SecurityConfig,
    add_trusted_schema: Optional[str],
    remove_schema: Optional[str],
    export_allowlist: Optional[PathType],
    import_allowlist: Optional[PathType],
    merge_allowlist: bool,
    cleanup_allowlist: bool,
    older_than: int,
    allowlist_status: bool,
) -> bool:
    """Handle allowlist management commands. Returns True if a command was executed."""

    if not any(
        [
            add_trusted_schema,
            remove_schema,
            export_allowlist,
            import_allowlist,
            cleanup_allowlist,
            allowlist_status,
        ]
    ):
        return False

    try:
        allowlist_manager = AllowlistManager(security_config)

        if allowlist_status:
            stats = allowlist_manager.get_stats()

            # Use safe table creation
            try:
                table = Table(title="Schema Allowlist Status", show_header=True)
                table.add_column("Metric", style="cyan")
                table.add_column("Value", style="green")

                for key, value in stats.items():
                    if key != "most_used":
                        table.add_row(key.replace("_", " ").title(), str(value))

                console.print(table)
            except Exception:
                safe_print("Schema Allowlist Status:")
                for key, value in stats.items():
                    if key != "most_used":
                        safe_print(f"  {key.replace('_', ' ').title()}: {value}")

            if stats.get("most_used"):
                safe_print("\nMost Used Schemas:", style=STATUS_STYLES["info"])
                for schema in stats["most_used"]:
                    safe_print(f"  • {schema['url']} (used {schema['use_count']} times)")

        if add_trusted_schema:
            allowlist_manager.add_trusted_url(add_trusted_schema, TrustLevel.PERMANENT, "Added via CLI")
            safe_print(f"[SUCCESS] Added trusted schema: {add_trusted_schema}", style=STATUS_STYLES["success"])

        if remove_schema:
            if allowlist_manager.remove_url(remove_schema):
                safe_print(f"[SUCCESS] Removed schema: {remove_schema}", style=STATUS_STYLES["success"])
            else:
                safe_print(f"[WARNING] Schema not found in allowlist: {remove_schema}", style=STATUS_STYLES["warning"])

        if export_allowlist:
            allowlist_manager.export_allowlist(export_allowlist)
            safe_print(f"[SUCCESS] Exported allowlist to: {export_allowlist}", style=STATUS_STYLES["success"])

        if import_allowlist:
            imported_count = allowlist_manager.import_allowlist(import_allowlist, merge=merge_allowlist)
            mode = "merged" if merge_allowlist else "imported"
            safe_print(
                f"[SUCCESS] {mode.title()} {imported_count} entries from: {import_allowlist}",
                style=STATUS_STYLES["success"],
            )

        if cleanup_allowlist:
            removed_count = allowlist_manager.cleanup_old_entries(days=older_than)
            safe_print(
                f"[SUCCESS] Cleaned up {removed_count} old entries (older than {older_than} days)",
                style=STATUS_STYLES["success"],
            )

        return True

    except Exception as e:
        safe_print(f"[ERROR] Error managing allowlist: {e}", style=STATUS_STYLES["error"])
        sys.exit(1)


def compile_template(
    template_path: str,
    output_path: Optional[str],
    variables_path: Optional[str],
    validate_only: bool,
    verbose: bool,
    watch: bool,
    no_cache: bool,
    security_config: SecurityConfig,
    security_report_path: Optional[str],
    watch_mode: bool = False,
) -> bool:
    """Compile a template file with security controls."""

    # Load variables if provided
    variables: Dict[str, Any] = {}
    if variables_path:
        try:
            variables = load_variables(variables_path)
            if verbose:
                safe_print(
                    f"[INFO] Loaded {len(variables)} variables from {variables_path}", style=STATUS_STYLES["info"]
                )
        except Exception as e:
            error_msg = f"Failed to load variables: {e}"
            safe_print(f"[ERROR] {error_msg}", style=STATUS_STYLES["error"])
            if not watch_mode:
                sys.exit(1)
            return False

    # Configure compiler
    config = ITSConfig(cache_enabled=not no_cache, report_overrides=verbose)

    try:
        compiler = ITSCompiler(config, security_config)

        # Show security status if verbose
        if verbose:
            security_status = compiler.get_security_status()
            safe_print("Security Configuration:", style=STATUS_STYLES["info"])
            safe_print(f"  HTTP allowed: {security_config.network.allow_http}")
            safe_print(f"  Interactive allowlist: {security_config.allowlist.interactive_mode}")
            safe_print(f"  Block localhost: {security_config.network.block_localhost}")

            enabled_features = [k for k, v in security_status["features"].items() if v]
            if enabled_features:
                safe_print(f"Security Features: {', '.join(enabled_features)}", style=STATUS_STYLES["info"])

        start_time = time.time()

        if validate_only:
            # Validation only
            with create_safe_progress_context("Validating template...") as progress:
                task = progress.add_task("Validating template...", total=None)
                validation_result = compiler.validate_file(template_path)
                progress.update(task, completed=True)

            if validation_result.is_valid:
                safe_print("[SUCCESS] Template is valid", style=STATUS_STYLES["success"])
                if validation_result.warnings and verbose:
                    for warning in validation_result.warnings:
                        safe_print(f"[WARNING] {warning}", style=STATUS_STYLES["warning"])
                if validation_result.security_issues and verbose:
                    for issue in validation_result.security_issues:
                        safe_print(f"[WARNING] Security: {issue}", style=STATUS_STYLES["warning"])
                return True
            else:
                safe_print("[ERROR] Template validation failed", style=STATUS_STYLES["error"])
                for error in validation_result.errors:
                    safe_print(f"Error: {error}", style=STATUS_STYLES["error"])
                for issue in validation_result.security_issues:
                    safe_print(f"Security: {issue}", style=STATUS_STYLES["error"])
                if not watch_mode:
                    sys.exit(1)
                return False
        else:
            # Full compilation
            with create_safe_progress_context("Compiling template...") as progress:
                task = progress.add_task("Compiling template...", total=None)
                compilation_result = compiler.compile_file(template_path, variables)
                progress.update(task, completed=True)

            # Show compilation success
            compilation_time = time.time() - start_time
            safe_print(
                f"[SUCCESS] Template compiled successfully ({compilation_time:.2f}s)", style=STATUS_STYLES["success"]
            )

            # Show security metrics, overrides, warnings, etc.
            if verbose:
                if compilation_result.overrides:
                    safe_print("Type Overrides:", style=STATUS_STYLES["warning"])
                    for type_override in compilation_result.overrides:
                        safe_print(
                            (
                                f"  {type_override.type_name}: "
                                f"{type_override.override_source} -> "
                                f"{type_override.overridden_source}"
                            )
                        )

                if compilation_result.warnings:
                    safe_print("Warnings:", style=STATUS_STYLES["warning"])
                    for warning in compilation_result.warnings:
                        safe_print(f"  {warning}")

            # Output result
            if output_path:
                output_file = PathType(output_path)

                # Security check on output path
                if not _is_safe_output_path(output_file):
                    error_msg = f"Unsafe output path: {output_path}"
                    safe_print(f"[ERROR] {error_msg}", style=STATUS_STYLES["error"])
                    if not watch_mode:
                        sys.exit(1)
                    return False

                try:
                    output_file.parent.mkdir(parents=True, exist_ok=True)
                    with open(output_file, "w", encoding="utf-8") as f:
                        f.write(compilation_result.prompt)
                    safe_print(f"[INFO] Output written to: {output_path}", style=STATUS_STYLES["info"])
                except PermissionError:
                    error_msg = f"Permission denied writing to: {output_path}"
                    safe_print(f"[ERROR] {error_msg}", style=STATUS_STYLES["error"])
                    if not watch_mode:
                        sys.exit(1)
                    return False
            else:
                safe_print("\n" + "=" * 80)
                safe_print(compilation_result.prompt)
                safe_print("=" * 80)

        # Generate security report if requested
        if security_report_path and hasattr(compiler, "generate_security_report"):
            try:
                report = compiler.generate_security_report(template_path)
                with open(security_report_path, "w", encoding="utf-8") as f:
                    json.dump(report.to_dict(), f, indent=2)
                safe_print(f"[INFO] Security report written to: {security_report_path}", style=STATUS_STYLES["info"])
            except Exception as e:
                safe_print(f"[WARNING] Failed to generate security report: {e}", style=STATUS_STYLES["warning"])

        return True

    except ITSSecurityError as e:
        safe_print(f"[ERROR] Security Error: {e.get_user_message()}", style=STATUS_STYLES["error"])
        if verbose and e.threat_type:
            safe_print(f"Threat Type: {e.threat_type}", style=STATUS_STYLES["dim"])
        if not watch_mode:
            sys.exit(1)
        return False

    except ITSValidationError as e:
        safe_print(f"[ERROR] Validation Error: {e.message}", style=STATUS_STYLES["error"])
        if e.path:
            safe_print(f"Path: {e.path}", style=STATUS_STYLES["dim"])
        for error in e.validation_errors:
            safe_print(f"  • {error}", style=STATUS_STYLES["error"])
        for issue in e.security_issues:
            safe_print(f"  • Security: {issue}", style=STATUS_STYLES["error"])
        if not watch_mode:
            sys.exit(1)
        return False

    except ITSCompilationError as e:
        safe_print(f"[ERROR] Compilation Error: {e.get_context_message()}", style=STATUS_STYLES["error"])
        if not watch_mode:
            sys.exit(1)
        return False

    except ITSError as e:
        safe_print(f"[ERROR] ITS Error: {e.get_user_message()}", style=STATUS_STYLES["error"])
        if verbose:
            safe_print(f"Details: {e.details}", style=STATUS_STYLES["dim"])
        if not watch_mode:
            sys.exit(1)
        return False

    except Exception as e:
        safe_print(f"[ERROR] Unexpected error: {e}", style=STATUS_STYLES["error"])
        if verbose:
            import traceback

            traceback.print_exc()
        if not watch_mode:
            sys.exit(1)
        return False


def _is_safe_output_path(output_path: PathType) -> bool:
    """Check if output path is safe to write to."""
    try:
        # Resolve to absolute path
        resolved = output_path.resolve()
        path_str = str(resolved)

        # Check for dangerous patterns that could indicate path traversal or injection
        # Note: Removed ":" from dangerous patterns as it's legitimate in Windows drive letters
        dangerous_patterns = ["..", "%", "<", ">", "|", '"', "?", "*"]

        for pattern in dangerous_patterns:
            if pattern in path_str:
                return False

        # Check if trying to write to system directories
        import platform

        if platform.system() == "Windows":
            system_dirs = ["C:\\Windows", "C:\\System32", "C:\\Program Files", "C:\\Program Files (x86)"]
            # Case-insensitive comparison for Windows
            check_path = path_str.upper()
            for sys_dir in system_dirs:
                if check_path.startswith(sys_dir.upper()):
                    return False
        else:
            system_dirs = ["/etc", "/bin", "/sbin", "/usr/bin", "/usr/sbin", "/proc", "/sys", "/dev", "/boot"]
            for sys_dir in system_dirs:
                if path_str.startswith(sys_dir):
                    return False

        return True
    except Exception:
        return False


@click.command()
@click.argument("template_file", type=str, required=False)
@click.option(
    "-o",
    "--output",
    type=click.Path(),
    help="Output file (default: stdout)",
)
@click.option(
    "-v",
    "--variables",
    type=click.Path(exists=True),
    help="JSON file with variable values",
)
@click.option("-w", "--watch", is_flag=True, help="Watch template file for changes")
@click.option("--validate-only", is_flag=True, help="Validate template without compiling")
@click.option("--verbose", is_flag=True, help="Show detailed output including security metrics")
@click.option("--strict", is_flag=True, help="Enable strict validation mode")
@click.option("--no-cache", is_flag=True, help="Disable schema caching")
@click.option("--timeout", type=int, default=30, help="Network timeout in seconds")
@click.option(
    "--allow-http",
    is_flag=True,
    help="Allow HTTP URLs (not recommended for production)",
)
@click.option(
    "--interactive-allowlist/--no-interactive-allowlist",
    default=None,
    help="Enable/disable interactive schema allowlist prompts",
)
@click.option(
    "--security-report",
    type=click.Path(),
    help="Generate security analysis report to specified file",
)
@click.option(
    "--supported-schema-version",
    is_flag=True,
    help="Show the supported ITS specification version and exit",
)
# Allowlist management options
@click.option("--allowlist-status", is_flag=True, help="Show allowlist status and exit")
@click.option(
    "--add-trusted-schema",
    type=str,
    help="Add a schema URL to the permanent allowlist and exit",
)
@click.option("--remove-schema", type=str, help="Remove a schema URL from the allowlist and exit")
@click.option(
    "--export-allowlist",
    type=click.Path(),
    help="Export allowlist to specified file and exit",
)
@click.option(
    "--import-allowlist",
    type=click.Path(exists=True),
    help="Import allowlist from specified file and exit",
)
@click.option(
    "--merge-allowlist",
    is_flag=True,
    help="Merge imported allowlist with existing (use with --import-allowlist)",
)
@click.option(
    "--cleanup-allowlist",
    is_flag=True,
    help="Remove old unused allowlist entries and exit",
)
@click.option(
    "--older-than",
    type=int,
    default=90,
    help="Days threshold for cleanup (default: 90)",
)
@click.version_option(version=f"CLI: {__version__}, Core: {core_version}")
def main(
    template_file: Optional[str],
    output: Optional[PathType],
    variables: Optional[PathType],
    watch: bool,
    validate_only: bool,
    verbose: bool,
    strict: bool,
    no_cache: bool,
    timeout: int,
    allow_http: bool,
    interactive_allowlist: Optional[bool],
    security_report: Optional[PathType],
    supported_schema_version: bool,
    allowlist_status: bool,
    add_trusted_schema: Optional[str],
    remove_schema: Optional[str],
    export_allowlist: Optional[PathType],
    import_allowlist: Optional[PathType],
    merge_allowlist: bool,
    cleanup_allowlist: bool,
    older_than: int,
) -> None:
    """
    ITS Compiler CLI - Convert ITS templates to AI prompts with security controls.

    TEMPLATE_FILE: Path to the ITS template JSON file to compile, or URL to download from.
    """

    # Handle --supported-schema-version flag
    if supported_schema_version:
        safe_print(f"ITS Compiler CLI v{__version__}")
        safe_print(f"ITS Compiler Core v{core_version}")
        safe_print(f"Supported ITS Specification Version: {__supported_schema_version__}")
        return

    # Create security configuration
    security_config = create_security_config(allow_http, interactive_allowlist, strict)

    # Validate security configuration
    config_warnings = security_config.validate()
    if config_warnings and verbose:
        for warning in config_warnings:
            safe_print(f"[WARNING] Config Warning: {warning}", style=STATUS_STYLES["warning"])

    # Handle allowlist management commands
    if handle_allowlist_commands(
        security_config,
        add_trusted_schema,
        remove_schema,
        export_allowlist,
        import_allowlist,
        merge_allowlist,
        cleanup_allowlist,
        older_than,
        allowlist_status,
    ):
        return  # Exit after handling allowlist commands

    # Template file is required for compilation/validation
    if not template_file:
        safe_print("[ERROR] Template file is required for compilation", style=STATUS_STYLES["error"])
        safe_print("Use --help for available commands or provide a template file or URL.")
        sys.exit(1)

    # Handle URL vs local file
    temp_file_path = None
    actual_template_path = template_file

    if is_url(template_file):
        # Download from URL
        temp_file_path = download_template(template_file, security_config)
        actual_template_path = temp_file_path
    else:
        # Validate local file exists
        if not PathType(template_file).exists():
            safe_print(f"[ERROR] Template file not found: {template_file}", style=STATUS_STYLES["error"])
            sys.exit(1)

    if watch and validate_only:
        raise click.ClickException("Cannot use --watch with --validate-only")

    if watch and is_url(template_file):
        raise click.ClickException("Cannot use --watch with URL templates")

    try:
        # Initial compilation
        compile_template(
            actual_template_path,
            str(output) if output else None,
            str(variables) if variables else None,
            validate_only,
            verbose,
            watch,
            no_cache,
            security_config,
            str(security_report) if security_report else None,
        )

        # Watch mode (only for local files)
        if watch:
            safe_print(
                f"\n[INFO] Watching {template_file} for changes... (Press Ctrl+C to stop)", style=STATUS_STYLES["info"]
            )

            event_handler = TemplateChangeHandler(
                actual_template_path,
                str(output) if output else None,
                str(variables) if variables else None,
                verbose,
                security_config,
            )

            observer = Observer()
            observer.schedule(event_handler, str(PathType(actual_template_path).parent), recursive=False)
            observer.start()

            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                safe_print("\n[WARNING] Stopping watch mode...", style=STATUS_STYLES["warning"])
                observer.stop()
            observer.join()

    finally:
        # Clean up temporary file if we downloaded one
        if temp_file_path:
            try:
                os.unlink(temp_file_path)
                if verbose:
                    safe_print("[INFO] Cleaned up temporary file", style=STATUS_STYLES["info"])
            except OSError:
                # Ignore file cleanup errors - file may already be deleted
                if verbose:
                    safe_print("[WARNING] Could not clean up temporary file", style=STATUS_STYLES["warning"])


if __name__ == "__main__":
    main()
