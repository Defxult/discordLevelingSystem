from setuptools import setup, find_packages

def _get_readme():
    with open('README.md', encoding='utf-8') as fp:
        return fp.read()

classifiers = [
    'Development Status :: 3 - Alpha',
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
    'Github Issues' : 'https://github.com/Defxult/discordLevelingSystem/issues'
}

setup(
    author='Defxult#8269',
    name='discordLevelingSystem',
    description='A local discord.py leveling system powered by SQLite',
    version='0.0.1', 
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
