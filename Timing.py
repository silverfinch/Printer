import math
import SlicerGeometries
import PathGen
import Infill
import numpy as np
import sys
from stl import mesh

n=6
h = 0.1
D = 1
filaD = 1.75
bMax = 1.663
limitL = 40
limitR = 130
limitTheta = 2*np.pi*5.4

def findDots(line):
	Ldot = (filaD**2)*np.pi/4/D/h*bMax
	if Ldot>limitL:
		Ldot = limitL
	if not line.isExtruding:
		Ldot = 130
	rmax = np.sqrt(line.startPoint.X**2+line.startPoint.Y**2)
	r = np.sqrt(line.endPoint.X**2+line.endPoint.Y**2)
	if r>rmax:
		rmax = r
	if np.abs(line.endPoint.X - line.startPoint.X)<0.000001:
		thing = 1 + (line.startPoint.X**2/(1-line.startPoint.X**2/rmax**2))
	else:
		m = (line.endPoint.Y-line.startPoint.Y)/(line.endPoint.X-line.startPoint.X)
		thing = 1 + ((line.startPoint.Y-m*line.startPoint.X)**2/(1+m**2-(line.startPoint.Y-m*line.startPoint.X)**2/rmax**2))
	Rdot = Ldot/np.sqrt(thing)
	if np.sqrt(line.endPoint.X**2 + line.endPoint.Y**2)-np.sqrt(line.startPoint.X**2+line.startPoint.Y**2)<0:
		Rdot = -Rdot
	if np.abs(Rdot)>limitR:
		Rdot = Rdot/np.abs(Rdot)*limitR
		Ldot = np.abs(Rdot)*np.sqrt(thing)
	if np.abs(Ldot)<np.abs(Rdot):
		if Rdot<0:
			Rdot = -Ldot
		else:
			Rdot = Ldot
	Thetadot = np.sqrt(Ldot**2-Rdot**2)/rmax
	if (line.startPoint.X*line.endPoint.Y - line.startPoint.Y*line.endPoint.X)<-0.000001:#account for rounding errors here
		Thetadot = -Thetadot
	if np.abs(Thetadot)<0.000001:
		if np.abs(Rdot)>limitR:
			B = np.abs(limitR/Rdot)
			Thetadot *= B
			Ldot *= B
			Rdot *= B
	if np.abs(Thetadot)>limitTheta:
		B = np.abs(limitTheta/Thetadot)
		Thetadot *= B
		Ldot *= B
		Rdot *= B
	return [Ldot,Rdot,Thetadot]
	
def timeLine(startPoint,endPoint,dots):
#	print("reached timeLine")
#	print(startPoint.X,startPoint.Y,endPoint.X,endPoint.Y,dots)
	if dots[1] == 0 and dots[2] == 0:
		return 0
	if np.sqrt(startPoint.X**2 + startPoint.Y**2)==0 or np.sqrt(endPoint.X**2 + endPoint.Y**2)==0:
		dtheta = 0
	else:
#		print('angles')
#		print(np.arctan2(startPoint.Y,startPoint.X),np.arctan2(endPoint.Y,endPoint.X),np.sqrt(endPoint.Y**2 + endPoint.X**2),startPoint.X)
		d = (startPoint.X*endPoint.X + startPoint.Y*endPoint.Y)/np.sqrt(endPoint.X**2 + endPoint.Y**2)/np.sqrt(startPoint.X**2 + startPoint.Y**2)
#		print("d")
#		print(d)
		if d>1:
			d = 1
		if d<-1:
			d = -1
		dtheta = np.arccos(d)
#	if math.isnan(dtheta):
#		print(d)
	if (startPoint.X*endPoint.Y - startPoint.Y*endPoint.X)<-0.000001:#account for rounding errors here
#		print('dtheta oops')
#		print(dtheta)
		dtheta = 2*np.pi-dtheta
#	print('dtheta')
#	print(dtheta)
	if np.abs(dtheta)<0.000001 or np.abs(dots[2])<0.000001:
		dr = np.sqrt(endPoint.X**2 + endPoint.Y**2)-np.sqrt(startPoint.X**2 + startPoint.Y**2)
#		print("dr")
#		print(dr,dtheta)
#		print(dr,dots[1])
		dt = np.abs(dr/dots[1])
	else:
#		print(dtheta,dots[2])
		dt = np.abs(dtheta/dots[2])
#	print(dt,dtheta,dots[2],dr,dots[1])
	return dt


my_mesh = mesh.Mesh.from_file('Cube_and_ball.stl')
currentZ = 0.5
zIncrement = 0.000001
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
#	elif face.isSliced(currentZ,zIncrement) == 2:
#		print('Has level face')

if len(newLines) != 0:
	precontour = SlicerGeometries.preContour(newLines)
	contours = precontour.reorder()
#else:
#	print('No non-filled contours')

try:
	for contour in contours:
		print()
#		print('Contour')
except NameError as e:
	print('Object does not exist at this elevation')
	sys.exit()
finalpath = PathGen.contourPath(contours,currentZ,LINEWIDTH,NOZZLEFRONT)

currentLines = [None for _ in range(0,n)]
currentLimits = [[0,0,0] for _ in range(0,n)]
currentPoint = [None for _ in range(0,n)]
tTotal = 0
maxlen = 0
for j in range(0,n):
	currentLines[j] = finalpath[j][0]
	currentPoint[j] = finalpath[j][0].startPoint
	if maxlen<len(finalpath[j]):
		maxlen = len(finalpath[j])
go = 0
newR = 0
while go<1000000:
	go +=1
	try:
		thetamin = limitTheta
		rmin = limitR
		for j in range(0,n):
			currentLimits[j] = findDots(Infill.Line(currentPoint[j],currentLines[j].endPoint,j,currentLines[j].isExtruding))
#			print(currentLimits[j][1])
			if np.abs(currentLimits[j][2]) < np.abs(thetamin):
				thetamin = currentLimits[j][2]
			if np.abs(currentLimits[j][1]) <= np.abs(rmin):
				if currentLimits[j][2]>=0.000001 and rmin<0.000001:
					rmin = 0
				rmin = currentLimits[j][1]
#				print(rmin)
#		print(rmin)
		tmin = 1000000
		useR = False
		if thetamin<0.000001:
			useR = True
		if useR:
			tmin2 = 1000000
			for j in range(0,n):
				dt2 = timeLine(currentPoint[j],currentLines[j].endPoint,currentLimits[j])
				if dt2<tmin2 and dt2>=0.000000001:#shouldn't advance by zero time, won't get anywhere, sticking program into endless loop
					tmin2 = dt2				
		for j in range(0,n):
			if useR:
				if np.abs(currentLimits[j][2])>=0.000001:
					currentLimits[j][0] = 0
					currentLimits[j][1] = 0
					currentLimits[j][2] = 0
				else:
					currentLimits[j][0] = (np.sqrt(currentLines[j].endPoint.X**2+currentLines[j].endPoint.Y**2)-np.sqrt(currentPoint[j].X**2+currentPoint[j].Y**2))/tmin2
					currentLimits[j][1] = currentLimits[j][0]
					currentLimits[j][2] = 0
			else:
				B = np.abs(thetamin/currentLimits[j][2])
				currentLimits[j][0] *= B
				currentLimits[j][1] *= B
				currentLimits[j][2] *= B
			dt = timeLine(currentPoint[j],currentLines[j].endPoint,currentLimits[j])
			if dt<tmin and dt>=0.000000001:#shouldn't advance by zero time, won't get anywhere, sticking program into endless loop
				tmin = dt
#			print("tmin")
#			print(tmin)
		extrude = False
		for j in range(0,n):
			oldR = newR
			newR = rmin*tmin + np.sqrt(currentPoint[j].X**2 + currentPoint[j].Y**2)
#			print(j,tmin,rmin,thetamin)
			if newR>150.000001:
				print(j,newR,rmin,tmin)
				sys.exit()
			newTheta = thetamin*tmin + np.arctan2(currentPoint[j].Y,currentPoint[j].X)
			newX = newR*np.cos(newTheta)
			newY = newR*np.sin(newTheta)
			print(rmin)
#			print(newX,newY,currentLines[j].endPoint.X,currentLines[j].endPoint.Y)
#			print(np.sqrt((newX-currentLines[j].endPoint.X)**2 + (newY-currentLines[j].endPoint.Y)**2))
			if currentLines[j].isExtruding:
				extrude = True
			if np.sqrt((newX-currentLines[j].endPoint.X)**2 + (newY-currentLines[j].endPoint.Y)**2) < 0.001:
				print("got em")
				currentLines[j] = finalpath[j][finalpath[j].index(currentLines[j])+1]#goes to next line
				currentPoint[j] = currentLines[j].startPoint
			else:
				currentPoint[j] = SlicerGeometries.Point(newX,newY,0)
		if True:#extrude:
			tTotal += tmin
#		print("tTotal")
#		print(tTotal)
#		print(finalpath[j].index(currentLines[j]))
	except IndexError as e:
		if str(e) != "list index out of range":
			raise
		else:
			break
print tTotal
