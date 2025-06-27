"""
Trading Bot Setup Script
Automated setup and deployment script for the Fibonacci Trading Bot.
"""

import os
import sys
import subprocess
import platform
from pathlib import Path
import json
import shutil
from typing import Dict, Any, List

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class TradingBotSetup:
    """Trading bot setup and deployment manager."""
    
    def __init__(self):
        self.project_root = project_root
        self.system = platform.system().lower()
        self.is_windows = self.system == 'windows'
        
        print("🎯 Fibonacci Trading Bot Setup")
        print("=" * 50)
        print(f"📍 Project Root: {self.project_root}")
        print(f"💻 System: {platform.system()} {platform.release()}")
        print(f"🐍 Python: {sys.version}")
        print("=" * 50 + "\n")
    
    def check_prerequisites(self) -> bool:
        """Check system prerequisites."""
        print("🔍 Checking prerequisites...")
        
        try:
            # Check Python version
            if sys.version_info < (3, 9):
                print("❌ Python 3.9+ required")
                return False
            print("✅ Python version OK")
            
            # Check if MetaTrader 5 is available (Windows only)
            if self.is_windows:
                try:
                    import MetaTrader5
                    print("✅ MetaTrader 5 Python package available")
                except ImportError:
                    print("⚠️  MetaTrader 5 Python package not found - will install")
            
            # Check pip
            try:
                subprocess.run([sys.executable, "-m", "pip", "--version"], 
                             check=True, capture_output=True)
                print("✅ pip available")
            except subprocess.CalledProcessError:
                print("❌ pip not available")
                return False
            
            print("✅ Prerequisites check passed\n")
            return True
            
        except Exception as e:
            print(f"❌ Prerequisites check failed: {e}")
            return False
    
    def install_dependencies(self) -> bool:
        """Install Python dependencies."""
        print("📦 Installing dependencies...")
        
        try:
            # Upgrade pip first
            print("Upgrading pip...")
            subprocess.run([
                sys.executable, "-m", "pip", "install", "--upgrade", "pip"
            ], check=True)
            
            # Install requirements
            requirements_file = self.project_root / "requirements.txt"
            if requirements_file.exists():
                print("Installing main requirements...")
                subprocess.run([
                    sys.executable, "-m", "pip", "install", "-r", str(requirements_file)
                ], check=True)
            
            # Install development requirements
            dev_requirements_file = self.project_root / "requirements-dev.txt"
            if dev_requirements_file.exists():
                print("Installing development requirements...")
                subprocess.run([
                    sys.executable, "-m", "pip", "install", "-r", str(dev_requirements_file)
                ], check=True)
            
            # Windows-specific packages
            if self.is_windows:
                print("Installing Windows-specific packages...")
                windows_packages = [
                    "pywin32",
                    "wmi"
                ]
                for package in windows_packages:
                    try:
                        subprocess.run([
                            sys.executable, "-m", "pip", "install", package
                        ], check=True)
                        print(f"✅ Installed {package}")
                    except subprocess.CalledProcessError:
                        print(f"⚠️  Failed to install {package}")
            
            print("✅ Dependencies installed successfully\n")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install dependencies: {e}")
            return False
        except Exception as e:
            print(f"❌ Unexpected error installing dependencies: {e}")
            return False
    
    def setup_directories(self) -> bool:
        """Setup required directories."""
        print("📁 Setting up directories...")
        
        try:
            directories = [
                "data/historical",
                "data/live",
                "data/models",
                "logs",
                "config",
                "notebooks/research"
            ]
            
            for directory in directories:
                dir_path = self.project_root / directory
                dir_path.mkdir(parents=True, exist_ok=True)
                print(f"✅ Created directory: {directory}")
            
            print("✅ Directories setup completed\n")
            return True
            
        except Exception as e:
            print(f"❌ Failed to setup directories: {e}")
            return False
    
    def setup_configuration(self) -> bool:
        """Setup configuration files."""
        print("⚙️  Setting up configuration...")
        
        try:
            config_dir = self.project_root / "config"
            
            # Copy template files if they don't exist
            templates = {
                "development.yaml.template": "development.yaml",
                "production.yaml.template": "production.yaml",
                "strategy_parameters.yaml.template": "strategy_parameters.yaml"
            }
            
            for template, target in templates.items():
                template_path = config_dir / template
                target_path = config_dir / target
                
                if template_path.exists() and not target_path.exists():
                    shutil.copy2(template_path, target_path)
                    print(f"✅ Created config file: {target}")
                elif target_path.exists():
                    print(f"ℹ️  Config file already exists: {target}")
                else:
                    print(f"⚠️  Template not found: {template}")
            
            # Create .env file if it doesn't exist
            env_file = self.project_root / ".env"
            env_example = self.project_root / ".env.example"
            
            if env_example.exists() and not env_file.exists():
                shutil.copy2(env_example, env_file)
                print("✅ Created .env file from template")
                print("⚠️  Please edit .env file with your MT5 credentials")
            
            print("✅ Configuration setup completed\n")
            return True
            
        except Exception as e:
            print(f"❌ Failed to setup configuration: {e}")
            return False
    
    def test_mt5_connection(self) -> bool:
        """Test MetaTrader 5 connection."""
        print("🔌 Testing MT5 connection...")
        
        try:
            if not self.is_windows:
                print("ℹ️  MT5 testing skipped (not Windows)")
                return True
            
            # Run MT5 connection test
            test_script = self.project_root / "scripts" / "test_mt5_connection.py"
            if test_script.exists():
                result = subprocess.run([
                    sys.executable, str(test_script)
                ], capture_output=True, text=True, timeout=30)
                
                if result.returncode == 0:
                    print("✅ MT5 connection test passed")
                    return True
                else:
                    print("❌ MT5 connection test failed")
                    print(f"Error: {result.stderr}")
                    return False
            else:
                print("⚠️  MT5 test script not found")
                return True
                
        except subprocess.TimeoutExpired:
            print("❌ MT5 connection test timed out")
            return False
        except Exception as e:
            print(f"❌ MT5 connection test error: {e}")
            return False
    
    def setup_windows_service(self) -> bool:
        """Setup Windows service for VPS deployment."""
        if not self.is_windows:
            print("ℹ️  Windows service setup skipped (not Windows)")
            return True
        
        print("🔧 Setting up Windows service...")
        
        try:
            response = input("Do you want to install the Windows service? (y/n): ").lower().strip()
            
            if response == 'y':
                service_script = self.project_root / "src" / "utils" / "windows_service.py"
                
                if service_script.exists():
                    # Install the service
                    result = subprocess.run([
                        sys.executable, str(service_script), "install"
                    ], capture_output=True, text=True)
                    
                    if result.returncode == 0:
                        print("✅ Windows service installed successfully")
                        print("ℹ️  Use 'python src/utils/windows_service.py start' to start the service")
                        return True
                    else:
                        print("❌ Failed to install Windows service")
                        print(f"Error: {result.stderr}")
                        return False
                else:
                    print("❌ Windows service script not found")
                    return False
            else:
                print("ℹ️  Windows service installation skipped")
                return True
                
        except Exception as e:
            print(f"❌ Windows service setup error: {e}")
            return False
    
    def create_startup_scripts(self) -> bool:
        """Create startup scripts for easy execution."""
        print("📄 Creating startup scripts...")
        
        try:
            scripts_dir = self.project_root / "scripts"
            scripts_dir.mkdir(exist_ok=True)
            
            if self.is_windows:
                # Windows batch file
                batch_content = f"""@echo off
cd /d "{self.project_root}"
python main.py
pause
"""
                batch_file = scripts_dir / "start_trading_bot.bat"
                with open(batch_file, 'w') as f:
                    f.write(batch_content)
                print("✅ Created start_trading_bot.bat")
                
                # Service management batch file
                service_content = f"""@echo off
echo Fibonacci Trading Bot Service Manager
echo =====================================
echo 1. Install Service
echo 2. Start Service
echo 3. Stop Service
echo 4. Uninstall Service
echo 5. Run in Debug Mode
echo.
set /p choice="Enter your choice (1-5): "

if "%choice%"=="1" (
    python "{self.project_root}/src/utils/windows_service.py" install
) else if "%choice%"=="2" (
    python "{self.project_root}/src/utils/windows_service.py" start
) else if "%choice%"=="3" (
    python "{self.project_root}/src/utils/windows_service.py" stop
) else if "%choice%"=="4" (
    python "{self.project_root}/src/utils/windows_service.py" uninstall
) else if "%choice%"=="5" (
    python "{self.project_root}/src/utils/windows_service.py" debug
) else (
    echo Invalid choice
)

pause
"""
                service_file = scripts_dir / "service_manager.bat"
                with open(service_file, 'w') as f:
                    f.write(service_content)
                print("✅ Created service_manager.bat")
            
            else:
                # Linux/Mac shell script
                shell_content = f"""#!/bin/bash
cd "{self.project_root}"
python main.py
"""
                shell_file = scripts_dir / "start_trading_bot.sh"
                with open(shell_file, 'w') as f:
                    f.write(shell_content)
                os.chmod(shell_file, 0o755)
                print("✅ Created start_trading_bot.sh")
            
            print("✅ Startup scripts created\n")
            return True
            
        except Exception as e:
            print(f"❌ Failed to create startup scripts: {e}")
            return False
    
    def display_completion_info(self):
        """Display setup completion information."""
        print("\n" + "=" * 60)
        print("🎉 SETUP COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        
        print("\n📋 Next Steps:")
        print("1. Edit config/development.yaml with your MT5 credentials")
        print("2. Test MT5 connection: python scripts/test_mt5_connection.py")
        
        if self.is_windows:
            print("3. Run the bot:")
            print("   - Direct: python main.py")
            print("   - Batch file: scripts/start_trading_bot.bat")
            print("   - Windows Service: scripts/service_manager.bat")
        else:
            print("3. Run the bot:")
            print("   - Direct: python main.py")
            print("   - Shell script: ./scripts/start_trading_bot.sh")
        
        print("\n🌐 Dashboard Access:")
        print("   - URL: http://localhost:8000")
        print("   - Use the dashboard to control trading operations")
        
        print("\n📁 Important Files:")
        print("   - Configuration: config/development.yaml")
        print("   - Logs: logs/trading_bot.log")
        print("   - Data: data/ directory")
        
        print("\n🔧 Service Management (Windows):")
        print("   - Install: python src/utils/windows_service.py install")
        print("   - Start: python src/utils/windows_service.py start")
        print("   - Stop: python src/utils/windows_service.py stop")
        
        print("\n⚠️  Important Notes:")
        print("   - Ensure MetaTrader 5 is installed and running")
        print("   - Configure your MT5 account credentials")
        print("   - Test on demo account first")
        print("   - Monitor logs for any issues")
        
        print("\n" + "=" * 60)
    
    def run_setup(self) -> bool:
        """Run the complete setup process."""
        steps = [
            ("Prerequisites Check", self.check_prerequisites),
            ("Install Dependencies", self.install_dependencies),
            ("Setup Directories", self.setup_directories),
            ("Setup Configuration", self.setup_configuration),
            ("Test MT5 Connection", self.test_mt5_connection),
            ("Setup Windows Service", self.setup_windows_service),
            ("Create Startup Scripts", self.create_startup_scripts)
        ]
        
        for step_name, step_func in steps:
            print(f"🔄 {step_name}...")
            try:
                if not step_func():
                    print(f"❌ {step_name} failed!")
                    return False
            except Exception as e:
                print(f"❌ {step_name} failed with error: {e}")
                return False
        
        self.display_completion_info()
        return True


def main():
    """Main setup function."""
    try:
        setup = TradingBotSetup()
        
        print("This script will set up the Fibonacci Trading Bot on your system.")
        print("It will install dependencies, create directories, and configure the system.")
        print()
        
        response = input("Do you want to continue? (y/n): ").lower().strip()
        
        if response != 'y':
            print("Setup cancelled.")
            return
        
        print()
        success = setup.run_setup()
        
        if success:
            print("\n🎉 Setup completed successfully!")
        else:
            print("\n❌ Setup failed. Please check the errors above.")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\nSetup interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error during setup: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()