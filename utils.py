"""
Some codes from https://github.com/Newmu/dcgan_code
"""
from __future__ import division
import os
import math
import pprint
import scipy.misc
import numpy as np
import copy
import matplotlib.pyplot as plt

pp = pprint.PrettyPrinter()

get_stddev = lambda x, k_h, k_w: 1/math.sqrt(k_w*k_h*x.get_shape()[-1])

# -----------------------------
# new added functions for cyclegan
class ImagePool(object):
    def __init__(self, maxsize=50):
        self.maxsize = maxsize
        self.num_img = 0
        self.images = []

    def __call__(self, image):
        if self.maxsize <= 0:
            return image
        if self.num_img < self.maxsize:
            self.images.append(image)
            self.num_img += 1
            return image
        if np.random.rand() > 0.5:
            idx = int(np.random.rand()*self.maxsize)
            tmp1 = copy.copy(self.images[idx])[0]
            self.images[idx][0] = image[0]
            idx = int(np.random.rand()*self.maxsize)
            tmp2 = copy.copy(self.images[idx])[1]
            self.images[idx][1] = image[1]
            return [tmp1, tmp2]
        else:
            return image

def load_test_data(image_path, fine_size=256):
    img = imread(image_path)
    img = scipy.misc.imresize(img, [fine_size, fine_size])
    img = img/127.5 - 1
    return img

def load_train_data_backup(image_path, load_size=286, fine_size=256, is_testing=False):
    img_A = imread(image_path[0])
    img_B = imread(image_path[1])
    mask_A = np.load('datasets/personReid/trainA_mask/'+image_path[0].split('/')[-1].split('.')[0]+'.npy')
    mask_B = np.load('datasets/personReid/trainB_mask/'+image_path[1].split('/')[-1].split('.')[0]+'.npy')
    
    if not is_testing:
        img_A = scipy.misc.imresize(img_A, [load_size, load_size])
        img_B = scipy.misc.imresize(img_B, [load_size, load_size])
        h1 = int(np.ceil(np.random.uniform(1e-2, load_size-fine_size)))
        w1 = int(np.ceil(np.random.uniform(1e-2, load_size-fine_size)))
        img_A = img_A[h1:h1+fine_size, w1:w1+fine_size]
        img_B = img_B[h1:h1+fine_size, w1:w1+fine_size]

        if np.random.random() > 0.5:
            img_A = np.fliplr(img_A)
            img_B = np.fliplr(img_B)
    else:
        img_A = scipy.misc.imresize(img_A, [fine_size, fine_size])
        img_B = scipy.misc.imresize(img_B, [fine_size, fine_size])

    img_A = img_A/127.5 - 1.
    img_B = img_B/127.5 - 1.
    
    img_AB = np.concatenate((img_A, img_B), axis=2)
    mask_A = mask_A.reshape(256,256,1)
    mask_B = mask_B.reshape(256,256,1)
    img_AB = np.concatenate((img_AB, mask_A), axis=2)
    img_AB = np.concatenate((img_AB, mask_B), axis=2)

    # img_AB shape: (fine_size, fine_size, input_c_dim + output_c_dim+2)
    return img_AB

# -----------------------------

def get_image(image_path, image_size, is_crop=True, resize_w=64, is_grayscale = False):
    return transform(imread(image_path, is_grayscale), image_size, is_crop, resize_w)

def save_images(images, size, image_path):
    return imsave(inverse_transform(images), size, image_path)

def imread(path, is_grayscale = False):
    if (is_grayscale):
        return scipy.misc.imread(path, flatten = True).astype(np.float)
    else:
        return scipy.misc.imread(path, mode='RGB').astype(np.float)

def merge_images(images, size):
    return inverse_transform(images)

def merge(images, size):
    h, w = images.shape[1], images.shape[2]
    img = np.zeros((h * size[0], w * size[1], 3))
    for idx, image in enumerate(images):
        i = idx % size[1]
        j = idx // size[1]
        img[j*h:j*h+h, i*w:i*w+w, :] = image

    return img

def imsave(images, size, path):
    return scipy.misc.imsave(path, merge(images, size))

def center_crop(x, crop_h, crop_w,
                resize_h=64, resize_w=64):
  if crop_w is None:
    crop_w = crop_h
  h, w = x.shape[:2]
  j = int(round((h - crop_h)/2.))
  i = int(round((w - crop_w)/2.))
  return scipy.misc.imresize(
      x[j:j+crop_h, i:i+crop_w], [resize_h, resize_w])

def transform(image, npx=64, is_crop=True, resize_w=64):
    # npx : # of pixels width/height of image
    if is_crop:
        cropped_image = center_crop(image, npx, resize_w=resize_w)
    else:
        cropped_image = image
    return np.array(cropped_image)/127.5 - 1.

def inverse_transform(images):
    return (images+1.)/2.

def load_train_data(image_path, load_size=286, fine_size=256, is_testing=False):
    img_A = imread(image_path[0])
    img_B = imread(image_path[1])

    img_B_H, img_B_W = img_B.shape[:2]
    img_B_centx = img_B_W//2
    img_B_centy = img_B_H//2

    img_B_minx = max(img_B_centx-256, (load_size//2)+1)
    img_B_maxx = min(img_B_centx+256, img_B_W-(load_size//2)-1)

    img_B_miny = max(img_B_centy-256, load_size//2)
    img_B_maxy = min(img_B_centy+256, img_B_H=load_size//2)

    if img_B_minx < img_B_maxx:
        img_B_centx = random.randint(img_B_minx, img_B_maxx)
    else:
        img_B_centx = (img_B_minx+img_B_maxx)//2
    if img_B_miny < img_B_maxy:
        img_B_centy = random.randint(img_B_miny, img_B_maxy)
    else:
        img_B_centy = (img_B_miny+img_B_maxy)//2

    xmin = max(0, img_B_centx-(load_size//2))
    ymin = max(0, img_B_centy-(load_size//2))
    xmax = min(img_B_W, xmin+load_size)
    ymax = min(img_B_H, ymin+load_size)
    img_B = img_B[ymin:ymax, xmin:xmax]

    img_A_name = os.path.basename(image_path[0])
    img_B_name = os.path.basename(image_path[1])

    print('IMG_A', type(img_A), img_A.dtype, img_A.shape, np.max(img_A), np.min(img_A))
    print('IMG_B', type(img_B), img_B.dtype, img_B.shape, np.max(img_B), np.min(img_B))

    mask_A_dir = './datasets/{}/'.format('t2t_masks' + '/trainA')
    mask_B_dir = './datasets/{}/'.format('t2t_masks' + '/trainB')

    mask_A = os.path.join(mask_A_dir, img_A_name)
    mask_B = os.path.join(mask_B_dir, img_B_name)


    #mask_A = os.path.join('/Users/junhuang.hj/Desktop/code_paper/code/data_gene/src/mask_dir', img_A_name)
    #mask_B = os.path.join('/Users/junhuang.hj/Desktop/code_paper/code/data_gene/src/mask_dir', img_B_name)

    if os.path.isfile(mask_A):
        mask_A = imread(mask_A, is_grayscale=True)
    else:
        mask_A = np.zeros((load_size, load_size), dtype=np.float)

    if os.path.isfile(mask_B):
        mask_B = imread(mask_B, is_grayscale=True)
    else:
        mask_B = np.zeros((load_size, load_size), dtype=np.float)

    if not is_testing:
        img_A = scipy.misc.imresize(img_A, [load_size, load_size])
        img_B = scipy.misc.imresize(img_B, [load_size, load_size])

        mask_A = scipy.misc.imresize(mask_A, [load_size, load_size])
        mask_B = scipy.misc.imresize(mask_B, [load_size, load_size])

        h1 = int(np.ceil(np.random.uniform(1e-2, load_size-fine_size)))
        w1 = int(np.ceil(np.random.uniform(1e-2, load_size-fine_size)))
        img_A = img_A[h1:h1+fine_size, w1:w1+fine_size]
        img_B = img_B[h1:h1+fine_size, w1:w1+fine_size]

        mask_A = mask_A[h1:h1+fine_size, w1:w1+fine_size]
        mask_B = mask_B[h1:h1+fine_size, w1:w1+fine_size]

        if np.random.random() > 0.5:
            img_A = np.fliplr(img_A)
            img_B = np.fliplr(img_B)
            mask_A = np.fliplr(mask_A)
            mask_B = np.fliplr(mask_B)
    else:
        img_A = scipy.misc.imresize(img_A, [fine_size, fine_size])
        img_B = scipy.misc.imresize(img_B, [fine_size, fine_size])
        mask_A = scipy.misc.imresize(mask_A, [fine_size, fine_size])
        mask_B = scipy.misc.imresize(mask_B, [fine_size, fine_size])

    mask_m = np.max(mask_A)*0.18
    mask_A = np.array(mask_A > mask_m, dtype=np.float)
    mask_m = np.max(mask_B)*0.18
    mask_B = np.array(mask_B > mask_m, dtype=np.float)

    img_A = img_A/127.5 - 1.
    img_B = img_B/127.5 - 1.

    print('img_A', type(img_A), img_A.dtype, img_A.shape, np.max(img_A), np.min(img_A))
    print('img_B', type(img_B), img_B.dtype, img_B.shape, np.max(img_B), np.min(img_B))
    print('mask_A', type(mask_A), mask_A.dtype, mask_A.shape, np.max(mask_A), np.min(mask_A))
    print('mask_B', type(mask_B), mask_B.dtype, mask_B.shape, np.max(mask_B), np.min(mask_B))

    img_AB = np.concatenate((img_A, img_B), axis=2)
    mask_A = mask_A.reshape(fine_size, fine_size, 1)
    mask_B = mask_B.reshape(fine_size, fine_size, 1)
    img_AB = np.concatenate((img_AB, mask_A), axis=2)
    img_AB = np.concatenate((img_AB, mask_B), axis=2)

    # img_AB shape: (fine_size, fine_size, input_c_dim + output_c_dim+2)
    return img_AB


if __name__=='__main__':
    image_path = []
    image_path.append('/Users/junhuang.hj/Desktop/code_paper/code/data_gene/src/imgs_dir/process_0__DengXian_12_1_1556510481_4.jpg')
    image_path.append('/Users/junhuang.hj/Desktop/code_paper/code/data_gene/src/imgs_dir/process_0__DengXian_23_1_1556510479_3.jpg')
    load_train_data(image_path, load_size=286, fine_size=256, is_testing=False)


