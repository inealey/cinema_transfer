import os
import socket, select
import traceback
import pickle
from glob import glob
import argparse

"""
current assumptions:
(in the future, verify these):

- cinema image file names are written with the following convention:
    'RenderView1_000000p=000.00t=000.00.png'
    view name, _, time step, p=phi, t=theta

- when this client script is called, only cinema output from 
    whole timesteps is present (PNG data and .csv produced).
    i.e. if any images from timestep n are present in the input directory,
    ALL images from timestep n are present.
    
- all of the data from a single timestep fits into memory (do not need to 
    break up data to send)
"""

def extract_timestep(filename):
    """
    filename: filename in cinema convention:
        assumes cinema image file names are written like:
        'RenderView1_000000p=000.00t=000.00.png'
    returns: timestep from filename as integer
    """
    return int(filename.split('/')[-1].split('_')[1][:6])


def write_log(filename, dbName, timestep):
    """
    once a timestep has been completed, 
    write name of cinema db and completed timestep to log
    """
    log = open(filename, 'a')
    log.write(dbName + ' ' + str(timestep) + '\n')
    log.close()
    
    
def check_log(filename, dbName, timestep):
    """
    check what timesteps have been completed on the current db
    maybe implement in a better way if need to scale
    returns true if current timestep is present
    """    
    log = open(filename, 'rt')
    if dbName + ' ' + str(timestep) + '\n' in log.readlines():
        return True
    else:
        return False


def txt_query(sock, msg):
    """
    sock: socket to read/write from
    msg: message to send
    returns: 16 byte response from server
    """
    sock.sendall(msg.encode())
    response = sock.recv(16).decode()
    return response


def main(config):
    """
    initialize socket, send cinema data to server
    """
    
    ## check log for which timestep to process
    if os.path.isfile(config.log):
        ## assuming log file is a reasonable size here.
        with open(config.log, 'r') as file:
            lines = file.readlines()
            for l in lines:
                if config.name in l:
                    ts = int(l.split()[1]) + 1
    else:
        ts = 0
    
    ## timestep var to string
    ts = str(ts).zfill(6)
    
    ## read all files in path into list
    nameList, dataList = ['NAMES'], ['DATA']
    imgFiles = sorted(glob(config.input + '/*.png'))
    for img in imgFiles:
        if ts in img:
            nameList.append(img.split('/')[-1])
            file = open(img, 'rb')
            dataList.append(file.read())
            file.close()

    if len(nameList) == 0:
        exit('no images from current timestep found. exiting.')

    ## serialize lists
    namePkl = pickle.dumps(nameList)
    dataPkl = pickle.dumps(dataList)

    ## num bytes for each flattened object
    nameSize = len(namePkl)
    dataSize = len(dataPkl)
        
    try:
        ## init socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_address = (config.host, config.port)
        sock.connect(server_address)
        

        ## start conversation w server
        response = txt_query(sock, ('NSIZE %s' % nameSize))
        if response:
            active = True
            print('preparing to transfer ' + 
                  str(dataSize / 1000000) + ' MB to ' +
                  config.host + ':' + str(config.port)  )
        else:
            active = False
            print('no response from server')
        
        ## negotiate w server while connection open
        while active:

            if response == 'GOT_NSIZE':
                sock.sendall(namePkl)
                response = sock.recv(16).decode()
                if response != 'GOT_NAMES':
                    active = False
                else:
                    response = txt_query(sock, 'DSIZE %s' % dataSize)

            elif response == 'GOT_DSIZE':
                sock.sendall(dataPkl)
                response = sock.recv(16).decode()
                if response != 'GOT_DATA':
                    active = False
                else:
                    sock.sendall(("DONE").encode())
                    print('images successfully sent to server')
                    active = False
                    write_log(config.log, config.name, ts)
                    
            else:
                print('ERROR: unexpected response:')
                print(response)
                active = False

    except Exception as e:
        print(traceback.format_exc())
        sock.close()

    finally:
        sock.close()

        
if __name__ == '__main__':
    
    parser = argparse.ArgumentParser()
    
    ## socket settings
    parser.add_argument('--host', type=str, default='127.0.0.1')
    parser.add_argument('--port', type=int, default=10001)
    
    ## path settings
    parser.add_argument('--input', type=str, default='test_images',
                       help='path to cinema database directory to send')
    parser.add_argument('--log', type=str, default='completed_steps.txt',
                       help='where to log completed timesteps')
    parser.add_argument('--name', type=str, default='test', 
                       help='unique identifier for dataset (used by log file)')
    
#     parser.add_argument('--timestep' type=int, default=0, 
#                        help='current timestep to process')
    
#     ## extractor settings
#     parser.add_argument('--phi', type=int, default=6)
#     parser.add_argument('--theta', type=str, default=6)
    
    ## parse cmd line args and start server
    config = parser.parse_args()
    main(config)