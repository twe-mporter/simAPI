import re
import cjson
import jsonrpclib
import time
import traceback

import CapiAaa
import CapiConstants
import CapiRequestContext
import Tracing

traceHandle = Tracing.Handle('SimApi')
trace = traceHandle.trace3

EAPI_SOCKET = 'unix:/var/run/command-api.sock'
SIM_API_CONFIG_FILE = '/persist/sys/simApi.json'

# Regular expression for comments
COMMENT_RE = re.compile(
    '(^)?[^\S\n]*/(?:\*(.*?)\*/[^\S\n]*|/[^\n]*)($)?',
    re.DOTALL | re.MULTILINE
)

def load_config():
    with open(SIM_API_CONFIG_FILE) as f:
        content = ''.join(f.readlines())

        match = COMMENT_RE.search(content)
        while match:
            content = content[:match.start()] + content[match.end():]
            match = COMMENT_RE.search(content)

        return cjson.decode(content)

def processCommand(cmd, config):
    if type(cmd) != str:
        return None

    if 'regexes' in config:
        for regex, value in config['regexes'].iteritems():
            match = re.match(regex, cmd)
            if match:
                if 'result' not in value:
                    raise Exception('"%s" matched "%s", but result is missing '
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
                    raise Exception('Invalid delay value for "%s": %s' %
                                    (regex, value['delay']))
                return result

    if 'cmds' in config:
        for command, value in config['cmds'].iteritems():
            if cmd == command:
                if 'result' not in value:
                    raise Exception('"%s" matched "%s", but result is missing '
                                    'from config' % (cmd, command))

                try:
                    time.sleep(int(value.get('delay', 0)))
                except TypeError:
                    raise Exception('Invalid delay value for "%s": %s' %
                                    (command, value['delay']))

                result = value['result']
                if result is None:
                    return {}
                else:
                    return result

    return None

class SimApiApplication(object):
    def __init__(self):
        self.aaaManager = CapiAaa.AaaManager('ar')
        self.server = jsonrpclib.Server(EAPI_SOCKET)

    def __call__(self, request, start_response):
        (reposeCode, contentType,
         headers, body) = self.processRequest(request)
        headers = headers if headers else []
        headers.append(('Content-type', contentType))
        if body:
            headers.append(('Content-length', str(len(body))))
            start_response(reposeCode,
                           CapiConstants.ServerConstants.DEFAULT_HEADERS +
                           headers)
        return [body]

    def processRequest(self, request):
        '''Common implementation of all HTTP requests.'''
        trace('processRequest entry')
        try:
            config = load_config()

            with CapiRequestContext.RequestContext(
                    request,
                    self.aaaManager) as request:
                requestObject = cjson.decode(request.getRequestContent())
                assert requestObject['method'] == 'runCmds', \
                    'Only runCmds is mocked'
                cmdResult = []
                print requestObject
                for cmd in requestObject['params'][1]:
                    result = processCommand(cmd, config)
                    if result is not None:
                        cmdResult.append(result)
                    else:
                        reqFormat = 'json'
                        if len(requestObject['params']) == 3:
                            reqFormat = requestObject['params'][2]
                        try:
                           normalOutput = self.server.runCmds(
                              1, [cmd], reqFormat)
                        except jsonrpclib.ProtocolError as e:
                           print('processRequest protocol error', result)
                           result = cjson.encode({'jsonrpc': '2.0',
                                                  'error': { 'code': e.message[0],
                                                             'message': e.message[1] },
                                                  'id': requestObject['id']})
                           return ('1002 invalid command', 'application/json', 
                                   None, result)
                        cmdResult.append(normalOutput[0])
                result = cjson.encode({'jsonrpc': '2.0',
                                        'result': cmdResult,
                                        'id': requestObject['id']})
                print('processRequest exit', result)
                return ('200 OK', 'application/json', None, result)
        except CapiRequestContext.HttpException as e:
            trace('processRequest HttpException', e)
            return ('%s %s' % (e.code, e.name), e.contentType,
                    e.additionalHeaders,
                    e.message)
        except Exception as e:
            print('processRequest Exception', e)
            traceback.print_exc()
            return ('500 Internal Server Error', 'text/html', None, e.message)
