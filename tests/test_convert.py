import datetime

import numpy as np
import pandas as pd
import pyarrow as pa
import pytest
from pandas.testing import assert_frame_equal, assert_series_equal

from cjwpandasmodule.convert import (
    arrow_chunked_array_to_pandas_series,
    arrow_table_to_pandas_dataframe,
    pandas_dataframe_to_arrow_table,
    pandas_series_to_arrow_array,
)

IntSeriesAndArrayParams = [
    pytest.param(
        pd.Series([1, 2], dtype=np.uint8), pa.array([1, 2], pa.uint8()), id="uint8"
    ),
    pytest.param(
        pd.Series([1, -2], dtype=np.int8), pa.array([1, -2], pa.int8()), id="int8"
    ),
    pytest.param(
        pd.Series([1, 2], dtype=np.uint16),
        pa.array([1, 2], pa.uint16()),
        id="uint16",
    ),
    pytest.param(
        pd.Series([1, -2], dtype=np.int16),
        pa.array([1, -2], pa.int16()),
        id="int16",
    ),
    pytest.param(
        pd.Series([1, 2], dtype=np.uint32),
        pa.array([1, 2], pa.uint32()),
        id="uint32",
    ),
    pytest.param(
        pd.Series([1, -2], dtype=np.int32),
        pa.array([1, -2], pa.int32()),
        id="int32",
    ),
    pytest.param(
        pd.Series([1, 2], dtype=np.uint64),
        pa.array([1, 2], pa.uint64()),
        id="uint64",
    ),
    pytest.param(
        pd.Series([1, -2], dtype=np.int64),
        pa.array([1, -2], pa.int64()),
        id="int64",
    ),
    pytest.param(
        pd.Series([1, -2, None], dtype=np.float16),
        pa.array([np.float16(1), np.float16(-2), None], pa.float16()),
        id="float16",
    ),
    pytest.param(
        pd.Series([1, -2, None], dtype=np.float32),
        pa.array([1, -2, None], pa.float32()),
        id="float32",
    ),
    pytest.param(
        pd.Series([1, -2, None], dtype=np.float64),
        pa.array([1, -2, None], pa.float64()),
        id="float64",
    ),
]


@pytest.mark.parametrize("series,expected_array", IntSeriesAndArrayParams)
def test_series_to_array_numeric(series, expected_array):
    assert pandas_series_to_arrow_array(series).equals(expected_array)


def test_series_to_array_timestamp():
    series = pd.Series(["2021-04-05T17:31:12.456", None], dtype="datetime64[ns]")
    expected_array = pa.array(
        [datetime.datetime(2021, 4, 5, 17, 31, 12, 456000, tzinfo=None), None],
        pa.timestamp(unit="ns"),
    )
    result = pandas_series_to_arrow_array(series)
    assert result == expected_array


def test_series_to_array_date():
    series = pd.Series(["2021-04-05", None], dtype="period[D]")
    expected_array = pa.array([datetime.date(2021, 4, 5), None])
    result = pandas_series_to_arrow_array(series)
    assert result == expected_array


def test_series_to_array_str():
    series = pd.Series(["a", "b", "c\0d", None])
    expected_array = pa.array(["a", "b", "c\0d", None])
    result = pandas_series_to_arrow_array(series)
    assert result == expected_array


def test_series_to_array_categorical_int8():
    series = pd.Series(["a", "b", "c\0d", "a", None], dtype="category")
    expected_array = pa.DictionaryArray.from_arrays(
        pa.array([0, 1, 2, 0, None], pa.int8()), pa.array(["a", "b", "c\0d"])
    )
    result = pandas_series_to_arrow_array(series)
    assert result == expected_array


def test_series_to_array_categorical_int32():
    series = pd.Series([chr(i) for i in range(35536)], dtype="category")
    expected_array = pa.DictionaryArray.from_arrays(
        pa.array(list(range(35536)), pa.int32()), pa.array(chr(i) for i in range(35536))
    )
    result = pandas_series_to_arrow_array(series)
    assert result == expected_array


def test_dataframe_to_table():
    dataframe = pd.DataFrame({"A": ["a", "b"], "B": [1, None]})
    expected_table = pa.table({"A": ["a", "b"], "B": [1.0, None]})
    result = pandas_dataframe_to_arrow_table(dataframe)
    assert result == expected_table


@pytest.mark.parametrize("expected_series,array", IntSeriesAndArrayParams)
def test_chunked_array_to_series_numeric(expected_series, array):
    chunked_array = pa.chunked_array([array])
    result = arrow_chunked_array_to_pandas_series(chunked_array)
    assert_series_equal(result, expected_series)


def test_chunked_array_to_series_int_null_becomes_float64():
    chunked_array = pa.chunked_array([pa.array([1, 2, None])])
    expected_series = pd.Series([1.0, 2.0, None])
    result = arrow_chunked_array_to_pandas_series(chunked_array)
    assert_series_equal(result, expected_series)


def test_chunked_array_to_series_timestamp():
    chunked_array = pa.chunked_array(
        [
            pa.array(
                [datetime.datetime(2021, 4, 5, 17, 31, 12, 456000, tzinfo=None), None],
                pa.timestamp(unit="ns"),
            )
        ]
    )
    expected_series = pd.Series(
        ["2021-04-05T17:31:12.456", None], dtype="datetime64[ns]"
    )
    result = arrow_chunked_array_to_pandas_series(chunked_array)
    assert_series_equal(result, expected_series)


def test_chunked_array_to_series_date():
    chunked_array = pa.chunked_array([pa.array([datetime.date(2021, 4, 5), None])])
    expected_series = pd.Series(["2021-04-05", None], dtype="period[D]")
    result = arrow_chunked_array_to_pandas_series(chunked_array)
    assert_series_equal(result, expected_series)


def test_chunked_array_to_series_str():
    chunked_array = pa.chunked_array([pa.array(["a", "b", "c\0d", None])])
    expected_series = pd.Series(["a", "b", "c\0d", None])
    result = arrow_chunked_array_to_pandas_series(chunked_array)
    assert_series_equal(result, expected_series)


def test_chunked_array_to_series_categorical_int8():
    chunked_array = pa.chunked_array(
        [
            pa.DictionaryArray.from_arrays(
                pa.array([0, 1, 2, 0, None], pa.int8()), pa.array(["a", "b", "c\0d"])
            )
        ]
    )
    expected_series = pd.Series(["a", "b", "c\0d", "a", None], dtype="category")
    result = arrow_chunked_array_to_pandas_series(chunked_array)
    assert_series_equal(result, expected_series)


def test_chunked_array_to_series_categorical_int32():
    chunked_array = pa.chunked_array(
        [
            pa.DictionaryArray.from_arrays(
                pa.array(list(range(35536)), pa.int32()),
                pa.array(chr(i) for i in range(35536)),
            )
        ]
    )
    expected_series = pd.Series([chr(i) for i in range(35536)], dtype="category")
    result = arrow_chunked_array_to_pandas_series(chunked_array)
    assert_series_equal(result, expected_series)


def test_table_to_dataframe():
    table = pa.table(
        {
            "A": ["a", "b"],
            "B": pa.array([1, 2], pa.int32()),
        }
    )
    expected_dataframe = pd.DataFrame(
        {"A": ["a", "b"], "B": pd.Series([1, 2], dtype=np.int32)}
    )
    result = arrow_table_to_pandas_dataframe(table)
    assert_frame_equal(result, expected_dataframe)
