from .timepixconfig import TimepixConfig
import xml.etree.ElementTree as et
import zipfile
import numpy as np
class SophyConfig(TimepixConfig):

    def __init__(self,filename):        
        self._dac_codes = {'Ibias_Preamp_ON' : 1,
                            'Ibias_Preamp_OFF' : 2,
                            'VPreamp_NCAS' : 3,
                            'Ibias_Ikrum' : 4,
                            'Vfbk' : 5,
                            'Vthreshold_fine' : 6,
                            'Vthreshold_coarse' : 7,
                            'Ibias_DiscS1_ON' : 8,
                            'Ibias_DiscS1_OFF' : 9,
                            'Ibias_DiscS2_ON' : 10,
                            'Ibias_DiscS2_OFF' : 11,
                            'Ibias_PixelDAC' : 12,
                            'Ibias_TPbufferIn' : 13,
                            'Ibias_TPbufferOut' : 14,
                            'VTP_coarse' : 15,
                            'VTP_fine' : 16,
                            'Ibias_CP_PLL' : 17,
                            'PLL_Vcntrl' : 18,}

        self._dac_values = {'Ibias_Preamp_ON' : 128,
                            'Ibias_Preamp_OFF' : 8,
                            'VPreamp_NCAS' : 128,
                            'Ibias_Ikrum' : 10,
                            'Vfbk' : 128,
                            'Vthreshold_fine' : 150,
                            'Vthreshold_coarse' : 6,
                            'Ibias_DiscS1_ON' : 128,
                            'Ibias_DiscS1_OFF' : 8,
                            'Ibias_DiscS2_ON' : 128,
                            'Ibias_DiscS2_OFF' : 8,
                            'Ibias_PixelDAC' : 150,
                            'Ibias_TPbufferIn' : 128,
                            'Ibias_TPbufferOut' : 128,
                            'VTP_coarse' : 128,
                            'VTP_fine' : 256,
                            'Ibias_CP_PLL' : 128,
                            'PLL_Vcntrl' : 128,}
        self.loadFile(filename)
    def loadFile(self,filename):
        spx = zipfile.ZipFile(filename)
        names = spx.namelist()
        xml_string = spx.read(names[0])

        self.parseDAC(xml_string)

        self.parsePixelConfig(spx,names[-3:])



    
    def parseDAC(self,xmlstring):
        root = et.fromstring(xmlstring)
        dac_setting = root.findall(".//entry[@class='sophy.medipix.SPMPXDACCollection']")
        dac_setting = dac_setting[0][0]

        for element in dac_setting.findall(".//element[@class='java.util.Map.Entry']"):
            key=element.find('key')
            
            entry=element.find('entry')
            data = entry.find('data')
            dac_key = key.items()[-1][-1]
            dac_value = int(data.items()[-1][-1])

            self._dac_values[dac_key]= dac_value


    def dacCodes(self):
        dac_codes = []
        for key,value in self._dac_values.items():
            code = self._dac_codes[key]
            dac_codes.append((code,value))
        return dac_codes


    def parsePixelConfig(self,zip_file,file_names):
        #First is mask
        buffer = zip_file.read(file_names[0])
        self._mask = np.frombuffer(buffer[27:],dtype=np.uint16).reshape(256,256)
        buffer = zip_file.read(file_names[1])
        self._test = np.frombuffer(buffer[27:],dtype=np.uint16).reshape(256,256)
        buffer = zip_file.read(file_names[2])
        self._thresh = np.frombuffer(buffer[27:],dtype=np.uint16).reshape(256,256)
    
    def maskPixels(self):
        """Returns mask pixels"""
        return self._mask//256
    
    def testPixels(self):
        """Returns test pixels"""
        return self._test
    
    def thresholdPixels(self):
        """Returns threshold pixels"""
        return self._thresh*16//4096



def main():
    import matplotlib.pyplot as plt
    spx = SophyConfig('/Users/alrefaie/Documents/repos/libtimepix/lib/pymepix/config/W0028_H06_50V.spx')
    print(spx.dacCodes())
    # plt.matshow(spx.maskPixels()[::-1,:])
    # plt.show()
    # plt.matshow(spx.thresholdPixels()[::-1,:])
    # plt.show()  
    print(spx.maskPixels().max())
    thresh = spx.thresholdPixels()
    print('MAX',np.max(thresh))
    print('MEAN',np.mean(thresh))
    print('STDDEV',np.std(thresh))

    
    # plt.hist(thresh.flatten(),bins=16,range=[0,15])
    # plt.show()

if __name__=="__main__":
    main()
#dac_setting = e.findall(".//entry[@class='sophy.medipix.SPMPXDACCollection']")
#dac_setting = dac_setting[0]
#dac_setting = dac_setting[0]
# In [68]: for element in dac_setting.findall(".//element[@class='java.util.Map.Entry']"):
#     ...:     key=element.find('key')
#     ...:
#     ...:     entry=element.find('entry')
#     ...:     data = entry.find('data')
#     ...:     print(key.items()[-1][-1],data.items()[-1][-1])