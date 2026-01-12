import unittest
import os, sys

# Get the location of avsitk
scriptpath = os.path.dirname(os.path.realpath(__file__))
idhpath    = os.path.dirname(os.path.dirname(scriptpath))

# Add the root path
sys.path.insert(1, idhpath)

import inputdicthelper as idh

class TestIDH(unittest.TestCase):
    testheader="""
This is a test of the inputdicthelper
These are the inputs

"""
    testsubdict = [
        {'key':'name',  'required':True,  'type':str,   'default':'mysubdict', 'validate':None,
         'help':'An arbitrary name',},
        {'key':'mylist', 'required':False,  'type':[],   'default':[1,2,3,5], 'validate':None,
         'help':'An arbitrary list',},
    ]

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


    def test_ini(self):
        """
        Test the basic module
        """
        inputs    = idh.inputdict(self.testmaininput, globalhelp=self.testheader)
        inputdict = {
            'name':'junk',
            'intval':111,
            'floatval':100,
            'subdict':{'name':'subdictname'},
            'extrakey':'blah',
        }

        # Test ingest from dict
        outdict = inputs.ingestdict(inputdict, checkunused=False)
        self.assertEqual(outdict['name'],     'junk')
        self.assertEqual(outdict['intval'],   111)
        self.assertEqual(outdict['floatval'], 100)
        self.assertEqual(outdict['boolval'],  True)
        self.assertEqual(outdict['subdict']['name'],  'subdictname')
        self.assertEqual(outdict['subdict']['mylist'], [1,2,3,5])
        return

    def test_ingestyaml(self):
        """
        Test the yaml ingestion
        """
        inputs    = idh.inputdict(self.testmaininput, globalhelp=self.testheader)
        # Test ingest from string
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
        self.assertEqual(outdict['name'],     'myname')
        self.assertEqual(outdict['intval'],   0)
        self.assertEqual(outdict['floatval'], 300.123)
        self.assertEqual(outdict['boolval'],  True)
        self.assertEqual(outdict['subdict']['name'],  'mysubdict')
        self.assertEqual(outdict['subdict']['mylist'], [1,2,3])
        return

    def test_ingestini(self):
        """
        Test the ini ingestion
        """
        inputsini = idh.inputdict(self.testiniinput) 
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
        self.assertEqual(outdict['default']['name'],     'myname')
        self.assertEqual(outdict['default']['intval'],   0)
        self.assertEqual(outdict['default']['floatval'], 200.123)
        self.assertEqual(outdict['default']['boolval'],  True)
        self.assertEqual(outdict['subdict']['name'],  'mysubdict')
        self.assertEqual(outdict['subdict']['mylist'], [1,2,3])
        return
        
if __name__ == "__main__":
    unittest.main(verbosity=2)
