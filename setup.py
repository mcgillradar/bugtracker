from setuptools import setup, find_packages

# Get the long description from the README file
long_description = """# bugtracker
"""

setup(
    name='bugtracker',
    version='1.5.2',
    description='Insect tracking from radar data.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Frederic Fabry, Daniel Hogg',
    author_email='daniel.hogg@mcgill.ca',
    classifiers=[
        'Development Status :: 5 - Alpha',
        'Programming Language :: Python :: 3',
    ],
    keywords='radar',
    packages=find_packages(exclude=['tests','examples']),
    # Distributing binary as a possible alternative to CPython extensions
    package_data={'pyrefract.corelib': ['io_corelib.so']},
    python_requires='>=3.5, <4',
    install_requires=['numpy', 'matplotlib', 'opencv-python', 'cartopy', 'beautifulsoup4', 
                      'requests', 'scipy', 'geopy', 'arm-pyart', 'pytest', 'pyproj'],
)