try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

setup(name='tagar',
      packages=['tagar'],
      py_modules=['tagar'],
      version='0.1.0',
      description='Standalone team server for agario',
      author='astumpf',
      author_email='Stumpf.Alex@web.de',
      url='https://github.com/astumpf/tagar',
      license='GPLv3',
      install_requires=[
          'agarnet >= 0.1.3',
      ],
      entry_points={'gui_scripts': ['gagar = gagar.main:main']},
      classifiers=[
          'Development Status :: 5 - Production/Stable',
          'Environment :: X11 Applications :: GTK',
          'Intended Audience :: End Users/Desktop',
          'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
          'Natural Language :: English',
          'Programming Language :: Python',
          'Programming Language :: Python :: 3',
          'Programming Language :: Python :: 3.3',
          'Programming Language :: Python :: 3.4',
          'Topic :: Education',
          'Topic :: Games/Entertainment',
          'Topic :: Games/Entertainment :: Simulation',
      ],
)
