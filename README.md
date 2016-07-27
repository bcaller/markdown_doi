# Document Object Identifiers and Python and Markdown, together!

Type journal article DOIs, and have them automagically converted into a beautiful bibliography.

[![travis](https://travis-ci.org/bcaller/markdown_doi.svg)](https://travis-ci.org/bcaller/markdown_doi)
[![PyPI version](https://badge.fury.io/py/markdown_doi.svg)](https://badge.fury.io/py/markdown_doi)

A Markdown extension that looks through your text for things like `doi:10.1234/j.banana.5678`,
looks up the metadata on the crossref API and outputs text according to your requirements

Add `'markdown_doi'` to your Markdown call and watch the magic unfold:

```python
>>> from markdown import Markdown

>>> markdown = Markdown(extensions=['markdown_doi']
>>> markdown.convert('doi:10.1016/j.applanim.2010.02.004')
```
outputs
```html
<p><span class="doi"><a href="http://dx.doi.org/10.1016/j.applanim.2010.02.004">Are cows more likely to lie down the longer they stand?</a> <span class="doi-year">(2010)</span></span></p>
```

You can enable the caching if for example you are using Pelican and constantly regenerating the same files

```python
>>> markdown = Markdown(extensions=['markdown_doi(cache_file=.doi_cache)']
```

The templating function takes the metadata Dict from the
message key of [the JSON API response](https://api.crossref.org/works/10.1016/j.applanim.2010.02.004)
and returns a `markdown.util.etree.ElementTree`. See the default `template_title_link_year` function.

```python
from markdown_doi import makeExtension as makeDoiExtension

def templater(metadata, doi_pattern):
    el = markdown.util.etree.Element("span")
    el.text = '%(given)s %(family)s' % metadata['author'][0]
    return el

ext = makeDoiExtension(templater=templater)
md = markdown.Markdown(extensions=[ext])
html = md.convert('hello 10.1016/j.applanim.2010.02.004')
assert html == 'hello <p><span>Bert J. Tolkamp</span></p>'
```

## Options
| Option    | Type | Default |Description |
|-----------|------|---------|------------|
| templater | (Dict, LinkPattern) -> etree.ElementTree | None | Function which renders the metadata as an element tree |
| cache_file | str | '' | File name that can store a cache of the DOIs looked up |
| cache | dict | None | Instead, you can pass a map from DOI to metadata dict as the cache rather than a file name |


## Installation
From Github:

```
git clone https://github.com/bcaller/markdown_doi.git
pip install -e ./markdown_doi
```

From Pypi:

```
pip install markdown_doi
```
