#!/usr/bin/env python
# -*- coding: utf-8 -*-

import io
import os
import re
import csv
import iso8601
import requests
from textwrap import dedent
from operator import attrgetter


SOURCEDIR = os.path.join(os.path.dirname(__file__), '..', 'source')
SOURCEFILE = os.path.join(SOURCEDIR, 'result-of-survey.tsv')

descriptions = {
    'autodoc': u'Generates documentation from source code or others',
    'builders': u'Enables to output document as new format',
    'changelog/version-control': u'Enables to mark up changelog, history and version info',
    'data-sources': u'Generates tables from database or others',
    'domains': u'Adds language-domains',
    'enhancement': u'Enhances features of Sphinx',
    'execute/result': u'Executes commands or codes, and takes the results to document',
    'images': u'Inserts (generates) images to document',
    'integrations': u'Integrates with other documents',
    'jokes': u'Joke extensions',
    'metadata': u'Enables to mark up metadata to document',
    'multimedia/web-services': u'Inserts multimedia contents and contents from Web services',
    'roles': u'Adds Sphinx roles',
    'search': u'Enhances search features of Sphinx',
    'thesis/latex': u'Extensions for thesis and LaTeX',
    'utilities': u'Tools for Sphinx',
    'website/blogs': u'Extensions for Web sites and blogging',
    'misc': u'miscellaneous extensions',
}


class Extension(object):
    @staticmethod
    def create(row):
        if row[2] == 'PyPI':
            return ExtensionOnPyPI(row)
        elif row[2] in ('gist', 'github'):
            return ExtensionOnGithub(row)
        elif row[2] == 'bitbucket':
            return ExtensionOnBitbucket(row)
        else:
            return Extension(row)

    def __init__(self, row):
        self.name = row[0]
        self.url = row[1]
        self.published_at = row[2]
        self.category = row[3]
        self.notes = row[4]

    def to_rst(self):
        template = u"""
        .. container:: sphinx-extension misc

           :extension-name:`%(package_name)s`

           :release: %(published_at)s
           :Download URL: %(url)s
           :Note: %(notes)s
        """
        params = dict(package_name=self.name,
                      url=self.url,
                      published_at=self.published_at,
                      notes=self.notes)
        return dedent(template) % params


class ExtensionOnPyPI(Extension):
    author = 'unknown'
    version = 'unknown'
    released_at = 'unknown'

    def fetch_packageinfo(self):
        url = "https://pypi.python.org/pypi/%s/json" % self.name
        r = requests.get(url).json()
        self.version = r['info']['version']
        self.author = r['info']['author']
        releases = r['releases'].get(self.version)
        if releases:
            self.released_at = iso8601.parse_date(releases[0]['upload_time']).replace(tzinfo=None)

    def to_rst(self):
        self.fetch_packageinfo()
        template = u"""
        .. container:: sphinx-extension PyPI

           :extension-name:`%(package_name)s`
           |%(package_name)s-py_versions| |%(package_name)s-download|

           :author:  %(author)s
           :version: %(version)s
           :release: %(released_at)s
           :Download URL: %(url)s

           .. |%(package_name)s-py_versions| image:: https://pypip.in/py_versions/%(package_name)s/badge.svg
              :target: https://pypi.python.org/pypi/%(package_name)s/
              :alt: Latest Version

           .. |%(package_name)s-download| image:: https://pypip.in/download/%(package_name)s/badge.svg
              :target: https://pypi.python.org/pypi/%(package_name)s/
              :alt: Downloads
        """
        params = dict(package_name=self.name,
                      author=self.author,
                      url=self.url,
                      version=self.version,
                      released_at=self.released_at)
        return dedent(template) % params


class ExtensionOnGithub(Extension):
    author = 'unknown'

    def fetch_packageinfo(self):
        match = re.search('github.com/(\w+)/', self.url)
        if match:
            self.author = match.group(1)

    def to_rst(self):
        self.fetch_packageinfo()
        template = u"""
        .. container:: sphinx-extension github

           :extension-name:`%(package_name)s`

           :author:  %(author)s
           :Download URL: %(url)s
           :Note: %(notes)s
        """
        params = dict(package_name=self.name,
                      author=self.author,
                      url=self.url,
                      notes=self.notes)
        return dedent(template) % params


class ExtensionOnBitbucket(Extension):
    author = 'unknown'

    def fetch_packageinfo(self):
        match = re.search('bitbucket.org/(\w+)/', self.url)
        if match:
            self.author = match.group(1)

    def to_rst(self):
        self.fetch_packageinfo()
        template = u"""
        .. container:: sphinx-extension bitbucket

           :extension-name:`%(package_name)s`

           :author:  %(author)s
           :Download URL: %(url)s
           :Note: %(notes)s
        """
        params = dict(package_name=self.name,
                      author=self.author,
                      url=self.url,
                      notes=self.notes)
        return dedent(template) % params


def main():
    categories = {}
    with open(SOURCEFILE) as fd:
        fd.readline()  # skip header
        for row in csv.reader(fd, delimiter='\t'):
            ext = Extension.create(row)
            category = categories.setdefault(ext.category, [])
            category.append(ext)

    for category, extensions in categories.items():
        output = os.path.join(SOURCEDIR, category.replace("/", "-") + '.rst')
        with io.open(output, 'wt', encoding='utf-8') as fd:
            category_name = "%s (%d)" % (category, len(extensions))
            fd.write(u"%s\n" % category_name)
            fd.write(u"%s\n" % ("=" * len(category_name)))
            fd.write(u"\n")
            fd.write(u"%s\n" % descriptions[category])
            fd.write(u"\n")
            fd.write(u".. role:: extension-name\n")
            fd.write(u"\n")
            for ext in sorted(extensions, key=attrgetter('name')):
                fd.write(ext.to_rst())


main()
