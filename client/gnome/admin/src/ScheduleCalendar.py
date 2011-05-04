#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (C) 2009,2010 Junta de Andalucia
# 
# Authors:
#   Roberto Majadas <roberto.majadas at openshine.com>
#   Cesar Garcia Tapia <cesar.garcia.tapia at openshine.com>
#   Luis de Bethencourt <luibg at openshine.com>
#   Pablo Vieytes <pvieytes at openshine.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301
# USA

import os
import gtk
if os.name == "posix" :
    import gconf

import cairo
import pango
import pangocairo

import math
import copy

import datetime

class ScheduleCalendar (gtk.EventBox):

    def __init__ (self):
        gtk.EventBox.__init__(self)
        
        if os.name == "posix":
            self.gconf_client = gconf.client_get_default()

        self.WEEKDAYS = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]

        self.drawing_area = gtk.DrawingArea ()

        self.add (self.drawing_area)

        # The schedule data is divided in blocks of half an hour
        self.schedule_data = [[False for i in range(48)] for i in range(7)]

        self.drawing_area.connect("expose_event", self.__on_expose_event)
        self.connect("button_press_event", self.__on_button_press_event)
        self.connect("button_release_event", self.__on_button_release_event)

        tarjet = [ ( "", 0, gtk.TARGET_SAME_WIDGET) ]

        self.drag_source_set (gtk.gdk.BUTTON1_MASK, tarjet, gtk.gdk.ACTION_DEFAULT)
        self.drag_source_set_icon_stock(gtk.STOCK_EDIT)
        self.drag_dest_set(0, [], 0)
        self.connect("drag_motion", self.__on_drag_motion_event)

    def set_block_data (self, block_data):
        """
        block_data follows this format:

        block_data = { "mon": [("12:30", "15:30"), ("18:30", "23:00")],
                       "sun": [("10:00", "18:30")]
                     }
        """
        self.schedule_data = [[False for i in range(48)] for i in range(7)]
        for day in block_data:
            if day in self.WEEKDAYS:
                day_index = self.WEEKDAYS.index(day)

                for range_value in block_data[day]:
                    from_hour = int (range_value[0].partition(':')[0])
                    from_minute = int (range_value[0].partition(':')[2])
                    to_hour = int (range_value[1].partition(':')[0])
                    to_minute = int (range_value[1].partition(':')[2])

                    init_block = int (from_hour*2)
                    if from_minute >= 30 and from_minute <=59:
                        init_block = init_block + 1 

                    end_block = int (to_hour*2)
                    if to_minute > 0 and to_minute <= 30:
                        end_block = end_block + 1
                    if to_minute > 30 and to_minute <= 59:
                        end_block = end_block + 2

                    if init_block < end_block:
                        for block in range (init_block, end_block):
                            self.schedule_data[day_index][block] = True
        self.__reload ()

    def get_block_data (self):
        half_hour = datetime.timedelta (minutes=30)
        in_interval = False
        interval_begin_time = None
        interval_end_time = None
        interval_length = None

        block_data = {}
        
        for day in range(7):
            for hour in range (48):
                if hour == 47 and self.schedule_data [day][hour]:
                    if not self.WEEKDAYS[day] in block_data:
                        block_data[self.WEEKDAYS[day]] = []

                    if not in_interval:
                        block_data[self.WEEKDAYS[day]].append (('23:30', '23:59'))
                    else:
                        begin_time_string = str(interval_begin_time)[:-3]

                        block_data[self.WEEKDAYS[day]].append ((begin_time_string, '23:59'))

                        in_interval = False

                elif self.schedule_data [day][hour]:
                    if not in_interval:
                        interval_begin_time = datetime.timedelta (hours=round (hour/2), minutes=hour%2*30)
                        interval_length = datetime.timedelta ()
                        in_interval = True
                    else:
                        interval_length += half_hour
                else:
                    if in_interval:
                        interval_length += half_hour
                        interval_end_time = interval_begin_time + interval_length

                        if not self.WEEKDAYS[day] in block_data:
                            block_data[self.WEEKDAYS[day]] = []

                        begin_time_string = str(interval_begin_time)[:-3]

                        if interval_end_time >= datetime.timedelta (hours=24):
                            end_time_string = '23:59'
                        else:
                            end_time_string = str(interval_end_time)[:-3]

                        block_data[self.WEEKDAYS[day]].append ((begin_time_string, end_time_string))

                        in_interval = False

        return block_data

    def __on_drag_motion_event (self, widget, drag_context, x, y, data=None):
        day, hour = self.__get_time_from_pos (x, y)
        if day is None:
            return

        if self.__origin_hour > hour:
            min_hour = hour
            max_hour = self.__origin_hour
        else:
            min_hour = self.__origin_hour
            max_hour = hour

        if self.__origin_day > day:
            min_day = day
            max_day = self.__origin_day
        else:
            min_day = self.__origin_day
            max_day = day

        self.schedule_data = copy.deepcopy (self.__origin_schedule_data)
        for h in range (min_hour, max_hour+1):
            for d in range (min_day, max_day+1):
                try:
                    self.schedule_data[d][h] = self.__origin_value 
                except:
                    break
        self.__reload ()

    def __on_button_press_event (self, widget, event, data=None):
        if event.button == 1:
            day, hour = self.__get_time_from_pos (event.x, event.y)
            if day is None:
                return

            self.__origin_day = day
            self.__origin_hour = hour
            self.__origin_schedule_data = copy.deepcopy (self.schedule_data)
            self.__origin_value = not self.schedule_data[self.__origin_day][self.__origin_hour]
            self.schedule_data[self.__origin_day][self.__origin_hour] = self.__origin_value
            self.__reload ()

    def __on_button_release_event (self, widget, event, data=None):
        self.__origin_day = None
        self.__origin_hour = None
        self.__origin_value = None
        self.__origin_schedule_data = None

    def __get_time_from_pos (self, x, y):
            x = x - self.LEFT_MARGIN
            y = y - self.TOP_MARGIN

            if x < 0 or y < 0:
                return None, None

            hour = int (math.floor (2.0*float(x) /(self.ITEM_WIDTH+self.MARGIN)))
            day = int (math.floor (y /(self.ITEM_HEIGHT+self.MARGIN)))

            return day, hour

    def __on_expose_event (self, widget, event):
        self.__reload (True)

    def __reload (self, fill=False):
        try:
            context = self.drawing_area.window.cairo_create()
        except AttributeError:
            return
        rect = self.get_allocation()

        ITEMS = 24
        DAYS = 7

        if fill:
            if os.name == "posix" :
                font = self.gconf_client.get_string ('/desktop/gnome/interface/font_name')
                self.font_size = int (font.split(' ')[-1])
                self.font_name = ' '.join (font.split(' ')[:-1])
            else:
                self.font_size = 10
                self.font_name = "Sans"

            self.TOP_MARGIN = self.font_size + 10 
            self.LEFT_MARGIN = 80

            self.MARGIN = 3 
            self.ITEM_WIDTH = (rect.width - self.LEFT_MARGIN - self.MARGIN * ITEMS) / ITEMS
            self.ITEM_HEIGHT = (rect.height - self.TOP_MARGIN - self.MARGIN * DAYS) / DAYS 

            self.__write_key (context)

        x = self.LEFT_MARGIN + self.MARGIN 
        y = self.TOP_MARGIN + self.MARGIN

        for i in range(0, ITEMS):
            for j in range(0, DAYS):
                if self.state == gtk.STATE_INSENSITIVE:
                    self.__roundedrec_stroke (context, x, y, self.ITEM_WIDTH, self.ITEM_HEIGHT, 5, fill=True)
                else:
                    first_half = self.schedule_data[j][i*2]
                    second_half = self.schedule_data[j][i*2+1]

                    self.__roundedrec_left_half (context, x, y, self.ITEM_WIDTH, self.ITEM_HEIGHT, 5)
                    radial = cairo.LinearGradient(x, y, x,  y + self.ITEM_HEIGHT)
                    if first_half:
                        radial.add_color_stop_rgb(0.0, 1.0,  0.45, 0.45)
                        radial.add_color_stop_rgb(1.0, 0.75,  0.0, 0.0)
                    else:
                        radial.add_color_stop_rgb(0.0, 0.36,  1.0, 0.36)
                        radial.add_color_stop_rgb(1.0, 0.0,  0.76, 0.0)
                    context.set_source (radial)
                    context.fill()
                    
                    if first_half is not second_half:
                        context.move_to(x+self.ITEM_WIDTH/2,y)
                        context.line_to(x+self.ITEM_WIDTH/2,y+self.ITEM_HEIGHT)
                        context.set_source_rgb(0.3, 0.3, 0.3)
                        context.set_line_width(1)
                        context.stroke()

                    self.__roundedrec_right_half (context, x, y, self.ITEM_WIDTH, self.ITEM_HEIGHT, 5)
                    radial = cairo.LinearGradient(x, y, x,  y + self.ITEM_HEIGHT)
                    if second_half:
                        radial.add_color_stop_rgb(0.0, 1.0,  0.45, 0.45)
                        radial.add_color_stop_rgb(1.0, 0.75,  0.0, 0.0)
                    else:
                        radial.add_color_stop_rgb(0.0, 0.36,  1.0, 0.36)
                        radial.add_color_stop_rgb(1.0, 0.0,  0.76, 0.0)
                    context.set_source (radial)
                    context.fill()

                    if fill:
                        self.__roundedrec_stroke (context, x, y, self.ITEM_WIDTH, self.ITEM_HEIGHT, 5)

                y = y + self.ITEM_HEIGHT + self.MARGIN

            y = self.TOP_MARGIN + self.MARGIN
            x = x + self.ITEM_WIDTH + self.MARGIN

    def __write_key (self, context):
        context.set_source_rgb(0.0, 0.0, 0.0)
        # According Cairo's FAQ: using pango instead of Cairo's toy font api
        pango_cairo = pangocairo.CairoContext(context)
        font_dsc = pango.FontDescription("sans %s" % self.font_size)
        layout = pango_cairo.create_layout()
        layout.set_font_description(font_dsc)

        for i in range (0, 25):
            text = "%02d" % (i%24)
            x_bearing, y_bearing, width, height = context.text_extents(text)[:4]
            x_pos = self.MARGIN + (self.ITEM_WIDTH - width) / 2
            context.move_to (self.LEFT_MARGIN + (self.ITEM_WIDTH + self.MARGIN) * i - x_pos, height+5)
            layout.set_text(text)
            pango_cairo.show_layout_line(layout.get_line(0))

        i = 0
        for text in [_('Monday'), _('Tuesday'), _('Wednesday'), _('Thursday'), _('Friday'), _('Saturday'), _('Sunday')]:
            x_bearing, y_bearing, width, height = context.text_extents(text)[:4]
            y_pos = self.MARGIN + (self.ITEM_HEIGHT - height) / 2
            context.move_to (5, self.TOP_MARGIN + (self.ITEM_HEIGHT + self.MARGIN ) * i + height + y_pos)
            layout.set_text(text)
            pango_cairo.show_layout_line(layout.get_line(0))
            i += 1

    def __roundedrec_left_half (self,context,x,y,w,h,r = 10):
        "Draw a rounded rectangle"
        #   A****B
        #  F     * 
        #  *     * 
        #  E     *
        #   D****C

        w = w/2

        context.move_to(x+r,y)                      # Move to A
        context.line_to(x+w,y)                      # Line to B
        context.line_to(x+w,y+h)                    # Line to C 
        context.line_to(x+r,y+h)                    # Line to D 
        context.curve_to(x,y+h,x,y+h,x,y+h-r)       # Curve to E 
        context.line_to(x,y+r)                      # Line to F
        context.curve_to(x,y,x,y,x+r,y)             # Curve to A

    def __roundedrec_right_half (self,context,x,y,w,h,r = 10):
        "Draw a rounded rectangle"
        #  A***B
        #  *    C
        #  *    *
        #  *    D
        #  F***E

        w = w/2
        x = x+w

        context.move_to(x,y)                      # Move to A
        context.line_to(x+w-r,y)                    # Line to B
        context.curve_to(x+w,y,x+w,y,x+w,y+r)       # Curve to C, Control points are both at Q
        context.line_to(x+w,y+h-r)                  # Move to D
        context.curve_to(x+w,y+h,x+w,y+h,x+w-r,y+h) # Curve to E
        context.line_to(x,y+h)                    # Line to F 
        context.line_to(x,y)                        # Line to A

    def __roundedrec_stroke (self,context,x,y,w,h,r = 10, fill=False):
        "Draw a rounded rectangle"
        #   A****BQ
        #  H      C
        #  *      *
        #  G      D
        #   F****E

        context.move_to(x+r,y)                      # Move to A
        context.line_to(x+w-r,y)                    # Straight line to B
        context.curve_to(x+w,y,x+w,y,x+w,y+r)       # Curve to C, Control points are both at Q
        context.line_to(x+w,y+h-r)                  # Move to D
        context.curve_to(x+w,y+h,x+w,y+h,x+w-r,y+h) # Curve to E
        context.line_to(x+r,y+h)                    # Line to F
        context.curve_to(x,y+h,x,y+h,x,y+h-r)       # Curve to G
        context.line_to(x,y+r)                      # Line to H
        context.curve_to(x,y,x,y,x+r,y)             # Curve to A

        context.set_source_rgb(0.3, 0.3, 0.3)
        if fill:
            context.fill()
        context.set_line_width(1)
        context.stroke()
