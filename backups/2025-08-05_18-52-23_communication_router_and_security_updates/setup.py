from setuptools import setup, find_packages

setup(
    name="mingus-app",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "flask>=3.0.0",
        "pydantic>=2.5.2",
        "python-jose[cryptography]>=3.3.0",
        "python-dateutil>=2.8.2",
        "loguru>=0.7.2",
        "flask-pydantic>=0.11.0",
        "supabase>=2.3.0",
        "python-dotenv>=1.0.0",
        "flask-cors>=4.0.0",
    ],
    extras_require={
        "test": [
            "pytest>=7.4.0",
            "pytest-asyncio>=0.21.1",
            "pytest-cov>=4.1.0",
        ],
    },
    python_requires=">=3.8",
) 