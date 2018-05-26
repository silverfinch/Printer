import numpy as np
from SlicerGeometries import Point
import matplotlib.path as mpltPath
import SlicerGeometries

def infill(contours,infill_type,LINEWIDTH,n,NOZZLEFRONT):
	mags = []
	if infill_type == 'solid':
		for contour in contours:
			for line in contour.lines:
				mags.append(line.startPoint.magnitude())
				mags.append(line.endPoint.magnitude())
		max_mag = max(mags)###-LINEWIDTH#distance of outermost infill shell
		num_infill_shells = int(np.floor(max_mag/LINEWIDTH))#leaves excess in the center to be filled with smush
		min_mag = NOZZLEFRONT 
		crowded_shells = int(np.ceil(min_mag/LINEWIDTH))
		infill_path = []
		crowdPoint = []
		arcwidths = []
		for e in range(0,n):
			R = max_mag
#			print(max_mag)
			theta = e*360./n
			for i in range(0,num_infill_shells-crowded_shells):
				R2 = R-LINEWIDTH
				arcwidth = 180./np.pi*2*np.arctan2(LINEWIDTH/2.,R)
				theta2 = theta+(360./n-arcwidth)
#				print("where is it")
#				print(R*np.sin(theta2*np.pi/180))
				# inwards withdrawal
				infill_path.append(ArcLine((0,0),R,theta,theta2,e,False))
				#creates new Arc, stops just at edge of next infill pattern
				infill_path.append(Line(Point(R*np.cos(theta2*np.pi/180),R*np.sin(theta2*np.pi/180),0),Point(R2*np.cos(theta2*np.pi/180),R2*np.sin(theta2*np.pi/180),0),e,False))
				R = R2
				theta = theta2
			arcwidth = 180./np.pi*2*np.arctan2(LINEWIDTH/2.,R)
			theta2 = theta+(360./n-arcwidth)
			infill_path.append(ArcLine((0,0),R,theta,theta2,e,False))
			crowdPoint.append(Point(R*np.cos(theta2*np.pi/180),R*np.sin(theta2*np.pi/180),0))
			#crowding region management:
			if e!=0:
				infill_path.append(Line(crowdPoint[e],Point((R+LINEWIDTH*crowded_shells+8)*np.cos(theta2*np.pi/180),(R+LINEWIDTH*crowded_shells+8)*np.sin(theta2*np.pi/180),0),e,False,True))#increase radius by 8 to see paths clearly on graphic
				idleR = R+LINEWIDTH*crowded_shells+8
			for i in range(1,crowded_shells):
				if e!=0:
					theta=theta2
					theta2 = theta2+360-arcwidths[i-1]
					infill_path.append(ArcLine((0,0),idleR,theta,theta2,e,False,True))
				else:
					R = R-LINEWIDTH
					arcwidth = 180./np.pi*2*np.arctan2(LINEWIDTH/2.,R)
					arcwidths.append(arcwidth)
					theta=theta2
					theta2 = theta2+360-arcwidth
					infill_path.append(Line(Point(crowdPoint[0].X,crowdPoint[0].Y,crowdPoint[0].Z),Point(R*np.cos(theta*np.pi/180),R*np.sin(theta*np.pi/180),0),0,False))
					infill_path.append(ArcLine((0,0),R,theta,theta2,0,False))
					crowdPoint[0].X = R*np.cos(theta2*np.pi/180)
					crowdPoint[0].Y = R*np.sin(theta2*np.pi/180)
			infill_path.append(Line(Point(crowdPoint[0].X,crowdPoint[0].Y,crowdPoint[0].Z),Point(0,0,0),0,False))
		infill_path_final = []
		for item in infill_path:
			if isinstance(item,ArcLine):
#				print('arc')
				R = item.r
				a = 1-0.1/R
				ang_width = 2*np.arctan2(np.sqrt(1-a**2),a)
				theta2_selftemp = item.theta2*np.pi/180 - item.theta1*np.pi/180
		                theta2_selftemp = (theta2_selftemp/2/np.pi-np.floor(theta2_selftemp/2/np.pi))*2*np.pi
				n = theta2_selftemp/ang_width
#				print(n)
				n = int(np.ceil(n))
#				print(n)
				ang_width = theta2_selftemp/n
				for i in range(0,n):
					x1 = R*np.cos(item.theta1*np.pi/180+i*ang_width)
					y1 = R*np.sin(item.theta1*np.pi/180+i*ang_width)
					x2 = R*np.cos(item.theta1*np.pi/180+(i+1)*ang_width)
					y2 = R*np.sin(item.theta1*np.pi/180+(i+1)*ang_width)
					infill_path_final.append(Line(Point(x1,y1,0),Point(x2,y2,0),item.index,False,item.isMove))
			else:
				infill_path_final.append(item)
#	print('final')
#	print(len(infill_path_final))
	elif infill_type == "solid2":
		return None
	return infill_path_final

class ArcLine:
	def __init__(self,hk,r,theta1,theta2,index,isExtruding,isMove=False):
		self.index = index
		self.type = 'arc'
		self.hk = hk
		self.r = r
		self.theta1 = (theta1/360-np.floor(theta1/360))*360
		self.theta2 = (theta2/360-np.floor(theta2/360))*360
		self.isExtruding = isExtruding
		self.isMove = isMove

	def lineIntersect(self,line):
		a = line.startPoint.Y-line.endPoint.Y
		b = line.endPoint.X-line.startPoint.X
		c = b*line.startPoint.Y + a*line.startPoint.X
		d = a**2 * self.r**2 + b**2 * self.r**2 - c**2
		coords = []
		if d<0:
			return coords
		if a != 0:
			y1 = (b*c + a*np.sqrt(d))/(a**2 + b**2)
			y2 = (b*c - a*np.sqrt(d))/(a**2 + b**2)
			x1 = (c-b*y1)/a
			x2 = (c-b*y2)/a

		elif b != 0:
			x1 = (a*c + b*np.sqrt(d))/(a**2 + b**2)
			x2 = (a*c - b*np.sqrt(d))/(a**2 + b**2)
			y1 = (c-a*x1)/b
			y2 = (c-a*x2)/b
		r1 = np.sqrt(x1**2 + y1**2)
		r2 = np.sqrt(x2**2 + y2**2)
		theta1 = np.arctan2(y1,x1)
		theta2 = np.arctan2(y2,x2)
		theta1 = (theta1/2/np.pi-np.floor(theta1/2/np.pi))*2*np.pi
		theta2 = (theta2/2/np.pi-np.floor(theta2/2/np.pi))*2*np.pi
		theta1_temp = theta1 - self.theta1*np.pi/180
		if theta1_temp < 0:
			theta1_temp += 2*np.pi
		theta2_temp = theta2 - self.theta1*np.pi/180
		if theta2_temp < 0:
			theta2_temp += 2*np.pi
		theta2_selftemp = self.theta2*np.pi/180 - self.theta1*np.pi/180
		theta2_selftemp = (theta2_selftemp/2/np.pi-np.floor(theta2_selftemp/2/np.pi))*2*np.pi
		f1 = np.tan(theta1)
		g1 = np.tan(self.theta1*np.pi/180)
		f2 = np.tan(theta2)
		g2 = np.tan(self.theta2*np.pi/180)
		print(theta1_temp,theta2_temp,0,theta2_selftemp)
		#if (np.arctan2((f1-g1)/(1+f1*g1),1)>0) and (np.arctan2((g2-f1)/(1+f1*g2),1)>0):
		#if (theta1 > self.theta1*np.pi/180 and theta1 < self.theta2*np.pi/180):
		if theta1_temp > theta2_temp:#orders angles in increasing fashion
			dummy = theta2_temp
			theta2_temp = theta1_temp
			theta1_temp = dummy
		if theta1_temp > 0 and theta2_selftemp > theta1_temp:
#			print(theta1,self.theta1*np.pi/180,self.theta2*np.pi/180)
			coords.append([r1,theta1])
			print('appended theta1')
#			print(x1,y1)
		#if (np.arctan2((f2-g1)/(1+f2*g1),1)>0) and (np.arctan2((g2-f2)/(1+f2*g2),1)>0):
		#if (theta2 > self.theta1*np.pi/180 and theta2 < self.theta2*np.pi/180):
		if theta2_temp > 0 and theta2_selftemp > theta2_temp:
#			print(theta1,self.theta1*np.pi/180,self.theta2*np.pi/180)
			coords.append([r2,theta2])
			print('appended theta2')
#			print(x2,y2)
		return coords
	
class Line:
	def __init__(self,startPoint,endPoint,index,isExtruding,isMove=False):
		self.index = index
		self.type = 'line'
		self.startPoint = startPoint
		if (not isinstance(startPoint.X,float)) and (not isinstance(startPoint.X,int)):
			startPoint.X = np.asscalar(startPoint.X)
		if (not isinstance(startPoint.Y,float)) and (not isinstance(startPoint.Y,int)):
			startPoint.Y = np.asscalar(startPoint.Y)
		if (not isinstance(startPoint.Z,float)) and (not isinstance(startPoint.Z,int)):
			startPoint.Z = np.asscalar(startPoint.Z)
		if (not isinstance(endPoint.X,float)) and (not isinstance(endPoint.X,int)):
			endPoint.X = np.asscalar(endPoint.X)
		if (not isinstance(endPoint.Y,float)) and (not isinstance(endPoint.Y,int)):
			endPoint.Y = np.asscalar(endPoint.Y)
		if (not isinstance(endPoint.Z,float)) and (not isinstance(endPoint.Z,int)):
			endPoint.Z = np.asscalar(endPoint.Z)
		self.endPoint = endPoint
		self.isExtruding = isExtruding
		self.isMove = isMove
#		if not isinstance(startPoint.X,int):# and isinstance(startPoint.Y,int) and isinstance(startPoint.Z,int) and isinstance(endPoint.X,int) and isinstance(endPoint.Y,int) and isinstance(endPoint.Z,int)):
#			print(startPoint.X)
#			startPoint.X = np.asscalar(startPoint.X)
#			print(type(startPoint.X))
#			raise ValueError("Found a matrix where there should have been an int")

	def __eq__(self,other):
		if self.startPoint.isEqual(other.startPoint) and self.endPoint.isEqual(other.endPoint):
			return True
		else:
			return False

	def __hash__(self):
		return hash(self.startPoint) + hash(self.endPoint)

	def lineIntersect(self,line):
		return line.intersectsWith(self)

	def lineIntersect2(self,line):
		return line.intersectsWith2(self)

	def direction(self):
                vertex = np.array([self.startPoint.X,self.startPoint.Y,0])
                endpoint = np.array([self.endPoint.X,self.endPoint.Y,0])
		vertex = np.array([vertex[0].item(),vertex[1].item(),0])
		endpoint = np.array([endpoint[0].item(),endpoint[1].item(),0])
                dir = np.cross(vertex,np.subtract(endpoint,vertex))[2]
                if dir > 0:
                        return 1
                elif dir < 0:
                        return -1
                else:
                        return 0

	def radius(self):
		return np.sqrt(self.startPoint.X**2 + self.startPoint.Y**2)

def cookieCutter(infill,contours):
	i = len(infill)-1
	while i >= 0:
		#print(i,len(infill))
		for contour in contours:
			for line in contour.lines:
				thing = infill[i]
				if thing.isMove:
					continue
#				print('index')
#				print(thing.index,i)
				coords = thing.lineIntersect2(line)
				if len(coords)!=0:
					if isinstance(thing,Line):
						x = coords[0]
						y = coords[1]
						replace1 = Line(thing.startPoint,Point(x,y,0,True),thing.index,thing.isExtruding)
						replace2 = Line(Point(x,y,0,True),thing.endPoint,thing.index,thing.isExtruding)
						del infill[i]

						infill.insert(i,replace2)
						infill.insert(i,replace1)
					if isinstance(thing,ArcLine):
#						print('is arc')
						if len(coords) == 2:
#							print('foolde dyou')
							#if np.arctan2((np.tan(coords[0][1])-np.tan(coords[1][1]))/(1+np.tan(coords[0][1])*np.tan(coords[1][1])),1)>0:
							replace1 = ArcLine(thing.hk,thing.r,thing.theta1,coords[0][1],thing.index,thing.isExtruding)
							replace2 = ArcLine(thing.hk,thing.r,coords[0][1],coords[1][1],thing.index,thing.isExtruding)
							replace3 = ArcLine(thing.hk,thing.r,coords[1][1],thing.theta2,thing.index,thing.isExtruding)
							#else:
							#	replace1 = ArcLine(thing.hk,thing.r,thing.theta1,coords[0][1],thing.index+1,thing.isExtruding)
							#	replace2 = ArcLine(thing.hk,thing.r,coords[0][1],coords[1][1],thing.index+2,thing.isExtruding,True)
							#	replace3 = ArcLine(thing.hk,thing.r,coords[1][1],thing.theta2,thing.index+3,thing.isExtruding,True)
							del infill[i]
							infill.insert(i,replace3)
							infill.insert(i,replace2)
							infill.insert(i,replace1)
						else:
							replace1 = ArcLine(thing.hk,thing.r,thing.theta1,coords[0][1],thing.index,thing.isExtruding)
							replace2 = ArcLine(thing.hk,thing.r,coords[0][1],thing.theta2,thing.index,thing.isExtruding)
							del infill[i]
							infill.insert(i,replace2)
							infill.insert(i,replace1)
#							print('you fool')
		i -= 1
#	maxlevel = 0
#	contour_by_level = []
#	for contour in contours:
#		if maxlevel<contour.level:
#			maxlevel = contour.level
#	for num in range(0,maxlevel+1):
#		contour_by_level.append([])
#	print(len(contour_by_level))
#	for contour in contours:# sort contours into lists according to level
#		contour_by_level[contour.level].append(contour)
#	for num in range(0,maxlevel+1):
#		for contour in contour_by_level[num]:
#			if num%2==0:
#				doExtrude = 
#	doExtrude = False
#	for item in infill:
#		if item.alternate:
#			doExtrude = not doExtrude
#		item.isExtruding = doExtrude
		#print(item.isExtruding)
	for item in infill:
		if item.isMove:
			continue
		if isinstance(item,Line):
			midpoint = [(item.endPoint.X+item.startPoint.X)/2,(item.endPoint.Y+item.startPoint.Y)/2]
		elif isinstance(item,ArcLine):
#			if item.r>5:
#				print('here')
			midtheta = (item.theta1+item.theta2)/2
			midpoint = [item.r*np.cos(midtheta),item.r*np.sin(midtheta)]
		maxLevel = 0
		filled = False
		SlicerGeometries.findHoles(contours)
		for contour in contours:
			polygon = []
                	for line in contour.lines:
                        	polygon.append([line.startPoint.X,line.startPoint.Y])
                	path = mpltPath.Path(polygon)
    	           	if (path.contains_point(midpoint)) and contour.level >= maxLevel:
				maxLevel = contour.level
				filled = True
		count = 0
		if filled and maxLevel%2==0:
			item.isExtruding = True
			count += 1
		elif filled:
			item.isExtruding = False
