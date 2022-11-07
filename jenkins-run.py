#!/usr/bin/env python2.7


"""This script is called by a jenkins job.
The job of the script is to install the package (current directory)
with the passed buildout configuration file, update source dependencies
using mr.developer (if there are any) and run all tests.
"""

from md5 import md5
from urlparse import urlparse
import ConfigParser
import os
import subprocess
import sys
import tempfile
import time
import urllib2


class Main(object):

    def __init__(self, args):
        if len(args) == 0 and os.path.isfile('buildout.cfg'):
            self.configfile = 'buildout.cfg'

        elif len(args) == 1 and os.path.isfile(args[0]):
            self.configfile = args[0]

        else:
            print 'Usage: jenkins-run.py BUILDOUT-CONFIG-FILE'
            sys.exit(0)

        self.buildout_retries = 5
        self.current_buildout_attempt = 0

    def __call__(self):
        if self.configfile != 'buildout.cfg':
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
        def rerun_needed(errors):
            rerun_errors = (
                # bitbucket.org is offline while bootstrapping
                'HTTP Error 503: SERVICE UNAVAILABLE',

                # raw.githubusercontent.com has timed out:
                '[Errno socket error] [Errno 110] ',
                )

            for err in rerun_errors:
                if err in errors:
                    return True
            return False

        python_path = self.get_python_path()
        if python_path.endswith('buildout'):
            # we use another buildout to bootstrap - do it offline
            cmd = '%s -o bootstrap' % python_path

        else:
            # we use a regular python to bootstrap
            cmd = '%s bootstrap.py --setuptools-version 44.1.1' % python_path

            # If bootstrap is run with Python2.7, we need to restrict the
            # buildout version to <3
            if 'python2.7' in python_path:
                cmd += ' --buildout-version 2.13.8'

        runcmd_with_retries(
            cmd,
            rerun_needed,
            retries=5,
            sleep=5)

    def pull_source_dependencies(self):
        if not os.path.isfile(os.path.join('bin', 'develop')):
            return

        # Workaround for making sure that we remove the sources
        # when the fork (git remote) has changed and therefore
        # we need to clone a new version.
        # The problem is that bin/develop exits with "0" even
        # though there is an error.
        with tempfile.NamedTemporaryFile() as outfile:
            if runcmd('bin/develop up', teefile=outfile) == 0:
                outfile.seek(0)
                if 'ERROR: ' in outfile.read():
                    runcmd('rm -rf src')
                return

        runcmd_with_retries(
            'bin/develop up',
            lambda errors: True,
            retries=2,
            sleep=20) or runcmd('rm -rf src')

    def run_buildout(self):
        def rerun_needed(errors):
            rerun_errors = (
                "('http error', 502, 'Bad Gateway',",
                "IOError: ('http error', 502, 'Bad Gateway',",
                "mr.developer: error: The requested URL returned " + \
                    "error: 503 while accessing",
                "varnish-conf: <urlopen error timed out>",
                "varnish-conf: <urlopen error The read operation timed out>",
                "IOError: [Errno socket error]",
                "mr.developer: git pull of",  # 'package' failed.
                'timeout: timed out',
                'Error: Error downloading extends for URL',
                "IOError: ('http error', 503, 'Connection timed out',",
                'error: [Errno 104] Connection reset by peer',

                # Sometimes we get a 404 when pypi is maintained (?)
                "IOError: ('http error', 404, 'Not Found'",
                )

            for err in rerun_errors:
                if err in errors:
                    return True
            return False

        runcmd_with_retries(
            self.buildout_command,
            rerun_needed,
            retries=5,
            sleep=60) or error('Buildout failed.')

    @property
    def buildout_command(self):
        self.current_buildout_attempt += 1
        timeout = (2 ** (self.current_buildout_attempt - 1)) * 5
        return 'bin/buildout -n -t %i' % timeout

    def run_tests(self):
        return runcmd(os.environ.get('JENKINS_RUN_TEST_COMMAND', 'bin/test-jenkins'))

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
        self.extends_cache = ExtendsCache()

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
            path = self.extends_cache.get_cache_path_for(file_or_url)
            if path is None:
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
        print '  download', url
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


class ExtendsCache(object):
    """Loads config files from the global extends cache
    (~/.buildout/default.cfg) for guessing python version if there
    is one configured.
    """

    def __init__(self, config_file='~/.buildout/default.cfg'):
        self.extends_cache_directory = self._get_cache_directory(config_file)

    def get_cache_path_for(self, url):
        """Returns the path to the cache file, caching the contents of `url`.
        If there is not (yet) such a cache file, `None` is returned.
        """

        if not self.extends_cache_directory:
            return None

        hash_ = md5(url).hexdigest()

        cache_path = os.path.join(self.extends_cache_directory, hash_)
        if not os.path.isfile(cache_path):
            return None

        return cache_path

    def _get_cache_directory(self, config_file):
        config_file = os.path.expanduser(config_file)
        if not os.path.exists(config_file):
            return None

        parser = ConfigParser.SafeConfigParser()
        parser.read(config_file)

        if not parser.has_option('buildout', 'extends-cache'):
            return None

        cache_directory = os.path.expanduser(
            parser.get('buildout', 'extends-cache'))
        if not os.path.exists(cache_directory):
            return None

        return cache_directory


def runcmd(command, teefile=None):
    """Execute a command and return the actual exit code.
    """
    print ''
    print '+ %s' % command
    sys.stdout.flush()

    if teefile:
        tee = subprocess.Popen(["tee", teefile.name], stdin=subprocess.PIPE)
        os.dup2(tee.stdin.fileno(), sys.stderr.fileno())
        os.dup2(tee.stdin.fileno(), sys.stdout.fileno())

    return os.system(command) >> 8


def runcmd_with_retries(command, rerun_condition, retries=5, sleep=30):
    """Runs a command and retries if the exitcode is not 0.
    Expects a command (string) and a `rerun_condition` function, which will
    be called with the stderr (string) of the last run. If it returns
    `True` the command will be rerun.
    If the command still fails after `retries` the function returns
    `Flase`, otherwise `True`.
    """

    for attempt in range(1, retries + 2):
        is_last = attempt == retries + 1

        with tempfile.NamedTemporaryFile() as outfile:
            exitcode = runcmd(command, teefile=outfile)
            outfile.seek(0)
            errors = outfile.read()

        if exitcode == 0:
            return True

        elif not is_last and rerun_condition(errors):
            print 'Attempt %i of "%s" failed. Retrying after %s seconds.' % (
                attempt, command, sleep)
            print '\n'
            time.sleep(sleep)

        else:
            print 'Attempt %i of "%s" failed.' % (attempt, command)
            print '\n'
            return False

    assert exitcode != 0
    return False


def error(msg, exit=1):
    print 'ERROR: %s' % msg
    if exit != 0:
        sys.exit(exit)


if __name__ == '__main__':
    Main(sys.argv[1:])()
