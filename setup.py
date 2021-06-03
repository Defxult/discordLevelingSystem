from setuptools import setup, find_packages

def _get_readme():
    with open('README.md', encoding='utf-8') as fp:
        return fp.read()

classifiers = [
    'Development Status :: 4 - Beta',
    'Programming Language :: Python :: 3',
    'Programming Language :: Python :: 3.8',
    'Programming Language :: Python :: 3.9',
    'Topic :: Software Development :: Libraries',
    'Topic :: Software Development :: Libraries :: Python Modules'
]

tags = [
    'discord',
    'discord.py',
    'discord py',
    'discord level',
    'discord leveling system',
    'level',
    'levels',
    'leveling',
    'level up'
]

details = {
    'Github Repo' : 'https://github.com/Defxult/discordLevelingSystem',
    'Github Issues' : 'https://github.com/Defxult/discordLevelingSystem/issues',
    'Changelog' : 'https://github.com/Defxult/discordLevelingSystem/blob/main/CHANGELOG.txt'
}

setup(
    author='Defxult#8269',
    name='discordLevelingSystem',
    description='A library to implement a leveling system into a discord bot. Contains features such as XP, level, ranks, and role awards.',
    version='0.0.2', 
    url='https://github.com/Defxult',
    project_urls=details,
    classifiers=classifiers,
    long_description=_get_readme(),
    long_description_content_type='text/markdown',
    license='MIT',
    keywords=tags,
    packages=find_packages(),
    install_requires=['discord.py>=1.4.0', 'aiosqlite>=0.17.0']
)

# PyPI project description

# For full documentation of this library, visit the [Github repo](https://github.com/Defxult/discordLevelingSystem). For the time being, this PyPI page will only
# act as a placeholder that directs you to Github because a vast majority of fixes, changes, and additions will take place there during the initial stages of development.
# Feel free to install the current PyPI version, but updates will always be pushed to Github before PyPI.
