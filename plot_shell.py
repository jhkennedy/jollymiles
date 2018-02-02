#!/usr/bin/env python3
"""
Plot a rowing shell by importing an svg and turning it into a matplotlib path.
"""

import numpy as np

from lxml import etree
from svgpath2mpl import parse_path

from matplotlib import patches
from matplotlib import transforms
from matplotlib import pyplot as plt


with open('shell.svg', 'r') as svg_file:
    svg_tree = etree.parse(svg_file)

svg_root = svg_tree.getroot()
svg_width = int(svg_root.attrib['width'][:-2])
svg_height = int(svg_root.attrib['height'][:-2])
svg_aspect_ratio = svg_height / svg_width

svg_paths = []
for svg_elem in svg_tree.iter():
    if svg_elem.tag.split('}')[1] == 'path':
        svg_paths.append(parse_path(svg_elem.get('d')))

pace_boat = svg_paths.copy()
holly_boat = svg_paths.copy()
joe_boat = svg_paths.copy()

boat_width = 250
scale_factor = boat_width / svg_width
boat_height = svg_height * scale_factor

# Get course in miles
plot_width = 1009 + boat_width * 2
plot_height = svg_aspect_ratio * plot_width

lane_height = plot_height / 3
lane_padding = (lane_height - boat_height) / 2

joe_y = lane_padding
holly_y = lane_height + lane_padding
pace_y = lane_height * 2 + lane_padding


fig, ax = plt.subplots(1, 1, figsize=(15, 5))
tf = ax.transData  # Note: the plot transform should be the last transform!

ax.plot([0, 0], [0, plot_height], 'g-', lw=5, zorder=1)
ax.plot([1009, 1009], [0, plot_height], 'k-', lw=5, zorder=1)

lane_buoys_x = np.linspace(-boat_width,plot_width-boat_width, 37)
lane_buoys_y = np.ones(lane_buoys_x.shape)

ax.scatter(lane_buoys_x, lane_buoys_y*0, 25, marker='o', color='orange', zorder=2)
ax.scatter(lane_buoys_x, lane_buoys_y*lane_height, 25, marker='o', color='orange', zorder=2)
ax.scatter(lane_buoys_x, lane_buoys_y*lane_height*2, 25, marker='o', color='orange', zorder=2)
ax.scatter(lane_buoys_x, lane_buoys_y*lane_height*3, 25, marker='o', color='orange', zorder=2)

for part in joe_boat:
    part_patch = patches.PathPatch(part, lw=2, color='green')
    ti = transforms.Affine2D().scale(scale_factor)
    ti += transforms.Affine2D().translate(-boat_width, joe_y)
    part_patch.set_transform(ti+tf)
    ax.add_patch(part_patch)

for part in holly_boat:
    part_patch = patches.PathPatch(part, lw=2, color='blue')
    ti = transforms.Affine2D().scale(scale_factor)
    ti += transforms.Affine2D().translate(-boat_width, holly_y)
    part_patch.set_transform(ti+tf)
    ax.add_patch(part_patch)

for part in pace_boat:
    part_patch = patches.PathPatch(part, lw=2, color='black')
    ti = transforms.Affine2D().scale(scale_factor)
    ti += transforms.Affine2D().translate(-boat_width, pace_y)
    part_patch.set_transform(ti+tf)
    ax.add_patch(part_patch)

ax.set_xlim(-boat_width, plot_width-boat_width)
ax.set_ylim(0, plot_height)
plt.show()
