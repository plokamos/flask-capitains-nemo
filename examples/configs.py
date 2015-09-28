from flask.ext.nemo import Nemo
import lxml.etree as etree
from flask import Markup

configs = {
    # The CIHAM project is made of critical editions. We load for it a specific xslt to render the result of GetPassage
    # And specifics assets
   "ciham" : {
        "api_url": "http://services2.perseids.org/exist/restxq/cts",
        "base_url": "",
        "inventory": "nemo",
        "xslt": "examples/ciham.xslt",  # Use default epidoc XSLT
        "css": [
            # USE Own CSS
            "examples/ciham.css"
        ],
        "js": [
            # use own js file to load a script to go from normalized edition to diplomatic one.
            "examples/ciham.js"
        ],
        "chunker": {
            # The default chunker takes care of book, poem, lines
            # but it would be cool to have 30 lines group for Nemo
            "urn:cts:froLit:jns915.jns1856.ciham-fro1": lambda text, cb: [(reff.split(":")[-1], reff.split(":")[-1]) for reff in cb(1)],
            "default": Nemo.scheme_chunker  # lambda text, cb: Nemo.line_grouper(text, cb, 50)
        }
    },
    "translations": {
        "api_url": "http://services2.perseids.org/exist/restxq/cts",
        "base_url": "",
        "inventory": "nemo",
        "urls" : Nemo.ROUTES + [("/read/<collection>/<textgroup>/<work>/<version>/<passage_identifier>/<visavis>", "r_double", ["GET"])],
        "css": [
            "examples/translations.css"
        ],
        "chunker": {
            # The default chunker takes care of book, poem, lines
            # but it would be cool to have 30 lines group for Nemo
            "urn:cts:froLit:jns915.jns1856.ciham-fro1": lambda text, cb: [(reff.split(":")[-1], reff.split(":")[-1]) for reff in cb(1)],
            "default": Nemo.scheme_chunker  # lambda text, cb: Nemo.line_grouper(text, cb, 50)
        },
        "templates": {
            "r_double": "./examples/translations/r_double.html"
        }
    },
    "default": {
        "api_url": "http://services2.perseids.org/exist/restxq/cts",
        "base_url": "",
        "inventory": "nemo",
        "chunker": {
            # The default chunker takes care of book, poem, lines
            # but it would be cool to have 30 lines group for Nemo
            "urn:cts:latinLit:phi1294.phi002.perseus-lat2": lambda text, cb: [(reff.split(":")[-1], reff.split(":")[-1]) for reff in cb(2)],
            "default": Nemo.scheme_chunker  # lambda text, cb: Nemo.line_grouper(text, cb, 50)
        },
        "css" : [
            # Use teibp from default nemo configuration
            "examples/tei.pb.min.css"
        ]
    }
}


class NemoDouble(Nemo):
    """ Implementation of Nemo with a new route accepting a second version for comparison.

    """
    def r_double(self, collection, textgroup, work, version, passage_identifier, visavis):
        """ Optional route to add a visavis version

        :param collection: Collection identifier
        :type collection: str
        :param textgroup: Textgroup Identifier
        :type textgroup: str
        :param work: Work identifier
        :type work: str
        :param version: Version identifier
        :type version: str
        :param passage_identifier: Reference identifier
        :type passage_identifier: str
        :return: Template, version inventory object and Markup object representing the text
        :rtype: {str: Any}

        ..todo:: Change text_passage to keep being lxml and make so self.render turn etree element to Markup.
        """
        text = self.get_passage(collection, textgroup, work, version, passage_identifier)
        second_text = self.get_passage(collection, textgroup, work, visavis, passage_identifier)

        passage = self.xslt(text.xml)
        passage2 = self.xslt(second_text.xml)

        version = self.get_text(collection, textgroup, work, version)
        version2 = self.get_text(collection, textgroup, work, visavis)

        return {
            "template": self.templates["r_double"],
            "version": version,
            "visavis": version2,
            "text_passage": Markup(passage),
            "visavis_passage": Markup(passage2)
        }


classes = {
    "default": Nemo,
    "ciham": Nemo,
    "translations": NemoDouble
}