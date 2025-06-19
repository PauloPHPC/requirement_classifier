import torch
import torch.nn as nn
import torch.nn.functional as F
from transformers import (
    AutoModel,
)

class FocalLoss(nn.Module):
    def __init__(self, weight=None, gamma=2.0, reduction='mean'):
        super().__init__()
        self.weight = weight
        self.gamma = gamma
        self.reduction = reduction

    def forward(self, logits, targets):
        # força o weight para o dispositivo dos logits
        weight = self.weight.to(logits.device) if self.weight is not None else None

        ce = F.cross_entropy(logits, targets, weight=weight, reduction='none')
        pt = torch.exp(-ce)
        focal = ((1 - pt) ** self.gamma) * ce

        if self.reduction == 'mean':
            return focal.mean()
        elif self.reduction == 'sum':
            return focal.sum()
        else:
            return focal
        
class BertForMultiTask(nn.Module):
    def __init__(self, model_name, num_categories, gamma=2.0,
                 weight_bin=None, weight_cat=None):
        super().__init__()
        self.backbone = AutoModel.from_pretrained(model_name)
        config = self.backbone.config

        # hidden_size é comum a todas as configs
        hidden = config.hidden_size

        # fallback para dropout: usa hidden_dropout_prob (BERT/RoBERTa) ou config.dropout (DistilBERT)
        dropout_prob = getattr(config, "hidden_dropout_prob", None)
        if dropout_prob is None:
            dropout_prob = getattr(config, "dropout", 0.1)

        self.dropout = nn.Dropout(dropout_prob)

        self.bin_head = nn.Linear(hidden, 2)
        self.cat_head = nn.Linear(hidden, num_categories)

        self.focal_bin = FocalLoss(weight=weight_bin, gamma=gamma, reduction='mean')
        self.focal_cat = FocalLoss(weight=weight_cat, gamma=gamma, reduction='mean')

    def forward(self, input_ids, attention_mask, binary_labels=None, category_labels=None):
        out = self.backbone(input_ids=input_ids, attention_mask=attention_mask)

        # se existir pooler_output (BERT/RoBERTa), use-o, senão pega CLS de last_hidden_state (DistilBERT)
        if hasattr(out, "pooler_output") and out.pooler_output is not None:
            cls_emb = out.pooler_output
        else:
            cls_emb = out.last_hidden_state[:, 0]

        pooled = self.dropout(cls_emb)

        logits_bin = self.bin_head(pooled)
        logits_cat = self.cat_head(pooled)

        loss = None
        if binary_labels is not None:
            loss_bin = self.focal_bin(logits_bin, binary_labels)

            mask = binary_labels == 1
            if mask.any():
                loss_cat = self.focal_cat(logits_cat[mask], category_labels[mask])
            else:
                loss_cat = torch.tensor(0.0, device=loss_bin.device)

            loss = loss_bin + loss_cat

        return {"loss": loss, "logits_bin": logits_bin, "logits_cat": logits_cat}