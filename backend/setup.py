"""Setup file for the backend package"""
from setuptools import setup, find_packages

setup(
    name="backend",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "flask==3.0.0",
        "flask-pymongo==2.3.0",
        "flask-cors==4.0.0",
        "python-dotenv==1.0.0",
        "xrpl-py==2.4.0",
    ],
) 