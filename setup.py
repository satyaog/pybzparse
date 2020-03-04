import glob
from setuptools import setup, find_packages

try:
    import pypandoc
    long_description = pypandoc.convert("README.md", "rst")
except(IOError, ImportError):
    long_description = open("README.md").read()

setup(
    name="pybzparse",
    version="0.2.0",
    packages=find_packages(exclude=["test_*"]),
    url="https://github.com/satyaog/pybzparse",
    license="The MIT License",
    author="Satya Ortiz-Gagné",
    author_email="satya.ortiz-gagne@mila.quebec",
    description="MP4 / ISO base media file format (ISO/IEC 14496-12 - MPEG-4 Part 12) file parser",
    requires=["bitstring"],
    install_requires=["bitstring"],
    setup_requires=["pytest-runner"],
    tests_require=["pytest"],
    long_description=long_description,
    data_files=[("", ["README.md", ]),
               ("tests", glob.glob("data/*"))]
)
