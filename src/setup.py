from setuptools import setup, find_packages

setup(
    name='DataSubmitter',
    packages=find_packages(),
    install_requires=['numpy', 'pandas','pymongo','watchdog',],
    entry_points={'console_scripts' : ['DataSubmitter=DataSubmitter:DataSubmitter']},
    py_modules=['DataSubmitter'],
    version='20180425a',
    description='Automated data submission program for ASCII to mongo',
    long_description= """ Automated data submission program for ASCII to mongo """,
    author_email='ferralis@mit.edu',
    url='https://github.com/feranick/DataSubmitter',
    download_url='https://github.com/feranick/DataSubmitter/archive/master.zip',
    keywords=['Data', 'ASCII', 'data-management', 'automation',],
    license='GPLv3',
    platforms='any',
    classifiers=[
     'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
     'Development Status :: 4 - Beta',
     'Programming Language :: Python :: Only',
     'Programming Language :: Python :: 3',
     'Programming Language :: Python :: 3.5',
     'Programming Language :: Python :: 3.6',
     'Intended Audience :: Science/Research',
     'Topic :: Scientific/Engineering :: Chemistry',
     'Topic :: Scientific/Engineering :: Physics',
     ],
)
