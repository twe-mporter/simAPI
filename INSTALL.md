If another extension with the same name is already installed, first remove that:

```
EOS# show extensions
Name                                       Version/Release           Status extension
------------------------------------------ ------------------------- ------ ----
simApi-1.0.0.swix                          1.0.0/1                   A, I      1

A: available | NA: not available | I: installed | NI: not installed | F: forced

EOS# no extension simApi-1.0.0.swix
EOS# show extensions
show extensions
Name                                       Version/Release           Status extension
------------------------------------------ ------------------------- ------ ----
simApi-1.0.0.swix                          1.0.0/1                   A, NI     1

A: available | NA: not available | I: installed | NI: not installed | F: forced

EOS# delete extension:simApi-1.0.0.swix
EOS# show extensions
No extensions are available

EOS# show boot-extensions
simApi-1.0.0.swix

EOS# copy installed-extensions boot-extensions
Copy completed successfully.
EOS# show boot-extensions
<empty>
```

Copy the extension to the switch using the **copy** command:
```
EOS# copy <simApi-1.0.0.swix> extension:
```

Install the extension:
```
EOS# extension simApi-1.0.0.swix
```

In order to make the extension persistent over reboot, use:
```
EOS# copy installed-extensions boot-extensions
```

Add the following configuration to EOS:
```
management api http-commands
   protocol http[s]
   protocol unix-socket
   no shutdown
```

In order to make the configuration persistent over reboot, use:
```
EOS# copy running-config startup-config
```

If everything went well, **show extensions** should show:
```
EOS#show extensions 
show extensions
Name                                       Version/Release           Status extension
------------------------------------------ ------------------------- ------ ----
simApi-1.0.0.swix                          1.0.0/1                   A, I      1

A: available | NA: not available | I: installed | NI: not installed | F: forced
```