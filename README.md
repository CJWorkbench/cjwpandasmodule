Utilities for [CJWorkbench](https://github.com/CJWorkbench/cjworkbench) modules
that use Pandas.

Workbench modules may _optionally_ depend on the latest version of this Python
package for its handy utilities:

* `cjwpandasmodule.validate`: functions to check if a DataFrame can be saved
  in Workbench.

Developing
==========

0. Run `tox` to confirm that unit tests pass
1. Write a failing unit test in `tests/`
2. Make it pass by editing code in `cjwpandasmodule/`
3. Submit a pull request

We use [semver](https://semver.org/). Workbench will upgrade this dependency
(minor version only) without module authors' explicit consent. Features in the
same major version must be backwards-compatible.


Publishing
==========

1. ``git push`` and make sure Travis tests all pass.
2. ``git tag vX.X.X``
3. ``git push --tags``

TravisCI will push to PyPi.
