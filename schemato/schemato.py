import urllib
import re

from schemas.rnews import RNewsValidator
from schemas.opengraph import OpenGraphValidator
from schemas.schemaorg import SchemaOrgValidator
from compound_graph import CompoundGraph

class Schemato(object):
    def __init__(self, source):
        super(Schemato, self).__init__()
        text, url, doc_lines = self._read_stream(source)
        self.url = url
        self.graph = CompoundGraph(url)
        self.doc_lines = doc_lines
        self.validators = []
        self.validators.append(RNewsValidator(self.graph, self.doc_lines))
        self.validators.append(OpenGraphValidator(self.graph, self.doc_lines, self.url))
        self.validators.append(SchemaOrgValidator(self.graph, self.doc_lines))

    def validate(self):
        for v in self.validators:
            if v.graph:
                print v.validate()

    def _document_lines(self, text):
        """helper, get a list of (linetext, linenum) from a string with newlines"""
        doc_lines, num = [], 0
        for line in text.split('\n'):
            num += 1
            line = re.sub(r'^ +| +$', '', line)
            line = line.replace("<", "&lt;").replace(">", "&gt;")
            doc_lines.append((line, num))
        return doc_lines

    def _get_document(self, url):
        """helper, open a file or url and return the doctype and content separately"""
        try:
            if "http://" not in url:
                scheme_url = "http://%s" % url
            else:
                scheme_url = url
            try:
                text = urllib.urlopen(scheme_url).read()
                url = scheme_url
            except:
                text = open(url, "r").read()
        except:
            raise IOError('Failed to read stream from %s' % url)

        return (text, url)

    def _read_stream(self, url):
        text, url = self._get_document(url)
        return text, url, self._document_lines(text)