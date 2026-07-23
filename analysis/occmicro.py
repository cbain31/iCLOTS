"""iCLOTS is a free software created for the analysis of common hematology and/or microfluidic workflow image data

Author: Meredith Fay, Lam Lab, Georgia Institute of Technology and Emory University
Last updated: 2022-07-18 for version 1.0b1

Series of functions that handles analysis for fluorescent occlusion/accumulation microchannel app

A later version of this application will incorporate channel detection for brightfield microscopy images

"""

import tkinter as tk
import tkinter.font as font
import os
import cv2
from PIL import Image, ImageTk
import numpy as np
import pandas as pd
from skimage import measure
from scipy.ndimage import label
import matplotlib.pyplot as plt
import datetime
import shutil

from iclotspython.core.accumulation import (
    legacy_microchannel_map,
    legacy_microchannel_series,
    threshold_channel,
)


def analysis_math(df_img, mapbin_ext, filelist, umpix, layer, threshold, x, y, w, h):
    """Calculates occlusion and accumulation for desired RGB channel"""

    data_raw = []
    data = []
    signal_masks = []
    # Column index titles
    rng = range(w)
    ypix_names = [str(a) for a in rng]
    col_names = ['Frame', 'Channel'] + ypix_names

    df_img = df_img.append({'name': 'map', 'color': 'map', 'img': mapbin_ext}, ignore_index=True)

    for i in range(len(filelist)):
        img = cv2.imread(filelist[i])
        imgbasename = os.path.basename(filelist[i].split(".")[0])
        crop = img[y:(y + h), x:(x + w), :]  # Create cropped image

        df_img = df_img.append({'name': imgbasename, 'color': 'full', 'img': crop}, ignore_index=True)

        img_channel = crop[:, :, layer]

        signal_mask = threshold_channel(img_channel, threshold)
        signal_masks.append(signal_mask)
        img_thresh = signal_mask * 255

        # Layer
        map_save = np.dstack((mapbin_ext, mapbin_ext, mapbin_ext))
        color = [0, 0, 0]
        color[layer] = 255
        map_save[np.where(img_thresh == 255)] = color

        df_img = df_img.append({'name': imgbasename, 'color': str(layer), 'img': map_save}, ignore_index=True)

    measurements = legacy_microchannel_series(
        signal_masks, mapbin_ext, umpix
    )
    for result in measurements:
        data_raw.append(
            [result.frame, result.channel]
            + result.column_occupancy_percent.tolist()
        )
        data.append(
            [
                result.frame,
                result.channel,
                result.mean_occlusion_percent,
                result.max_occlusion_percent,
                result.area_pixels,
                result.accumulation_pixels,
                result.area_micrometres_squared,
                result.accumulation_micrometres_squared,
            ]
        )

    # Save and return as dataframes
    df_data_raw = pd.DataFrame(data_raw, columns=col_names)
    df_data = pd.DataFrame(data, columns=['Frame', 'Channel', 'Mean occlusion (%)',
                                          'Max. occlusion (%)', 'Area (pix)', 'Accumulation (pix)',
                                          u'Area (\u03bcm\u00b2)', u'Accumulation (\u03bcm\u00b2)'])
    df_data_byframe = pd.DataFrame(df_data.groupby(['Frame']).mean(), columns=['Mean occlusion (%)',
                                                                               'Max. occlusion (%)',
                                                                               'Area (pix)',
                                                                               'Accumulation (pix)',
                                                                               u'Area (\u03bcm\u00b2)',
                                                                               u'Accumulation (\u03bcm\u00b2)'])
    framelist = np.linspace(0, len(df_data_byframe)-1, len(df_data_byframe))
    df_data_byframe.insert(0, column='Frame', value=framelist)

    return df_data_raw, df_data, df_data_byframe, df_img


class RunOccAccMicroAnalysis():

    def __init__(self, filelist, umpix, rchannel, rthresh, gchannel, gthresh, bchannel, bthresh, x, y, w, h):
        super().__init__(filelist, umpix, rchannel, rthresh, gchannel, gthresh, bchannel, bthresh, x, y, w, h)

    def analysis(self, filelist, umpix, rchannel, rthresh, gchannel, gthresh, bchannel, bthresh, x, y, w, h):
        """Function runs final analysis based on the parameters chosen in GUI"""

        # Global variables for use with additional export functions within class
        global df, df_summary_frame, df_summary_all, graphimg, df_colors

        cvfont = cv2.FONT_HERSHEY_SIMPLEX  # For labeling

        foldername = os.path.dirname(filelist[0])
        name = os.path.basename(foldername)

        # Read image
        img = cv2.imread(filelist[-1])

        crop = img[y:(y + h), x:(x + w), :]  # Create cropped image

        # Generate final-frame, all-layer horizontal geometry in the core.
        thresholds = {"red": rthresh, "green": gthresh, "blue": bthresh}
        mapbin_ext = legacy_microchannel_map(crop, thresholds) * 255

        graphs = plt.figure()
        graphs.suptitle(name, fontweight='bold')

        # Set up dataframes
        df = pd.DataFrame()  # For raw data
        df_summary_all = pd.DataFrame()  # For summary data
        df_summary_frame = pd.DataFrame()  # For summary data, summarized into frames

        df_colors = pd.DataFrame()
        df_img = pd.DataFrame()

        # For each present color, run analysis_math for by-color spatial dataframe and mean, max dataframes
        # Add to graph
        if rchannel is True:
            df_data_raw, df_data, df_data_byframe, df_img = analysis_math(df_img, mapbin_ext, filelist, umpix, 2, rthresh, x, y, w, h)

            # Add column with color, append to overall dataframe
            df_data_raw.insert(0, 'Color', 'red')
            df_data.insert(0, 'Color', 'red')
            df_data_byframe.insert(0, 'Color', 'red')

            df = df.append(df_data_raw, ignore_index=True)
            df_summary_all = df_summary_all.append(df_data, ignore_index=True)
            df_summary_frame = df_summary_frame.append(df_data_byframe, ignore_index=True)
            df_colors = df_colors.append(df_img, ignore_index=True)

            # Add to graph
            # Plot each channel as light color
            for k in range(df_data['Channel'].max()):
                df_graph = df_data[df_data['Channel'] == k]
                # Occlusion
                plt.subplot(1, 2, 1)
                plt.plot(df_graph['Frame'], df_graph['Mean occlusion (%)'], color='salmon')
                # Accumulation
                plt.subplot(1, 2, 2)
                plt.plot(df_graph['Frame'], df_graph[u'Accumulation (\u03bcm\u00b2)'], color='salmon')
            # Plot mean as darker color
            # Occlusion
            plt.subplot(1, 2, 1)
            plt.plot(df_data_byframe['Frame'], df_data_byframe['Mean occlusion (%)'], color='red', linewidth='3',
                     marker='3')
            # Accumulation
            plt.subplot(1, 2, 2)
            plt.plot(df_data_byframe['Frame'], df_data_byframe[u'Accumulation (\u03bcm\u00b2)'], color='red',
                     linewidth='3', marker='3')
            # Titles, xlabels, ylabels
            # Occlusion
            plt.subplot(1, 2, 1)
            plt.title('Mean occlusion')
            plt.xlabel('Time point (n)')
            plt.ylabel('Percent channel occluded')
            # Accumulation
            plt.subplot(1, 2, 2)
            plt.title('Accumulation')
            plt.xlabel('Time point (n)')
            plt.ylabel(u'Accumulation (\u03bcm\u00b2)')

        if gchannel is True:
            df_data_raw, df_data, df_data_byframe, df_img = analysis_math(df_img, mapbin_ext, filelist, umpix, 1, gthresh, x, y, w, h)

            # Add column with color, append to overall dataframe
            df_data_raw.insert(0, 'Color', 'green')
            df_data.insert(0, 'Color', 'green')
            df_data_byframe.insert(0, 'Color', 'green')
            df = df.append(df_data_raw, ignore_index=True)
            df_summary_all = df_summary_all.append(df_data, ignore_index=True)
            df_summary_frame = df_summary_frame.append(df_data_byframe, ignore_index=True)
            df_colors = df_colors.append(df_img, ignore_index=True)

            # Add to graph
            # Plot each channel as light color
            for k in range(df_data['Channel'].max()):
                df_graph = df_data[df_data['Channel'] == k]
                # Occlusion
                plt.subplot(1, 2, 1)
                plt.plot(df_graph['Frame'], df_graph['Mean occlusion (%)'], color='palegreen')
                # Accumulation
                plt.subplot(1, 2, 2)
                plt.plot(df_graph['Frame'], df_graph[u'Accumulation (\u03bcm\u00b2)'], color='palegreen')
            # Plot mean as darker color
            # Occlusion
            plt.subplot(1, 2, 1)
            plt.plot(df_data_byframe['Frame'], df_data_byframe['Mean occlusion (%)'], color='green', linewidth='3')
            # Accumulation
            plt.subplot(1, 2, 2)
            plt.plot(df_data_byframe['Frame'], df_data_byframe[u'Accumulation (\u03bcm\u00b2)'], color='green', linewidth='3')
            # Titles, xlabels, ylabels
            # Occlusion
            plt.subplot(1, 2, 1)
            plt.title('Mean occlusion')
            plt.xlabel('Time point (n)')
            plt.ylabel('Percent channel occluded')
            # Accumulation
            plt.subplot(1, 2, 2)
            plt.title('Accumulation')
            plt.xlabel('Time point (n)')
            plt.ylabel(u'Accumulation (\u03bcm\u00b2)')
            plt.tight_layout()

        if bchannel is True:
            df_data_raw, df_data, df_data_byframe, df_img = analysis_math(df_img, mapbin_ext, filelist, umpix,
                                                                  0, bthresh, x, y, w, h)

            # Add column with color, append to overall dataframe
            df_data_raw.insert(0, 'Color', 'blue')
            df_data.insert(0, 'Color', 'blue')
            df_data_byframe.insert(0, 'Color', 'blue')
            df = df.append(df_data_raw, ignore_index=True)
            df_summary_all = df_summary_all.append(df_data, ignore_index=True)
            df_summary_frame = df_summary_frame.append(df_data_byframe, ignore_index=True)
            df_colors = df_colors.append(df_img, ignore_index=True)

            # Add to graph
            # Plot each channel as light color
            for k in range(df_data['Channel'].max()):
                df_graph = df_data[df_data['Channel'] == k]
                # Occlusion
                plt.subplot(1, 2, 1)
                plt.plot(df_graph['Frame'], df_graph['Mean occlusion (%)'], color='lightskyblue')
                # Accumulation
                plt.subplot(1, 2, 2)
                plt.plot(df_graph['Frame'], df_graph[u'Accumulation (\u03bcm\u00b2)'], color='lightskyblue')
            # Plot mean as darker color
            # Occlusion
            plt.subplot(1, 2, 1)
            plt.plot(df_data_byframe['Frame'], df_data_byframe['Mean occlusion (%)'], color='blue', linewidth='3')
            # Accumulation
            plt.subplot(1, 2, 2)
            plt.plot(df_data_byframe['Frame'], df_data_byframe[u'Accumulation (\u03bcm\u00b2)'], color='blue', linewidth='3')
            # Titles, xlabels, ylabels
            # Occlusion
            plt.subplot(1, 2, 1)
            plt.title('Mean occlusion')
            plt.xlabel('Time point (n)')
            plt.ylabel('Percent channel occluded')
            # Accumulation
            plt.subplot(1, 2, 2)
            plt.title('Accumulation')
            plt.xlabel('Time point (n)')
            plt.ylabel(u'Accumulation (\u03bcm\u00b2)')

            plt.tight_layout()

        # Set up graph for toplevel graph display window
        graphs.canvas.draw()
        graphimg = np.frombuffer(graphs.canvas.tostring_rgb(), dtype=np.uint8)
        graphimg = graphimg.reshape(graphs.canvas.get_width_height()[::-1] + (3,))

        # Clear image variables
        img = None
        crop = None
        img_th_red = None
        img_th_blue = None
        img_th_green = None
        mapbin_ext = None

        # Raise toplevel to show graphs
        GraphTopLevel(graphimg)

    def expnum(self, filelist, umpix, rchannel, rthresh, gchannel, gthresh, bchannel, bthresh, x, y, w, h):

        # Create naming convention for excel sheet
        if len(filelist) == 1:  # Single file
            nameconvention = os.path.basename(filelist[0]).split(".")[0]
        elif len(filelist) > 1:  # Directory of files
            nameconvention_d = os.path.dirname(filelist[0])
            nameconvention = os.path.basename(nameconvention_d)

        # Create writer to save results to
        writer = pd.ExcelWriter(nameconvention[0:14] + '_analysis.xlsx', engine='openpyxl')  # Crop to avoid excel error

        # Calculate summary metrics, write individual sheets to excel file writer
        # Individual image names
        unique_colors = []
        if rchannel is True:
            unique_colors.append('red')
        if gchannel is True:
            unique_colors.append('green')
        if bchannel is True:
            unique_colors.append('blue')
        # unique_colors = df.color.unique()

        for uc in unique_colors:
            # Find all rows corresponding to unique name, three dataframes
            df_a = df[df['Color'] == uc]
            df_a.to_excel(writer, sheet_name=uc + ' raw data', index=False)  # Crop name to prevent errors
            df_summary_all_a = df_summary_all[df_summary_all['Color'] == uc]
            df_summary_all_a.to_excel(writer, sheet_name=uc + ' channel data', index=False)
            df_summary_frame_a = df_summary_frame[df_summary_frame['Color'] == uc]
            df_summary_frame_a.to_excel(writer, sheet_name=uc + ' frame data', index=False)

        now = datetime.datetime.now()
        # Print parameters to a sheet
        param_df = pd.DataFrame({'Ratio, \u03bcm-to-pixels': umpix,
                      'Red channel': rchannel,
                      'Threshold, red channel': rthresh,
                      'Green channel': gchannel,
                      'Threshold, green channel': gthresh,
                      'Blue channel': bchannel,
                      'Threshold, blue channel': bthresh,
                      'X coordinate (top)': x,
                      'Y coordinate (top)': y,
                      'ROI width': w,
                      'ROI height': h,
                      'Analysis date': now.strftime("%D"),
                      'Analysis time': now.strftime("%H:%M:%S")}, index=[1])
        param_df.to_excel(writer, sheet_name='Parameters used', index=False)

        writer.save()
        writer.close()

    def expgraph(self):

        current_dir = os.getcwd()  # Select filepath

        if os.path.basename(current_dir) == 'Results, labeled image data':
            os.chdir(os.path.dirname(current_dir))

        # Convert image to BGR
        array = cv2.cvtColor(graphimg, cv2.COLOR_RGB2BGR)
        cv2.imwrite('Analysis_graph.png', array)

    def expimgs(self):

        current_dir = os.getcwd()  # Select filepath

        # if 'Results' in current_dir.split('/')[-1]:
        #     current_dir = os.path.dirname(current_dir)
        img_folder = os.path.join(current_dir, 'Results, labeled image data')

        if os.path.exists(img_folder):
            shutil.rmtree(img_folder)

        os.mkdir(img_folder)
        os.chdir(img_folder)

        for j in range(len(df_colors)):
            array = (df_colors['img'].iloc[j]).astype('uint8')
            cv2.imwrite(df_colors['name'].iloc[j] + '_' + df_colors['color'].iloc[j] + '_image.png', array)

        # Clear large dataframe variables
        df = None
        df_img = None
        df_summary_all = None
        df_frame = None


class GraphTopLevel(tk.Toplevel):
    def __init__(self, graphimg):
        super().__init__()

        self.graphimg = graphimg

        self.title("Analysis results")

        # Canvas widget
        self.img_canvas = tk.Canvas(self, width=480, height=320)
        self.img_canvas.grid(row=0, column=0, padx=5, pady=5)
        # Show graph
        graphimg = np.asarray(graphimg).astype('uint8')
        # Resize
        height, width, layers = graphimg.shape
        if width/480 > height/320:
            factor = 480 / width
        else:  # If height ratio greater or if equal (if equal factor same)
            factor = 320/height
        dim = (int(width * factor), int(height * factor))
        graphimgr = cv2.resize(graphimg, dim, interpolation=cv2.INTER_AREA)
        graphimgr_tk = ImageTk.PhotoImage(image=Image.fromarray(graphimgr))
        self.graphimgr_tk = graphimgr_tk  # Some fix?
        self.img_canvas.create_image(240, 160, anchor='c', image=graphimgr_tk)

        quit_button = tk.Button(self, text="Quit", command=self.destroy)
        quit_button.grid(row=1, column=0, padx=5, pady=5)

        # Row and column configures
        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        self.columnconfigure(0, weight=1)
