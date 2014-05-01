4teamwork buildouts
===================

This repositories provides some base buildouts to extend for.

It contains buildouts for testing and development as well as for production.


Testing and development
-----------------------

Buildouts
~~~~~~~~~

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
developing a plone add-on package. It is an extension for a version specific
test buildout.

Features:

- bin/instance : A zope instance with plone, your package and development
  tools installed.
- bin/test : A test runner, testing this package only.
- bin/test-coverage : A test runner generating and open a coverage report.
- bin/zopepy : A python shell with zope environment.
- `omelette`_
- bin/qunit : Run qunit tests (tests/qunit/test*.html) using `PhantomJS`_.
- bin/i18n-build: Extract and sync translation strings. All you need to keep the
  package's translations in sync. Also syncs the files
  ``${buildout:package-name}-manual.pot`` (manually created translations) and
  ``${buildout:package-name}-content.pot`` (translations from `ftw.inflator`_
  initial content).

Example usage: add a configuration file to your
package (``development.cfg``)::

    [buildout]
    extends =
        https://raw.github.com/4teamwork/ftw-buildouts/master/test-plone-4.2.x.cfg
        https://raw.github.com/4teamwork/ftw-buildouts/master/plone-development.cfg

    package-name = my.package


Buildout options
~~~~~~~~~~~~~~~~

- ``${buildout:package-name}`` -- The name of the package (mandatory).
- ``${buildout:test-egg}`` -- Egg with extra included by test
  runners (defaults to ``${buildout:package-name} [tests]``).
- ``${buildout:package-directory}`` -- Option for changing the default
  namespace directory. This is used for packages wich have a different name than
  namespace. By default, for a package with name ``foo.bar`` the source is
  expected at ``foo/bar``, ``src/foo/bar`` or ``src/foo.bar/foo/bar``.


qunit tests / PhantomJS
~~~~~~~~~~~~~~~~~~~~~~~

Running qunit tests with jenkins compatible XML reports is possible with ``bin/qunit``.
It requires `PhantomJS`_ to be installed and either in the ``$PATH`` or in
``$PHANTOMJS`` environment variable.





Production
----------

The production buildouts allows to install a Plone with custom packages in a production
environment with as few configurations as possible.

The production buildouts are set up with theese features:

- A ZEO-Server / ZEO-Client environment
- Filestorage configuration
- `ftw.recipe.deployment`_ logrotate configuration and run-control scripts
- Supervisor configuration with superlance (HTTPOk per instance and Memmon)
- Port range sets for all ports used in this buildout
- Easily configurable


Using the buildout
~~~~~~~~~~~~~~~~~~

Extend your buildout from ``production.cfg``. This will install a ZEO enviroment two ZEO clients:

- ``bin/instance0`` - this is the administrative instance for maintenance. Supervisor does not start
  this instance automatically.
- ``bin/instance1`` - this is the productive instance where the visitors should land.

The amount of instance can be changed by extending another buildout configuration where the name
of the configuration is the amount of zeo clients to install.

An example:

.. code:: ini

    [buildout]
    extends =
        https://raw.github.com/4teamwork/ftw-buildouts/master/production.cfg
        https://raw.github.com/4teamwork/ftw-buildouts/master/zeoclients/4.cfg

    deployment-number = 05

    filestorage-parts =
        www.mywebsite.com

    instance-eggs +=
        mywebsite


.. _Additional ZCML:

Additional ZCML
~~~~~~~~~~~~~~~

There is a `problem <https://github.com/plone/plone.recipe.zope2instance/pull/13>`_ with
extending the ``zcml-additional``.
As a workaround we use the ``buildout:zcml-additional-fragments`` variable, which takes
care that ``zcml-additional`` is wrapped properly.

Usage example:

.. code:: ini

    [buildout]
    extends =
        https://raw.github.com/4teamwork/ftw-buildouts/master/production.cfg

    deployment-number = 05

    zcml-additional-fragments +=
        <include package="my.package" file="meta.zcml" />
        <myPackageSecurity token="123123" />


Port range configuration
~~~~~~~~~~~~~~~~~~~~~~~~

At 4teamwork we use a port range of 100 ports for each deployment. We use the deployment
number (two-digit) as prefix and append a leading ``1``.

For example if we use ``deployment-number = 05`` the ports would be:

.. csv-table::
  :header: "Port", "Service", "Description"

  10500, "bin/instance0", "Maintenance ZEO client"
  10501, "bin/instance1", "Default ZEO client"
  10502, "bin/instance2", "Additional ZEO client (optional)"
  10503, "bin/instance3", "Additional ZEO client (optional)"
  10504, "bin/instance4", "Additional ZEO client (optional)"
  10505, "bin/instance5", "Additional ZEO client (optional)"
  10519, "bin/maintenance", "Maintenance HTTP Server (ftw.maintenanceserver)"
  "...", "bin/instance...", "..."
  10520, "bin/zeo", "ZEO Server (Database)"
  10530, "bin/solr-instance", "Solr instance"
  10531, "bin/tika-server", "Tika Server"
  10150, "bin/haproxy", "Haproxy (reserved, not installation yet)"
  10199, "bin/supervisord", "Supervisor daemon"


Buildout configuration
~~~~~~~~~~~~~~~~~~~~~~

There is a variety of options which can be configured in the buildout.
Here is a full example, below is the detail explenation:

.. code:: ini

    [buildout]
    extends =
        https://raw.github.com/4teamwork/ftw-buildouts/master/production.cfg
        https://raw.github.com/4teamwork/ftw-buildouts/master/zeoclients/4.cfg

    deployment-number = 05

    filestorage-parts =
        www.mywebsite.com

    instance-eggs +=
        mywebsite

    supervisor-client-startsecs = 60
    supervisor-memmon-size = 1200MB
    supervisor-httpok-timeout = 40
    supervisor-email = zope@localhost
    supervisor-memmon-options = -a ${buildout:supervisor-memmon-size} -m ${buildout:supervisor-email}
    supervisor-httpok-options = -t ${buildout:supervisor-httpok-timeout} -m ${buildout:supervisor-email}

    plone-languages = en de fr

    zcml-additional-fragments +=
        <include package="my.package" file="meta.zcml" />
        <myPackageSecurity token="123123" />


These are the most common configuration settings.
You can also override any options in the sections of the parts.

Details:

- ``deployment-number`` - The deployment number is used as port base. See the `Port range configuration`_ section.
- ``filestorage-parts`` - Configures ZODB mount points, one per line.
- ``instance-eggs`` - List the eggs you want to install in the ZEO client. The ``Plone`` egg is added to this list.
- ``supervisor-client-startsecs`` - The time in seconds it takes to start the ZEO client until Plone is ready
  to handle requests. This depends on your server and how big your database is. If it is too low, HttpOk will
  loop-restart the zeo clients when you restart all zeo clients at the same time and the server has load.
- ``supervisor-memmon-size`` - The size of RAM each ZEO client can use. If it uses more, memmon will restart it.
- ``supervisor-httpok-timeout`` - The number of seconds that httpok should wait for a response to the
  HTTP request before timing out.
- ``supervisor-email`` - The email address to notification messages of httpok and memmon are sent.
- ``supervisor-memmon-options`` - Allows to change or extend the memmon configuration options.
- ``supervisor-httpok-options`` - Allows to change or extend the httpok settings per instance. The process name
  and the http address are added per ZEO client.
- ``plone-languages`` - The short names of the languages which are loaded by Zope.
- ``zcml-additional-fragments`` - Define additional zcml to load. See the `Additional ZCML`_ section.



Maintenance HTTP Server
~~~~~~~~~~~~~~~~~~~~~~~

When including the ``maintenance-server.cfg``, a maintenance HTTP server is automatically
configured (using `ftw.maintenanceserver`_), listening on port ``1XX19`` and serving
the ``${buildout:directory}/maintenance`` directory, which is expected to contain
an ``index.html`` file.

Example:

.. code:: ini

    [buildout]
    extends =
        https://raw.github.com/4teamwork/ftw-buildouts/master/production.cfg
        https://raw.github.com/4teamwork/ftw-buildouts/master/maintenance-server.cfg

    deployment-number = 05


Tika server
~~~~~~~~~~~

The ``tika-server.cfg`` installs and configures `ftw.tika`_ as daemon, which provides
document to text transforms (e.g. for fulltext indexing) using `Apache Tika`_.
A ``bin/tika-server`` script is installed and hooked up with supervisor and ``ftw.tika``
is configured. You just need to install ``ftw.tika`` in ``portal_setup``.

Example:

.. code:: ini

    [buildout]
    extends =
        https://raw.github.com/4teamwork/ftw-buildouts/master/production.cfg
        https://raw.github.com/4teamwork/ftw-buildouts/master/tika-server.cfg

    deployment-number = 05


Warmup
~~~~~~

For production deployments, the ``warmup.cfg`` installs and configures
`collective.warmup`_ to automatically hit the site root when an instance is started
or restarted.
It also requests the resources, resulting in cooked resources (JavaScript / CSS).

It works without further configuration when there is *only one filestorage-part*
configured and the *plone site has the ID* ``platform``.

Simple example:

.. code:: ini

    [buildout]
    extends =
        https://raw.github.com/4teamwork/ftw-buildouts/master/production.cfg
        https://raw.github.com/4teamwork/ftw-buildouts/master/warmup.cfg

    deployment-number = 05

    filestorage-parts = www.mywebsite.com
    instance-eggs += mywebsite

.. note:: Make sure to use ``instance-eggs +=`` rather than ``instance-eggs =``,
   otherwise the ``collective.warmup`` will not be installed.

When booting up ``bin/instance1``, this configuration will make a request to
``http://localhost:10501/www.mywebsite.com/platform``.

If you have different paths you can configuration the base path manually:

.. code:: ini

    [buildout]
    extends =
        https://raw.github.com/4teamwork/ftw-buildouts/master/production.cfg
        https://raw.github.com/4teamwork/ftw-buildouts/master/warmup.cfg

    deployment-number = 05

    filestorage-parts =
        www.mywebsite.com
        test.mywebsite.com
    instance-eggs += mywebsite

    [warmup-configuration]
    base_path = www.mywebsite.com/Plone

If you want to add more urls to check, follow the instructions in the
`collective.warmup`_ readme and fill in ``warmup-configuration`` options, e.g.:

.. code:: ini

    [buildout]
    extends =
        https://raw.github.com/4teamwork/ftw-buildouts/master/production.cfg
        https://raw.github.com/4teamwork/ftw-buildouts/master/warmup.cfg

    deployment-number = 05

    filestorage-parts = www.mywebsite.com
    instance-eggs += mywebsite

    [warmup-configuration]
    urls += sitemap

    url-sections +=
        [sitemap]
        path = ${warmup-configuration:base_path}/sitemap
        check_exists = Sitemap

The ``warmup-configuration:urls`` and ``warmup-configuration:url-sections`` options
will be included in the generated warmup configuration file.



.. _coverage: http://pypi.python.org/pypi/coverage
.. _Cobertura Jenkins Plugin: https://wiki.jenkins-ci.org/display/JENKINS/Cobertura+Plugin
.. _Warnings Plugin: https://wiki.jenkins-ci.org/display/JENKINS/Warnings+Plugin
.. _omelette: http://pypi.python.org/pypi/collective.recipe.omelette
.. _PhantomJS: http://phantomjs.org/
.. _ftw.recipe.deployment: https://github.com/4teamwork/ftw.recipe.deployment
.. _ftw.inflator: https://github.com/4teamwork/ftw.inflator
.. _ftw.tika: https://github.com/4teamwork/ftw.tika
.. _ftw.maintenanceserver: https://github.com/4teamwork/ftw.maintenanceserver
.. _Apache Tika: http://tika.apache.org/
.. _collective.warmup: https://github.com/collective/collective.warmup
