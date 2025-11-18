"""
Platform detection and utilities
"""
import sys
import platform


def is_windows() -> bool:
    """Check if running on Windows."""
    return sys.platform == 'win32' or sys.platform == 'cygwin'


def is_linux() -> bool:
    """Check if running on Linux."""
    return sys.platform == 'linux'


def get_architecture() -> str:
    """Get system architecture."""
    machine = platform.machine().lower()
    if machine in ('x86_64', 'amd64'):
        return 'x86_64'
    elif machine in ('arm64', 'aarch64'):
        return 'arm64'
    elif machine in ('i386', 'i686', 'x86'):
        return 'x86'
    else:
        return machine


def get_pipe_name() -> str:
    """Get platform-appropriate pipe/socket name."""
    if is_windows():
        return r'\\.\pipe\TpmWrapperPipe'
    else:
        return '/tmp/TpmWrapperPipe.sock'

