# setup.py
from setuptools import setup, find_packages

setup(
    name="tilttracker",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        'psycopg2-binary',
        'python-dotenv',
        'discord.py',
        'requests',
    ],
    python_requires='>=3.8',
    author="Guillaume",
    description="Tilt Tracker pour ARAM"
)