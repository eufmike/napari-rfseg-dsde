from tqdm import tqdm
import numpy as np
from skimage.io import imread, imsave

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