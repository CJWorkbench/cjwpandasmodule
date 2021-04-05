import numpy as np
import pandas as pd
import pyarrow as pa


def arrow_chunked_array_to_pandas_series(chunked_array: pa.ChunkedArray) -> pd.Series:
    if pa.types.is_date32(chunked_array.type):
        return pd.Series(pd.arrays.PeriodArray(chunked_array.to_numpy(), freq="D"))
    return chunked_array.to_pandas(
        date_as_object=False, deduplicate_objects=True, ignore_metadata=True
    )  # TODO ensure dictionaries stay dictionaries


def _dtype_to_arrow_type(dtype: np.dtype) -> pa.DataType:
    if dtype == np.int8:
        return pa.int8()
    elif dtype == np.int16:
        return pa.int16()
    elif dtype == np.int32:
        return pa.int32()
    elif dtype == np.int64:
        return pa.int64()
    elif dtype == np.uint8:
        return pa.uint8()
    elif dtype == np.uint16:
        return pa.uint16()
    elif dtype == np.uint32:
        return pa.uint32()
    elif dtype == np.uint64:
        return pa.uint64()
    elif dtype == np.float16:
        return pa.float16()
    elif dtype == np.float32:
        return pa.float32()
    elif dtype == np.float64:
        return pa.float64()
    elif dtype.kind == "M":
        # [2019-09-17] Pandas only allows "ns" unit -- as in, datetime64[ns]
        # https://github.com/pandas-dev/pandas/issues/7307#issuecomment-224180563
        assert dtype.str.endswith("[ns]")
        return pa.timestamp(unit="ns", tz=None)
    elif dtype == np.object_:
        return pa.string()
    else:
        raise RuntimeError("Unhandled dtype %r" % dtype)  # pragma: no cover


def arrow_table_to_pandas_dataframe(table: pa.Table) -> pd.DataFrame:
    """Convert an Arrow Table to a Pandas DataFrame."""
    return pd.DataFrame(
        {
            colname: arrow_chunked_array_to_pandas_series(column)
            for colname, column in zip(table.column_names, table.itercolumns())
        },
        index=pd.RangeIndex(0, table.num_rows),
    )


def pandas_series_to_arrow_array(series: pd.Series) -> pa.Array:
    """Convert a Pandas series to an in-memory Arrow array. """
    if hasattr(series, "cat"):
        return pa.DictionaryArray.from_arrays(
            # Pandas categorical value "-1" means None
            pa.Array.from_pandas(series.cat.codes, mask=(series.cat.codes == -1)),
            pandas_series_to_arrow_array(series.cat.categories),
        )
    elif pd.PeriodDtype(freq="D") == series.dtype:
        return pa.array(series.array.asi8, pa.int32(), mask=series.array.isna()).cast(
            pa.date32()
        )
    else:
        arrow_type = _dtype_to_arrow_type(series.dtype)
        return pa.array(series, type=arrow_type)


def pandas_dataframe_to_arrow_table(dataframe: pd.DataFrame) -> pa.Table:
    """Copy a Pandas DataFrame to an Arrow Table.

    This isn't zero-copy. There may be significant RAM costs. (But of course,
    you accepted this cost when you chose Pandas....)

    This assumes the input is valid. Run `validate_dataframe()` prior to calling
    this if you don't know whether the input is valid. Otherwise, you'll get
    undefined behavior.
    """
    return pa.table(
        {
            column: pandas_series_to_arrow_array(dataframe[column])
            for column in dataframe.columns
        }
    )
