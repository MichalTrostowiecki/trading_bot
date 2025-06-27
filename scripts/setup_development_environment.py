#!/usr/bin/env python3
"""
Development Environment Setup Script for Fibonacci Trading Bot

This script automates the setup of the development environment including:
- Git configuration
- Python virtual environment
- Dependencies installation
- Pre-commit hooks
- IDE configuration
- Initial project validation

Usage:
    python scripts/setup_development_environment.py
"""

import os
import sys
import subprocess
import json
import platform
from pathlib import Path
from typing import Dict, List, Optional

class DevelopmentSetup:
    """Handles the complete development environment setup."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.system = platform.system()
        self.python_executable = sys.executable
        self.errors: List[str] = []
        self.warnings: List[str] = []
        
    def run_command(self, command: List[str], check: bool = True, capture_output: bool = True) -> subprocess.CompletedProcess:
        """Run a command and handle errors."""
        try:
            result = subprocess.run(
                command, 
                check=check, 
                capture_output=capture_output, 
                text=True,
                cwd=self.project_root
            )
            return result
        except subprocess.CalledProcessError as e:
            error_msg = f"Command failed: {' '.join(command)}\nError: {e.stderr}"
            self.errors.append(error_msg)
            if check:
                raise
            return e
    
    def check_prerequisites(self) -> bool:
        """Check if all prerequisites are installed."""
        print("🔍 Checking prerequisites...")
        
        prerequisites = {
            'git': ['git', '--version'],
            'python': [self.python_executable, '--version'],
            'pip': [self.python_executable, '-m', 'pip', '--version']
        }
        
        missing = []
        for name, command in prerequisites.items():
            try:
                result = self.run_command(command, check=False)
                if result.returncode == 0:
                    print(f"  ✅ {name}: {result.stdout.strip()}")
                else:
                    missing.append(name)
                    print(f"  ❌ {name}: Not found")
            except Exception:
                missing.append(name)
                print(f"  ❌ {name}: Not found")
        
        if missing:
            print(f"\n❌ Missing prerequisites: {', '.join(missing)}")
            print("Please install the missing prerequisites and run this script again.")
            return False
        
        print("✅ All prerequisites found!")
        return True
    
    def setup_git_configuration(self) -> bool:
        """Set up Git configuration."""
        print("\n🔧 Setting up Git configuration...")
        
        try:
            # Check if user.name and user.email are configured
            name_result = self.run_command(['git', 'config', 'user.name'], check=False)
            email_result = self.run_command(['git', 'config', 'user.email'], check=False)
            
            if name_result.returncode != 0 or not name_result.stdout.strip():
                name = input("Enter your full name for Git commits: ")
                self.run_command(['git', 'config', 'user.name', name])
                print(f"  ✅ Set user.name to: {name}")
            else:
                print(f"  ✅ user.name already set: {name_result.stdout.strip()}")
            
            if email_result.returncode != 0 or not email_result.stdout.strip():
                email = input("Enter your email for Git commits: ")
                self.run_command(['git', 'config', 'user.email', email])
                print(f"  ✅ Set user.email to: {email}")
            else:
                print(f"  ✅ user.email already set: {email_result.stdout.strip()}")
            
            # Set up additional Git configurations
            git_configs = {
                'init.defaultBranch': 'main',
                'pull.rebase': 'false',
                'core.autocrlf': 'true' if self.system == 'Windows' else 'input',
                'core.editor': 'code --wait'
            }
            
            for key, value in git_configs.items():
                self.run_command(['git', 'config', key, value], check=False)
                print(f"  ✅ Set {key} to: {value}")
            
            # Check if we're in a Git repository
            result = self.run_command(['git', 'status'], check=False)
            if result.returncode != 0:
                print("  ⚠️  Not in a Git repository. Make sure to clone the repository first.")
                self.warnings.append("Not in a Git repository")
            
            return True
            
        except Exception as e:
            self.errors.append(f"Git configuration failed: {e}")
            return False
    
    def setup_python_environment(self) -> bool:
        """Set up Python virtual environment and install dependencies."""
        print("\n🐍 Setting up Python environment...")
        
        try:
            venv_path = self.project_root / 'venv'
            
            # Create virtual environment if it doesn't exist
            if not venv_path.exists():
                print("  📦 Creating virtual environment...")
                self.run_command([self.python_executable, '-m', 'venv', 'venv'])
                print("  ✅ Virtual environment created")
            else:
                print("  ✅ Virtual environment already exists")
            
            # Determine the correct Python executable in venv
            if self.system == 'Windows':
                venv_python = venv_path / 'Scripts' / 'python.exe'
                pip_executable = [str(venv_python), '-m', 'pip']
            else:
                venv_python = venv_path / 'bin' / 'python'
                pip_executable = [str(venv_python), '-m', 'pip']
            
            # Upgrade pip
            print("  📦 Upgrading pip...")
            self.run_command(pip_executable + ['install', '--upgrade', 'pip'])
            
            # Install requirements
            requirements_files = [
                'requirements.txt',
                'requirements-dev.txt',
                'requirements-test.txt'
            ]
            
            for req_file in requirements_files:
                req_path = self.project_root / req_file
                if req_path.exists():
                    print(f"  📦 Installing {req_file}...")
                    self.run_command(pip_executable + ['install', '-r', str(req_path)])
                    print(f"  ✅ Installed {req_file}")
                else:
                    print(f"  ⚠️  {req_file} not found, skipping...")
            
            return True
            
        except Exception as e:
            self.errors.append(f"Python environment setup failed: {e}")
            return False
    
    def setup_pre_commit_hooks(self) -> bool:
        """Set up pre-commit hooks."""
        print("\n🪝 Setting up pre-commit hooks...")
        
        try:
            # Check if pre-commit is installed
            venv_path = self.project_root / 'venv'
            if self.system == 'Windows':
                precommit_executable = [str(venv_path / 'Scripts' / 'python.exe'), '-m', 'pre_commit']
            else:
                precommit_executable = [str(venv_path / 'bin' / 'python'), '-m', 'pre_commit']
            
            # Install pre-commit hooks
            result = self.run_command(precommit_executable + ['install'], check=False)
            if result.returncode == 0:
                print("  ✅ Pre-commit hooks installed")
                
                # Run pre-commit on all files to set up the environment
                print("  🔍 Running pre-commit on all files (this may take a while)...")
                result = self.run_command(precommit_executable + ['run', '--all-files'], check=False)
                if result.returncode == 0:
                    print("  ✅ Pre-commit setup completed successfully")
                else:
                    print("  ⚠️  Pre-commit found some issues, but hooks are installed")
                    self.warnings.append("Pre-commit found formatting issues")
            else:
                print("  ❌ Failed to install pre-commit hooks")
                self.errors.append("Pre-commit installation failed")
                return False
            
            return True
            
        except Exception as e:
            self.errors.append(f"Pre-commit setup failed: {e}")
            return False
    
    def setup_ide_configuration(self) -> bool:
        """Set up IDE configuration files."""
        print("\n💻 Setting up IDE configuration...")
        
        try:
            # VS Code settings
            vscode_dir = self.project_root / '.vscode'
            vscode_dir.mkdir(exist_ok=True)
            
            vscode_settings = {
                "python.defaultInterpreterPath": "./venv/Scripts/python.exe" if self.system == 'Windows' else "./venv/bin/python",
                "python.linting.enabled": True,
                "python.linting.flake8Enabled": True,
                "python.linting.mypyEnabled": True,
                "python.formatting.provider": "black",
                "python.testing.pytestEnabled": True,
                "python.testing.pytestArgs": ["tests/"],
                "git.enableCommitSigning": False,
                "files.exclude": {
                    "**/__pycache__": True,
                    "**/.pytest_cache": True,
                    "**/.mypy_cache": True,
                    "**/venv": True
                },
                "python.analysis.typeCheckingMode": "basic"
            }
            
            settings_file = vscode_dir / 'settings.json'
            with open(settings_file, 'w') as f:
                json.dump(vscode_settings, f, indent=2)
            
            print("  ✅ VS Code settings configured")
            
            # Create launch configuration for debugging
            launch_config = {
                "version": "0.2.0",
                "configurations": [
                    {
                        "name": "Python: Current File",
                        "type": "python",
                        "request": "launch",
                        "program": "${file}",
                        "console": "integratedTerminal",
                        "cwd": "${workspaceFolder}"
                    },
                    {
                        "name": "Python: Trading Bot",
                        "type": "python",
                        "request": "launch",
                        "program": "${workspaceFolder}/src/main.py",
                        "console": "integratedTerminal",
                        "cwd": "${workspaceFolder}",
                        "env": {
                            "ENVIRONMENT": "development"
                        }
                    }
                ]
            }
            
            launch_file = vscode_dir / 'launch.json'
            with open(launch_file, 'w') as f:
                json.dump(launch_config, f, indent=2)
            
            print("  ✅ VS Code launch configuration created")
            
            return True
            
        except Exception as e:
            self.errors.append(f"IDE configuration failed: {e}")
            return False
    
    def validate_setup(self) -> bool:
        """Validate the setup by running basic tests."""
        print("\n🧪 Validating setup...")
        
        try:
            venv_path = self.project_root / 'venv'
            if self.system == 'Windows':
                python_executable = str(venv_path / 'Scripts' / 'python.exe')
            else:
                python_executable = str(venv_path / 'bin' / 'python')
            
            # Test Python imports
            test_imports = [
                'import pandas',
                'import numpy',
                'import pytest',
                'import black',
                'import flake8',
                'import mypy'
            ]
            
            for import_test in test_imports:
                result = self.run_command([python_executable, '-c', import_test], check=False)
                if result.returncode == 0:
                    print(f"  ✅ {import_test}")
                else:
                    print(f"  ❌ {import_test}")
                    self.warnings.append(f"Failed to import: {import_test}")
            
            # Test if we can run basic commands
            commands_to_test = [
                ([python_executable, '-m', 'black', '--version'], 'Black formatter'),
                ([python_executable, '-m', 'flake8', '--version'], 'Flake8 linter'),
                ([python_executable, '-m', 'pytest', '--version'], 'Pytest testing'),
            ]
            
            for command, description in commands_to_test:
                result = self.run_command(command, check=False)
                if result.returncode == 0:
                    print(f"  ✅ {description}")
                else:
                    print(f"  ❌ {description}")
                    self.warnings.append(f"Failed to run: {description}")
            
            return True
            
        except Exception as e:
            self.errors.append(f"Setup validation failed: {e}")
            return False
    
    def print_summary(self):
        """Print setup summary."""
        print("\n" + "="*60)
        print("🎉 DEVELOPMENT ENVIRONMENT SETUP COMPLETE!")
        print("="*60)
        
        if not self.errors and not self.warnings:
            print("✅ Setup completed successfully with no issues!")
        else:
            if self.warnings:
                print(f"⚠️  Setup completed with {len(self.warnings)} warnings:")
                for warning in self.warnings:
                    print(f"   • {warning}")
            
            if self.errors:
                print(f"❌ Setup completed with {len(self.errors)} errors:")
                for error in self.errors:
                    print(f"   • {error}")
        
        print("\n📋 NEXT STEPS:")
        print("1. Activate your virtual environment:")
        if self.system == 'Windows':
            print("   venv\\Scripts\\activate")
        else:
            print("   source venv/bin/activate")
        
        print("2. Read the documentation:")
        print("   • docs/GIT_WORKFLOW_GUIDE.md")
        print("   • docs/CORE_STRATEGY_SPECIFICATION.md")
        print("   • docs/PHASE_1_DETAILED_SPECIFICATION.md")
        
        print("3. Start development:")
        print("   git checkout -b feature/your-feature-name")
        print("   # Make your changes")
        print("   git add .")
        print("   git commit -m 'feat: your feature description'")
        
        print("\n🆘 NEED HELP?")
        print("• Check docs/GIT_COMMANDS_REFERENCE.md for Git help")
        print("• Review docs/DEPENDENCIES_MATRIX.md for dependency issues")
        print("• Open an issue on GitHub for project-specific questions")
    
    def run(self):
        """Run the complete setup process."""
        print("🚀 FIBONACCI TRADING BOT - DEVELOPMENT ENVIRONMENT SETUP")
        print("="*60)
        
        if not self.check_prerequisites():
            return False
        
        success = True
        success &= self.setup_git_configuration()
        success &= self.setup_python_environment()
        success &= self.setup_pre_commit_hooks()
        success &= self.setup_ide_configuration()
        success &= self.validate_setup()
        
        self.print_summary()
        return success

def main():
    """Main entry point."""
    setup = DevelopmentSetup()
    success = setup.run()
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
