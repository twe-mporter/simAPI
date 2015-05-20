# simAPI - custom eAPI responses

## Overview
simAPI enables users to define their own custom responses to eAPI requests. This can be useful in order to:
 - simulate LLDP neighbors by serving a custom response to **show lldp neighbors**
 - simulate VMs with a large number of interfaces, without actually configuring them in the hypervisor (by customising the output of **show interfaces ...**)
 - create custom CLI commands and responses
 - convert text/JSON output from eAPI commands to custom JSON responses
 - simulate eAPI responses for platform-specific CLI commands in vEOS
 - return eAPI results in non-JSON format (e.g. XML)
 - run BASH commands via eAPI
 - etc.

## Configuration
For installation instructions, please see INSTALL.md.

Once the extension is installed, users can start sending JSON-RPC requests via an HTTP POST request to **http[s]://\<hostname\>/command-api**. The format of the request is the same as for eAPI.

The response will be:
 - either read from **/persist/sys/simAPI/simApi.json**, if there
 - the same as for a request made to **http[s]://\<hostname\>/command-api**, if the CLI command is not configured in **/persist/sys/simAPI/simApi.json**

In order to send simAPI requests to an URL different than the eAPI URL (**http[s]://\<hostname\>/sim-api** instead of **http[s]://\<hostname\>/command-api**):

 - change the first line in **/etc/nginx/external_conf/simApi.conf** as follows:

    <pre>-location =/command-api {
    +location /sim-api {</pre>

 - run **sudo service nginx restart** from bash in order to reload the config

The configuration file (**/persist/sys/simAPI/simApi.json**) is using the JSON format and is following the conventions below:

```
{
  // This is a comment
  "cmds" : {
     <COMMAND>:
      { 
        "delay" : <SECONDS>,     // Optional, default 0       
        "result" : <RESULT>,
        "plugin" : <PLUGIN>      // Yet another comment
      },

    /* This is
       another 
       comment. */

},

  "regexes" : {
     <REGULAR EXPRESSION>:
      { 
        "delay" : <SECONDS>,      // Optional, default 0       
        "plugin" : <PLUGIN>,
        "result" : <RESULT>       // Can use $<NUMBER> to refer to 
      },
  }
}
```

The optional *delay* can be configured for each CLI command in order to simulate eAPI responses which take a long time.

The configuration file contains two sections: **cmds** and **regexes**. **cmds** provides exact matches for the CLI commands and is assesed first. If no match can be found in **cmds**, the **regexes** section is considered. If not match can be found there either, then the eAPI engine will be used in order to return the native result for a particular command.

Once a match is made in either **cmds** and **regexes**, the response will be:
 - the return value of the **main** function in the plugin, if the **plugin** attribute is specified
 - the value of the **result** attribute, if the **plugin** attribute is NOT specified

Requests made to *simApi* may contain a mix of CLI commands, some of which are configured in the configuration file and some which are served via the eAPI engine.

Here is an example:
```
{
  // New CLI command
  "cmds" : {
     "show my version": 
      { 
        "result" : { "version" : 1 } 
      },

     "show port-channel": 
      { 
        "plugin" : "show_port-channel",

       // ignored because plugin takes precedence
        "result" : { "1" : 1 } 
      },

    /* Add
       delay */
    "show interfaces status": 
      { 
        "delay" : 3,
        "result" : { "Ethernet1" : "up",
                     "Ethernet2" : "down" } 
      }
  },

  "regexes" : {
     "show managament (.*)": 
      { 
        "delay" : 4,               // All "show management" 
                                   // commands will have a delay
        "result" : { "management" : "$1" } 
      }
  }
}
```

And here is how the results look in Python (example):
```
> import jsonrpclib
> client = jsonrpclib.Server( 'http://admin:admin@vEOS/sim-api' )
> client.runCmds( 1, [ 'show version' ] )
[{u'version': 1}]
```

## Plugins

Plugins must be written in Python and added to **/persist/sys/simAPI/plugins**. They must have a **main** method, which has a single input argument called *server*. This attribute is a jsonrpc.Server object which can be used in order to access the underlying eAPI engine on the switch.

Here is an example:

```
# force eAPI to always return the 'text' output for 'show version'
def main(server):
    return server.runCmds(1, ['show version'], 'text')[0]
```

Adding a new plugin does NOT require restarting any services.

## Rebuilding the RPM from source code

 - run **make rpm** on a Fedora system (running the same Fedora version as the EOS target version)

## Limitations

This extension is only compatible with EOS-4.14.5F and later.

## **ibm** branch
The *ibm* branch of this repository defaults the simAPI configuration to enabling the Burst Monitor plugin in simApi.json:

```
{
  "cmds" : {
  },

  "regexes" : {
     "ibm (.*)": { "plugin": "ibm" }
  }
}
```
For more details, please see the Burst Monitor repository @ https://github.com/arista-eosplus/BurstMonitor.
