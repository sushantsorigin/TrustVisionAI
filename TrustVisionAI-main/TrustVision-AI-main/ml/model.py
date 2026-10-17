import torch
import torch.nn as nn
from torchvision import models

class DeepfakeResNetViT(nn.Module):
    def __init__(self, pretrained=True, freq_feature_size=256):
        super(DeepfakeResNetViT, self).__init__()

        # EfficientNet-V2-S backbone (SOTA for deepfake features)
        eff_weights = models.EfficientNet_V2_S_Weights.DEFAULT if pretrained else None
        self.efficientnet = models.efficientnet_v2_s(weights=eff_weights)
        self.eff_fc_in_features = self.efficientnet.classifier[1].in_features
        self.efficientnet.classifier[1] = nn.Identity()

        # Vision Transformer backbone
        vit_weights = models.ViT_B_16_Weights.DEFAULT if pretrained else None
        self.vit = models.vit_b_16(weights=vit_weights)
        self.vit_head_in_features = self.vit.heads.head.in_features
        self.vit.heads.head = nn.Identity()

        # Frequency & Edge branch CNN (Specifically targets 2026 Diffusion artifacts)
        self.freq_cnn = nn.Sequential(
            nn.Conv2d(2, 16, kernel_size=3, padding=1),
            nn.BatchNorm2d(16),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2),

            nn.Conv2d(16, 32, kernel_size=3, padding=1),
            nn.BatchNorm2d(32),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2),

            nn.Conv2d(32, 64, kernel_size=3, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),
            nn.AdaptiveAvgPool2d(1)
        )
        self.freq_feature_size = freq_feature_size
        self.freq_fc = nn.Linear(64, self.freq_feature_size)

        # Classifier: efficientnet + vit + freq + landmark scaler
        fused_features = self.eff_fc_in_features + self.vit_head_in_features + self.freq_feature_size + 1
        self.classifier = nn.Sequential(
            nn.Dropout(0.5),
            nn.Linear(fused_features, 512),
            nn.ReLU(inplace=True),
            nn.Dropout(0.5),
            nn.Linear(512, 2)
        )

        self.feature_names = {
            'efficientnet': self.eff_fc_in_features,
            'vit': self.vit_head_in_features,
            'freq': self.freq_feature_size,
            'fused': fused_features
        }
        self.register_buffer('input_mean', torch.tensor([0.485, 0.456, 0.406], dtype=torch.float32).view(1, 3, 1, 1), persistent=False)
        self.register_buffer('input_std', torch.tensor([0.229, 0.224, 0.225], dtype=torch.float32).view(1, 3, 1, 1), persistent=False)

    def _compute_freq_and_edge_map(self, x):
        x_float = x.float()
        x_denorm = x_float * self.input_std + self.input_mean
        gray = 0.299 * x_denorm[:, 0:1, :, :] + 0.587 * x_denorm[:, 1:2, :, :] + 0.114 * x_denorm[:, 2:3, :, :]
        
        # 1. FFT Magnitude (Catches Generative Checkerboard Artifacts in 2026 models)
        fft = torch.fft.fft2(gray, norm='ortho')
        fft_shift = torch.fft.fftshift(fft)
        magnitude = torch.log1p(torch.abs(fft_shift))
        min_v = magnitude.amin(dim=[1,2,3], keepdim=True)
        max_v = magnitude.amax(dim=[1,2,3], keepdim=True)
        fft_normed = (magnitude - min_v) / (max_v - min_v + 1e-6)

        # 2. Laplacian Edge Map (Catches 2026 Diffusion VAE over-smoothing and plastic skin)
        laplacian_kernel = torch.tensor([[[[0.0, 1.0, 0.0], [1.0, -4.0, 1.0], [0.0, 1.0, 0.0]]]], device=x.device, dtype=x_float.dtype)
        edges = torch.nn.functional.conv2d(gray, laplacian_kernel, padding=1)
        edges = torch.abs(edges)
        e_min = edges.amin(dim=[1,2,3], keepdim=True)
        e_max = edges.amax(dim=[1,2,3], keepdim=True)
        edges_normed = (edges - e_min) / (e_max - e_min + 1e-6)

        combined = torch.cat([fft_normed, edges_normed], dim=1)
        return combined.to(dtype=x.dtype)

    def forward(self, x, landmark_scores=None):
        eff_feats = self.efficientnet(x)
        vit_feats = self.vit(x)

        freq_x = self._compute_freq_and_edge_map(x)
        freq_feats = self.freq_cnn(freq_x)
        freq_feats = torch.flatten(freq_feats, 1)
        freq_feats = self.freq_fc(freq_feats)

        if landmark_scores is None:
            landmark_feats = torch.full((x.size(0), 1), 0.5, device=x.device)
        else:
            landmark_feats = landmark_scores.view(-1, 1).to(x.device)
        landmark_feats = landmark_feats.to(dtype=eff_feats.dtype)

        joint = torch.cat([eff_feats, vit_feats, freq_feats, landmark_feats], dim=1)
        out = self.classifier(joint)
        return out

    def get_target_layer(self):
        return [self.efficientnet.features[-1]]


class DeepfakeResNet(DeepfakeResNetViT):
    def __init__(self, pretrained=True, freq_feature_size=256):
        super(DeepfakeResNet, self).__init__(pretrained=pretrained, freq_feature_size=freq_feature_size)
