import numpy as np
import copy
import Infill
from Infill import Line
import SlicerGeometries
import pyclipper
from collections import OrderedDict

plateRad = 150
n = 6

def contourPath(contours,currentZ,LINEWIDTH,NOZZLEFRONT):
	buildpath = []
	SlicerGeometries.findHoles(contours)
	newcontours = []
	infillcontours = []
	for i in range(0,len(contours)):
                contour = contours[i]
                vertices = []
                new_lines = []
                for line in contour.lines:
                        vertices.append((line.startPoint.X,line.startPoint.Y))
                vertices = tuple(vertices)
#               print(len(vertices))
                pco = pyclipper.PyclipperOffset()
                pco.AddPath(pyclipper.scale_to_clipper(vertices,2**31), pyclipper.JT_MITER, pyclipper.ET_CLOSEDPOLYGON)
                offset = pyclipper.scale_to_clipper(LINEWIDTH/2,2**31)
                if contour.level%2==0:
                        new_vertices = pyclipper.scale_from_clipper(pco.Execute(-offset),2**31)
                else:
                        new_vertices = pyclipper.scale_from_clipper(pco.Execute(offset),2**31)
                new_vertices = new_vertices[0]
                for i in range(0,len(new_vertices)):
#                       print(len(new_vertices))
                        if i==len(new_vertices)-1:
                                new_lines.append(SlicerGeometries.SliceLine([[new_vertices[len(new_vertices)-1][0],new_vertices[len(new_vertices)-1][1],currentZ],[new_vertices[0][0],new_vertices[0][1],currentZ]],np.array([0,0,0])))
                        else:
                                new_lines.append(SlicerGeometries.SliceLine([[new_vertices[i][0],new_vertices[i][1],currentZ],[new_vertices[i+1][0],new_vertices[i+1][1],currentZ]],np.array([0,0,0])))
                newcontours.append(SlicerGeometries.closedContour(new_lines,1))

	for contour in newcontours:
		for line in contour.lines:
			buildpath.append(Line(line.startPoint,line.endPoint,0,True))

	replace1 = []
	replace2 = []
	where = []
	for i in range(0,len(buildpath)):
		line = buildpath[i]
#		print(line.startPoint.X,line.startPoint.Y,line.endPoint.X,line.endPoint.Y)
		for j in range(0,n):
			x = plateRad*np.cos((j+1)*np.pi*2/n)
			y = plateRad*np.sin((j+1)*np.pi*2/n)
			radial = SlicerGeometries.SliceLine([[0,0,0],[x,y,0]],[0,0,0])
#			print(radial.startPoint.X,radial.startPoint.Y,radial.endPoint.X,radial.endPoint.Y)
			a = radial.intersectsWith(line)
			if len(a)!=0:
#				print(line.startPoint.X,line.startPoint.Y,line.endPoint.X,line.endPoint.Y)
#				print(a)
				if j != n-1:
					replace1.append(Line(line.startPoint,SlicerGeometries.Point(a[0],a[1],0),j,True))
					replace2.append(Line(SlicerGeometries.Point(a[0],a[1],0),line.endPoint,j+1,True))
				else:
					replace1.append(Line(line.startPoint,SlicerGeometries.Point(a[0],a[1],0),j,True))
					replace2.append(Line(SlicerGeometries.Point(a[0],a[1],0),line.endPoint,0,True))
				where.append(i)
	for g in range(len(where)-1,-1,-1):
		i = where[g]
		del buildpath[i]
		buildpath.insert(i,replace1[g])
		buildpath.insert(i+1,replace2[g])
	for line in buildpath:
		c = np.arctan2((line.startPoint.Y+line.endPoint.Y)/2,(line.startPoint.X+line.endPoint.X)/2)
		if c<0:
			c += 2*np.pi
		b = int(np.floor(c/(2*np.pi/n)))
#		b = int(2*np.pi/np.arctan2(line.startPoint.Y,line.startPoint.X))
		line.index = b
	nozzlelines = [[] for _ in range(0,n)]
	for line in buildpath:
		nozzlelines[line.index].append(line)
	nozzlegroups = [[] for _ in range(0,n)]
	CCW = [[] for _ in range(0,n)]
	CW = [[] for _ in range(0,n)]
	for j in range(0,len(nozzlelines)):
		for line in nozzlelines[j]:
			if line.direction()<0:
				CW[j].append(line)#separates CW lines
			else:
				CCW[j].append(line)#separates CCW lines
	for j in range(0,len(nozzlelines)):
		while len(CW[j])!=0:
			max = CW[j][0]
			for line in CW[j]:
				if Line(SlicerGeometries.Point(line.startPoint.X,line.startPoint.Y,0),SlicerGeometries.Point(max.startPoint.X,max.startPoint.Y,0),0,True).direction()<0:
					max = line
			currentCW = max
			currentListCW = []
			currentListCW.append(max)
			CW[j].remove(max)
			found = True
			while found:
				found = False
				for line in CW[j]:
					if line.startPoint.isEqual(currentCW.endPoint):
						currentListCW.append(line)
						currentCW = line
						CW[j].remove(line)
						found = True
						break
			nozzlegroups[j].append(Group(currentListCW,j,0))
		for group in nozzlegroups[j]:
			group.lines.reverse()
			for line in group.lines:
				dummy = line.startPoint
				line.startPoint = line.endPoint
				line.endPoint = dummy

		while len(CCW[j])!=0:
			min = CCW[j][0]
			for line in CCW[j]:
				if Line(SlicerGeometries.Point(min.startPoint.X,min.startPoint.Y,0),SlicerGeometries.Point(line.startPoint.X,line.startPoint.Y,0),0,True).direction()<0:
					min = line
			currentCCW = min
			currentListCCW = []
			currentListCCW.append(min)	
			CCW[j].remove(min)
			found = True
			while found:
				found = False
#				print(np.arctan2(currentCCW.startPoint.Y,currentCCW.startPoint.X))
				for line in CCW[j]:
					if line.startPoint.isEqual(currentCCW.endPoint):
						currentListCCW.append(line)
						currentCCW = line
						CCW[j].remove(line)
						found = True
						break
			nozzlegroups[j].append(Group(currentListCCW,j,1))
#	for j in range(0,len(nozzlelines)):
#		nozzle = nozzlelines[j]
#		currentList = []
#		dir = 0
#		for i in range(0,len(nozzle)):
#			line = nozzle[i]
#			a = np.array([line.startPoint.X,line.startPoint.Y,0])
#                       b = np.array([line.endPoint.X-line.startPoint.X,line.endPoint.Y-line.startPoint.Y,0])
#                       a = np.array([a[0].item(),a[1].item(),0])
#                       b = np.array([b[0].item(),b[1].item(),0])
#                       c = np.cross(a,b)
#			if c[2]>=0:
#				d=0
#			else:
#				d=1
#			if i != 0:
#                                if not nozzle[i-1].endPoint.isEqual(nozzle[i].startPoint):
#                                        print(nozzle[i].endPoint.X-nozzle[i+1].startPoint.X)
#					
#                                        nozzlegroups[j].append(Group(currentList,j,dir))
#                                        currentList = []
#			f = np.arctan2(line.endPoint.Y,line.endPoint.X)/(2*np.pi/n)
#			if d!=dir and not np.abs(f-np.round(f))<0.000001:#if not ended at dividing radius
#				nozzlegroups[j].append(Group(currentList,j,dir))
#				dir=d
#				currentList = []
#			currentList.append(line)
#			i+=1
#		nozzlegroups[j].append(Group(currentList,j,dir))
#	finalpath = [[] for _ in range(0,n)]
#	for nozzle in nozzlegroups:
#		for i in range(len(nozzle)-1,-1,-1):
#			if len(nozzle[i].lines)==0:
#				del nozzle[i]
#	for j in range(0,n):
#		nozzle = nozzlegroups[j]
#		found = True
#		while(found):
#			found = False
#			for i in range(len(nozzle)-1,-1,-1):
#				others = copy.deepcopy(nozzle)
#				group = others.pop(i)
#				for other in others:
#					if group.dir == other.dir:
#						print(len(group.lines),len(other.lines))
#						if group.lines[-1].endPoint.isEqual(other.lines[0].startPoint):
#							found = True
#							del nozzle[i]
#							nozzle.insert(i,Group(group.lines+other.lines,group.index,group.dir))
#	for nozzle in nozzlegroups:
#		for group in nozzle:
#			for line in group.lines:
#				line.index = group.dir
#
	r = [[] for _ in range(0,n)]
	for j in range(0,n):
		nozzlegroups[j].sort(key=radius,reverse=True)

	maxgroups = 0
	for j in range(0,n):
		if maxgroups<len(nozzlegroups[j]):
			maxgroups = len(nozzlegroups[j])

	nozzlegroups2 = [[] for _ in range(0,n)]
	for j in range(0,n):
		for i in range(0,maxgroups):
			if i<len(nozzlegroups[j]):
				nozzlegroups[j][i].index = (nozzlegroups[j][i].index-i)%n #staggers groups by nozzle index

	nozzlepaths = [[] for _ in range(0,n)]
	for Index in range(0,n):#performing this searching for each nozzle in turn
		found = True
		while found:#will keep cycling through all sectors until there are no more lines left for that nozzle
			found = False
			for sector in range(0,n):#among geometric sectors of build area
#				print(found)
				minDist = 0
				if len(nozzlegroups[sector])==0:
					continue
				groupchoice = Group([],Index,0)
				for i in range(0,len(nozzlegroups[sector])):#finds best choice among groups for sector
					if (nozzlegroups[sector][i].index == Index):
						found = True
						x = nozzlegroups[sector][i].lines[0].startPoint.X
						y = nozzlegroups[sector][i].lines[0].startPoint.Y
						sectorangle = sector*2*np.pi/n
						r = np.sqrt(x**2+y**2)
						dist = np.sqrt((x-r*np.cos(sectorangle))**2 + (y - r*np.sin(sectorangle))**2)
						if len(groupchoice.lines)==0:
							groupchoice = nozzlegroups[sector][i]
						if minDist>dist:
							minDist = dist
							groupchoice = nozzlegroups[sector][i]
						elif minDist==dist:
							Rchoice = np.sqrt(groupchoice.lines[0].startPoint.X**2 + groupchoice.lines[0].startPoint.Y**2)
							if Rchoice<r:
								groupchoice = nozzlegroups[sector][i]
				if len(groupchoice.lines)!=0:
					nozzlegroups[sector].remove(groupchoice)	
					#once the choice is made
					nozzlepaths[Index].append(groupchoice)
#		print(len(nozzlepaths[Index]))
#	for nozzle in nozzlegroups:
#		print(len(nozzle))
#		for r in range(0,len(nozzle)):
#			nozzle[r].index = r
#	nozzlegroups = nozzlegroups2
	for nozzle in nozzlepaths:
		for group in nozzle:
			for line in group.lines:
				line.index = group.index
	lengths = [0 for _ in range(0,n)]
	for j in range(0,n):
		for group in nozzlepaths[j]:
			lengths[j] += len(group.lines)
#		print("lines per nozzle")
#		print(lengths[j])
#	for nozzle in nozzlegroups:
#		for r in range(0,len(nozzle)):
#			group = nozzle[r]
#			for line in group.lines:
#				line.index = r
	finalpath = [[] for _ in range(0,n)]
	ang_tracking = [0 for _ in range(0,n)]
	for j in range(0,n):
		for s in range(0,len(nozzlepaths[j])):
			group = nozzlepaths[j][s]
			if s==0:
				w = np.arctan2(group.lines[0].startPoint.Y,group.lines[0].startPoint.X)
				r1 = np.sqrt(group.lines[0].startPoint.X**2 + group.lines[0].startPoint.Y**2)
				if w<0:
					w+=2*np.pi
               		        v = 2*np.pi/n*group.index
		                if w<0:
                		        w += 2*np.pi
					if np.abs(w/2/np.pi-np.round(w/2/np.pi))<0.000001:
						w = 0
               			if not np.abs(w-v)<0.00001:#if line does not come from radial border
#					print("adjf")
#					print(group.index)
		                        a = 1-0.1/r1
                		        ang_width = 2*np.arctan2(np.sqrt(1-a**2),a)
					if ang_width<0:
						ang_width+=2*np.pi
		                        theta2_selftemp = np.arctan2(np.cos(v)*np.sin(w)-np.sin(v)*np.cos(w),np.cos(v)*np.cos(w)+np.sin(v)*np.sin(w))
#                		        theta2_selftemp = (theta2_selftemp/2/np.pi-np.floor(theta2_selftemp/2/np.pi))*2*np.pi
					if theta2_selftemp<0:
						theta2_selftemp+=2*np.pi
		                        m = theta2_selftemp/ang_width
                		        m = int(np.ceil(m))
#					print(theta2_selftemp)
		                        if m!=0:
                		                ang_width = theta2_selftemp/m#positive to join to group in CCW direction
						prepath = []                  
                                		for i in range(0,m):
		                                        x1 = r1*np.cos(v+i*ang_width)
                		                        y1 = r1*np.sin(v+i*ang_width)
                                		        x2 = r1*np.cos(v+(i+1)*ang_width)
		                                        y2 = r1*np.sin(v+(i+1)*ang_width)
                		                        prepath.append(Line(SlicerGeometries.Point(x1,y1,0),SlicerGeometries.Point(x2,y2,0),group.lines[0].index,False))
					finalpath[j] = prepath + finalpath[j]
			for line in group.lines:
				finalpath[j].append(line)
			if s<len(nozzlepaths[j])-1:
#				print("called")
#				print(len(nozzlepaths[j]))
#				finalpath[j].append(Line(nozzlepaths[j][s].lines[-1].endPoint,nozzlepaths[j][s+1].lines[0].startPoint,j,False))
				spiral = makeSpiral(nozzlepaths[j][s],nozzlepaths[j][s+1],LINEWIDTH)
				finalpath[j] = finalpath[j] + spiral			
		finalpath[j].insert(0,Line(SlicerGeometries.Point(plateRad*np.cos(j*2*np.pi/n),plateRad*np.sin(j*2*np.pi/n),0),finalpath[j][0].startPoint,j,False))
	
	for j in range(0,n):
		a = list(OrderedDict.fromkeys(finalpath[j]))
		finalpath[j] = a

	for j in range(0,n):
		x1 = finalpath[j][0].startPoint.X
		y1 = finalpath[j][0].startPoint.Y
		x2 = finalpath[j][-1].endPoint.X
		y2 = finalpath[j][-1].endPoint.Y
		r1 = np.sqrt(x1**2 + y1**2)
		r2 = np.sqrt(x2**2 + y2**2)
		theta1 = np.arctan2(y1,x1)
		theta2 = np.arctan2(y2,x2)
		dtheta = np.arctan2(r1*np.cos(theta1)*r2*np.sin(theta2)-r1*np.sin(theta1)*r2*np.cos(theta2),r1*np.cos(theta1)*r2*np.cos(theta2) + r1*np.sin(theta1)*r2*np.sin(theta2))
		if dtheta<0:
			dtheta += 2*np.pi
		ang_tracking[j] = 2*np.pi - dtheta #gives angle needed to complete another loop
#		print("angles")
#		print(dtheta)

	#now to track looping counts:
	loops = [0 for _ in range(0,n)]
	for j in range(0,n):
		radial = SlicerGeometries.SliceLine([[0,0,0],[plateRad*np.cos(j*2*np.pi/n),plateRad*np.sin(j*2*np.pi/n),0]],[0,0,0])
		for i in range(2,len(finalpath[j])):#skip first two lines since they intersect with the radius by design
			line = finalpath[j][i]
			x1 = line.startPoint.X
			x2 = line.endPoint.X
			y1 = line.startPoint.Y
			y2 = line.endPoint.Y
			r1 = np.sqrt(x1**2 + y1**2)
			r2 = np.sqrt(x2**2 + y2**2)
			theta1 = np.arctan2(y1,x1)
			theta2 = np.arctan2(y2,x2)
			dtheta = np.arctan2(r1*np.cos(theta1)*r2*np.sin(theta2)-r1*np.sin(theta1)*r2*np.cos(theta2),r1*np.cos(theta1)*r2*np.cos(theta2) + r1*np.sin(theta1)*r2*np.sin(theta2))
			if not np.abs(dtheta)<0.000001:
				if radial.intersectsWith(line):
					if not radial.intersectsWith(finalpath[j][i-1]):
					#this check is to prevent double-counting when the radius intersects with a vertex between two lines
						loops[j] += 1
			else:
				continue#if line is radial, skip it
	loopMax = np.max(loops) + 1
#	print("bloop")
#	for nozzle in nozzlepaths:
#		print(len(nozzle))
        for i in range(0,len(contours)):
                contour = contours[i]
                vertices = []
                new_lines = []
                for line in contour.lines:
                        vertices.append((line.startPoint.X,line.startPoint.Y))
                vertices = tuple(vertices)
#               print(len(vertices))
                pco = pyclipper.PyclipperOffset()
                pco.AddPath(pyclipper.scale_to_clipper(vertices,2**31), pyclipper.JT_MITER, pyclipper.ET_CLOSEDPOLYGON)
                offset = pyclipper.scale_to_clipper(LINEWIDTH,2**31)
                if contour.level%2==0:
                        new_vertices = pyclipper.scale_from_clipper(pco.Execute(-offset),2**31)
                else:
                        new_vertices = pyclipper.scale_from_clipper(pco.Execute(offset),2**31)
                new_vertices = new_vertices[0]
                for i in range(0,len(new_vertices)):
#                       print(len(new_vertices))
                        if i==len(new_vertices)-1:
                                new_lines.append(SlicerGeometries.SliceLine([[new_vertices[len(new_vertices)-1][0],new_vertices[len(new_vertices)-1][1],currentZ],[new_vertices[0][0],new_vertices[0][1],currentZ]],np.array([0,0,0])))
                        else:
                                new_lines.append(SlicerGeometries.SliceLine([[new_vertices[i][0],new_vertices[i][1],currentZ],[new_vertices[i+1][0],new_vertices[i+1][1],currentZ]],np.array([0,0,0])))
                infillcontours.append(SlicerGeometries.closedContour(new_lines,1))
        infill_path = Infill.infill(infillcontours,'solid',LINEWIDTH,n,NOZZLEFRONT)
        Infill.cookieCutter(infill_path,infillcontours)
	print("how long do cookies take")
# cookies take a while, look into this
	infills = [[]]*n
	for line in infill_path:
		infills[line.index].append(line)

	for j in range(0,n):
		r1 = np.sqrt(finalpath[j][-1].endPoint.X**2 + finalpath[j][-1].endPoint.Y**2)
		v = np.arctan2(finalpath[j][-1].endPoint.Y,finalpath[j][-1].endPoint.X)
		if v<0:
			v+=2*np.pi
		a = 1-0.1/r1
	        ang_width = 2*np.arctan2(np.sqrt(1-a**2),a)
		if ang_width<0:
			ang_width+=2*np.pi
                theta2_selftemp = ang_tracking[j] + (loopMax-loops[j])*2*np.pi
		if theta2_selftemp<0:
			theta2_selftemp+=2*np.pi
	        m = theta2_selftemp/ang_width
                m = int(np.ceil(m))
#		print(theta2_selftemp)
	        if m!=0:
        	        ang_width = theta2_selftemp/m#positive to join to group in CCW direction
#			print("ang width")
#			print(ang_width)
			postpath = []                  
                	for i in range(0,m):
				r2 = r1 + (plateRad-r1)/m
		        	x1 = r1*np.cos(v+i*ang_width)
                	        y1 = r1*np.sin(v+i*ang_width)
                                x2 = r2*np.cos(v+(i+1)*ang_width)
		                y2 = r2*np.sin(v+(i+1)*ang_width)
				r1 = r2
                	        postpath.append(Line(SlicerGeometries.Point(x1,y1,0),SlicerGeometries.Point(x2,y2,0),j,False))
#		print("postpaths")
#		print(len(postpath))
		postpath.append(Line(postpath[-1].endPoint,infills[j][0].startPoint,j,False))
		finalpath[j] = finalpath[j] + postpath
	for j in range(0,n):
		finalpath[j] = finalpath[j] + infills[j]
#		print("infills")
#		print(len(infills[j]))
	return finalpath

class Group:
	def __init__(self,lines,index,dir):
		self.lines = lines
		self.index = index
		self.dir = dir

	def __eq__(self,other):
		all = False
		if len(self.lines)==len(other.lines):
			all = True
			for i in range(0,len(self.lines)):
				if not self.lines[i] == other.lines[i]:
					all = False
		return all

def radius(group):
	return group.lines[0].radius()

def makeSpiral(group1,group2,LINEWIDTH):
	joinlines = []
	r1 = np.sqrt(group1.lines[-1].endPoint.X**2 + group1.lines[-1].endPoint.Y**2)
	r2 = np.sqrt(group2.lines[0].startPoint.X**2 + group2.lines[0].startPoint.Y**2)
	theta1 = np.arctan2(group1.lines[-1].endPoint.Y,group1.lines[-1].endPoint.X)
	theta2 = np.arctan2(group2.lines[0].startPoint.Y,group2.lines[0].startPoint.X)
	dtheta = np.arctan2(r1*np.cos(theta1)*r2*np.sin(theta2)-r1*np.sin(theta1)*r2*np.cos(theta2),r1*np.cos(theta1)*r2*np.cos(theta2) + r1*np.sin(theta1)*r2*np.sin(theta2))
	if dtheta<0:
		dtheta += 2*np.pi
	dr = r2-r1
	theta2_ = (group1.lines[0].index)*np.pi*2/n #sets spiral goal to dividing line towards CW
	dot = (r2*np.cos(theta2)*group1.lines[-1].endPoint.X)+(r2*np.sin(theta2)*group1.lines[-1].endPoint.Y)
	d = dot/r1/r2
	if d>=1:
		d = 1
#	dtheta = np.arccos(d)
	if dtheta==0.:
		joinlines.append(Line(group1.lines[-1].endPoint,SlicerGeometries.Point(r2*np.cos(theta2),r2*np.sin(theta2),0),group1.lines[0].index,False))
	else:
		B = float(dr)/float(dtheta)
		r_a = r1
             	theta_a= theta1
                totalAngle = 0
		x_a,y_a,x_b,y_b = 0,0,0,0
                while totalAngle<np.abs(dtheta):
       	                dtheta_ = LINEWIDTH/np.sqrt(B**2 + r_a**2)
               	        theta_b = theta_a+dtheta_
                       	r_b = B*dtheta_ + r_a
#			print(r_a,r_b,B)
#			print(dr,r1,r2)
                        x_a = r_a*np.cos(theta_a)
       	                y_a = r_a*np.sin(theta_a)
               	        x_b = r_b*np.cos(theta_b)
                       	y_b = r_b*np.sin(theta_b)
			if not ((r_b>=r2 and r_a<=r2) or (r_b<=r2 and r_a>=r2)):
                                joinlines.append(Line(SlicerGeometries.Point(x_a,y_a,0),SlicerGeometries.Point(x_b,y_b,0),group1.lines[0].index,False))
                        r_a = r_b
       	                theta_a = theta_b
               	        totalAngle += dtheta_
              	joinlines.append(Line(SlicerGeometries.Point(x_a,y_a,0),group2.lines[0].startPoint,group1.lines[0].index,False))
	return joinlines

def join(group1,group2,LINEWIDTH):
	joinlines = []
	r1 = np.sqrt(group1.lines[-1].endPoint.X**2 + group1.lines[-1].endPoint.Y**2)
	r2 = np.sqrt(group2.lines[0].startPoint.X**2 + group2.lines[0].startPoint.Y**2)
	theta1 = np.arctan2(group1.lines[-1].endPoint.Y,group1.lines[-1].endPoint.X)
	theta2 = np.arctan2(group2.lines[0].startPoint.Y,group2.lines[0].startPoint.X)
	dr = r2-r1
	dot = (group1.lines[-1].endPoint.X*group2.lines[0].startPoint.X + group1.lines[-1].endPoint.Y*group2.lines[0].startPoint.Y)
	d = dot/r1/r2
	if d>=1:
		d = 1
	dtheta = np.arccos(d)
	if Line(SlicerGeometries.Point(group1.lines[-1].endPoint.X,group1.lines[-1].endPoint.Y,0),SlicerGeometries.Point(group2.lines[0].startPoint.X-group1.lines[-1].endPoint.X,group2.lines[0].startPoint.Y-group1.lines[-1].endPoint.Y,0),0,True).direction()<0:
		dtheta = -dtheta
	if group1.lines[-1].direction()>=0:
		if group2.lines[0].direction()>=0:
			if dtheta!=0:
				B = dr/dtheta
			print("monkey")
			#direct
			r_a = r1
			theta_a= theta1
			totalAngle = 0
			while totalAngle<np.abs(dtheta):
				dtheta_ = LINEWIDTH/np.sqrt(B**2 + r_a**2)
				theta_b = theta_a+dtheta_
				r_b = B*dtheta_+r_a
				print(r_b,r2)
				x_a = r_a*np.cos(theta_a)
				y_a = r_a*np.sin(theta_a)
				x_b = r_b*np.cos(theta_b)
				y_b = r_b*np.sin(theta_b)
				if r_b>=r2:
					joinlines.append(Line(SlicerGeometries.Point(x_a,y_a,0),SlicerGeometries.Point(x_b,y_b,0),group1.lines[0].index,False))
				r_a = r_b
				theta_a = theta_b
				totalAngle += dtheta_
			joinlines.append(Line(SlicerGeometries.Point(x_b,y_b,0),group2.lines[0].startPoint,group1.lines[0].index,False))
		else:
			#go to end and pass again
			theta2_ = (group1.lines[0].index+1)*np.pi*2/n #sets spiral goal to dividing line towards CCW
			dot = (r2*np.cos(theta2_)*group1.lines[-1].endPoint.X)+(r2*np.sin(theta2_)*group1.lines[-1].endPoint.Y)
			d = dot/r1/r2
			if d>=1:
				d = 1
			dtheta = np.arccos(d)
			print(np.arccos(d))
			if dtheta==0.:
				print("got here")
				print(group1.lines[0].index)
				joinlines.append(Line(group1.lines[-1].endPoint,SlicerGeometries.Point(r2*np.cos(theta2_),r2*np.sin(theta2_),0),group1.lines[0].index,False))
			else:
				B = dr/dtheta
				r_a = r1
                	        theta_a= theta1
                        	totalAngle = 0
				x_a,y_a,x_b,y_b = 0,0,0,0
        	                while totalAngle<np.abs(dtheta):
                	                dtheta_ = LINEWIDTH/np.sqrt(B**2 + r_a**2)
                        	        theta_b = theta_a+dtheta_
                                	r_b = B*dtheta_ + r_a
					#print(r_a,r_b,B)
        	                        x_a = r_a*np.cos(theta_a)
                	                y_a = r_a*np.sin(theta_a)
                        	        x_b = r_b*np.cos(theta_b)
                                	y_b = r_b*np.sin(theta_b)
					if r_b>=r2:
		                                joinlines.append(Line(SlicerGeometries.Point(x_a,y_a,0),SlicerGeometries.Point(x_b,y_b,0),group1.lines[0].index,False))
        	                        r_a = r_b
                	                theta_a = theta_b
                        	        totalAngle += dtheta_
                        	joinlines.append(Line(SlicerGeometries.Point(x_b,y_b,0),SlicerGeometries.Point(r2*np.cos(theta2_),r2*np.sin(theta2_),0),group1.lines[0].index,False))
                        a = 1-0.1/r2
			print("making arc")
                        ang_width = 2*np.arctan2(np.sqrt(1-a**2),a)
                        theta2_selftemp = np.arcsin(np.cos(theta2)*np.sin(theta2_)-np.sin(theta2)*np.cos(theta2_))
                        theta2_selftemp = (theta2_selftemp/2/np.pi-np.floor(theta2_selftemp/2/np.pi))*2*np.pi
			if np.abs(theta2_selftemp/2/np.pi-round(theta2_selftemp/2/np.pi))<0.000001:
				theta2_selftemp = 0
			print(theta2_selftemp)
                        m = theta2_selftemp/ang_width
                        m = int(np.ceil(m))
			if m!=0:
	                        ang_width = -theta2_selftemp/m#negative to go in opposite direction of spiral arc just made
				print(r2*np.cos(theta2_),r2*np.sin(theta2_))
        	                for i in range(0,m):
                	                x1 = r2*np.cos(theta2_+i*ang_width)
                        	        y1 = r2*np.sin(theta2_+i*ang_width)
                                	x2 = r2*np.cos(theta2_+(i+1)*ang_width)
                                	y2 = r2*np.sin(theta2_+(i+1)*ang_width)
                                	joinlines.append(Line(SlicerGeometries.Point(x1,y1,0),SlicerGeometries.Point(x2,y2,0),group1.lines[0].index,False))
				print(joinlines[-1].endPoint.X,joinlines[-1].endPoint.Y)
	else:
		if group2.lines[0].direction()>=0:
			#go to end and pass again
			theta2_ = (group1.lines[0].index)*np.pi*2/n #sets spiral goal to dividing line towards CW
			dot = (r2*np.cos(theta2_)*group1.lines[-1].endPoint.X)+(r2*np.sin(theta2_)*group1.lines[-1].endPoint.Y)
			d = dot/r1/r2
			if d>=1:
				d = 1
			dtheta = np.arccos(d)
			if dtheta==0.:
				joinlines.append(Line(group1.lines[-1].endPoint,SlicerGeometries.Point(r2*np.cos(theta2_),r2*np.sin(theta2_),0),group1.lines[0].index,False))
			else:
				B = float(dr)/float(dtheta)
				r_a = r1
                	        theta_a= theta1
                        	totalAngle = 0
				x_a,y_a,x_b,y_b = 0,0,0,0
        	                while totalAngle<np.abs(dtheta):
                	                dtheta_ = -LINEWIDTH/np.sqrt(B**2 + r_a**2)
                        	        theta_b = theta_a+dtheta_
                                	r_b = -B*dtheta_ + r_a
					print(r_a,r_b,B)
					print(dr,r1,r2)
        	                        x_a = r_a*np.cos(theta_a)
                	                y_a = r_a*np.sin(theta_a)
                        	        x_b = r_b*np.cos(theta_b)
                                	y_b = r_b*np.sin(theta_b)
					if r_b>=r2:
		                                joinlines.append(Line(SlicerGeometries.Point(x_a,y_a,0),SlicerGeometries.Point(x_b,y_b,0),group1.lines[0].index,False))
        	                        r_a = r_b
                	                theta_a = theta_b
                        	        totalAngle -= dtheta_
                        	joinlines.append(Line(SlicerGeometries.Point(x_b,y_b,0),SlicerGeometries.Point(r2*np.cos(theta2_),r2*np.sin(theta2_),0),group1.lines[0].index,False))
                        a = 1-0.1/r2
			print("making arc")
                        ang_width = 2*np.arctan2(np.sqrt(1-a**2),a)
                        theta2_selftemp = np.arcsin(np.cos(theta2)*np.sin(theta2_)-np.sin(theta2)*np.cos(theta2_))
#			if theta2_selftemp<0:
#				theta2_selftemp += 2*np.pi
#			print(theta2_selftemp)
#                       theta2_selftemp = (theta2_selftemp/2/np.pi-np.floor(theta2_selftemp/2/np.pi))*2*np.pi
			if np.abs(theta2_selftemp/2/np.pi-round(theta2_selftemp/2/np.pi))<0.000001:
				theta2_selftemp = 0
			print(theta2_selftemp)
                        m = theta2_selftemp/ang_width
                        m = int(np.ceil(m))
			if m!=0:
	                        ang_width = theta2_selftemp/m#positive to go in opposite direction of spiral arc just made
				print(r2*np.cos(theta2_),r2*np.sin(theta2_))
        	                for i in range(0,m):
                	                x1 = r2*np.cos(theta2_+i*ang_width)
                        	        y1 = r2*np.sin(theta2_+i*ang_width)
                                	x2 = r2*np.cos(theta2_+(i+1)*ang_width)
                                	y2 = r2*np.sin(theta2_+(i+1)*ang_width)
                                	joinlines.append(Line(SlicerGeometries.Point(x1,y1,0),SlicerGeometries.Point(x2,y2,0),group1.lines[0].index,False))
				print(joinlines[-1].endPoint.X,joinlines[-1].endPoint.Y)
		else:
			#direct
			print("monkey")
			if dtheta!=0:
				B = dr/dtheta
			r_a = r1
			print(B,r_a)
			theta_a= theta1
			totalAngle = 0
			while totalAngle<np.abs(dtheta):
				dtheta_ = -LINEWIDTH/np.sqrt(B**2 + r_a**2)
				theta_b = theta_a+dtheta_
				r_b = B*dtheta_+r_a
				x_a = r_a*np.cos(theta_a)
				y_a = r_a*np.sin(theta_a)
				x_b = r_b*np.cos(theta_b)
				y_b = r_b*np.sin(theta_b)
				if r_b>=r2:
					joinlines.append(Line(SlicerGeometries.Point(x_a,y_a,0),SlicerGeometries.Point(x_b,y_b,0),group1.lines[0].index,False))
				r_a = r_b
				theta_a = theta_b
				totalAngle -= dtheta_
			joinlines.append(Line(SlicerGeometries.Point(x_b,y_b,0),group2.lines[0].startPoint,group1.lines[0].index,False))
				
	return joinlines
