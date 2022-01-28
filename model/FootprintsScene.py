
# ------------------------------------------------------------------------------
# class FootprintsScene
# ------------------------------------------------------------------------------
class FootprintsScene(object):

    # --------------------------------------------------------------------------
    # __init__
    # --------------------------------------------------------------------------
    def __init__(self, sceneGML):

        self.gml = sceneGML

    # --------------------------------------------------------------------------
    # fileName
    # --------------------------------------------------------------------------
    def fileName(self):
        return self._getValue('ogr:s_filepath')

    # --------------------------------------------------------------------------
    # getValue
    # --------------------------------------------------------------------------
    def _getValue(self, tagName):

        # return self.gml.getElementsByTagName(tagName)[0].childNodes[0]. \
        #        nodeValue

        tag = self.gml.getElementsByTagName(tagName)

        if tag.length == 0:

            raise RuntimeError('Unable to get the value for the GML tag, ' +
                               tagName +
                               ' because that tag is not in the GML.')

        valueNode = tag[0].childNodes[0]

        return valueNode.nodeValue if valueNode else None

    # --------------------------------------------------------------------------
    # pairName
    # --------------------------------------------------------------------------
    def pairName(self):
        return self._getValue('ogr:pairname')

    # --------------------------------------------------------------------------
    # stripName
    # --------------------------------------------------------------------------
    def stripName(self):
        return self._getValue('ogr:strip_id')

    # --------------------------------------------------------------------------
    # __repr__
    # --------------------------------------------------------------------------
    def __repr__(self):
        return self.__str__()

    # --------------------------------------------------------------------------
    # __str__
    # --------------------------------------------------------------------------
    def __str__(self):
        return self.fileName()
