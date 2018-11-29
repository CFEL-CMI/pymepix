"""Useful functions to store data"""
import numpy as np

def open_output_file(filename,ext):
    import os,logging
    index = 0     
    file_format = '{}_{:06d}.{}'           
    raw_filename = file_format.format(filename,index,ext)
    while os.path.isfile(raw_filename):
        index+=1 
        raw_filename = file_format.format(filename,index,ext)
    logging.info('Opening output file {}'.format(filename))

    return open(raw_filename,'wb')

def store_raw(f,data):
    raw,longtime = data
    f.write(raw.tostring())

def store_toa(f,data):
    x,y,toa,tot = data

    np.save(f,x)
    np.save(f,y)
    np.save(f,toa)
    np.save(f,tot)

def store_tof(f,data):
    counter,x,y,tof,tot = data

    np.save(f,counter)  
    np.save(f,x) 
    np.save(f,y) 
    np.save(f,tof) 
    np.save(f,tot)  

