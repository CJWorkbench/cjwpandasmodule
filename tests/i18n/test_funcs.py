from cjwmodule.i18n import I18nMessage
from cjwpandasmodule import i18n


def test_trans_cjwpandasmodule():
    assert i18n._trans_cjwpandasmodule(
        "errors.allNull",
        "The column “{column}” must contain non-null values.",
        {"column": "A"},
    ) == I18nMessage("errors.allNull", {"column": "A"}, "cjwpandasmodule")
