"""
Deployer for artisan websites.

Handles:
- Copying template to new directory
- Updating config file
- Creating GitHub repository
- Deploying to Vercel
"""

import os
import shutil
import subprocess
import re
from typing import Dict, Any, Optional, Tuple
from pathlib import Path

# Configuration
TEMPLATE_PATH = Path(r"C:\Users\nadja\OneDrive\Bureau\code\plomberie-fluide-1")
OUTPUT_BASE_PATH = Path(r"C:\Users\nadja\OneDrive\Bureau\code\client-sites")
GITHUB_ORG = "artisan-sites"  # Change to your organization name


def slugify(text: str) -> str:
    """Convert text to URL-safe slug."""
    text = text.lower().strip()
    text = re.sub(r'[àâä]', 'a', text)
    text = re.sub(r'[éèêë]', 'e', text)
    text = re.sub(r'[îï]', 'i', text)
    text = re.sub(r'[ôö]', 'o', text)
    text = re.sub(r'[ùûü]', 'u', text)
    text = re.sub(r'[ç]', 'c', text)
    text = re.sub(r'[^a-z0-9]+', '-', text)
    text = text.strip('-')
    return text


def generate_repo_name(parsed_data: Dict[str, Any]) -> str:
    """Generate repository name from parsed data."""
    trade_type = parsed_data.get("trade_type", "artisan")
    city = parsed_data.get("city", "")
    business_name = parsed_data.get("business_name", "site")

    # French to English trade mapping
    trade_fr = {
        "plumber": "plombier",
        "electrician": "electricien",
        "roofer": "couvreur",
        "painter": "peintre",
        "hvac": "chauffagiste",
        "carpenter": "menuisier",
        "mason": "macon",
        "locksmith": "serrurier",
    }

    trade = trade_fr.get(trade_type, trade_type)

    parts = [trade]
    if city:
        parts.append(slugify(city))
    parts.append(slugify(business_name))

    return "-".join(parts)[:50]  # GitHub limit


def prepare_site_directory(
    parsed_data: Dict[str, Any],
    config_content: str,
    photos_dir: Optional[str] = None
) -> Tuple[Path, str]:
    """
    Prepare site directory by copying template and updating config.

    Args:
        parsed_data: Parsed form data
        config_content: Generated TypeScript config content
        photos_dir: Optional path to client photos

    Returns:
        Tuple of (site_path, repo_name)
    """
    repo_name = generate_repo_name(parsed_data)
    site_path = OUTPUT_BASE_PATH / repo_name

    # Create output base if it doesn't exist
    OUTPUT_BASE_PATH.mkdir(parents=True, exist_ok=True)

    # Remove existing directory if it exists
    if site_path.exists():
        shutil.rmtree(site_path)

    # Copy template
    shutil.copytree(
        TEMPLATE_PATH,
        site_path,
        ignore=shutil.ignore_patterns(
            'node_modules',
            '.git',
            'dist',
            '.env',
            '*.log'
        )
    )

    # Update config file
    config_path = site_path / "src" / "config" / "artisan.config.ts"
    with open(config_path, 'w', encoding='utf-8') as f:
        f.write(config_content)

    # Copy photos if provided
    if photos_dir and os.path.exists(photos_dir):
        assets_dir = site_path / "public" / "assets"
        assets_dir.mkdir(parents=True, exist_ok=True)

        for filename in os.listdir(photos_dir):
            if filename.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
                src = Path(photos_dir) / filename
                dst = assets_dir / filename
                shutil.copy2(src, dst)

    # Update package.json name
    package_json_path = site_path / "package.json"
    if package_json_path.exists():
        with open(package_json_path, 'r', encoding='utf-8') as f:
            content = f.read()

        content = re.sub(
            r'"name":\s*"[^"]*"',
            f'"name": "{repo_name}"',
            content
        )

        with open(package_json_path, 'w', encoding='utf-8') as f:
            f.write(content)

    return site_path, repo_name


def run_command(command: str, cwd: Optional[Path] = None) -> Tuple[int, str, str]:
    """Run a shell command and return result."""
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "Command timed out"
    except Exception as e:
        return -1, "", str(e)


def init_git_repo(site_path: Path) -> bool:
    """Initialize git repository."""
    commands = [
        "git init",
        "git add .",
        'git commit -m "Initial commit: Generated artisan website"',
    ]

    for cmd in commands:
        code, stdout, stderr = run_command(cmd, cwd=site_path)
        if code != 0:
            print(f"Git command failed: {cmd}")
            print(f"Error: {stderr}")
            return False

    return True


def create_github_repo(repo_name: str, site_path: Path, use_org: bool = True) -> Optional[str]:
    """
    Create GitHub repository using gh CLI.

    Args:
        repo_name: Name for the repository
        site_path: Path to the local repo
        use_org: Whether to create in organization

    Returns:
        GitHub repo URL or None if failed
    """
    # Create repo
    org_flag = f"--org {GITHUB_ORG}" if use_org else ""
    cmd = f'gh repo create {repo_name} --public --source="{site_path}" --push {org_flag}'

    code, stdout, stderr = run_command(cmd, cwd=site_path)

    if code != 0:
        print(f"GitHub repo creation failed: {stderr}")
        # Try without organization
        if use_org:
            print("Trying without organization...")
            cmd = f'gh repo create {repo_name} --public --source="{site_path}" --push'
            code, stdout, stderr = run_command(cmd, cwd=site_path)

            if code != 0:
                print(f"GitHub repo creation still failed: {stderr}")
                return None

    # Get repo URL
    if use_org:
        return f"https://github.com/{GITHUB_ORG}/{repo_name}"
    else:
        # Get username
        code, stdout, stderr = run_command("gh api user --jq .login")
        username = stdout.strip() if code == 0 else "user"
        return f"https://github.com/{username}/{repo_name}"


def deploy_to_vercel(site_path: Path, repo_name: str) -> Optional[str]:
    """
    Deploy to Vercel using vercel CLI.

    Args:
        site_path: Path to the site directory
        repo_name: Name to use for the project

    Returns:
        Vercel deployment URL or None if failed
    """
    # Install dependencies first
    print("Installing dependencies...")
    code, _, stderr = run_command("npm install", cwd=site_path)
    if code != 0:
        print(f"npm install failed: {stderr}")
        return None

    # Build the project
    print("Building project...")
    code, _, stderr = run_command("npm run build", cwd=site_path)
    if code != 0:
        print(f"Build failed: {stderr}")
        return None

    # Deploy to Vercel
    print("Deploying to Vercel...")
    cmd = f'vercel --prod --yes --name="{repo_name}"'
    code, stdout, stderr = run_command(cmd, cwd=site_path)

    if code != 0:
        print(f"Vercel deployment failed: {stderr}")
        return None

    # Extract URL from output
    url_match = re.search(r'https://[^\s]+\.vercel\.app', stdout)
    if url_match:
        return url_match.group(0)

    # Try to get from vercel CLI
    code, stdout, stderr = run_command("vercel ls --json", cwd=site_path)
    if code == 0:
        import json
        try:
            data = json.loads(stdout)
            if data and len(data) > 0:
                return f"https://{data[0].get('url', '')}"
        except:
            pass

    return f"https://{repo_name}.vercel.app"


def deploy_site(
    parsed_data: Dict[str, Any],
    config_content: str,
    photos_dir: Optional[str] = None,
    skip_github: bool = False,
    skip_vercel: bool = False
) -> Dict[str, Any]:
    """
    Full deployment pipeline.

    Args:
        parsed_data: Parsed form data
        config_content: Generated config content
        photos_dir: Optional path to client photos
        skip_github: Skip GitHub repo creation
        skip_vercel: Skip Vercel deployment

    Returns:
        Dictionary with deployment results
    """
    result = {
        "success": False,
        "site_path": None,
        "repo_name": None,
        "github_url": None,
        "vercel_url": None,
        "errors": [],
    }

    try:
        # Step 1: Prepare directory
        print("Preparing site directory...")
        site_path, repo_name = prepare_site_directory(
            parsed_data,
            config_content,
            photos_dir
        )
        result["site_path"] = str(site_path)
        result["repo_name"] = repo_name
        print(f"Site prepared at: {site_path}")

        # Step 2: Initialize git
        print("Initializing git repository...")
        if not init_git_repo(site_path):
            result["errors"].append("Git initialization failed")

        # Step 3: Create GitHub repo
        if not skip_github:
            print("Creating GitHub repository...")
            github_url = create_github_repo(repo_name, site_path)
            if github_url:
                result["github_url"] = github_url
                print(f"GitHub repo created: {github_url}")
            else:
                result["errors"].append("GitHub repo creation failed")

        # Step 4: Deploy to Vercel
        if not skip_vercel:
            print("Deploying to Vercel...")
            vercel_url = deploy_to_vercel(site_path, repo_name)
            if vercel_url:
                result["vercel_url"] = vercel_url
                print(f"Deployed to: {vercel_url}")
            else:
                result["errors"].append("Vercel deployment failed")

        result["success"] = len(result["errors"]) == 0

    except Exception as e:
        result["errors"].append(str(e))
        print(f"Deployment failed: {e}")

    return result


def check_prerequisites() -> Dict[str, bool]:
    """Check if required CLI tools are installed and authenticated."""
    checks = {
        "git": False,
        "gh": False,
        "gh_auth": False,
        "vercel": False,
        "vercel_auth": False,
        "node": False,
        "npm": False,
    }

    # Check git
    code, _, _ = run_command("git --version")
    checks["git"] = code == 0

    # Check GitHub CLI
    code, _, _ = run_command("gh --version")
    checks["gh"] = code == 0

    if checks["gh"]:
        code, _, _ = run_command("gh auth status")
        checks["gh_auth"] = code == 0

    # Check Vercel CLI
    code, _, _ = run_command("vercel --version")
    checks["vercel"] = code == 0

    if checks["vercel"]:
        code, _, _ = run_command("vercel whoami")
        checks["vercel_auth"] = code == 0

    # Check Node.js
    code, _, _ = run_command("node --version")
    checks["node"] = code == 0

    # Check npm
    code, _, _ = run_command("npm --version")
    checks["npm"] = code == 0

    return checks


def open_terminal_for_auth(auth_type: str) -> bool:
    """
    Open a terminal window for interactive authentication.

    Args:
        auth_type: Either 'gh' for GitHub or 'vercel' for Vercel

    Returns:
        True if terminal was opened successfully
    """
    import platform

    system = platform.system()

    if auth_type == "gh":
        command = "gh auth login"
        title = "GitHub Authentication"
    elif auth_type == "vercel":
        command = "vercel login"
        title = "Vercel Authentication"
    else:
        return False

    try:
        if system == "Windows":
            # Open new cmd window that stays open after command
            subprocess.Popen(
                f'start "{title}" cmd /k "{command}"',
                shell=True
            )
        elif system == "Darwin":  # macOS
            subprocess.Popen(
                f'''osascript -e 'tell app "Terminal" to do script "{command}"' ''',
                shell=True
            )
        else:  # Linux
            # Try common terminal emulators
            terminals = [
                f'gnome-terminal -- bash -c "{command}; exec bash"',
                f'xterm -e "{command}; exec bash"',
                f'konsole -e "{command}"',
            ]
            for term_cmd in terminals:
                try:
                    subprocess.Popen(term_cmd, shell=True)
                    break
                except:
                    continue
        return True
    except Exception as e:
        print(f"Failed to open terminal: {e}")
        return False


def install_cli_tool(tool: str) -> bool:
    """
    Install a CLI tool.

    Args:
        tool: Either 'gh' for GitHub CLI or 'vercel' for Vercel CLI

    Returns:
        True if installation command was started
    """
    import platform

    system = platform.system()

    if tool == "gh":
        if system == "Windows":
            # Use winget or chocolatey
            command = "winget install --id GitHub.cli"
        elif system == "Darwin":
            command = "brew install gh"
        else:
            command = "sudo apt install gh || sudo dnf install gh"
        title = "Install GitHub CLI"
    elif tool == "vercel":
        command = "npm install -g vercel"
        title = "Install Vercel CLI"
    else:
        return False

    try:
        if system == "Windows":
            subprocess.Popen(
                f'start "{title}" cmd /k "{command}"',
                shell=True
            )
        else:
            subprocess.Popen(
                f'gnome-terminal -- bash -c "{command}; exec bash"',
                shell=True
            )
        return True
    except Exception as e:
        print(f"Failed to start installation: {e}")
        return False


if __name__ == "__main__":
    # Check prerequisites
    print("Checking prerequisites...")
    prereqs = check_prerequisites()
    for tool, status in prereqs.items():
        status_str = "✓" if status else "✗"
        print(f"  {status_str} {tool}")

    if not all(prereqs.values()):
        print("\nSome prerequisites are missing. Please install:")
        if not prereqs["gh"]:
            print("  - GitHub CLI: https://cli.github.com/")
        if not prereqs["gh_auth"]:
            print("  - Run: gh auth login")
        if not prereqs["vercel"]:
            print("  - Vercel CLI: npm i -g vercel")
        if not prereqs["vercel_auth"]:
            print("  - Run: vercel login")
