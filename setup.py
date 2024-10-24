# python setup.py sdist bdist_wheel
# twine upload dist/*
import os
import shutil
from setuptools import setup, find_packages

requirements = [
    'tqdm~=4.66.2',
    'boto3~=1.34.72',
    'requests~=2.31.0',
    'click~=8.1.7',
    'fiona~=1.10.0',
    'shapely~=2.0.1',
    'protobuf~=5.26.1',
    'pillow~=10.0.1'
],

def clean_build():
    build_dir = 'build'
    dist_dir = 'dist'
    if os.path.exists(build_dir):
        shutil.rmtree(build_dir)
    if os.path.exists(dist_dir):
        shutil.rmtree(dist_dir)

clean_build()

setup(
    name='vtiles',
    version='1.0.8',
    author = 'Thang Quach',
    author_email= 'quachdongthang@gmail.com',
    url='https://github.com/thangqd/vtiles',
    description='Vector Tiles Utilities',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    requires_python=">=3.0",
    packages=find_packages(),
    include_package_data=True,  # Include package data specified in MANIFEST.in
    entry_points={
        'console_scripts': [
                        
            'mbtilesinfo = vtiles.mbtiles.mbtilesinfo:main',
            'mbtilesinspect = vtiles.mbtiles.mbtilesinspect:main',
            'mbtilesdelduplicate = vtiles.mbtiles.mbtilesdelduplicate:main',           

            'mbtiles2folder = vtiles.mbtiles.mbtiles2folder:main',
            'folder2mbtiles = vtiles.mbtiles.folder2mbtiles:main',
            'url2folder = vtiles.mbtiles.url2folder:main',   
            'mbtiles2geojson = vtiles.mbtiles.mbtiles2geojson:main',
            'geojson2mbtiles = vtiles.mbtiles.geojson2mbtiles:main',                   
            'mbtiles2s3 = vtiles.mbtiles.mbtiles2s3:main',        
            'folder2s3 = vtiles.mbtiles.folder2s3:main',         
            'mbtiles2pbf = vtiles.mbtiles.mbtiles2pbf:main',

            'mbtilessplit = vtiles.mbtiles.mbtilessplit:main',
            'mbtilesmerge = vtiles.mbtiles.mbtilesmerge:main',
            'mbtilesdecompress = vtiles.mbtiles.mbtilesdecompress:main',
            'mbtilescompress = vtiles.mbtiles.mbtilescompress:main',
            'mbtilesfixmeta = vtiles.mbtiles.mbtilesfixmeta:main',
           
            'tileinfo = vtiles.mbtiles.pbfinfo:main',
            'tile2geojson = vtiles.mbtiles.tile2geojson:main',      
            'flipy = vtiles.mbtiles.flipy:main',   
            'mbtiles2pmtiles = vtiles.mbtiles.mbtiles2pmtiles:main',         
            
            'servefolder= vtiles.server.servefolder:main',
            'servepostgis= vtiles.server.servepostgis:main',          
            'servembtiles=vtiles.server.servembtiles:main',    
            'serverastermbtiles=vtiles.server.serverastermbtiles:main',
            'servevectormbtiles=vtiles.server.servevectormbtiles:main',       
            'servepmtiles=vtiles.server.servepmtiles:main',                   
            'tilesinspect=vtiles.server.tilesinspect.tilesinspect:main',                   

            'pmtilesinfo = vtiles.utils.pmtilesinfo:main',
            'pmtiles2folder = vtiles.utils.pmtiles2folder:main',
            'pmtiles2mbtiles = vtiles.utils.pmtiles2mbtiles:main',           
            'vtpk2folder=vtiles.utils.vtpk2folder:main',
            'centerline=vtiles.utils.centerline:main'
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
