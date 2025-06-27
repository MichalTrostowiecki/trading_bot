#!/usr/bin/env python3
"""
Development Environment Setup Script
Automated setup for the Fibonacci Trading Bot development environment.
"""

import os
import sys
import subprocess
import platform
from pathlib import Path
from typing import List, Optional


class EnvironmentSetup:
    """Automated development environment setup."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.venv_path = self.project_root / "venv"
        self.is_windows = platform.system() == "Windows"
        
    def run_command(self, command: List[str], check: bool = True) -> subprocess.CompletedProcess:
        """Run a command and return the result."""
        print(f"Running: {' '.join(command)}")
        try:
            result = subprocess.run(
                command, 
                check=check, 
                capture_output=True, 
                text=True,
                cwd=self.project_root
            )
            if result.stdout:
                print(result.stdout)
            return result
        except subprocess.CalledProcessError as e:
            print(f"Error running command: {e}")
            if e.stderr:
                print(f"Error output: {e.stderr}")
            if check:
                raise
            return e
    
    def check_python_version(self) -> bool:
        """Check if Python 3.9+ is available."""
        print("Checking Python version...")
        
        if sys.version_info < (3, 9):
            print(f"❌ Python 3.9+ required, found {sys.version}")
            return False
        
        print(f"✅ Python {sys.version} - OK")
        return True
    
    def create_virtual_environment(self) -> bool:
        """Create Python virtual environment."""
        print("\nCreating virtual environment...")
        
        if self.venv_path.exists():
            print("Virtual environment already exists, skipping creation")
            return True
        
        try:
            self.run_command([sys.executable, "-m", "venv", str(self.venv_path)])
            print("✅ Virtual environment created successfully")
            return True
        except subprocess.CalledProcessError:
            print("❌ Failed to create virtual environment")
            return False
    
    def get_pip_executable(self) -> str:
        """Get the pip executable path for the virtual environment."""
        if self.is_windows:
            return str(self.venv_path / "Scripts" / "pip.exe")
        else:
            return str(self.venv_path / "bin" / "pip")
    
    def install_dependencies(self) -> bool:
        """Install project dependencies."""
        print("\nInstalling dependencies...")
        
        pip_exe = self.get_pip_executable()
        
        # Upgrade pip first
        try:
            self.run_command([pip_exe, "install", "--upgrade", "pip"])
            print("✅ Pip upgraded successfully")
        except subprocess.CalledProcessError:
            print("❌ Failed to upgrade pip")
            return False
        
        # Install production dependencies
        requirements_file = self.project_root / "requirements.txt"
        if requirements_file.exists():
            try:
                self.run_command([pip_exe, "install", "-r", str(requirements_file)])
                print("✅ Production dependencies installed")
            except subprocess.CalledProcessError:
                print("❌ Failed to install production dependencies")
                return False
        
        # Install development dependencies
        dev_requirements_file = self.project_root / "requirements-dev.txt"
        if dev_requirements_file.exists():
            try:
                self.run_command([pip_exe, "install", "-r", str(dev_requirements_file)])
                print("✅ Development dependencies installed")
            except subprocess.CalledProcessError:
                print("❌ Failed to install development dependencies")
                return False
        
        return True
    
    def setup_pre_commit_hooks(self) -> bool:
        """Install pre-commit hooks."""
        print("\nSetting up pre-commit hooks...")
        
        pip_exe = self.get_pip_executable()
        
        try:
            # Install pre-commit if not already installed
            self.run_command([pip_exe, "install", "pre-commit"])
            
            # Install hooks
            if self.is_windows:
                python_exe = str(self.venv_path / "Scripts" / "python.exe")
            else:
                python_exe = str(self.venv_path / "bin" / "python")
            
            self.run_command([python_exe, "-m", "pre_commit", "install"])
            print("✅ Pre-commit hooks installed")
            return True
        except subprocess.CalledProcessError:
            print("❌ Failed to install pre-commit hooks")
            return False
    
    def create_configuration_file(self) -> bool:
        """Create development configuration file."""
        print("\nSetting up configuration...")
        
        config_dir = self.project_root / "config"
        template_file = config_dir / "development.yaml.template"
        config_file = config_dir / "development.yaml"
        
        if config_file.exists():
            print("Development configuration already exists")
            return True
        
        if template_file.exists():
            try:
                import shutil
                shutil.copy2(template_file, config_file)
                print("✅ Development configuration created from template")
                print(f"📝 Please edit {config_file} with your MT5 credentials")
                return True
            except Exception as e:
                print(f"❌ Failed to create configuration file: {e}")
                return False
        else:
            print("❌ Configuration template not found")
            return False
    
    def verify_installation(self) -> bool:
        """Verify the installation is working."""
        print("\nVerifying installation...")
        
        if self.is_windows:
            python_exe = str(self.venv_path / "Scripts" / "python.exe")
        else:
            python_exe = str(self.venv_path / "bin" / "python")
        
        # Test Python imports
        test_imports = [
            "import pandas",
            "import numpy", 
            "import MetaTrader5",
            "import fastapi",
            "import pytest"
        ]
        
        for import_test in test_imports:
            try:
                self.run_command([python_exe, "-c", import_test])
                print(f"✅ {import_test} - OK")
            except subprocess.CalledProcessError:
                print(f"❌ {import_test} - FAILED")
                return False
        
        return True
    
    def print_next_steps(self):
        """Print next steps for the user."""
        print("\n" + "="*60)
        print("🎉 SETUP COMPLETE!")
        print("="*60)
        
        if self.is_windows:
            activate_cmd = r"venv\Scripts\activate"
        else:
            activate_cmd = "source venv/bin/activate"
        
        print(f"""
Next steps:
1. Activate virtual environment:
   {activate_cmd}

2. Configure your MT5 credentials:
   Edit config/development.yaml

3. Test the setup:
   python -c "import src; print('Setup successful!')"

4. Start development:
   - Check Phase 1 tasks in docs/PHASE_1_DETAILED_SPECIFICATION.md
   - Run tests: pytest tests/ -v
   - Start coding!

📚 Documentation: See docs/ directory for detailed guides
🐛 Issues: Check troubleshooting section in docs/
""")
    
    def run_setup(self) -> bool:
        """Run the complete setup process."""
        print("🚀 Fibonacci Trading Bot - Development Environment Setup")
        print("="*60)
        
        steps = [
            ("Checking Python version", self.check_python_version),
            ("Creating virtual environment", self.create_virtual_environment),
            ("Installing dependencies", self.install_dependencies),
            ("Setting up pre-commit hooks", self.setup_pre_commit_hooks),
            ("Creating configuration", self.create_configuration_file),
            ("Verifying installation", self.verify_installation),
        ]
        
        for step_name, step_func in steps:
            print(f"\n📋 {step_name}...")
            if not step_func():
                print(f"\n❌ Setup failed at: {step_name}")
                return False
        
        self.print_next_steps()
        return True


def main():
    """Main entry point."""
    setup = EnvironmentSetup()
    
    try:
        success = setup.run_setup()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n❌ Setup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()