"""
ITS Compiler CLI

Command-line interface for the ITS Compiler Python library.
Converts Instruction Template Specification (ITS) templates into structured AI prompts.
"""

__version__ = "1.0.4"
__author__ = "Alexander Parker"
__email__ = "pypi@parker.im"

from .main import main

__all__ = ["main"]
