# python setup.py sdist bdist_wheel
# twine upload dist/*

from setuptools import setup, find_packages

requirements = [
    # "osmium~=3.6.0",
    "boto3~=1.34.72"
]

setup(
    name='mbtiles_util',
    version='1.0.4',
    author = 'Thang Quach',
    author_email= 'quachdongthang@gmail.com',
    url='https://github.com/thangqd/mbtiles_util',
    description='MBTiles Utilities',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    requires_python=">=3.0",
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'mbtilesinfo = mbtiles_util.mbtilesinfo:main',
            'mbtiles2folder = mbtiles_util.mbtiles2folder:main',
            'folder2s3 = mbtiles_util.folder2s3:main'   
        ],
    },    
    install_requires=requirements,    
    classifiers=[
        'Programming Language :: Python :: 3',
        'Environment :: Console',
        'Topic :: Scientific/Engineering :: GIS',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
)
