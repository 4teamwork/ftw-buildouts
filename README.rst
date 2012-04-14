4teamwork buildouts
===================

This repositories provides some base buildouts for development and testing.


Buildouts
---------

**test-package.cfg**: A base buildout configuration for testing a single
package with jenkins.

Features:

- Provides a ``bin/test-jenkins`` executable which runs the test and some
  analysis tools on the content.
- Detailed coverage report using `coverage`_ (optimized for use with the
  `Cobertura Jenkins Plugin`_).
- Pyflakes report (use jenkins `Warnings Plugin`_).
- Pep8 report
- Pylint report
- A check-translations script, warning if not translatable strings were used
  in templates and providing a translation statistic.

**test-plone-X.cfg**: There are various base buildouts extending the
**test-package.cfg** config and using known version sets of plone for pinning
the packages.

Example usage: add a configuration file to your
package (``test-plone-4.1.x.cfg``)::

    [buildout]
    extends =
        https://raw.github.com/4teamwork/ftw-buildouts/master/test-plone-4.1.x.cfg

    package-name = my.package

The buildout assumes that your source code is in the subfolder
``my/package`` (see option ``${buildout:package-directory}``) and that the
package has a ``extras_require`` with the name ``tests`` (see option
``${buildout:test-egg}``).

**plone-development.cfg**: Provides a buildout base configuration for
developing a plone add-on package.

Features:

- bin/instance : A zope instance with plone, your package and development
  tools installed.
- bin/test : A test runner, testing this package only.
- bin/test-coverage : A test runner generating and open a coverage report.
- bin/zopepy : A python shell with zope environment.
- `omelette`_

Example usage: add a configuration file to your
package (``development.cfg``)::

    [buildout]
    extends =
        http://dist.plone.org/release/4.1/versions.cfg
        https://raw.github.com/4teamwork/ftw-buildouts/master/plone-development.cfg

    package-name = my.package


Buildout options
----------------

- ``${buildout:package-name}`` -- The name of the package (mandatory).
- ``${buildout:test-egg}`` -- Egg with extra included by test
  runners (defaults to ``${buildout:package-name} [tests]``).
- ``${buildout:package-directory}`` -- Option for changing the default
  namespace directory. This is used for packages wich have a different name than
  namespace. By default, for a package with name ``foo.bar`` the source is
  expected at ``foo/bar``, ``src/foo/bar`` or ``src/foo.bar/foo/bar``.



.. _coverage: http://pypi.python.org/pypi/coverage
.. _Cobertura Jenkins Plugin: https://wiki.jenkins-ci.org/display/JENKINS/Cobertura+Plugin
.. _Warnings Plugin: https://wiki.jenkins-ci.org/display/JENKINS/Warnings+Plugin
.. _omelette: http://pypi.python.org/pypi/collective.recipe.omelette
