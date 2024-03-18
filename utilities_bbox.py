import math
from mathutils import Vector, Matrix


class BBox:
	@classmethod
	def calc_bbox(cls, coords):
		xmin = math.inf
		xmax = -math.inf
		ymin = math.inf
		ymax = -math.inf

		for x, y in coords:
			if xmin > x:
				xmin = x
			if xmax < x:
				xmax = x
			if ymin > y:
				ymin = y
			if ymax < y:
				ymax = y
		return cls(xmin, xmax, ymin, ymax)

	@classmethod
	def calc_bbox_uv(cls, group, uv_layers, are_loops=False):
		xmin = math.inf
		xmax = -math.inf
		ymin = math.inf
		ymax = -math.inf

		if not are_loops:
			for face in group:
				for loop in face.loops:
					x, y = loop[uv_layers].uv
					if xmin > x:
						xmin = x
					if xmax < x:
						xmax = x
					if ymin > y:
						ymin = y
					if ymax < y:
						ymax = y
		else:
			for loop in group:
				x, y = loop[uv_layers].uv
				if xmin > x:
					xmin = x
				if xmax < x:
					xmax = x
				if ymin > y:
					ymin = y
				if ymax < y:
					ymax = y
		return cls(xmin, xmax, ymin, ymax)

	@classmethod
	def init_from_minmax(cls, min, max):
		bbox = cls(min[0], max[0], min[1], max[1])
		bbox.sanitize()
		return bbox

	def __init__(self, xmin=math.inf, xmax=-math.inf, ymin=math.inf, ymax=-math.inf):
		self.xmin = xmin
		self.xmax = xmax
		self.ymin = ymin
		self.ymax = ymax

	def __str__(self):
		return f"xmin={self.xmin:.6}, xmax={self.xmax:.6}, ymin={self.ymin:.6}, ymax={self.ymax:.6}, width={self.width:.6}, height={self.height:.6}"

	@property
	def is_valid(self) -> bool:
		return (self.xmin < self.xmax) and (self.ymin < self.ymax)

	@property
	def max(self):
		return Vector((self.xmax, self.ymax))

	@property
	def min(self):
		return Vector((self.xmin, self.ymin))

	@property
	def left_upper(self):
		return Vector((self.xmin, self.ymax))

	@property
	def left_bottom(self):
		return Vector((self.xmin, self.ymin))

	@property
	def right_bottom(self):
		return Vector((self.xmax, self.ymin))

	@property
	def right_upper(self):
		return Vector((self.xmax, self.ymax))

	@property
	def upper(self):
		return Vector(((self.xmin + self.xmax) * 0.5, self.ymax))

	@property
	def bottom(self):
		return Vector(((self.xmin + self.xmax) * 0.5, self.ymin))

	@property
	def left(self):
		return Vector((self.xmin, (self.ymin + self.ymax) * 0.5))

	@property
	def right(self):
		return Vector((self.xmax, (self.ymin + self.ymax) * 0.5))

	@property
	def center(self):
		return Vector(((self.xmin + self.xmax) * 0.5, (self.ymin + self.ymax) * 0.5))

	@property
	def width(self) -> float:
		return self.xmax - self.xmin

	@property
	def height(self) -> float:
		return self.ymax - self.ymin

	@property
	def max_lenght(self):
		return max(self.width, self.height)

	@property
	def min_lenght(self):
		return min(self.width, self.height)

	@property
	def half_width(self) -> float:
		return (self.xmax - self.xmin) * 0.5

	@property
	def half_height(self) -> float:
		return (self.ymax - self.ymin) * 0.5

	@property
	def area(self):
		return self.width * self.height

	@property
	def is_empty(self) -> bool:
		return (self.xmax <= self.xmin) or (self.ymax <= self.ymin)

	def union(self, other):
		if self.xmin > other.xmin:
			self.xmin = other.xmin
		if self.xmax < other.xmax:
			self.xmax = other.xmax
		if self.ymin > other.ymin:
			self.ymin = other.ymin
		if self.ymax < other.ymax:
			self.ymax = other.ymax
		return self

	def sanitize(self):
		if self.xmin > self.xmax:
			self.xmin, self.xmax = self.xmax, self.xmin
		if self.ymin > self.ymax:
			self.ymin, self.ymax = self.ymax, self.ymin
		# assert self.is_valid
		return self

	def do_minmax_v(self, xy):
		if xy[0] < self.xmin:
			self.xmin = xy[0]
		if xy[0] > self.xmax:
			self.xmax = xy[0]
		if xy[1] < self.ymin:
			self.ymin = xy[1]
		if xy[1] > self.ymax:
			self.ymax = xy[1]

	def clamp(self, xmin=0, ymin=0, xmax=1, ymax=1):
		if self.xmin < xmin:
			self.xmin = xmin
		if self.ymin < ymin:
			self.ymin = ymin
		if self.xmax > xmax:
			self.xmax = xmax
		if self.ymax > ymax:
			self.ymax = ymax

	def translate(self, delta):
		self.xmin, self.ymin = self.min + delta
		self.xmax, self.ymax = self.max + delta
		return self

	def rotate_expand(self, angle):
		center = self.center
		rot_matrix = Matrix.Rotation(-angle, 2)

		corner = self.right_upper - center
		corner_rot = corner @ rot_matrix
		corner_max = Vector((abs(corner_rot[0]), abs(corner_rot[1])))

		corner.y *= -1
		corner_rot = corner @ rot_matrix
		corner_max[0] = max(corner_max[0], abs(corner_rot[0]))
		corner_max[1] = max(corner_max[1], abs(corner_rot[1]))

		self.xmin = center[0] - corner_max[0]
		self.xmax = center[0] + corner_max[0]
		self.ymin = center[1] - corner_max[1]
		self.ymax = center[1] + corner_max[1]

		return self

	def scale(self, scale):
		center = self.center
		self.xmin, self.ymin = (self.min - center) * scale + center
		self.xmax, self.ymax = (self.max - center) * scale + center
		return self.sanitize()


	def update(self, coords):
		for x, y in coords:
			if x < self.xmin:
				self.xmin = x
			if x > self.xmax:
				self.xmax = x
			if y < self.ymin:
				self.ymin = y
			if y > self.ymax:
				self.ymax = y
