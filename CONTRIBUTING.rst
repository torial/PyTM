============
Contributing
============

Contributions are welcome, and they are greatly appreciated! Every
little bit helps, and credit will always be given.

Types of Contributions
----------------------

Report Bugs
~~~~~~~~~~~

Report bugs at https://github.com/torial/PyTM/issues.

If you are reporting a bug, please include:

* Your operating system name and version.
* Any details about your local setup that might be helpful in troubleshooting.
* Detailed steps to reproduce the bug.

Fix Bugs
~~~~~~~~

Look through the GitHub issues for bugs. Anything tagged with "bug"
is open to whoever wants to implement it.

Implement Features
~~~~~~~~~~~~~~~~~~

Look through the GitHub issues for features. Anything tagged with "feature"
is open to whoever wants to implement it.

Write Documentation
~~~~~~~~~~~~~~~~~~~

PyTM could always use more documentation, whether as part of the
official docs, in docstrings, or even on the web in blog posts,
articles, and such.

Submit Feedback
~~~~~~~~~~~~~~~

The best way to send feedback is to file an issue at https://github.com/torial/PyTM/issues.

If you are proposing a feature:

* Explain in detail how it would work.
* Keep the scope as narrow as possible, to make it easier to implement.
* Remember that this is a volunteer-driven project, and that contributions
  are welcome :)

Get Started!
------------

Ready to contribute? Here's how to set up `PyTM` for local development.

1. Fork_ the `PyTM` repo on GitHub.
2. Clone your fork locally::

    $ git clone git@github.com:your_name_here/PyTM.git

3. Install in editable mode with all dependencies::

    $ cd PyTM
    $ pip install -e ".[web]"
    $ pip install pytest

4. Create a branch for local development::

    $ git checkout -b name-of-your-bugfix-or-feature

5. Make your changes and ensure the tests pass::

    $ pytest

6. Commit your changes and push your branch to GitHub::

    $ git add .
    $ git commit -m "Your detailed description of your changes."
    $ git push origin name-of-your-bugfix-or-feature

7. Submit a pull request through the GitHub website.

.. _Fork: https://github.com/torial/PyTM/fork

Pull Request Guidelines
-----------------------

Before you submit a pull request, check that it meets these guidelines:

1. The pull request should include tests.
2. If the pull request adds functionality, the docs should be updated.
3. All tests should pass for Python 3.12+.

Tips
----

To run a subset of tests::

    $ pytest tests/test_cli.py

Publishing to PyPI
------------------

These steps are for the package maintainer only.

1. Install the build and upload tools::

    $ pip install build twine

2. Bump the version in both ``setup.py`` and ``PyTM/__init__.py``.

3. Add a changelog entry in ``HISTORY.rst``.

4. Build the distribution packages (creates ``dist/``)::

    $ python -m build

5. Check the packages before uploading::

    $ twine check dist/*

6. Upload to PyPI::

    $ twine upload dist/*

   You will be prompted for your PyPI username and password (or API token).
   To use an API token, set username to ``__token__`` and paste the token
   as the password, or configure ``~/.pypirc``::

    [pypi]
    username = __token__
    password = pypi-<your-token-here>

7. Verify the release at https://pypi.org/project/pytm-web/.

8. Tag the release in git::

    $ git tag v1.0.0
    $ git push origin v1.0.0
