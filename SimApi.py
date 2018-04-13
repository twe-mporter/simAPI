# Copyright (c) 2015, Arista Networks, Inc.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
#
#   Redistributions of source code must retain the above copyright notice,
#   this list of conditions and the following disclaimer.
#
#   Redistributions in binary form must reproduce the above copyright
#   notice, this list of conditions and the following disclaimer in the
#   documentation and/or other materials provided with the distribution.
#
#   Neither the name of Arista Networks nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL ARISTA NETWORKS
# BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
# WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE
# OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN
# IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

# pylint: disable=C0103
# pylint: disable=F0401
# pylint: disable=R0912

import cjson
import imp
import re
import time
import traceback

import jsonrpclib

import UwsgiConstants
import UwsgiRequestContext

#Handle non-backward compatible CAPI change
try:
    from CapiAaa import CapiAaaManager as AaaManager
except ImportError:
    from CapiAaa import AaaManager

EAPI_SOCKET = 'unix:/var/run/command-api.sock'

SIM_API_CONFIG_FILE = '/persist/sys/simAPI/simApi.json'
SIM_API_PLUGINS_DIR = '/persist/sys/simAPI/plugins'

# Regular expression for comments
COMMENT_RE = re.compile(
    r'(^)?[^\S\n]*/(?:\*(.*?)\*/[^\S\n]*|/[^\n]*)($)?',
    re.DOTALL | re.MULTILINE
)

class PluginError(Exception):
    pass

class MissingConfigError(Exception):
    pass

class InvalidDelayError(Exception):
    pass


def load_config():
    with open(SIM_API_CONFIG_FILE) as config:
        content = config.read()

        match = COMMENT_RE.search(content)
        while match:
            content = content[:match.start()] + content[match.end():]
            match = COMMENT_RE.search(content)

        # JSON only accepts double quotes
        content = content.replace("'", '"')
        
        return cjson.decode(content)


class SimApiApplication(object):
    def __init__(self):

        self.aaa_manager = AaaManager('ar')
        self.server = jsonrpclib.Server(EAPI_SOCKET)

    def __call__(self, request, start_response):
        (code, content_type,
         headers, body) = self.processRequest(request)
        headers = headers if headers else []
        headers.append(('Content-type', content_type))
        if body:
            headers.append(('Content-length', str(len(body))))
            start_response(code,
                           UwsgiConstants.DEFAULT_HEADERS +
                           headers)
        return [body]

    def processCommand(self, cmd, config, params):
        if type(cmd) != str:
            return None

        if 'cmds' in config:
            for command, value in config['cmds'].iteritems():
                if cmd == command:
                    if 'result' not in value and 'plugin' not in value:
                        raise MissingConfigError(
                           '"%s" matched "%s", but result/plugin is missing '
                           'from config' % (cmd, command))

                    result = None
                    if 'plugin' in value:
                        try:
                            plugin = imp.load_source(
                                value['plugin'], 
                                '%s/%s' % (SIM_API_PLUGINS_DIR,
                                           value['plugin']))
                            result = plugin.main(self.server, cmd, params)
                        except Exception as exc:
                            raise PluginError(
                                'Failed to load plugin %s: %s' % 
                                (value['plugin'], exc))
                            
                    elif 'result' in value:
                        result = value['result']

                    try:
                        time.sleep(int(value.get('delay', 0)))
                    except TypeError:
                        raise InvalidDelayError(
                           'Invalid delay value for "%s": %s' %
                           (command, value['delay']))

                    if result is None:
                        return {}
                    else:
                        return result

        if 'regexes' in config:
            for regex, value in config['regexes'].iteritems():
                match = re.match(regex, cmd)
                if match:
                    if 'result' not in value and 'plugin' not in value:
                        raise MissingConfigError(
                           '"%s" matched "%s", but result is missing '
                           'from config' % (cmd, regex))

                    result = None
                    if 'plugin' in value:
                        try:
                            plugin = imp.load_source(
                                value['plugin'], 
                                '%s/%s' % (SIM_API_PLUGINS_DIR,
                                           value['plugin']))
                            result = plugin.main(self.server, cmd, params)
                        except Exception as exc:
                            raise PluginError(
                                'Failed to load plugin %s: %s' % 
                                (value['plugin'], exc))
                            
                    elif 'result' in value:
                        result = value['result']

                    try:
                        time.sleep(int(value.get('delay', 0)))
                    except TypeError:
                        raise InvalidDelayError(
                           'Invalid delay value for "%s": %s' %
                           (regex, value['delay']))

                    if result is None:
                        return {}

                    for index, group in enumerate(match.groups()):
                        result = eval(str(result).replace('$%d' % (index + 1),
                                                          group))
                    return result

        return None

    def processRequest(self, request):
        '''Common implementation of all HTTP requests.'''
        try:
            config = load_config()

            with UwsgiRequestContext.UwsgiRequestContext(
                    request,
                    self.aaa_manager) as request:
                request = cjson.decode(request.getRequestContent())

                params = request['params']
                result = []

                if request['method'] == 'getCommandCompletions':
                    if isinstance(params, list):
                        command = params[0]
                    else:
                        command = params['command']
                        if isinstance(command, list):
                            command = command[0]

                    output = self.server.getCommandCompletions(
                        command)

                    result = cjson.encode({'jsonrpc': '2.0',
                                           'result': output,
                                           'id': request['id']})
                    return ('200 OK', 'application/json', None, result)
                elif request['method'] != 'runCmds':
                    assert False, \
                        'Only runCmds and getCommandCompletions are mocked'

                req_format = 'json'
                if isinstance(params, list):
                    cmds = params[1]
                    if len(params) == 3:
                        req_format = params[2]
                else:
                    cmds = params['cmds']
                    if 'format' in params:
                        req_format = params['format']
                    elif len(params) == 3:
                        req_format = params[-1]

                for index, cmd in enumerate(cmds):
                    cmd_result = self.processCommand(cmd, config, params)
                    if cmd_result is not None:
                        result.append(cmd_result)
                    else:
                        try:
                            output = self.server.runCmds(
                                1, cmds[:index+1], req_format)[-1]
                            result.append(output)
                        except jsonrpclib.ProtocolError as exc:
                            result = cjson.encode({
                                    'jsonrpc': '2.0',
                                    'error': {'code': exc.message[0],
                                              'message': exc.message[1]},
                                    'id': request['id']})
                            return ('1002 invalid command', 'application/json',
                                    None, result)
                result = cjson.encode({'jsonrpc': '2.0',
                                        'result': result,
                                        'id': request['id']})
                return ('200 OK', 'application/json', None, result)
        except UwsgiRequestContext.HttpException as exc:
            return ('%s %s' % (exc.code, exc.name), exc.contentType,
                    exc.additionalHeaders,
                    exc.message)
        except (Exception, cjson.DecodeError) as exc:
            traceback.print_exc()
            return ('500 Internal Server Error', 'text/html', None,
                    exc.message)
