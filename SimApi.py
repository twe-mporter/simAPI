#!/usr/bin/env python
# Copyright (c) 2014 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.

# pylint: disable=C0103
# pylint: disable=F0401

import cjson
import imp
import re
import time
import traceback

import jsonrpclib

import CapiAaa
import CapiConstants
import CapiRequestContext

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
        self.aaa_manager = CapiAaa.AaaManager('ar')
        self.server = jsonrpclib.Server(EAPI_SOCKET)

    def __call__(self, request, start_response):
        (code, content_type,
         headers, body) = self.processRequest(request)
        headers = headers if headers else []
        headers.append(('Content-type', content_type))
        if body:
            headers.append(('Content-length', str(len(body))))
            start_response(code,
                           CapiConstants.ServerConstants.DEFAULT_HEADERS +
                           headers)
        return [body]

    def processCommand(self, cmd, config):
        if type(cmd) != str:
            return None

        if 'cmds' in config:
            for command, value in config['cmds'].iteritems():
                if cmd == command:
                    if 'result' not in value and 'plugin' not in value:
                        raise MissingConfigError(
                           '"%s" matched "%s", but result/plugin is missing '
                           'from config' % (cmd, command))

                    try:
                        time.sleep(int(value.get('delay', 0)))
                    except TypeError:
                        raise InvalidDelayError(
                           'Invalid delay value for "%s": %s' %
                           (command, value['delay']))

                    if 'plugin' in value:
                        try:
                            plugin = imp.load_source(
                                None, 
                                '%s/%s' % (SIM_API_PLUGINS_DIR,
                                           value['plugin']))
                            result = plugin.main(self.server)
                        except Exception as exc:
                            raise PluginError(
                                'Failed to load plugin %s: %s' % 
                                (value['plugin'], exc))
                            
                    elif 'result' in value:
                        result = value['result']

                    if result is None:
                        return {}
                    else:
                        return result

        if 'regexes' in config:
            for regex, value in config['regexes'].iteritems():
                match = re.match(regex, cmd)
                if match:
                    if 'result' not in value:
                        raise MissingConfigError(
                           '"%s" matched "%s", but result is missing '
                           'from config' % (cmd, regex))

                    result = value['result']
                    if result is None:
                        return {}

                    for index, group in enumerate(match.groups()):
                        result = eval(str(result).replace('$%d' % (index + 1),
                                                          group))
                    try:
                        time.sleep(int(value.get('delay', 0)))
                    except TypeError:
                        raise InvalidDelayError(
                           'Invalid delay value for "%s": %s' %
                           (regex, value['delay']))
                    return result

        return None

    def processRequest(self, request):
        '''Common implementation of all HTTP requests.'''
        try:
            config = load_config()

            with CapiRequestContext.RequestContext(
                    request,
                    self.aaa_manager) as request:
                request = cjson.decode(request.getRequestContent())
                assert request['method'] == 'runCmds', \
                    'Only runCmds is mocked'
                result = []

                req_format = 'json'
                params = request['params']
                if isinstance(params, list):
                    cmds = params[1]
                    if len(params) == 3:
                        req_format = params[2]
                else:
                    cmds = params['cmds']
                    if 'format' in params:
                        req_format = params['format']

                for cmd in cmds:
                    cmd_result = self.processCommand(cmd, config)
                    if cmd_result is not None:
                        result.append(cmd_result)
                    else:
                        try:
                            output = self.server.runCmds(
                                1, [cmd], req_format)
                        except jsonrpclib.ProtocolError as exc:
                            result = cjson.encode({
                                'jsonrpc': '2.0',
                                'error': {'code': exc.message[0],
                                          'message': exc.message[1]},
                                'id': request['id']})
                            return ('1002 invalid command', 'application/json',
                                    None, result)
                        result.append(output[0])
                result = cjson.encode({'jsonrpc': '2.0',
                                        'result': result,
                                        'id': request['id']})
                return ('200 OK', 'application/json', None, result)
        except CapiRequestContext.HttpException as exc:
            return ('%s %s' % (exc.code, exc.name), exc.content_type,
                    exc.additionalHeaders,
                    exc.message)
        except Exception as exc:
            traceback.print_exc()
            return ('500 Internal Server Error', 'text/html', None,
                    exc.message)
