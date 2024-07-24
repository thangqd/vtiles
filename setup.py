# python setup.py sdist bdist_wheel
# twine upload dist/*

from setuptools import setup, find_packages

requirements = [
    'tqdm~=4.66.2',
    'boto3~=1.34.72',
    'requests~=2.31.0',
    'click~=8.1.7',
    'fiona~=1.9.4',
    'shapely~=2.0.1',
    'osmium~=3.7.0'
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
            'osmdownload = tiles_util.osm.osmdownload:main',
            'osmreplication = tiles_util.osm.osmreplication:main',
            'osminfo = tiles_util.osm.osminfo:main',
            'osm2geojson = tiles_util.osm.osm2geojson:main',
            'osmpub = tiles_util.osm.osmpub:main',
            
            'mbtilesinfo = tiles_util.mbtiles.mbtilesinfo:main',
            'mbtiles2folder = tiles_util.mbtiles.mbtiles2folder:main',
            'mbtiles2pmtiles = tiles_util.mbtiles.mbtiles2pmtiles:main',
            'mbtiles2s3 = tiles_util.mbtiles.mbtiles2s3:main',     
            'mbtiles2geojson = tiles_util.mbtiles.mbtiles2geojson:main',
            'mbtiles2pbf = tiles_util.mbtiles.mbtiles2pbf:main',
            'mbtilesdel = tiles_util.mbtiles.mbtilesdel:main',
            'mbtilessplit = tiles_util.mbtiles.mbtilessplit:main',
            'mbtilesmerge = tiles_util.mbtiles.mbtilesmerge:main',
            'mbtilesdecompress = tiles_util.mbtiles.mbtilesdecompress:main',
            'mbtilescompress = tiles_util.mbtiles.mbtilescompress:main',
            'geojson2mbtiles = tiles_util.mbtiles.geojson2mbtiles:main',                   
            'folder2mbtiles = tiles_util.mbtiles.folder2mbtiles:main',  
            'pbfinfo = tiles_util.mbtiles.pbfinfo:main',
            'pbf2geojson = tiles_util.mbtiles.pbf2geojson:main',
            'folder2s3 = tiles_util.mbtiles.folder2s3:main',
            'flipy = tiles_util.mbtiles.flipy:main',
            'debuggrid = tiles_util.mbtiles.debuggrid:main',
                                  
            'servefolder= tiles_util.server.servefolder:main',
            'servepostgis= tiles_util.server.servepostgis:main',          
            'servembtiles=tiles_util.server.servembtiles:main',    
            'servevectormbtiles=tiles_util.server.servevectormbtiles:main',       
            'servepmtiles=tiles_util.server.servepmtiles:main',                   
            
            'pmtilesinfo = tiles_util.utils.pmtilesinfo:main',
            'pmtiles2folder = tiles_util.utils.pmtiles2folder:main',
            'pmtiles2mbtiles = tiles_util.utils.pmtiles2mbtiles:main',           
            'centerline=tiles_util.utils.centerline:main'
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
