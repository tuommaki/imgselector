#!/usr/bin/env python
#
# This program is free software. It comes without any warranty, to
# the extent permitted by applicable law. You can redistribute it
# and/or modify it under the terms of the Do What The Fuck You Want
# To Public License, Version 2, as published by Sam Hocevar. See
# http://sam.zoy.org/wtfpl/COPYING for more details.


import pygtk
pygtk.require('2.0')
import glib
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

    def next_image(self):
        # Draw pre-fetched image
        self.draw_image(self.pixbuf)
        # Set the current image 'pointer'
        self.cur_image_file = self.next_image_file
        # And pre-fetch a next one
        self.pre_fetch_next_image()

    def pre_fetch_next_image(self):
        # Initialize next image path
        next_idx = self.images.index(self.cur_image_file) + 1
        if next_idx == len(self.images):
            try:
                self.next_image_file = self.image_iterator.next()
            except StopIteration:
                return
            self.images.append(self.next_image_file)
        else:
            self.next_image_file = self.images[next_idx]

        # And try to load it
        try:
            self.pixbuf = self.load_image(self.next_image_file)
        except glib.GError:
            # Couldn't load file - throw away the "current" next image and
            # fetch a next image if such exists
            self.images.pop()
            self.next_image_file = self.cur_image_file
            self.pre_fetch_next_image()

    def prev_image(self):
        prev_idx = self.images.index(self.cur_image_file) - 1
        if prev_idx >= 0:
            self.cur_image_file = self.images[prev_idx]
            self.draw_image(self.load_image(self.cur_image_file))
            # set the next_image_file with pre fetch
            self.pre_fetch_next_image()

    def add_image(self):
        image_path = self.get_dst_image()

        # If file is already copied, there's no point to do it again
        if not os.path.isfile(image_path):
            # Check that destination directory exists
            image_dir = os.path.dirname(image_path)
            if not os.path.exists(image_dir):
                os.makedirs(image_dir)

            # And copy
            shutil.copyfile(self.cur_image_file, image_path)
        self.next_image()

    def del_image(self):
        image_path = self.get_dst_image()

        # Only remove if dst file exists - Doh!
        if os.path.exists(image_path):
            os.remove(image_path)
        self.next_image()

    def load_image(self, image_path):
        allocation = self.window.get_allocation()
        pixbuf = gtk.gdk.pixbuf_new_from_file(image_path)

        max_width = float(allocation.width)
        max_height = float(allocation.height)
        image_width = float(pixbuf.get_width())
        image_height = float(pixbuf.get_height())

        if max_width < max_height:
            height = int((image_height / image_width) * max_width)
            width = int(max_width)
        else:
            height = int(max_height)
            width = int((image_width / image_height) * max_height)
        return pixbuf.scale_simple(width, height, gtk.gdk.INTERP_BILINEAR)

    def draw_image(self, pixbuf):
        self.image.set_from_pixbuf(pixbuf)

    def get_dst_image(self):
        # Remove root path
        image_path = self.cur_image_file[len(self.src_path):]
        # Remove possible leading '/'
        if image_path[0] == '/':
            image_path = image_path[1:]
        # Construct dest path
        image_path = os.path.join(self.dst_path, image_path)
        return image_path

    def quit(self):
        self.destroy(self.window)

    def __init__(self):
        if len(sys.argv) < 3:
            print "usage: imageselector <src path> <dst path>"
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
        self.image_iterator = iterdirwalk(self.src_path)

        # Fetch first image
        try:
            self.next_image_file = self.image_iterator.next()
        except StopIteration:
            print "No files in source path"
            sys.exit(2)

        self.images = [self.next_image_file]
        self.pixbuf = self.load_image(self.next_image_file)
        self.next_image()

        self._key_actions = {
            'h': self.prev_image,
            'l': self.next_image,
            ' ': self.add_image,
            'd': self.del_image,
            'q': self.quit,
        }

    def main(self):
        gtk.main()

if __name__ == "__main__":
    imageselector = ImageSelector()
    imageselector.main()
