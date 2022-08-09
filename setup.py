from setuptools import setup

requirements = [
    'SPARQLWrapper'
]

setup(
    name='biofid-term-resolver',
    version='0.1.0',
    description='Allows the resolution of terms to their respective URI.',
    license="AGPLv3",
    long_description='',
    long_description_content_type="text/markdown",
    author='Adrian Pachzelt',
    author_email='a.pachzelt@ub.uni-frankfurt.de',
    url="https://www.biofid.de",
    download_url='https://github.com/FID-Biodiversity/biofid-term-resolver',
    python_requires='>=3.8',
    packages=['term_resolver'],
    install_requires=requirements,
    extras_require={
        'dev': [
            'black',
            'pytest',
            'rdflib'
        ]
    }
)
