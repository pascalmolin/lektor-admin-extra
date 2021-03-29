import ast
import io
import re

from setuptools import setup, find_packages

with io.open('README.md', 'rt', encoding="utf8") as f:
    readme = f.read()

_description_re = re.compile(r'description\s+=\s+(?P<description>.*)')

with open('lektor_admin_extra.py', 'rb') as f:
    description = str(ast.literal_eval(_description_re.search(
        f.read().decode('utf-8')).group(1)))

setup(
    author='Pascal Molin',
    author_email='molin.maths@gmail.com',
    description=description,
    keywords='Lektor plugin admin help',
    license='MIT',
    long_description=readme,
    long_description_content_type='text/markdown',
    name='lektor-admin-extra',
    packages=find_packages(),
    py_modules=['lektor_admin_extra'],
    url='http://github.com/pascalmolin/lektor-admin-extra',
    version='0.1',
    classifiers=[
        'Framework :: Lektor',
        'Environment :: Plugins',
        'License :: OSI Approved :: MIT License',
    ],
    entry_points={
        'lektor.plugins': [
            'admin-extra = lektor_admin_extra:AdminExtraPlugin',
        ]
    }
)
