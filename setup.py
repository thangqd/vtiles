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
    'dataclasses-json~=0.5.6',
    'click~=8.1.7',
    'fiona~=1.9.4',
    'networkx~=2.8.8',
    'scipy~=1.11.3',
    'shapely~=2.0.1',
    'osmium~=3.7.0',
    'mapbox-vector-tile[proj]~=2.1.0'
]

setup(
    name='tiles_util',
    version='1.0.6',
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
            'osmdownload = tiles_util.osmdownload:main',
            'osmreplication = tiles_util.osmreplication:main',
            'osminfo = tiles_util.osminfo:main',
            'osm2geojson = tiles_util.osm2geojson:main',
           
            'osmpub = tiles_util.osmpub:main',
            'pbfinfo = tiles_util.pbfinfo:main',
            'pbf2geojson = tiles_util.pbf2geojson:main',
            'pbfview = tiles_util.pbfview:main',


            'mbtilesinfo = tiles_util.mbtilesinfo:main',
            'mbtiles2folder = tiles_util.mbtiles2folder:main',
            'mbtiles2pmtiles = tiles_util.mbtiles2pmtiles:main',
            'mbtiles2s3 = tiles_util.mbtiles2s3:main',     
            'mbtiles2geojson = tiles_util.mbtiles2geojson:main',
            'mbtilesdellayer = tiles_util.mbtilesdellayer:main',
            'geojson2mbtiles = tiles_util.geojson2mbtiles:main',                   
            'folder2mbtiles = tiles_util.folder2mbtiles:main',  
             
            'folder2s3 = tiles_util.folder2s3:main',
            
            'pmtilesinfo = tiles_util.pmtilesinfo:main',
            'pmtiles2folder = tiles_util.pmtiles2folder:main',
            'pmtiles2mbtiles = tiles_util.pmtiles2mbtiles:main',
                        
            'servefolder= tiles_util.servefolder:main',
            'servepostgis= tiles_util.servepostgis:main',          
            'servembtiles=tiles_util.servembtiles:main',    
            'servevectormbtiles=tiles_util.servevectormbtiles:main',       
            'servepmtiles=tiles_util.servepmtiles:main',                   
            
            'flipy = tiles_util.flipy:main',
            'centerline=tiles_util.centerline:main'
        ],
    },    

    # scripts=["bin/utils.py"], # utils.py is just a demo,
    install_requires=requirements,    
    classifiers=[
        'Programming Language :: Python :: 3',
        'Environment :: Console',
        'Topic :: Scientific/Engineering :: GIS',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
)
