"""iCLOTS is a free software created for the analysis of common hematology and/or microfluidic workflow image data

Author: Meredith Fay, Lam Lab, Georgia Institute of Technology and Emory University
Last updated: 2022-11-01 for version 1.0b1

Series of functions that handles analysis for brightfield single cell tracking application

"""

import tkinter as tk
import tkinter.font as font
import os
import cv2
from PIL import Image, ImageTk, ImageDraw
import numpy as np
import pandas as pd
import math
import trackpy as tp
import warnings
warnings.filterwarnings("ignore", module="trackpy")
import matplotlib.pyplot as plt
import seaborn as sns
import datetime
import shutil

from iclotspython.core.tracking import (
    LegacyTrackingPolicy,
    measure_legacy_tracks,
)

class RunBFSCTAnalysis():

    def __init__(self, filelist, frames_crop, frames_bgr, umpix, fps, maxdiameter, minintensity, search_range, min_dist, x, y, w, h):
        super().__init__(filelist, frames_crop, frames_bgr, umpix, fps, maxdiameter, minintensity, search_range, min_dist, x, y, w, h)

    def analysis(self, filelist, frames_crop, frames_bgr, umpix, fps, maxdiameter, minintensity, search_range, min_dist, x, y, w, h):
        """Function runs final analysis based on the parameters chosen in GUI"""

        # Global variables for use with additional export functions within class
        global df_img, df_summary, df_video, video_basename, t_sdi

        # Base name for files
        video_basename = os.path.basename(filelist[0].split(".")[0])

        cvfont = cv2.FONT_HERSHEY_SIMPLEX  # For labeling

        df_all = pd.DataFrame()  # For all events, good for plotting
        df_summary = pd.DataFrame()  # For descriptive statistics
        df_img = pd.DataFrame(columns=['name', 'graph'])  # For images, graphs

        # Begin trackpy tracking analysis
        tp.quiet()
        f = tp.batch(frames_bgr[:len(frames_bgr)], self.maxdiameter.get(),
                     minmass=self.minintensity.get(), invert=False, processes=1);  # Detect particles/cells
        # Link particles, cells into dataframe format
        # Search range criteria: must travel no further than 1/3 the channel length in one frame
        # Memory here signifies a particle/cell cannot "disappear" for more than one frame
        tr = tp.link_df(f, search_range=self.search_range.get(), memory=1, adaptive_stop=1, adaptive_step=0.95)
        # Filter stubs criteria requires a particle/cell to be present for at least three frames
        t_final = tp.filter_stubs(tr, 3)

        t_sdi = pd.DataFrame()  # Create dataframe
        measurements = measure_legacy_tracks(
            t_final.to_dict("records"),
            tr.to_dict("records"),
            self.fps.get(),
            self.umpix.get(),
            LegacyTrackingPolicy.GENERAL,
            self.min_dist.get(),
        )
        for result in measurements:
            t_sdi = t_sdi.append(
                tr[tr['particle'] == result.source_particle], ignore_index=True
            )

        # Organize time, location, and RDI data in a list format
        df_video = pd.DataFrame(
            {'Particle': [result.source_particle for result in measurements],
             'Start frame': [result.start_frame for result in measurements],
             'End frame': [result.end_frame for result in measurements],
             'Transit time (s)': [result.elapsed_seconds for result in measurements],
             'Distance traveled (\u03bcm)': [result.distance_micrometres for result in measurements],
             'Velocity (\u03bcm/s)': [result.velocity_micrometres_per_second for result in measurements],
             'Area (pix)': [result.area_pixels for result in measurements]
             })

        # Renumber particles 0 to n
        df_video['Particle'] = np.arange(len(df_video))
        uniqvals = t_sdi['particle'].unique()
        newvals = np.arange(len(uniqvals))
        for val in newvals:
            uniqval = uniqvals[val]
            t_sdi['particle'] = t_sdi['particle'].replace(uniqval, val)

        # Graph for display
        graphs = plt.figure(figsize=(4, 4), dpi=80)
        graphs.suptitle(video_basename, fontweight='bold')

        # If cells exist within the image
        if len(f) != 0:
            # Subplot 212
            plt.subplot(2, 1, 1)
            plt.hist(df_video['Velocity (\u03bcm/s)'], rwidth=0.8, color='orangered')
            plt.xlabel('Velocity (\u03bcm/s)')
            plt.ylabel('n')

            # Subplot 211 (area hist)
            plt.subplot(2, 1, 2)
            plt.hist(df_video['Area (pix)'], rwidth=0.8, color='orangered')
            plt.xlabel('Area (pix)')
            plt.ylabel('n')

            plt.tight_layout()

            # Prepare for saving to be later referenced in graph window and in exports
            graphs.canvas.draw()
            graphimg = np.frombuffer(graphs.canvas.tostring_rgb(), dtype=np.uint8)
            graphimg = graphimg.reshape(graphs.canvas.get_width_height()[::-1] + (3,))

            plt.close()

            # Save images to special dataframe
            df_img = df_img.append({'name': video_basename,
                                    'graph': [graphimg]}, ignore_index=True)

            # Append individual image dataframe to larger dataframe
            f.insert(0, 'Image', video_basename)
            df_all = df_all.append(f, ignore_index=True)

            # Append summary data
            df_summary = descriptive_statistics(df_video)
            df_summary.insert(0, 'Video', video_basename)


        GraphTopLevel(df_img)  # Raise graph window

    def expnum(self, filelist, umpix, fps, maxdiameter, minintensity, search_range, min_dist, x, y, w, h):
        """Export numerical (excel) data, including descriptive statistics and parameters used"""

        writer = pd.ExcelWriter(video_basename + '_analysis.xlsx',
                                engine='openpyxl')

        # Write all data to special page
        df_video.to_excel(writer, sheet_name='Velocity data', index=False)

        # Write all data to special page
        t_sdi.to_excel(writer, sheet_name='Trackpy details', index=False)

        # Write summary data to special page
        df_summary.to_excel(writer, sheet_name='Summary', index=False)

        now = datetime.datetime.now()
        # Print parameters to a sheet
        param_df = pd.DataFrame({'Ratio, \u03bcm-to-pixels': umpix,
                                 'FPS': fps,
                                 'Maximum cell diameter (px)': maxdiameter,
                                 'Minimum cell intensity (a.u.)': minintensity,
                                 'Search range (px)': search_range,
                                 'Min. dist. traveled (px)': min_dist,
                                 'ROI x': x,
                                 'ROI y': y,
                                 'ROI w': w,
                                 'ROI h': h,
                                 'Analysis date': now.strftime("%D"),
                                 'Analysis time': now.strftime("%H:%M:%S")}, index=[1])
        param_df.to_excel(writer, sheet_name='Parameters used', index=False)

        writer.save()
        writer.close()

    def expgraph(self):
        """Export graphical (.png image) data, including pairplots"""

        array = cv2.cvtColor(df_img['graph'].iloc[0][0], cv2.COLOR_RGB2BGR)
        cv2.imwrite(df_img['name'].iloc[0] + '_graph.png', array)

        pp = plt.figure(figsize=(4, 4), dpi=300)
        df_subset = df_video[['Transit time (s)', 'Distance traveled (\u03bcm)',
                              'Velocity (\u03bcm/s)', 'Area (pix)']]
        sns.pairplot(df_subset)
        plt.savefig(video_basename + '_pairplot.png', dpi=300)
        plt.close()

    def expimgs(self, frames_crop):
        """Export image data (.png image) with processing and labeling applied"""

        current_dir = os.getcwd()  # Select filepath
        img_folder = os.path.join(current_dir, 'Results, labeled image data')

        if os.path.exists(img_folder):
            shutil.rmtree(img_folder)

        os.mkdir(img_folder)
        os.chdir(img_folder)

        # For frame in cropped frames
        for i in range(len(frames_crop)):
            image_name = video_basename + '_frame_' + str(i).zfill(5)

            f = t_sdi[t_sdi['frame'] == i]
            # Set up image to label, including cropping
            PILimg = Image.fromarray(np.dstack((frames_crop[i], frames_crop[i], frames_crop[i])))  # Color
            drawimg = ImageDraw.Draw(PILimg)  # " "
            for j in range(len(f)):
                drawimg.text((f['x'].iloc[j], f['y'].iloc[j]), str(f['particle'].iloc[j]),
                             fill="#ff0000")  # Label
            PILimg.save(image_name + "_labeled.png")  # Save image

        # Close large variables
        frames_crop = None
        frames_bgr = None
        df_video = None


class GraphTopLevel(tk.Toplevel):
    def __init__(self, df_img):
        super().__init__()

        self.df_img = df_img

        # Fonts
        boldfont = font.Font(weight='bold')

        # Widgets
        self.title("Analysis results")

        # Label
        title_label = tk.Label(self, text="Graphical results")
        title_label['font'] = boldfont
        title_label.grid(row=0, column=0, padx=10, pady=10)
        # Canvas
        self.img_canvas = tk.Canvas(self, width=320, height=320)
        self.img_canvas.grid(row=1, column=0, padx=5, pady=5)

        self.displaygraph(idx=0)

        quit_button = tk.Button(self, text="Quit", command=self.destroy)
        quit_button.grid(row=2, column=0, padx=5, pady=5)

        # Row and column configures
        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        self.rowconfigure(2, weight=1)
        self.rowconfigure(3, weight=1)
        self.rowconfigure(4, weight=1)
        self.columnconfigure(0, weight=1)

    def displaygraph(self, idx):
        """Display graphs in toplevel window immediately after analysis is run"""
        # Add image name to image name label
        graphimg = np.asarray(df_img['graph'].iloc[idx][0]).astype('uint8')
        graphimgr_tk = ImageTk.PhotoImage(image=Image.fromarray(graphimg))
        self.graphimgr_tk = graphimgr_tk  # Some fix?
        self.img_canvas.create_image(0, 0, anchor='nw', image=graphimgr_tk)

def descriptive_statistics(df_input):
    """Function to calculate descriptive statistics for each population, represented as a dataframe"""

    dict = {'n cells': len(df_input),
                  u'Min. distance (\u03bcm)': df_input['Distance traveled (\u03bcm)'].min(),
                  u'Mean distance (\u03bcm)': df_input['Distance traveled (\u03bcm)'].mean(),
                  u'Max. distance (\u03bcm)': df_input['Distance traveled (\u03bcm)'].max(),
                  u'Stdev, distance (\u03bcm)': df_input['Distance traveled (\u03bcm)'].std(),
                  u'Min. transit time (s)': df_input['Transit time (s)'].min(),
                  u'Mean transit time (s)': df_input['Transit time (s)'].mean(),
                  u'Max. transit time (s)': df_input['Transit time (s)'].max(),
                  u'Stdev, transit time (s)': df_input['Transit time (s)'].std(),
                  u'Min. velocity (\u03bcm/s)': df_input['Velocity (\u03bcm/s)'].min(),
                  u'Mean velocity (\u03bcm/s)': df_input['Velocity (\u03bcm/s)'].mean(),
                  u'Max. velocity (\u03bcm/s)': df_input['Velocity (\u03bcm/s)'].max(),
                  u'Stdev, velocity (\u03bcm/s)': df_input['Velocity (\u03bcm/s)'].std(),
                  u'Min. area (pix)': df_input['Area (pix)'].min(),
                  u'Mean area (pix)': df_input['Area (pix)'].mean(),
                  u'Max. area (pix)': df_input['Area (pix)'].max(),
                  u'Stdev, area (pix)': df_input['Area (pix)'].std()
                  }
    dict_df = pd.DataFrame(dict, index=[0])

    return dict_df
