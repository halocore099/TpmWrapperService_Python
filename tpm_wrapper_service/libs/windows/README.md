# Windows DLLs Directory

This directory contains Windows TSS2 DLLs that are bundled with the package.

## Required DLLs

- `tss2-esys.dll` - TSS2 ESYS library
- `tss2-mu.dll` - TSS2 marshalling/unmarshalling library
- `tss2-rcdecode.dll` - TSS2 return code decoding library
- `tss2-tctildr.dll` - TSS2 TCTI loader library
- `tss2-tcti-tbs.dll` - TSS2 TCTI for Windows TBS (TPM Base Services)

## Building

To populate this directory, run `build_windows.ps1` or follow the instructions in `BUILD.md`.

The DLLs are extracted from MSYS2 after building tpm2-pytss.

