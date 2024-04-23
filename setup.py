# python setup.py sdist bdist_wheel
# twine upload dist/*


from setuptools import setup, find_packages

setup(
    name='mbtiles_util',
    version='1.0.0',
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'mbtiles2folder = mbtiles_util.mbtiles2folder:main',
            'mbtilesinfo = mbtiles_util.mbtilesinfo:main',
        ],
    },
    description='MBTiles Utilities',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    install_requires=[],
    author='Thang Quach',
    author_email='quachdongthang@gmail.com',
    url='https://github.com/thangqd/mbtiles_util',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
)
