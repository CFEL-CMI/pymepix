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

def find_cluster(shot,x,y,tof,tot,epsilon=2,min_samples=2):
    from sklearn.cluster import DBSCAN
    import scipy.ndimage as nd
    tof_eps = 81920*(25./4096)*1E-9

    tof_scale = epsilon/tof_eps
    X = np.vstack((shot*epsilon*1000,x,y,tof*tof_scale)).transpose()
    dist= DBSCAN(eps=epsilon, min_samples=min_samples,metric='euclidean').fit(X)
    labels = dist.labels_ + 1
    label_index = np.unique(labels)
    print()

    # tot_max = nd.maximum_position(tot,labels=labels,index=label_index)
    # x_mean = nd.mean(x,labels=labels,index=label_index)
    # y_mean = nd.mean(tot,labels=labels,index=label_index)

    tot_max = np.array(nd.maximum_position(tot,labels=labels,index=label_index)).flatten()
    cluster_x = np.array(nd.mean(x,labels=labels,index=label_index)).flatten()
    cluster_y = np.array(nd.mean(y,labels=labels,index=label_index)).flatten()
    new_tof = np.copy(tof)
    cluster_tof = tof[tot_max]
    cluster_shot = shot[tot_max]
    clusters = nd.find_objects(labels)
    for cluster in clusters:
        ob = cluster[0]
        max_tot = np.argmax(tot[ob])
        tof_Val = tof[ob][max_tot]
        new_tof[ob] = tof_Val


    return cluster_shot,cluster_x,cluster_y,cluster_tof,tot[tot_max],label_index,new_tof







def main():
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d import Axes3D
    from sklearn.cluster import DBSCAN
    from sklearn import metrics
    import sklearn
    import scipy
    with open('C:\\Users\\Bahamut\\Documents\\repos\\libtimepix\\lib\\pymepix\\processing\\Lenscan_-80020181024-143826.dat','rb') as f:
        shot,x,y,tof,tot = read_timepix_data(f)
        shot_avail = np.unique(shot)
        evt_filt = (shot > 0) # (shot < 10) #& (tot > 300) #(shot == shot_avail[2]) | (shot == shot_avail[1]) | (shot == shot_avail[0])

        #~25 clusters
        shot = shot[evt_filt]
        x = x[evt_filt]
        y = y[evt_filt]
        tof = tof[evt_filt]
        tot = tot[evt_filt]

        # tw = open('/Users/alrefaie/Documents/repos/libtimepix/lib/pymepix/processing/timewalkCorrection.csv','r')
        # timewalk = np.loadtxt(tw,dtype=float,delimiter=',')[:,1]
        # print(timewalk)
        # tw.close()

        # raw_tot = tot//25
        # correction = timewalk[raw_tot]
        # print(correction)
        

        # tof += correction*4.5E-7

        # tof_us = tof*1E6
        # evt_filt =  (tof_us > 1.6)& (tof_us < 2.1)

        # # plt.hist2d(tof_us[evt_filt],tot[evt_filt],bins=100,cmap='hsv')
        # # plt.show()
        # # quit()

        # # #print()
        # # #generate

        # # db = DBSCAN(eps=6, min_samples=4,metric='euclidean').fit(X)
        # # labels = db.labels_

        # desired_epsilon = 2


        # tof_eps = 81920*(25./4096)*1E-9

        # tof_scale = desired_epsilon/tof_eps
        # X = np.vstack((shot*desired_epsilon*1000,x,y,tof*tof_scale)).transpose()
        # dist= DBSCAN(eps=desired_epsilon, min_samples=2,metric='euclidean').fit(X)
        # print(np.unique(dist.labels_))
        # labels = dist.labels_
        cluster_shot,cluster_x,cluster_y,cluster_tof,cluster_tot,labels,new_tof = find_cluster(shot,x,y,tof,tot)

        cluster_tof*=1E6
        print(new_tof*1E6,tot)
        plt.hist2d(new_tof*1E6,tot,bins=100,cmap='hot',range=[[1.75,2],[0,4000]])
        plt.show()
        # print('DISTANCE',dist)
        # print('SHAPE',dist.shape)
        # print(dist.max())
        # print(tof_dist)
        # print(tof_dist.shape)
        # print(81920*(25./4096)*1E-9)
        # quit()
        # print(dist.max())
        # print(np.mean(dist))
        
        # # print(X.shape)
        # # print(X)
        # # print(labels)
        # # print(labels.min(),labels.max())
        # # n_clusters_ = len(set(labels)) - (1 if -1 in labels else 0)
        # # print(n_clusters_)
        # shot_avail = np.unique(shot)
        # print(np.unique(labels))

        # fig = plt.figure()
        # ax = fig.add_subplot(111, projection='3d')
        # bx = fig.add_subplot(122, projection='3d')
        # # tof_us = tof*1E6
        # # tot_ns = tot.astype(np.float)
        # # #evt_filt =   (tof_us > 1.75) & (tof_us < 2.1) 
        # # # print(np.where(evt_filt))


        # p = ax.scatter(x, y, zs=new_tof, s=6, c=tot, depthshade=True, cmap="hot")
        # # bx.scatter(cluster_x, cluster_y, zs=cluster_tof, s=10, c=labels, depthshade=True, cmap="hsv")
        # plt.colorbar(p)
        # plt.show()
        plt.hist(new_tof*1E6,bins=500)
        plt.show()

if __name__=="__main__":
    main()
