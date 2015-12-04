# eba-tools

These scripts use the [Python v2.2 API](http://manual.altova.com/RaptorXML/pyapiv2/html/) of [RaptorXML+XBRL Server](http://www.altova.com/raptorxml.html).


##### eba_validation.py
This script implements additional validation rules specified in the EBA XBRL Filing Rules ([Version 4.1](https://www.eba.europa.eu/documents/10180/1181744/EBA+XBRL+Filing+Rules+v4.1.pdf)) document.

The following script parameters can be additionally specified:

parameter | description
--- | ---
`max-string-length`   |            Issue warnings if length of fact content exceeds the given limit (default=100)
`max-id-length`      |             Issue warnings if length of id attribute values exceeds the given limit (default=50)


###### Example invocations:

Validate a single filing
```
  raptorxmlxbrl valxbrl --script=eba_validation.py instance.xbrl
```

Validate a single filing with additional options
```
  raptorxmlxbrl valxbrl --script=eba_validation.py --script-param=max-id-length:10 instance.xbrl
```

Using Altova RaptorXML+XBRL Server with XMLSpy client:

1. do one of
    * Copy `eba_validation.py` to the Altova RaptorXML Server script directory `etc/scripts/` (default `C:\Program Files\Altova\RaptorXMLXBRLServer2016\etc\scripts\` on Windows)
    *   Edit the `<server.script-root-dir>` tag in the `etc/server_config.xml` Altova RaptorXML Server script directory
2.    Start Altova RaptorXML+XBRL server
3.    Start Altova XMLSpy, open `Tools|Manage Raptor Servers...` and connect to the running server
4.    Create a new configuration and rename it to e.g. "EBA CHECKS"
5.    Select the XBRL Instance property page and then set the script property to `eba_validation.py`
6.    Select the new "EBA CHECKS" configuration in `Tools|Raptor Servers and Configurations`
7.    Open a EBA instance file
8.    Validate instance with `XML|Validate XML on Server` (`Ctrl+F8`)
