"""
Setup configuration for Fingerprint R307 Sensor package
"""
from setuptools import setup, find_packages
import os

# Read the contents of README file
this_directory = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='fingerprint-r307',
    version='1.0.0',
    author='Your Name',
    author_email='your.email@example.com',
    description='Python interface for R307 Fingerprint Sensor Module',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/yourusername/fingerprint-r307',
    package_dir={'': 'src'},
    packages=find_packages(where='src'),
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Topic :: System :: Hardware',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Operating System :: POSIX :: Linux',
    ],
    python_requires='>=3.7',
    install_requires=[
        'pyfingerprint>=1.5',
    ],
    extras_require={
        'dev': [
            'pytest>=7.0.0',
            'pytest-cov>=4.0.0',
            'black>=23.0.0',
            'flake8>=6.0.0',
            'pylint>=2.15.0',
        ],
        'rpi': [
            'RPi.GPIO>=0.7.0',
        ],
    },
    entry_points={
        'console_scripts': [
            'fingerprint-admin=fingerprint_r307.admin.cli:main',
            'fingerprint-reader=fingerprint_r307.reader.verifier:main',
        ],
    },
    include_package_data=True,
    keywords='fingerprint biometric r307 sensor hardware authentication',
    project_urls={
        'Bug Reports': 'https://github.com/yourusername/fingerprint-r307/issues',
        'Source': 'https://github.com/yourusername/fingerprint-r307',
    },
)
