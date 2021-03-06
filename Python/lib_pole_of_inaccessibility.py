import numpy
import sys
sys.path.append('/d/bandrieu/GitHub/Code/Python/')
from lib_compgeom import get_bounding_box, is_inside_polygon
from PIL import Image, ImageDraw

####################################################################
def make_box(center, ranges, hole=False):
    verts = numpy.zeros((4,2))
    for j in range(2):
        for i in range(2):
            verts[2*j+i,0] = center[0] - ranges[0]*(-1)**i
            verts[2*j+i,1] = center[1] - ranges[1]*(-1)**j
    edges = numpy.array([[0,1],[1,3],[3,2],[2,0]])
    if hole: edges = numpy.flip(edges, axis=1)
    return verts, edges
####################################################################
def sample_domain(verts, edges, samples):
    xymin, xymax = get_bounding_box(verts, xymrg=0.5/float(samples - 1))
    xy = numpy.zeros((samples, samples, 2))
    x = numpy.linspace(xymin[0], xymax[0], samples)
    y = numpy.linspace(xymin[1], xymax[1], samples)
    for j in range(samples):
        for i in range(samples):
            xy[i,j,0] = x[i]
            xy[i,j,1] = y[j]
    return xy.reshape((samples*samples,2))
####################################################################
def minimum_distance_from_boundary(point, verts, edges):
    dist = 1e9
    for e in edges:
        v = verts[e]
        t = v[1] - v[0]
        lt = numpy.hypot(t[0], t[1])
        t = t/lt
        q = point - v[0]
        qt = numpy.dot(q, t)
        if qt < 0.:
            dist = min(dist, numpy.sum(numpy.power(q,2)))
        elif qt > lt:
            dist = min(dist, numpy.sum(numpy.power(point - v[1],2)))
        else:
            dist = min(dist, q[0]**2 + q[1]**2 - qt**2)
    return numpy.sqrt(dist)
####################################################################
def brute_force_PIA_polygon(verts,
                            edges,
                            samples=21):
    dmax = 0.
    xyPIA = numpy.zeros(2)
    for xy in sample_domain(verts, edges, samples):
        if is_inside_polygon(xy, verts, edges):
            d = minimum_distance_from_boundary(xy, verts, edges)
            if d > dmax:
                dmax = d
                xyzPIA = xy
    return xyzPIA, dmax
####################################################################












####################################################################
def threshold_alpha(alpha, seuil=128):
    if alpha < seuil:
        return 0
    else:
        return 255
####################################################################
def image_segmentation_by_alpha(image,
                                seuil_alpha):
    width = image.size[0]
    height = image.size[1]
    npx = width*height
    pixeldata = list(image.getdata())
    visited = numpy.zeros(npx, dtype=bool)
    countvis = 0
    boundary = []
    regions = []
    while countvis < npx:
        for iseed in range(npx):
            if visited[iseed]: continue
            alphaseed = threshold_alpha(pixeldata[iseed][3],seuil_alpha)
            front = [iseed]
            region = []
            while True:
                fronttmp = []
                for ifront in front:
                    j = ifront%width
                    i = (ifront-j)/width
                    visited[ifront] = True
                    countvis += 1
                    region.append(ifront)
                    isonboundary = False
                    neighbors = []
                    if j < width-1:# east
                        neighbors.append(ifront+1)
                    if i > 0:# north
                        neighbors.append(ifront-width)
                    if j > 0:# west
                        neighbors.append(ifront-1)                   
                    if i < height-1:# south
                        neighbors.append(ifront+width)
                    
                    for ingb in neighbors:
                        if threshold_alpha(pixeldata[ingb][3],seuil_alpha) != alphaseed:
                            isonboundary = True
                        else:
                            if not visited[ingb] and ingb not in front and ingb not in fronttmp:
                                fronttmp.append(ingb)
                    if isonboundary: boundary.append([i,j])
                if len(fronttmp) == 0: break
                front = fronttmp
            regions.append(region)
            break
    return regions, boundary
####################################################################
def brute_force_PIA_pixel(image, stride=10, seuil_alpha=128):
    width = image.size[0]
    height = image.size[1]
    npx = width*height
    image.save('/d/bandrieu/Bureau/input.png')
    
    print 'image segmentation by alpha...'
    regions, boundary = image_segmentation_by_alpha(image, seuil_alpha)  
    print 'OK, ',len(regions),' region(s) have been found'
    nb = len(boundary)

    isinterior = numpy.zeros(npx, dtype=bool)
    pixeldata = list(image.getdata())
    for r in regions:
        if threshold_alpha(pixeldata[r[0]][3], seuil=seuil_alpha) > 0:
            isinterior[r] = True
    
    dmax = 0.
    iPIA = int(height/2)
    jPIA = int(width/2)
    diagsqr = height**2 + width**2
    if nb > 0:
        print 'pixel of inaccessibility...'
        for i in range(0,height,stride):
            for j in range(0,width,stride):
                k = i*width + j
                if isinterior[k]:
                    dk = diagsqr
                    for ijb in boundary:
                        dk = min(dk, (ijb[0] - i)**2 + (ijb[1] - j)**2)
                    if dmax < dk:
                        iPIA = i
                        jPIA = j
                        dmax = dk

    modif = numpy.zeros((npx,4), dtype=int)
    for r in regions:
        if isinterior[r[0]]:
            for i in r:
                modif[i,:] = [0,255,0,255]
        else:
            for i in r:
                modif[i,:] = [255,0,0,255]
    for ij in boundary:
        modif[ij[0]*width+ij[1],0:3] = 0

    kmax = iPIA*width + jPIA
    modif[kmax] = [0,0,255,255]
    modif = tuple(map(tuple,numpy.reshape(modif.astype(int), [width*height,4])))
    image.putdata(modif)
    image.save('/d/bandrieu/Bureau/output.png')
    
    draw = ImageDraw.Draw(image)
    draw.ellipse((jPIA-dmax,iPIA-dmax,jPIA+dmax,iPIA+dmax),
                 fill=None, outline='blue')
    #image.show()
    
    
    return iPIA, jPIA, numpy.sqrt(dmax)
####################################################################
