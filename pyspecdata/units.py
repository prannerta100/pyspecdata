from numpy import *
import re
from itertools import chain

class units (object):
    r"""Each instance of this object stores a numerical representation of a single set of units, and there are routines to set units by
    (*i.e.* :func:`parsing <pyspecdata.units.parse>`) strings to units
    and routines to convert units to an
    :func:`str <pyspecdata.units.part>` representation.

    At its core, the units are represented by three numpy structured arrays per instance:
    one for the coefficients in terms of base units,
    one for the order of magnitude used to determine any prefixes added to the base units,
    and one for any scaling factors needed to convert to base units.

    An array of these structured arrays can be converted into a row
    vector with ``.view((float16,len(base_dtype.names)))``.
    "Base Units" here are the same as SI base units **except** that it uses g instead of kg (so we can do  the prefixes correctly), and we have added rad.
    """
    def __init__(self,*args):
        "If an argument is passed, it's passed to :func:`parse <pyspecdata.units.parse>`"
        self.base_dtype = dtype(map(lambda x: (x, float16), ['m', 'g', 's', 'A',
            'K', 'mol', 'cd', 'rad']))
        self.oom_names =   ['T' , 'G' , 'M' , 'k' , 'c' , 'm' , u'\u03bc' , 'n' , 'p']
        oom_values =      r_[12 , 9   , 6   , 3   , -2  , -3  , -6     , -9  , -12]
        self.oom_dict = dict(zip(self.oom_names,oom_values))
        self.unit_vec = zeros(1,dtype = self.base_dtype)
        self.prefix_vec = zeros(1,dtype = self.base_dtype)
        # {{{ load the base units into the derived units dictionary
        identity_matrix = eye(len(self.base_dtype.names),dtype=float16).view(self.base_dtype)
        zero_matrix = zeros(len(self.base_dtype.names),dtype=self.base_dtype)
        self.derived_units = {}
        self.derived_units_oom = {}
        for n,j in enumerate(self.base_dtype.names):
            self.derived_units[j] = identity_matrix[n]
            self.derived_units_oom[j] = zero_matrix[n]
        # }}}
        if len(args) > 0:
            if len(args) > 1:
                raise ValueError("only one argument allowed")
            self.parse(args[0])
        return
    def load_derived(self):
        r"""Parses and loads a series of definitions for derived units.

        It uses definition list to determine a derived dtype vector, which is
        larger than the base dtype vector.

        Then, (not yet done), based on the dictionary that this generates, it
        will generate a matrix that converts from the derived dtype vector to
        the base dtype vector."""
        definition_list = [('T','kg/A*s^2')]
        self.derived_dtype = dtype(map(lambda x: (x, float16), self.derived_units.keys()))
        # {{{ this is a lot of calculation that can be saved in the future by loading from a file
        temp = units()
        for j in definition_list:#, ('N','kg*m/s^2'), ('C','A*s'),]:
            thisunit,thismath = j
            temp.parse(thismath)
            self.derived_units[thisunit] = temp.unit_vec
            self.derived_units_oom[thismath] = temp.prefix_vec
        # }}}
        return
    def parse(self,in_str, verbose=True):
        u"""Take `in_str` and parse it as a unit or series of units, and set the units associated with the current instance to the result.

        Addition, subtraction, and parentheses are not allowed, and we define a
        non-standard order of operations, as follows:

        #. ``\\\\mu`` (including a trailing space) and ``u`` are converted to the utf-8 equivalent (\u03bc)
        #. ``...^-0.125`` any number is assumed to be part of the exponent, and only numbers are allowed.
        #. ``*`` multiplication
        #. a space also represents multiplication
        #. ``.../...`` comes **after** all other operations, as is typical for single-line text
        #. ``sqrt(...)`` comes "last" in the sense that we take care of everything both inside and outside the sqrt first, before applying the sqrt.
        
        At this point, I use split to break up according to the order of operations, assign powers to each, and determine the prefix.
        However, I'm currently only using base units, and I will eventually want to use derived units as well.
        """
        in_str = unicode(in_str)
        mu_re = re.compile(r'\bu|\\mu ')
        in_str = mu_re.sub(u'\u03bc',in_str)
        working_list = [in_str]
        unit_powers = [1]
        for op_num,this_regexp in enumerate([r'\bsqrt\((.*)\)',
            r'(?:\*| *)',
            r'/',
            r'(?:\^|\*\*)([\-\.0-9]+)', ]):# the first in the order of operations are actually inside
            last_len = 0
            while len(working_list) > last_len:
                last_len = len(working_list)
                working_list = map(lambda x: re.split(this_regexp,x,maxsplit = 1),
                        working_list)
                if verbose: print "broken according to",this_regexp
                new_unit_powers = [[unit_powers[j]]*len(working_list[j]) for j
                        in range(len(working_list))]
                for j,v in enumerate(new_unit_powers):
                    if len(v) > 1:# then, it split this element
                        if op_num == 0:
                            new_unit_powers[j][1] = float(new_unit_powers[j][1]) / 2.0 # middle element is inside parens, and goes to half power
                        elif op_num == 1:
                            pass # for multiplication, we don't need to do anything
                        elif op_num == 2:
                            if verbose: print "unit powers before messing:",new_unit_powers
                            new_unit_powers[j][1] *= -1 # second half of this expression becomes negative
                            # {{{ all following elements are also negative
                            if j+1 < len(new_unit_powers):
                                if verbose: print "setting all subsequent to -1"
                                for k in range(j+1,len(new_unit_powers)):
                                    new_unit_powers[k] = map(lambda x: -1*x,new_unit_powers[k])
                            # }}}
                        elif op_num == 3:
                            if verbose: print "unit powers before messing:",new_unit_powers
                            if verbose: print "working list before messing",working_list
                            new_unit_powers[j][0] *= float(working_list[j][1])
                            working_list[j].pop(1)
                            new_unit_powers[j].pop(1)
                            if verbose: print "unit power after messing:",new_unit_powers
                            if verbose: print "working list after messing:",working_list
                        working_list[j] = filter(lambda x: len(x)>0,working_list[j])
                        new_unit_powers[j] = [new_unit_powers[j][k] for k in
                                range(len(working_list[j])) if
                                len(working_list[j][k]) > 0]
                unit_powers = new_unit_powers
                if verbose: print working_list
                if verbose: print unit_powers
                working_list = list(chain(*working_list))
                unit_powers = list(chain(*unit_powers))
        if verbose: print "Final result:"
        if verbose: print unit_powers
        oom_regexp = r'^('+'|'.join(self.oom_names)+'){0,1}'+'('+'|'.join(self.derived_units.keys())+r')$'
        if verbose: print "oom_regexp",repr(oom_regexp)
        oom_regexp = re.compile(oom_regexp)
        if verbose: print working_list
        if verbose: print "breaks into:"
        self.unit_vec = zeros(1,dtype = self.base_dtype)
        self.prefix_vec = zeros(1,dtype = self.base_dtype)
        for n,j in enumerate(working_list):
            m = oom_regexp.match(j)
            if m:
                prefix,unit = m.groups()
                un_np = zeros(1,dtype = self.base_dtype)
                oom_np = zeros(1,dtype = self.base_dtype)
                un_np[unit] = unit_powers[n]
                if prefix is not None:
                    oom_np[unit] = self.oom_dict[prefix]
                if verbose: print r_[un_np,oom_np] 
                self.unit_vec.view(float16)[:] += un_np.view(float16)
                self.prefix_vec.view(float16)[:] += oom_np.view(float16)
            elif j=='1':
                pass #don't do anything
            else:
                raise ValueError(' '.join(["couldn't match:",repr(j),"to a unit"]))
        if verbose: print "leading to:"
        if verbose: print r_[self.unit_vec,self.prefix_vec] 
        return self
    def str(self,number):
        r"""Give a string that prints `number`, which has the units
        given by the current instance of the class.
        Choose the simplest possible expression for the units.

        When printing, we have a matrix that give all our "representation" units,
        and we use a pseudoinverse to give us the simplest possible expression of our units.
        (This is assuming that all derived units are defined in terms of powers
        greater than or equal to 1 of the base units, because powers of
        magnitude less than 1 would complicate things by allowing us to reduce
        the norm by spreading across several derived units -- in that case, we
        might want to add a threshold before taking
        the pinv.)

        Currently,  I am only giving a method for printing in the base units.

        Also, I will want to use number in order to adjust the prefix(es) of the units.
        """
        prefixes = self.oom_dict.keys() + ['']
        ooms = self.oom_dict.values() + [0]
        def oom_tostr(x):
            return prefixes[ooms.index(x)]
        vec_to_render = self.unit_vec
        def render_string(nonzero_fields,inverse = 1):
            if len(nonzero_fields) == 0:
                return ''
            # {{{ reduce to only the non-zero fields
            reduced_unit_powers = inverse * self.unit_vec[nonzero_fields].view(float16)
            reduced_unit_power_strings = []
            for j in reduced_unit_powers:
                if j == 1:
                    reduced_unit_power_strings.append('')
                else:
                    reduced_unit_power_strings.append('^{:g}'.format(j))
            reduced_prefixes = map(oom_tostr,self.prefix_vec[nonzero_fields].view(float16))
            print "reduced unit powers",reduced_unit_powers,"for",nonzero_fields,"with prefixes",reduced_prefixes
            retval = ' '.join(map(lambda x: x[0]+x[1]+x[2],zip(reduced_prefixes,nonzero_fields,reduced_unit_power_strings)))
            # }}}
            return retval
        # {{{ render a numerator and denominator
        temp = render_string([j for j in self.unit_vec.dtype.names if self.unit_vec[j] > 0])
        if len(temp) > 0:
            retval = temp
            temp = render_string([j for j in self.unit_vec.dtype.names if self.unit_vec[j] < 0],inverse = -1)
            if len(temp) > 0:
                retval = retval + '/' + temp
        else:
            # if there is no numerator, just render all the negative exponents as such
            retval = render_string([j for j in self.unit_vec.dtype.names if self.unit_vec[j] < 0])
        # }}}
        return retval
    def __mul__(self,arg):
        retval = units()
        retval.unit_vec.view(float16)[:] = self.unit_vec.view(float16) + arg.unit_vec.view(float16)
        retval.prefix_vec.view(float16)[:] = self.prefix_vec.view(float16) + arg.prefix_vec.view(float16)
        return retval
    def __pow__(self,thisnumber):
        retval = units()
        retval.unit_vec.view(float16)[:] = self.unit_vec.view(float16) * thisnumber
        retval.prefix_vec = self.prefix_vec.copy()
        return retval
    def __ldif__(self,arg):
        if arg != 1:
            raise ValueError("left division of units only supported with 1")
        return self**-1
    def __div__(self,arg):
        retval = units()
        retval.unit_vec.view(float16)[:] = self.unit_vec.view(float16) - arg.unit_vec.view(float16)
        retval.prefix_vec.view(float16)[:] = self.prefix_vec.view(float16) - arg.prefix_vec.view(float16)
        return retval
