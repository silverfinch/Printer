import pyclipper
import copy
import math
import SlicerGeometries
import numpy
from numpy import ma
from matplotlib import pyplot
from matplotlib.patches import Arc
from mpl_toolkits import mplot3d
from stl import mesh
import sys

dontOrder = 0
showNormals = 0
currentZ = 0.5
zIncrement = 0.000001
my_mesh = mesh.Mesh.from_file('Cube_and_ball.stl')
scale = 20
my_mesh.x, my_mesh.y, my_mesh.z = my_mesh.x*scale, my_mesh.y*scale, my_mesh.z#*scale
LINEWIDTH = 1
my_mesh.x += -25.6
my_mesh.y += -25.6
#my_mesh.z -= 20

my_normals = my_mesh.normals
v0 = my_mesh.v0
v1 = my_mesh.v1
v2 = my_mesh.v2
Zcoords = []
#for vector in v0:
#	Zcoords.append(v0[2])
#	Zcoords.append(v1[2])
#	Zcoords.append(v2[2])
#maxZ = max(Zcoords)
#minZ = min(Zcoords)
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
if dontOrder == 1:
	X=[]
	Y=[]
	Z=[]
	U=[]
	V=[]
	W=[]
	lengths=[]
	for i in range(0,len(newLines)):
		line = newLines[i]
		X.append(line.startPoint.X)
		Y.append(line.startPoint.Y)
		Z.append(line.startPoint.Z)
		U.append(line.endPoint.X-line.startPoint.X)
		V.append(line.endPoint.Y-line.startPoint.Y)
		W.append(line.endPoint.Z-line.startPoint.Z)
		if line.magnitude() == 0:
			lengths.append(1)
		else:
			lengths.append(line.magnitude())
	figure = pyplot.figure()
	axes = mplot3d.Axes3D(figure)
	for i in range(0,len(newLines)):
		axes.quiver(X[i],Y[i],Z[i],U[i],V[i],W[i],length=1.0,arrow_length_ratio=0.01/lengths[i])
	pyplot.show()
else:
	if len(newLines) != 0:
		precontour = SlicerGeometries.preContour(newLines)
		contours = [precontour.reorder()[1]]
	else:
		print('No non-filled contours')
	X=[]
	Y=[]
	Z=[]
	U=[]
	V=[]
	W=[]
	lengths = []
	color = []
	try:
		for contour in contours:
			print(len(contour.lines))
	except NameError as e:
		print('Object does not exist at this elevation')
		sys.exit()
	totalLines = 0

#	contours = [contours[5]]

	shells = []
	for i in range(len(contours)):
		otherContours = copy.deepcopy(contours)
		contour = otherContours.pop(i)
		a = contour.makeShell(otherContours,LINEWIDTH,1)
#		for boo in range(0,4):
#			a = a.makeShell(otherContours,LINEWIDTH,1)
		if a!=0:
			shells.append(a)
	for contour in shells:
		i = len(contour.lines)-1
		while i>=0:
			if i==0:
				line1 = contour.lines[len(contour.lines)-1]
				line2 = contour.lines[0]
			else:
				line1 = contour.lines[i-1]
				line2 = contour.lines[i]
			if line1.endPoint.X == line1.startPoint.X:
				slope1 = 'nan'
			else:
				slope1 = (line1.endPoint.Y-line1.startPoint.Y)/(line1.endPoint.X-line1.startPoint.X)
			if line2.endPoint.X == line2.startPoint.X:
				slope2 = 'nan'
			else:
				slope2 = (line2.endPoint.Y-line2.startPoint.Y)/(line2.endPoint.X-line2.startPoint.X)
			if slope1 == slope2:
# if lines are parallel, stretch the first to reach the end of the second,essentially fusing them
				line1.endPoint = line2.endPoint
				contour.lines.remove(line2)
			i-=1

#	contours.extend(shells)
#	print(len(contours))

#	algorithm to determine which contours are holes
	SlicerGeometries.findHoles(contours)
#	for contour in contours:
#		print(contour.level)
#		print("done")

	for i in range(0,len(contours)):
		contour = contours[i]
		vertices = []
		new_lines = []
		for line in contour.lines:
			vertices.append((line.startPoint.X,line.startPoint.Y))
		vertices = tuple(vertices)
#		print(len(vertices))
		pco = pyclipper.PyclipperOffset()
		pco.AddPath(pyclipper.scale_to_clipper(vertices,2**31), pyclipper.JT_MITER, pyclipper.ET_CLOSEDPOLYGON)
		offset = pyclipper.scale_to_clipper(LINEWIDTH,2**31)
		if contour.level%2==0:
			new_vertices = pyclipper.scale_from_clipper(pco.Execute(-offset),2**31)
		else:
			new_vertices = pyclipper.scale_from_clipper(pco.Execute(offset),2**31)
		new_vertices = new_vertices[0]
		for i in range(0,len(new_vertices)):
#			print(len(new_vertices))
			if i==len(new_vertices)-1:
				new_lines.append(SlicerGeometries.SliceLine([[new_vertices[len(new_vertices)-1][0],new_vertices[len(new_vertices)-1][1],currentZ],[new_vertices[0][0],new_vertices[0][1],currentZ]],numpy.array([0,0,0])))
			else:
				new_lines.append(SlicerGeometries.SliceLine([[new_vertices[i][0],new_vertices[i][1],currentZ],[new_vertices[i+1][0],new_vertices[i+1][1],currentZ]],numpy.array([0,0,0])))
		contours.append(SlicerGeometries.closedContour(new_lines,1))

	for contour in contours:
		if contour.shellLevel > 0:# for shell vectors
			for line in contour.lines:
				X.append(line.startPoint.X)
				Y.append(line.startPoint.Y)
				Z.append(line.startPoint.Z)
				U.append(line.endPoint.X-line.startPoint.X)
				V.append(line.endPoint.Y-line.startPoint.Y)
				W.append(line.endPoint.Z-line.startPoint.Z)
				lengths.append(line.magnitude())
				color.append('b')
				totalLines += 1
		else:
			for line in contour.lines:
				#for regular vectors
				X.append(line.startPoint.X)
				Y.append(line.startPoint.Y)
				Z.append(line.startPoint.Z)
				U.append(line.endPoint.X-line.startPoint.X)
				V.append(line.endPoint.Y-line.startPoint.Y)
				W.append(line.endPoint.Z-line.startPoint.Z)
				lengths.append(line.magnitude())
				color.append('g')
				totalLines += 1
#		print('pooped em')
	if showNormals:
		for contour in contours:
			for line in contour.lines:
				#for normals
				X.append((line.startPoint.X+line.endPoint.X)/2)
				Y.append((line.startPoint.Y+line.endPoint.Y)/2)
				Z.append((line.startPoint.Z+line.endPoint.Z)/2)
				U.append(line.normal[0])
				V.append(line.normal[1])
				W.append(line.normal[2])
				lengths.append(numpy.linalg.norm(line.normal))
				color.append('r')
				totalLines +=1
	figure = pyplot.figure()
#	axes.set_zlim3d(0,1)
	ax = figure.add_subplot(111)
#	e1 = Arc((0,0),1,1,angle=0,theta1=0,theta2=90,fill=False)
#	ax.add_patch(e1)
	print(totalLines)
	for i in range(0,totalLines):
		pyplot.quiver(X[i],Y[i],U[i],V[i],scale=1,angles='xy', scale_units='xy', headwidth=1.5, color=color[i])#,arrow_length_ratio=0.01/lengths[i],colors=color[i])
	print(len(contours))
#	print(contours[1].isInside(contours[0]))
#	print(len(contours[0].lines))
	pyplot.show()
#for line in newLines:
#	if (math.fabs(line.startPoint.X-4.0055466)<0.0000001 and math.fabs(line.startPoint.Y+1.4059982)<0.0000001) or (math.fabs(line.endPoint.X-4.0055466)<0.0000001 and math.fabs(line.endPoint.Y+1.4059982)<0.0000001):
#		print('found')
