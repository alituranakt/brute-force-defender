from setuptools import find_packages, setup


setup(
    name="brute-force-defender",
    version="1.0.0",
    description="BLAKE3 salting demonstration against brute-force and rainbow-table attacks",
    author="alituranakt",
    python_requires=">=3.8",
    packages=find_packages(),
    install_requires=[
        "blake3>=1.0.0",
        "matplotlib>=3.5.0",
        "flask>=2.3.0",
        "python-dotenv>=1.0.1",
    ],
    entry_points={
        "console_scripts": [
            "brute-force-defender=main:main",
        ],
    },
)
