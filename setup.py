from setuptools import setup, find_packages

setup(
    name="brute-force-defender",
    version="1.0.0",
    description="BLAKE3 kullanarak brute-force saldırılara karşı tuzlama (salting) mekanizmasının etkisini gösteren eğitim projesi",
    author="Tersine Mühendislik Dersi",
    python_requires=">=3.8",
    packages=find_packages(),
    install_requires=[
        "blake3>=1.0.0",
        "matplotlib>=3.5.0",
        "colorama>=0.4.6",
        "tabulate>=0.9.0",
    ],
    entry_points={
        "console_scripts": [
            "brute-force-defender=main:main",
        ],
    },
)
