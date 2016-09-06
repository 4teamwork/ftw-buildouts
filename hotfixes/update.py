#!/usr/bin/env python

from operator import itemgetter
import json
import os
import pkg_resources
import re
import urllib2


HOTFIX_VERSIONS = {}

BLACKLIST = (
    'plone4.csrffixes',
    'Products.PloneHotfix20160830',
)


def update_hotfixes_files():
    hotfixes = load_hotfixes()
    dirpath = os.path.dirname(os.path.abspath(__file__))

    for filename in sorted(os.listdir(dirpath)):
        if not filename.endswith('.cfg'):
            continue

        plone_version, _ = os.path.splitext(filename)
        print plone_version

        proposed = filter(requirement_filter(plone_version), hotfixes)

        with open(os.path.join(dirpath, filename), 'w+') as fileio:
            fileio.write('[buildout]\n\n')
            fileio.write('instance-eggs +=\n')
            for package in map(itemgetter('package'), proposed):
                fileio.write('    {}\n'.format(package))

            fileio.write('\n\n[versions]\n')
            for package in map(itemgetter('package'), proposed):
                hotfix_version = get_hotfix_version(package)
                fileio.write('{} = {}\n'.format(package, hotfix_version))


def load_hotfixes():
    hotfixes_javascript = http_get(
        'http://jone.github.io/plone-hotfixes/hotfixes.js')
    hotfixes = json.loads(re.search(r'var hotfixes =(.*});',
                                    hotfixes_javascript, re.DOTALL).group(1))
    [hotfix.update({'package': package}) for (package, hotfix) in hotfixes.items()]
    hotfixes = hotfixes.values()
    hotfixes = [hotfix for hotfix in hotfixes
                if hotfix['package'] not in BLACKLIST]
    return sorted(hotfixes, key=itemgetter('package'))


def get_hotfix_version(package):
    if package in HOTFIX_VERSIONS:
        return HOTFIX_VERSIONS[package]

    url = 'http://pypi.python.org/pypi/{}/json'.format(package)
    pkg_info = json.loads(http_get(url))
    HOTFIX_VERSIONS[package] = pkg_info['info']['version']
    return HOTFIX_VERSIONS[package]


def requirement_filter(plone_version):
    plone_version = pkg_resources.parse_version(plone_version)

    def required(hotfix):
        for first, last in hotfix.get('required_for_plone'):
            first = pkg_resources.parse_version(first)
            last = pkg_resources.parse_version(last)
            if first <= plone_version <= last:
                return True

        return False

    return required


def http_get(url):
    print 'GET', url
    return urllib2.urlopen(url).read()


def update_plone_versions():
    html = urllib2.urlopen('http://dist.plone.org/release/').read()
    versions = re.findall(r'<a[^>]*>([^>]*)</a>', html)
    versions.remove('../')
    versions = [version.strip('/') for version in versions]
    versions = filter(lambda version: not version.endswith('-pending'), versions)
    versions = filter(lambda version: not version.endswith('-latest'), versions)
    versions = filter(lambda version: not 'a' in version, versions)
    versions = filter(lambda version: not 'b' in version, versions)
    versions = filter(lambda version: not 'rc' in version, versions)
    versions = filter(lambda version: int(version[0]) > 3, versions)

    dirpath = os.path.dirname(os.path.abspath(__file__))
    for version in versions:
        path = dirpath + '/{}.cfg'.format(version)
        with open(path, 'a'):
            pass


if __name__ == '__main__':
    update_plone_versions()
    update_hotfixes_files()
