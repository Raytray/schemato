class SchemaValidator(object):
    def __init__(self):
        super(SchemaValidator, self).__init__()
        self.schema_def = None
        self.graph = None
        self.parser = None

    def validate(self, source):
        # must create doc_lines here
        self.graph = self.parser.graph_from_source(source)
        errors = []
        for s,p,o in self.graph:
            error = self._check_triple((s,p,o))
            if error and error not in errors:
                errors.append(error)
        return errors

    def _check_triple(self, (subj, pred, obj)):
        """take a triple and compare it to the ontology, return indication
        of whether it's adherent or not"""
        # don't bother with special 'type' triples
        if self._field_name_from_uri(pred) in ['type', 'item', 'first', 'rest']:
            return
        if self._namespace_from_uri(pred) not in self.ns_ont.keys():
            return

        classes = []

        instanceof = self._is_instance((subj, pred, obj)) or self.source

        # this method should differentiate between an "error" and a "warning"
        # since not all issues with an implementation worth telling
        # the user about are actual "errors", just things to keep in mind
        class_invalid = self._validate_class(instanceof)
        if class_invalid:
            return class_invalid

        classes = self._superclasses_for_subject(self.graph, instanceof)
        classes.append(instanceof)

        # is this attribute a valid member of the class or superclasses?
        # in the case of OG, this just means "is it a valid og field"
        member_invalid = self._validate_member(pred, classes, instanceof)
        if member_invalid:
            return member_invalid

        dupe_invalid = self._validate_duplication((subj, pred), instanceof)
        if dupe_invalid:
            return dupe_invalid

        # collect a list of checked attributes
        self.attributes.append((subj,pred))

        return

    def _validate_class(self, cl):
        """return error if class `cl` is not found in the ontology"""
        raise NotImplementedError

    def _validate_member(self, member, classes, instanceof):
        """return error if `member` is not a member of any class in `classes`"""
        valid = False
        # change this
        for ns in self.ns_ont.keys():
            name = "%s%s" % (ns, self.field_name_from_uri(member))
            if rt.URIRef(name) in sum([self.schema_def.attributes_by_class[cl] for cl in classes], []):
                valid = True
                # break
        if not valid:
            return _error("{0} - invalid member of {1}",
                self.field_name_from_uri(member), self.field_name_from_uri(instanceof),
                doc_lines=self.doc_lines)

    def _validate_duplication(self, (subj, pred), cl):
        """returns error if we've already seen the member `pred` on `subj`"""
        # pull over self.attributes
        if (subj,pred) in self.attributes:
            return _error("{0} - duplicated member of {1}", self.field_name_from_uri(pred),
                self.field_name_from_uri(cl), doc_lines=self.doc_lines)

    def _superclasses_for_subject(self, graph, typeof):
        """helper, returns a list of all superclasses of a given class"""
        classes = []
        superclass = typeof
        while True:
            found = False
            for (p, o) in self.schema_def.ontology[superclass]:
                if self.subclass_uri == str(p):
                    found = True
                    classes.append(o)
                    superclass = o
            if not found:
                break
        return classes

    def _is_instance(self, (subj, pred, obj)):
        """helper, returns the class type of subj"""
        for s,p,o in self.graph:
            if s == subj and str(p) == self.schema_def.lexicon['type']:
                return o
        return None

    def _field_name_from_uri(self, uri):
        """helper, returns the name of an attribute (without namespace prefix)"""
        uri = str(uri)
        parts = uri.split('#')
        if len(parts) == 1:
            return uri.split('/')[-1]
        return parts[-1]

    def _namespace_from_uri(self, uri):
        """returns the expanded namespace prefix of a uri"""
        uri = str(uri)
        parts = uri.split('#')
        if len(parts) == 1:
            return "%s/" % '/'.join(uri.split('/')[:-1])
        return "%s#" % '#'.join(parts[:-1])

# what functionality do rdf and microdata validation not share
class RdfValidator(SchemaValidator):
    def __init__(self):
        self.parser = pyRdfa()

    def _validate_class(self, cl):
        if cl not in self.schema_def.attributes_by_class.keys():
            search_string = self._field_name_from_uri(cl)
            return _error("{0} - invalid class", self.field_name_from_uri(cl),
                search_string=search_string, doc_lines=self.doc_lines)

class MicrodataValidator(SchemaValidator):
    def __init__(self):
        self.parser = pyMicrodata()

    def _validate_class(self, cl):
        if cl not in self.schema_def.attributes_by_class.keys():
            search_string = str(cl)
            return _error("{0} - invalid class", self.field_name_from_uri(cl),
                search_string=search_string, doc_lines=self.doc_lines)



