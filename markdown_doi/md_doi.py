# Copyright 2016 Ben Caller
import gzip
import json

import requests
from markdown import Extension
from markdown.util import etree
from markdown.inlinepatterns import LinkPattern

RE_DOI = r'''(?x)(?i)
(?<![/-_@\w])                                   # Nothing bad before the doi
doi:
(
    10\.
    \d{4,9}/                                    # Prefix
    [-._;()/:A-Z0-9]+                           # Suffix
    \b(?![\d\-_@])                              # Don't allow last char to be followed by these
)
'''
API_URL = 'https://api.crossref.org/works/{doi}'


class DoiPattern(LinkPattern):
    """Convert doi links to clickable links."""

    def __init__(self, md, templater, cache_file=None, cache=None):
        """

        :param Callable[[Dict, LinkPattern], etree.ElementTree] templater: function which processes the metadata
        """
        self._templater = templater
        self._cache_file = cache_file
        self._cache = cache
        super(LinkPattern, self).__init__(RE_DOI, md)

    def _cached_get_json(self, doi):
        if self._cache_file is not None or self._cache is not None:
            # Lazy load cache once for all matches
            if self._cache is None:
                try:
                    with gzip.open(self._cache_file, 'rt') as gz_json_file:
                        self._cache = json.load(gz_json_file)
                except (FileNotFoundError, ValueError, OSError):
                    self._cache = dict()

            # Check cache
            if doi in self._cache:
                return self._cache[doi]

            # Cache miss
            value = DoiPattern._make_request(doi)
            # New value for cache
            self._cache[doi] = value
            if self._cache_file:
                with gzip.open(self._cache_file, 'wt') as gz_json_file:
                    json.dump(self._cache, gz_json_file)
            return value
        return DoiPattern._make_request(doi)

    @staticmethod
    def _make_request(doi):
        # print("Making request for", doi)
        r = requests.get(API_URL.format(doi=doi))
        r.raise_for_status()
        req_json = r.json()
        if not req_json["status"] == "ok":
            raise Exception("DOI API was not OK!")
        return req_json["message"]

    def handleMatch(self, m):
        """Handle DOI matches."""

        doi = m.group(2)
        metadata = self._cached_get_json(doi)
        return self._templater(metadata, self)


def template_title_link_year(metadata, doi_pattern):
    """
    Take the metadata and output a link to the article with the article title as the text, followed by the year
    :param dict metadata: Metadata about the target of the DOI
    :param DoiPattern doi_pattern: The DoiPattern instance which has matched this DOI
    :rtype: etree.ElementTree
    """
    el = etree.Element("span")
    el.attrib = {"class": 'doi'}

    link = etree.SubElement(el, "a")
    link.text = metadata["title"][0]
    link.set("href", doi_pattern.sanitize_url(metadata["URL"]))
    link.tail = " "

    year = etree.SubElement(el, "span")
    year.text = '({})'.format(metadata["created"]["date-parts"][0][0])
    year.attrib = {"class": "doi-year"}

    return el


class DoiExtension(Extension):
    """Add doi extension to Markdown class."""

    def __init__(self, *args, **kwargs):
        """Initialize."""

        self.config = {
            'templater': [template_title_link_year, "Method converting JSON Dict to markdown.util.etree.ElementTree"],
            'cache_file': ['', "Filename for storing cache of map from doi to metadata"],
            'cache': [{}, "Actual map of doi to dict instead of loading from a file"]
        }

        super(DoiExtension, self).__init__(*args, **kwargs)

        if len(self.getConfig('cache_file')) == 0:
            self.setConfig('cache_file', None)
        if len(self.getConfig('cache')) == 0:
            self.setConfig('cache', None)


    def extendMarkdown(self, md, md_globals):
        """Add support for turning html links and emails to link tags."""

        link_pattern = DoiPattern(md, **self.getConfigs())
        md.inlinePatterns.add("doi-link", link_pattern, "<not_strong")


def makeExtension(*args, **kwargs):
    """Return extension."""

    return DoiExtension(*args, **kwargs)
