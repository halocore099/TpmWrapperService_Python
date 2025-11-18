# Linux x86_64 Libraries Directory

This directory contains Linux x86_64 TSS2 shared libraries (.so files) that are bundled with the package.

## Required Libraries

- `libtss2-esys.so*` - TSS2 ESYS library (with version symlinks)
- `libtss2-mu.so*` - TSS2 marshalling/unmarshalling library
- `libtss2-rcdecode.so*` - TSS2 return code decoding library
- `libtss2-tctildr.so*` - TSS2 TCTI loader library
- `libtss2-tcti-device.so*` - TSS2 TCTI for Linux device access

## Building

To populate this directory, run `build_linux.sh` or follow the instructions in `BUILD.md`.

The libraries are extracted from the system after building tpm2-pytss.

## Cross-Distribution Compatibility

These libraries are ABI-compatible across Linux distributions (Ubuntu, Arch, Debian, Fedora, etc.) for the same architecture (x86_64).

