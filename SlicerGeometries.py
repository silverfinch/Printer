import numpy as np
import numpy
import math
import copy
import matplotlib.path as mpltPath

class SliceLine:
	def __init__(self,endpoints,normal):
		self.startPoint = Point(endpoints[0][0],endpoints[0][1],endpoints[0][2])
		self.endPoint = Point(endpoints[1][0],endpoints[1][1],endpoints[1][2])
		self.startPoint.setLine(self)
		self.endPoint.setLine(self)
		self.normal = normal
	
	def __eq__(self,other):
		if self.startPoint.isEqual(other.startPoint) and self.endPoint.isEqual(other.endPoint):
			return True
		else:
			return False

	def __hash__(self):
		return hash(self.startPoint) + hash(self.endPoint)

	def magnitude(self):
		dX = self.startPoint.X-self.endPoint.X
		dY = self.startPoint.Y-self.endPoint.Y
		dZ = self.startPoint.Z-self.endPoint.Z
		return math.sqrt(dX**2 + dY**2 + dZ**2)
	
	def otherEnd(self,point):
		if self.startPoint.isEqual(point):
			return self.endPoint
		elif self.endPoint.isEqual(point):
			return self.startPoint
		else:
			print('Point not on line')

	def flipDirection(self):
		dummy = self.startPoint
		self.startPoint = self.endPoint
		self.endPoint = dummy

	def isInteriorTo(self, other):
		midX = (self.endPoint.X-self.startPoint.X)/2
		midY = (self.endPoint.Y-self.startPoint.Y)/2
#		translation = [normal[0]-midX,normal[1]-midY]# distance from normal to origin
		angle = -math.atan2(self.normal[1],self.normal[0])# transforms endpoints of other line according to transformation matrix
		transformedStart = [other.startPoint.X*math.cos(angle) - other.startPoint.Y*math.sin(angle) + midX,other.startPoint.X*math.sin(angle) + other.startPoint.Y*math.cos(angle) + midY]
		transformedEnd = [other.endPoint.X*math.cos(angle) - other.endPoint.Y*math.sin(angle) + midX,other.endPoint.X*math.sin(angle) + other.endPoint.Y*math.cos(angle) + midY]
		if (transformedStart[1]*transformedEnd[1] <= 0):# if transformed other line has one end above x axis and one end below
			slope = (transformedStart[1]-transformedEnd[1])/(transformedStart[0]-transformedEnd[0])
			zeroX = transformedStart[0] - transformedStart[1]/slope
			if (zeroX > 0):
				return 1
			else:
				return 0
		else:
			return 0

	def distToPoint(self,point):
		vertex = np.array([self.startPoint.X,self.startPoint.Y],dtype=float)
		endpoint = np.array([self.endPoint.X,self.endPoint.Y],dtype=float)
		thePoint = np.array([point.X,point.Y],dtype=float)
		hyp = numpy.linalg.norm(vertex-thePoint)
#		print(vertex-thePoint,vertex-endpoint)
		adj = numpy.dot(vertex-endpoint,vertex-thePoint)/numpy.linalg.norm(vertex-endpoint)
#		print(hyp,adj,numpy.linalg.norm(vertex-endpoint))
		return math.sqrt(hyp**2-adj**2)

	def direction(self):
		vertex = np.array([self.startPoint.X,self.startPoint.Y])
                endpoint = np.array([self.endPoint.X,self.endPoint.Y])
		dir = numpy.cross(vertex,numpy.subtract(endpoint,vertex))
		if dir > 1:
			return 1
		elif dir < 1:
			return -1
		else:
			return 0
	
	def intersectsWith(self,other):
		xa1 = self.startPoint.X
                xa2 = self.endPoint.X
                xb1 = other.startPoint.X
                xb2 = other.endPoint.X
                ya1 = self.startPoint.Y
                ya2 = self.endPoint.Y
                yb1 = other.startPoint.Y
                yb2 = other.endPoint.Y
                angle = np.pi/2-np.arctan2(self.endPoint.Y-self.startPoint.Y,self.endPoint.X-self.startPoint.X)
                #added 90 degrees to make self vertical and avoid infinite slope in other line
                mat = np.matrix([[np.cos(angle),-np.sin(angle),-xa1],[np.sin(angle),np.cos(angle),ya1],[0,0,1]])
                va2 = np.matrix([[xa2],[ya2],[1]]) 
                vb1 = np.matrix([[xb1],[yb1],[1]]) 
                vb2 = np.matrix([[xb2],[yb2],[1]])
                y = np.matmul(mat,va2)[1]
                vb1_ = np.matmul(mat,vb1)
                vb2_ = np.matmul(mat,vb2)
                yint = vb1_[1]-((vb2_[1]-vb1_[1])/(vb2_[0]-vb1_[0]))*vb1_[0]
#		print(y,yint,vb1_[0],vb2_[0])
                if yint>=0 and yint<=y:#theoretical line intersects  
			if (vb1_[0]<=0 and vb2_[0]>=0) or (vb1_[0]>=0 and vb2_[0]<=0):#actual line intersects
				inter = np.matrix([[0],[yint],[1]])
				angle = -angle
		                mat = np.matrix([[np.cos(angle),-np.sin(angle),-xa1],[np.sin(angle),np.cos(angle),ya1],[0,0,1]])
				intersection = np.matmul(mat,inter)
				return [intersection[0],intersection[1]]
		return []
		
	def intersectsWith2(self,other):
	### added this one back since the other one seems to break the infill cookie cutting script.
 		if self.endPoint.X != self.startPoint.X:
 			mA = (self.endPoint.Y-self.startPoint.Y)/(self.endPoint.X-self.startPoint.X)
 			bA = self.endPoint.Y-mA*self.endPoint.X
 			if other.endPoint.X != other.startPoint.X:
 				mB = (other.endPoint.Y-other.startPoint.Y)/(other.endPoint.X-other.startPoint.X)
 				bB = other.endPoint.Y-mB*other.endPoint.X
 				x = (bB-bA)/(mA-mB)
 				if (x>=self.startPoint.X and x<=self.endPoint.X) or (x<=self.startPoint.X and x>=self.endPoint.X):
 					if (x>=other.startPoint.X and x<=other.endPoint.X) or (x<=other.startPoint.X and x>=other.endPoint.X):
 						return [x,mA*x+bA]
 			else:
 				yA = mA*other.endPoint.X + bA
 				if (yA>=self.startPoint.Y and yA<=self.endPoint.Y) or (yA<=self.startPoint.Y and yA>=self.endPoint.Y):
 					if (yA>=other.startPoint.Y and yA<=other.endPoint.Y) or (yA<=other.startPoint.Y and yA>=other.endPoint.Y):
 						return [other.endPoint.X,yA]
 		elif other.endPoint.X != other.startPoint.X:
 			mB = (other.endPoint.Y-other.startPoint.Y)/(other.endPoint.X-other.startPoint.X)
 			bB = other.endPoint.Y-mB*other.endPoint.X
 			yB = mB*self.startPoint.X + bB
 			if (yB>=other.startPoint.Y and yB<=other.endPoint.Y) or (yB<=other.startPoint.Y and yB>=other.endPoint.Y):
 				return [self.endPoint.X,yB]

		return []

class Point:
	def __init__(self,X,Y,Z,atBorder=False):
		self.X = X
		self.Y = Y
		self.Z = Z
		self.atBorder = atBorder

	def __hash__(self):
		return hash(self.X) + hash(self.Y) + hash(self.Z)

	def isEqual(self,point):
		if (np.abs(self.X-point.X)<0.000001 and np.abs(self.Y-point.Y)<0.000001 and np.abs(self.Z-point.Z)<0.000001):
			return 1
		else:
			return 0

	def magnitude(self):
		return np.sqrt(self.X**2 + self.Y**2)

	def otherEnd(self):
		return self.Line.otherEnd

	def setLine(self,line):
		self.Line = line

	def distanceTo(self,other):
		return np.sqrt((self.X-other.X)**2 + (self.Y-other.Y)**2)

class Face:
        def __init__(self, v0, v1, v2, normal):
                self.points = [v0, v1, v2]
                self.maxZ = max(v0[2],v1[2],v2[2])
                self.minZ = min(v0[2],v1[2],v2[2])
		self.normal = numpy.divide(normal,numpy.linalg.norm(normal))

        def isSliced(self, currentZ, zIncrement):
                upperZ = self.maxZ - self.maxZ%(zIncrement/2) + zIncrement/2
                lowerZ = self.minZ - self.minZ%(zIncrement/2)
		Zcoords = [self.points[0][2],self.points[1][2],self.points[2][2]]
		if ((self.normal[0] == 0 and self.normal[1] == 0) and (self.normal[2] == 1 or self.normal[2] == -1)):
			return 2
                elif (currentZ <= upperZ and currentZ >= lowerZ):
                        return 1
                else:
                        return 0

        def sliceLine(self, currentZ, zIncrement):
                if (self.isSliced(currentZ, zIncrement) == 1):
			Zcoords = [self.points[0][2],self.points[1][2],self.points[2][2]]
                	endpoints = []
                	below = []
                	above = []
			normal = np.array([self.normal[0],self.normal[1],0])
			normal = normal/numpy.linalg.norm(normal)
                	for i in range(0,3):# tells which vertices are above the current elevation and which are below
				#print(abs(currentZ-Zcoords[i])<zIncrement)
                        	if (abs(currentZ-Zcoords[i]) < zIncrement/2 or currentZ-Zcoords[i] == -zIncrement/2):
# if vertices are at current elevation, then add those vertices to the slice (including upper bound, which the second condition accounts for)
					newpoint = self.points[i]
                                	newpoint[2] = currentZ# adjusts point Z to match actual current Z, effectively rounding to nearest Z increment
                                	endpoints.append(newpoint)
                        	elif (Zcoords[i] < currentZ):
                               		below.append(self.points[i])
                        	else:
                                	above.append(self.points[i])
                	if (not below or not above):# if no vertices below current Z or no vertices above, then this is a case
# where vertices intersect perfectly with slice and thus have already been added
                        	if (len(endpoints) == 1):
                                	endpoints.append(endpoints[0])#if a single point, make it the start and end of its own infinitesmal line
                        	return SliceLine(endpoints,normal)

			else:
        	                for i in below:
                	                for j in above:
                        	                newpoint = ((currentZ - i[2])/(j[2] - i[2]))*(j-i) + i# linear interpolation between upper and lower po$
                                	        endpoints.append(newpoint)
                        return SliceLine(endpoints,normal)

class preContour:
	def __init__(self,lines):
		self.unorderedLines = lines
		i = len(self.unorderedLines)-1
		while i >= 0:
			a = lines[i]
			#print(i)
			if a.magnitude() == 0:
				self.unorderedLines.pop(i)# removes lines of zero length created when slicing face
				#print('pop')
			i-=1
		lineDic = {}
		for line in lines:
			if line not in lineDic:
				line.flipDirection()
				if line not in lineDic:
					lineDic[line] = line
		self.unorderedLines = list(lineDic.values())

	def reorder(self):
		contours = []
		while (len(self.unorderedLines) != 0):
			orderedLines = []
			R1 = 0
			R2 = 0
			for i in range(0,len(self.unorderedLines)):
				line = self.unorderedLines[i]
				r1 = math.sqrt(line.startPoint.X**2 + line.startPoint.Y**2)
				r2 = math.sqrt(line.endPoint.X**2 + line.endPoint.Y**2)
				if r1<r2:# make it so r1 is always farther end
					line.flipDirection()
					r1 = math.sqrt(line.startPoint.X**2 + line.startPoint.Y**2)
					r2 = math.sqrt(line.endPoint.X**2 + line.endPoint.Y**2)
				if r1>R1:# finds farthest endpoint
					R1 = r1
					R2 = r2
					maxIndex = i
				elif r1==R1:
					if r2>R2:
# if two endpoints are equally far, then choose one with farthest other end
						R2 = r2
						maxIndex = i
			orderedLines.append(self.unorderedLines.pop(maxIndex))
			currentLine = orderedLines[0]# first line has been chosen
			if currentLine.direction() == 1:
				CCW = 1
			else:
				CCW = 0
			for x in range(0,len(self.unorderedLines)):
				found = 0
				choices = []
				choiceIndices = []
				for i in range(0,len(self.unorderedLines)):
					line = self.unorderedLines[i]
					if currentLine.endPoint.isEqual(line.startPoint):
						#print('fine')
						choices.append(line)
						choiceIndices.append(i)# gets choice's index in unorderedLines
						found = 1
						continue
					elif currentLine.endPoint.isEqual(line.endPoint):
						#print('flip')
						line.flipDirection()
						choices.append(line)
						#print(line.startPoint.X,line.startPoint.Y,line.startPoint.Z)
						choiceIndices.append(i)
						found = 1
						continue
					#else:
						#print('failure')
						#print(currentLine.endPoint.X,currentLine.endPoint.Y,currentLine.endPoint.Z,line.startPoint.X,line.startPoint.Y,line.startPoint.Z,line.endPoint.X,line.endPoint.Y,line.endPoint.Z)
				lineAngles = []
				#print(len(choices))
				for choice in choices:
					current = np.array([currentLine.endPoint.X-currentLine.startPoint.X,currentLine.endPoint.Y-currentLine.startPoint.Y,0])
					choiceVector = np.array([choice.endPoint.X-choice.startPoint.X,choice.endPoint.Y-choice.startPoint.Y,0])
					#print(currentLine.startPoint.X,currentLine.startPoint.Y,currentLine.endPoint.X,currentLine.endPoint.Y)
					#print(choice.startPoint.X,choice.startPoint.Y,choice.startPoint.Z,choice.endPoint.X,choice.endPoint.Y,choice.endPoint.Z,choiceIndices)
					cross = np.cross(current,choiceVector)
					dot = np.dot(np.multiply(current,-1),choiceVector)
					angle = np.arccos(dot/currentLine.magnitude()/choice.magnitude())
					if cross[2]<0:
						angle = 2*math.pi - angle
					lineAngles.append(angle)
					#if len(orderedLines) == 25:
						#print(currentLine.startPoint.X,currentLine.startPoint.Y,currentLine.endPoint.X,currentLine.endPoint.Y,choice.startPoint.X,choice.startPoint.Y,choice.endPoint.X,choice.endPoint.Y)
					#print(choice.endPoint.X,choice.endPoint.Y,choice.endPoint.Z)
				#if len(lineAngles)==0:
					#contours.append(closedContour(choices))
					#return contours
				#print(choices[0].startPoint.isEqual(choices[2].startPoint) and choices[0].endPoint.isEqual(choices[2].endPoint))
				#print(lineAngles)
				if len(choices) == 0:
					print('Incomplete contour')
					return [closedContour(orderedLines,0)]
				if CCW:
					bestChoice = np.argmax(lineAngles)
				else:
					bestChoice = np.argmin(lineAngles)
				#print(lineAngles)
				orderedLines.append(choices[bestChoice])
				self.unorderedLines.pop(choiceIndices[bestChoice])
				currentLine = choices[bestChoice]
				#print(len(orderedLines))
				if currentLine.endPoint.isEqual(orderedLines[0].startPoint):
					contours.append(closedContour(orderedLines,0))
					break
				elif len(choices) == 0:
					print('Could not resolve contour')
					
		for contour in contours:
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
# if lines are parallel, stretch the first to reach the end of the second, and remove the second, essentially fusing them
					line1.endPoint = line2.endPoint
					contour.lines.remove(line2)
				i-=1
		return contours

class closedContour:
	def __init__(self,orderedLines,shellLevel):
		self.lines = orderedLines
		self.shellLevel = shellLevel
		self.maxR = 0
		for line in self.lines:
			currentR = np.sqrt(line.startPoint.X**2 + line.startPoint.Y**2)
			if currentR>self.maxR:
				self.maxR = currentR
		self.level = 0

	def isInside(self,other):
		polygon = []
		for line in other.lines:
			polygon.append([line.startPoint.X,line.startPoint.Y])
		path = mpltPath.Path(polygon)
		return path.contains_point([self.lines[0].startPoint.X,self.lines[0].startPoint.Y])

	def makeShell(self,allContoursExceptSelf,LINEWIDTH,n):
		elsePoints = []
		failed = 0
		badLines = []
		contours = allContoursExceptSelf
		for contour in contours:
			for line in contour.lines:
				elsePoints.append(line.startPoint)
				elsePoints.append(line.endPoint)
		for line in self.lines:
			for point in elsePoints:
				if line.distToPoint(point) < LINEWIDTH:
					#print(line.distToPoint(point))
					#print('Not enough room for shell')
					failed += 1
					badLines.append(line)
		#			return 0
		selfPoints = []
		for line in self.lines:
			selfPoints.append(line.startPoint)
			selfPoints.append(line.endPoint)
		for contour in contours:
			for line in contour.lines:
				for point in selfPoints:
					if line.distToPoint(point) < LINEWIDTH:
						#print(line.distToPoint(point))
						#print('Not enough room for shell')
						failed += 1
						badLines.append(line)
		#				return 0
		# now that we've checked there's enough space for a shell, proceed to create it:
		
		points = []
		for i in range(0,len(self.lines)):
			if i == 0:
				line1 = self.lines[len(self.lines)-1]
				line2 = self.lines[0]
			else:
				line1 = self.lines[i-1]
				line2 = self.lines[i]
			normal1 = np.array([line1.normal[0],line1.normal[1]])
			normal2 = np.array([line2.normal[0],line1.normal[1]])
			vector1 = np.array([line1.startPoint.X-line1.endPoint.X,line1.startPoint.Y-line1.endPoint.Y],dtype=float)
			vector2 = np.array([line2.endPoint.X-line2.startPoint.X,line2.endPoint.Y-line2.startPoint.Y],dtype=float)
			unit1 = numpy.divide(vector1,np.linalg.norm(vector1))
			unit2 = numpy.divide(vector2,np.linalg.norm(vector2))
			vertex = np.array([line1.endPoint.X,line1.endPoint.Y])
			dist = np.linalg.norm(np.add(unit1,unit2))
			ratio = n*LINEWIDTH/dist/np.sin(1./2*np.arccos(np.dot(unit1,unit2)))
			print(np.linalg.norm(unit1),np.linalg.norm(unit2))
#			if (np.sin(1/2*np.arccos(np.dot(unit1,unit2))))==0:
#				print('found you!')
			units = numpy.add(unit1,unit2)
			units = numpy.multiply(units,ratio)
			if numpy.dot(units,normal1) < 0:# check if shell goes on exterior side
				units = numpy.multiply(units,-1)
                        bisector = numpy.subtract(vertex,units)
#			print(vertex[0])
			points.append(Point(bisector[0],bisector[1],line1.startPoint.Z))
		newLines = []
		for i in range(0,len(points)):
			if i==0:
				endpoints = [[points[len(points)-1].X,points[len(points)-1].Y,points[len(points)-1].Z],[points[0].X,points[0].Y,points[0].Z]]
			else:
				endpoints = [[points[i-1].X,points[i-1].Y,points[i-1].Z],[points[i].X,points[i].Y,points[i].Z]]
			newLines.append(SliceLine(endpoints,self.lines[i-1].normal))
#		print(failed)
#		print(len(badLines))
		c = closedContour(newLines,1)
#		c.trimShell(self,LINEWIDTH*n)
		return c
		# for n shells, subtract n*unit1 and n*unit2

	def trimShell(self,baseContour,LINEWIDTH):
		i = len(self.lines)-1
		while i>=0:# delete lines too close to base contour
			for contourLine in baseContour.lines:
				print('line')
				vector = np.array([self.lines[i].endPoint.X-self.lines[i].startPoint.X,self.lines[i].endPoint.Y-self.lines[i].startPoint.Y])
				a = contourLine.distToPoint(self.lines[i].startPoint)
				b = contourLine.distToPoint(self.lines[i].endPoint)
				if (a < LINEWIDTH*0.5) and (b < LINEWIDTH*0.5):
					print(contourLine.distToPoint(self.lines[i].startPoint))
					del self.lines[i]
					break
				else:
					if a < LINEWIDTH*0.5:#shortens line from startPoint, withdrawing to safe distance
						unit = np.divide(vector,np.linalg.norm(vector))
						vector = np.multiply(unit,np.linalg.norm(vector)-(LINEWIDTH-a))
						self.lines[i].startPoint.X = self.lines[i].endPoint.X - vector[0]
						self.lines[i].startPoint.Y = self.lines[i].endPoint.Y - vector[1]
					elif b < LINEWIDTH*0.5:#shortens line from endPoint, withdrawing to safe distance
						unit = np.divide(vector,np.linalg.norm(vector))
						vector = np.multiply(unit,np.linalg.norm(vector)-(LINEWIDTH-b))
						self.lines[i].endPoint.X = self.lines[i].startPoint.X + vector[0]
						self.lines[i].endPoint.Y = self.lines[i].startPoint.Y + vector[1]
			i-=1

def findHoles(contours):
	currentLevel = 0
	count = 0
	while(count < len(contours)):
		queue = []
		maxR = []
		for contour in contours:
			if contour.level == currentLevel:
				queue.append(contour)
				maxR.append(contour.maxR)
		if len(queue)==1:
			currentLevel += 1
			count += 1
			break
		currentMax = np.argmax(maxR)
		del maxR[currentMax]
		currentContour = queue.pop(currentMax)
		for contour in queue:
			if contour.isInside(currentContour):
				contour.level = currentLevel+1
		count += 1
