"""Pytest configuration and fixtures"""

import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import torchvision before TensorFlow pulls in its native libraries.
# torchvision loads Triton via torch._dynamo; on some TensorFlow/PyTorch
# builds, loading Triton *after* TensorFlow aborts the interpreter with
# "free(): invalid pointer". Importing torchvision up front loads Triton in a
# safe order so the Keras (TensorFlow) and Lightning tests can share one
# process. If torchvision isn't installed, torchmetrics simply skips its
# torchvision-dependent metrics, so the failure here is non-fatal.
try:
    import torchvision  # noqa: F401
except ImportError:
    pass
