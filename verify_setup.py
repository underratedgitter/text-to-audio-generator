"""Setup verification script for the audio-only pipeline."""

import sys
import yaml
from pathlib import Path

# Color codes for console output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def check_python_version():
    """Check Python version"""
    print(f"\n{Colors.BLUE}Checking Python version...{Colors.END}")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print(f"{Colors.GREEN}✓ Python {version.major}.{version.minor}.{version.micro}{Colors.END}")
        return True
    else:
        print(f"{Colors.RED}✗ Python 3.8+ required, found {version.major}.{version.minor}.{version.micro}{Colors.END}")
        return False

def check_package(package_name, import_name=None):
    """Check if a package is installed"""
    if import_name is None:
        import_name = package_name
    
    try:
        __import__(import_name)
        print(f"{Colors.GREEN}✓ {package_name}{Colors.END}")
        return True
    except ImportError:
        print(f"{Colors.RED}✗ {package_name} not installed{Colors.END}")
        return False

def check_ffmpeg():
    """Check if FFmpeg is installed"""
    print(f"\n{Colors.BLUE}Checking FFmpeg...{Colors.END}")
    print(f"{Colors.YELLOW}⚠ FFmpeg not required for audio-only mode{Colors.END}")
    return True

def check_env_file():
    """Check if .env file exists and has required keys"""
    print(f"\n{Colors.BLUE}Checking .env configuration...{Colors.END}")
    
    env_file = Path('.env')
    if not env_file.exists():
        print(f"{Colors.RED}✗ .env file not found{Colors.END}")
        print(f"{Colors.YELLOW}  Create it from .env.example{Colors.END}")
        return False
    
    required_keys = []
    optional_keys = []
    
    with open(env_file, 'r') as f:
        content = f.read()
    
    all_good = True
    if not required_keys:
        print(f"{Colors.GREEN}✓ No required API keys for current configuration{Colors.END}")
    for key in required_keys:
        if key in content and not content.split(key)[1].split('\n')[0].strip('= ').startswith('your_'):
            print(f"{Colors.GREEN}✓ {key} configured{Colors.END}")
        else:
            print(f"{Colors.RED}✗ {key} not configured{Colors.END}")
            all_good = False
    
    for key in optional_keys:
        if key in content and not content.split(key)[1].split('\n')[0].strip('= ').startswith('your_'):
            print(f"{Colors.GREEN}✓ {key} configured (optional){Colors.END}")
        else:
            print(f"{Colors.YELLOW}⚠ {key} not configured (optional){Colors.END}")
    
    return all_good

def check_config_file():
    """Check if config.yaml exists"""
    print(f"\n{Colors.BLUE}Checking configuration files...{Colors.END}")
    
    config_file = Path('config/config.yaml')
    if config_file.exists():
        print(f"{Colors.GREEN}✓ config/config.yaml found{Colors.END}")
        return True
    else:
        print(f"{Colors.RED}✗ config/config.yaml not found{Colors.END}")
        return False

def check_directories():
    """Check if required directories exist"""
    print(f"\n{Colors.BLUE}Checking directory structure...{Colors.END}")
    
    required_dirs = ['src', 'config', 'output', 'logs']
    all_exist = True
    
    for dir_name in required_dirs:
        dir_path = Path(dir_name)
        if dir_path.exists():
            print(f"{Colors.GREEN}✓ {dir_name}/{Colors.END}")
        else:
            print(f"{Colors.RED}✗ {dir_name}/ not found{Colors.END}")
            all_exist = False
    
    return all_exist

def main():
    """Run all checks"""
    print(f"""
{Colors.BLUE}{'='*60}
Text-to-Audio Pipeline - Setup Verification
{'='*60}{Colors.END}
""")
    
    results = []
    
    # Check Python version
    results.append(check_python_version())
    
    # Check required packages
    print(f"\n{Colors.BLUE}Checking Python packages...{Colors.END}")
    packages = [
        ('pyyaml', 'yaml'),
        ('python-dotenv', 'dotenv'),
        ('edge-tts', 'edge_tts'),
        ('gtts', 'gtts'),
        ('pydub', 'pydub'),
    ]
    
    for package_name, import_name in packages:
        results.append(check_package(package_name, import_name))
    
    # Check FFmpeg
    results.append(check_ffmpeg())
    
    # Check .env file
    results.append(check_env_file())
    
    # Check config file
    results.append(check_config_file())
    
    # Check directories
    results.append(check_directories())
    
    # Summary
    print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"{Colors.GREEN}✓ All checks passed ({passed}/{total})!{Colors.END}")
        print(f"\n{Colors.GREEN}You're ready to generate audio!{Colors.END}")
        print(f"{Colors.BLUE}Run: python src/main.py{Colors.END}")
    else:
        failed = total - passed
        print(f"{Colors.YELLOW}⚠ {passed}/{total} checks passed, {failed} issues found{Colors.END}")
        print(f"\n{Colors.YELLOW}Please address the issues above before running the pipeline.{Colors.END}")
    
    print(f"{Colors.BLUE}{'='*60}{Colors.END}\n")

if __name__ == '__main__':
    main()
