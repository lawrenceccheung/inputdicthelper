#!/usr/bin/env python3
#
# A helper library to get inputs from a dictionary

# Note: Can download this file from
#   https://raw.githubusercontent.com/lawrenceccheung/inputdicthelper/refs/heads/main/inputdicthelper.py

import copy
import inspect
import sys
import os
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

def stringReplaceDict(s, dreplace):
    """
    Replace strings in s with items in dreplace
    """
    outstr = str(s)
    for k, g in dreplace.items():
        s = '' if g is None else str(g)
        outstr=outstr.replace(k, s)
    return outstr

def checkPathExists(f):
    """
    Check that the file or directory f exists
    """
    if os.path.exists(f):
        return True
    else:
        return (False, f'The path {f} does not exist')


def checkInList(l, x):
    """
    Check that element x is in l
    """
    if x in l:
        return True
    else:
        return (False, repr(x)+' is not one of '+repr(l))

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
            elif isinstance(d['type'], list) and (d['validate']):
                outdict[key] = template2dict(d['validate']) 
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
    if indict is None:
        indict = {}
    allkeys = list(indict.keys())
    for d in dictdefs:
        key = d['key']
        if (d['required']) and (key not in indict):
            # Stop, we have a problem
            raise ValueError(f'Problem, missing {key} in dictionary')
        # Set the value in outdict
        if not isinstance(d['type'], dict):
            # If it's not a dictionary type
            outdict[key] = indict[key] if key in indict else d['default']
        else:
            # For dictionary types
            if d['default'] == {}:
                # Default is empty, pass everything through
                outdict[key] = indict[key]
            else:
                # Else try to merge it in
                outdict[key] = mergedict(indict[key], d['default'], checkunused=checkunused) if key in indict else template2dict(d['default'])
        # Validate entry (just this entry)
        if validate:
            # Check the value type
            if (d['type'] is not None) and (d['type']) and (not isinstance(outdict[key], d['type'])):
                raise ValueError(f'Type of {key} not correct')
            # Check for validating/merging a list
            if isinstance(outdict[key], list) and isinstance(d['validate'], list):
                for i, x in enumerate(outdict[key]):
                    outdict[key][i] = mergedict(x, d['validate'], checkunused=False)
            # Check the validate function
            if (d['validate'] is not None) and (not isinstance(d['validate'], list)) and (len(inspect.signature(d['validate']).parameters)==1):
                valid, vmesg = splitvalidateout(d['validate'](outdict[key]))
                if not valid:
                    raise ValueError(f'Validation failed for {key}: '+vmesg)
        # Remove the key from allkeys
        if key in allkeys: allkeys.remove(key)

    # Do a global validation
    if validate:
        for d in dictdefs:
            key = d['key']
            if (d['validate'] is not None) and (not isinstance(d['validate'], list)) and (len(inspect.signature(d['validate']).parameters)==2):
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

def loadyamlstring(s, replacekey='__replacestrings__'):
    """
    Load a yaml input from  a string and handle any string replacements
    """
    f = io.StringIO(s) 
    yamldicttemp = Loader(f, **loaderkwargs)
    # Do any direct string replacements
    if replacekey in yamldicttemp:
        replacedict = yamldicttemp[replacekey]
        sclean   = s.replace(replacekey+':', '#replacestrings')
        for k, g in replacedict.items():
            sclean = sclean.replace(k+':', '#REPLACED')
        newstr   = stringReplaceDict(sclean, replacedict)
        f2       = io.StringIO(newstr)
        yamldict1 = Loader(f2, **loaderkwargs)
    else:
        newstr   = s
        yamldict1 = yamldicttemp
    return yamldict1


def loadyamlfile(f):
    """
    Load a yaml file, handle any string replacements, and return the dictionary
    """
    with open(f, 'r') as file:
        s= file.read()
        return loadyamlstring(s)
    return


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

    def dumpyaml(self, outputfile, includeoptional=True, toplevel=None):
        """
        Write the template to a yaml file
        """
        yamldict = template2dict(self.template, includeoptional=includeoptional,
                                 startcomments=self.globalhelp)
        if toplevel is None:
            outputyaml = yamldict
        else:
            outputyaml = {}
            outputyaml[toplevel] = yamldict
        yaml.dump(outputyaml, outputfile, **dumperkwargs)
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


