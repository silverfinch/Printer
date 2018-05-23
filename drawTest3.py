import SlicerGeometries
import PathGen
import numpy
from matplotlib import pyplot
from matplotlib.lines import Line2D
from stl import mesh
from Infill import Line
from Infill import ArcLine
import sys
import time

currentZ = 0.5
zIncrement = 0.000001
my_mesh = mesh.Mesh.from_file('Cube_and_ball.stl')
LINEWIDTH = 1
n = 6
scale = 20
NOZZLEFRONT = 1.22
my_mesh.x = my_mesh.x*scale
my_mesh.y = my_mesh.y*scale

my_mesh.x += -25.6
my_mesh.y += -25.6
my_normals = my_mesh.normals
v0 = my_mesh.v0
v1 = my_mesh.v1
v2 = my_mesh.v2

xlim = [-40,40]
ylim = [-40,40]

faces = []
for i in range(0,len(v0)):
	newFace = SlicerGeometries.Face(v0[i],v1[i],v2[i],my_normals[i])
	faces.append(newFace)
newLines = []
for face in faces:
	if face.isSliced(currentZ,zIncrement) == 1:
		newSliceLine = face.sliceLine(currentZ,zIncrement)
		newLines.append(newSliceLine)
	elif face.isSliced(currentZ,zIncrement) == 2:
		print('Has level face')

if len(newLines) != 0:
		precontour = SlicerGeometries.preContour(newLines)
		contours = precontour.reorder()
else:
	print('No non-filled contours')

try:
	for contour in contours:
		print('Contour')
except NameError as e:
	print('Object does not exist at this elevation')
	sys.exit()

figure = pyplot.figure()
ax = figure.add_subplot(111)

buildpath = PathGen.contourPath(contours,currentZ,LINEWIDTH,NOZZLEFRONT)#this ties everything together
sum = 0
for i in range(0,n):
	sum += len(buildpath[i])
print(sum)
for i in range(0,n):
	for obj in buildpath[i]:
        	if obj.index == 0:
	                c = (0,0,0)
	        elif obj.index == 1:
	                c = (1,0,0)
	        elif obj.index == 2:
	                c = (0,1,0)
	        elif obj.index == 3:
	                c = (0,0,1)
	        elif obj.index == 4:
	                c = (0.5,0.5,0)
	        elif obj.index == 5:
	                c = (0.5,0,0.5)
	        elif obj.index == 6:
	                c = (0,0.5,0.5)
	        else:
       	 	        c = (0.5,0.5,0.5)
	        if obj.isExtruding:
	       	        style = 'solid'
	        else:
 		 	style = ':'
		if True:#obj.index == 5:
			alphaset = 1.
		else:
			alphaset = 0

	      	if obj.type == 'line':
#                print(obj.index)
	                x = [obj.startPoint.X,obj.endPoint.X]
        	        y = [obj.startPoint.Y,obj.endPoint.Y]
                	line = Line2D(x,y,color=c,alpha=alphaset,linewidth=4,solid_capstyle='round',linestyle = style)
                	ax.add_line(line)
#        elif obj.type == 'arc':
#                print('arc')
#                arc = Arc(obj.hk,2*obj.r,2*obj.r,angle = 0,theta1 = obj.theta1,theta2 = obj.theta2,fill=False,color=c,linewidth=16,linestyle=st$
#                ax.add_patch(arc)
#	adding all the lines takes FOREVER, keep that in mind
ax.set_xlim(xlim)
ax.set_ylim(ylim)
pyplot.show()
