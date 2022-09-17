from typing import Final, Literal
from discordLevelingSystem import __source__
from setuptools import setup, find_packages

def _get_readme():
    with open('README.md', encoding='utf-8') as fp:
        return fp.read()

def _version_info() -> str:
    version = (1, 2, 0)
    release_level: Literal['alpha', 'beta', 'rc', 'final'] = 'final'

    BASE: Final[str] = '.'.join([str(n) for n in version])

    if release_level == 'final':
        return BASE
    else:
        # try and get the last commit hash for a more precise version, if it fails, just use the basic version
        try:
            import subprocess
            p = subprocess.Popen(['git', 'ls-remote', __source__, 'HEAD'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            out, _ = p.communicate()
            short_hash = out.decode('utf-8')[:7]
            p.kill()
            return BASE + f"{release_level}+{short_hash}"
        except Exception:
            print('discordLevelingSystem notification: An error occurred when attempting to get the last commit ID of the repo for a more precise version of the library. Returning base development version instead.')
            return BASE + release_level

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
    version=_version_info(), 
    url='https://github.com/Defxult/discordLevelingSystem',
    project_urls=details,
    classifiers=classifiers,
    long_description=_get_readme(),
    long_description_content_type='text/markdown',
    license='MIT',
    keywords=tags,
    packages=find_packages(),
    install_requires=['aiosqlite>=0.17.0', 'discord.py>=2.0.0', 'Pillow>=9.2.0']
)
