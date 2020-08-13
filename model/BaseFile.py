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
