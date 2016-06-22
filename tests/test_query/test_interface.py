from flask_nemo.query.interface import SimpleQuery
from flask_nemo.query.annotation import AnnotationResource
from flask_nemo.query.resolve import Resolver, LocalRetriever
from flask_nemo import Nemo
from unittest import TestCase
from flask import Flask
from capitains_nautilus.mycapytain import NautilusRetriever
from MyCapytain.common.reference import URN
from werkzeug.exceptions import NotFound


def dict_list(l):
    return [(a.uri, a.target.urn, a.type_uri) for a in l]


class TestSimpleQuery(TestCase):
    """ Test simple query interface """
    def setUp(self):
        self.resolver = Resolver(LocalRetriever(path="./tests/test_data/"))
        self.one = ("urn:cts:latinLit:phi1294.phi002.perseus-lat2:6.1", "interface/treebanks/treebank1.xml", "dc:treebank")
        self.two = ("urn:cts:latinLit:phi1294.phi002.perseus-lat2:1.5", "interface/treebanks/treebank2.xml", "dc:treebank")
        self.three = ("urn:cts:latinLit:phi1294.phi002.perseus-lat2:6.1", "interface/images/N0060308_TIFF_145_145.tif", "dc:image")
        self.unavail = ("urn:cts:greekLit:my0000.my00.perseus-lat2:1.1", "interface/treebanks/treebank1.xml","dc:treebank")
        self.four = AnnotationResource(
            "interface/researchobject/researchobject.json",
            type_uri="dc:researchobject",
            target="urn:cts:latinLit:phi1294.phi002.perseus-lat2:1.pr.1",
            resolver=self.resolver
        )
        self.one_anno = AnnotationResource(
            self.one[1],
            type_uri=self.one[2],
            target=self.one[0],
            resolver=self.resolver
        )
        self.two_anno = AnnotationResource(
            self.two[1],
            type_uri=self.two[2],
            target=self.two[0],
            resolver=self.resolver
        )
        self.three_anno =  AnnotationResource(
            self.three[1],
            type_uri=self.three[2],
            target=self.three[0],
            resolver=self.resolver
        )
        self.unavail_anno =  AnnotationResource(
            self.unavail[1],
            type_uri=self.unavail[2],
            target=self.unavail[0],
            resolver=self.resolver
        )
        self.app = Flask("app")
        self.nautilus = NautilusRetriever(folders=["tests/test_data/interface/latinLit"])
        self.nemo = Nemo(app=self.app, retriever=self.nautilus, base_url="/")
        self.query = SimpleQuery(
            [
                self.one,
                self.two,
                self.three,
                self.four,
                self.unavail,
            ],  # List of annotations
            self.resolver
        )
        self.query.process(self.nemo)

    def test_process(self):
        """ Check that all annotations are taken care of"""
        self.assertEqual(len(self.query.annotations), 5, "There should be 4 annotations")

    def test_get_all(self):
        """ Check that get all returns 3 annotations """
        hits, annotations = self.query.getAnnotations(None)
        self.assertEqual(hits, 5, "There should be 5 annotations")
        self.assertCountEqual(dict_list(annotations), dict_list(
            [
                self.one_anno,
                self.two_anno,
                self.three_anno,
                self.unavail_anno,
                self.four
            ]), "There should be all annotation")

    def test_available_flag(self):
        hits, annotations = self.query.getAnnotations(None)
        self.assertEqual(annotations[0].target.available, True, "Annotation target should be available")
        self.assertEqual(annotations[1].target.available, True, "Annotation target should be available")
        self.assertEqual(annotations[2].target.available, True, "Annotation target should be available")
        self.assertEqual(annotations[3].target.available, False, "Annotation target should not be available")
        self.assertEqual(annotations[4].target.available, True, "Annotation target should be available")

    def test_get_exact_match(self):
        """ Ensure exact match works """
        # Higher level annotation or same match
        hits, annotations = self.query.getAnnotations("urn:cts:latinLit:phi1294.phi002.perseus-lat2:6.1")
        self.assertEqual(hits, 2, "There should be 2 annotations")
        self.assertCountEqual(
            [anno.uri for anno in annotations],
            [
                "interface/images/N0060308_TIFF_145_145.tif",
                "interface/treebanks/treebank1.xml"
            ],
            "Only 2 annotation s having 6.1 should match"
        )

        # Deep Annotations
        hits, annotations = self.query.getAnnotations("urn:cts:latinLit:phi1294.phi002.perseus-lat2:1.pr.1")
        self.assertEqual(annotations[0], self.four, "Deepest node should match as well")

        # It should take URNs as well
        hits, annotations = self.query.getAnnotations(URN("urn:cts:latinLit:phi1294.phi002.perseus-lat2:1.pr.1"))
        self.assertEqual(annotations[0], self.four, "Deepest node should match as well")

    def test_get_range_match(self):
        """ Ensure range match as well """
        # Higher level annotation or same match
        hits, annotations = self.query.getAnnotations("urn:cts:latinLit:phi1294.phi002.perseus-lat2:6.1-6.2")
        self.assertEqual(hits, 2, "There should be 2 annotations")
        self.assertCountEqual(
            [anno.uri for anno in annotations],
            [
                "interface/images/N0060308_TIFF_145_145.tif",
                "interface/treebanks/treebank1.xml"
            ],
            "Only 2 annotation s having 6.1 should match"
        )

        # Deep Annotations
        hits, annotations = self.query.getAnnotations("urn:cts:latinLit:phi1294.phi002.perseus-lat2:1.pr.1-1.pr.3")
        self.assertEqual(annotations[0], self.four, "Deepest node should match as well")

    def test_get_resource(self):
        resource = self.query.getResource("0f9a85344190c3a0376f67764f7e193ffb175c1b59fefb0017c15a5cd8baaa33")
        self.assertEqual(resource, self.four, "Getting one resource should work")

        with self.assertRaises(NotFound, msg="Getting a resource ofr an unknown sha should raise NotFound from werkzeug"):
            self.query.getResource("sasfd")
