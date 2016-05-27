#!/usr/bin/python

"""
SAND conformance server.

This implements a conformance server for ISO/IEC 23009-5 SAND.
It validates the incoming SAND messages as well as the protocols used by
a SAND client.

Copyright (c) 2016-, ISO/IEC JTC1/SC29/WG11
All rights reserved.

See AUTHORS for a full list of authors.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:
* Redistributions of source code must retain the above copyright
notice, this list of conditions and the following disclaimer.
* Redistributions in binary form must reproduce the above copyright
notice, this list of conditions and the following disclaimer in the
documentation and/or other materials provided with the distribution.
* Neither the name of the ISO/IEC nor the
names of its contributors may be used to endorse or promote products
derived from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDERS BE LIABLE FOR ANY
DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

import logging
from flask import Flask, request
from werkzeug.routing import Rule
from lxml import etree

import sand.header
from sand.xml_message import XMLValidator

root = logging.getLogger()
root.setLevel(logging.DEBUG)

app = Flask(__name__)
app.debug = True
app.url_map.add(Rule('/metrics', endpoint='metrics'))

@app.endpoint('metrics')
def metrics():
    success = True
  
    expected_request_method = "POST"
    expected_content_type = "application/sand+xml"

    # Test 1 - HTTP method test
    if request.method == expected_request_method:
        logging.info("[TEST] HTTP method OK (%s)", expected_request_method)
        success &= True
    else:
        logging.info("[TEST] HTTP method NOK (%s != %s)",
                     request.method,
                     expected_request_method)
        success = False
  
    # Test 2 - Content-Type of SAND messages
    if request.headers['Content-Type'] == expected_content_type:
        logging.info("[TEST] Content-Type OK (%s)", expected_content_type)
        success &= True
    else:
        logging.info("[TEST] Content-Type NOK (%s != %s)",
                     request.headers['Content-Type'],
                     expected_content_type)
        success = False

    # Test 3 - Message validation
    try:
        validator = XMLValidator()
        if validator.from_string(request.data):
            logging.info("[TEST] SAND message validation OK")
            success &= True
        else:
            logging.info("[TEST] SAND message validation KO")
            success = False
    except:
        logging.error("XML SAND message parsing")
        success = False

    if success:
        logging.info("[RESULT] Success")
        return ("Test succeeded !", 200)
    else:
        logging.info("[RESULT] Failure")
        return ("Test failed !", 400)

@app.route('/headers')
def check_headers():
    success = True
    report = {}
    for header_name, msg in request.headers.items():
        if header_name.upper().startswith('SAND-'):
            checker = sand.header.header_name_to_checker.get(header_name.lower())
            if checker:
                checker.check_syntax(msg.strip())
                report[header_name] = checker.errors
            else:
                report[header_name] = [('Header name not supported by this ' +
                                        'version of conformance server')]
        result = "Report for SAND headers conformance:\n"
        if report:
            for name, errors in report.items():
                if errors:
                    result += '%s: FAILED\n' % name
                    for msg in errors:
                        result  += '    %s\n' % msg
                else:
                    result += '%s: PASSED\n' % name
        else:
            result += 'No SAND header found!\n'
    return result, 200, {'Content-Type': 'text/plain'}

if __name__ == "__main__":
    print "========= SAND conformance server ============="
    print "-----------------------------------------------"
    app.run()
