 .. image:: https://github.com/wasi0013/PyTM/raw/master/ext/images/PyTM-logo.png
    :target: https://github.com/wasi0013/PyTM/
    :alt: PyTM - Logo




**PУΓM** -  A CLI time tracker for projects with invoice generation
-------------------------------------------------------------------


|image1| |coverage| |image3| |Contributors| |DownloadStats| |DocsStats| |image2|
================================================================================

.. |image1| image:: https://badge.fury.io/py/python-pytm.png
   :target: https://badge.fury.io/py/python-pytm
.. |image2| image:: https://img.shields.io/pypi/l/python-pytm.svg
   :target: https://pypi.org/project/python-pytm/
.. |image3| image:: https://img.shields.io/pypi/pyversions/python-pytm.svg
   :target: https://pypi.org/project/python-pytm/
   :alt: Supported Python Versions
.. |Contributors| image:: https://img.shields.io/github/contributors/wasi0013/PyTM.svg
   :target: https://github.com/wasi0013/PyTM/graphs/contributors
   :alt: List of Contributors
.. |DownloadStats| image:: https://pepy.tech/badge/python-pytm
   :target: https://pepy.tech/project/python-pytm
   :alt: Download Stats
.. |DocsStats| image:: https://readthedocs.org/projects/pytm/badge/?version=latest
   :target: https://pytm.readthedocs.io/en/latest/?badge=latest
   :alt: Documentation Status
.. |coverage| image:: https://img.shields.io/badge/coverage-56%25-blue
   :target: https://pytm.readthedocs.io/en/latest/?badge=latest
   :alt: Documentation Status

Goals
-----

Project time management, billing, and invoice generation.

Preview
-------

 .. image:: https://github.com/wasi0013/PyTM/raw/master/ext/images/demo.gif
    :target: https://github.com/wasi0013/PyTM/raw/master/ext/images/demo.gif
    :alt: PyTM - Preview

Screenshots
-----------

 .. image:: https://github.com/wasi0013/PyTM/raw/master/ext/images/demo.png
    :target: https://github.com/wasi0013/PyTM/
    :alt: PyTM - Screenshot

 .. image:: https://github.com/wasi0013/PyTM/raw/master/ext/images/Demo-Invoice.png
    :target: https://github.com/wasi0013/PyTM/
    :alt: PyTM - Invoice

Installing PyTM
---------------

* First download and install `pyenv <https://github.com/pyenv/pyenv#installation>`_. Use the command::

    curl https://pyenv.run | bash

* Next, install Python 3.12 using the command::

    pyenv install 3.12.0

  Alternatively, you can skip pyenv installation and download python 3.12 or above from the official website and setup a virtualenv as well. 


* Next, install PyTM from `PyPI <https://pypi.org/project/python-pytm/>`_ using :code:`pip`::

    python -m pip install python-pytm

Check the version by typing the following in your terminal.::
    
     pytm --version


Basic commands
---------------

To see the available commands type::

    pytm --help


Commands related to projects
============================
* Start a new project with a default name: :code:`pytm project start`
* Start a new project with the given name or, start an existing project: :code:`pytm project start PROJECT_NAME`
* Rename a project: :code:`pytm project rename OLD_PROJECT_NAME NEW_NAME`
* Archive (soft-delete) a project: :code:`pytm project remove PROJECT_NAME`
* Restore an archived project: :code:`pytm project recover PROJECT_NAME`
* List all archived projects: :code:`pytm project archived`
* Check the status of a project: :code:`pytm project status PROJECT_NAME`
* Check the list of tasks and duration of a project: :code:`pytm project summary PROJECT_NAME`
* Finish active project: :code:`pytm project finish`
* Pause active project: :code:`pytm project pause`
* Abort active project: :code:`pytm project abort`

.. note::
   ``pytm project remove`` performs a **soft delete** — the project is archived to ``~/.pytm/archive.json`` and can be recovered with ``pytm project recover PROJECT_NAME``. No data is permanently lost.

Commands related to Task
========================
* Start a new task with a default name in the current active project: :code:`pytm task start`
* Start a new task with the given name or existing task in the current active project: :code:`pytm task start TASK_NAME`
* Rename a task of the active project: :code:`pytm task rename OLD_TASK_NAME NEW_NAME`
* Remove a task: :code:`pytm task remove PROJECT_NAME TASK_NAME`
* Current task's status: :code:`pytm task status`
* Finish active task: :code:`pytm task finish`
* Pause active task: :code:`pytm task pause`
* Abort active task: :code:`pytm task abort`
* Backfill a completed task with a past date and duration: :code:`pytm task backfill PROJECT_NAME TASK_NAME --date YYYY-MM-DD --hours N`

Backfill options::

    pytm task backfill PROJECT_NAME TASK_NAME \
        --date 2026-01-15 \
        --hours 2.5 \
        --time 09:00 \           # optional, defaults to 00:00
        --description "Notes"    # optional

Invoice commands
================
Configure invoice defaults (title, logo, footnote, starting invoice number)::

    pytm config invoice

Generate an invoice interactively (uses tracked project tasks)::

    pytm invoice auto PROJECT_NAME

Generate an invoice interactively without a tracked project (prompts for tasks manually)::

    pytm invoice auto

Generate a non-interactive multi-project invoice with optional date filtering::

    pytm invoice generate
    pytm invoice generate --projects alpha --projects beta
    pytm invoice generate --from 2026-01-01 --to 2026-03-31
    pytm invoice generate --invoice-number 7 --discount 50 --title "March Invoice"
    pytm invoice generate --list    # show available projects with hours and exit

Track invoice payment status::

    pytm invoice mark-paid INVOICE_NUMBER
    pytm invoice mark-paid INVOICE_NUMBER --date 2026-03-15
    pytm invoice write-off INVOICE_NUMBER
    pytm invoice status    # summary table of all invoices with totals by status

Invoice records are stored in ``~/.pytm/invoices.json``. Generated HTML files are written to ``~/.pytm/invoices/``.

Others
======
Configure project, user and invoice info::

    pytm config project PROJECT_NAME
    pytm config user
    pytm config invoice

Check version::

    pytm --version
    pytm -v

Check summary of all the projects::

    pytm summary

For a list of all the available commands try::

    pytm --help


Running the tests
-----------------

* Clone this `repository <https://github.com/wasi0013/PyTM>`_

* Install dependencies::

    pip install -r requirements.txt

* run the tests::

    py.test


Notes
-----

* **Author** - `Wasi <https://www.wasi0013.com/>`_ - (`wasi0013 <https://github.com/wasi0013>`_).
* **License** - see the `LICENSE <LICENSE>`_ file.
* **Contributing** - see `CONTRIBUTING.rst <CONTRIBUTING.rst>`_ for detail. You can also help by creating `issues <https://github.com/wasi0013/PyTM/issues/new/>`_.
* **Version** - see the `tags on this repository <https://github.com/wasi0013/PyTM/tags>`_.
* **Acknowledgments** - bootstrapped using `this cookiecutter package <https://github.com/audreyr/cookiecutter-pypackage>`_.
* Built With :heart: using `Python <https://python.org/>`_.
