from ctypes import *
import colorsys
import math

dll = CDLL('_fractal')

dll.mandelbrot.argtypes = [c_int, c_int, c_int,
    c_double, c_double, c_double, c_double,
    POINTER(c_uint), c_int, POINTER(c_uint)]

dll.julia.argtypes = [c_int, c_int, c_int,
    c_double, c_double, c_double, c_double, c_double, c_double,
    POINTER(c_uint), c_int, POINTER(c_uint)]

class Fractal(object):
    def __init__(self, palette_size):
        self.create_palette(palette_size)
    def create_palette(self, size):
        self.palette = (c_uint * size)()
        for i in xrange(size):
            p = i / float(size - 1)
            p = math.sin(p * math.pi)
            h = p / 5
            s = 0.8
            v = 0.5 + p / 2
            r, g, b = colorsys.hsv_to_rgb(h, s, v)
            r, g, b = int(r * 255), int(g * 255), int(b * 255)
            value = (255 << 24) | (b << 16) | (g << 8) | (r << 0)
            self.palette[i] = value
    def mandelbrot(self, max_iterations, width, height, wx, wy, ww, wh):
        data = (c_uint * (width * height))()
        dll.mandelbrot(max_iterations, width, height,
            wx, wy, ww, wh, self.palette, len(self.palette), data)
        return data
    def julia(self, max_iterations, width, height, wx, wy, ww, wh, jx, jy):
        data = (c_uint * (width * height))()
        dll.julia(max_iterations, width, height,
            wx, wy, ww, wh, jx, jy, self.palette, len(self.palette), data)
        return data
