# Inputdicthelper

A lightweight, helper library to read inputs from dictionary format: yaml, json, ini.  Has the following features:
- Self documenting
- Input validation

## Define the inputs

The input definitions should be a list of dicts.

```python
inputdefinition = [
    {'key':'name',    'required':True,  'type':None, 'default':'myname', 'validate':None,
     'help':'An arbitrary name',},
    {'key':'intval',  'required':True, 'type':int, 'default':0, 'validate':(lambda x: (x>=0)),
     'help':'An arbitrary integer',},
    {'key':'floatval','required':False, 'type':(int, float), 'default':0, 'validate':(lambda x, y: (x+y['intval']>=200)),
     'help':'An arbitrary float',},
    {'key':'boolval','required':False, 'type':bool, 'default':True, 'validate':None,
     'help':'An arbitrary boolean',},
    {'key':'subdict', 'required':True,  'type':{}, 'default':testsubdict, 'validate':None,
     'help':'A required subdictionary',},
]
```

**key**: `String`

**required**:`Boolean`

**type**:

**default**:

**validate**: function or `None`

**help***:`String`

A help string that describes

## Initialize the dictionary
