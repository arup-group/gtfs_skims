
# Installation

Note: this library only supports Unix-based systems (ie Ubuntu/macOS). If you wish to use it on Windows please use the Windows Subsystem for Linux.

## Setting up a user environment

As a `gtfs_skims` user, it is easiest to install using the [mamba](https://mamba.readthedocs.io/en/latest/index.html) package manager, as follows:

1. Install mamba with the [Mambaforge](https://github.com/conda-forge/miniforge#mambaforge) executable for your operating system.
1. Open the command line (or the "miniforge prompt" in Windows).
1. Download (a.k.a., clone) the gtfs_skims repository: `git clone git@github.com:arup-group/gtfs_skims.git`
1. Change into the `gtfs_skims` directory: `cd gtfs_skims`
1. Create the gtfs_skims mamba environment: `mamba create -n gtfs_skims -c conda-forge -c city-modelling-lab --file requirements/base.txt`
1. Activate the gtfs_skims mamba environment: `mamba activate gtfs_skims`
1. Install the gtfs_skims package into the environment, ignoring dependencies (we have dealt with those when creating the mamba environment): `pip install --no-deps .`

All together:

--8<-- "README.md:docs-install-user"

## Setting up a development environment

The install instructions are slightly different to create a development environment compared to a user environment:

--8<-- "README.md:docs-install-dev"

For more detailed installation instructions specific to developing the gtfs_skims codebase, see our [development documentation][setting-up-a-development-environment].
