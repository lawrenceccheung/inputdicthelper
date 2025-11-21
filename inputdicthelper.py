#!/usr/bin/env python3
#
# A helper library to get inputs from a dictionary

import copy
import inspect

testsubdict = [
    {'key':'name',  'required':True,  'type':str,   'default':'mysubdict', 'validate':None,
     'help':'An arbitrary name',},
]

testmaininput = [
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

def template2dict(template, includeoptional=True):
    outdict = {}
    for d in template:
        key = d['key']
        val = d['default']
        if d['required'] or includeoptional:
            if isinstance(d['type'], dict):
                outdict[key] = template2dict(val)
            else:
                outdict[key] = val
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
                if not d['validate'](outdict[key]):
                    raise ValueError(f'Validation failed for {key}')
        # Remove the key from allkeys
        if key in allkeys: allkeys.remove(key)

    # Do a global validation
    if validate:
        for d in dictdefs:
            key = d['key']
            if (d['validate'] is not None) and (len(inspect.signature(d['validate']).parameters)==2):
                if not d['validate'](outdict[key], outdict):
                    raise ValueError(f'Global validation failed for {key}')
                

    # Check for unused keys
    if checkunused and (len(allkeys)>0):
        raise ValueError('These keys were not used: ',allkeys)
    return outdict

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
    
    def ingestdict(self, inputdict, validate=True, checkunused=True):
        outdict = mergedict(inputdict, self.template, validate=validate, checkunused=checkunused)
        return outdict

    def printtemplate(self):
        for x in self.template:
            print(x)

# ========================================================================
#
# Main
#
# ========================================================================
if __name__ == "__main__":
    inputs = inputdict(testmaininput)
    #inputs.printtemplate()

    inputdict = {
        'name':'junk',
        'intval':111,
        'floatval':100,
        'subdict':{'name':'subdictname'},
        'extrakey':'blah',
    }
    outdict = inputs.ingestdict(inputdict, checkunused=False)
    print(inputs.getdefaultdict())
    print(outdict)
