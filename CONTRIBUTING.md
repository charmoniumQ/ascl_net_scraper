# How to setup the development environment

This project manages dependencies through [Poetry][poetry] or through [Nix][nix]. These are package managers that create a "project-local" development environment with minimal system-wide changes.

- Poetry is a wrapper around virtualenv/pip, so it can only manage packages in PyPI. Use it like so:

    ```
    # install Python
    # Version should match that in `pyproject.toml` > `tool.poetry.dependencies` > `python`

    $ python -m pip --user install poetry
    # This is the only "system-wide" command.

    $ poetry install
    # This creates a virtualenv and installs the dev dependencies.

    $ poetry run ipython
    # This runs just one command, "ipython" in this case, in the project environment.

    $ poetry shell
    # This gives you a shell in the project environment.
    ```

- Nix is a language-agnostic UNIX-agnostic package manager that can create project-local environments. Nix uses Poetry's config file thanks to [poetry2nix][poetry2nix], but it can install binary dependencies that are not in PyPI. However, not all Python packages work in Nix (see [poetry2nix issue #413][issue-413]). Use it like so:

    ```
    # Install nix
    # This is the only "system-wide" command.

    $ nix develop --command ipython
    # This runs just one command in the project environment.

    $ nix develop --command zsh
    # This runs a shell in the project environment.
    ```

[poetry]: https://python-poetry.org/
[nix]: https://nixos.org/
[poetry2nix]: https://github.com/nix-community/poetry2nix
[issue-413]: https://github.com/nix-community/poetry2nix/issues/413

# How to use development tools

Once in the development environment, use `./script.py` to run black, isort, mypy, etc.

- `./script.py fmt` runs code formatters (autoimport, isort, black).

- `./script.py test` runs tests and code complexity analysis (mypy, pylint, pytest, coverage, radon in parallel).

- `./script.py all-tests` runs the usual tests and more (proselint, rstcheck, twine, pytest, tox). It runs them in multiple Python versions. This is mostly for CI.

- `./script.py docs` builds the documentation locally (sphinx, proselint).

- `./script.py publish` publishes the package to PyPI and deploys the documentation to GitHub pages (`./scripts.py all-tests`, bump2version, poetry publish, git push).
