"""Exceptions and errors from CLI and internal processing."""

import logging
import sys
from typing import Any, Callable, List, Tuple

import numpy as np

log = logging.getLogger(__name__)


class Error(Exception):
    """Base class for exceptions in Landshark."""

    message = "Landshark error."


def catch_and_exit(f: Callable) -> Callable:
    """Decorate function to exit program if it throws an Error."""
    def wrapped(*args: Any, **kwargs: Any) -> None:
        try:
            f(*args, **kwargs)
        except Error as e:
            log.error(e.message)
            sys.exit()

    return wrapped


class NoTifFilesFound(Error):
    """Couldn't find TIF files."""

    message = "The supplied paths had no files with .tif or .gtif extensions"


class ZeroDeviation(Error):
    """Zero standard deviation in supplied column."""

    def __init__(self, sd: np.ndarray, cols: List[str]) -> None:
        zsrcs = [c for z, c in zip(sd, cols) if z]
        self.message = "The following sources have bands \
            with zero standard deviation: {}".format(zsrcs)


class ConCatNMismatch(Error):
    """N doesnt match between the con and cat sources."""

    def __init__(self, N_con: int, N_cat: int) -> None:
        """Construct the object."""
        self.message = "Continuous and Categorical source mismatch with \
            {} and {} points respectively".format(N_con, N_cat)


class PredictionShape(Error):
    """Prediction output is not 1D or 2D."""

    def __init__(self, name: str, shape: Tuple[int]) -> None:
        """Construct the object."""
        self.message = "Prediction shape for {} is shaped {}. Predictions \
            must be 1D.".format(name, shape)
