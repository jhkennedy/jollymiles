#!/usr/bin/env python3

import os
import errno

import gspread as gs
from oauth2client.service_account import ServiceAccountCredentials as SaC

import datetime as dt
import numpy as np

from lxml import etree
from svgpath2mpl import parse_path

from matplotlib import patches
from matplotlib import transforms
from matplotlib import pyplot as plt


def mkdir_p(path):
    """
    Make parent directories as needed and no error if existing. Works like `mkdir -p`.
    """
    if path:
        try:
            os.makedirs(path)
        except OSError as exc:  # Python >2.5
            if exc.errno == errno.EEXIST and os.path.isdir(path):
                pass
            else:
                raise


def sheet_data():
    scope = ['https://spreadsheets.google.com/feeds']
    creds = SaC.from_json_keyfile_name('client_secret.json', scope)
    client = gs.authorize(creds)

    sheet = client.open("2018 Jolly miles for 2018").sheet1
    holly_d = 1009.0 - float(sheet.cell(4, 3).value)
    joe_d = 1009.0 - float(sheet.cell(4, 2).value)

    return holly_d, joe_d


def plot_shell(date=dt.date(2017, 12, 31), pace_d=0, joe_d=0, holly_d=0, plot_file='output/jolly_miles_0.png'):
    """
    Plot a rowing shell by importing an svg and turning it into a matplotlib path.
    """

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

    boat_width = 250.0
    scale_factor = boat_width / svg_width
    boat_height = svg_height * scale_factor

    # Get course in miles
    plot_width = 1009.0 + boat_width * 2.0
    plot_height = svg_aspect_ratio * plot_width

    lane_height = plot_height / 3.0
    lane_padding = (lane_height - boat_height) / 2.0

    joe_y = lane_padding
    holly_y = lane_height + lane_padding
    pace_y = lane_height * 2.0 + lane_padding

    fig, ax = plt.subplots(1, 1, figsize=(15, 5))
    tf = ax.transData  # Note: the plot transform should be the last transform!

    ax.plot([0, 0], [0, plot_height], '-', color='seagreen', lw=5, zorder=1)
    ax.plot([1009, 1009], [0, plot_height], '-', color='darkslategrey', lw=5, zorder=1)

    lane_buoys_x = np.linspace(-boat_width, plot_width-boat_width, 37)
    lane_buoys_y = np.ones(lane_buoys_x.shape)

    ax.scatter(lane_buoys_x, lane_buoys_y*0.0, 25, marker='o', color='orange', zorder=2)
    ax.scatter(lane_buoys_x, lane_buoys_y*lane_height, 25, marker='o', color='orange', zorder=2)
    ax.scatter(lane_buoys_x, lane_buoys_y*lane_height*2.0, 25, marker='o', color='orange', zorder=2)
    ax.scatter(lane_buoys_x, lane_buoys_y*lane_height*3.0, 25, marker='o', color='orange', zorder=2)

    for part in pace_boat:
        part_patch = patches.PathPatch(part, lw=2, color='darkslategrey', zorder=3)
        ti = transforms.Affine2D().scale(scale_factor)
        ti += transforms.Affine2D().translate(-boat_width+pace_d, pace_y)
        part_patch.set_transform(ti+tf)
        ax.add_patch(part_patch)

    for part in holly_boat:
        part_patch = patches.PathPatch(part, lw=2, color='darkcyan', zorder=3)
        ti = transforms.Affine2D().scale(scale_factor)
        ti += transforms.Affine2D().translate(-boat_width+holly_d, holly_y)
        part_patch.set_transform(ti+tf)
        ax.add_patch(part_patch)

    for part in joe_boat:
        part_patch = patches.PathPatch(part, lw=2, color='crimson', zorder=3)
        ti = transforms.Affine2D().scale(scale_factor)
        ti += transforms.Affine2D().translate(-boat_width+joe_d, joe_y)
        part_patch.set_transform(ti+tf)
        ax.add_patch(part_patch)

    ax.set_xlim(-boat_width, plot_width-boat_width)
    ax.set_ylim(-10, plot_height+10)

    plot_x_ticks = np.append(np.arange(0, 1000, 50), 1009)
    ax.set_xticks(plot_x_ticks)
    ax.tick_params(axis='y', which='both', left='off', labelleft='off')

    ax.set_title(f'{(holly_d+joe_d):.1f} Jolly miles for 2018 so far')
    ax.set_title(f'{date}', loc='right')

    fig.tight_layout()
    plt.savefig(plot_file)
    plt.show()


if __name__ == '__main__':
    today = dt.date.today()
    day_of_year = today.timetuple().tm_yday
    pf = f'output/jolly_miles_{day_of_year}.png'
    mkdir_p(os.path.dirname(pf))

    hd, jd = sheet_data()
    pd = day_of_year/365.0 * 1009.0

    plot_shell(date=today, pace_d=pd, holly_d=hd, joe_d=jd, plot_file=pf)
