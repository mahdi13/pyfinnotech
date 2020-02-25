from setuptools import setup, find_packages

dependencies = [
    'requests',
    'ujson',
    'restfulpy == 0.40.1',
    'nanohttp == 0.26.1',
    'pymlconf == 0.8.6',
]
test_dependencies = ['nose', 'codecov']

setup(
    name="pyfinnotech",
    version='0.2.3',
    author="mahdi13",
    tests_require=test_dependencies,
    extras_require={'test': test_dependencies},
    install_requires=dependencies,
    packages=find_packages(),
    test_suite="pyfinnotech.tests"
)
