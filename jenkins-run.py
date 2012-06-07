#!/usr/bin/env python


"""This script is called by a jenkins job.
The job of the script is to install the package (current directory)
with the passed buildout configuration file, update source dependencies
using mr.developer (if there are any) and run all tests.
"""

from urlparse import urlparse
import ConfigParser
import os
import sys
import tempfile
import time
import urllib2


class Main(object):

    def __init__(self, args):
        if len(args) != 1 or not os.path.isfile(args[0]):
            print 'Usage: jenkins-run.py BUILDOUT-CONFIG-FILE'
            sys.exit(0)
        self.configfile = args[0]

    def __call__(self):
        self.symlink_buildout()
        if not os.path.isfile(os.path.join('bin', 'buildout')):
            self.run_bootstrap()
        self.pull_source_dependencies()
        self.run_buildout()
        sys.exit(self.run_tests())

    def symlink_buildout(self):
        if os.path.isfile('buildout.cfg') or os.path.lexists('buildout.cfg'):
            os.unlink('buildout.cfg')

        runcmd('ln -s %s buildout.cfg' % self.configfile) == 0 or \
            error('Symlinking failed.')

    def run_bootstrap(self):
        python_path = self.get_python_path()
        cmd = '%s bootstrap.py' % python_path
        runcmd(cmd) == 0 or error('Could not bootstrap.')

    def pull_source_dependencies(self):
        if not os.path.isfile(os.path.join('bin', 'develop')):
            return

        cmd = 'bin/develop up'
        if runcmd(cmd) == 0:
            return

        print '"%s" failure. Retry after 10 seconds' % cmd
        time.sleep(10)
        if runcmd(cmd) == 0:
            return

        print '"%s" second failure. Remove sources and continue with buildout.' % cmd
        runcmd('rm -rf src')

    def run_buildout(self):
        cmd = 'bin/buildout -n'
        runcmd(cmd) == 0 or error('buildout failed.')

    def run_tests(self):
        return runcmd('bin/test-jenkins')

    def get_python_path(self):
        buildout = BuildoutConfigReader(self.configfile).get_config()
        if buildout.has_option('buildout', 'jenkins_python'):
            value = buildout.get('buildout', 'jenkins_python')
            if value and value.startswith('$') and value[1:] in os.environ:
                value = os.environ.get(value[1:])
            if value:
                return value
            else:
                error(('Could not find python "%s" from '
                       '${buildout:jenkins_python}') % value)
        else:
            error('Could not find ${buildout:jenkins_python} '
                  'option in buildout.')


class BuildoutConfigReader(object):

    def __init__(self, mainconfig):
        self.mainconfig = os.path.abspath(mainconfig)
        self._temporary_downloaded = None

    def get_config(self):
        files = self.get_ordered_extend_files()
        files.reverse()
        return self.load_config_files(files)

    def load_config_files(self, files):
        parser = ConfigParser.SafeConfigParser()
        for path in files:
            parser.read(path)
        return parser

    def get_ordered_extend_files(self):
        configfiles = []
        self.get_extends_recursive(configfiles, self.mainconfig)
        return configfiles

    def get_extends_recursive(self, configfiles, file_or_url):
        if file_or_url.startswith('http'):
            path = self._download_file(file_or_url)
        else:
            path = file_or_url
        directory, filename = os.path.split(path)

        if path in configfiles:
            return

        parser = ConfigParser.SafeConfigParser()
        parser.read(path)
        configfiles.append(path)

        if parser.has_option('buildout', 'extends'):
            extend_files = reversed(parser.get('buildout', 'extends').split())
            for filename in extend_files:
                if filename.startswith('http') or filename.startswith('/'):
                    path = filename
                else:
                    path = os.path.join(directory, filename)
                self.get_extends_recursive(configfiles, path)

    def _download_file(self, url):
        """ Download file from *url*, store it in a tempfile and return its path
        """
        if self._temporary_downloaded is None:
            # we need to keep a reference to the tempfile, otherwise it will be deleted
            # imidiately
            self._temporary_downloaded = {}

        if url in self._temporary_downloaded:
            return self._temporary_downloaded[url]['path']

        if '@' in url:
            # http basic auth in url

            # remove credentials part from url
            protocol, rest = url.split('://', 1)
            protocol += '://'
            credentials, rest = rest.split('@', 1)
            url = protocol + rest

            realm = HTTPRealmFinder(url).get()

            # install a basic auth handler
            if ':' in credentials:
                user, password = credentials.split(':', 1)
            else:
                user, password = credentials, None

            auth_handler = urllib2.HTTPBasicAuthHandler()
            auth_handler.add_password(realm=realm,
                                      uri=url,
                                      user=user,
                                      passwd=password)
            opener = urllib2.build_opener(auth_handler)
            urllib2.install_opener(opener)

        request = urllib2.Request(url)
        response = urllib2.urlopen(request)
        data = response.read()
        file_ = tempfile.NamedTemporaryFile()
        file_.write(data)
        file_.flush()

        self._temporary_downloaded[url] = {
            'path': file_.name,
            # It is important to keep a reference to the file handle,
            # otherwise it will be deleted immediately.
            'handle': file_,
            }

        return self._temporary_downloaded[url]['path']


class HTTPRealmFinderHandler(urllib2.HTTPBasicAuthHandler):
    def http_error_401(self, req, fp, code, msg, headers):
        realm_string = headers['www-authenticate']

        q1 = realm_string.find('"')
        q2 = realm_string.find('"', q1+1)
        realm = realm_string[q1+1:q2]

        self.realm = realm


class HTTPRealmFinder:
    def __init__(self, url):
        self.url = url
        scheme, domain, path, x1, x2, x3 = urlparse(url)

        handler = HTTPRealmFinderHandler()
        handler.add_password(None, domain, 'foo', 'bar')
        self.handler = handler

        opener = urllib2.build_opener(handler)
        urllib2.install_opener(opener)

    def ping(self, url):
        try:
            urllib2.urlopen(url)
        except urllib2.HTTPError:
            pass

    def get(self):
        self.ping(self.url)
        try:
            realm = self.handler.realm
        except AttributeError:
            realm = None

        return realm

    def prt(self):
        print self.get()


def runcmd(command):
    """Execute a command and return the actual exit code.
    """
    print '+ %s' % command
    sys.stdout.flush()
    return os.system(command) >> 8


def error(msg, exit=1):
    print 'ERROR: %s' % msg
    if exit != 0:
        sys.exit(exit)


if __name__ == '__main__':
    Main(sys.argv[1:])()
