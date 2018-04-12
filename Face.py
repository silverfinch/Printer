class Face:
	def __init__(self, v0, v1, v2):
		self.points = [v0, v1, v2]
		self.maxZ = max(v0[2],v1[2],v2[2])
		self.minZ = min(v0[2],v1[2],v2[2])

	def isSliced(self, currentZ, zIncrement):
		upperZ = self.maxZ - self.maxZ%(zIncrement/2) + zIncrement/2
		lowerZ = self.minZ - self.minZ%(zIncrement/2)
		if (currentZ <= upperZ and currentZ >= lowerZ):
			return 1
		else:
			return 0

	def sliceLine(self, currentZ, zIncrement):
		Zcoords = [self.points[0][2],self.points[1][2],self.points[2][2]]
		endpoints = []
		below = []
		above = []
		for i in range(0,3):# tells which vertices are above the current elevation and which are below
			print(currentZ)
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
			return endpoints
		else:
			for i in below:
				for j in above:
					newpoint = ((currentZ - i[2])/(j[2] - i[2]))*(j-i) + i# linear interpolation between upper and lower points
					endpoints.append(newpoint)
			return endpoints
