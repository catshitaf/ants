""" This module implements the DecompressionMiddleware which tries to recognise
and extract the potentially compressed responses that may arrive. 
"""

import bz2
import gzip
import zipfile
import tarfile
from cStringIO import StringIO
from tempfile import mktemp

from ants.utils import log
from ants.responsetypes import responsetypes


class DecompressionMiddleware(object):
    """ This middleware tries to recognise and extract the possibly compressed
    responses that may arrive. """

    def __init__(self):
        self._formats = {
            'tar': self._is_tar,
            'zip': self._is_zip,
            'gz': self._is_gzip,
            'bz2': self._is_bzip2
        }

    def _is_tar(self, response):
        archive = StringIO(response.body)
        try:
            tar_file = tarfile.open(name=mktemp(), fileobj=archive)
        except tarfile.ReadError:
            return

        body = tar_file.extractfile(tar_file.members[0]).read()
        respcls = responsetypes.from_args(filename=tar_file.members[0].name, body=body)
        return response.replace(body=body, cls=respcls)

    def _is_zip(self, response):
        archive = StringIO(response.body)
        try:
            zip_file = zipfile.ZipFile(archive)
        except zipfile.BadZipfile:
            return

        namelist = zip_file.namelist()
        body = zip_file.read(namelist[0])
        respcls = responsetypes.from_args(filename=namelist[0], body=body)
        return response.replace(body=body, cls=respcls)

    def _is_gzip(self, response):
        archive = StringIO(response.body)
        try:
            body = gzip.GzipFile(fileobj=archive).read()
        except IOError:
            return

        respcls = responsetypes.from_args(body=body)
        return response.replace(body=body, cls=respcls)

    def _is_bzip2(self, response):
        try:
            body = bz2.decompress(response.body)
        except IOError:
            return

        respcls = responsetypes.from_args(body=body)
        return response.replace(body=body, cls=respcls)

    def process_response(self, request, response, spider):
        if not response.body:
            return response

        for fmt, func in self._formats.iteritems():
            new_response = func(response)
            if new_response:
                log.spider_log('Decompressed response with format:' + fmt,
                               level=log.DEBUG, spider=spider, )
                return new_response
        return response
