# Copyright (c) Facebook, Inc. and its affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import logging
import torch
from fairseq.tasks import register_task
from fairseq.tasks.translation import TranslationTask, TranslationConfig
from transformers import ElectraForPreTraining
from fairseq import metrics

logger = logging.getLogger(__name__)

@register_task("rdrop_summeration", dataclass=TranslationConfig)
class RDropTranslationTask(TranslationTask):
    
    @staticmethod
    def add_args(parser):
        TranslationTask.add_args(parser)
        parser.add_argument('--reg-alpha', default=0, type=float)

    def __init__(self, args, src_dict, tgt_dict):
        super().__init__(args, src_dict, tgt_dict)
        self.criterion_reg_alpha = getattr(args, 'reg_alpha', 0)
        
    def reduce_metrics(self, logging_outputs, criterion):
        with metrics.aggregate():
            # pass 'sample_size', 'nsentences', 'ntokens' stats to fairseq_task
            super().reduce_metrics(logging_outputs, criterion)
            for k in ["sample_size", "nsentences", "ntokens", "disc_loss"]:
                metrics.log_scalar(k, sum(l[k] for l in logging_outputs))

    def train_step(
        self, sample, model, criterion, optimizer, update_num, ignore_grad=False
    ):  

        model.train()
        model.set_num_updates(update_num)
        with torch.autograd.profiler.record_function("forward"):
            loss, sample_size, logging_output = criterion.forward_reg(model, sample, optimizer, self.criterion_reg_alpha, ignore_grad)
        return loss, sample_size, logging_output
