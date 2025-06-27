"""
Quick Core Dependencies Installer
Installs only the essential packages needed to run the trading bot.
"""

import subprocess
import sys
from pathlib import Path

def install_core_dependencies():
    """Install core dependencies for Python 3.11."""
    
    print("🔧 Installing Core Trading Bot Dependencies")
    print("=" * 50)
    
    # Core packages that are essential
    core_packages = [
        "pandas>=2.0.0",
        "numpy>=1.24.0", 
        "MetaTrader5>=5.0.45",
        "fastapi>=0.100.0",
        "uvicorn>=0.22.0",
        "plotly>=5.15.0",
        "sqlalchemy>=2.0.0",
        "python-dotenv>=1.0.0",
        "pydantic>=2.0.0",
        "loguru>=0.7.0",
        "aiofiles>=23.0.0",
        "requests>=2.31.0",
        "websockets>=11.0.0",
        "pyyaml>=6.0",
        "click>=8.1.0",
        "rich>=13.0.0"
    ]
    
    # Windows-specific packages
    if sys.platform == 'win32':
        core_packages.append("pywin32>=306")
    
    print("📦 Installing packages one by one...")
    
    failed_packages = []
    
    for package in core_packages:
        try:
            print(f"Installing {package}...")
            result = subprocess.run([
                sys.executable, "-m", "pip", "install", package
            ], capture_output=True, text=True, check=True)
            print(f"✅ {package}")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install {package}")
            print(f"   Error: {e.stderr}")
            failed_packages.append(package)
    
    # Optional packages (don't fail if these don't install)
    optional_packages = [
        "matplotlib>=3.7.0",
        "seaborn>=0.12.0", 
        "scikit-learn>=1.3.0",
        "aiohttp>=3.8.0"
    ]
    
    print("\n📦 Installing optional packages...")
    
    for package in optional_packages:
        try:
            print(f"Installing {package}...")
            subprocess.run([
                sys.executable, "-m", "pip", "install", package
            ], capture_output=True, text=True, check=True)
            print(f"✅ {package}")
        except subprocess.CalledProcessError:
            print(f"⚠️  Skipped {package} (optional)")
    
    print("\n" + "=" * 50)
    
    if failed_packages:
        print("❌ Some packages failed to install:")
        for pkg in failed_packages:
            print(f"  - {pkg}")
        print("\nYou can try installing these manually:")
        for pkg in failed_packages:
            print(f"pip install {pkg}")
    else:
        print("✅ All core packages installed successfully!")
    
    print("\n🚀 Next steps:")
    print("1. Configure your MT5 credentials in config/development.yaml")
    print("2. Test the system: python main.py")
    print("3. Access dashboard: http://localhost:8000")

if __name__ == "__main__":
    install_core_dependencies()