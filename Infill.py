import numpy as np
from SlicerGeometries import Point

def infill(contours,infill_type,LINEWIDTH,n,NOZZLEFRONT):
	mags = []
	if infill_type == 'solid':
		for contour in contours:
			for line in contour.lines:
				mags.append(line.startPoint.magnitude())
				mags.append(line.endPoint.magnitude())
		max_mag = max(mags)-LINEWIDTH#distance of outermost infill shell
		num_infill_shells = int(np.floor(max_mag/LINEWIDTH))#leaves excess in the center to be filled with smush
		min_mag = NOZZLEFRONT 
		crowded_shells = int(np.ceil(min_mag/LINEWIDTH))
		infill_path = []
		crowdPoint = []
		arcwidths = []
		for e in range(0,n):
			R = max_mag
			print(max_mag)
			theta = e*360./n
			for i in range(0,num_infill_shells-crowded_shells):
				R2 = R-LINEWIDTH
				arcwidth = 180./np.pi*2*np.arctan2(LINEWIDTH/2.,R)
				theta2 = theta+(360./n-arcwidth)
				# inwards withdrawal
				infill_path.append(ArcLine((0,0),R,theta,theta2,e,True))
				#creates new Arc, stops just at edge of next infill pattern
				infill_path.append(Line(Point(R*np.cos(theta2*np.pi/180),R*np.sin(theta2*np.pi/180),0),Point(R2*np.cos(theta2*np.pi/180),R2*np.sin(theta2*np.pi/180),0),e,True))
				R = R2
				theta = theta2
			arcwidth = 180./np.pi*2*np.arctan2(LINEWIDTH/2.,R)
			theta2 = theta+(360./n-arcwidth)
			infill_path.append(ArcLine((0,0),R,theta,theta2,e,True))
			crowdPoint.append(Point(R*np.cos(theta2*np.pi/180),R*np.sin(theta2*np.pi/180),0))
			#crowding region management:
			if e!=0:
				infill_path.append(Line(crowdPoint[e],Point((R+LINEWIDTH*crowded_shells+8)*np.cos(theta2*np.pi/180),(R+LINEWIDTH*crowded_shells+8)*np.sin(theta2*np.pi/180),0),e,False))#increase radius by 8 to see paths clearly on graphic
				idleR = R+LINEWIDTH*crowded_shells+8
			for i in range(1,crowded_shells):
				if e!=0:
					print('thing')
					theta=theta2
					theta2 = theta2+360-arcwidths[i-1]
					infill_path.append(ArcLine((0,0),idleR,theta,theta2,e,False))
				else:
					R = R-LINEWIDTH
					arcwidth = 180./np.pi*2*np.arctan2(LINEWIDTH/2.,R)
					arcwidths.append(arcwidth)
					theta=theta2
					theta2 = theta2+360-arcwidth
					infill_path.append(Line(Point(crowdPoint[0].X,crowdPoint[0].Y,crowdPoint[0].Z),Point(R*np.cos(theta*np.pi/180),R*np.sin(theta*np.pi/180),0),0,True))
					infill_path.append(ArcLine((0,0),R,theta,theta2,0,True))
					crowdPoint[0].X = R*np.cos(theta2*np.pi/180)
					crowdPoint[0].Y = R*np.sin(theta2*np.pi/180)
			infill_path.append(Line(Point(crowdPoint[0].X,crowdPoint[0].Y,crowdPoint[0].Z),Point(0,0,0),0,True))
	return infill_path

class ArcLine:
	def __init__(self,hk,r,theta1,theta2,index,isExtruding):
		self.index = index
		self.type = 'arc'
		self.hk = hk
		self.r = r
		self.theta1 = theta1
		self.theta2 = theta2
		self.isExtruding = isExtruding

class Line:
	def __init__(self,startPoint,endPoint,index,isExtruding):
		self.index = index
		self.type = 'line'
		self.startPoint = startPoint
		self.endPoint = endPoint
		self.isExtruding = isExtruding
