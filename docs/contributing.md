# Contributing

gtfs_skims is an actively maintained and utilised project.

## How to contribute

to report issues, request features, or exchange with our community, just follow the links below.

__Is something not working?__

[:material-bug: Report a bug](https://github.com/arup-group/gtfs_skims/issues/new?template=BUG-REPORT.yml "Report a bug in gtfs_skims by creating an issue and a reproduction"){ .md-button }

__Missing information in our docs?__

[:material-file-document: Report a docs issue](https://github.com/arup-group/gtfs_skims/issues/new?template=DOCS.yml "Report missing information or potential inconsistencies in our documentation"){ .md-button }

__Want to submit an idea?__

[:material-lightbulb-on: Request a change](https://github.com/arup-group/gtfs_skims/issues/new?template=FEATURE-REQUEST.yml "Propose a change or feature request or suggest an improvement"){ .md-button }

__Have a question or need help?__

[:material-chat-question: Ask a question](https://github.com/arup-group/gtfs_skims/discussions "Ask questions on our discussion board and get in touch with our community"){ .md-button }

## Developing gtfs_skims

To find beginner-friendly existing bugs and feature requests you may like to start out with, take a look at our [good first issues](https://github.com/arup-group/gtfs_skims/contribute).

### Setting up a development environment

To create a development environment for gtfs_skims, with all libraries required for development and quality assurance installed, it is easiest to install gtfs_skims using the [mamba](https://mamba.readthedocs.io/en/latest/index.html) package manager, as follows:

1. Install mamba with the [Mambaforge](https://github.com/conda-forge/miniforge#mambaforge) executable for your operating system.
1. Open the command line (or the "miniforge prompt" in Windows).
1. Download (a.k.a., clone) the gtfs_skims repository: `git clone git@github.com:arup-group/gtfs_skims.git`
1. Change into the `gtfs_skims` directory: `cd gtfs_skims`
1. Create the gtfs_skims mamba environment: `mamba create -n gtfs_skims -c conda-forge --file requirements/base.txt --file requirements/dev.txt`
1. Activate the gtfs_skims mamba environment: `mamba activate gtfs_skims`
1. Install the gtfs_skims package into the environment, in editable mode and ignoring dependencies (we have dealt with those when creating the mamba environment): `pip install --no-deps -e .`

All together:

--8<-- "README.md:docs-install-dev"

If installing directly with pip, you can install these libraries using the `dev` option, i.e., `pip install -e '.[dev]'`

If you plan to make changes to the code then please make regular use of the following tools to verify the codebase while you work:

- `pre-commit`: run `pre-commit install` in your command line to load inbuilt checks that will run every time you commit your changes.
The checks are: 1. check no large files have been staged, 2. lint python files for major errors, 3. format python files to conform with the [PEP8 standard](https://peps.python.org/pep-0008/).
You can also run these checks yourself at any time to ensure staged changes are clean by calling `pre-commit`.
- `pytest` - run the unit test suite and check test coverage.

### Rapid-fire testing

The following options allow you to strip down the test suite to the bare essentials:
1. You can avoid generating coverage reports, by adding the `--no-cov` argument: `pytest --no-cov`.
1. By default, the tests run with up to two parallel threads, to increase this to e.g. 4 threads: `pytest -n4`.

All together:

``` shell
pytest tests/ --no-cov -n4
```

!!! note

    You cannot debug failing tests and have your tests run in parallel, you will need to set `-n0` if using the `--pdb` flag

### Memory profiling

!!! note
    When you open a pull request (PR), one of the GitHub actions will run memory profiling for you.
    This means you don't *have* to do any profiling locally.
    However, if you can, it is still good practice to do so as you will catch issues earlier.

gtfs_skims can be memory intensive; we like to ensure that any development to the core code does not exacerbate this.
If you are running on a UNIX device (i.e., **not** on Windows), you can test whether any changes you have made adversely impact memory and time performance as follows:

1. Install [memray](https://bloomberg.github.io/memray/index.html) in your `gtfs_skims` mamba environment: `mamba install memray pytest-memray`.
2. Run the memory profiling integration test: `pytest -p memray -m "high_mem" --no-cov`.
3. Optionally, to visualise the memory allocation, run `pytest -p memray -m "high_mem" --no-cov --memray-bin-path=[my_path] --memray-bin-prefix=[my_prefix]` - where you must define `[my_path]` and `[my_prefix]` - followed by `memray flamegraph [my_path]/[my_prefix]-tests-test_100_memory_profiling.py-test_mem.bin`.
You will then find the HTML report at `[my_path]/memray-flamegraph-[my_prefix]-tests-test_100_memory_profiling.py-test_mem.html`.

All together:

``` shell
mamba install memray pytest-memray
pytest -p memray -m "high_mem" --no-cov --memray-bin-path=[my_path] --memray-bin-prefix=[my_prefix]
memray flamegraph [my_path]/[my_prefix]-tests-test_100_memory_profiling.py-test_mem.bin
```

For more information on using memray, refer to their [documentation](https://bloomberg.github.io/memray/index.html).

## Updating the project when the template updates

This project has been built with [cruft](https://cruft.github.io/cruft/) based on the [Arup Cookiecutter template](https://github.com/arup-group/cookiecutter-pypackage).
When changes are made to the base template, they can be merged into this project by running `cruft update` from the  `gtfs_skims` mamba environment.

You may be prompted to do this when you open a Pull Request, if our automated checks identify that the template is newer than that used in the project.

## Submitting changes

--8<-- "CONTRIBUTING.md:docs"
