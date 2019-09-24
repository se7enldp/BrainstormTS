import os
import sys
import glob
import numpy as np
import pandas as pd
import nibabel as nib

import matplotlib.pylab as plt
import matplotlib.cm as cm
import matplotlib.image as Image

import torch
import torch.nn as nn
from torch.utils.data import Dataset
import scipy.misc

from .datautils import *

module = ['flair', 't1', 't1ce', 't2']

class BraTS2017(Dataset):
	"""
		先做tumor core任务试试，打通数据与模型。
		tumor core：label中只有像素值4代表肿瘤核。
	"""
	def __init__(self, train_root_path, val_root_path, is_train=True, step=1):
		"""
			参数说明：
				train_root_path: 训练根目录
				val_root_path: 验证根目录
				is_train: 是否为训练模式
				step: 第几次模型使用的数据集
		"""
		self.train_root_path = train_root_path
		self.val_root_path = val_root_path
		self.is_train = is_train
		self.data_box = [144, 192, 192]
		self.data_size = 16
		self.step = step

		# hgg_path_list = glob.glob(self.train_root_path+'/HGG/*')
		# lgg_path_list = glob.glob(self.train_root_path+'/LGG/*')
		self.path_list = load_hgg_lgg_files(self.train_root_path)
		if self.is_train:
			self.path_list = self.path_list[:int(0.9*len(self.path_list))]
		else:
			self.path_list = self.path_list[int(0.9*len(self.path_list)):]
		# if not self.is_train:
		# 	self.path_list = load_val_file(self.val_root_path)
		
		# print(self.path_list)

	
	def __len__(self):
		return len(self.path_list)
	
	def __getitem__(self, index):
		path = self.path_list[index]

		if self.step == 2:
			image, label = self.pretreat(path)
			image, label = self.train_pretreat(image, label)
			image = torch.from_numpy(image).float()
			label = torch.from_numpy(label).float()
			# print(label.shape)
		elif self.step == 1:
			image, label = self.module_detection(path)

		return image, label
	
	def module_detection(self, path):
		"""
			数据定位的数据处理。
		"""
		image = []
		label = []
		image_t, label_t = make_image_label(path)
		
		flair, t1, t1ce, t2 = image_t
		seg = label_t

		# 去定裁剪区域.
		box_min, box_max = get_box(seg, 0)
		print(box_min)
		print(box_max)
		return image, label

	def pretreat(self, path):
		"""
			处理图像与标签。
		"""
		image = []
		label = []

		image_t, label_t = make_image_label(path)
		# print(image_t[0].shape)
		flair, t1, t1ce, t2 = image_t
		seg = label_t

		# 按照flair确定裁剪区域
		box_min, box_max = get_box(flair, 0)
		index_min, index_max = make_box(flair, box_min, box_max, self.data_box)

		# 裁剪
		flair = crop_with_box(flair, index_min, index_max)
		t1 = crop_with_box(t1, index_min, index_max)
		t1ce = crop_with_box(t1ce, index_min, index_max)
		t2 = crop_with_box(t2, index_min, index_max)
		seg = crop_with_box(seg, index_min, index_max)

		# 标准化
		flair = normalization(flair)
		t1 = normalization(t1)
		t1ce = normalization(t1ce)
		t2 = normalization(t2)

		tumor_core_label = get_tumor_core_labels(seg)

		# 想法：阅读别人的程序，发现也可以多方向扫描MRI。
		# ...

		image.append(flair)
		image.append(t1)
		image.append(t1ce)
		image.append(t2)

		label.append(tumor_core_label)

		image = np.asarray(image)
		label = np.asarray(label)
		# print(image.shape)
		# print(label.shape)

		return image, label

	def train_pretreat(self, image, label):
		"""
			随机切片。
		"""
		times = int(image.shape[1] / self.data_size)

		image_volumn = []
		label_volumn = []

		for i in range(times):
			if self.is_train:
				st = np.random.randint(0, image.shape[1] - self.data_size+1)
			else:
				st = i * self.data_size
			
			image_volumn.append(image[:, st:st+self.data_size, :, :])
			label_volumn.append(label[:, st:st+self.data_size, :, :])
		
		image_volumn = np.asarray(image_volumn)
		label_volumn = np.asarray(label_volumn)
		
		return image_volumn, label_volumn












