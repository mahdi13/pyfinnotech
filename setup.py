from setuptools import setup, find_packages

dependencies = ['requests']

setup(
    name="pyfinnotech",
    version='0.2.0',
    author="mahdi13",
    install_requires=dependencies,
    packages=find_packages(),
    test_suite="pyfinnotech.tests"
)
