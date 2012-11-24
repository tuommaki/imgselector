#!/usr/bin/env python
#
# This program is free software. It comes without any warranty, to
# the extent permitted by applicable law. You can redistribute it
# and/or modify it under the terms of the Do What The Fuck You Want
# To Public License, Version 2, as published by Sam Hocevar. See
# http://sam.zoy.org/wtfpl/COPYING for more details.


import pygtk
pygtk.require('2.0')
import gtk
import os
import sys
import shutil


def iterdirwalk(path):
    for root, dirs, files in os.walk(path):
        for f in files:
            yield os.path.join(root, f)
        for d in dirs:
            iterdirwalk(d)


class ImageSelector:

    def on_key_press(self, widget, data=None):
        if data.string in self._key_actions:
            self._key_actions[data.string]()

    def delete_event(self, widget, event, data=None):
        return False

    def destroy(self, widget, data=None):
        gtk.main_quit()

    def next_img(self):
        next_idx = self.images.index(self.cur_image) + 1
        if next_idx == len(self.images):
            try:
                self.cur_image = self.img_iterator.next()
            except StopIteration:
                return
            self.images.append(self.cur_image)
        else:
            self.cur_image = self.images[next_idx]
        self.redraw_img()

    def prev_img(self):
        prev_idx = self.images.index(self.cur_image) - 1
        if prev_idx >= 0:
            self.cur_image = self.images[prev_idx]
            self.redraw_img()

    def add_img(self):
        img_path = self.get_dst_image()

        # If file is already copied, there's no point to do it again
        if os.path.isfile(img_path):
            return

        # Check that destination directory exists
        img_dir = os.path.dirname(img_path)
        if not os.path.exists(img_dir):
            os.makedirs(img_dir)

        # And copy
        shutil.copyfile(self.cur_image, img_path)

    def del_img(self):
        img_path = self.get_dst_image()

        # Only remove if dst file exists - Doh!
        if os.path.exists(img_path):
            os.remove(img_path)

    def redraw_img(self):
        self.image.set_from_file(self.cur_image)

    def get_dst_image(self):
        # Remove root path
        img_path = self.cur_image[len(self.src_path):]
        # Remove possible leading '/'
        if img_path[0] == '/':
            img_path = img_path[1:]
        # Construct dest path
        img_path = os.path.join(self.dst_path, img_path)
        return img_path

    def quit(self):
        self.destroy(self.window)

    def __init__(self):
        if len(sys.argv) < 3:
            print "usage: imgselector <src path> <dst path>"
            sys.exit(1)

        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.image = gtk.Image()

        self.window.connect("delete_event", self.delete_event)
        self.window.connect("destroy", self.destroy)
        self.window.connect("key_press_event", self.on_key_press)
        self.window.add(self.image)

        self.image.show()
        self.window.show()

        self.src_path = sys.argv[1]
        self.dst_path = sys.argv[2]
        self.img_iterator = iterdirwalk(self.src_path)
        try:
            self.cur_image = self.img_iterator.next()
        except StopIteration:
            print "No files in source path"
            sys.exit(2)

        self.images = [self.cur_image]
        self.redraw_img()

        self._key_actions = {
            'h': self.prev_img,
            'l': self.next_img,
            ' ': self.add_img,
            'd': self.del_img,
            'q': self.quit,
        }

    def main(self):
        gtk.main()

if __name__ == "__main__":
    imgselector = ImageSelector()
    imgselector.main()
