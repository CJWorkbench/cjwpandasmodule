Utilities for [CJWorkbench](https://github.com/CJWorkbench/cjworkbench) modules.

Workbench modules may _optionally_ depend on the latest version of this Python
package for its handy utilities.

**None of these APIs are stable.** Please open a GitHub issue if you wish to
use one of these APIs.

Developing
==========

1. Write a failing unit test in `tests/`
2. Make it pass by editing code in `cjwmodule/`
3. `black cjwmodule tests && isort --recursive cjwmodule tests`
4. Submit a pull request

API stability: these APIs are all in use, even though they are unstable. Be
extremely careful about changing behavior: all modules that rely on the old
behavior will be changed silently.

I18n
====

### Marking strings for translation

Strings in `cjwpandasmodule` can be marked for translation using
`cjwpandasmodule.i18n._trans_cjwpandasmodule`. Each translation message must
have a (unique) ID. ICU is supported for the content.

For example:

```python
from .i18n import _trans_cjwpandasmodule

err = "Error 404"

with_arguments = _trans_cjwpandasmodule(
    "greatapi.exception.message",
    "Something is wrong: {error}",
    {"error": err}
)

without_arguments = _trans_cjwpandasmodule(
    "greatapi.exception.general",
    "Something is wrong",
)
```

Workbench is wired to accept the return value of `_trans_cjwpandasmodule`
wherever an error/warning or quick fix is expected.

### Creating `po` catalogs

Calls to `_trans_cjwpandasmodule` can (and must) be parsed to create
`cjwpandasmodule`'s `.po` files. Update the `.po` files with:

```
./setup.py extract_messages
```

The first time you run this, you'll need to install dependencies:
`pip3 install .[maintenance]`

### Unit testing

In case a `_trans_cjwpandasmodule` invocation needs to be unit tested, use
`cjwpandasmodule.testing.i18n.cjwpandasmodule_i18n_message` like this:

```python
from cjwpandasmodule.testing.i18n import cjwpandasmodule_i18n_message

assert with_arguments == cjwpandasmodule_i18n_message("greatapi.exception.message", {"error": "Error 404"})
assert without_arguments == cjwpandasmodule_i18n_message("greatapi.exception.general")
```

### Message deprecation

Never delete a `trans()` call: each message ID, once assigned, must be preserved
forever.

When there is no more code path to a `trans()` call, move it to
`cjwpandasmodule/i18n/_deprecated_i18n_messages.py`. The file is only read by
extraction code. It is never executed.


Publishing
==========

1. Write a new `__version__` to `cjwpandasmodule/__init__.py`. Adhere to
   [semver](https://semver.org). (As changes must be backwards-compatible,
   the version will always start with `1` and look like `1.x.y`.)
2. Prepend notes to `CHANGELOG.md` about the new version
3. `git commit`
4. `git tag v1.x.y`
5. `git push --tags && git push`
6. Wait for Travis to push our changes to PyPI
