import math

for i in range(360):
    x1, y1 = 0, 0
    x2, y2 = math.cos(math.radians(i)), math.sin(math.radians(i))
    angle = math.degrees(math.atan2(x2 - x1, y2 - y1))
    print(i, angle, 90 - angle)
