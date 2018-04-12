import SlicerGeometries
import numpy
from matplotlib import pyplot
from matplotlib.patches import Arc
from matplotlib.lines import Line2D
from stl import mesh
import sys
import Infill
from Infill import Line
from Infill import ArcLine

currentZ = 0
zIncrement = 0.000001
my_mesh = mesh.Mesh.from_file('cube.stl')
LINEWIDTH = .5
n=6

xmin = -8.
xmax = 8.
ymin = -8.
ymax = 8.

my_normals = my_mesh.normals
v0 = my_mesh.v0
v1 = my_mesh.v1
v2 = my_mesh.v2

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

infill_path = Infill.infill(contours,'solid',LINEWIDTH,n)
figure = pyplot.figure()
ax = figure.add_subplot(111)
ax.set_xlim([xmin,xmax])
ax.set_ylim([ymin,ymax])

print(len(infill_path))
for obj in infill_path:
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

	if obj.type == 'line':
		#print('line')
		x = [obj.startPoint.X,obj.endPoint.X]
		y = [obj.startPoint.Y,obj.endPoint.Y]
		line = Line2D(x,y,color=c,linewidth=8,solid_capstyle='round')
		ax.add_line(line)
	elif obj.type == 'arc':
		#print('arc')
		arc = Arc(obj.hk,2*obj.r,2*obj.r,angle = 0,theta1 = obj.theta1,theta2 = obj.theta2,fill=False,color=c,linewidth=8)
		ax.add_patch(arc)

pyplot.show()
