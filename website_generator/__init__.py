"""
Website Generator Module

Automates the creation of customized artisan websites from Google Form responses.

Components:
- parser.py: Parses email content from Google Form responses
- config_generator.py: Generates TypeScript config files
- deployer.py: Handles GitHub repo creation and Vercel deployment
- trade_defaults.py: Trade-specific defaults (Python version)
"""

from .parser import parse_email_content
from .config_generator import generate_config
from .trade_defaults import TRADE_DEFAULTS, get_trade_services
from .deployer import (
    deploy_site,
    check_prerequisites,
    open_terminal_for_auth,
    install_cli_tool,
)

__all__ = [
    'parse_email_content',
    'generate_config',
    'TRADE_DEFAULTS',
    'get_trade_services',
    'deploy_site',
    'check_prerequisites',
    'open_terminal_for_auth',
    'install_cli_tool',
]
