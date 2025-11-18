# Build script for Windows - Extracts DLLs from MSYS2 and builds wheel
# This script should be run from PowerShell on Windows

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "TPM Wrapper Service - Windows Build" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if MSYS2 is installed
$msys2Path = "C:\msys64"
if (-not (Test-Path $msys2Path)) {
    Write-Host "ERROR: MSYS2 not found at $msys2Path" -ForegroundColor Red
    Write-Host "Please install MSYS2 from https://www.msys2.org/" -ForegroundColor Yellow
    Write-Host "After installation, run this script again." -ForegroundColor Yellow
    exit 1
}

Write-Host "MSYS2 found at: $msys2Path" -ForegroundColor Green
Write-Host ""

# Check if DLLs directory exists
$dllDir = "tpm_wrapper_service\libs\windows"
if (-not (Test-Path $dllDir)) {
    New-Item -ItemType Directory -Force -Path $dllDir | Out-Null
    Write-Host "Created directory: $dllDir" -ForegroundColor Green
}

Write-Host "Step 1: Building tpm2-pytss in MSYS2..." -ForegroundColor Yellow
Write-Host "Please open MSYS2 UCRT64 terminal and run the following commands:" -ForegroundColor Yellow
Write-Host ""
Write-Host "  pacman -Syu" -ForegroundColor Cyan
Write-Host "  pacman -S mingw-w64-ucrt-x86_64-tpm2-tss" -ForegroundColor Cyan
Write-Host "  pacman -S mingw-w64-ucrt-x86_64-pkg-config mingw-w64-ucrt-x86_64-gcc" -ForegroundColor Cyan
Write-Host "  pacman -S mingw-w64-ucrt-x86_64-python mingw-w64-ucrt-x86_64-python-pip" -ForegroundColor Cyan
Write-Host "  python -m pip install tpm2-pytss" -ForegroundColor Cyan
Write-Host ""
Write-Host "After building, run this script again to extract DLLs." -ForegroundColor Yellow
Write-Host ""

$response = Read-Host "Have you completed the MSYS2 build? (y/n)"
if ($response -ne "y" -and $response -ne "Y") {
    Write-Host "Please complete the MSYS2 build first, then run this script again." -ForegroundColor Yellow
    exit 0
}

Write-Host ""
Write-Host "Step 2: Extracting DLLs from MSYS2..." -ForegroundColor Yellow

$msys2Bin = "$msys2Path\ucrt64\bin"
if (-not (Test-Path $msys2Bin)) {
    Write-Host "ERROR: MSYS2 UCRT64 bin directory not found at: $msys2Bin" -ForegroundColor Red
    exit 1
}

# Copy TSS2 DLLs
$dlls = @(
    "tss2-esys.dll",
    "tss2-mu.dll",
    "tss2-rcdecode.dll",
    "tss2-tctildr.dll",
    "tss2-tcti-tbs.dll"
)

$copiedCount = 0
foreach ($dll in $dlls) {
    $source = Join-Path $msys2Bin $dll
    $dest = Join-Path $dllDir $dll
    
    if (Test-Path $source) {
        Copy-Item $source $dest -Force
        Write-Host "  Copied: $dll" -ForegroundColor Green
        $copiedCount++
    } else {
        Write-Host "  WARNING: $dll not found at $source" -ForegroundColor Yellow
    }
}

if ($copiedCount -eq 0) {
    Write-Host ""
    Write-Host "ERROR: No DLLs were copied. Please verify tpm2-pytss is installed in MSYS2." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Copied $copiedCount DLL(s) to $dllDir" -ForegroundColor Green
Write-Host ""

# Check for dependency DLLs (OpenSSL, etc.)
Write-Host "Step 3: Checking for dependency DLLs..." -ForegroundColor Yellow
Write-Host "If tpm2-pytss requires additional DLLs (e.g., OpenSSL), copy them manually:" -ForegroundColor Yellow
Write-Host "  From: $msys2Bin" -ForegroundColor Cyan
Write-Host "  To: $dllDir" -ForegroundColor Cyan
Write-Host ""

Write-Host "Step 4: Building wheel..." -ForegroundColor Yellow

# Activate virtual environment if it exists
if (Test-Path "venv\Scripts\Activate.ps1") {
    & "venv\Scripts\Activate.ps1"
    Write-Host "Activated virtual environment" -ForegroundColor Green
}

# Clean previous builds
Write-Host "Cleaning previous builds..." -ForegroundColor Cyan
python setup.py clean --all 2>&1 | Out-Null

# Build wheel
Write-Host "Building wheel..." -ForegroundColor Cyan
python setup.py bdist_wheel

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Wheel build failed" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Step 5: Verifying wheel contents..." -ForegroundColor Yellow

$wheelFile = Get-ChildItem "dist\*.whl" | Select-Object -First 1
if ($wheelFile) {
    Write-Host "Wheel created: $($wheelFile.Name)" -ForegroundColor Green
    
    # Check if DLLs are in the wheel (basic check)
    Write-Host "Verifying DLLs are included..." -ForegroundColor Cyan
    $zip = [System.IO.Compression.ZipFile]::OpenRead($wheelFile.FullName)
    $dllEntries = $zip.Entries | Where-Object { $_.FullName -like "*libs/windows/*.dll" }
    $zip.Dispose()
    
    if ($dllEntries.Count -gt 0) {
        Write-Host "Found $($dllEntries.Count) DLL(s) in wheel" -ForegroundColor Green
        foreach ($entry in $dllEntries) {
            Write-Host "  - $($entry.Name)" -ForegroundColor Gray
        }
    } else {
        Write-Host "WARNING: No DLLs found in wheel. Check MANIFEST.in and setup.py" -ForegroundColor Yellow
    }
} else {
    Write-Host "ERROR: Wheel file not found in dist/" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Build completed successfully!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Test installation: pip install $($wheelFile.Name)" -ForegroundColor Cyan
Write-Host "2. Test import: python -c 'from tpm_wrapper_service import service'" -ForegroundColor Cyan
Write-Host ""

