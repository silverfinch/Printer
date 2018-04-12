import numpy as np
from SlicerGeometries import Point

def infill(contours,infill_type,LINEWIDTH,n):
	mags = []
	if infill_type == 'solid':
		for contour in contours:
			for line in contour.lines:
				mags.append(line.startPoint.magnitude())
				mags.append(line.endPoint.magnitude())
		max_mag = max(mags)-LINEWIDTH#distance of outermost infill shell
		num_infill_shells = int(np.floor(max_mag/LINEWIDTH))#leaves excess in the center to be filled with smush
		min_mag = LINEWIDTH/2/np.tan(np.pi/180*360/2/n) + (max_mag-num_infill_shells*LINEWIDTH) 
		crowded_shells = 1#int(np.ceil(min_mag/LINEWIDTH))
		infill_path = []
		for e in range(0,n):
			R = max_mag
			print(max_mag)
			theta = e*360./n
			for i in range(0,num_infill_shells-crowded_shells):
				R2 = R-LINEWIDTH
				arcwidth = 180./np.pi*2*np.arctan2(LINEWIDTH/2.,R)
				theta2 = theta+(360./n-arcwidth)
				# inwards withdrawal
				infill_path.append(ArcLine((0,0),R,theta,theta2,e))
				#creates new Arc, stops just at edge of next infill pattern
				infill_path.append(Line(Point(R*np.cos(theta2*np.pi/180),R*np.sin(theta2*np.pi/180),0),Point(R2*np.cos(theta2*np.pi/180),R2*np.sin(theta2*np.pi/180),0),e))
				R = R2
				theta = theta2
			arcwidth = 180./np.pi*2*np.arctan2(LINEWIDTH/2.,R)
			theta2 = theta+(360./n-arcwidth)
			infill_path.append(ArcLine((0,0),R,theta,theta2,e))
	return infill_path

class ArcLine:
	def __init__(self,hk,r,theta1,theta2,index):
		self.index = index
		self.type = 'arc'
		self.hk = hk
		self.r = r
		self.theta1 = theta1
		self.theta2 = theta2

class Line:
	def __init__(self,startPoint,endPoint,index):
		self.index = index
		self.type = 'line'
		self.startPoint = startPoint
		self.endPoint = endPoint
