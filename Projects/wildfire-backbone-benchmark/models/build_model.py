import timm
import timm.models._builder as _timm_builder

# This environment's egress policy blocks huggingface.co (timm's default weight
# host) but allows github.com and storage.googleapis.com, where timm's older
# non-HF-hub checkpoint URLs still live. Forcing has_hf_hub() to report
# unavailable makes timm fall back to those URLs instead of failing on the
# blocked Hub download.
_timm_builder.has_hf_hub = lambda necessary=False: False


def build_model(backbone_name, num_classes=3, freeze_backbone=True):
    model = timm.create_model(backbone_name, pretrained=True, num_classes=num_classes)

    if freeze_backbone:
        for name, param in model.named_parameters():
            if "head" not in name and "fc" not in name and "classifier" not in name:
                param.requires_grad = False

    return model
