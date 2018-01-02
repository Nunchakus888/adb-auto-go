# coding: u8

from __future__ import print_function, unicode_literals

import colorsys
import commands
import itertools
import math
import time
import traceback

from PIL import Image, ImageDraw


class Otsu(object):

    def __init__(self, path, debug=False):
        self.im = Image.open(path)

        self.w, self.h = self.im.size
        self.pixels = self.im.load()
        self.draw = ImageDraw.Draw(self.im)

        self.hero_pos = self.find_hero()
        print('hero pos:', self.hero_pos)

        is_hero_on_left = self.hero_pos[0] < self. w / 2

        bg_hsv = self.get_background_hsv()
        print('background hsv:', bg_hsv)

        top_most, lr_most = self.find_most(is_hero_on_left, bg_hsv)
        print('top most pos：', top_most)
        print('left/right most pos', lr_most)

        self.center_pos = top_most[0], lr_most[1]
        print('center pos', self.center_pos)

        if debug:
            #self.erase_background(bg_hsv)
            self.draw_pos(self.hero_pos)
            self.draw_pos(top_most)
            self.draw_pos(lr_most)
            self.draw_pos(self.center_pos)

            cx, cy = self.center_pos
            hx, hy = self.hero_pos
            self.draw.line((cx, cy, hx, hy), fill=(0, 255, 0), width=8)

            self.im.show()

    def find_hero(self):
        hero_poses = []
        for y in xrange(self.h / 3, self.h * 2 / 3):
            for x in xrange(self.w):
                # is purple
                if self.pixels[x, y] == (56, 56, 97, 255):
                    hero_poses.append((x, y))
        # calc the avg pos
        return map(lambda i: sum(i) / len(i), itertools.izip(*hero_poses))

    def rgb_to_hsv(self, r, g, b, a=255):
        h, s, v = colorsys.rgb_to_hsv(r / 255., g / 255., b / 255.)
        return int(h * 255.), int(s * 255.), int(v * 255.)

    def get_background_hsv(self):
        # use the (10, 800) as the background color
        bg_color = self.pixels[10, 800]
        return self.rgb_to_hsv(*bg_color)

    def erase_background(self, bg_hsv):
        for y in xrange(self.h / 4, self.h * 2 / 3):
            for x in xrange(self.w):
                h, s, v = self.rgb_to_hsv(*self.pixels[x, y])
                if self.is_same_color(h, s, v, bg_hsv):
                    self.im.putpixel((x, y), (0, 0, 0))
                else:
                    self.im.putpixel((x, y), (255, 255, 255))

    def find_most(self, is_hero_on_left, bg_hsv):
        hero_r = 15
        if is_hero_on_left:
            # top most is on the right, scan from right
            from_x = self.w - 1
            to_x = self.hero_pos[0] + hero_r
            step = -1
        else:
            # top most is on the left, scan from left
            from_x = 0
            to_x = self.hero_pos[0] - hero_r
            step = 1

        from_y, to_y = self.h / 4, self.hero_pos[1]

        top_most = self.find_top_most(bg_hsv, from_x, to_x, from_y, to_y, step)
        lr_most = self.find_lr_most(bg_hsv, from_x, to_x, from_y, to_y, step)
        return top_most, lr_most

    def find_top_most(self, bg_hsv, from_x, to_x, from_y, to_y, step):
        for y in xrange(from_y, to_y):
            for x in xrange(from_x, to_x, step):
                h, s, v = self.rgb_to_hsv(*self.pixels[x, y])
                if not self.is_same_color(h, s, v, bg_hsv):
                    return x, y

    def find_lr_most(self, bg_hsv, from_x, to_x, from_y, to_y, step):
        for x in xrange(from_x, to_x, step):
            for y in xrange(from_y, to_y):
                h, s, v = self.rgb_to_hsv(*self.pixels[x, y])
                if not self.is_same_color(h, s, v, bg_hsv):
                    return x, y

    def is_same_color(self, h, s, v, bg_hsv):
        bg_h, bg_s, bg_v = bg_hsv
        return (abs(h - bg_h) < 15) and (abs(s - bg_s) < 20)

    def draw_pos(self, pos, color=(0, 255, 0)):
        x, y = pos
        r = 25
        self.draw.ellipse((x, y, x + r, y + r), fill=color, outline=color)

    def get_holding(self):
        line_length = int(math.sqrt(
            pow(self.center_pos[0] - self.hero_pos[0], 2) + \
            pow(self.center_pos[1] - self.hero_pos[1], 2)
        ))

        length_time = line_length * 1.5

        holding = min(950, max(length_time, 300))

        print('length, duration, holding: ', line_length, length_time, holding)

        return int(holding)


def run_cmd(cmd):
    a = commands.getstatusoutput(cmd)
    print('-----', cmd)
    return a


jump_times = itertools.count(0)
adb_path = '/Users/nunchakus/tools/android/platform-tools/adb'
while True:
    try:
        debug = False

        if debug:
            fn = 's'
        else:
            fn = str(next(jump_times))
            run_cmd(adb_path + ' shell screencap -p /sdcard/s.png')
            run_cmd(adb_path + ' pull /sdcard/s.png /tmp/{}.png'.format(fn))
            run_cmd('cp /tmp/{}.png /tmp/s.png'.format(fn))
            print(fn)

        holding = Otsu('/tmp/{}.png'.format(fn), debug=debug).get_holding()

        if debug:
            raise KeyboardInterrupt
        else:
            run_cmd(adb_path + ' shell input swipe 255 255 0 0 {}'.format(holding))
            time.sleep(2)
    except KeyboardInterrupt:
        raise KeyboardInterrupt
    except Exception as e:
        traceback.print_exc()
        time.sleep(2)
