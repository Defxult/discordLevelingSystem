from discordLevelingSystem import version_info
from setuptools import setup, find_packages

def _get_readme():
    with open('README.md', encoding='utf-8') as fp:
        return fp.read()

classifiers = [
    'Development Status :: 5 - Production/Stable',
    'Programming Language :: Python :: 3',
    'Programming Language :: Python :: 3.8',
    'Programming Language :: Python :: 3.9',
    'Programming Language :: Python :: 3.10',
    'Topic :: Software Development :: Libraries',
    'Topic :: Software Development :: Libraries :: Python Modules'
]

tags = [
    'database',
    'discord',
    'discord bot',
    'discord.py',
    'discord py',
    'discord level',
    'discord leveling',
    'discord leveling system',
    'level',
    'levels',
    'leveling',
    'level up',
    'level system',
    'mee6',
    'rank',
    'ranking',
    'role award',
    'xp'
]

details = {
    'Changelog' : 'https://github.com/Defxult/discordLevelingSystem/blob/main/CHANGELOG.md'
}

setup(
    author='Defxult#8269',
    name='discordLevelingSystem',
    description='A library to implement a leveling system into a discord bot. Contains features such as XP, level, ranks, and role awards.',
    version=str(version_info()), 
    url='https://github.com/Defxult/discordLevelingSystem',
    project_urls=details,
    classifiers=classifiers,
    long_description=_get_readme(),
    long_description_content_type='text/markdown',
    license='MIT',
    keywords=tags,
    packages=find_packages(),
    install_requires=['aiosqlite>=0.17.0'] #! update to discord.py 2.0 when released
)
