import os
from glob import glob
import time

IMAGE_DIR = '/home/sensei/sensei-debug/extracts'
IMG_COUNT = 36

step = 0
step_pretty = str(step).zfill(6)

while True:
    images = glob(IMAGE_DIR + '/*')
    if any(step_pretty in i for i in images):
        current = [step_pretty in i for i in images]
        
        if np.unique(current, return_counts=True)[1][1] == IMG_COUNT:
         #if len(images) % IMG_COUNT == 0:
            
            print('calling cinema client')
            
            start = time.time()
            
            os.system('python3 cinema_client.py --name osc --input %'.format(IMAGE_DIR))
            
            elapsed = time.time() - start
            print('time elapsed: ' + str(elapsed)) 
 
            step += 1
            step_pretty = str(step).zfill(6)
            
