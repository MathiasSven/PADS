"""SVG.py

Simple generation of SVG-format vector graphics files

D. Eppstein, November 2011.
"""

def _coord(x):
    """String representation for coordinate"""
    return ("%.4f" % x).rstrip("0").rstrip(".")

class SVG:
    def __init__(self, bbox, stream,
               standalone=True, prefix=None, indentation=0):
        """Create a new SVG object, to be written to the given stream.
        If standalone is True or omitted, the SVG object becomes a whole
        XML file; otherwise, it becomes an XML object within a larger XML
        file. If the prefix is nonempty, it is used to distinguish svg tags
        from other tags; a reasonable choice for the prefix value would be
        "s" or "svg". If the indentation is nonzero, it gives a number of
        spaces by which every line of the file is indented.
        
        The bbox argument should be a complex number, the farthest visible
        point from the origin in the positive quadrant. The bounding box
        will become the rectangle between the origin and that point.
        All other methods that specify points should do so using
        complex number coordinates."""
        self.stream = stream
        if prefix:
            self.prefix = prefix + ":"
        else:
            self.prefix = ""
        if standalone:
            self.stream.write('''<?xml version="1.0"?>
<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN" 
  "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">
''')
        self.indentation = indentation
        self.nesting = 0
        br = _coord(bbox.real)
        bi = _coord(bbox.imag)
        self.element('''svg width="%s" height="%s" viewBox="0 0 %s %s"
     xmlns="http://www.w3.org/2000/svg" version="1.1"''' % (br,bi,br,bi),+1)

    def close(self):
        """Output the end of an SVG file."""
        self.element("svg", -1)
        if self.nesting:
            raise Exception("SVG: Unclosed tags")

    def element(self, e, delta=0, unspaced=False, style={}, **morestyle):
        """Output an SVG element.
        The delta argument distinguishes between XML tags that
        open a nested section of the XML file (delta=+1), XML tags
        that close the same section (delta=-1), and XML tags that
        stand alone without anything nested inside them (delta=0).
        Every call with delta=+1 must be matched by a call with delta=-1.
        If the style argument is nonempty, it should be a dictionary
        of style parameters, included within the object; these
        may also be passed as keyword arguments to element.
        If the same keyword is present both in style and as a keyword
        argument, the keyword argument takes priority."""
        if delta < 0:
            self.nesting += delta
        if delta >= 0 or not unspaced:
            output = [" " * (self.indentation + 2*self.nesting), "<"]
        else:
            output = ["<"]
        if delta < 0:
            output.append("/")
        output += [self.prefix, e]
        style = dict(style)
        style.update(morestyle)
        if style:
            output.append(' style="')
            second = False
            for keyword in style:
                if second:
                    output.append("; ")
                second = True
                output += [keyword, ":", style[keyword]]
            output.append('"')
        if delta > 0:
            self.nesting += delta
        elif delta == 0:
            output.append("/")
        output.append(">")
        if delta <= 0 or not unspaced:
            output.append("\n")
        self.stream.write("".join(output))

    def group(self,style={},**morestyle):
        """Start a group of objects, all with the same style"""
        self.element("g", +1, style=style, **morestyle)

    def ungroup(self):
        """End a group of objects"""
        self.element("g", -1)

    def circle(self, center, radius, style={}, **morestyle):
        """Circle with given center and radius"""
        self.element('circle cx="%s" cy="%s" r="%s"' %
                (_coord(center.real), _coord(center.imag), _coord(radius)),
            style=style, **morestyle)

    def rectangle(self, p, q, style={}, **morestyle):
        """Rectangle with corners at points p and q"""
        x = min(p.real,q.real)
        y = min(p.imag,q.imag)
        width = abs((p-q).real)
        height = abs((p-q).imag)
        self.element('rect x="%s" y="%s" width="%s" height="%s"' %
                (_coord(x), _coord(x), _coord(width), _coord(height)),
            style=style, **morestyle)

    def polygon(self, points, style={}, **morestyle):
        """Polygon with corners at the given set of points"""
        pointlist = " ".join(_coord(p.real)+","+_coord(p.imag) for p in points)
        self.element('polygon points="%s"' % pointlist,
                     style=style, **morestyle)

    def polyline(self, points, style={}, **morestyle):
        """Polyline with corners at the given set of points"""
        pointlist = " ".join(_coord(p.real)+","+_coord(p.imag) for p in points)
        self.element('polyline points="%s"' % pointlist,
                     style=style, **morestyle)

    def polycurve(self, points, style={}, **morestyle):
        """Smooth curve through given set of points, excepting first and last.
        The first and last points are used only to determine control points
        to make the curve pass smoothly through the other points.
        Repeat the first three points to make a smooth closed curve.
        
        Uses strain-optimal Hermite interpolation from Yong & Cheng, CAGD 2004,
        https://www.cs.uky.edu/%7Echeng/PUBL/Paper-Geometric-Hermite.pdf"""

        def straincontrol(q0,p0,p1,q1):
            """Spline through q and r with directions controlled by q1 and q2
            Results returned as four Bezier control points"""
            # get initial direction vectors
            v0 = p1-q0
            v1 = q1-p0
            
            # formula from Yong & Cheng Theorem 2 (t0=0 t1=1)
            def dot(r,s):
                return r.real*s.real + r.imag*s.imag
            d = 3*(p1-p0)
            dv0 = dot(d,v0)
            dv1 = dot(d,v1)
            v00 = dot(v0,v0)
            v01 = dot(v0,v1)
            v11 = dot(v1,v1)
            e = 4*v00*v11-v01**2
            a0 = (2*dv0*v11-dv1*v01)/e
            a1 = (2*dv1*v00-dv0*v01)/e

            # convert to Bezier form
            return p0,p0+a0*v0/3,p1-a1*v1/3,p1

        data = ["M"]
        def _point(q):
            data.append(_coord(q.real))
            data.append(_coord(q.imag))
        _point(points[1])
        data.append("C")
        for i in range(1,len(points)-2):
            a,b,c,d = straincontrol(points[i-1], points[i],
                                    points[i+1], points[i+2])
            _point(b)
            _point(c)
            _point(d)
        self.element('path d="%s"' % ' '.join(data), style=style, **morestyle)

    def segment(self, p, q, style={}, **morestyle):
        """Line segment from p to q"""
        self.element('line x1="%s" y1="%s" x2="%s" y2="%s"' % 
                     (_coord(p.real), _coord(p.imag),
                      _coord(q.real), _coord(q.imag)), style=style, **morestyle)

    def arc(self, p, q, r, large=False, style={}, **morestyle):
        """Circular arc from p to q with radius r.
        If the large flag is set true, the arc will cover more than
        half of a circle. The SVG "sweep-flag" is not provided;
        instead, to achieve the same effect, swap p and q."""
        if large:
            large = "1"
        else:
            large = "0"
        r = _coord(abs(r))
        self.element('path d="M %s,%s A %s,%s 0 %s 0 %s,%s"' %
                     (_coord(p.real),_coord(p.imag),r,r,large,
                      _coord(q.real),_coord(q.imag)), style=style, **morestyle)

    def text(self, label, location, style={}, **morestyle):
        """Text label at the given location.
        Caller is responsible for making the label xml-safe."""
        self.element('text x="%s" y="%s"' %
            (_coord(location.real),_coord(location.imag)),
            delta=1, unspaced=True, style=style, **morestyle)
        self.stream.write(label)
        self.element('text', delta=-1, unspaced=True)

# A small color palette chosen to have high contrast
# even when viewed by color-blind readers
class colors:
    none = "none"
    white = "#FFFFFF"
    black = "#000000"
    red = "#BC1E46"
    blue = "#0081CD"
    green = "#009246"
    yellow = "#FEC200"
    magenta = "#CC33CC"
