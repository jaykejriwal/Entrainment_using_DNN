# ------------------------------------------------------------------------
# Name : feat_extract_nopre.py
# Author : Jay Kejriwal
# Date   : 03-04-22
# Description : resample to 16k Hz, and run openSMILE to extract features
# ------------------------------------------------------------------------
from __future__ import division
import sys, os
import csv
from os.path import basename
import pandas as pd
import numpy as np
import argparse
import subprocess
from sklearn import preprocessing
import matplotlib.pyplot as plt
import pdb
import math

# -----------------
def_wav = '/home/jay_kejriwal/Fisher/fisher03_audio/fe_03_00708.sph'
config_path = '/home/jay_kejriwal/Fisher/Programs/LLD/emobase2010_haoqi_revised.conf'
out_dir = '/home/jay_kejriwal/Fisher/Processed/Embeddings/LLD'
transcript_dir='/home/jay_kejriwal/Fisher/fisher03_text'
feat_dir = '/home/jay_kejriwal/Fisher/Programs/LLD/raw_features'


IPU_gap=50
writing=True   # set True for getting functionals
extract=True 

#------------------------------------------------

# ------------------------------------------------------------------------
# Params Setup				 
# ------------------------------------------------------------------------
parser = argparse.ArgumentParser(description='Process some integers.')

parser.add_argument('--audio_file', type=str, required=False, default=def_wav,
					help='File path of the input audio file')
parser.add_argument('--transcript_file', type=str, required=False, default=transcript_dir,
					help='File path of the input transcript file')
parser.add_argument('--openSMILE_config', type=str, required=False, default=config_path,
					help='config file of openSMILE')
parser.add_argument('--output_path', type=str, required=False, default=out_dir,
					help='output folder path')
parser.add_argument('--norm', type=str, required=False, default=True, 
					help='do session level normalization or not')
parser.add_argument('--window_size', required=False, type=float, default=None)
parser.add_argument('--shift_size', required=False, type=float, default=1)

args = parser.parse_args()

CONFIG_openSMILE = args.openSMILE_config
INPUT_audio      = args.audio_file
Trancript_audio  = args.transcript_file
OUTPUT_path      = args.output_path
window_size      = args.window_size
shift_size       = args.shift_size
norm             = args.norm

if window_size is None:
	window_size = 10
if shift_size is None:
	shift_size = 1
if norm == 'False':
	norm = False

print(sys.stderr,  'Current audio file: %s ' %INPUT_audio)
print(sys.stderr,  'Current audio file: %s ' %Trancript_audio)

def get_status_output(*args, **kwargs):
    p = subprocess.Popen(*args, **kwargs)
    stdout, stderr = p.communicate()
    return p.returncode, stdout, stderr
#----------------------------------------------------------------
#---------------------------------------------------------------------
# check if file is wav or not
#---------------------------------------------------------------------
if extract:
	not_wav = False
	if basename(INPUT_audio).split('.')[-1] != 'wav':
		not_wav = True
		print(sys.stderr,  'convert to .wav file...') 
		# cmd2wav = 'sox ' + INPUT_audio +' '+ basename(INPUT_audio).split('.')[-2]+'.wav'
		cmd2wav = 'sph2pipe -f rif ' + INPUT_audio +' '+ basename(INPUT_audio).split('.')[-2]+'.wav'
		subprocess.run(cmd2wav, shell  = True)
		INPUT_audio = basename(INPUT_audio).split('.')[-2]+'.wav'
		file_to_be_removed = basename(INPUT_audio).split('.')[-2]+'.wav'
	# ------------------------------------------------------------------------
	# downsample audio to 16kHz and convert to mono (unless file already downsampled)
	# ------------------------------------------------------------------------
	print(INPUT_audio)
	cmd_check_sample_rate = 'sox --i -r '+ INPUT_audio
	print(cmd_check_sample_rate)
	sample_rate = subprocess.run(cmd2wav, shell  = True)
	#t1=librosa.get_samplerate(INPUT_audio)
	not_16k = False
	if sample_rate != '16000':
		not_16k = True
		print(sys.stderr,  "Resampling to 16k ... ")
		output_16k_audio = 'resampled--' + os.path.basename(INPUT_audio)
		cmd_resample = 'sox %s -b 16 -c 1 -r 16k %s dither -s' %(INPUT_audio, output_16k_audio)
		subprocess.run(cmd_resample, shell  = True)
		# replace variable with downsampled audio
		#INPUT_audio = ''.join(output_16k_audio.split('--')[1:])
		INPUT_audio = output_16k_audio

	# # ------------------------------------------------------------------------
	# # extract feature use openSMILE
	# # ------------------------------------------------------------------------
	if not os.path.exists(OUTPUT_path):
		os.makedirs(OUTPUT_path)
	if not_16k:
		csv_file_name = feat_dir +'/'+ basename(INPUT_audio).split('.wav')[0].split('--')[1] + '.csv'
	else:
		csv_file_name = feat_dir +'/'+basename(INPUT_audio).split('.wav')[0] + '.csv'
	print(sys.stderr,  "Using openSMILE to extract features ... ")
	cmd_feat = '/home/jay_kejriwal/Fisher/opensmile/build/progsrc/smilextract/SMILExtract -C %s -I %s -O %s' %(CONFIG_openSMILE, INPUT_audio, csv_file_name)
	subprocess.call(cmd_feat, shell  = True)

	# delete resampled audio file
	if not_wav:
		os.remove(file_to_be_removed)
	if not_16k:
		os.remove(output_16k_audio)


# ------------------------------------------------------------------------
# load transcript timings
# ------------------------------------------------------------------------
## TODO: load the file from trans/, store it in an array in start, end, spk (A or B) fmt

spk_list=[]
if extract:
	ext='.wav'
else:
	ext='.csv'

if extract:
	transcript = transcript_dir +'/'+ basename(INPUT_audio).split(ext)[0].split('--')[1] + '.txt'
	#basename(Trancript_audio).split(ext)[0].split('--')[1] + '.txt'
else:
	transcript = transcript_dir +'/'+ basename(INPUT_audio).split(ext)[0] + '.txt'
trans = open(transcript).readlines()
# pdb.set_trace()
for line in trans:
	if line!='\n':
		if line[0] !='#':
			start, stop, spk = line.split(':')[0].split(' ')
			spk_list.append([start, stop, spk])

# ------------------------------------------------------------------------
# functional calculation: this has to be  PER Utterance (for entrainment)
# ------------------------------------------------------------------------
# frame length and overlap size in seconds
# frame_len = window_size/0.01
# frame_shift_len = shift_size/0.01


# csv_file_name = feat_dir +'/'+basename(INPUT_audio).split('.sph')[0] + '.csv'

if extract:
	csv_file_name = feat_dir +'/'+basename(INPUT_audio).split(ext)[0].split('--')[1]  + '.csv'
else:
	csv_file_name = feat_dir +'/'+basename(INPUT_audio).split(ext)[0]  + '.csv'

# read csv feature file
csv_feat = pd.read_csv(csv_file_name, dtype=np.float32)
csv_feat = csv_feat.values.copy()

feat_data = np.copy(csv_feat)
# convert the first column indext to int index
sample_index = list(map(int,list((feat_data[:,0]))))


# def turn_level_index(spk_list, sample_index):
	# '''generate indices for different turns'''

turn_level_index_list=[]
last_spk ='A'
s2_found=True
gap_found=True
# pdb.set_trace()
for spch in spk_list:
	start = int(float(spch[0])/0.01)
	stop = int(float(spch[1])/0.01)
	spk = spch[2]
	if not turn_level_index_list:
		turn_level_index_list = [sample_index[start:stop]]
		last_stop =stop
		continue
	if spk==last_spk:
		if start-last_stop < IPU_gap/10:
			turn_level_index_list[-1].extend(sample_index[start:stop])

		else:
			if s2_found:
				if gap_found:
					turn_level_index_list[-1]=sample_index[start:stop]
				else:
					turn_level_index_list.append(sample_index[start:stop])
					
			else:
				turn_level_index_list.append(sample_index[start:stop])
				s2_found=True		
			gap_found=True		
	else:
		if not gap_found:
			turn_level_index_list.append(turn_level_index_list[-1])
		gap_found=False
		s2_found=False
		turn_level_index_list.append(sample_index[start:stop])
	last_stop=stop
	last_spk = spk

if len(turn_level_index_list)%2==1:
	turn_level_index_list=turn_level_index_list[:-1]


s1_list=[]
s2_list=[]
for i, itm in enumerate(turn_level_index_list):
	if i%2==0:
		s1_list.append(itm)
	else:
		s2_list.append(itm)
##-----------------------------------------------------------------------
## feature selection and normalization 
##-----------------------------------------------------------------------
# remove the mean for mfcc
# normalize for pitch = log(f_0/u_0)
# normalize for loudness 
epsilon=0.0001
if norm:
	# do normalization
	print(sys.stderr,  "Do session level feature normalization... ")
	# f0 normalization
	f0                            = np.copy(feat_data[:, 70])
	# replace 0 in f0 with epsilon
	f0[f0==0.]                     = epsilon
	f0_mean                       = np.nanmean(f0)
	f0[~np.isnan(f0)]             = np.log2(f0[~np.isnan(f0)]/f0_mean)
	f0                            = np.reshape(f0,(-1,1))
	
	# f0_de normalization
	f0_de                         = np.copy(feat_data[:, 74])
	f0_de[f0_de==0.]               = epsilon
	f0_de_mean                    = np.nanmean(f0_de)
	f0_de[~np.isnan(f0_de)]       = np.log2(np.absolute(f0_de[~np.isnan(f0_de)]/f0_de_mean))
	f0_de                         = np.reshape(f0_de,(-1,1))
	# intensity normalization
	intensity                     = np.copy(feat_data[:,2])
	int_mean                      = np.mean(intensity)
	intensity                     = intensity / int_mean
	intensity                     = np.reshape(intensity, (-1,1))
	
	# intensity_de normalization
	intensity_de                  = np.copy(feat_data[:,36])
	int_de_mean                   = np.mean(intensity_de)
	intensity_de                  = intensity_de / int_de_mean
	intensity_de                  = np.reshape(intensity_de, (-1,1))
	
	# all other features normalization, just 
	# feat_idx                      = range(3,34) + range(37, 68)   with spectral de
	feat_idx                      = range(3,34)
	mfcc_etc                      = np.copy(feat_data[:,feat_idx])
	
	mfcc_etc_mean                 = np.mean(mfcc_etc, axis=0)
	mfcc_etc_mean.reshape(-1,1)
	mfcc_etc_norm                 =  mfcc_etc - mfcc_etc_mean
	
	# jitter and shimmer normalization
	idx_jitter_shimmer            = [71,72,73]
	jitter_shimmer                = np.copy(feat_data[:,idx_jitter_shimmer])
	jitter_shimmer[jitter_shimmer==0.] = epsilon
	jitter_shimmer_mean           = np.nanmean(jitter_shimmer, axis=0)
	jitter_shimmer_mean.reshape(-1,1)
	jitter_shimmer_norm           = jitter_shimmer - jitter_shimmer_mean
else:
	# did not do session level normalization
	print(sys.stderr,  "Ignore session level feature normalization... ")
	# f0 normalization
	f0                            = np.copy(feat_data[:, 70])
	# replace 0 in f0 with nan
	f0[f0==0.]                     = epsilon
	f0_mean                       = np.nanmean(f0)
	f0                            = np.reshape(f0,(-1,1))
	
	# f0_de normalization
	f0_de                         = np.copy(feat_data[:, 74])
	f0_de[f0_de==0.]               = epsilon
	f0_de                         = np.reshape(f0_de,(-1,1))
	
	# intensity normalization
	intensity                     = np.copy(feat_data[:,2])
	intensity                     = np.reshape(intensity, (-1,1))
	
	# intensity_de normalization
	intensity_de                  = np.copy(feat_data[:,36])
	intensity_de                  = np.reshape(intensity_de, (-1,1))
	
	# feat_idx                      = range(3,34) + range(37, 68)   with spectral de
	feat_idx                      = range(3,34)
	mfcc_etc                      = np.copy(feat_data[:,feat_idx])
	mfcc_etc_norm                 =  np.copy(mfcc_etc) 
	
	# jitter and shimmer normalization
	idx_jitter_shimmer            = [71,72,73]
	jitter_shimmer                = np.copy(feat_data[:,idx_jitter_shimmer])
	jitter_shimmer[jitter_shimmer==0.] = epsilon
	jitter_shimmer_norm           = jitter_shimmer 

##-----------------------------------------------------------------------
## function calculation
##-----------------------------------------------------------------------
all_raw_norm_feat = np.hstack((f0, f0_de, intensity, intensity_de,  jitter_shimmer_norm, mfcc_etc_norm))
# feature dimension
all_raw_feat_dim = all_raw_norm_feat.shape[1]


def final_feat_calculate(sample_index, all_raw_norm_feat):
	whole_output_feat = np.array([], dtype=np.float32).reshape(0, all_raw_feat_dim*6)
	for idx_frame in sample_index:
		tmp_all_raw_norm_feat = np.copy(all_raw_norm_feat[idx_frame,:])
		funcs_per_frame = func_calculate(tmp_all_raw_norm_feat)
		whole_output_feat = np.concatenate((whole_output_feat, funcs_per_frame), axis=0)
	return whole_output_feat

def func_calculate(input_feat_matrix):
	'''
		Given a numpy array calculate its statistic functions 
		6 functions: mean, median, std, perc1, perc99, range99-1
	'''
	output_feat = np.array([], dtype=np.float32).reshape(1, -1)
	num_feat = input_feat_matrix.shape[1]
	for i in range(num_feat):
		#print i
		tmp              = input_feat_matrix[:,i]
		tmp_no_nan       = tmp[~np.isnan(tmp)]
		if tmp_no_nan.size == 0:

			mean_tmp         = 0
			std_tmp          = 0
			median_tmp       = 0
			perc1            = 0
			perc99           = 0
			range99_1        = 0
		else:
			mean_tmp         = np.nanmean(tmp)
			std_tmp          = np.nanstd(tmp)
			median_tmp       = np.median(tmp_no_nan)
			tmp_no_nan_sorted= np.sort(tmp_no_nan)
			total_len        = tmp_no_nan_sorted.shape[0]
			perc1_idx        = np.int_(np.ceil(total_len*0.01))
			if perc1_idx >= total_len:
				perc1_idx = 0 
			perc99_idx       = np.int_(np.floor(total_len*0.99))
			if perc99_idx < 0 or perc99_idx >= total_len:
				perc99_idx = total_len-1 
			perc1            = tmp_no_nan_sorted[perc1_idx]
			perc99           = tmp_no_nan_sorted[perc99_idx]
			range99_1        = perc99 - perc1
		# append for one 
		new_func = np.array([mean_tmp, median_tmp, std_tmp, perc1, perc99, range99_1])
		new_func = np.reshape(new_func, (1,6))
		output_feat = np.hstack((output_feat,new_func))

	return output_feat

whole_func_feat1 = final_feat_calculate(s1_list, all_raw_norm_feat)
whole_func_feat2 = final_feat_calculate(s2_list, all_raw_norm_feat)
whole_func_feat = np.hstack((whole_func_feat1,whole_func_feat2))


##-----------------------------------------------------------------------
## normalization at whole session level, using scikit learn
## -- for each feature 0 mean and 1 variance
##-----------------------------------------------------------------------
# norm_whole_func_feat = preprocessing.scale(whole_func_feat)
# write to csv file

if writing==True:
	feat_csv_file_name = out_dir + '/' + basename(csv_file_name).split('.csv')[0] + '.csv'
	print(feat_csv_file_name)
	with open(feat_csv_file_name, 'w') as fcsv:
		writer = csv.writer(fcsv)
		writer.writerows(whole_func_feat)
