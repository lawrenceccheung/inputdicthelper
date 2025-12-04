#!/usr/bin/env python3
#
# A helper library to get inputs from a dictionary

import copy
import inspect
import sys
import io
import configparser
import ast

# Load ruamel or pyyaml as needed
try:
    import ruamel.yaml
    from ruamel.yaml.comments import CommentedMap
    yaml = ruamel.yaml.YAML(typ='rt')
    #yaml.default_flow_style = True
    useruamel=True
    loaderkwargs = {}
    dumperkwargs = {}
    Loader=yaml.load
except:
    import yaml as yaml
    useruamel=False
    loaderkwargs = {}
    dumperkwargs = {'default_flow_style':False }
    Loader=yaml.safe_load

testsubdict = [
    {'key':'name',  'required':True,  'type':str,   'default':'mysubdict', 'validate':None,
     'help':'An arbitrary name',},
    {'key':'mylist', 'required':False,  'type':[],   'default':[1,2,3,5], 'validate':None,
     'help':'An arbitrary list',},
]

testheader="""
This is a test of the inputdicthelper
These are the inputs

"""
testmaininput = [
    {'key':'name',    'required':True,  'type':None, 'default':'myname', 'validate':None,
     'help':'An arbitrary name',},
    {'key':'intval',  'required':True, 'type':int, 'default':0, 'validate':(lambda x: (x>=0, 'intval must be >= 0.')),
     'help':'An arbitrary integer',},
    {'key':'floatval','required':False, 'type':(int, float), 'default':0.123, 'validate':(lambda x, y: (x+y['intval']>=200)),
     'help':'An arbitrary float',},
    {'key':'boolval','required':False, 'type':bool, 'default':True, 'validate':None,
     'help':'An arbitrary boolean',},
    {'key':'subdict', 'required':True,  'type':{}, 'default':testsubdict, 'validate':None,
     'help':'A required subdictionary',},
]

testiniinput = [
    {'key':'default', 'required':True,  'type':{}, 'default':testmaininput[:-1], 'validate':None,
     'help':'Default section',},
    {'key':'subdict', 'required':True,  'type':{}, 'default':testsubdict, 'validate':None,
     'help':'A required subdictionary',},
    ]

def convertstring(s, typedef):
    """
    Convert a string to a python type
    """
    if not isinstance(s, str):
        # Is is already some non-string python type, so return it
        return s
    if (typedef is None) or (typedef==str) or isinstance(typedef, dict):
        return s.strip()
    seval = ast.literal_eval(s)
    return seval

def template2dict(template, includeoptional=True, ruamel=useruamel,
                  startcomments='', extendedhelp=True):
    """
    Converts the template definitions to a python dictionary
    """
    if ruamel:
        outdict = CommentedMap()
        if startcomments: outdict.yaml_set_start_comment(startcomments)
    else:
        outdict = {}
    for d in template:
        key = d['key']
        val = d['default']
        if d['required'] or includeoptional:
            if isinstance(d['type'], dict):
                outdict[key] = template2dict(val)
            else:
                outdict[key] = val
        if ruamel and len(d['help'])>0:
            helpstr = d['help']
            default = d['default']
            default = {} if isinstance(d['type'], dict) else default 
            if extendedhelp: helpstr += " [Required: "+repr(d['required'])+", default: "+repr(default)+"]"
            outdict.yaml_add_eol_comment(helpstr, key, column=40)
    return outdict
    

def mergedict(indict, dictdefs, validate=True, checkunused=True):
    """
    """
    outdict = {}
    allkeys = list(indict.keys())
    for d in dictdefs:
        key = d['key']
        if (d['required']) and (key not in indict):
            # Stop, we have a problem
            raise ValueError(f'Problem, missing {key} in dictionary')
        # Set the value in outdict
        if not isinstance(d['type'], dict):
            outdict[key] = indict[key] if key in indict else d['default']
        else:
            outdict[key] = mergedict(indict[key], d['default']) if key in indict else template2dict(d['default'])
        # Validate entry (just this entry)
        if validate:
            # Check the value type
            if (d['type'] is not None) and (d['type']) and (not isinstance(outdict[key], d['type'])):
                raise ValueError(f'Type of {key} not correct')
            # Check the validate function
            if (d['validate'] is not None) and (len(inspect.signature(d['validate']).parameters)==1):
                valid, vmesg = splitvalidateout(d['validate'](outdict[key]))
                if not valid:
                    raise ValueError(f'Validation failed for {key}: '+vmesg)
        # Remove the key from allkeys
        if key in allkeys: allkeys.remove(key)

    # Do a global validation
    if validate:
        for d in dictdefs:
            key = d['key']
            if (d['validate'] is not None) and (len(inspect.signature(d['validate']).parameters)==2):
                valid, vmesg = splitvalidateout(d['validate'](outdict[key], outdict))
                if not valid:
                    raise ValueError(f'Global validation failed for {key}: '+vmesg)
                

    # Check for unused keys
    if checkunused and (len(allkeys)>0):
        raise ValueError('These keys were not used: ',allkeys)
    return outdict

def splitvalidateout(vout):
    """
    Splits the output of validate functions
    """
    if isinstance(vout, tuple):
        return vout[0], vout[1]
    else:
        return vout, ''

def mergeconfig(inconfig, dictdefs, validate=True, checkunused=True):
    """
    """
    outdict = {}
    allkeys = list(inconfig.keys())
    for d in dictdefs:
        key = d['key']
        if (d['required']) and (key not in inconfig):
            # Stop, we have a problem
            raise ValueError(f'Problem, missing {key} in dictionary')
        # Set the value in outdict
        if not isinstance(d['type'], dict):
            outdict[key] = inconfig[key] if key in inconfig else d['default']
            outdict[key] = convertstring(outdict[key], d['type'])
        else:
            outdict[key] = mergeconfig(inconfig[key], d['default']) if key in inconfig else template2dict(d['default'])
        # Validate entry (just this entry)
        if validate:
            # Check the value type
            if (d['type'] is not None) and (d['type']) and (not isinstance(outdict[key], d['type'])):
                raise ValueError(f'Type of {key} not correct')
            # Check the validate function
            if (d['validate'] is not None) and (len(inspect.signature(d['validate']).parameters)==1):
                valid, vmesg = splitvalidateout(d['validate'](outdict[key]))
                if not valid:
                    raise ValueError(f'Validation failed for {key}: '+vmesg)
    # Do a global validation
    if validate:
        for d in dictdefs:
            key = d['key']
            if (d['validate'] is not None) and (len(inspect.signature(d['validate']).parameters)==2):
                valid, vmesg = splitvalidateout(d['validate'](outdict[key], outdict))
                if not valid:
                    raise ValueError(f'Global validation failed for {key}: '+vmesg)
    return outdict

def getfilehandle(f, fromstring):
    """
    returns a file handle to f, depending on whether:
    1. f is already a file handle
    2. f is a string containing the data (fromstring=True)
    3. f is a filename
    """
    if isinstance(f, io.IOBase):
        # f is already a file handle
        return f
    if fromstring:
        # Convert f from string to a file handle
        return io.StringIO(f)
    return open(f, 'r')


class inputdict:
    """
    An input dictionary helper class
    """
    def __init__(self, templatedefs, globalhelp=''):
        self.template   = copy.deepcopy(templatedefs)
        self.globalhelp = globalhelp
        return

    def getdefaultdict(self, includeoptional=True):
        return template2dict(self.template, includeoptional=includeoptional)

    def dumpyaml(self, outputfile, includeoptional=True):
        """
        Write the template to a yaml file
        """
        yamldict = template2dict(self.template, includeoptional=includeoptional,
                                 startcomments=self.globalhelp)
        yaml.dump(yamldict, outputfile, **dumperkwargs)
        return

    def dumpini(self, outputfile, includeoptional=True, defautsec='DEFAULT'):
        """
        Write the template to an ini file
        """
        yamldict = template2dict(self.template, includeoptional=includeoptional,
                                 startcomments=self.globalhelp)
        config = configparser.ConfigParser()
        #config.read_dict(yamldict)
        config[defautsec] = {}
        for key, values in yamldict.items():
            if isinstance(values, dict):
                config[key] = values
            else:
                config[defautsec][key] = repr(values)
        config.write(outputfile)
        return
    
    def ingestdict(self, inputdict, validate=True, checkunused=True):
        outdict = mergedict(inputdict, self.template, validate=validate, checkunused=checkunused)
        return outdict

    def ingestyaml(self, yamlfile, fromstring=False, validate=True, checkunused=True):
        """
        Read the dictionary from a yaml file
        """
        f = getfilehandle(yamlfile, fromstring)
        inputdict = Loader(f, **loaderkwargs)
        f.close()
        outdict = mergedict(inputdict, self.template, validate=validate, checkunused=checkunused)
        return outdict

    def ingestini(self, inifile, fromstring=False, validate=True, checkunused=True):
        """
        Read the dictionary from an ini file
        """
        f = getfilehandle(inifile, fromstring)
        config = configparser.ConfigParser()
        config.read_file(f)
        outdict = mergeconfig(config, self.template, validate=validate, checkunused=checkunused)
        return outdict


# ========================================================================
#
# Main
#
# ========================================================================
if __name__ == "__main__":
    inputs = inputdict(testmaininput, globalhelp=testheader)
    inputsini = inputdict(testiniinput) 
    #inputs.printtemplate()

    inputdict = {
        'name':'junk',
        'intval':111,
        'floatval':100,
        'subdict':{'name':'subdictname'},
        'extrakey':'blah',
    }
    outdict = inputs.ingestdict(inputdict, checkunused=False)
    inputs.dumpyaml(sys.stdout)
    print()
    inputsini.dumpini(sys.stdout)
    print()
    #print(inputs.getdefaultdict())
    print(outdict)
    print()
    inputstr="""
name: myname                            # An arbitrary name [Required: True, default: 'myname']
intval: 0                               # An arbitrary integer [Required: True, default: 0]
floatval: 300.123                         # An arbitrary float [Required: False, default: 0.123]
boolval: true                           # An arbitrary boolean [Required: False, default: True]
subdict:                                # A required subdictionary [Required: True, default: {}]
  name: mysubdict                       # An arbitrary name [Required: True, default: 'mysubdict']
  mylist: [1,2,3]                               # An arbitrary list [Required: False, default: [1, 2, 3]]
"""
    outdict = inputs.ingestyaml(inputstr, fromstring=True, checkunused=False)
    print(outdict)
    inputstr="""
[default]
name = myname
intval = 0
floatval = 200.123
boolval = True

[subdict]
name = mysubdict
mylist = [1, 2, 3]
"""

    outdict = inputsini.ingestini(inputstr, fromstring=True, checkunused=False)
    print(outdict)
