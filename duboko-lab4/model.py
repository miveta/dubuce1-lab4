import torch
import torch.nn as nn
import torch.nn.functional as F


class _BNReluConv(nn.Sequential):
    def __init__(self, num_maps_in, num_maps_out, k=3, bias=True):
        super(_BNReluConv, self).__init__()
        self.append(nn.BatchNorm2d(num_maps_in))
        self.append(nn.ReLU(inplace=True))
        self.append(nn.Conv2d(num_maps_in, num_maps_out, k, padding=1, bias=bias))


class SimpleMetricEmbedding(nn.Module):
    def __init__(self, input_channels, emb_size=32):
        super().__init__()
        self.emb_size = emb_size
        self.maxPool = nn.MaxPool2d(kernel_size=3, stride=2)
        self.globalAvgPool = nn.AdaptiveAvgPool2d(1)
        self.conv1 = _BNReluConv(input_channels, emb_size)
        self.conv2 = _BNReluConv(emb_size, emb_size)
        self.conv3 = _BNReluConv(emb_size, emb_size)
        # YOUR CODE HERE

    def get_features(self, img):
        # Returns tensor with dimensions BATCH_SIZE, EMB_SIZE
        # YOUR CODE HERE
        # provuć kroz model
        x = self.maxPool(self.conv1(img))
        x = self.maxPool(self.conv2(x))
        x = self.globalAvgPool(self.conv3(x))
        x = x.reshape(x.shape[0], x.shape[1])
        return x

    def loss(self, anchor, positive, negative):
        a_x = self.get_features(anchor)
        p_x = self.get_features(positive)
        n_x = self.get_features(negative)
        # implement triplet margin loss like pyTorch TripletMarginLoss
        # default l2 norm and margin = 1.0
        d_a_p = torch.norm(a_x - p_x, p=2, dim=1)
        d_a_n = torch.norm(a_x - n_x, p=2, dim=1)

        loss = torch.sum(torch.clamp(d_a_p - d_a_n + 1.0, min=0.0))
        return loss


class IdentityModel(nn.Module):
    def __init__(self):
        super(IdentityModel, self).__init__()

    def get_features(self, img):
        feats = img.reshape(img.shape[0], -1)
        return feats
