#!/usr/bin/env python
# encoding: utf-8

# Copyright (C) 2010-2011 Red Hat, Inc.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
# MA  02110-1301, USA.  A copy of the GNU General Public License is
# also available at http://www.gnu.org/copyleft/gpl.html.

import logging
import httplib2
import re
import uuid
from imagefactory.ApplicationConfiguration import ApplicationConfiguration
from imagefactory.ImageWarehouse import ImageWarehouse

class Template(object):
    uuid_pattern = '([0-9a-f]{8})-([0-9a-f]{4})-([0-9a-f]{4})-([0-9a-f]{4})-([0-9a-f]{12})'
    
    # @classmethod
    # def fetch_template_with_id(cls, identifier):
    #     return cls(uuid)
    # 
    # @classmethod
    # def fetch_template_with_url(cls, url):
    #     return cls(url)
    # 
    
    # Properties
    def identifier():
        doc = "The identifier property."
        def fget(self):
            return self._identifier
        def fset(self, value):
            self._identifier = value
        def fdel(self):
            del self._identifier
        return locals()
    identifier = property(**identifier())
    
    def url():
        doc = "The url property."
        def fget(self):
            return self._url
        def fset(self, value):
            self._url = value
        def fdel(self):
            del self._url
        return locals()
    url = property(**url())
    
    def xml():
        doc = "The xml property."
        def fget(self):
            return self._xml
        def fset(self, value):
            self._xml = value
        def fdel(self):
            del self._xml
        return locals()
    xml = property(**xml())
    
    
    def __repr__(self):
        if(self.xml):
            return self.xml
        else:
            return super(Template, self).__repr__
    
    def __str__(self):
        return self.__repr__()
    
    def __init__(self, template=None, uuid=None, url=None, xml=None, bucket="templates"):
        self.log = logging.getLogger('%s.%s' % (__name__, self.__class__.__name__))
        self.warehouse = ImageWarehouse(ApplicationConfiguration().configuration["warehouse"])
        self.bucket = bucket
        
        self.identifier = None
        self.url = None
        self.xml = None
        
        if(template):
            template_string = str(template)
            template_string_type = self.__template_string_type(template_string)
            if(template_string_type == "UUID"):
                uuid = template_string
            elif(template_string_type == "URL"):
                url = template_string
            elif(template_string_type == "XML"):
                xml = template_string
        
        if(uuid):
            self.identifier, self.xml = self.__fetch_template_for_uuid(uuid, bucket)
            if((not self.identifier) and (not self.xml)):
                raise RuntimeError("Could not create a template with the uuid %s" % (uuid, ))
        elif(url):
            self.url = url
            self.identifier, self.xml = self.__fetch_template_with_url(url)
        elif(xml):
            self.xml = xml
        else:
            raise ValueError("'template' must be a UUID, URL, or XML document...")
    
    def __template_string_type(self, template_string):
        regex = re.compile(Template.uuid_pattern)
        match = regex.search(template_string)
        
        if(template_string.lower().startswith("http")):
            return "URL"
        elif(("<template>" in template_string.lower()) and ("</template>" in template_string.lower())):
            return "XML"
        elif(match):
            return "UUID"
        else:        
            raise ValueError("'template_string' must be a UUID, URL, or XML document...")
    
    def __fetch_template_for_uuid(self, uuid_string, bucket):
        xml_string, metadata = self.warehouse.template_with_id(uuid_string, bucket=self.bucket)
        if(xml_string and self.__string_is_xml_template(xml_string)):
            return uuid.UUID(uuid_string), xml_string
        else:
            self.log.debug("Unable to fetch a valid template given template id %s:\n%s\n" % (uuid_string, self._addreviated_template(xml_string)))
            template_id, xml_string, metadata = self.warehouse.template_for_image_id(uuid_string, bucket=self.bucket.replace("templates", "images"), template_bucket=self.bucket)
            if(template_id and xml_string and self.__string_is_xml_template(xml_string)):
                return uuid.UUID(template_id), xml_string
            else:
                self.log.debug("Unable to fetch a valid template given an image id %s:\n%s\n" % (uuid_string, self._addreviated_template(xml_string)))
                return None, None
    
    def __string_is_xml_template(self, text):
        return (("<template>" in text.lower()) and ("</template>" in text.lower()))
    
    def __fetch_template_with_url(self, url):
        template_id = None
        regex = re.compile(Template.uuid_pattern)
        match = regex.search(url)
        
        if (match):
            template_id = uuid.UUID(match.group())
            
        response_headers, response = httplib2.Http().request(url, "GET", headers={'content-type':'text/plain'})
        if(response and self.__string_is_xml_template(response)):
            return template_id, response
        else:
            raise RuntimeError("Recieved status %s fetching a template from %s!\n--- Response Headers:\n%s\n--- Response:\n%s" % (response_headers["status"], url, response_headers, response))
    
    def _addreviated_template(self, template_string):
        lines = template_string.splitlines(True)
        if(len(lines) > 20):
            return "%s\n...\n...\n...\n%s" % ("".join(lines[0:10]), "".join(lines[-10:len(lines)]))
        else:
            return template_string
    
