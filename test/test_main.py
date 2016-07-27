# Copyright (c) 2016 Ben Caller
from sys import version_info

import markdown
import pytest
from requests.exceptions import HTTPError
import vcr

from markdown_doi.md_doi import makeExtension as makeDoiExtension

if version_info.major == 2:
    import __builtin__ as builtins  # pylint:disable=import-error
else:
    import builtins  # pylint:disable=import-error

GOOD_ARTICLE_DOI = '10.1016/j.applanim.2010.02.004'


@pytest.fixture
def md():
    return markdown.Markdown(extensions=['markdown_doi'])


@pytest.fixture(params=['hello', 'doi:10.101/j.appl', '10.1016/j.appl', 'doi:10X1016/j.appl',
                        'doi:10/1234.32470j', GOOD_ARTICLE_DOI + '!X', 'a' + GOOD_ARTICLE_DOI])
def bad_doi(request):
    return request.param


def surround(s):
    return '<p>{}</p>'.format(s)


def doify(s):
    return 'doi:' + s


# Tests


@vcr.use_cassette('test/cassettes/api_success.yml')
def test_good_article(md):
    text = doify(GOOD_ARTICLE_DOI)
    html = md.convert(text)

    assert html == surround('<span class="doi">'
                            '<a href="http://dx.doi.org/10.1016/j.applanim.2010.02.004">'
                            'Are cows more likely to lie down the longer they stand?'
                            '</a> <span class="doi-year">(2010)</span>'
                            '</span>')


@vcr.use_cassette('test/cassettes/api_fail.yml')
def test_non_existent(md):
    text = doify('10.1016/j.appXXXlanim.20XXXXX10.02.004')
    with pytest.raises(HTTPError):
        md.convert(text)


@vcr.use_cassette('test/cassettes/api_malformed.yml')
def test_bad_json(md):
    text = doify(GOOD_ARTICLE_DOI)
    with pytest.raises(ValueError):
        md.convert(text)


@vcr.use_cassette('test/cassettes/nothing.yml')
def test_bad_doi(md, bad_doi):
    html = md.convert(bad_doi)
    assert html == surround(bad_doi)


@vcr.use_cassette('test/cassettes/nothing.yml')
def test_cache_hit():
    ext = makeDoiExtension(cache={
        GOOD_ARTICLE_DOI: {
            'URL': 'http://x',
            'title': ['Title'],
            'created': {
                'date-parts': [[1]]
            }
        }
    })
    mkd = markdown.Markdown(extensions=[ext])
    html = mkd.convert(doify(GOOD_ARTICLE_DOI))
    assert html == surround('<span class="doi"><a href="http://x">Title</a> <span class="doi-year">(1)</span></span>')


@vcr.use_cassette('test/cassettes/api_success.yml')
def test_template():
    def templater(metadata, doi_pattern):
        el = markdown.util.etree.Element("span")
        el.text = '%(given)s %(family)s' % metadata['author'][0]
        return el

    ext = makeDoiExtension(templater=templater)
    mkd = markdown.Markdown(extensions=[ext])
    html = mkd.convert(doify(GOOD_ARTICLE_DOI))
    assert html == surround('<span>Bert J. Tolkamp</span>')


# TODO Test cache file
