4teamwork buildouts
===================

This repositories provides some base buildouts to extend for.

It contains buildouts for testing and development as well as for production.

.. contents:: Table of Contents


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
- A check-translations script, warning if not translatable strings were used
  in templates and providing a translation statistic.

**test-plone-X.cfg**: There are various base buildouts extending the
**test-package.cfg** config and using known version sets of plone for pinning
the packages.

Example usage: add a configuration file to your
package (``test-plone-4.1.x.cfg``)::

    [buildout]
    extends =
        https://raw.githubusercontent.com/4teamwork/ftw-buildouts/master/test-plone-4.1.x.cfg

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
- bin/i18n-build: Extract and sync translation strings. All you need to keep the
  package's translations in sync. Also syncs the files
  ``${buildout:package-name}-manual.pot`` (manually created translations) and
  ``${buildout:package-name}-content.pot`` (translations from `ftw.inflator`_
  initial content).
- bin/upgrade: `ftw.upgrade <https://github.com/4teamwork/ftw.upgrade>`_ script
  for managing upgrade steps.

Example usage: add a configuration file to your
package (``development.cfg``)::

    [buildout]
    extends =
        https://raw.githubusercontent.com/4teamwork/ftw-buildouts/master/test-plone-4.2.x.cfg
        https://raw.githubusercontent.com/4teamwork/ftw-buildouts/master/plone-development.cfg

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
        https://raw.githubusercontent.com/4teamwork/ftw-buildouts/master/production.cfg
        https://raw.githubusercontent.com/4teamwork/ftw-buildouts/master/zeoclients/4.cfg

    deployment-number = 05

    filestorage-parts =
        www.mywebsite.com

    instance-eggs +=
        mywebsite

    [versions]
    zc.buildout = ${proposed-versions:zc.buildout}
    setuptools = ${proposed-versions:setuptools}


Pinning setuptools and buildout
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Since the Plone KGS are pinning setuptools and zc.buildout to the version from the time
of the release, it will get outdated over time.
In order to use the newest versions of setuptools and zc.buildout, ``production.cfg``
provides new pinnings. It can be used like this:

.. code:: ini

    [versions]
    zc.buildout = ${proposed-versions:zc.buildout}
    setuptools = ${proposed-versions:setuptools}




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
        https://raw.githubusercontent.com/4teamwork/ftw-buildouts/master/production.cfg

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
  10510, "bin/instancepub", "Additional ZEO client for ftw.publisher (optional)"
  10519, "bin/maintenance", "Maintenance HTTP Server (ftw.maintenanceserver)"
  "...", "bin/instance...", "..."
  10520, "bin/zeo", "ZEO Server (Database)"
  10521, "bin/zeo", "ZRS Replication Port"
  10530, "bin/solr-instance", "Solr instance"
  10532, "bin/tika-server", "Tika JAXRS Server"
  10533, "bin/redis", "Redis instance"
  10534, "gever-ui", "Frontend for Gever deployments"
  10550, "bin/haproxy", "Haproxy (reserved, not installation yet)"
  10581, "Monitor for instance1", "ftw.monitor TCP socket for health checks"
  "...", "Monitor for instance...", "..."
  10599, "bin/supervisord", "Supervisor daemon"
  8800, "HaProxy", "HaProxy status page (Server-wide)"
  8801, "HaProxy", "HaProxy stats socket (Server-wide)"


Buildout configuration
~~~~~~~~~~~~~~~~~~~~~~

There is a variety of options which can be configured in the buildout.
Here is a full example, below is the detail explanation:

.. code:: ini

    [buildout]
    extends =
        https://raw.githubusercontent.com/4teamwork/ftw-buildouts/master/production.cfg
        https://raw.githubusercontent.com/4teamwork/ftw-buildouts/master/zeoclients/4.cfg

    deployment-number = 05

    filestorage-parts =
        www.mywebsite.com

    instance-eggs +=
        mywebsite

    supervisor-client-startsecs = 60
    supervisor-email = zope@localhost
    supervisor-memmon-size = 1200MB
    supervisor-memmon-options = -a ${buildout:supervisor-memmon-size} -m ${buildout:supervisor-email}
    supervisor-httpok-timeout = 40
    supervisor-httpok-options = -t ${buildout:supervisor-httpok-timeout} -m ${buildout:supervisor-email}
    supervisor-httpok-view =

    os-user = zope

    plone-languages = en de fr

    zcml-additional-fragments +=
        <include package="my.package" file="meta.zcml" />
        <myPackageSecurity token="123123" />

    [instance4]
    supervisor-autostart = false


These are the most common configuration settings.
You can also override any options in the sections of the parts.

Details:

- ``deployment-number`` - The deployment number is used as port base. See the `Port range configuration`_ section.
- ``filestorage-parts`` - Configures ZODB mount points, one per line.
- ``instance-eggs`` - List the eggs you want to install in the ZEO client. The ``Plone`` egg is added to this list.
- ``supervisor-client-startsecs`` - The time in seconds it takes to start the ZEO client until Plone is ready
  to handle requests. This depends on your server and how big your database is. If it is too low, HttpOk will
  loop-restart the zeo clients when you restart all zeo clients at the same time and the server has load.
- ``supervisor-email`` - The email address to notification messages of httpok and memmon are sent.
- ``supervisor-memmon-size`` - The size of RAM each ZEO client can use. If it uses more, memmon will restart it.
- ``supervisor-memmon-options`` - Allows to change or extend the memmon configuration options.
- ``supervisor-httpok-timeout`` - The number of seconds that httpok should wait for a response to the
  HTTP request before timing out.
- ``supervisor-httpok-options`` - Allows to change or extend the httpok settings per instance. The process name
  and the http address are added per ZEO client.
- ``supervisor-httpok-view`` - Allows to specify a view name (or any path relative to the Zope application root)
  that will be appended to the base URL for the instance, in order to build the full health check URL for the
  HttpOk plugin. Must return 200 OK to indicate the instance is healthy.
- ``os-user`` - The operating system user is used by supervisor, which makes sure
  that the processes managed by supervisor are started with this user.
  It defaults to ``zope``.
- ``plone-languages`` - The short names of the languages which are loaded by Zope.
- ``zcml-additional-fragments`` - Define additional zcml to load. See the `Additional ZCML`_ section.
- ``instance-zcml`` - Add packages to the instances `zcml` list.
- ``instance-early-zcml`` - Add packages on top of the instances `zcml` list.
- ``supervisor-autostart`` - by default, all instances except instance0 will be automatically started in supervisor. By setting ``supervisor-autostart`` to ``false`` for a specific ``[instanceX]`` section, this can be overridden.


HAProxy / Supervisor integration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The `supervisor-haproxy`_ event listener tells haproxy to remove backends / add
backends to the load balancing when supervisor detects instances to be stopping
and starting.

Example configuration:

.. code:: ini

    [buildout]
    extends =
        https://raw.githubusercontent.com/4teamwork/ftw-buildouts/master/production.cfg
        https://raw.githubusercontent.com/4teamwork/ftw-buildouts/master/zeoclients/3.cfg
        https://raw.githubusercontent.com/4teamwork/ftw-buildouts/master/haproxy.cfg

    deployment-number = 05

    # If you want to change the default configuration, copy and change the settings below:
    # supervisor-haproxy-backend = plone${buildout:deployment-number}
    # supervisor-haproxy-socket = tcp://localhost:8801


The ``haproxy.cfg`` works well when using names in HAProxy such as "plone05" for
the backend and "plone0502" for the servers (=zope instances).
If you name backends and servers differently you may want to configure the name
with ``supervisor-haproxy-backend`` variable.

Example HaProxy configuration:

.. code:: ini

    global
       stats socket ipv4@0.0.0.0:8801 level admin

    defaults
        mode http
        timeout connect 10s
        timeout client 5m
        timeout server 5m


    frontend plone04
        bind *:10450
        default_backend plone04

    backend plone04
        server plone0401 localhost:10401 cookie p01 check inter 10s downinter 15s maxconn 5 rise 1 slowstart 60s
        server plone0402 localhost:10402 cookie p02 check inter 10s downinter 15s maxconn 5 rise 1 slowstart 60s
        server plone0403 localhost:10403 cookie p03 check inter 10s downinter 15s maxconn 5 rise 1 slowstart 60s


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
        https://raw.githubusercontent.com/4teamwork/ftw-buildouts/master/production.cfg
        https://raw.githubusercontent.com/4teamwork/ftw-buildouts/master/maintenance-server.cfg

    deployment-number = 05


Relstorage
~~~~~~~~~~
When including ``production-relstorage.cfg`` as the example shows below, no
ZEO Server and filestorage will be installed. Besides that, the relstorage will
be configured according to the relstorage buildout variables. The Following
variables have to be defined in the buildout section:

- relstorage-type
- relstorage-user
- relstorage-pw
- relstorage-shared-blob-dir
- relstorage-commit-lock-id
- relstorage-blob-cache-size


Example:

.. code:: ini

    [buildout]
    extends =
        https://raw.githubusercontent.com/4teamwork/ftw-buildouts/master/production.cfg
        https://raw.githubusercontent.com/4teamwork/ftw-buildouts/master/production-relstorage.cfg

    relstorage-type = oracle
    relstorage-user = user1
    relstorage-pw = secure
    relstorage-blob-cache-size = 1gb
    relstorage-shared-blob-dir = false
    relstorage-commit-lock-id = 7



ZODB Replicated Storage (ZRS)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Including ``zrs-primary.cfg`` configures the ZEO server as primary storage listening
on port ``1XX21``.

Example:

.. code:: ini

    [buildout]
    extends =
        https://raw.githubusercontent.com/4teamwork/ftw-buildouts/master/production.cfg
        https://raw.githubusercontent.com/4teamwork/ftw-buildouts/master/zrs-primary.cfg

    deployment-number = 05

Including ``zrs-secondary.cfg`` configures the ZEO server as a secondary storage replicating
from the storage given in the option ``zrs-replicate-from`` in the ``buildout`` part. In addition
ZEO clients are configured as read-only.

Example:

.. code:: ini

    [buildout]
    extends =
        https://raw.githubusercontent.com/4teamwork/ftw-buildouts/master/production.cfg
        https://raw.githubusercontent.com/4teamwork/ftw-buildouts/master/zrs-secondary.cfg

    deployment-number = 05
    zrs-replicate-from = primaryhost.net:10121


Tika server
~~~~~~~~~~~

The ``tika-jaxrs-server.cfg`` installs and configures `ftw.tika`_, and sets up
an `Apache Tika`_ JAXRS server as daemon, which provides document to text
transforms (e.g. for fulltext indexing).
A ``bin/tika-server`` script is installed and hooked up with supervisor and ``ftw.tika``
is configured. You just need to install ``ftw.tika`` in ``portal_setup``.

Example:

.. code:: ini

    [buildout]
    extends =
        https://raw.githubusercontent.com/4teamwork/ftw-buildouts/master/production.cfg
        https://raw.githubusercontent.com/4teamwork/ftw-buildouts/master/tika-jaxrs-server.cfg

    deployment-number = 05


Server-wide tika deployment
~~~~~~~~~~~~~~~~~~~~~~~~~~~

When having multiple Plone installations on the same server, it is effient to
only use one tika server:

.. code:: ini

    [buildout]
    extends =
        https://raw.githubusercontent.com/4teamwork/ftw-buildouts/master/tika-jaxrs-standalone.cfg
        versions.cfg

    deployment-number = 99


This sets up a complete standalone deployment with a supervisor and a memmon.
In order to use that in the Plone deployments, just extend the "remote" config:

.. code:: ini

    [buildout]
    extends =
        https://raw.githubusercontent.com/4teamwork/ftw-buildouts/master/production.cfg
        https://raw.githubusercontent.com/4teamwork/ftw-buildouts/master/tika-jaxrs-remote.cfg

    deployment-number = 05
    tika-deployment-number = 99


Solr
~~~~

The solr configurations provide a standard way to install solr,
based on `collective.solr`_ and `ftw.solr`_.

Standard installation
+++++++++++++++++++++

For production:

.. code:: ini

    [buildout]
    extends =
        https://raw.githubusercontent.com/4teamwork/ftw-buildouts/master/production.cfg
        https://raw.githubusercontent.com/4teamwork/ftw-buildouts/master/solr.cfg

    deployment-number = 05

For local development:

.. code:: ini

    [buildout]
    extends =
        https://raw.githubusercontent.com/4teamwork/ftw-buildouts/master/plone-development.cfg
        https://raw.githubusercontent.com/4teamwork/ftw-buildouts/master/plone-development-solr.cfg


Custom core configuration
+++++++++++++++++++++++++

It is possible to change the solr core configuration or add additional cores.
Take a look at the ``solr-core-template`` section in the ``solr-base.cfg``
for the options you may change.

For having the changes both, in production and development, the standard way to
do customizations is to add a ``solr.cfg`` in your project repository and extend
it both in development and in production buildout configurations.
The ``solr.cfg`` is a configuration extension and should not extend anything.

Example local ``solr.cfg``:

.. code:: ini

    [solr-settings]
    solr-cores =
        main-core
        another-core
    solr-default-core = main-core

    [main-core]
    <= solr-core-template
    max-num-results = 2000

    [anothre-core]
    <= solr-core-template
    max-num-results = 500


Example ``production-*.cfg``:

.. code:: ini

    [buildout]
    extends =
        https://raw.githubusercontent.com/4teamwork/ftw-buildouts/master/production.cfg
        https://raw.githubusercontent.com/4teamwork/ftw-buildouts/master/solr.cfg
        solr.cfg

    deployment-number = 05

Example ``development.cfg``:

.. code:: ini

    [buildout]
    extends =
        https://raw.githubusercontent.com/4teamwork/ftw-buildouts/master/plone-development.cfg
        https://raw.githubusercontent.com/4teamwork/ftw-buildouts/master/plone-development-solr.cfg
        solr.cfg


Redis
~~~~~

In the ``redis`` folder there are standard buildouts for installing a dedicated
redis installation within the buildout directory.
You can simply extend ``redis/development.cfg`` or ``redis/production.cfg``,
depending on your base config file, and then choose the redis version with
e.g. ``redis/3.2.3.cfg``.

Production buildout example:

.. code:: ini

    [buildout]
    extends =
        https://raw.githubusercontent.com/4teamwork/ftw-buildouts/master/production.cfg
        https://raw.githubusercontent.com/4teamwork/ftw-buildouts/master/redis/production.cfg
        https://raw.githubusercontent.com/4teamwork/ftw-buildouts/master/redis/3.2.3.cfg

Local development buildout example:

.. code:: ini

    [buildout]
    extends =
        test-plone-4.3.7.cfg
        https://raw.githubusercontent.com/4teamwork/ftw-buildouts/master/plone-development.cfg
        https://raw.githubusercontent.com/4teamwork/ftw-buildouts/master/redis/development.cfg
        https://raw.githubusercontent.com/4teamwork/ftw-buildouts/master/redis/3.2.3.cfg


collective.taskqueue
~~~~~~~~~~~~~~~~~~~~

When using `collective.taskqueue`_, you need to configure a queue and a
queue-server in your buildout.
For convenience there are some standard queue configuration buildouts which simply
can be exended.

Local volatile queue
++++++++++++++++++++

The local volatile queue is an in-memory queue which will be lost when terminating
a process. If you do important stuff you should consider installing redis.

For production:

.. code:: ini

    [buildout]
    extends =
        https://raw.githubusercontent.com/4teamwork/ftw-buildouts/master/production.cfg
        https://raw.githubusercontent.com/4teamwork/ftw-buildouts/master/taskqueue/volatile-production.cfg

For development:

.. code:: ini

    [buildout]
    extends =
        test-plone-4.3.x.cfg
        https://raw.githubusercontent.com/4teamwork/ftw-buildouts/master/plone-development.cfg
        https://raw.githubusercontent.com/4teamwork/ftw-buildouts/master/taskqueue/volatile-development.cfg


Redis queue
+++++++++++

Redis can be used as queue backend.
By default, redis is not configured to really persist everything.
With the standard configuration provided in ``ftw-buildouts``, redis is set up
and configured to persist the queue.

For production:

.. code:: ini

    [buildout]
    extends =
        https://raw.githubusercontent.com/4teamwork/ftw-buildouts/master/production.cfg
        https://raw.githubusercontent.com/4teamwork/ftw-buildouts/master/redis/production.cfg
        https://raw.githubusercontent.com/4teamwork/ftw-buildouts/master/redis/3.2.3.cfg
        https://raw.githubusercontent.com/4teamwork/ftw-buildouts/master/taskqueue/redis-production.cfg

For development:

.. code:: ini

    [buildout]
    extends =
        test-plone-4.3.x.cfg
        https://raw.githubusercontent.com/4teamwork/ftw-buildouts/master/plone-development.cfg
        https://raw.githubusercontent.com/4teamwork/ftw-buildouts/master/redis/development.cfg
        https://raw.githubusercontent.com/4teamwork/ftw-buildouts/master/taskqueue/redis-development.cfg


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
        https://raw.githubusercontent.com/4teamwork/ftw-buildouts/master/production.cfg
        https://raw.githubusercontent.com/4teamwork/ftw-buildouts/master/warmup.cfg

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
        https://raw.githubusercontent.com/4teamwork/ftw-buildouts/master/production.cfg
        https://raw.githubusercontent.com/4teamwork/ftw-buildouts/master/warmup.cfg

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
        https://raw.githubusercontent.com/4teamwork/ftw-buildouts/master/production.cfg
        https://raw.githubusercontent.com/4teamwork/ftw-buildouts/master/warmup.cfg

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


One thread per Zope instance
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For production buildouts, it may be desirable to run Zope instances with one
ZServer thread per instance in order to get more predictable memory usage
and load balancing.

In order to run instances with one single thread, the ``single-thread.cfg``
can be used:

.. code:: ini

    [buildout]
    extends =
        https://raw.githubusercontent.com/4teamwork/ftw-buildouts/master/production.cfg
        https://raw.githubusercontent.com/4teamwork/ftw-buildouts/master/zeoclients/4.cfg
        https://raw.githubusercontent.com/4teamwork/ftw-buildouts/master/single-thread.cfg

This buildout *must* be extended after ``production.cfg`` and, if present,
``zeoclients/n.cfg`` and ``warmup.cfg``. It will:

- Set ``zserver-threads`` to ``1`` for each Zope instance
- Include ``ftw.monitor``
- Remove the ``HttpOk`` plugins from supervisor
- Remove ``collective.warmup`` (if present)

Once this buildout is used, the HAProxy health check needs to be switched
to a TCP health check to the ``ftw.monitor`` port (instead of a HTTP health
check to the instance port). See the
`corresponding section in the ftw.monitor README <https://github.com/4teamwork/ftw.monitor#haproxy-example>`_
for an example HAProxy configuration.


Chameleon
~~~~~~~~~

The ``chameleon.cfg`` enables the Chameleon templating engine with our custom
integration `ftw.chameleon`_ and provides default configuration for use in
production and development.

If you want to run your tests with chameleon, you should add ``ftw.chameleon``
to the ``install_requires`` list in your ``setup.py``.

Production example:

.. code:: ini

    [buildout]
    extends =
        https://raw.githubusercontent.com/4teamwork/ftw-buildouts/master/production.cfg
        https://raw.githubusercontent.com/4teamwork/ftw-buildouts/master/chameleon.cfg

    deployment-number = 05


Development example:

.. code:: ini

    [buildout]
    extends =
        https://raw.githubusercontent.com/4teamwork/ftw-buildouts/master/plone-development.cfg
        https://raw.githubusercontent.com/4teamwork/ftw-buildouts/master/chameleon.cfg


Slack
~~~~~

It is often useful to send notifications to a slack channel when certain things happen.
For example if you run a maintenance job you may want to receive a notification when it is finished.
The slacker config just installs a simple script for slacking messages.

- `create a Slack webhook <https://my.slack.com/services/new/incoming-webhook/>`_.
- update your buildout:

.. code:: ini

    [buildout]
    extends =
        https://raw.githubusercontent.com/4teamwork/ftw-buildouts/master/production.cfg
        https://raw.githubusercontent.com/4teamwork/ftw-buildouts/master/slacker.cfg

    slack-webhook = https://hooks.slack.com/services/111/222/333
    deployment-number = 05

- send messsages:

.. code:: sh

  $ ./bin/slacker -t "Hello World"
  $ ./bin/slacker -t "Done" -u "migration-bot" -i ":robot:" -c "myproject-migration"
  $ echo "all done" | ./bin/slacker -s
  $ echo '{"text": "Important things", "icon_emoji": "monkey_face"}' | ./bin/slacker -s -r

Options:

.. code::

  -t "Message, may contain emojis :+1:"
  -u "user name, must not be registered"
  -i ":smile:"
  -c "channel"
  -s read stdin
  -r text is raw json


Maintaining ftw-buildouts
-------------------------

Updating deployment version pinnings
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``production.cfg`` provides version pinnings for the deployment related eggs,
such as buildout recipes and extensions.
From time to time we want to update the production version pinnings to the newest versions.
In the directory ``production-versions-buildout`` there is a buildout which helps updating
to the newest version.

Usage:

.. code:: sh

    $ cd production-versions-buildout
    $ python2.7 bootstrap.py
    $ bin/buildout
    $ bin/checkversions

Then manually update the ``[proposed-versions]`` in ``../production.cfg`` according to
the versions proposed by ``bin/checkversions``.

Finally run ``bin/buildout`` again to verify the versions constraints.


.. _coverage: https://pypi.python.org/pypi/coverage
.. _Cobertura Jenkins Plugin: https://wiki.jenkins-ci.org/display/JENKINS/Cobertura+Plugin
.. _Warnings Plugin: https://wiki.jenkins-ci.org/display/JENKINS/Warnings+Plugin
.. _omelette: https://pypi.python.org/pypi/collective.recipe.omelette
.. _PhantomJS: http://phantomjs.org/
.. _ftw.recipe.deployment: https://github.com/4teamwork/ftw.recipe.deployment
.. _ftw.inflator: https://github.com/4teamwork/ftw.inflator
.. _ftw.tika: https://github.com/4teamwork/ftw.tika
.. _ftw.maintenanceserver: https://github.com/4teamwork/ftw.maintenanceserver
.. _Apache Tika: http://tika.apache.org/
.. _collective.warmup: https://github.com/collective/collective.warmup
.. _ftw.solr: https://github.com/4teamwork/ftw.solr
.. _collective.solr: https://github.com/collective/collective.solr
.. _collective.taskqueue: https://github.com/collective/collective.taskqueue
.. _supervisor-haproxy: https://pypi.python.org/pypi/supervisor-haproxy
.. _ftw.chameleon: https://github.com/4teamwork/ftw.chameleon
