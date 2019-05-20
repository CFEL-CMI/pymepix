.. _examples:

========
Examples
========


Starting timepix and polling data::

    import pymepix
    from pymepix.processing import MessageType
    import numpy as np

    #Connect to SPIDR
    timepix = pymepix.Pymepix(('192.168.1.10',50000))

    #Set bias voltage
    timepix.biasVoltage = 50

    #Set pixel masks
    timepix[0].pixelThreshold = np.zeros(shape=(256,256),dtype=np.uint8)
    timepix[0].pixelMask = np.zeros(shape=(256,256),dtype=np.uint8)
    timepix[0].uploadPixels()

    #Start acquisition
    timepix.start()

    while True:
        try:
            #Poll
            data_type,data = timepix.poll()
        except pymepix.PollBufferEmpty:
            #If empty then just loop
            continue

        #Handle Raw
        if data_type is MessageType.RawData:

            print('UDP PACKET')

            packets,longtime = data

            print('Packet ',packets)
            print('Time', longtime)

        #Handle Pixels
        elif data_type is MessageType.PixelData:

            print('I GOT PIXELS!!!!')

            x,y,toa,tot = data

            print('x',x)
            print('y', y)
            print('toa', toa)
            print('tot',tot)

    #Stop
    timepix.stop()

Using callbacks to acquire::

    import pymepix
    from pymepix.processing import MessageType
    import numpy as np
    import time

    #Connect to SPIDR
    timepix = pymepix.Pymepix(('192.168.1.10',50000))

    #Set bias voltage
    timepix.biasVoltage = 50

    #Set pixel masks
    timepix[0].pixelThreshold = np.zeros(shape=(256,256),dtype=np.uint8)
    timepix[0].pixelMask = np.zeros(shape=(256,256),dtype=np.uint8)
    timepix[0].uploadPixels()

    #Define callback
    def my_callback(data_type,data):
        print('MY CALLBACK!!!!')
        #Handle Raw
        if data_type is MessageType.RawData:

            print('UDP PACKET')

            packets,longtime = data

            print('Packet ',packets)
            print('Time', longtime)

        #Handle Pixels
        elif data_type is MessageType.PixelData:

            print('I GOT PIXELS!!!!')

            x,y,toa,tot = data

            print('x',x)
            print('y', y)
            print('toa', toa)
            print('tot',tot)

    #Set callback
    timepix.dataCallback = my_callback

    #Start acquisition
    timepix.start()
    #Wait 5 seconds
    time.sleep(5.0)
    #Stop
    timepix.stop()