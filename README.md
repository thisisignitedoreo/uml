
# uml
~~ur mom language~~

universal markup language example implementation in python

## overview
meant to be used as library, but can be used as cmd program to interfer with json.

i know the code is messy, stop saying that to me.

library thing:

- function `parse(text)`:

    parses krml to python object<br/>
    throws ValueError on error
    
    arguments:
    
      text: str
    
    returns: any
- function `serialize(object, compact=False, indent="  ")`:
    
    parses python object to krml<br/>
    throws ValueError on error<br/>
    no newlines/indents if compact<br/>
    if not compact indent code with indent
    
    arguments:
      
      object: any
      compact: bool
      indent: str
    
    returns: str

cmd thing:

run it without arguments to get help

