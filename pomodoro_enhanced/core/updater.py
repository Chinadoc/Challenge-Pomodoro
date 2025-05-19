"""
Update management for the Enhanced Pomodoro Timer.
Handles checking for and applying application updates.
"""

import json
import logging
import platform
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, Callable
from urllib.request import urlopen, Request
from urllib.error import URLError

# Initialize logger
logger = logging.getLogger(__name__)

class UpdateManager:
    """Manages application updates."""
    
    def __init__(self, 
                 current_version: str,
                 update_url: str,
                 app_name: str = "Enhanced Pomodoro Timer",
                 app_dir: Optional[Path] = None):
        """Initialize the update manager.
        
        Args:
            current_version: Current application version (e.g., "1.0.0")
            update_url: Base URL for checking updates
            app_name: Application name
            app_dir: Application directory (for portable updates)
        """
        self.current_version = current_version
        self.update_url = update_url.rstrip('/')
        self.app_name = app_name
        self.app_dir = app_dir or Path(sys.executable).parent
        self._update_info: Optional[Dict[str, Any]] = None
    
    def check_for_updates(self, beta: bool = False) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """Check for available updates.
        
        Args:
            beta: Whether to include beta releases
            
        Returns:
            Tuple of (update_available, update_info)
        """
        try:
            # Build the update URL
            os_name = platform.system().lower()
            arch = platform.machine().lower()
            
            # Map common architecture names
            if arch in ('x86_64', 'amd64'):
                arch = 'x64'
            elif arch in ('i386', 'i686', 'x86'):
                arch = 'x86'
            elif arch in ('arm64', 'aarch64'):
                arch = 'arm64'
            
            # Create request with user agent
            headers = {
                'User-Agent': f'{self.app_name}/{self.current_version}',
                'Accept': 'application/json'
            }
            
            # Check for updates
            check_url = f"{self.update_url}/check?version={self.current_version}&os={os_name}&arch={arch}"
            if beta:
                check_url += "&beta=true"
            
            logger.info(f"Checking for updates at {check_url}")
            
            req = Request(check_url, headers=headers)
            with urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode('utf-8'))
            
            # Check if update is available
            if not isinstance(data, dict) or 'success' not in data:
                logger.error("Invalid update server response")
                return False, None
            
            if not data.get('success'):
                logger.warning(f"Update check failed: {data.get('message', 'Unknown error')}")
                return False, None
            
            update_available = data.get('update_available', False)
            if not update_available:
                logger.info("No updates available")
                return False, None
            
            # Store update info
            self._update_info = data.get('update', {})
            
            # Log update info
            logger.info(f"Update available: {self._update_info.get('version')} "
                       f"(current: {self.current_version})")
            
            return True, self._update_info
            
        except URLError as e:
            logger.error(f"Network error checking for updates: {e}")
            return False, None
        except Exception as e:
            logger.error(f"Error checking for updates: {e}", exc_info=True)
            return False, None
    
    def download_update(self, 
                       progress_callback: Optional[Callable[[int, int], None]] = None) -> bool:
        """Download the available update.
        
        Args:
            progress_callback: Optional callback for download progress (received, total)
            
        Returns:
            bool: True if download was successful
        """
        if not self._update_info:
            logger.error("No update information available. Check for updates first.")
            return False
        
        download_url = self._update_info.get('download_url')
        if not download_url:
            logger.error("No download URL available in update info")
            return False
        
        try:
            # Create a temporary file for the download
            with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as temp_file:
                temp_path = Path(temp_file.name)
                
                # Download the update
                logger.info(f"Downloading update from {download_url}")
                
                req = Request(download_url, headers={'User-Agent': f'{self.app_name}/{self.current_version}'})
                with urlopen(req, timeout=30) as response:
                    # Get file size for progress tracking
                    total_size = int(response.headers.get('content-length', 0))
                    received = 0
                    
                    # Download chunks and write to file
                    chunk_size = 8192
                    while True:
                        chunk = response.read(chunk_size)
                        if not chunk:
                            break
                            
                        temp_file.write(chunk)
                        received += len(chunk)
                        
                        # Call progress callback if provided
                        if progress_callback and total_size > 0:
                            progress_callback(received, total_size)
                
                logger.info(f"Downloaded {received} bytes to {temp_path}")
                
                # Store the downloaded file path
                self._update_info['downloaded_file'] = temp_path
                
                return True
                
        except Exception as e:
            logger.error(f"Error downloading update: {e}", exc_info=True)
            # Clean up partially downloaded file
            if 'downloaded_file' in locals() and temp_path.exists():
                try:
                    temp_path.unlink()
                except Exception as cleanup_error:
                    logger.error(f"Error cleaning up temporary file: {cleanup_error}")
            return False
    
    def apply_update(self) -> bool:
        """Apply the downloaded update.
        
        Returns:
            bool: True if the update was applied successfully
        """
        if not self._update_info or 'downloaded_file' not in self._update_info:
            logger.error("No update has been downloaded yet")
            return False
        
        update_file = Path(self._update_info['downloaded_file'])
        if not update_file.exists():
            logger.error(f"Downloaded update file not found: {update_file}")
            return False
        
        try:
            # Determine the update type and apply it
            if self._update_info.get('update_type') == 'portable':
                return self._apply_portable_update(update_file)
            else:
                return self._apply_standard_update(update_file)
                
        except Exception as e:
            logger.error(f"Error applying update: {e}", exc_info=True)
            return False
        finally:
            # Clean up the downloaded file
            try:
                if update_file.exists():
                    update_file.unlink()
            except Exception as cleanup_error:
                logger.error(f"Error cleaning up update file: {cleanup_error}")
    
    def _apply_standard_update(self, update_file: Path) -> bool:
        """Apply a standard update (installer or package).
        
        Args:
            update_file: Path to the update file
            
        Returns:
            bool: True if the update was applied successfully
        """
        try:
            # On Windows, we might have an installer executable
            if platform.system().lower() == 'windows' and update_file.suffix.lower() == '.exe':
                logger.info("Launching installer...")
                subprocess.Popen([str(update_file), '/SILENT', '/NORESTART'], 
                               shell=True)
                return True
            
            # On macOS, we might have a .pkg or .dmg file
            elif platform.system().lower() == 'darwin':
                if update_file.suffix.lower() == '.pkg':
                    logger.info("Launching package installer...")
                    subprocess.Popen(['open', str(update_file)])
                    return True
                elif update_file.suffix.lower() == '.dmg':
                    logger.info("Mounting disk image...")
                    subprocess.Popen(['hdiutil', 'attach', str(update_file)])
                    return True
            
            # On Linux, we might have a .deb, .rpm, or .AppImage file
            elif platform.system().lower() == 'linux':
                if update_file.suffix.lower() in ('.deb', '.rpm'):
                    logger.info("Installing package...")
                    # This would require root privileges
                    pkg_manager = 'apt' if update_file.suffix.lower() == '.deb' else 'dnf'
                    subprocess.Popen(['sudo', pkg_manager, 'install', str(update_file)])
                    return True
                elif 'appimage' in update_file.name.lower():
                    # Make the AppImage executable
                    update_file.chmod(0o755)
                    # Launch the new version
                    subprocess.Popen([str(update_file)])
                    return True
            
            logger.error(f"Unsupported update file format: {update_file.suffix}")
            return False
            
        except Exception as e:
            logger.error(f"Error applying standard update: {e}", exc_info=True)
            return False
    
    def _apply_portable_update(self, update_file: Path) -> bool:
        """Apply a portable update (ZIP file).
        
        Args:
            update_file: Path to the update ZIP file
            
        Returns:
            bool: True if the update was applied successfully
        """
        try:
            # Create a temporary directory for extraction
            with tempfile.TemporaryDirectory(prefix='pomodoro_update_') as temp_dir:
                temp_dir_path = Path(temp_dir)
                
                logger.info(f"Extracting update to {temp_dir_path}")
                
                # Extract the update
                with zipfile.ZipFile(update_file, 'r') as zip_ref:
                    zip_ref.extractall(temp_dir_path)
                
                # Find the main executable in the extracted files
                extracted_dirs = list(temp_dir_path.glob('*'))
                if not extracted_dirs:
                    logger.error("No files found in the update package")
                    return False
                
                # Assume the first directory is the application directory
                update_dir = extracted_dirs[0]
                
                # On Windows, we need to stop the application before updating
                if platform.system().lower() == 'windows':
                    # Create an update script that will be run after the application exits
                    update_script = temp_dir_path / 'update.bat'
                    with open(update_script, 'w') as f:
                        f.write("@echo off\n")
                        f.write("echo Updating application...\n")
                        f.write("timeout /t 3 /nobreak >nul\n")  # Wait for the app to exit
                        
                        # Copy all files from update to app directory
                        f.write(f"xcopy /E /Y /I /Q \"{update_dir}\" \"{self.app_dir}\"\n")
                        
                        # Restart the application
                        app_exe = self.app_dir / f"{self.app_name.replace(' ', '')}.exe"
                        f.write(f"start \"\" \"{app_exe}\"\n")
                        
                        # Delete the update script itself
                        f.write(f"del \"%~f0\"\n")
                    
                    # Launch the update script
                    subprocess.Popen(['cmd', '/c', str(update_script)], 
                                   creationflags=subprocess.CREATE_NO_WINDOW)
                
                # On Unix-like systems, we can use a shell script
                else:
                    update_script = temp_dir_path / 'update.sh'
                    with open(update_script, 'w') as f:
                        f.write("#!/bin/bash\n")
                        f.write("echo 'Updating application...'\n")
                        f.write("sleep 3\n")  # Wait for the app to exit
                        
                        # Copy all files from update to app directory
                        f.write(f"cp -Rf \"{update_dir}/\"* \"{self.app_dir}/\"\n")
                        
                        # Make the main script executable
                        app_script = self.app_dir / f"{self.app_name.lower().replace(' ', '_')}.py"
                        f.write(f"chmod +x \"{app_script}\"\n")
                        
                        # Restart the application
                        f.write(f"\"{app_script}\" &\n")
                        
                        # Delete the update script itself
                        f.write("rm -f \"$0\"\n")
                    
                    # Make the script executable
                    update_script.chmod(0o755)
                    
                    # Launch the update script
                    subprocess.Popen(['nohup', str(update_script)], 
                                   stdout=subprocess.DEVNULL,
                                   stderr=subprocess.DEVNULL)
                
                return True
                
        except Exception as e:
            logger.error(f"Error applying portable update: {e}", exc_info=True)
            return False
    
    def check_and_apply_update(self, 
                              beta: bool = False,
                              progress_callback: Optional[Callable[[int, int], None]] = None) -> bool:
        """Check for and apply an update in one step.
        
        Args:
            beta: Whether to include beta releases
            progress_callback: Optional callback for download progress
            
        Returns:
            bool: True if an update was applied successfully
        """
        # Check for updates
        update_available, _ = self.check_for_updates(beta=beta)
        if not update_available:
            return False
        
        # Download the update
        if not self.download_update(progress_callback=progress_callback):
            return False
        
        # Apply the update
        return self.apply_update()

# Global update manager instance
update_manager: Optional[UpdateManager] = None

def get_update_manager() -> Optional[UpdateManager]:
    """Get the global update manager instance."""
    return update_manager

def init_update_manager(current_version: str, 
                       update_url: str, 
                       app_name: str = "Enhanced Pomodoro Timer") -> UpdateManager:
    """Initialize the global update manager.
    
    Args:
        current_version: Current application version
        update_url: Base URL for checking updates
        app_name: Application name
        
    Returns:
        The initialized UpdateManager instance
    """
    global update_manager
    update_manager = UpdateManager(
        current_version=current_version,
        update_url=update_url,
        app_name=app_name
    )
    return update_manager
