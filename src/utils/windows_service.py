"""
Windows Service Wrapper
Allows the trading bot to run as a Windows service for VPS deployment.
"""

import asyncio
import sys
import os
import logging
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    import servicemanager
    import win32serviceutil
    import win32service
    import win32event
    WINDOWS_SERVICE_AVAILABLE = True
except ImportError:
    WINDOWS_SERVICE_AVAILABLE = False
    # Create mock classes for non-Windows environments
    class win32serviceutil:
        class ServiceFramework:
            def __init__(self, *args): pass
            def SvcStop(self): pass
            def SvcDoRun(self): pass
            def ReportServiceStatus(self, status): pass
        
        @staticmethod
        def HandleCommandLine(cls): pass
    
    class win32service:
        SERVICE_ACCEPTED_STOP = 1
        SERVICE_STOP_PENDING = 3
        SERVICE_RUNNING = 4
    
    class win32event:
        @staticmethod
        def CreateEvent(*args): return None
        
        @staticmethod
        def WaitForSingleObject(*args): return 0
    
    class servicemanager:
        @staticmethod
        def LogInfoMsg(msg): print(f"INFO: {msg}")
        
        @staticmethod
        def LogErrorMsg(msg): print(f"ERROR: {msg}")

from main import TradingBotApplication
from src.monitoring import get_logger

logger = get_logger("windows_service")


class FibonacciTradingBotService(win32serviceutil.ServiceFramework):
    """Windows service wrapper for the Fibonacci Trading Bot."""
    
    _svc_name_ = "FibonacciTradingBot"
    _svc_display_name_ = "Fibonacci Trading Bot - AI Enhanced"
    _svc_description_ = "Automated Fibonacci retracement trading bot with AI enhancement and web dashboard"
    
    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        self.is_alive = True
        self.trading_app = None
        
        # Setup logging for Windows service
        self._setup_service_logging()
    
    def _setup_service_logging(self):
        """Setup logging specifically for Windows service."""
        try:
            # Create logs directory if it doesn't exist
            log_dir = project_root / "logs"
            log_dir.mkdir(exist_ok=True)
            
            # Setup service-specific logging
            service_log_file = log_dir / "service.log"
            
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                handlers=[
                    logging.FileHandler(service_log_file),
                    logging.StreamHandler()
                ]
            )
            
            logger.info("Service logging initialized")
            
        except Exception as e:
            servicemanager.LogErrorMsg(f"Failed to setup service logging: {e}")
    
    def SvcStop(self):
        """Handle service stop request."""
        try:
            logger.info("Service stop requested")
            servicemanager.LogInfoMsg("Fibonacci Trading Bot service is stopping...")
            
            self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
            win32event.SetEvent(self.hWaitStop)
            self.is_alive = False
            
            # Shutdown trading application
            if self.trading_app:
                asyncio.create_task(self.trading_app.shutdown())
            
            servicemanager.LogInfoMsg("Fibonacci Trading Bot service stopped")
            
        except Exception as e:
            logger.error(f"Error stopping service: {e}")
            servicemanager.LogErrorMsg(f"Error stopping service: {e}")
    
    def SvcDoRun(self):
        """Main service execution."""
        try:
            logger.info("Starting Fibonacci Trading Bot service")
            servicemanager.LogInfoMsg("Fibonacci Trading Bot service is starting...")
            
            self.ReportServiceStatus(win32service.SERVICE_RUNNING)
            
            # Start the trading bot application
            self._run_trading_bot()
            
        except Exception as e:
            logger.error(f"Service execution error: {e}")
            servicemanager.LogErrorMsg(f"Service execution error: {e}")
    
    def _run_trading_bot(self):
        """Run the trading bot application in service context."""
        try:
            # Set up event loop for Windows service
            if sys.platform.startswith('win'):
                asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Create trading application
            self.trading_app = TradingBotApplication()
            
            # Run the application
            loop.run_until_complete(self._service_main())
            
        except Exception as e:
            logger.error(f"Error running trading bot in service: {e}")
            servicemanager.LogErrorMsg(f"Error running trading bot: {e}")
        finally:
            try:
                loop.close()
            except:
                pass
    
    async def _service_main(self):
        """Main service loop."""
        try:
            # Initialize the trading application
            if not await self.trading_app.initialize():
                raise Exception("Failed to initialize trading application")
            
            servicemanager.LogInfoMsg("Trading application initialized successfully")
            
            # Start the application components
            start_task = asyncio.create_task(self.trading_app.start())
            
            # Wait for stop signal or application completion
            while self.is_alive:
                # Check if application is still running
                if start_task.done():
                    exception = start_task.exception()
                    if exception:
                        raise exception
                    break
                
                # Sleep briefly to avoid busy waiting
                await asyncio.sleep(1)
            
            # Shutdown if still alive
            if self.is_alive:
                await self.trading_app.shutdown()
            
        except Exception as e:
            logger.error(f"Service main loop error: {e}")
            servicemanager.LogErrorMsg(f"Service main loop error: {e}")
            raise


class ServiceInstaller:
    """Utility class for installing/uninstalling the Windows service."""
    
    @staticmethod
    def install():
        """Install the Windows service."""
        try:
            if not WINDOWS_SERVICE_AVAILABLE:
                print("Windows service modules not available. This only works on Windows.")
                return False
            
            # Install the service
            win32serviceutil.InstallService(
                pythonClassString=f"{__name__}.FibonacciTradingBotService",
                serviceName=FibonacciTradingBotService._svc_name_,
                displayName=FibonacciTradingBotService._svc_display_name_,
                description=FibonacciTradingBotService._svc_description_,
                startType=win32service.SERVICE_AUTO_START
            )
            
            print(f"Service '{FibonacciTradingBotService._svc_display_name_}' installed successfully")
            print("The service is set to start automatically on system boot")
            return True
            
        except Exception as e:
            print(f"Failed to install service: {e}")
            return False
    
    @staticmethod
    def uninstall():
        """Uninstall the Windows service."""
        try:
            if not WINDOWS_SERVICE_AVAILABLE:
                print("Windows service modules not available. This only works on Windows.")
                return False
            
            # Stop the service if running
            try:
                win32serviceutil.StopService(FibonacciTradingBotService._svc_name_)
                print("Service stopped")
            except:
                pass
            
            # Remove the service
            win32serviceutil.RemoveService(FibonacciTradingBotService._svc_name_)
            print(f"Service '{FibonacciTradingBotService._svc_display_name_}' uninstalled successfully")
            return True
            
        except Exception as e:
            print(f"Failed to uninstall service: {e}")
            return False
    
    @staticmethod
    def start():
        """Start the Windows service."""
        try:
            if not WINDOWS_SERVICE_AVAILABLE:
                print("Windows service modules not available. This only works on Windows.")
                return False
            
            win32serviceutil.StartService(FibonacciTradingBotService._svc_name_)
            print("Service started successfully")
            return True
            
        except Exception as e:
            print(f"Failed to start service: {e}")
            return False
    
    @staticmethod
    def stop():
        """Stop the Windows service."""
        try:
            if not WINDOWS_SERVICE_AVAILABLE:
                print("Windows service modules not available. This only works on Windows.")
                return False
            
            win32serviceutil.StopService(FibonacciTradingBotService._svc_name_)
            print("Service stopped successfully")
            return True
            
        except Exception as e:
            print(f"Failed to stop service: {e}")
            return False
    
    @staticmethod
    def status():
        """Check service status."""
        try:
            if not WINDOWS_SERVICE_AVAILABLE:
                print("Windows service modules not available. This only works on Windows.")
                return False
            
            # This is a simplified status check
            print("Use Windows Services Manager or 'sc query FibonacciTradingBot' for detailed status")
            return True
            
        except Exception as e:
            print(f"Failed to check service status: {e}")
            return False


def main():
    """Service management command line interface."""
    if len(sys.argv) == 1:
        # No arguments - try to run as service
        if WINDOWS_SERVICE_AVAILABLE:
            servicemanager.Initialize()
            servicemanager.PrepareToHostSingle(FibonacciTradingBotService)
            servicemanager.StartServiceCtrlDispatcher()
        else:
            print("Windows service modules not available")
            sys.exit(1)
    else:
        # Handle command line arguments
        command = sys.argv[1].lower()
        
        if command == "install":
            ServiceInstaller.install()
        elif command == "uninstall":
            ServiceInstaller.uninstall()
        elif command == "start":
            ServiceInstaller.start()
        elif command == "stop":
            ServiceInstaller.stop()
        elif command == "status":
            ServiceInstaller.status()
        elif command == "debug":
            # Run in debug mode (not as service)
            from main import run_trading_bot
            run_trading_bot()
        else:
            print("Usage:")
            print("  python windows_service.py install    - Install the service")
            print("  python windows_service.py uninstall  - Uninstall the service")
            print("  python windows_service.py start      - Start the service")
            print("  python windows_service.py stop       - Stop the service")
            print("  python windows_service.py status     - Check service status")
            print("  python windows_service.py debug      - Run in debug mode")
            print("  python windows_service.py            - Run as service (automatic)")


if __name__ == "__main__":
    main()