#!/usr/bin/env python3
"""Sunday 22 November 2026 — The World in One Day (make.fun news-image-20261122 v4).
Self-contained stdlib-only generator: pure-Python PNG encoder, hand-typed fonts,
vector drawing. No network, no PIL, no file reads. Deterministic.
Writes /output/entry.png (or $MAKEFUN_OUTPUT_DIR/entry.png)."""
import os, struct, zlib

W, H = 1024, 1024
PAPER = (247, 242, 231)
CREAM = (250, 246, 236)
INK = (24, 24, 22)
NAVY = (15, 30, 61)
NAVY2 = (9, 22, 52)
NIGHT = (13, 22, 48)
RED = (176, 30, 36)
RED2 = (140, 20, 26)
GOLD = (201, 162, 39)
TEAL = (0, 122, 110)
GREY = (110, 108, 100)
LGREY = (210, 206, 194)
WHITE = (255, 255, 255)
SKY1 = (246, 178, 96)
SKY2 = (232, 120, 74)
DAWN1 = (250, 205, 130)
DAWN2 = (238, 140, 80)

def png_bytes(w, h, rgb):
    raw = bytearray()
    for y in range(h):
        raw.append(0)
        raw += rgb[y * w * 3:(y + 1) * w * 3]
    def chunk(t, data):
        c = struct.pack('>I', len(data)) + t + data
        return c + struct.pack('>I', zlib.crc32(t + data) & 0xffffffff)
    ihdr = struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0)
    return (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', ihdr)
            + chunk(b'IDAT', zlib.compress(bytes(raw), 9)) + chunk(b'IEND', b''))

class Canvas:
    def __init__(self, w, h, bg):
        self.w, self.h = w, h
        self.px = bytearray(w * h * 3)
        self.fill(bg)
    def fill(self, c):
        r, g, b = c
        self.px[:] = bytes((r, g, b)) * (self.w * self.h)
    def set(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i], self.px[i+1], self.px[i+2] = c
    def rect(self, x, y, w, h, c):
        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(self.w, x + w), min(self.h, y + h)
        if x1 <= x0 or y1 <= y0:
            return
        r, g, b = c
        row = bytes((r, g, b)) * (x1 - x0)
        for yy in range(y0, y1):
            i = (yy * self.w + x0) * 3
            self.px[i:i + len(row)] = row
    def hline(self, x0, x1, y, c, w=1):
        for yy in range(y, y + w):
            for x in range(x0, x1):
                self.set(x, yy, c)
    def vline(self, x, y0, y1, c, w=1):
        for xx in range(x, x + w):
            for y in range(y0, y1):
                self.set(xx, y, c)
    def disc(self, cx, cy, r, c):
        for yy in range(cy - r, cy + r + 1):
            for xx in range(cx - r, cx + r + 1):
                if (xx - cx) ** 2 + (yy - cy) ** 2 <= r * r:
                    self.set(xx, yy, c)
    def line(self, x0, y0, x1, y1, c, w=1):
        dx, dy = abs(x1 - x0), abs(y1 - y0)
        steps = max(dx, dy, 1)
        r = max(0, w // 2)
        for i in range(steps + 1):
            x = x0 + (x1 - x0) * i // steps
            y = y0 + (y1 - y0) * i // steps
            if r:
                self.disc(x, y, r, c)
            else:
                self.set(x, y, c)
    def poly(self, pts, c):
        # scanline fill for a simple polygon
        if len(pts) < 3:
            return
        ys = [p[1] for p in pts]
        for y in range(max(0, min(ys)), min(self.h, max(ys) + 1)):
            xs = []
            n = len(pts)
            for i in range(n):
                x0, y0 = pts[i]
                x1, y1 = pts[(i + 1) % n]
                if (y0 <= y < y1) or (y1 <= y < y0):
                    t = (y - y0) / (y1 - y0)
                    xs.append(int(x0 + t * (x1 - x0)))
            xs.sort()
            for j in range(0, len(xs) - 1, 2):
                for x in range(xs[j], xs[j + 1] + 1):
                    self.set(x, y, c)
    def vgrad(self, x, y, w, h, c0, c1):
        for yy in range(h):
            t = yy / max(1, h - 1)
            c = tuple(int(c0[k] + (c1[k] - c0[k]) * t) for k in range(3))
            self.rect(x, y + yy, w, 1, c)
    def frame(self, x, y, w, h, c, t=1):
        self.rect(x, y, w, t, c)
        self.rect(x, y + h - t, w, t, c)
        self.rect(x, y, t, h, c)
        self.rect(x + w - t, y, t, h, c)

# ---- 5x7 bitmap font (body text). Each glyph: 7 rows of 5 bits. ----
F5 = {
'A': ('01110','10001','10001','11111','10001','10001','10001'),
'B': ('11110','10001','10001','11110','10001','10001','11110'),
'C': ('01110','10001','10000','10000','10000','10001','01110'),
'D': ('11100','10010','10001','10001','10001','10010','11100'),
'E': ('11111','10000','10000','11110','10000','10000','11111'),
'F': ('11111','10000','10000','11110','10000','10000','10000'),
'G': ('01110','10001','10000','10111','10001','10001','01111'),
'H': ('10001','10001','10001','11111','10001','10001','10001'),
'I': ('01110','00100','00100','00100','00100','00100','01110'),
'J': ('00111','00010','00010','00010','00010','10010','01100'),
'K': ('10001','10010','10100','11000','10100','10010','10001'),
'L': ('10000','10000','10000','10000','10000','10000','11111'),
'M': ('10001','11011','10101','10101','10001','10001','10001'),
'N': ('10001','11001','10101','10011','10001','10001','10001'),
'O': ('01110','10001','10001','10001','10001','10001','01110'),
'P': ('11110','10001','10001','11110','10000','10000','10000'),
'Q': ('01110','10001','10001','10001','10101','10010','01101'),
'R': ('11110','10001','10001','11110','10100','10010','10001'),
'S': ('01111','10000','10000','01110','00001','00001','11110'),
'T': ('11111','00100','00100','00100','00100','00100','00100'),
'U': ('10001','10001','10001','10001','10001','10001','01110'),
'V': ('10001','10001','10001','10001','10001','01010','00100'),
'W': ('10001','10001','10001','10101','10101','11011','10001'),
'X': ('10001','10001','01010','00100','01010','10001','10001'),
'Y': ('10001','10001','01010','00100','00100','00100','00100'),
'Z': ('11111','00001','00010','00100','01000','10000','11111'),
'a': ('00000','00000','01110','00001','01111','10001','01111'),
'b': ('10000','10000','10110','11001','10001','10001','11110'),
'c': ('00000','00000','01110','10000','10000','10001','01110'),
'd': ('00001','00001','01101','10011','10001','10001','01111'),
'e': ('00000','00000','01110','10001','11111','10000','01110'),
'f': ('00110','01001','01000','11110','01000','01000','01000'),
'g': ('00000','01111','10001','10001','01111','00001','01110'),
'h': ('10000','10000','10110','11001','10001','10001','10001'),
'i': ('00100','00000','01100','00100','00100','00100','01110'),
'j': ('00010','00000','00110','00010','00010','10010','01100'),
'k': ('10000','10000','10010','10100','11000','10100','10010'),
'l': ('01100','00100','00100','00100','00100','00100','01110'),
'm': ('00000','00000','11010','10101','10101','10101','10101'),
'n': ('00000','00000','10110','11001','10001','10001','10001'),
'o': ('00000','00000','01110','10001','10001','10001','01110'),
'p': ('00000','00000','10110','11001','10001','11110','10000'),
'q': ('00000','00000','01101','10011','10001','01111','00001'),
'r': ('00000','00000','10110','11001','10000','10000','10000'),
's': ('00000','00000','01111','10000','01110','00001','11110'),
't': ('01000','01000','11110','01000','01000','01001','00110'),
'u': ('00000','00000','10001','10001','10001','10011','01101'),
'v': ('00000','00000','10001','10001','10001','01010','00100'),
'w': ('00000','00000','10001','10101','10101','10101','01010'),
'x': ('00000','00000','10001','01010','00100','01010','10001'),
'y': ('00000','00000','10001','10001','01111','00001','01110'),
'z': ('00000','00000','11111','00010','00100','01000','11111'),
'0': ('01110','10001','10011','10101','11001','10001','01110'),
'1': ('00100','01100','00100','00100','00100','00100','01110'),
'2': ('01110','10001','00001','00110','01000','10000','11111'),
'3': ('11110','00001','00001','01110','00001','00001','11110'),
'4': ('00010','00110','01010','10010','11111','00010','00010'),
'5': ('11111','10000','11110','00001','00001','10001','01110'),
'6': ('00110','01000','10000','11110','10001','10001','01110'),
'7': ('11111','00001','00010','00100','01000','01000','01000'),
'8': ('01110','10001','10001','01110','10001','10001','01110'),
'9': ('01110','10001','10001','01111','00001','00010','01100'),
' ': ('00000','00000','00000','00000','00000','00000','00000'),
'.': ('00000','00000','00000','00000','00000','01100','01100'),
',': ('00000','00000','00000','00000','01100','00100','01000'),
"'": ('00100','00100','01000','00000','00000','00000','00000'),
'!': ('00100','00100','00100','00100','00100','00000','00100'),
'?': ('01110','10001','00001','00110','00100','00000','00100'),
':': ('00000','01100','01100','00000','01100','01100','00000'),
';': ('00000','01100','01100','00000','01100','00100','01000'),
'-': ('00000','00000','00000','01110','00000','00000','00000'),
'\u2013': ('00000','00000','00000','11111','00000','00000','00000'),
'\u2014': ('00000','00000','00000','11111','00000','00000','00000'),
'(': ('00010','00100','01000','01000','01000','00100','00010'),
')': ('01000','00100','00010','00010','00010','00100','01000'),
'/': ('00001','00010','00010','00100','01000','01000','10000'),
'%': ('11001','11010','00010','00100','01000','01011','10011'),
'+': ('00000','00100','00100','11111','00100','00100','00000'),
'\u00b7': ('00000','00000','00000','01100','01100','00000','00000'),
'&': ('01100','10010','10100','01000','10101','10010','01101'),
'$': ('00100','01111','10100','01110','00101','11110','00100'),
'"': ('01010','01010','00000','00000','00000','00000','00000'),
'=': ('00000','00000','11111','00000','11111','00000','00000'),
'<': ('00010','00100','01000','10000','01000','00100','00010'),
'>': ('01000','00100','00010','00001','00010','00100','01000'),
}
F5_ADV = {'i': 4, 'j': 4, 'l': 4, ' ': 4, '.': 4, ',': 4, "'": 3, '!': 4,
          ':': 4, ';': 4, '(': 4, ')': 4, '/': 5, '%': 6, '1': 5, '\u00b7': 4}

def w5(s, sc=1):
    return sum(F5_ADV.get(ch, 6) * sc for ch in s) - sc

def draw5(cv, x, y, s, c, sc=1):
    cx = x
    for ch in s:
        g = F5.get(ch)
        if g is None:
            cx += 6 * sc
            continue
        for r in range(7):
            row = g[r]
            for cc in range(5):
                if row[cc] == '1':
                    cv.rect(cx + cc * sc, y + r * sc, sc, sc, c)
        cx += F5_ADV.get(ch, 6) * sc
    return cx

def wrap5(s, maxw, sc=1):
    words = s.split(' ')
    lines, cur = [], ''
    for wd in words:
        t = (cur + ' ' + wd).strip()
        if w5(t, sc) <= maxw or not cur:
            cur = t
        else:
            lines.append(cur)
            cur = wd
    if cur:
        lines.append(cur)
    return lines

# ---- Slab-serif display font (masthead, hero headlines, section headers).
# Stroke-based: each glyph is a list of segments in font units.
# Cap top y=0, baseline y=12, descenders to y=15. Feet are baked in as
# short horizontal ticks at the ends of vertical stems. ----
D = {
'A': [((0,12),(5,0)),((5,0),(10,12)),((2,8),(8,8)),((0,12),(2,12)),((8,12),(10,12))],
'B': [((1,0),(1,12)),((1,0),(7,0)),((7,0),(9,2)),((9,2),(9,4)),((9,4),(7,6)),((7,6),(1,6)),((7,6),(9,8)),((9,8),(9,10)),((9,10),(7,12)),((7,12),(1,12)),((0,12),(2,12))],
'C': [((9,2),(6,0)),((6,0),(3,0)),((3,0),(1,3)),((1,3),(1,9)),((1,9),(3,12)),((3,12),(6,12)),((6,12),(9,10))],
'D': [((1,0),(1,12)),((1,0),(7,0)),((7,0),(10,3)),((10,3),(10,9)),((10,9),(7,12)),((7,12),(1,12)),((0,12),(2,12))],
'E': [((1,0),(1,12)),((1,0),(9,0)),((1,6),(7,6)),((1,12),(9,12)),((0,12),(2,12))],
'F': [((1,0),(1,12)),((1,0),(9,0)),((1,6),(7,6)),((0,12),(2,12))],
'G': [((9,2),(6,0)),((6,0),(3,0)),((3,0),(1,3)),((1,3),(1,9)),((1,9),(3,12)),((3,12),(6,12)),((6,12),(9,10)),((6,8),(10,8)),((10,8),(10,12))],
'H': [((1,0),(1,12)),((9,0),(9,12)),((1,6),(9,6)),((0,12),(2,12)),((8,12),(10,12))],
'I': [((5,0),(5,12)),((2,0),(8,0)),((2,12),(8,12))],
'J': [((8,0),(8,9)),((8,9),(6,12)),((6,12),(3,12)),((3,12),(1,10)),((5,0),(9,0))],
'K': [((1,0),(1,12)),((1,7),(9,0)),((4,6),(9,12)),((0,12),(2,12))],
'L': [((1,0),(1,12)),((1,12),(9,12)),((0,12),(2,12))],
'M': [((1,0),(1,12)),((12,0),(12,12)),((1,0),(6,6)),((6,6),(12,0)),((0,12),(2,12)),((11,12),(13,12))],
'N': [((1,0),(1,12)),((10,0),(10,12)),((1,0),(10,12)),((0,12),(2,12)),((9,12),(11,12))],
'O': [((3,0),(7,0)),((7,0),(10,3)),((10,3),(10,9)),((10,9),(7,12)),((7,12),(3,12)),((3,12),(0,9)),((0,9),(0,3)),((0,3),(3,0))],
'P': [((1,0),(1,12)),((1,0),(7,0)),((7,0),(9,2)),((9,2),(9,4)),((9,4),(7,6)),((7,6),(1,6)),((0,12),(2,12))],
'Q': [((3,0),(7,0)),((7,0),(10,3)),((10,3),(10,9)),((10,9),(7,12)),((7,12),(3,12)),((3,12),(0,9)),((0,9),(0,3)),((0,3),(3,0)),((6,9),(10,13))],
'R': [((1,0),(1,12)),((1,0),(7,0)),((7,0),(9,2)),((9,2),(9,4)),((9,4),(7,6)),((7,6),(1,6)),((5,6),(10,12)),((0,12),(2,12))],
'S': [((9,2),(7,0)),((7,0),(3,0)),((3,0),(1,2)),((1,2),(1,4)),((1,4),(3,6)),((3,6),(7,6)),((7,6),(9,8)),((9,8),(9,10)),((9,10),(7,12)),((7,12),(3,12)),((3,12),(1,10))],
'T': [((0,0),(10,0)),((5,0),(5,12)),((3,12),(7,12))],
'U': [((1,0),(1,9)),((1,9),(3,12)),((3,12),(7,12)),((7,12),(9,9)),((9,9),(9,0)),((0,0),(2,0)),((8,0),(10,0))],
'V': [((0,0),(5,12)),((5,12),(10,0)),((0,0),(2,0)),((8,0),(10,0))],
'W': [((0,0),(3,12)),((3,12),(6,5)),((6,5),(9,12)),((9,12),(12,0)),((0,0),(2,0)),((10,0),(12,0))],
'X': [((0,0),(10,12)),((10,0),(0,12))],
'Y': [((0,0),(5,6)),((5,6),(10,0)),((5,6),(5,12)),((3,12),(7,12))],
'Z': [((0,0),(10,0)),((10,0),(0,12)),((0,12),(10,12))],
'0': [((3,0),(7,0)),((7,0),(10,3)),((10,3),(10,9)),((10,9),(7,12)),((7,12),(3,12)),((3,12),(0,9)),((0,9),(0,3)),((0,3),(3,0)),((3,9),(7,3))],
'1': [((2,3),(6,0)),((6,0),(6,12)),((3,12),(8,12))],
'2': [((1,3),(3,0)),((3,0),(7,0)),((7,0),(9,3)),((9,3),(9,6)),((9,6),(1,12)),((1,12),(9,12))],
'3': [((2,1),(5,0)),((5,0),(8,1)),((8,1),(9,4)),((9,4),(6,6)),((9,4),(9,8)),((9,8),(8,11)),((8,11),(5,12)),((5,12),(2,11))],
'4': [((7,0),(7,12)),((1,8),(8,8)),((7,0),(1,8))],
'5': [((1,0),(8,0)),((1,0),(1,5)),((1,5),(7,5)),((7,5),(9,7)),((9,7),(9,10)),((9,10),(7,12)),((7,12),(3,12)),((3,12),(1,10))],
'6': [((8,0),(4,0)),((4,0),(1,3)),((1,3),(1,9)),((1,9),(3,12)),((3,12),(7,12)),((7,12),(9,9)),((9,9),(9,7)),((9,7),(7,5)),((7,5),(4,5)),((4,5),(2,7))],
'7': [((1,0),(9,0)),((9,0),(4,12))],
'8': [((2,1),(5,0)),((5,0),(8,1)),((8,1),(9,3)),((9,3),(8,5)),((8,5),(5,6)),((5,6),(2,5)),((2,5),(1,3)),((1,3),(2,1)),((2,7),(5,6)),((5,6),(8,7)),((8,7),(9,9)),((9,9),(8,11)),((8,11),(5,12)),((5,12),(2,11)),((2,11),(1,9)),((1,9),(2,7))],
'9': [((1,11),(5,12)),((5,12),(8,10)),((8,10),(9,7)),((9,7),(9,3)),((9,3),(7,0)),((7,0),(3,0)),((3,0),(1,2)),((1,2),(1,5)),((1,5),(3,7)),((3,7),(6,7)),((6,7),(8,5))],
}
DADV = {'I': 9, 'J': 9, '1': 9, 'M': 14, 'W': 13, ' ': 5, '.': 5, ',': 5,
        "'": 4, ':': 5, ';': 5, '!': 6, '?': 10, '-': 8, '\u2013': 10,
        '\u2014': 12, '(': 6, ')': 6, '/': 8, '%': 12, '+': 10, '\u00b7': 5,
        '~': 11, 'i': 5, 'j': 5, 'l': 5, 't': 7, 'f': 7, 'r': 7}

D.update({
'a': [((8,4),(8,12)),((1,6),(3,4)),((3,4),(6,4)),((6,4),(8,6)),((8,6),(8,9)),((8,9),(6,12)),((6,12),(3,12)),((3,12),(1,10)),((1,10),(1,7))],
'b': [((1,0),(1,12)),((1,6),(4,5)),((4,5),(7,6)),((7,6),(7,10)),((7,10),(4,12)),((4,12),(1,11)),((0,12),(2,12))],
'c': [((8,6),(5,4)),((5,4),(2,5)),((2,5),(1,8)),((1,8),(2,11)),((2,11),(5,12)),((5,12),(8,10))],
'd': [((8,0),(8,12)),((1,6),(4,4)),((4,4),(7,6)),((7,6),(7,10)),((7,10),(4,12)),((4,12),(1,10)),((1,10),(1,7)),((7,12),(9,12))],
'e': [((8,8),(6,4)),((6,4),(3,4)),((3,4),(1,6)),((1,6),(1,8)),((1,8),(3,12)),((3,12),(6,12)),((6,12),(8,10)),((1,8),(8,8))],
'f': [((6,1),(4,0)),((4,0),(2,2)),((3,1),(3,12)),((1,4),(7,4))],
'g': [((1,6),(4,4)),((4,4),(7,6)),((7,6),(7,10)),((7,10),(4,12)),((4,12),(1,10)),((1,10),(1,7)),((7,10),(7,14)),((7,14),(5,15)),((5,15),(2,15)),((2,15),(1,13))],
'h': [((1,0),(1,12)),((1,5),(4,4)),((4,4),(7,6)),((7,6),(7,12)),((0,12),(2,12))],
'i': [((4,5),(4,12)),((3,12),(5,12)),((4,1),(4,1))],
'j': [((5,5),(5,14)),((5,14),(3,15)),((3,15),(1,14)),((5,1),(5,1))],
'k': [((1,0),(1,12)),((5,8),(8,4)),((4,7),(8,12)),((0,12),(2,12))],
'l': [((3,0),(3,12)),((2,12),(5,12))],
'm': [((1,4),(1,12)),((1,5),(3,4)),((3,4),(5,6)),((5,6),(5,12)),((5,5),(7,4)),((7,4),(9,6)),((9,6),(9,12)),((0,12),(2,12))],
'n': [((1,4),(1,12)),((1,5),(4,4)),((4,4),(7,6)),((7,6),(7,12)),((0,12),(2,12))],
'o': [((3,4),(6,4)),((6,4),(8,6)),((8,6),(8,10)),((8,10),(6,12)),((6,12),(3,12)),((3,12),(1,10)),((1,10),(1,6)),((1,6),(3,4))],
'p': [((1,4),(1,15)),((1,6),(4,4)),((4,4),(7,6)),((7,6),(7,10)),((7,10),(4,12)),((4,12),(1,11))],
'q': [((1,6),(4,4)),((4,4),(7,6)),((7,6),(7,10)),((7,10),(4,12)),((4,12),(1,10)),((1,10),(1,7)),((8,4),(8,15))],
'r': [((1,4),(1,12)),((1,5),(3,4)),((3,4),(6,5)),((6,5),(6,7)),((0,12),(2,12))],
's': [((7,5),(4,4)),((4,4),(2,5)),((2,5),(2,7)),((2,7),(4,8)),((4,8),(6,8)),((6,8),(8,10)),((8,10),(8,11)),((8,11),(6,12)),((6,12),(3,12)),((3,12),(1,11))],
't': [((4,0),(4,12)),((1,4),(7,4)),((4,12),(6,12))],
'u': [((1,4),(1,10)),((1,10),(3,12)),((3,12),(6,12)),((6,12),(8,10)),((8,10),(8,4))],
'v': [((0,4),(4,12)),((4,12),(8,4))],
'w': [((0,4),(2,12)),((2,12),(4,6)),((4,6),(6,12)),((6,12),(8,4))],
'x': [((1,4),(8,12)),((8,4),(1,12))],
'y': [((0,4),(4,11)),((4,11),(8,4)),((4,11),(3,15))],
'z': [((1,4),(8,4)),((8,4),(1,12)),((1,12),(8,12))],
' ': [],
'.': [((4,11),(4,11))],
',': [((4,11),(4,12)),((4,12),(3,14))],
"'": [((4,0),(3,3))],
':': [((4,4),(4,4)),((4,10),(4,10))],
';': [((4,4),(4,4)),((4,10),(4,11)),((4,11),(3,13))],
'!': [((4,0),(4,9)),((4,11),(4,11))],
'?': [((2,2),(5,0)),((5,0),(8,2)),((8,2),(8,5)),((8,5),(5,7)),((5,7),(4,8)),((4,11),(4,11))],
'-': [((1,7),(9,7))],
'\u2013': [((0,7),(11,7))],
'\u2014': [((0,7),(12,7))],
'(': [((6,0),(3,3)),((3,3),(3,9)),((3,9),(6,12))],
')': [((3,0),(6,3)),((6,3),(6,9)),((6,9),(3,12))],
'/': [((8,0),(2,12))],
'%': [((9,0),(1,12)),((2,2),(2,2)),((7,9),(7,9))],
'+': [((5,2),(5,10)),((1,6),(9,6))],
'\u00b7': [((4,6),(4,6))],
'~': [((1,4),(3,2)),((3,2),(6,4)),((6,4),(8,2)),((8,2),(10,4))],
'$': [((9,2),(7,0)),((7,0),(3,0)),((3,0),(1,2)),((1,2),(1,4)),((1,4),(3,6)),((3,6),(7,6)),((7,6),(9,8)),((9,8),(9,10)),((9,10),(7,12)),((7,12),(3,12)),((3,12),(1,10)),((5,0),(5,12))],
})

def dadv(ch):
    return DADV.get(ch, 11)

def wd(s, sc):
    return sum(dadv(ch) * sc for ch in s) - sc

def draw_d(cv, x, y, s, c, sc, weight=2):
    # s: text; y = top of cap height; sc = pixels per font unit (float ok)
    cx = x
    wdt = max(1, int(round(weight * sc / 2.0)))
    for ch in s:
        segs = D.get(ch)
        if segs is None:
            cx += 11 * sc
            continue
        for (x0, y0), (x1, y1) in segs:
            if x0 == x1 and y0 == y1:
                cv.disc(int(round(cx + x0 * sc)), int(round(y + y0 * sc)),
                        max(1, wdt // 2), c)
            else:
                cv.line(int(round(cx + x0 * sc)), int(round(y + y0 * sc)),
                        int(round(cx + x1 * sc)), int(round(y + y1 * sc)), c, wdt)
        cx += dadv(ch) * sc
    return cx

def wrap_d(s, maxw, sc):
    words = s.split(' ')
    lines, cur = [], ''
    for wd_ in words:
        t = (cur + ' ' + wd_).strip()
        if wd(t, sc) <= maxw or not cur:
            cur = t
        else:
            lines.append(cur)
            cur = wd_
    if cur:
        lines.append(cur)
    return lines

# ---- illustration helpers ----
def star4(cv, x, y, r, c):
    cv.poly([(x, y - r), (x + r // 3, y - r // 3), (x + r, y), (x + r // 3, y + r // 3),
             (x, y + r), (x - r // 3, y + r // 3), (x - r, y), (x - r // 3, y - r // 3)], c)

def city_skyline(cv, x, y, w, h, base, win, seed):
    # deterministic skyline: buildings with lit windows
    s = seed
    bx = x
    while bx < x + w - 8:
        s = (s * 1103515245 + 12345) & 0x7fffffff
        bw = 10 + s % 14
        bh = h * (30 + s % 65) // 100
        cv.rect(bx, y + h - bh, bw, bh, base)
        s = (s * 1103515245 + 12345) & 0x7fffffff
        for wy in range(y + h - bh + 4, y + h - 3, 7):
            for wx in range(bx + 2, bx + bw - 2, 6):
                if (s >> (wx % 7)) & 1:
                    cv.rect(wx, wy, 2, 3, win)
                s = (s * 1103515245 + 12345) & 0x7fffffff
        bx += bw + 2

def hero_cop31(cv, x, y, w, h):
    cv.vgrad(x, y, w, h, DAWN1, DAWN2)
    cv.disc(x + w - 34, y + 26, 15, (250, 226, 140))
    cv.disc(x + w - 34, y + 26, 11, (252, 236, 170))
    # conference table + delegates
    cv.rect(x + 8, y + h - 34, w - 16, 26, (122, 84, 52))
    cv.rect(x + 8, y + h - 38, w - 16, 4, (150, 108, 70))
    for i in range(5):
        dx = x + 24 + i * (w - 48) // 4
        cv.disc(dx, y + h - 52, 8, (232, 196, 160))
        cv.poly([(dx - 12, y + h - 40), (dx + 12, y + h - 40), (dx + 6, y + h - 62), (dx - 6, y + h - 62)], (52, 68, 96) if i % 2 else (96, 52, 60))
    cv.rect(x + w // 2 - 14, y + h - 52, 28, 3, WHITE)
    cv.rect(x + w // 2 - 14, y + h - 49, 28, 2, LGREY)
    # gavel
    cv.rect(x + 18, y + h - 60, 16, 5, (90, 60, 30))
    cv.line(x + 26, y + h - 55, x + 34, y + h - 44, (90, 60, 30), 3)

def hero_bahrain(cv, x, y, w, h):
    cv.vgrad(x, y, w, h, NAVY2, NIGHT)
    cv.disc(x + w - 30, y + 22, 12, (240, 238, 220))
    cv.disc(x + w - 30, y + 22, 9, (250, 248, 235))
    for sx, sy in ((30, 18), (70, 10), (120, 24), (180, 12), (230, 28)):
        star4(cv, x + sx, y + sy, 2, WHITE)
    # base buildings + radar dishes
    cv.rect(x + 10, y + h - 46, 60, 46, (24, 34, 58))
    cv.rect(x + 80, y + h - 58, 74, 58, (28, 40, 66))
    cv.rect(x + 164, y + h - 40, 54, 40, (24, 34, 58))
    for dx in (40, 117, 190):
        cv.line(x + dx, y + h - 58, x + dx, y + h - 84, (150, 150, 150), 2)
        cv.line(x + dx - 12, y + h - 84, x + dx + 12, y + h - 84, (150, 150, 150), 2)
        cv.poly([(x + dx - 10, y + h - 84), (x + dx + 10, y + h - 84), (x + dx, y + h - 70)], (190, 190, 190))
    # flames on two radars
    for fx in (117, 190):
        cv.poly([(x + fx - 7, y + h - 84), (x + fx, y + h - 108), (x + fx + 7, y + h - 84)], (240, 120, 30))
        cv.poly([(x + fx - 4, y + h - 84), (x + fx, y + h - 98), (x + fx + 4, y + h - 84)], (250, 200, 60))
    cv.rect(x + 10, y + h - 8, w - 20, 4, (60, 60, 60))

def hero_kyiv(cv, x, y, w, h):
    cv.vgrad(x, y, w, h, (10, 18, 44), (24, 34, 66))
    for sx, sy in ((24, 14), (60, 26), (110, 12), (160, 20), (210, 10), (260, 22), (300, 14)):
        star4(cv, x + sx, y + sy, 2, WHITE)
    cv.disc(x + w - 34, y + 24, 13, (240, 238, 220))
    # searchlight cones
    cv.poly([(x + 60, y + h), (x + 40, y + 20), (x + 80, y + 20)], (250, 240, 180))
    cv.poly([(x + 220, y + h), (x + 200, y + 30), (x + 240, y + 30)], (250, 240, 180))
    # drones
    for dx, dy in ((120, 34), (180, 22), (250, 40)):
        cv.line(x + dx - 4, y + dy - 4, x + dx + 4, y + dy + 4, (255, 220, 120), 2)
        cv.line(x + dx + 4, y + dy - 4, x + dx - 4, y + dy + 4, (255, 220, 120), 2)
        cv.disc(x + dx, y + dy + 8, 2, (255, 120, 60))
    # explosion glow + city
    cv.disc(x + 150, y + h - 40, 16, (250, 150, 50))
    cv.disc(x + 150, y + h - 40, 9, (255, 210, 90))
    city_skyline(cv, x, y + h - 52, w, 52, (8, 12, 30), (255, 210, 110), 12345)

def card_art(cv, kind, x, y, w, h):
    if kind == 'ballot':
        cv.rect(x, y, w, h, (232, 226, 210))
        cv.rect(x + w // 2 - 16, y + 12, 32, 30, (176, 30, 36))
        cv.rect(x + w // 2 - 16, y + 8, 32, 5, (140, 20, 26))
        cv.rect(x + w // 2 - 9, y + 2, 18, 8, WHITE)
        cv.line(x + w // 2 - 7, y + 6, x + w // 2 - 2, y + 11, RED, 2)
        cv.line(x + w // 2 - 2, y + 11, x + w // 2 + 7, y - 1, RED, 2)
    elif kind == 'race':
        cv.rect(x, y, w, h, (30, 60, 90))
        cv.rect(x + 8, y + h - 22, w - 16, 10, (200, 30, 30))
        cv.poly([(x + w - 34, y + h - 22), (x + w - 14, y + h - 22), (x + w - 20, y + h - 32), (x + w - 40, y + h - 32)], (200, 30, 30))
        cv.disc(x + 26, y + h - 10, 7, INK)
        cv.disc(x + w - 30, y + h - 10, 7, INK)
        for i in range(4):
            cv.rect(x + w - 12 - i * 6, y + 4 + (i % 2) * 6, 6, 6, WHITE if i % 2 == 0 else INK)
    elif kind == 'cricket':
        cv.rect(x, y, w, h, (120, 170, 90))
        cv.line(x + 14, y + 8, x + 30, y + h - 12, (210, 180, 120), 5)
        cv.disc(x + w - 22, y + 16, 8, (176, 30, 36))
        cv.rect(x + w - 46, y + h - 16, 4, 16, (240, 220, 160))
        cv.rect(x + w - 36, y + h - 16, 4, 16, (240, 220, 160))
        cv.rect(x + w - 26, y + h - 16, 4, 16, (240, 220, 160))
    elif kind == 'boat':
        cv.rect(x, y, w, h, (70, 130, 170))
        cv.poly([(x + 8, y + h - 22), (x + w - 8, y + h - 22), (x + w - 18, y + h - 10), (x + 18, y + h - 10)], (120, 80, 40))
        cv.line(x + w // 2, y + h - 22, x + w // 2, y + h - 40, (90, 60, 30), 3)
        cv.poly([(x + w // 2, y + h - 40), (x + w // 2 + 18, y + h - 32), (x + w // 2, y + h - 24)], WHITE)
        cv.line(x + 4, y + h - 6, x + w - 4, y + h - 6, WHITE, 2)
    elif kind == 'power':
        cv.rect(x, y, w, h, (40, 44, 60))
        cv.line(x + w // 2 - 14, y + h - 8, x + w // 2 - 6, y + 8, (200, 200, 200), 3)
        cv.line(x + w // 2 + 14, y + h - 8, x + w // 2 + 6, y + 8, (200, 200, 200), 3)
        cv.line(x + w // 2 - 6, y + 8, x + w // 2 + 6, y + 8, (200, 200, 200), 3)
        cv.poly([(x + w // 2 + 4, y + 12), (x + w // 2 - 4, y + 26), (x + w // 2 + 2, y + 26), (x + w // 2 - 4, y + 40), (x + w // 2 + 6, y + 22), (x + w // 2, y + 22)], (250, 220, 60))
    elif kind == 'star':
        cv.rect(x, y, w, h, (20, 40, 70))
        star4(cv, x + w // 2, y + h // 2 - 2, 16, GOLD)
        cv.disc(x + w // 2, y + h // 2 - 2, 5, (255, 220, 120))
        cv.line(x + 8, y + h - 8, x + w - 8, y + h - 8, WHITE, 2)
    elif kind == 'talks':
        cv.rect(x, y, w, h, (210, 225, 200))
        cv.line(x + 12, y + h - 12, x + w - 12, y + 12, (60, 120, 60), 3)
        for lx, ly in ((20, 34), (30, 26), (42, 18), (52, 12)):
            cv.disc(x + lx, y + ly, 4, (80, 150, 70))
        cv.rect(x + w - 30, y + h - 26, 22, 16, WHITE)
        cv.line(x + w - 30, y + h - 26, x + w - 8, y + h - 26, RED, 2)
    elif kind == 'wemby':
        cv.rect(x, y, w, h, (200, 220, 240))
        cv.rect(x + w - 26, y + 6, 4, 22, (200, 90, 30))
        cv.disc(x + w - 24, y + 32, 7, (200, 90, 30))
        cv.line(x + w - 31, y + 32, x + w - 17, y + 32, (200, 90, 30), 2)
        cv.disc(x + w // 2 - 8, y + h // 2 + 6, 14, (230, 120, 40))
        cv.line(x + w // 2 - 22, y + h // 2 + 6, x + w // 2 + 6, y + h // 2 + 6, INK, 2)
        cv.line(x + w // 2 - 8, y + h // 2 - 8, x + w // 2 - 8, y + h // 2 + 20, INK, 2)
    elif kind == 'tower':
        cv.rect(x, y, w, h, (190, 200, 215))
        cv.poly([(x + w // 2 - 8, y + h - 6), (x + w // 2 + 8, y + h - 6), (x + w // 2 + 4, y + 16), (x + w // 2 - 4, y + 16)], (90, 100, 120))
        cv.rect(x + w // 2 - 10, y + 8, 20, 10, (60, 80, 110))
        cv.line(x + 10, y + h - 14, x + w - 10, y + h - 14, (120, 120, 120), 2)
        cv.line(x + 14, y + h - 20, x + w - 14, y + h - 8, RED, 3)
        cv.line(x + w - 14, y + h - 20, x + 14, y + h - 8, RED, 3)
    elif kind == 'sat':
        cv.rect(x, y, w, h, (12, 16, 34))
        star4(cv, x + 14, y + 12, 2, WHITE)
        star4(cv, x + w - 16, y + 20, 2, WHITE)
        cv.disc(x + w - 20, y + h - 16, 12, (220, 140, 70))
        cv.disc(x + w - 24, y + h - 20, 3, (180, 100, 50))
        cv.disc(x + w - 14, y + h - 10, 2, (180, 100, 50))
        cv.rect(x + w // 2 - 8, y + h // 2 - 4, 16, 8, (200, 200, 200))
        cv.rect(x + w // 2 - 26, y + h // 2 - 2, 16, 4, (60, 90, 160))
        cv.rect(x + w // 2 + 10, y + h // 2 - 2, 16, 4, (60, 90, 160))
    elif kind == 'chip':
        cv.rect(x, y, w, h, (30, 34, 48))
        cv.rect(x + w // 2 - 12, y + h // 2 - 12, 24, 24, (20, 22, 30))
        cv.rect(x + w // 2 - 6, y + h // 2 - 6, 12, 12, (90, 200, 120))
        for px in range(x + w // 2 - 12, x + w // 2 + 13, 6):
            cv.line(px, y + h // 2 - 18, px, y + h // 2 - 12, (180, 180, 180), 2)
            cv.line(px, y + h // 2 + 12, px, y + h // 2 + 18, (180, 180, 180), 2)
        cv.poly([(x + w - 14, y + 8), (x + w - 6, y + 8), (x + w - 10, y + 20)], RED)
    elif kind == 'hospital':
        cv.rect(x, y, w, h, (225, 235, 225))
        cv.rect(x + 10, y + 14, w - 20, h - 22, WHITE)
        cv.rect(x + w // 2 - 8, y + 4, 16, 8, RED)
        cv.rect(x + w // 2 - 4, y + 0, 8, 16, RED)
        for wx in range(x + 16, x + w - 12, 12):
            cv.rect(wx, y + 22, 6, 6, (120, 170, 200))
        cv.rect(x + 10, y + h - 8, w - 20, 4, (150, 150, 150))

# ---- world map: coarse filled continents, equirect-ish, in a 300x150 box ----
CONTINENTS = [
    [(18, 20), (30, 10), (55, 8), (76, 14), (72, 26), (60, 32), (48, 30), (40, 40), (28, 38), (18, 30)],
    [(52, 62), (64, 58), (70, 70), (62, 88), (54, 80)],
    [(140, 14), (160, 8), (176, 16), (168, 28), (150, 30), (142, 22)],
    [(140, 42), (160, 38), (176, 50), (170, 72), (152, 80), (142, 60)],
    [(176, 10), (230, 6), (280, 14), (286, 30), (260, 38), (240, 30), (220, 44), (200, 36), (186, 28)],
    [(245, 78), (275, 74), (282, 86), (255, 90)],
]
def draw_map(cv, x, y, w, h, pins):
    cv.rect(x, y, w, h, NAVY)
    sx, sy = w / 300.0, h / 150.0
    for poly in CONTINENTS:
        pts = [(x + int(px * sx), y + int(py * sy)) for px, py in poly]
        cv.poly(pts, (222, 210, 185))
    for num, lon, lat in pins:
        px = x + int((lon + 180) / 360.0 * w)
        py = y + int((90 - lat) / 180.0 * h)
        cv.disc(px, py, 7, RED)
        cv.disc(px, py, 5, (255, 255, 255))
        draw5(cv, px - 2, py - 3, str(num), RED, 1)

# ---- story data ----
HEROES = [
    dict(n=1, place='ANTALYA, TURKIYE', region='WORLD', tag='REPORTED',
         art='cop31', head="Climate deal lands with no mention of fossil fuels",
         deck="Ten-page package drops the $120bn adaptation target, keeps a 35% electricity goal for 2035, admits the world will overshoot 1.5C. Objections close 03:00 GMT.",
         src='Sources: BBC \u00b7 Reuters \u00b7 Guardian'),
    dict(n=2, place='MANAMA, BAHRAIN', region='MIDDLE EAST', tag='CLAIM',
         art='bahrain', head='Iran claims strikes on US bases in Bahrain',
         deck='IRGC says it hit two Patriot radars at al-Riffa and Awali Sakir; Bahrain says its defences intercepted the attack and only a civilian site burned. No casualties.',
         src='Sources: Al Jazeera \u00b7 Reuters \u00b7 IRGC statement'),
    dict(n=3, place='KYIV, UKRAINE', region='EUROPE', tag='REPORTED',
         art='kyiv', head="Russia's overnight barrage: 186 drones, 161 downed",
         deck='Moscow fires 186 drones and three ballistic missiles overnight; air defences shoot down or jam 161. Strikes at 18 sites.',
         src='Sources: Ukrainian Air Force \u00b7 Kyiv Independent'),
]
CARDS = [
    (4, 'ASIA-PAC', 'HONG KONG', 'ballot', 'Hong Kong elects its Election Committee',
     '856 candidates for 723 seats; turnout 93.55% by 14:00.', 'CONFIRMED', 'SCMP'),
    (5, 'AMERICAS', 'LAS VEGAS GP', 'race', 'Verstappen wins the Las Vegas GP',
     'Beats Norris and Piastri; Russell hits the wall late, finishes 9th.', 'CONFIRMED', 'Reuters \u00b7 F1'),
    (6, 'OCEANIA', 'WELLINGTON', 'cricket', 'India declare 720/9 \u2014 a record in NZ',
     'Pant 128, Rahul 136; highest total ever in New Zealand.', 'CONFIRMED', 'Reuters \u00b7 AP'),
    (7, 'AFRICA', 'BAYELSA', 'boat', 'Bayelsa boat toll rises to 26',
     "Mourners' boat capsized Friday; recovery goes on.", 'REPORTED', 'RIA \u00b7 Vanguard'),
    (8, 'MIDDLE EAST', 'TEHRAN', 'power', 'Iran starts rationing electricity',
     'Two-hour daily cuts begin as gas output falls.', 'REPORTED', 'Tavani \u00b7 RFE/RL'),
    (9, 'AMERICAS', 'SINALOA', 'star', "'El Chapo Isidro' caught in Sinaloa",
     'FBI top-ten fugitive held after a shoot-out; 11 dead.', 'CONFIRMED', 'Sky News \u00b7 BBC'),
    (10, 'MIDDLE EAST', 'GAZA CITY', 'talks', 'Hamas seeks urgent talks after aid strike',
     'Three die in a drone strike on a food vehicle in Gaza City.', 'REPORTED', 'Al Jazeera \u00b7 Anadolu'),
    (11, 'AMERICAS', 'SAN ANTONIO', 'wemby', 'Wembanyama drops 50 \u2014 a first in NBA history',
     "50 pts, 19 reb, 5 blocks, 4 steals in Spurs' 114\u201391 win.", 'CONFIRMED', 'Reuters \u00b7 AP'),
    (12, 'EUROPE', 'BRUSSELS', 'tower', "Belgian controllers join Monday's strike",
     'No normal ATC Mon 07:00\u201321:00; most Brussels flights off.', 'REPORTED', 'Belga \u00b7 AFP'),
    (13, 'WORLD', 'MERCURY', 'sat', 'BepiColombo enters Mercury orbit',
     'After an eight-year journey; first observations begin.', 'REPORTED', 'AP \u00b7 ESA'),
    (14, 'AMERICAS', 'WASHINGTON', 'chip', 'Nvidia faces an SEC probe',
     'Accounting inquiry at an early stage as AI shares slide.', 'REPORTED', 'Straits Times \u00b7 CNBC'),
    (15, 'AMERICAS', 'BRASILIA', 'hospital', 'Bolsonaro in intensive care',
     'Bowel obstruction, stable, breathing on his own.', 'CONFIRMED', 'Al Jazeera \u00b7 Reuters'),
]
ALSO = [
    (16, 'Kryvyi Rih missile: 2 killed, 58 hurt \u2014 BBC'),
    (17, 'Sparta II ablaze; all 16 crew off \u2014 Reuters'),
    (18, 'Saudi downs Houthi missile aimed at Riyadh'),
    (19, 'EU and Indonesia sign trade deal \u2014 DW'),
    (20, "Germany's coalition talks grind on"),
    (21, 'England hammer New Zealand 37-12 \u2014 Reuters'),
    (22, 'Premier League: Leeds 4-1 Chelsea; Arsenal 2-2'),
    (23, 'Sanchez faces TV debate before Spain votes 29 Nov'),
    (24, 'Lebanon: Aoun demands Israel withdrawal \u2014 Al Jazeera'),
    (25, 'Israel: Eisenkot invites Likud to coalition talks'),
    (26, 'West Bank killing probed'),
    (27, 'Cikande factory fire: 3 dead, 36 missing \u2014 Reuters'),
    (28, 'Pakistan FM hopes for US-Iran deal'),
    (29, 'Japan Tobacco books $8.9bn Russia loss'),
    (30, 'Manipur toxic-liquor toll rises to 19'),
    (31, 'St Johns River breaks flood record; crest due Sunday'),
    (32, 'Peru quake toll: 1 dead, 16 hurt'),
    (33, 'Sudan: army seizes Bau district in Blue Nile'),
    (34, 'Congo: leaders meet in Oyo on Sunday'),
    (35, 'UNICEF: 1,144 children killed or hurt in Ukraine'),
]
PINS = [(1, 30.7, 36.9), (2, 50.6, 26.2), (3, 30.5, 50.5), (4, 114.2, 22.3),
        (5, -115.1, 36.2), (6, 174.8, -41.3), (7, 6.3, 4.9), (8, 51.4, 35.7),
        (9, -108.5, 25.6), (10, 34.5, 31.5), (11, -98.5, 29.4), (12, 4.35, 50.85),
        (14, -77.0, 38.9), (15, -47.9, -15.8)]
REGIONS = [('EUROPE', 9, (0, 90, 130)), ('MIDDLE EAST', 7, RED),
           ('ASIA-PAC', 5, (200, 120, 0)), ('AMERICAS', 7, TEAL),
           ('AFRICA', 3, (140, 100, 40)), ('OCEANIA', 1, (110, 80, 160)),
           ('WORLD', 3, (90, 90, 90))]
STRIP = [('~200', 'NATIONS AT THE COP31 TALKS'), ('03:00', 'GMT DEADLINE FOR OBJECTIONS'),
         ('186', 'DRONES FIRED AT UKRAINE OVERNIGHT'), ('2', 'US BASES TARGETED IN BAHRAIN'),
         ('856', 'CANDIDATES IN HONG KONG VOTE'), ('720/9', "INDIA'S RECORD TOTAL IN NZ")]
UTC = [('03:00', 'COP31 objections close'), ('05:11', 'Hamas seeks talks'),
       ('05:30', 'Las Vegas GP ends'), ('06:00', 'COP31 approval'),
       ('08:00', '161 of 186 downed'), ('14:00', 'HK turnout 93.55%')]

def bold5(cv, x, y, s, c, sc=1):
    draw5(cv, x, y, s, c, sc)
    draw5(cv, x + sc, y, s, c, sc)

def tagbox(cv, x, y, label, c):
    wpx = w5(label, 1) + 8
    cv.rect(x, y, wpx, 11, c)
    draw5(cv, x + 4, y + 2, label, WHITE, 1)
    return wpx

def render():
    cv = Canvas(W, H, PAPER)
    # kicker bar
    cv.rect(0, 0, W, 22, NAVY)
    draw5(cv, 16, 7, 'THE WORLD IN ONE DAY', GOLD, 1)
    r = '35 STORIES \u00b7 7 REGIONS \u00b7 EVERY ONE DATED SUNDAY 22 NOVEMBER 2026'
    draw5(cv, W - 16 - w5(r, 1), 7, r, WHITE, 1)
    # masthead (slab-serif display font)
    mh = 'Sunday 22 November 2026'
    sc = 3.9
    mw = wd(mh, sc)
    draw_d(cv, int((W - mw) / 2), 28, mh, NAVY, sc, weight=2)
    cv.hline(14, W - 14, 80, NAVY, 2)
    # deck (display font, red, centered, wrapped)
    deck = "COP31's final text lands at dawn \u00b7 Iran claims strikes on US bases in Bahrain \u00b7 186 drones over Ukraine overnight"
    dy = 86
    for ln in wrap_d(deck, 990, 0.95):
        lw = wd(ln, 0.95)
        draw_d(cv, int((W - lw) / 2), dy, ln, RED, 0.95, weight=2)
        dy += 15
    # numbers strip
    y0 = 118
    cw = 996 // 6
    for i, (num, lab) in enumerate(STRIP):
        cx0 = 14 + i * cw
        if i:
            cv.vline(cx0, y0 + 2, y0 + 48, LGREY, 1)
        nw = wd(num, 2.3)
        draw_d(cv, int(cx0 + (cw - nw) / 2), y0, num, RED, 2.3, weight=2)
        for j, ln in enumerate(wrap5(lab, cw - 10, 1)):
            lw = w5(ln, 1)
            draw5(cv, int(cx0 + (cw - lw) / 2), y0 + 32 + j * 9, ln, GREY, 1)
    cv.hline(14, W - 14, y0 + 52, INK, 1)
    # region bar
    y0 = 174
    rw = 996 // 7
    for i, (name, cnt, col) in enumerate(REGIONS):
        cx0 = 14 + i * rw
        wdt = rw if i < 6 else 996 - 6 * rw
        cv.rect(cx0, y0, wdt, 20, col)
        t = name + ' ' + str(cnt)
        draw5(cv, int(cx0 + (wdt - w5(t, 1)) / 2), y0 + 6, t, WHITE, 1)
    # UTC strip
    y0 = 196
    cv.rect(0, y0, W, 18, NAVY2)
    draw5(cv, 16, y0 + 5, 'THE DAY IN UTC', GOLD, 1)
    ux = 16 + w5('THE DAY IN UTC', 1) + 12
    for tm, tx in UTC:
        draw5(cv, ux, y0 + 5, tm, GOLD, 1)
        ux += w5(tm, 1) + 4
        draw5(cv, ux, y0 + 5, tx, WHITE, 1)
        ux += w5(tx, 1) + 6
        if ux < W - 16:
            cv.disc(ux - 3, y0 + 9, 1, GOLD)
    # heroes
    hy, hh = 218, 258
    for i, hro in enumerate(HEROES):
        hx = 14 + i * 334
        hw = 322
        if hro['art'] == 'cop31':
            hero_cop31(cv, hx, hy, hw, 128)
        elif hro['art'] == 'bahrain':
            hero_bahrain(cv, hx, hy, hw, 128)
        else:
            hero_kyiv(cv, hx, hy, hw, 128)
        ty = hy + 132
        draw5(cv, hx, ty, str(hro['n']) + ' \u00b7 ' + hro['place'] + ' \u00b7 ' + hro['region'], INK, 1)
        tagbox(cv, hx + hw - 62, ty - 1, hro['tag'], RED if hro['tag'] != 'CONFIRMED' else (0, 120, 60))
        hy2 = ty + 16
        for ln in wrap_d(hro['head'], hw, 1.5):
            draw_d(cv, hx, hy2, ln, INK, 1.5, weight=2)
            hy2 += 21
        hy2 += 2
        for ln in wrap5(hro['deck'], hw, 1):
            draw5(cv, hx, hy2, ln, (60, 60, 56), 1)
            hy2 += 9
        draw5(cv, hx, hy2 + 2, hro['src'], GREY, 1)
    # section header
    y0 = 492
    draw_d(cv, 14, y0, 'THE DAY IN TWELVE', INK, 1.35, weight=2)
    rt = 'THE STORIES THAT MOVED THE WORLD TODAY'
    draw5(cv, W - 14 - w5(rt, 1), y0 + 6, rt, GREY, 1)
    cv.hline(14, W - 14, y0 + 20, INK, 1)
    # cards: 3 rows x 4 cols
    for r in range(3):
        for cix in range(4):
            idx = r * 4 + cix
            if idx >= len(CARDS):
                break
            n, reg, place, art, head, deck, tag, src = CARDS[idx]
            cx0 = 14 + cix * 251
            cy0 = 516 + r * 104
            cw2, ch2 = 243, 100
            card_art(cv, art, cx0, cy0, cw2, 46)
            cv.disc(cx0 + 10, cy0 + 10, 8, RED)
            draw5(cv, cx0 + 7, cy0 + 7, str(n), WHITE, 1)
            draw5(cv, cx0, cy0 + 50, reg + ' \u00b7 ' + place, RED, 1)
            ly = cy0 + 60
            for ln in wrap5(head, cw2, 1):
                bold5(cv, cx0, ly, ln, INK, 1)
                ly += 9
                if ly > cy0 + 67:
                    break
            for ln in wrap5(deck, cw2, 1):
                draw5(cv, cx0, ly, ln, (60, 60, 56), 1)
                ly += 8
                if ly > cy0 + 84:
                    break
            draw5(cv, cx0, cy0 + 93, tag + ' \u00b7 ' + src, GREY, 1)
    # map + ALSO
    y0 = 830
    draw5(cv, 14, y0, 'WHERE IT HAPPENED \u2014 PINS MATCH STORY NUMBERS', INK, 1)
    draw_map(cv, 14, y0 + 12, 282, 100, PINS)
    draw5(cv, 14, y0 + 116, '13 BepiColombo is at Mercury \u2014 no pin on Earth.', GREY, 1)
    ax = 310
    draw5(cv, ax, y0, 'ALSO ON SUNDAY 22 NOVEMBER \u2014 20 MORE STORIES', RED, 1)
    for j, (n, txt) in enumerate(ALSO):
        col = 0 if j < 10 else 1
        row = j % 10
        tx = ax + col * 352
        ty2 = y0 + 14 + row * 11
        draw5(cv, tx, ty2, str(n), RED, 1)
        draw5(cv, tx + 16, ty2, txt, INK, 1)
    # DATE CHECK
    y0 = 956
    cv.frame(14, y0, 996, 44, RED, 2)
    dc = ("WIRES READ UP TO 14:00 UTC. Every story here was reported, or still developing, "
          "on 22 November in at least one time zone. Left out on purpose: the Peru quake "
          "(Fri 20 Nov), Russia's 400-drone barrage (19\u201320 Nov) and the Shenzhen summit "
          "(19 Nov). Tonight's barrage was 186, not 400.")
    draw5(cv, 20, y0 + 5, 'DATE CHECK \u2014 READ THIS FIRST', RED, 1)
    dlines = wrap5(dc, 996 - 20 - w5('DATE CHECK \u2014 READ THIS FIRST', 1) - 16, 1)
    dx = 20 + w5('DATE CHECK \u2014 READ THIS FIRST', 1) + 8
    for j, ln in enumerate(dlines[:2]):
        draw5(cv, dx, y0 + 5 + j * 10, ln, INK, 1)
    draw5(cv, 20, y0 + 28, 'NOT YET: COP31 adoption vote (plenary slipped past 11:00 Antalya) \u00b7 Spain votes 29 Nov \u00b7 G20 peace talks ahead \u00b7 Killer-robot rules by 2028.', INK, 1)
    # footer
    draw5(cv, 14, 1004, 'HOW TO READ THE TAGS \u2014 CONFIRMED = reported by the named source \u00b7 REPORTED = wire-reported, not yet confirmed \u00b7 CLAIM = one side\u2019s account, contested.', GREY, 1)
    draw5(cv, 14, 1013, 'SCENES ARE DRAWN ILLUSTRATIONS, NOT PHOTOGRAPHS. SOURCES: BBC \u00b7 REUTERS \u00b7 AL JAZEERA \u00b7 THE GUARDIAN \u00b7 AP \u00b7 SCMP \u00b7 DW \u00b7 UPI \u00b7 FT \u00b7 UKRAINIAN AIR FORCE \u00b7 ESA', GREY, 1)
    return cv

def main():
    out = os.environ.get('MAKEFUN_OUTPUT_DIR', '/output')
    os.makedirs(out, exist_ok=True)
    cv = render()
    data = png_bytes(W, H, cv.px)
    with open(os.path.join(out, 'entry.png'), 'wb') as f:
        f.write(data)

if __name__ == '__main__':
    main()
