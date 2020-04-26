from setuptools import find_packages, setup

setup(
    name="getplaylist",
    version="0.1.0",
    install_requires=[
        'requests',
        'lxml',
    ],
    entry_points='''
        [console_scripts]
        getplaylist=getplaylist:main
    ''',
    py_modules=['getplaylist'],
)