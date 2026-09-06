import os

os.environ["MAAFW_BINARY_PATH"] = os.path.expanduser("~/maa-bin")

from maa.resource import Resource
from maa.toolkit import Toolkit

Toolkit.init_option("./")
resource = Resource()
resource.post_bundle("./resource").wait()
