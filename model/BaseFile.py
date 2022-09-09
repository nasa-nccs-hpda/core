# -*- coding: utf-8 -*-

import os


# -----------------------------------------------------------------------------
# class BaseFile
# -----------------------------------------------------------------------------
class BaseFile(object):

    # -------------------------------------------------------------------------
    # __init__
    # -------------------------------------------------------------------------
    def __init__(self, pathToFile):

        if not pathToFile:
            raise RuntimeError('A fully-qualified path to a file must be \
                               specified.')

        if not os.path.exists(pathToFile):
            raise RuntimeError(str(pathToFile) + ' does not exist.')

        self._filePath = pathToFile

    # -------------------------------------------------------------------------
    # fileName
    # -------------------------------------------------------------------------
    def fileName(self):
        return self._filePath

    # -------------------------------------------------------------------------
    # __str__
    # -------------------------------------------------------------------------
    def __str__(self):
        return self.fileName()

    # -------------------------------------------------------------------------
    # __eq__
    #
    # Without this implementation, '==' returns true when two variables point
    # to the same instance of BaseFile in memory.  This implementation compares
    # file paths.
    # -------------------------------------------------------------------------
    def __eq__(self, other) -> bool:

        return isinstance(other, BaseFile) and \
               self._filePath == other._filePath

    # -------------------------------------------------------------------------
    # __lt__
    # -------------------------------------------------------------------------
    def __lt__(self, other) -> bool:

        return self._filePath < other._filePath

    # -------------------------------------------------------------------------
    # __hash__
    # -------------------------------------------------------------------------
    def __hash__(self) -> int:

        return hash(self._filePath)
