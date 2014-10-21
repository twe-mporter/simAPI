# simAPI - custom eAPI responses

## Overview
simAPI enables users to define their own custom responses to eAPI requests. This can be useful in order to:
 - simulate LLDP neighbors by serving a custom response to **show lldp neighbors**
 - simulate VMs with a large number of interfaces, without actually configuring them in the hypervisor (by customising the output of **show interfaces ...**)
 - create custom CLI commands and responses
 - etc.

## Configuration
For installation instructions, please see INSTALL.md.

Once the extension is installed, users can start sending JSON-RPC requests via an HTTP POST request to **http[s]://\<hostname\>/sim-api**. The format of the request is the same as for eAPI.

The response will be:
 - either read from **/persist/sys/simApi.json**, if there
 - the same as for a request made to **http[s]://\<hostname\>/command-api**, if the CLI command is not configured in **/persist/sys/simApi.json**

The configuration file (**/persist/sys/simApi.json**) is using the JSON format and is following the conventions below:

```
{
  // This is a comment
  "cmds" : {
     <COMMAND>:
      { 
        "delay" : <SECONDS>,     // Optional, default 0       
        "result" : <RESULT>
      },

    /* This is
       another 
       comment. */

     <COMMAND>:
      { 
        "result" : <RESULT>      // Yet another comment
      },
  },

  "regexes" : {
     <REGULAR EXPRESSION>:
      { 
        "delay" : <SECONDS>,      // Optional, default 0       
        "result" : <RESULT>       // Can use $<NUMBER> to refer to 
                                  // regex groups
      },
  }
}
```

Here is an example:
```
{
  // New CLI command
  "cmds" : {
     "show my version": 
      { 
        "result" : { "version" : 1 } 
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

The optional *delay* can be configured for each CLI command in order to simulate eAPI responses which take a long time.

The configuration file contains two sections: **cmds** and **regexes**. **cmds** provides exact matches for the CLI commands and is assesed first. If not match can be found in **cmds**, the **regexes** section is considered. If not match can be foun there either, then the eAPI engine will be used in order to return the result for a particular command.

Requests made to *simApi* may contain a mix of CLI commands, some of which are configured in the configuration file and some which are served via the eAPI engine.

## Generating the extension from source code

 - run **make rpm** on a Fedora system (running the same Fedora version as the EOS target version)
 - copy the RPM from **rpmbuild** folder to vEOS node
 - use **swix create** from bash in order to generate the new extension file

## Limitations

This extension is compatible with EOS-4.14.4 and later.