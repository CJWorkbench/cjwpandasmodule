from datetime import date

import numpy as np
import pandas as pd
import pytest

from cjwpandasmodule.validate import validate_dataframe


def test_index():
    with pytest.raises(ValueError, match="must use the default RangeIndex"):
        validate_dataframe(pd.DataFrame({"A": [1, 2]})[1:])


def test_non_str_objects():
    with pytest.raises(ValueError, match="must all be str"):
        validate_dataframe(pd.DataFrame({"foo": ["a", 1]}))


def test_empty_categories_with_wrong_dtype():
    with pytest.raises(ValueError, match="must have dtype=object"):
        validate_dataframe(
            pd.DataFrame({"foo": [np.nan]}, dtype=float).astype("category")
        )


def test_non_str_categories():
    with pytest.raises(ValueError, match="must all be str"):
        validate_dataframe(pd.DataFrame({"foo": ["a", 1]}, dtype="category"))


def test_unused_categories():
    with pytest.raises(ValueError, match="unused category 'b'"):
        validate_dataframe(
            pd.DataFrame({"foo": ["a", "a"]}, dtype=pd.CategoricalDtype(["a", "b"]))
        )


def test_null_is_not_a_category():
    # pd.CategoricalDtype means storing nulls as -1. Don't consider -1 when
    # counting the used categories.
    with pytest.raises(ValueError, match="unused category 'b'"):
        validate_dataframe(
            pd.DataFrame({"foo": ["a", None]}, dtype=pd.CategoricalDtype(["a", "b"]))
        )


def test_empty_categories():
    df = pd.DataFrame({"A": []}, dtype="category")
    validate_dataframe(df)


def test_unique_colnames():
    dataframe = pd.DataFrame({"A": [1], "B": [2]})
    dataframe.columns = ["A", "A"]
    with pytest.raises(ValueError, match="must not appear more than once"):
        validate_dataframe(dataframe)


def test_empty_colname():
    dataframe = pd.DataFrame({"": [1], "B": [2]})
    with pytest.raises(ValueError, match="must not be empty"):
        validate_dataframe(dataframe)


def test_numpy_dtype():
    # Numpy dtypes should be treated just like pandas dtypes.
    dataframe = pd.DataFrame({"A": np.array([1, 2, 3])})
    validate_dataframe(dataframe)


def test_period_dtype():
    dataframe = pd.DataFrame(
        {
            "A": pd.PeriodIndex(
                [date(2020, 1, 1), date(2021, 3, 9), None],
                freq="D",
            )
        }
    )
    validate_dataframe(dataframe)


def test_period_dtype_freq_not_D():
    dataframe = pd.DataFrame(
        {
            "A": pd.PeriodIndex(
                [date(2020, 1, 1), date(2021, 3, 1), None],
                freq="M",
            )
        }
    )
    with pytest.raises(
        ValueError, match=r"unsupported dtype period\[M\] in column 'A'"
    ):
        validate_dataframe(dataframe)


def test_unsupported_dtype():
    dataframe = pd.DataFrame(
        {
            # A type we never plan on supporting
            "A": pd.Series([pd.Interval(0, 1)], dtype="interval")
        }
    )
    with pytest.raises(ValueError, match="unsupported dtype"):
        validate_dataframe(dataframe)


def test_datetime64():
    dataframe = pd.DataFrame(
        {
            # We don't support datetimes with time zone data ... yet
            "A": pd.Series([pd.to_datetime("2019-04-23T12:34:00")])
        }
    )
    validate_dataframe(dataframe)


def test_datetime64tz_unsupported():
    dataframe = pd.DataFrame(
        {
            # We don't support datetimes with time zone data ... yet
            "A": pd.Series([pd.to_datetime("2019-04-23T12:34:00-0500")])
        }
    )
    with pytest.raises(ValueError, match="unsupported dtype"):
        validate_dataframe(dataframe)


def test_nullable_int_unsupported():
    dataframe = pd.DataFrame(
        {
            # We don't support nullable integer columns ... yet
            "A": pd.Series([1, np.nan], dtype=pd.Int64Dtype())
        }
    )
    with pytest.raises(ValueError, match="unsupported dtype"):
        validate_dataframe(dataframe)


def test_infinity_not_supported():
    # Make 'A': [1, -inf, +inf, nan]
    num = pd.Series([1, -2, 3, np.nan])
    denom = pd.Series([1, 0, 0, 1])
    dataframe = pd.DataFrame({"A": num / denom})
    with pytest.raises(
        ValueError,
        match=r"invalid value -inf in column 'A', row 1 \(infinity is not supported\)",
    ):
        validate_dataframe(dataframe)


def test_unsupported_numpy_dtype_unsupported():
    # We can't check if a numpy dtype == 'category'.
    # https://github.com/pandas-dev/pandas/issues/16697
    arr = np.array([1, 2, 3]).astype("complex")  # we don't support complex
    dataframe = pd.DataFrame({"A": arr})
    with pytest.raises(ValueError, match="unsupported dtype"):
        validate_dataframe(dataframe)


def test_colnames_dtype_object():
    with pytest.raises(ValueError, match="column names"):
        # df.columns is numeric
        validate_dataframe(pd.DataFrame({1: [1]}))


def test_colnames_all_str():
    with pytest.raises(ValueError, match="column names"):
        # df.columns is object, but not all are str
        validate_dataframe(pd.DataFrame({"A": [1], 2: [2]}))


def test_colnames_control_chars():
    with pytest.raises(ValueError, match="ASCII control characters"):
        validate_dataframe(pd.DataFrame({"A\x01": [1]}))


def test_colnames_invalid_unicode():
    with pytest.raises(ValueError, match="Unicode surrogates"):
        validate_dataframe(pd.DataFrame({"A \ud800 B": [1]}))


def test_colnames_too_long():
    class MySettings:
        MAX_BYTES_PER_COLUMN_NAME: int = 10

    with pytest.raises(ValueError, match="must contain 10 bytes or fewer"):
        validate_dataframe(pd.DataFrame({"01234567890": [1]}), settings=MySettings())
