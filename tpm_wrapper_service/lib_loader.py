"""
Library loader module for cross-platform TPM library loading.

This module sets up the library path to use bundled TSS2 libraries
on both Windows and Linux platforms.
"""
import os
import sys
import platform
from pathlib import Path


def setup_library_path():
    """Add bundled libraries to system library path.
    
    Works across:
    - Windows (all versions)
    - Linux (Ubuntu, Debian, Arch, Fedora, etc.)
    - Multiple architectures (x86_64, aarch64, etc.)
    
    This function must be called before importing tpm2-pytss or any
    TSS2-related modules to ensure bundled libraries are found.
    """
    libs_dir = Path(__file__).parent / 'libs'
    
    if sys.platform == 'win32':
        # Windows: Add DLL directory
        dll_dir = libs_dir / 'windows'
        if dll_dir.exists():
            try:
                os.add_dll_directory(str(dll_dir))
            except AttributeError:
                # Python < 3.8 doesn't have add_dll_directory
                # Fall back to PATH modification
                dll_path = str(dll_dir)
                path_env = os.environ.get('PATH', '')
                if dll_path not in path_env:
                    os.environ['PATH'] = f"{dll_path};{path_env}" if path_env else dll_path
    elif sys.platform == 'linux':
        # Linux: Add to LD_LIBRARY_PATH
        # Works across all Linux distributions for same architecture
        machine = platform.machine()
        so_dir = libs_dir / 'linux' / machine
        if so_dir.exists():
            lib_path = os.environ.get('LD_LIBRARY_PATH', '')
            so_dir_str = str(so_dir)
            if so_dir_str not in lib_path:
                os.environ['LD_LIBRARY_PATH'] = f"{so_dir_str}:{lib_path}" if lib_path else so_dir_str


# Automatically set up library path when this module is imported
setup_library_path()

