import sys
import pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / 'game'))

import random
import pickle
import json
import os
from collections import defaultdict

import numpy as np
from helper_functions import ACTIONS, END_TURN, state_to_key, make_clad, make_nibbit