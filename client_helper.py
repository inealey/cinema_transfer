import os
from glob import glob
import time

IMAGE_DIR = 'extracts'
IMG_COUNT = 36

step = 0
step_pretty = str(step).zfill(6)

while True:
    images = glob(IMAGE_DIR + '/*')
    if step_pretty in images:
        if len(images) % IMG_COUNT == 0:
            
            print('calling cinema client')
            
            start = time.time()
            
            os.system('python3 cinema_client.py --name osc --input extracts')
            
            elapsed = time.time() - start
            
            step += 1
            step_pretty = str(step).zfill(6)
            