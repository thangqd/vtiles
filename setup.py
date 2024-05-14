# python setup.py sdist bdist_wheel
# twine upload dist/*

from setuptools import setup, find_packages

requirements = [
    # "osmium~=3.6.0",
    # 'mapbox_vector_tile~=2.0.1',
    "tqdm~=4.66.2",
    "boto3~=1.34.72",
    "requests~=2.31.0",
    'asyncpg~=0.29.0',
    'tornado~=6.3.3',
    'betterproto~=1.2.5',
    'docopt-ng~=0.7.2',
    'deprecated~=1.2.13',
    'ascii_graph~=1.5.1',
    'dataclasses-json~=0.5.6'
]

setup(
    name='tiles_util',
    version='1.0.5',
    author = 'Thang Quach',
    author_email= 'quachdongthang@gmail.com',
    url='https://github.com/thangqd/tiles_util',
    description='Vector Tiles Utilities',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    requires_python=">=3.0",
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'mbtilesinfo = tiles_util.mbtilesinfo:main',
            'mbtiles2folder = tiles_util.mbtiles2folder:main',
            'folder2mbtiles = tiles_util.folder2mbtiles:main',  
            'vectorfolder2s3 = tiles_util.vectorfolder2s3:main',
            'rasterfolder2s3 = tiles_util.rasterfolder2s3:main',
            # 'geojson2mbtiles = mbtiles_util.geojson2mbtiles:main',
            'servefolder= tiles_util.servefolder:main',
            'servepostgis= tiles_util.servepostgis:main',
            'osmdownload = tiles_util.osmdownload:main'   
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
