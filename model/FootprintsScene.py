
# ------------------------------------------------------------------------------
# class FootprintsScene
# ------------------------------------------------------------------------------
class FootprintsScene(object):

    # --------------------------------------------------------------------------
    # __init__
    # --------------------------------------------------------------------------
    def __init__(self, pgRecord=None, sceneGML=None) -> None:

        self._fileName = None
        self._pairName = None
        self._stripName = None

        if pgRecord:

            self._fileName = pgRecord[0]
            self._pairName = pgRecord[1]
            self._stripName = pgRecord[2]

        elif sceneGML:

            self._fileName = self._getValue(sceneGML, 'ogr:s_filepath')
            self._pairName = self._getValue(sceneGML, 'ogr:pairname')
            self._stripName = self._getValue(sceneGML, 'ogr:strip_id')

    # --------------------------------------------------------------------------
    # fileName
    # --------------------------------------------------------------------------
    def fileName(self):
        return self._fileName

    # --------------------------------------------------------------------------
    # getValue
    # --------------------------------------------------------------------------
    def _getValue(self, gml, tagName):

        tag = gml.getElementsByTagName(tagName)

        if tag.length == 0:

            raise RuntimeError('Unable to get the value for the GML tag, ' +
                               tagName +
                               ' because that tag is not in the GML.')

        childNodes = tag[0].childNodes

        return childNodes[0].nodeValue if childNodes.length > 0 else None

    # --------------------------------------------------------------------------
    # __lt__
    # --------------------------------------------------------------------------
    def __lt__(self, other):

        return self.fileName() < other.fileName()

    # --------------------------------------------------------------------------
    # pairName
    # --------------------------------------------------------------------------
    def pairName(self) -> str:
        return self._pairName

    # --------------------------------------------------------------------------
    # stripName
    # --------------------------------------------------------------------------
    def stripName(self) -> str:
        return self._stripName

    # --------------------------------------------------------------------------
    # __repr__
    # --------------------------------------------------------------------------
    def __repr__(self):
        return self.__str__()

    # --------------------------------------------------------------------------
    # __str__
    # --------------------------------------------------------------------------
    def __str__(self):
        return self._fileName
