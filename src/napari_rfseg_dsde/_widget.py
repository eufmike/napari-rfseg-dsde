"""
This module is an example of a barebones QWidget plugin for napari

It implements the Widget specification.
see: https://napari.org/plugins/stable/guides.html#widgets

Replace code below according to your needs.
"""
import os, sys
import json
import glob
from tqdm import tqdm
import numpy as np
from skimage.io import imread, imsave
from pathlib import Path
from enum import Enum
from posixpath import dirname
from qtpy.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QFileDialog, QComboBox
from magicgui import magic_factory, magicgui
from napari.qt.threading import thread_worker
import napari
from napari.types import ImageData, LabelsData, LayerDataTuple

class ExampleQWidget(QWidget):
    # your QWidget.__init__ can optionally request the napari viewer instance
    # in one of two ways:
    # 1. use a parameter called `napari_viewer`, as done here
    # 2. use a type annotation of 'napari.viewer.Viewer' for any parameter
    def __init__(self, napari_viewer):
        super().__init__()
        self.viewer = napari_viewer
        btn = QPushButton("Click me!")
        btn.clicked.connect(self._on_click)
        btn_2 = QPushButton("print dir")
        btn_2.clicked.connect(self._print_dir)
        self.droplist = QComboBox()
        self.droplist.addItems(['mip_stt540', 'mip_sttoriginal'])
        self.droplist.currentIndexChanged.connect(self.selectionchange)
        
        self.hcadir = Path('L:')
        self.setLayout(QVBoxLayout())
        self.layout().addWidget(btn)
        self.layout().addWidget(btn_2)

    def _on_click(self):
        print("napari has", len(self.viewer.layers), "layers")
    
    def _print_dir(self): 
        self.dirdialog = QFileDialog.getExistingDirectory(self, "Select HCA Project Directory", directory = str(self.hcadir), options=QFileDialog.Option.ShowDirsOnly)
        print(Path(self.dirdialog))
        
    def selectionchange(self,i):
        ipfolder = self.droplist.currentText()
        print(f"Current index: {i}, selection changed: {ipfolder}")

# =======================================================================

def imgstackloader(imglist_dict, channels):
    img_stack_all = []
    for ch in channels:
        imglist = imglist_dict[ch]
        img_stack = []
        for imgpath in tqdm(imglist): 
            img_tmp = imread(imgpath, key=0)
            # img_tmp = tifffile.imread(imgpath, key=0)
            img_tmp = np.expand_dims(img_tmp, axis = (0, 1))
            img_stack.append(img_tmp)
        img_stack = np.concatenate(img_stack, axis = 0)
        print(img_stack.shape)
        img_stack_all.append(img_stack)
    img_stack_all = np.concatenate(img_stack_all, axis = 1)
    return img_stack_all

def imglistsampler(imglist_dict, init_batch, init_type):
    imglist_dict_show = {}
    for ch, imglist in imglist_dict.items():
        if init_type == 'Sequential':
            end = init_batch
            if end > len(imglist):
                print(f'The end index ({end}) is larger than the size of dataset ({len(imglist)}).')
                print(f'The whole dataset is included.')
                end = len(imglist)
            imglist_show = imglist[0:end]

        elif init_type == 'Random':
            random_amount = init_batch
            if random_amount > len(imglist):
                print(f'The end index ({random_amount}) is larger than the size of dataset ({len(imglist)}).')
                print(f'The whole dataset is included.')
                random_amount = len(imglist)
            random_order = np.random.choice(len(imglist), random_amount, replace=False)
            imglist_show = [imglist[idx] for idx in random_order]
        imglist_dict_show[ch] = imglist_show
    
    return imglist_dict_show

def pathloader(dirname, ipfldname, channels, imgcount):

    imglist_dict = {}
    for ch in channels:
        imgpathr = str(dirname.joinpath('Measurements', '*', '*', ipfldname, f'*-ch{str(ch)}*.tiff'))
        imglist_tmp = glob.glob(imgpathr)
        imglist_tmp.sort()
        imglist_dict[ch] = imglist_tmp

    print(imglist_dict)
    # Create subset
    init_batch = imgcount
    init_type = 'Sequential' # or 'Random'

    imglist_dict_show = imglistsampler(imglist_dict, init_batch, init_type)
    # print(imglist_dict_show)
    imgstack_show = imgstackloader(imglist_dict_show, channels)
    print(imgstack_show.shape)
    # firstimg = imread(imglist_show[0], key=0)

    return imgstack_show

'''
# mywidget
@magic_factory(
    dirname = {'mode': 'd'},
    call_button = 'Load',
    load_type = {"choices": ['Partial', 'All', 'Random']},
    
    )
def dataloader(
    dirname = Path('L:\\').joinpath('MicroTissue', 'MicroTissue2D', '20220418_microtissue2D96w'),
    ipfldname = 'mip_stt540',
    channel = 2,
    target = 'microtissue',
    start = 1,
    end = 20,
    load_type = 'Partial', 
    imgcount = 3,
    
):
    print(f"load_type {load_type}")
    print(f'dirname:{dirname}')
    print(f'ipfldname{ipfldname}')
    print(f'channel: {channel}')
    print(f'target: {target}')
    print(f'imgcount: {imgcount}')
    
    json_path = dirname.joinpath('Settings', 'imageconfig.json')
    print(json_path)
    print(json_path.is_file())    
    
    with open(json_path, 'r') as json_file:
        target_dict = json.load(json_file)
    
    channels = target_dict[target]
    if not isinstance(channels, list):
        channels = [channels]
    print(type(channels))
    
    imgstack_show = pathloader(dirname, ipfldname, channels, imgcount)
    
    print(imgstack_show.shape)
    print(napari.Viewer)
    viewer = napari.Viewer
    chnames = [f'image_ch{x}' for x in channels]
    ly_image = viewer.add_image(imgstack_show, gamma = 0.4, channel_axis = 1, name = chnames)
    # ly_image[0].contrast_limits = (0, np.percentile(imgstack_show[:, 0, :, :], 99.75))
    # ly_image[1].contrast_limits = (0, np.percentile(imgstack_show[:, 1, :, :], 99.75))

    viewer = napari.Viewer()
    chnames = [f'image_ch{x}' for x in channels]
    ly_image = viewer.add_image(imgstack_show, gamma = 0.4, channel_axis = 1, name = chnames)
    ly_image[0].contrast_limits = (0, np.percentile(imgstack_show[:, 0, :, :], 99.75))
    ly_image[1].contrast_limits = (0, np.percentile(imgstack_show[:, 1, :, :], 99.75))

    if end > len(imglist):
        print(f'The end index ({end}) is larger than the size of dataset ({len(imglist)}).')
        print(f'The whole dataset is included.')
        end = len(imglist)
    if random_images > len(imglist):
        print(f'The size of random images ({random_images}) is larger than the dataset ({len(imglist)}).')
        print(f'The whole dataset is included with randomized order.')
        random_images = len(imglist)

    def _dataloader():
        if load_type == 'Partial':
            self.imglist_show = imglist[start - 1 : end]
            self.labellist_show = labellist[start - 1 : end]
            self.predlist_show = predlist[start - 1 : end]
        elif load_type == 'All':
            self.imglist_show = imglist
            self.labellist_show = labellist
            self.predlist_show = predlist
        elif load_type == 'Random':
            random_order = np.random.choice(len(imglist), random_images, replace=False)
            self.imglist_show = [imglist[idx] for idx in random_order]
            self.labellist_show = [labellist[idx] for idx in random_order]
            self.predlist_show = [predlist[idx] for idx in random_order]

        firstimg = imread(self.imglist_show[0], key=0)
        img_y = firstimg.shape[0]
        img_x = firstimg.shape[1]
        img_stack_show = imageloader(self.imglist_show)
        label_stack_show = labelloader(self.labellist_show, (img_y, img_x))
        pred_stack_show = labelloader(self.predlist_show, (img_y, img_x))

        ly_image.data = img_stack_show
        ly_label_stroke.data = label_stack_show
        ly_suggestion.data = np.zeros(label_stack_show.shape, dtype = 'uint16')
        ly_label_pred.data = pred_stack_show
        ly_label_pred.refresh()
        return

    @thread_worker(connect={"returned": _dataloader})
    def main():
        return
    
    main()
    
'''

class dataloader(QWidget):
    # your QWidget.__init__ can optionally request the napari viewer instance
    # in one of two ways:
    # 1. use a parameter called `napari_viewer`, as done here
    # 2. use a type annotation of 'napari.viewer.Viewer' for any parameter
    def __init__(self, napari_viewer):
        super().__init__()
        self.viewer = napari_viewer
        btn = QPushButton("Click me!")
        btn.clicked.connect(self._on_click)

        self.setLayout(QHBoxLayout())
        self.layout().addWidget(btn)

    def _on_click(self):
        print("napari has", len(self.viewer.layers), "layers")