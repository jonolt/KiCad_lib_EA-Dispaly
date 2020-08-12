#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Aug 12 11:12:50 2020

@author: johannes
"""

from numpy import arange  # needed in eval
import numpy as np
import pandas as pd
import KicadModTree as kmt

#from KicadModTree import Footprint



def start_stop_from_size(length_x, height_y, center_offset_x=0, center_offset_y=0, ret_list=False, roundez=2):
    start = np.array([-center_offset_x, -center_offset_y], dtype=float)
    stop = start + np.array([length_x, height_y], dtype=float)
    try:
        start = start+global_offset
        stop = stop+ global_offset
    except NameError:
        pass
    if roundez:
        start = start.round(roundez)
        stop = stop.round(roundez)
    if ret_list:
        return list(start), list(stop)
    return start, stop

def start_stop_from_size_c(length_x, height_y, center_offset_x=None, center_offset_y=None, ret_list=False, roundez=2):
    if not center_offset_x:
        center_offset_x = length_x/2
    if not center_offset_y:
        center_offset_y = height_y/2
    return start_stop_from_size(length_x, height_y, center_offset_x=center_offset_x, center_offset_y=center_offset_y, ret_list=ret_list, roundez=roundez)

df = pd.read_excel("footprint_dimensions.ods", engine="odf", index_col=0)

for mode in ["lcd_only", "with_led"]:
    for ds in df.iteritems():
        footprint_name = ds[0]
        if mode == "with_led":
            if "OLED" in footprint_name:
                continue
            footprint_name += "_with_LED"
        print(footprint_name)
        param = ds[1]
    
        #center is center of lcd display
        global_offset = np.array([param.pin_count/4*param.rm-param.rm/2, -param.pin_y_distance+param.center_from_top])
        
        # init kicad footprint
        kicad_mod = kmt.Footprint(footprint_name)
        kicad_mod.setDescription("A example footprint")
        kicad_mod.setTags(footprint_name)
        
        # set general values
        kicad_mod.append(kmt.Text(type='reference', text='REF**', at=[0, -3], layer='F.SilkS'))
        kicad_mod.append(kmt.Text(type='value', text=footprint_name, at=[1.5, 3], layer='F.Fab'))
        
        # create silkscreen
        if mode == "lcd_only":
            p_start, p_stop = start_stop_from_size_c(param.width, param.height, center_offset_y=param.center_from_top-param.pin_size_y/2)
        else:
            p_start, p_stop = start_stop_from_size_c(param.bl_width, param.bl_height, center_offset_y=param.center_from_top+(param.bl_height-param.pin_y_distance)/2)
        kicad_mod.append(kmt.RectLine(start=list(p_start), end=list(p_stop), layer='F.SilkS'))
        
        # create courtyard (a bit biger than usual since i dont trust the drawings)
        ctrYs_clearance = np.array([.4, .4])
        kicad_mod.append(kmt.RectLine(start=list(p_start-ctrYs_clearance), end=list(p_stop+ctrYs_clearance), layer='F.CrtYd'))
        
        # create active area
        p_start, p_stop = start_stop_from_size_c(param.active_width, param.active_height, ret_list=True)
        kicad_mod.append(kmt.RectLine(start=p_start, end=p_stop, width=.1, layer='Dwgs.User'))
        
        # create pads
        pins_top = list(eval(param.pins_top))
        pins_bottom = list(eval(param.pins_bottom))
        pins_top.extend(pins_bottom)
        pads = pins_top
        
        drill_dia = np.sqrt(pow(param.pin_size_x, 2)+pow(param.pin_size_y, 2))+.2
        pad_diu = drill_dia + 2*.15
        
        for pad in pads:
            pad = int(pad)
            if pad <= param.pin_count/2:
                pos_x = (pad-1)*param.rm
                pos_y = 0.0
            else:
                pos_x = param.pin_count*param.rm-pad*param.rm
                pos_y = -param.pin_y_distance
            if pad==1:
                kicad_mod.append(kmt.Pad(number=1, type=kmt.Pad.TYPE_THT, shape=kmt.Pad.SHAPE_RECT,
                                     at=[0, 0], size=[2, 2], drill=1.2, layers=kmt.Pad.LAYERS_THT))
            else:
                kicad_mod.append(kmt.Pad(number=pad, type=kmt.Pad.TYPE_THT, shape=kmt.Pad.SHAPE_CIRCLE,
                                     at=[pos_x, pos_y], size=[2, 2], drill=1.2, layers=kmt.Pad.LAYERS_THT))
        
        # add model
        kicad_mod.append(kmt.Model(filename="example.3dshapes/example_footprint.wrl",
                               at=[0, 0, 0], scale=[1, 1, 1], rotate=[0, 0, 0]))
        
        # output kicad model
        file_handler = kmt.KicadFileHandler(kicad_mod)
        file_handler.writeFile(f'EA_Display.pretty/{footprint_name}.kicad_mod')
