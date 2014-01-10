import Queue
import fractal
import functools
import itertools
import random
import threading
import wx

MANDELBROT = 1
JULIA = 2

MODE = MANDELBROT
MAX_ITERATIONS = 512
TILE_SIZE = 128
SCROLL_FACTOR = 32

class Cache(object):
    def __init__(self, listener):
        self.listener = listener
        self.reset()
        self.pending = 0
        self.jx = -0.34
        self.jy = 0.6175
        self.fractal = fractal.Fractal(MAX_ITERATIONS)
        self.queue = Queue.Queue()
        for _ in xrange(4):
            thread = threading.Thread(target=self.worker)
            thread.setDaemon(True)
            thread.start()
    def reset(self):
        self.tiles = {}
        self.seen = set()
    def get_tile(self, i, j, zoom, create=True):
        key = (i, j, zoom)
        if create and key not in self.seen:
            self.pending += 1
            self.seen.add(key)
            self.queue.put(key)
        return self.tiles.get(key)
    def worker(self):
        while True:
            key = self.queue.get()
            tile = self.create_tile(key)
            wx.CallAfter(self.on_tile, key, tile)
    def on_tile(self, key, tile):
        self.pending -= 1
        self.tiles[key] = tile
        self.listener()
    def create_tile(self, key):
        i, j, zoom = key
        tw = float(TILE_SIZE) / zoom
        tx = i * tw
        ty = j * tw
        return self.create_bitmap(TILE_SIZE, TILE_SIZE, tx, ty, tw, tw)
    def create_bitmap(self, width, height, tx, ty, tw, th):
        if MODE == MANDELBROT:
            data = self.fractal.mandelbrot(MAX_ITERATIONS,
                width, height, tx, ty, tw, th)
        else:
            data = self.fractal.julia(MAX_ITERATIONS,
                width, height, tx, ty, tw, th, self.jx, self.jy)
        return wx.BitmapFromBufferRGBA(width, height, data)

class Renderer(object):
    def listener(self, cache, i1, j1, i2, j2, zoom, callback):
        if cache.pending:
            return
        width = (i2 - i1 + 1) * TILE_SIZE
        height = (j2 - j1 + 1) * TILE_SIZE
        bitmap = wx.EmptyBitmap(width, height)
        dc = wx.MemoryDC(bitmap)
        tiles = list(itertools.product(xrange(i1, i2 + 1), xrange(j1, j2 + 1)))
        for i, j in tiles:
            x = (i - i1) * TILE_SIZE
            y = height - (j - j1) * TILE_SIZE - TILE_SIZE
            tile = cache.get_tile(i, j, zoom, False)
            dc.DrawBitmap(tile, x, y)
        del dc
        callback(bitmap)
    def render(self, i1, j1, i2, j2, zoom, callback):
        cache = Cache(None)
        cache.listener = functools.partial(self.listener,
            cache, i1, j1, i2, j2, zoom, callback)
        tiles = list(itertools.product(xrange(i1, i2 + 1), xrange(j1, j2 + 1)))
        random.shuffle(tiles)
        for i, j in tiles:
            cache.get_tile(i, j, zoom)

class View(wx.Panel):
    def __init__(self, parent):
        super(View, self).__init__(parent, style=wx.WANTS_CHARS)
        self.cache = Cache(self.on_tile)
        self.x = 0
        self.y = 0
        self.zoom = 256
        self.anchor = None
        self.SetBackgroundStyle(wx.BG_STYLE_CUSTOM)
        self.Bind(wx.EVT_SIZE, self.on_size)
        self.Bind(wx.EVT_PAINT, self.on_paint)
        self.Bind(wx.EVT_KEY_DOWN, self.on_key_down)
        self.Bind(wx.EVT_LEFT_DCLICK, self.on_left_dclick)
        self.Bind(wx.EVT_LEFT_DOWN, self.on_left_down)
        self.Bind(wx.EVT_LEFT_UP, self.on_left_up)
        self.Bind(wx.EVT_RIGHT_DOWN, self.on_right_down)
        self.Bind(wx.EVT_RIGHT_DCLICK, self.on_right_dclick)
        self.Bind(wx.EVT_MOTION, self.on_motion)
        self.Bind(wx.EVT_MOUSEWHEEL, self.on_mouse_wheel)
    def on_tile(self):
        self.Refresh()
    def on_size(self, event):
        event.Skip()
        self.Refresh()
    def on_key_down(self, event):
        code = event.GetKeyCode()
        if code == wx.WXK_ESCAPE:
            self.GetParent().Close()
        if code == wx.WXK_LEFT:
            self.x -= float(SCROLL_FACTOR) / self.zoom
        if code == wx.WXK_RIGHT:
            self.x += float(SCROLL_FACTOR) / self.zoom
        if code == wx.WXK_UP:
            self.y -= float(SCROLL_FACTOR) / self.zoom
        if code == wx.WXK_DOWN:
            self.y += float(SCROLL_FACTOR) / self.zoom
        if code == ord('+') or code == wx.WXK_NUMPAD_ADD:
            self.zoom_in()
        if code == ord('-') or code == wx.WXK_NUMPAD_SUBTRACT:
            self.zoom_out()
        if code == ord('S'):
            self.save()
        self.Refresh()
    def save(self):
        style = wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT
        dialog = wx.FileDialog(self.GetParent(), wildcard='*.png', style=style)
        if dialog.ShowModal() == wx.ID_OK:
            path = dialog.GetPath()
            self.render(path)
        dialog.Destroy()
    def on_left_down(self, event):
        x, y = event.GetPosition()
        self.anchor = (x, y, self.x, self.y)
        self.CaptureMouse()
    def on_left_up(self, event):
        self.anchor = None
        try:
            self.ReleaseMouse()
        except Exception:
            pass
    def on_left_dclick(self, event):
        x, y = event.GetPosition()
        self.zoom_in_at(x, y)
        self.Refresh()
    def on_right_down(self, event):
        x, y = event.GetPosition()
        self.zoom_out_at(x, y)
        self.Refresh()
    def on_right_dclick(self, event):
        x, y = event.GetPosition()
        self.zoom_out_at(x, y)
        self.Refresh()
    def on_mouse_wheel(self, event):
        x, y = event.GetPosition()
        direction = event.GetWheelRotation()
        if direction > 0:
            self.zoom_in_at(x, y)
        else:
            self.zoom_out_at(x, y)
        self.Refresh()
    def on_motion(self, event):
        mx, my = event.GetPosition()
        if self.anchor is None:
            return
        ax, ay, x, y = self.anchor
        dx, dy = mx - ax, my - ay
        self.x = x - dx / float(self.zoom)
        self.y = y - dy / float(self.zoom)
        self.Refresh()
    def on_paint(self, event):
        dc = wx.BufferedPaintDC(self)
        dc.SetBackground(wx.BLACK_BRUSH)
        dc.Clear()
        w, h = self.GetClientSize()
        i1, j1 = self.screen_to_tile(0, h)
        i2, j2 = self.screen_to_tile(w, 0)
        tiles = list(itertools.product(xrange(i1, i2 + 1), xrange(j1, j2 + 1)))
        random.shuffle(tiles)
        for i, j in tiles:
            x, y = self.tile_to_screen(i, j)
            bitmap = self.cache.get_tile(i, j, self.zoom)
            if bitmap:
                dc.DrawBitmap(bitmap, x, y)
                continue
            for m in [2, 4, 8, 16, 32]:
                bitmap = self.cache.get_tile(
                    i / m, j / m, self.zoom / m, False)
                if bitmap is None:
                    continue
                size = TILE_SIZE / m
                dx = (i % m) * size
                dy = (m - 1 - j % m) * size
                image = wx.ImageFromBitmap(bitmap)
                image = image.GetSubImage((dx, dy, size, size))
                image.Rescale(TILE_SIZE, TILE_SIZE)
                bitmap = wx.BitmapFromImage(image)
                dc.DrawBitmap(bitmap, x, y)
                break
    def render(self, path):
        def callback(bitmap):
            bitmap.SaveFile(path, wx.BITMAP_TYPE_PNG)
        m = 2
        w, h = self.GetClientSize()
        w, h = w * m, h * m
        zoom = self.zoom * m
        i1, j1 = self._screen_to_tile(0, h, w, h, zoom)
        i2, j2 = self._screen_to_tile(w, 0, w, h, zoom)
        renderer = Renderer()
        renderer.render(i1, j1, i2, j2, zoom, callback)
    def zoom_in(self):
        self.zoom *= 2
    def zoom_in_at(self, x, y):
        ax, ay = self.screen_to_point(x, y)
        self.zoom *= 2
        bx, by = self.screen_to_point(x, y)
        dx, dy = bx - ax, by - ay
        self.x -= dx
        self.y += dy
    def zoom_out(self):
        self.zoom /= 2
    def zoom_out_at(self, x, y):
        ax, ay = self.screen_to_point(x, y)
        self.zoom /= 2
        bx, by = self.screen_to_point(x, y)
        dx, dy = bx - ax, by - ay
        self.x -= dx
        self.y += dy
    def _tile_to_screen(self, i, j, w, h, zoom):
        px = w / 2.0 - self.x * zoom + i * TILE_SIZE
        py = h / 2.0 - self.y * zoom - j * TILE_SIZE - TILE_SIZE
        px = int(px)
        py = int(py)
        return (px, py)
    def _screen_to_tile(self, px, py, w, h, zoom):
        i = (px - w / 2.0 + self.x * zoom) / TILE_SIZE
        j = (py - h / 2.0 + self.y * zoom) / -TILE_SIZE
        i = int(round(i - 0.5))
        j = int(round(j - 0.5))
        return (i, j)
    def _point_to_screen(self, x, y, w, h, zoom):
        px = (x - self.x) * zoom + w / 2.0
        py = (y - self.y) * zoom + h / 2.0
        px = int(px)
        py = int(py)
        return (px, py)
    def _screen_to_point(self, px, py, w, h, zoom):
        x = self.x + (px - w / 2.0) / zoom
        y = -self.y - (py - h / 2.0) / zoom
        return (x, y)
    def tile_to_screen(self, i, j):
        w, h = self.GetClientSize()
        return self._tile_to_screen(i, j, w, h, self.zoom)
    def screen_to_tile(self, px, py):
        w, h = self.GetClientSize()
        return self._screen_to_tile(px, py, w, h, self.zoom)
    def point_to_screen(self, x, y):
        w, h = self.GetClientSize()
        return self._point_to_screen(x, y, w, h, self.zoom)
    def screen_to_point(self, px, py):
        w, h = self.GetClientSize()
        return self._screen_to_point(px, py, w, h, self.zoom)

class Frame(wx.Frame):
    def __init__(self):
        super(Frame, self).__init__(None)
        self.SetTitle('Fractals!')
        self.view = View(self)

def main():
    app = wx.App(False)
    frame = Frame()
    frame.SetClientSize((800, 800))
    frame.Center()
    frame.Show()
    app.MainLoop()

if __name__ == '__main__':
    main()
