# Bundled Libraries Directory

This directory contains platform-specific TSS2 libraries that are bundled with the package.

## Structure

```
libs/
  windows/          # Windows DLLs (tss2-*.dll)
  linux/
    x86_64/        # Linux x86_64 shared libraries (libtss2-*.so*)
    aarch64/       # Linux ARM64 shared libraries (future)
```

## Purpose

These libraries are bundled to:
- Eliminate the need for users to install TSS2 libraries separately
- Provide a self-contained package that works on clean systems
- Support cross-platform distribution (Windows + Linux)
- Ensure compatibility across Linux distributions

## Building

See [BUILD.md](../../BUILD.md) for instructions on building and populating these directories.

## Library Loading

The `lib_loader.py` module automatically sets up the library path when the package is imported, ensuring bundled libraries are found before system libraries.

