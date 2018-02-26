"""Read features and targets from HDF5 files."""

import numpy as np
import tables

from landshark.image import ImageSpec
from landshark.basetypes import ArraySource, OrdinalArraySource, \
    CategoricalArraySource, CoordinateArraySource, FeatureValues, FixedSlice


class H5ArraySource(ArraySource):

    _array_name = ""

    def __init__(self, path) -> None:
        self._path = path
        with tables.open_file(self._path, "r") as hfile:
            carray = hfile.get_node("/" + self._array_name)
            self._shape = carray.shape
            self._missing = carray.attrs.missing
            self._columns = carray.attrs.columns
            self._native = carray.chunkshape[0]
            self._dtype = carray.atom.dtype.base

    def __enter__(self):
        self._hfile = tables.open_file(self._path, "r")
        self._carray = self._hfile.get_node("/" + self._array_name)
        super().__enter__()

    def __exit__(self, *args):
        self._hfile.close()
        del(self._carray)
        del(self._hfile)
        super().__exit__()

    def _arrayslice(self, start: int, end: int) -> np.ndarray:
        return self._carray[start:end]


class OrdinalH5ArraySource(H5ArraySource, OrdinalArraySource):
    _array_name = "ordinal_data"


class CategoricalH5ArraySource(H5ArraySource, CategoricalArraySource):
    _array_name = "categorical_data"

class CoordinateH5ArraySource(H5ArraySource, CoordinateArraySource):
    pass


class H5Features:

    def __init__(self, h5file):
        self._hfile = tables.open_file(h5file, "r")
        self.ordinal = None
        self.categorical = None
        self.coordinates = None

        if hasattr(self._hfile.root, "ordinal_data"):
            self.ordinal = OrdinalH5ArraySource(
                self._hfile.root.ordinal_data)
        if hasattr(self._hfile.root, "categorical_data"):
            self.categorical = CategoricalH5ArraySource(
                self._hfile.root.categorical_data)
        if hasattr(self._hfile.root, "coordinates"):
            self.coordinates = CoordinateH5ArraySource(
                self._hfile.root.coordinates)
        assert not (self.ordinal is None and self.categorical is None)
        if self.ordinal:
            self._n = len(self.ordinal)
        if self.categorical:
            self._n = len(self.categorical)
        if self.ordinal and self.categorical:
            assert len(self.ordinal) == len(self.categorical)
        if self.ordinal and self.coordinates:
            assert len(self.ordinal) == len(self.coordinates)
        if self.categorical and self.coordinates:
            assert len(self.categorical) == len(self.coordinates)

    def __len__(self):
        return self._n

    def __call__(self, s: FixedSlice):
        ord_data = None
        cat_data = None
        coord_data = None
        if self.ordinal:
            ord_data = self.ordinal(s)
        if self.categorical:
            cat_data = self.categorical(s)
        if self.coordinates:
            coord_data = self.coordinates(s)
        return FeatureValues(ord_data, cat_data, coord_data)

    def __del__(self):
        self._hfile.close()


def read_image_spec(filename):
    with tables.open_file(filename, mode="r") as h5file:
        x_coordinates = h5file.root.x_coordinates.read()
        y_coordinates = h5file.root.y_coordinates.read()
        crs = h5file.root._v_attrs.crs
    imspec = ImageSpec(x_coordinates, y_coordinates, crs)
    return imspec
