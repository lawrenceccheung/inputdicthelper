# Inputdicthelper

A lightweight, helper library to read inputs from dictionary format: yaml, json, ini.  Has the following features:
- Self documenting
- Input validation

## 1. Define the inputs

The input definitions should be a list of dicts.

```python
inputdefinition = [
    {'key':'name',    'required':True,  'type':str, 'default':'myname',
     'validate':None,
     'help':'An arbitrary name',},
    {'key':'intval',  'required':True, 'type':int, 'default':0,
     'validate':(lambda x: (x>=0)),
     'help':'An arbitrary integer',},
    {'key':'floatval','required':False, 'type':(int, float), 'default':0,
     'validate':(lambda x, y: (x+y['intval']>=200)),
     'help':'An arbitrary float',},
    {'key':'boolval','required':False, 'type':bool, 'default':True,
     'validate':None,
     'help':'An arbitrary boolean',},
    {'key':'subdict', 'required':True,  'type':{}, 'default':testsubdict,
     'validate':None,
     'help':'A required subdictionary',},
]
```

### Fields
Each of the dictionaries in the `inputdefinition` list should have the following fields
- **key**: `String`
  
  This is name of the key used in the input dictionary.

- **required**:`Boolean` which describes whether this input is a
  required to be provided or not.

- **type**: The variable type of the input.

  Note that `type` can be `None`, in which case type checking is
  bypassed.  This can also be specified as multiple allowed types by
  usinga tuple like `(int, float)`. For subdictionaries, use the `{}`
  type.  For list types, use `[]`.

- **default**: The default value of the input if it is not specified.

- **validate**: function or `None`

  This is a validation function that can be used to validate the input
  value.  The inputs can be one or two arguments.  For single argument
  functions, (e.g., `lambda x: (x>=0)`), it just validates the value
  itself.  For double arguments (e.g., `lambda x, y: (x+y['intval']>=200)`), 
  it accepts both the value `x` and the full dictionary `y`, so `x`
  can be validated against other entries in `y`.
  
  In either case, the function output should be either a boolean or a
  tuple of the form `(Boolean, ErrMesg)`, where `ErrMesg` is a string
  that gets displayed when `Boolean` is False.

- **help**:`String`
  
  A help string that describes the input value.

## 2. Initialize the input template


```
import inputdicthelper as idh
intemplate = idh.inputdict(inputdefinition, globalhelp=headerdoc)
```

`headerdoc` is an optional string which will provide the header
comments if `ruamel.yaml` is available.

## 3.  Read the inputs from the user

From string input `inputstr`:
```
inputs = intemplate.ingestyaml(inputstr, fromstring=True, checkunused=False)
```

From the file `filename`:
```
inputs = intemplate.ingestyaml(filename, fromstring=True, checkunused=False)
```

From a file handle `f`:
```
with open(filename 'r') as f:
	inputs = intemplate.ingestyaml(f, fromstring=True, checkunused=False)
```



