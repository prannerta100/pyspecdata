r"""These are general functions that need to be accessible to everything inside
pyspecdata.core.  I can't just put these inside pyspecdata.core, because that
would lead to cyclic imports, and e.g. submodules of pyspecdata can't find
them."""

import os
import sys
def inside_sphinx():
    if len(sys.argv) > 0:
        return os.path.basename(sys.argv[0]) == "sphinx-build"
    else:
        return False
if not inside_sphinx():
    from numpy import *
else:
    # {{{ sphinx dummy objects
    #      there is a better way of doing sphinx dummy objects, but this seems to work
    def exp(*args,**kwargs):
        return None
    def rc(*args,**kwargs):
        return None
    def plot(*args,**kwargs):
        return None
    rcParams = {}
    class rclass (object):
        def __init__(self):
            print("initializing")
            return
        def __getitem__(self,*args,**kwargs):
            return
    r_ = rclass()
    # }}}
import logging
import re

def process_kwargs(listoftuples, kwargs, pass_through=False, as_attr=False):
    '''This function allows dynamically processed (*i.e.* function definitions with `**kwargs`) kwargs (keyword arguments) to be dealt with in a fashion more like standard kwargs.
    The defaults set in `listoftuples` are used to process `kwargs`, which are then returned as a set of values (that are set to defaults as needed).

    Note that having `kwargs` as an explicit argument avoids errors where the user forgets to pass the `kwargs`.
    
    Parameters
    ==========
    kwargs : **dictionary

        The keyword arguments that you want to process.

    listoftuples : list of tuple pairs

        Tuple pairs, consisting of ``('param_name',param_value)``, that give the default values for the various parameters.

    pass_through : bool

        Defaults to False.  If it's true, then it's OK not to process all the kwargs here.
        In that case, the used kwargs are popped out of the dictionary, and you are expected to pass the unprocessed values (in the dictionary after the call) on to subsequent processing.
        Importantly, you should *always* end with a `pass_through`=`False` call of this function, or by passing **kwargs to a standard function in the standard way.
        Otherwise it's possible for the user to pass kwargs that are never processed!
    as_attr : bool, object

        Defaults to False. If not False, it must be an object whose attributes are set to the value of the respective kwargs.

    return : tuple

        It's expected that the output is assigned to variables with the **exact same** names as the string in the first half of the tuples, in the **exact same** order.
        These parameters will then be set to the appropriate values.
    '''
    kwargnames,kwargdefaultvals = list(zip(*listoftuples))
    output = []
    for j,val in enumerate(kwargnames):
        if val in list(kwargs.keys()):
            output.append(kwargs.pop(val))
        else:
            output.append(kwargdefaultvals[j])
    if not pass_through and len(kwargs) > 0:
        raise ValueError("I didn't understand the kwargs:",repr(kwargs))
    if len(output) > 1:
        return tuple(output)
    elif len(output) == 1:
        return output[0]
def autostringconvert(arg):
    if isinstance(arg,str):
        return str(arg)
    else:
        return arg
def check_ascending_axis(u,tolerance = 1e-7,additional_message = []):
    r"""Check that the array `u` is ascending and equally spaced, and return the
    spacing, `du`.  This is a common check needed for FT functions, shears,
    etc.
    
    Parameters
    ----------

    tolerance : double
        The relative variation in `du` that is allowed.
        Defaults to 1e-7.

    additional_message : str
        So that the user can easily figure out where the assertion error is
        coming from, supply some extra text for the respective message.

    Returns
    -------

    du : double
        the spacing between the elements of u
    """
    if isinstance(additional_message, str):
        additional_message = [additional_message]
    du = (u[-1]-u[0])/(len(u)-1.) # the dwell gives the bandwidth, whether or not it has been zero padded -- I calculate this way for better accuracy
    thismsg = ', '.join(additional_message + ["the axis must be ascending (and equally spaced)"])
    assert du > 0, thismsg
    thismsg = ', '.join(additional_message + ["the axis must be equally spaced (and ascending)"])
    assert all(abs(diff(u) - du)/du < tolerance), thismsg# absolute
    #   tolerance can be large relative to a du of ns -- don't use
    #   allclose/isclose, since they are more recent numpy additions
    assert du > 0, thismsg
    return du

def init_logging(level=logging.INFO, filename='pyspecdata.log'):
    "Initialize logging on pyspecdata.log -- do NOT log if run from within a notebook (it's fair to assume that you will run first before embedding)"
    if level.lower() == 'info':
        level=logging.INFO
    elif level.lower() == 'debug':
        level=logging.DEBUG
    FORMAT = "--> %(filename)s(%(lineno)s):%(name)s %(funcName)20s %(asctime)20s\n%(levelname)s: %(message)s"
    log_filename = os.path.join(os.path.expanduser('~'),filename)
    if os.path.exists(log_filename):
        # manually remove, and then use append -- otherwise, it won't write to
        # file immediately
        os.remove(log_filename)
    logging.basicConfig(format=FORMAT,
            filename=log_filename,
            filemode='a',
            level=level,
            )

def strm(*args):
    return ' '.join(map(str,args))

exp_re = re.compile(r'(.*)e([+\-])0*([0-9]+)')
def reformat_exp(arg):
    "reformat scientific notation in a nice latex format -- used in both pdf and jupyter notebooks"
    m = exp_re.match(arg)
    if 'i' not in arg and float(arg) == 0:
        return ''
    if m:
        retstr,pm,fin_numb = m.groups()
        retstr += r'\times 10^{'
        retstr += pm
        #retstr += pm if pm == '-' else ''
        retstr += fin_numb
        retstr += '}'
        return retstr
    else:
        return arg
def complex_str(arg, fancy_format=False, format_code='%.4g'):
    "render a complex string -- leaving out imaginary if it's real"
    retval = [format_code%arg.real]
    if arg.imag != 0.0:
        retval.append((format_code+"i")%arg.imag)
    retval = [reformat_exp(j) for j in retval]
    if len(retval)>1 and retval[1][0] not in '+-':
        retval[1] = '+'+retval[1]
    return ''.join(retval)
def render_matrix(arg, format_code='%.4g'):
    "return latex string representing 2D matrix"
    math_str = r'\begin{bmatrix}'
    math_str += '\n'
    if hasattr(arg.dtype,'fields') and arg.dtype.fields is not None:
        math_str += '\\\\\n'.join([' & '.join([', '.join([r'\text{'+f[0]+r'}\!=\!\text{"'+elem[f[0]]+'"}'
                                                          if isinstance(elem[f[0]],str)
                                                          else r'\text{%s}\!=\!%g'%(f[0],elem[f[0]])
                                                          for f in arg.dtype.descr])# f[0] is the name (vs. size)
                                               for elem in arg[k,:]]) for k in range(arg.shape[0])])
    else:
        math_str += '\\\\\n'.join([' & '.join([complex_str(j, format_code=format_code) for j in arg[k,:]]) for k in range(arg.shape[0])])
    math_str += '\n'
    math_str += r'\end{bmatrix}'
    return math_str
def redim_F_to_C(a):
    r"""the following creates a C array, reversing the *apparent* order of dimensions, while preserving the order in memory"""
    return a.ravel(order='F').reshape(a.shape[::-1], order='C')# 'C' not required, but for clarity
def redim_C_to_F(a):
    "see redim_F_to_C"
    return a.ravel(order='C').reshape(a.shape[::-1], order='F')
def log_fname(logname,fname,dirname):
    with open(logname+'.log','a+',encoding='utf-8') as fp:
        already_listed = False
        fp.seek(0,0)
        for j in fp:
            j = j.replace(r'\ ','LITERALSPACE')
            try:
                f, d = j.split()
            except:
                raise RuntimeError(strm("there seems to be something wrong with your",logname+'.log',"file (in the current directory).  It should consist of one line per file, with each file containing a file and directory name.  Instead, I find a line with the following elements",j.split(),'\n',"You might try deleting the",logname+'.log',"file"))
            f = f.replace('LITERALSPACE',' ')
            d = d.replace('LITERALSPACE',' ')
            if f == fname and d == dirname:
                already_listed = True
                break
        if not already_listed:
            fp.seek(0,os.SEEK_END)# make sure at end of file
            fp.write('%-70s%-50s\n'%(fname.replace(' ','\\ '),dirname.replace(' ','\\ ')))
