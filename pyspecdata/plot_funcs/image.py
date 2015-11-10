from ..general_functions import *
def image(A,x=[],y=[],**kwargs):
    r"Please don't call image directly anymore -- use the image method of figurelist"
    #{{{ pull out kwargs for imagehsv
    imagehsvkwargs = {}
    for k,v in kwargs.items():
        if k in ['black','logscale']:
            imagehsvkwargs[k] = kwargs.pop(k)
    #}}}
    spacing,ax,x_first = process_kwargs([('spacing',1),
        ('ax',gca()),
        ('x_first',False)],kwargs)
    if x_first: # then the first dimension should be the column
        # dimesion (i.e. last)
        if hasattr(A,'dimlabels'):# if I try to use isinstance, I get a circular import
            new_dimlabels = list(A.dimlabels)
            temp = new_dimlabels.pop(0)
            A = A.copy().reorder(new_dimlabels + [temp])
        else:
            A = A.T
    sca(ax)
    setlabels = False
    if hasattr(A,'dimlabels'):
        setlabels = True
        templabels = list(A.dimlabels)
        x_label = templabels[-1]
        try:
            x = list(A.getaxis(x_label))
        except:
            x = r_[0,ndshape(A)[x_label]]
        x_label = A.unitify_axis(x_label)
        templabels.pop(-1)
        y_label = ''
        if len(templabels) == 1:
            y_label = templabels[0]
            try:
                y = list(A.getaxis(y_label))
            except:
                y = r_[0:A.data.shape[A.axn(y_label)]]
            y_label = A.unitify_axis(y_label)
        else:
            while len(templabels)>0:
                y_label += templabels.pop(0)
                if len(templabels)>0:
                    y_label += '$\\otimes$'
        A = A.data
    if type(x) is list:
        x = array(x)
    if type(y) is list:
        y = array(y)
    if len(x)==0:
        x = [1,A.shape[1]]
    else:
        x = x.flatten()
    if len(y)==0:
        y = [1,A.shape[0]]
    else:
        y = y.flatten()
    dx = x[1]-x[0]
    dy = y[1]-y[0]
    myext = (x[0]-dx/2.,x[-1]+dx/2.,y[-1]+dy/2.,y[0]-dy/2.)
    linecounter = 0
    origAndim = A.ndim
    if A.ndim > 2:
        setp(ax.get_yticklabels(),visible = False)
        ax.yaxis.set_ticks_position("none")
    while A.ndim > 2:# to substitude for imagehsvm, etc., so that we just need a ersion of ft
        # order according to how it's ordered in the memory
        # the innermost two will form the image -- first add a line to the end of the images we're going to join up
        tempsize = array(A.shape) # make a tuple the right shape
        if linecounter == 0 and spacing < 1.0:
            spacing = round(prod(tempsize[0:-1])) # find the length of the thing not counting the columns
        tempsize[-2] = 2*linecounter + spacing # all dims are the same except the image row, to which I add an increasing number of rows
        #print "iterate (A.ndim=%d) -- now linecounter is "%A.ndim,linecounter
        linecounter += tempsize[-2] # keep track of the extra lines at the end
        A = concatenate((A,nan*zeros(tempsize)),axis=(A.ndim-2)) # concatenate along the rows
        tempsize = r_[A.shape[0:-3],A.shape[-2:]]
        tempsize[-2] *= A.shape[-3]
        A = A.reshape(tempsize) # now join them up
    A = A[:A.shape[0]-linecounter,:] # really I should an extra counter besides linecounter now that I am using "spacing", but leave alone for now, to be sure I don't cute off data
    if iscomplex(A).any():
        A = imagehsv(A,**imagehsvkwargs)
        retval = imshow(A,extent=myext,**kwargs)
    else:
        retval = imshow(A,extent=myext,**kwargs)
        colorbar()
    if setlabels:
        xlabel(x_label)
        #print y_label
        ylabel(y_label)
    return retval

def imagehsv(A,logscale = False,black = False):
    "This provides the HSV mapping used to plot complex number"
    # compare to http://www.rapidtables.com/convert/color/hsv-to-rgb.htm
    n = 256
    mask = isnan(A)
    A[mask] = 0
    mask = mask.reshape(-1,1)
    intensity = abs(A).reshape(-1,1)
    intensity /= abs(A).max()
    if logscale:
        raise ValueError("logscale is deprecated, use the cropped_log function instead")
    #theta = (n-1.)*mod(angle(A)/pi/2.0,1)# angle in 255*cycles
    if black:
        if black is True:
            V = intensity
        else:
            V = intensity*black + (1.0-black)
        S = 1.0 # always
    else:
        S = intensity
        V = 1.0 # always
    C = V*S
    H = (angle(-1*A).reshape(-1,1)+pi)/2./pi*6. # divide into 60 degree chunks -- the -1 is to rotate so red is at origin
    X = C * (1-abs(mod(H,2)-1))
    m = V-C
    colors = ones(list(A.shape) + [3])
    origshape = colors.shape
    colors = colors.reshape(-1,3)
    rightarray = c_[C, X, zeros_like(X)]
    # http://en.wikipedia.org/wiki/HSL_and_HSV#From_HSV,
    # except that the order was messed up
    thismask = where(H<1)[0]
    # C X 0
    colors[ix_(thismask,[0,1,2])] = rightarray[ix_(thismask,[0,1,2])]
    thismask = where(logical_and(H>=1,
        H<2))[0]
    # X C 0
    colors[ix_(thismask,[1,0,2])] = rightarray[ix_(thismask,[0,1,2])]
    thismask = where(logical_and(H>=2,
        H<3))[0]
    # X 0 C
    colors[ix_(thismask,[1,2,0])] = rightarray[ix_(thismask,[0,1,2])]
    thismask = where(logical_and(H>=3,
        H<4))[0]
    # 0 X C
    colors[ix_(thismask,[2,1,0])] = rightarray[thismask,:]
    thismask = where(logical_and(H>=4,
        H<5))[0]
    # 0 C X
    colors[ix_(thismask,[2,0,1])] = rightarray[thismask,:]
    thismask = where(H>5)[0]
    # C 0 X
    colors[ix_(thismask,[0,2,1])] = rightarray[thismask,:]
    colors += m
    colors *= (n-1)
    if black:
        colors[mask * r_[True,True,True]] = black
    else:
        colors[mask * r_[True,True,True]] = 1.0
    colors = colors.reshape(origshape)
    return uint8(colors.round())

def fl_image(self,A,**kwargs):
    r"""Called as `fl.image()` where `fl` is the `figlist_var`
    object

    Note that this code just wraps the figlist properties, and
    the heavy lifting is done by the `image(` function.
    Together, the effect is as follows:
    - `check_units` converts to human-readable units, and
      makes sure they match the units already used in the plot.
    - if `A` has more than two dimensions, the final dimension in
      `A.dimlabels` is used as the column dimension, and a
      direct-product of all non-column dimensions (a Kronecker
      product, such that the innermost index comes the latest in
      the list `A.dimlabels`) is used as the row dimension. A
      white/black line is drawn after the innermost index used to
      create the direct product is finished iterating.
    - If `A` consists of complex data, then an HSV plot
      (misnomer, actually an HV plot) is used:
      - convert to polar form: $z=\rho \exp(i \phi)$
      - $\phi$ determines the color (Hue)
        - Color wheel is cyclical, like $\exp(i \phi)$
        - red is taken as $\phi=0$, purely real and positive
        - green-blue is $pi$ radians out of phase with red and
          therefore negative real
      - $\rho$ determines the intensity (value)
        - Depending on whether or not `black` is set (either as a
          keyword argument, or `fl.black`, the background will be
          black with high $\rho$ values "lit up" (intended for
          screen plotting) or the background will be white with
          the high $\rho$ values "colored in" (intended for
          printing)
    - If the data type (`dtype`) of the data in `A` is real
      (typically achieved by calling `abs(A)` or
      `A.runcopy(real)`), then `A` is plotted with a colormap and
      corresponding colorbar.
    - If no title has been given, it's set to the name of the
      current plot in the figurelist

    Attributes
    ----------
    A : nddata or numpy array
    x : Optional[double] or Optional[scalar]
        If `A` is a numpy array, then this gives the values along
        the x axis (columns).
        Defaults to the size of the array.
        Not used if `A` is `nddata`.
    y : Optional[double] or Optional[scalar]
        If `A` is a numpy array, then this gives the values along
        the y axis (columns).
        Defaults to the size of the array.
        Not used if `A` is `nddata`.
    x_first : boolean
        Since it's designed to represent matrices, an image plot
        by defaults is "transposed" relative to all other plots.
        If you want the first dimension on the x-axis (*e.g.*, if
        you are plotting a contour plot on top of an image), then set
        `x_first` to `True`. 
    spacing : integer
        Determines the size of the white/black line drawn
        Defaults to 1
    ax : matplotlib Axes
        the Axis object where the plot should go.
    all remaning :
        are passed through to matplotlib `imshow`

    .. code-block:: python
        from pyspecdata import *
        fl = figlist_var()

        t = r_[-1:1:300j]
        x = nddata(t,[-1],['x']).labels('x',t)
        y = nddata(t,[-1],['y']).labels('y',t)

        z = x**2 + 2*y**2
        print "dimlabels of z:",z.dimlabels

        fl.next('image with contours')
        fl.image(z,x_first = True) #  x_first is needed to align
        #                             with the contour plot
        z.contour(colors = 'w',alpha = 0.75)

        fl.next('simple plot') #  just to show that x is the same
        #                         here as well
        fl.plot(z['y':(0,0.01)])

        fl.show('compare_image_contour_150911.pdf')
    """
    firstarg = self.check_units(A,-1,0) # check units, and if need be convert to human units, where x is the last dimension and y is the first
    interpolation,ax = process_kwargs([('interpolation',None),
        ('ax',gca()),
        ],kwargs,pass_through = True)
    if self.black and 'black' not in kwargs.keys():
        kwargs.update({'black':self.black})
    retval = image(A,**kwargs)#just a placeholder for now, will later keep units + such
    if ax.get_title() is None or len(ax.get_title()) == 0:
        title(self.current)
    if interpolation is not None:
        retval.set_interpolation(interpolation)
    return retval