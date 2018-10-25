import numpy as np


class TimepixCentroid(object):
    
    def __init__(self):
        pass
    


    def centroid(self,x,y,tof,tot,tot_filter):
        clust_count = 0

        highest_tot = np.where(tot_filter)

        label = np.ndarray(x.shape,dtype=np.int)

        label[...]=-1











def read_timepix_data(f):
    shot = None
    x = None
    y = None
    tof = None
    tot = None

    while True:

        try:
            _shot = np.load(f)
            _x = np.load(f)
            _y = np.load(f)
            _tof = np.load(f)
            _tot = np.load(f)

            if shot is None:
                shot = _shot
                x = _x
                y = _y
                tof = _tof
                tot = _tot
            else:
                shot = np.append(shot,_shot)
                x = np.append(x,_x)
                y = np.append(y,_y)
                tof = np.append(tof,_tof)
                tot = np.append(tot,_tot)
        except:
            pass
        
        return shot,x,y,tof,tot


def main():
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d import Axes3D
    from sklearn.cluster import DBSCAN
    from sklearn import metrics
    with open('/Users/alrefaie/Documents/repos/libtimepix/lib/pymepix/processing/Lenscan_-80020181024-143826.dat','rb') as f:
        shot,x,y,tof,tot = read_timepix_data(f)
        print(tot)

        evt_filt =  tof > 0#(tof_us > 1.6)# & (tof_us < 2.1) & ((tot_ns) > 300)
        tw = open('/Users/alrefaie/Documents/repos/libtimepix/lib/pymepix/processing/timewalkCorrection.csv','r')
        timewalk = np.loadtxt(tw,dtype=float,delimiter=',')[:,1]
        print(timewalk)
        tw.close()

        raw_tot = tot//25
        correction = timewalk[raw_tot]
        print(correction)
        

        tof += correction*4.5E-7

        tof_us = tof*1E6
        tot_ns = tot.astype(np.float)
        evt_filt =   (tof_us > 1.75) & (tof_us < 2.1) 
        plt.hist2d(tof[evt_filt],tot[evt_filt],bins=100)
        plt.show()
        # tof_norm = tof / np.linalg.norm(tof)
        # tot_norm = tot/np.linalg.norm(tot.astype(float))
        # #print()
        # #generate
        # X = np.vstack((x,y,tof_norm)).transpose()

        # db = DBSCAN(eps=1, min_samples=2).fit(X)
        # labels = db.labels_
        # print(X.shape)
        # print(X)
        # print(labels)
        # print(labels.min(),labels.max())
        # n_clusters_ = len(set(labels)) - (1 if -1 in labels else 0)
        # print(n_clusters_)
        # shot_avail = np.unique(shot)
        # print(np.unique(labels))

        # fig = plt.figure()
        # ax = fig.add_subplot(111, projection='3d')
        # tof_us = tof*1E6
        # tot_ns = tot.astype(np.float)
        # evt_filt =   (tof_us > 1.75) & (tof_us < 2.1) 
        # # print(np.where(evt_filt))
        # p = ax.scatter(x[evt_filt], y[evt_filt], zs=tof_us[evt_filt], s=6, c=tot_ns[evt_filt], depthshade=True, cmap='hot')
        # plt.colorbar(p)
        # plt.show()


if __name__=="__main__":
    main()
