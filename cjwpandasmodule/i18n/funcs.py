from typing import Any, Dict

from cjwmodule.i18n import I18nMessage


def _trans_cjwpandasmodule(
    id: str, default: str, args: Dict[str, Any] = {}
) -> I18nMessage:
    """
    Build an I18nMessage for use in `cjwpandasmodule`.

    Use ``_trans_cjwpandasmodule()`` rather than building a
    :py:class:`I18nMessage` directly. Workbench's i18n tooling parses
    ``_trans_cjwpandasmodule()`` calls to maintain translation files of
    `cjwpandasmodule`.

    Example usage::

        from cjwpandasmodule.i18n import _trans_cjwpandasmodule

        except ApiException as err:  # some 
            return _trans_cjwpandasmodule(
                "greatapi.exception.message",
                "Something is wrong: {error}",
                {"error": str(err)}
            )

    :param id: Message ID unique to this module (e.g., ``"errors.allNull"``)
    :param default: English-language message, in ICU format. (e.g.,
                    ``"The column “{column}” must contain non-null values.")``
    :param args: Values to interpolate into the message. (e.g.,
                 ``{"column": "A"}```
    """
    return I18nMessage(id, args, "cjwpandasmodule")
