from client.bb_item import VisualObject
import os.path
from projectile import Projectile as Base

class Projectile(Base):
    def __init__(self):
        Base.__init__(self)
        self.visual = VisualObject(os.path.join("data", "banana.png"))
