"""
Setup script for TPM Wrapper Service
"""
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [
        line.strip() for line in fh 
        if line.strip() and not line.startswith("#") and not line.strip().startswith("tpm2-pytss")
    ]

setup(
    name="tpm-wrapper-service",
    version="1.0.0",
    author="TPM Wrapper Service",
    description="Cross-platform TPM 2.0 wrapper service",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/tpm-wrapper-service",
    packages=find_packages(),
    package_data={
        'tpm_wrapper_service': [
            'libs/windows/*.dll',
            'libs/linux/x86_64/*.so*',
            'libs/linux/aarch64/*.so*',  # For ARM64 Linux
        ],
    },
    include_package_data=True,
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Security",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: POSIX :: Linux",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "tpm-wrapper-service=tpm_wrapper_service.service:main",
        ],
    },
)

