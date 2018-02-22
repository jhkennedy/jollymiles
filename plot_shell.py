#!/usr/bin/env python3

import os
import errno
import shutil
import logging
import subprocess
import datetime as dt

import gspread as gs
from oauth2client.service_account import ServiceAccountCredentials as SaC

import numpy as np
import pandas as pd

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
    data = sheet.range(f'A7:D{sheet.row_count}')

    col_idx = np.arange(0, len(data), 4)

    dates = [dt.datetime.strptime(data[idx].value, "%m/%d/%Y") for idx in col_idx if data[idx].value != '']
    joe_m = [float(data[idx + 1].value) for idx in col_idx if data[idx].value != '']
    holly_m = [float(data[idx + 2].value) for idx in col_idx if data[idx].value != '']
    method = [data[idx + 3].value for idx in col_idx if data[idx].value != '']

    frame = pd.DataFrame({'days': dates, 'joe_miles': joe_m, 'holly_miles': holly_m, 'method': method})
    frame = frame.set_index(frame['days'])

    return frame


def plot_shell(date=dt.date(2017, 12, 31), pace_d=0.0, joe_d=0.0, holly_d=0.0, plot_file='output/jolly_miles_0.png'):
    """
    Plot a rowing shell by importing an svg and turning it into a matplotlib path.
    """

    with open('shell.svg', 'r') as svg_file:
        svg_tree = etree.parse(svg_file)

    svg_root = svg_tree.getroot()
    svg_width = int(svg_root.attrib['width'][:-2])
    svg_height = int(svg_root.attrib['height'][:-2])
    svg_aspect_ratio = svg_height / svg_width

    pace_boat = []
    for svg_elem in svg_tree.iter():
        if svg_elem.tag.split('}')[1] == 'path':
            pace_boat.append(parse_path(svg_elem.get('d')))

    holly_boat = pace_boat.copy()
    joe_boat = pace_boat.copy()

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
    plt.close()


if __name__ == '__main__':
    mkdir_p('output/')

    records = sheet_data()
    year = pd.DataFrame()
    year['joe_miles'] = records.joe_miles.resample('D').sum().fillna(0)
    year['holly_miles'] = records.holly_miles.resample('D').sum().fillna(0)

    year_ix = pd.DatetimeIndex(start=dt.datetime(2017,12,31), end=dt.datetime(2018,12,31), freq='D')
    year = year.reindex(year_ix).fillna(0)

    year['joe_d'] = year.joe_miles.cumsum()
    year['holly_d'] = year.holly_miles.cumsum()
    year['pace_d'] = [day.timetuple().tm_yday * 1009.0/365.0 for day in year.index]
    year['pace_d'][0] = 0  # Fix last year start value

    d0 = year.index[0]
    plot_shell(date=d0.date(), pace_d=year.pace_d[d0], joe_d=year.joe_d[d0], holly_d=year.holly_d[d0],
               plot_file=f'output/jolly_miles_{0:03d}.png')

    for day in year.index[1:]:
        plot_shell(date=day.date(), pace_d=year.pace_d[day], joe_d=year.joe_d[day], holly_d=year.holly_d[day],
                   plot_file=f'output/jolly_miles_{day.timetuple().tm_yday:03d}.png')

    if shutil.which('convert') is not None:
        subprocess.check_call(['convert', '-delay', '5', '-loop', '0', '-layers', 'Optimize', '*.png', 'jolly_miles.gif'], cwd='output/')
    else:
        logging.warning("ImageMagick's convert utility required for gif creation!")
