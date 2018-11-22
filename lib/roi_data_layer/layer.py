# coding:utf-8
# --------------------------------------------------------
# Fast R-CNN
# Copyright (c) 2015 Microsoft
# Licensed under The MIT License [see LICENSE for details]
# Written by Ross Girshick
# --------------------------------------------------------

# 训练时使用data layer，用来训练 Fast R-CNN network.
"""The data layer used during training to train a Fast R-CNN network.
# RoIDataLayer实现了一个caffe python 层
RoIDataLayer implements a Caffe Python layer.
"""
# data layer用于训练时训练Fast R-CNN network
from fast_rcnn.config import cfg
from roi_data_layer.minibatch import get_minibatch
import numpy as np

class RoIDataLayer(object):
    """Fast R-CNN data layer used for training."""

    def __init__(self, roidb, num_classes):
        """Set the roidb to be used by this layer during training."""
        self._roidb = roidb
        self._num_classes = num_classes
        self._shuffle_roidb_inds()

    def _shuffle_roidb_inds(self):
        """Randomly permute the training roidb."""
        # self._perm是打乱后的roidb
        self._perm = np.random.permutation(np.arange(len(self._roidb)))
        self._cur = 0

    def _get_next_minibatch_inds(self):
        """Return the roidb indices for the next minibatch."""
        
        # 训练时是False； end2end的yml中是True
        '''
        EXP_DIR: faster_rcnn_end2end
        TRAIN:
          HAS_RPN: True
          IMS_PER_BATCH: 1
          BBOX_NORMALIZE_TARGETS_PRECOMPUTED: True
          RPN_POSITIVE_OVERLAP: 0.7
          RPN_BATCHSIZE: 256
          PROPOSAL_METHOD: gt
          BG_THRESH_LO: 0.0
        TEST:
          HAS_RPN: True
        '''
        if cfg.TRAIN.HAS_RPN:
            # 一次只训练一张图片
            if self._cur + cfg.TRAIN.IMS_PER_BATCH >= len(self._roidb):
                self._shuffle_roidb_inds()

            db_inds = self._perm[self._cur:self._cur + cfg.TRAIN.IMS_PER_BATCH]
            self._cur += cfg.TRAIN.IMS_PER_BATCH
        else:
            # sample images
            db_inds = np.zeros((cfg.TRAIN.IMS_PER_BATCH), dtype=np.int32)
            i = 0
            while (i < cfg.TRAIN.IMS_PER_BATCH):
                ind = self._perm[self._cur]
                num_objs = self._roidb[ind]['boxes'].shape[0]
                if num_objs != 0:
                    db_inds[i] = ind
                    i += 1

                self._cur += 1
                if self._cur >= len(self._roidb):
                    self._shuffle_roidb_inds()

        return db_inds

    def _get_next_minibatch(self):
        """Return the blobs to be used for the next minibatch.

        If cfg.TRAIN.USE_PREFETCH is True, then blobs will be computed in a
        separate process and made available through self._blob_queue.
        """
        db_inds = self._get_next_minibatch_inds()
        minibatch_db = [self._roidb[i] for i in db_inds]
        # get_minibatch返回的是blob? 是的
        return get_minibatch(minibatch_db, self._num_classes)
            
    def forward(self):
        """Get blobs and copy them into this layer's top blob vector."""
        blobs = self._get_next_minibatch()
        return blobs
