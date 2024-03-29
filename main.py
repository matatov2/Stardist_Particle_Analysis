# -*- coding: utf-8 -*-
"""Stardist.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1PTLebAqgEy-vZT0QMUECaTEsvSCeIp1d
"""
# Commented out IPython magic to ensure Python compatibility.
# %env PYTHONPATH=
# Commented out IPython magic to ensure Python compatibility.
# %matplotlib inline

import matplotlib as mpl
import numpy as np
import pandas as pd
import pims
import matplotlib.pyplot as plt
from stardist import render_label

mpl.rc('figure', figsize=(10, 6))
mpl.rc('image', cmap='gray')

image = input('Write the tif file name (including the .tif):')
## image should be tif stack

##opening image as a pims pipeline and converting to greyscale
video = pims.as_gray(pims.open(image))
vid_size = 0
for num, img in enumerate(video):
    vid_size += 1


##pims pipeline for inverting the image to make dark-field for stardist
@pims.pipeline
def invert(frame):
    new = 255 - frame  ## https://www.geeksforgeeks.org/python-color-inversion-using-pillow/
    return new


from stardist.models import StarDist2D
from csbdeep.utils import normalize

model = StarDist2D.from_pretrained('2D_versatile_fluo')
"""
plt.figure(figsize=(8,8))
plt.imshow(inv[0], cmap='gray')
plt.axis("off")
plt.show()"""


@pims.pipeline
def stardist_segm(img):
    img_labels, img_details = model.predict_instances(normalize(img))
    return img_labels


bright = input('is the image bright field? (type y for yes and n for no):')

if bright == 'y':
    ##inverting the video for use in stardist segm
    toMeasure = invert(video)
    label_image = stardist_segm(invert(video))
else:
    toMeasure = video
    label_image = stardist_segm(video)

num = int(input(f'Choose a frame to show (0-{vid_size-1}):'))
over,axo = plt.subplots(1,2)
axo[0].imshow(video[num],cmap = "gray")
axo[0].axis("off")
axo[0].set_title("input")


toplot = render_label(label_image[num], img=video[num])
axo[1].imshow(toplot)
axo[1].axis("off")
axo[1].set_title("prediction + input overlayed")

plt.show()

comp, axc = plt.subplots(1,2)
axc[0].imshow(video[num],cmap = "gray")
axc[0].axis("off")
axc[0].set_title("input")

toplot = render_label(label_image[num])
axc[1].imshow(toplot)
axc[1].axis("off")
axc[1].set_title("prediction")
plt.show()

from skimage.measure import regionprops

features = pd.DataFrame()
for num, img in enumerate(toMeasure):
    for region in regionprops(label_image[num], intensity_image=img):
        features = pd.concat([features, pd.DataFrame(data={'frame': num, 'area': region.area}, index = [num])])

objnum = np.zeros(vid_size)
totalarea = np.zeros(vid_size)
frames = np.zeros(vid_size)

for num in range(len(objnum)):
    objnum[num] += features['frame'][num].size
    totalarea[num] += features['area'][num].sum()
    frames[num] += num

##https://matplotlib.org/stable/gallery/subplots_axes_and_figures/two_scales.html
fig, ax1 = plt.subplots()

color = 'tab:red'
ax1.set_xlabel('Frame')
ax1.set_ylabel('Total Area of Particles (px^2)', color=color)
ax1.plot(frames, totalarea, color=color)
ax1.tick_params(axis='y', labelcolor=color)

ax2 = ax1.twinx()  # instantiate a second axes that shares the same x-axis

color = 'tab:blue'
ax2.set_ylabel('Number of Particles', color=color)  # we already handled the x-label with ax1
ax2.plot(frames, objnum, color=color)
ax2.tick_params(axis='y', labelcolor=color)

fig.tight_layout()  # otherwise the right y-label is slightly clipped
plt.show()

frame = input(f'Choose a frame to make a histogram of (0-{vid_size-1}):')
plt.hist(features['area'][int(frame)], edgecolor = 'black')
plt.xlabel("Area (px^2)")
plt.show()