import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

with open('requirements.txt') as f:
    requirements = list([p for p in f.read().splitlines() if not p.startswith('vext')])

setuptools.setup(
    name="saldo",
    version="0.0.1",
    author="Christian Meißner",
    author_email="monsieur.cm@gmx.de",
    description="A small example package",
    long_description=long_description,
    long_description_content_type="text/markdown",
    # url="https://github.com/pypa/sampleproject",
    packages=setuptools.find_packages(),
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    entry_points={
        'console_scripts': ['saldo = saldo.__main__:main']
    },
    data_files=[
        ('share/icons/hicolor/256x256/apps', ['saldo/gui/resources/icons/hicolor/256x256/apps/saldo.png']),
        ('share/icons/hicolor/512x512/apps', ['saldo/gui/resources/icons/hicolor/512x512/apps/saldo.png']),
        ('share/icons/hicolor/scalable/apps', ['saldo/gui/resources/icons/hicolor/scalable/apps/saldo.svg']),
        ('share/applications', ['saldo/gui/resources/saldo.desktop']),
    ],
    install_requires=requirements,
)
