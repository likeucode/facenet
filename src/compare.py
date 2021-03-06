"""Performs face alignment and calculates L2 distance between the embeddings of two images."""

# MIT License
# 
# Copyright (c) 2016 David Sandberg
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from scipy import misc
import tensorflow as tf
import numpy as np
import os
import sys
import argparse
import facenet
import align_dlib

def main(args):
    align = align_dlib.AlignDlib(os.path.expanduser(args.dlib_face_predictor))
    image_paths = [args.image1, args.image2]
    landmarkIndices = align_dlib.AlignDlib.OUTER_EYES_AND_NOSE

    with tf.Graph().as_default():

        with tf.Session() as sess:
      
            # Load the model
            print('Loading model "%s"' % args.meta_file)
            facenet.load_model(args.model_dir, args.meta_file, args.ckpt_file)
    
            # Get input and output tensors
            images_placeholder = tf.get_default_graph().get_tensor_by_name("input:0")
            phase_train_placeholder = tf.get_default_graph().get_tensor_by_name("phase_train:0")
            embeddings = tf.get_default_graph().get_tensor_by_name("embeddings:0")
            image_size = int(images_placeholder.get_shape()[1])

            # Run forward pass to calculate embeddings
            images = load_and_align_data(image_paths, image_size, align, landmarkIndices)
            feed_dict = { images_placeholder: images, phase_train_placeholder: False }
            emb = sess.run(embeddings, feed_dict=feed_dict)
            dist = np.sqrt(np.mean(np.square(np.subtract(emb[0,:], emb[1,:]))))
            print('Distance between the embeddings: %3.6f' % dist)
            
def load_and_align_data(image_paths, image_size, align, landmarkIndices):
    nrof_samples = len(image_paths)
    img_list = [None] * nrof_samples
    for i in xrange(nrof_samples):
        img = misc.imread(image_paths[i])
        aligned = align.align(image_size, img, landmarkIndices=landmarkIndices, skipMulti=True)
        prewhitened = facenet.prewhiten(aligned)
        img_list[i] = prewhitened
    images = np.stack(img_list)
    return images

def parse_arguments(argv):
    parser = argparse.ArgumentParser()
    
    parser.add_argument('model_dir', type=str, 
        help='Directory containing the meta_file and ckpt_file')
    parser.add_argument('meta_file', type=str, 
        help='File containing the model parameters as well as the model metagraph (with extension ".meta")')
    parser.add_argument('ckpt_file', type=str, 
        help='Checkpoint file (with extention ".ckpt-XXXXX"')
    parser.add_argument('image1', type=str, help='First image to compare.')
    parser.add_argument('image2', type=str, help='Second image to compare.')
    parser.add_argument('--dlib_face_predictor', type=str,
        help='File containing the dlib face predictor.', default='../data/shape_predictor_68_face_landmarks.dat')
    return parser.parse_args(argv)

if __name__ == '__main__':
    main(parse_arguments(sys.argv[1:]))
