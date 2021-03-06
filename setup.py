from setuptools import setup


setup(
    name='blink',
    version='0.0.1',
    description='REST client interface',
    long_description=open('README.rst').read(),
    author='Andy McKay',
    author_email='andym@mozilla.com',
    license='BSD',
    install_requires=['requests'],
    packages=['blink'],
    include_package_data=True,
    zip_safe=False,
    classifiers=[
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Operating System :: OS Independent',
    ]
)

