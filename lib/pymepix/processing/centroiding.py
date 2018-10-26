import numpy as np
import traceback

class TimepixCentroid(object):
    
    def __init__(self,input_queue,output_queue = None,file_queue=None):
        self._input_queue = input_queue
        self._output_queue = output_queue
        self._file_queue = file_queue

    
    def run(self):
        while True:
            try:
                # get a new message
                packet = self._input_queue.get()
                # this is the 'TERM' signal
                if packet is None:
                    break
                    # if self._output_queue is not None:
                    #     self._output_queue.put(None)
                    #     break

                # data = packet[0]
                # longtime = packet[1]
                #print('GOT DATA')
                blob_data = self.compute_blob(*packet)

                if blob_data is not None 
                    #print('EVENT FOUND')
                    if self._output_queue is not None:
                        self._output_queue.put(blob_data)

                    if self._file_queue is not None:
                        self._file_queue.put(('WRITEBLOB',blob_data))

        
            except Exception as e:
                print (str(e))
                traceback.print_exc()
                break            


    def compute_blob(self,shot,x,y,tof,tot):
        labels = self.find_cluster(shot,x,y,tof,tot,epsilon=2,min_samples=5)
        if labels[labels!=0].size == 0:
            return None
        else:
            return self.cluster_properties(shot,x,y,tof,tot,labels)





    def moments_com(self,X,Y,tot):

        total = tot.sum()
        x_bar = (X*tot).sum()/total
        y_bar = (Y*tot).sum()/total
        area = tot.size

        x_cm = X - x_bar
        y_cm = Y - y_bar
        coords = np.vstack([x_cm, y_cm])
        
        cov = np.cov(coords)
        evals, evecs = np.linalg.eig(cov)

        return x_bar,y_bar,area,total,evals,evecs.flatten()

    def find_cluster(self,shot,x,y,tof,tot,epsilon=2,min_samples=2):
        from sklearn.cluster import DBSCAN
        
        tof_eps = 81920*(25./4096)*1E-9

        tof_scale = epsilon/tof_eps
        X = np.vstack((shot*epsilon*1000,x,y,tof*tof_scale)).transpose()
        dist= DBSCAN(eps=epsilon, min_samples=min_samples,metric='euclidean').fit(X)
        labels = dist.labels_ + 1
        return labels

    def cluster_properties(self,shot,x,y,tof,tot,labels):
        label_iter = np.unique(labels[labels!=0])
        total_objects = label_iter.size


        #Prepare our output
        cluster_shot = np.ndarray(shape=(total_objects,),dtype=np.int)
        cluster_x = np.ndarray(shape=(total_objects,),dtype=np.float64)
        cluster_y = np.ndarray(shape=(total_objects,),dtype=np.float64)
        cluster_eig = np.ndarray(shape=(total_objects,2,),dtype=np.float64)
        cluster_vect = np.ndarray(shape=(total_objects,4,),dtype=np.float64)
        cluster_area = np.ndarray(shape=(total_objects,),dtype=np.float64)
        cluster_integral = np.ndarray(shape=(total_objects,),dtype=np.float64)
        cluster_tof = np.ndarray(shape=(total_objects,),dtype=np.float64)
        

        for idx in range(total_objects):


            obj_slice = (labels == label_iter[idx])
            obj_shot = shot[obj_slice]
            obj_x = x[obj_slice]
            obj_y = y[obj_slice]
            obj_tof = tof[obj_slice]
            obj_tot = tot[obj_slice]
            max_tot = np.argmax(obj_tot)

            cluster_tof[idx] = obj_tof[max_tot]

            x_bar,y_bar,area,integral,evals,evecs = self.moments_com(obj_x,obj_y,obj_tot)
            cluster_x[idx] = x_bar
            cluster_y[idx] = y_bar
            cluster_area[idx] = area
            cluster_integral[idx] = integral
            cluster_eig[idx]=evals
            cluster_vect[idx] = evecs
            cluster_shot[idx] = obj_shot[0]



            # moment = moments(obj_x,obj_y,obj_tot)
            # moments_com(obj_x,obj_y,obj_tot)
            #print(moment)
            # gauss = fitgaussian(obj_x,obj_y,obj_tot)
            # gh,gx,gy,gwx,gwy = gauss
            # cluster_h[idx] = gh
            # cluster_x[idx] = gx
            # cluster_y[idx] = gy
            # cluster_wx[idx] = gwx
            # cluster_wy[idx] = gwy
            # cluster_shot[idx] = obj_shot[0]

            #print('Moment ', moment,' Gaussian ',gauss)

        return cluster_shot,cluster_x,cluster_y,cluster_area,cluster_integral,cluster_eig,cluster_vect








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


def gaussian(height, center_x, center_y, width_x, width_y):
    """Returns a gaussian function with the given parameters"""
    width_x = float(width_x)
    width_y = float(width_y)
    return lambda x,y: height*np.exp(
                -(((center_x-x)/width_x)**2+((center_y-y)/width_y)**2)/2)

def moments(X,Y,tot):
    """Returns (height, x, y, width_x, width_y)
    the gaussian parameters of a 2D distribution by calculating its
    moments """
    total = tot.sum()
    x = (X*tot).sum()/total
    y = (Y*tot).sum()/total
    
    # x_filt = X == int(x)
    # y_filt = Y == int(y)
    # width_x = np.sqrt(((X[x_filt]-x)**2)*tot[x_filt]).sum()/tot[x_filt].sum()
    # width_y = np.sqrt(((Y[y_filt]-y)**2)*tot[y_filt]).sum()/tot[y_filt].sum()
    #print('YMIN',Y,tot)
    width_x = np.std(X)
    width_y = np.std(Y)
    height = tot.max()
    return height, x, y, width_x, width_y





def fitgaussian(x,y,tot):
    from scipy.optimize import leastsq
    """Returns (height, x, y, width_x, width_y)
    the gaussian parameters of a 2D distribution found by a fit"""
    params = moments(x,y,tot)
    errorfunction = lambda p: gaussian(*p)(x,y) - tot
    #print(params,len(x))
    p, success = leastsq(errorfunction, params)
    return p









def main():
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d import Axes3D
    from sklearn.cluster import DBSCAN
    from sklearn import metrics
    import sklearn
    import scipy
    import time
    with open('/Users/alrefaie/Documents/repos/libtimepix/lib/pymepix/processing/Lenscan_-80020181024-143826.dat','rb') as f:
    #with open('C:\\Users\\Bahamut\\Documents\\repos\\libtimepix\\lib\\pymepix\\processing\\Lenscan_-80020181024-143826.dat','rb') as f:
        shot,x,y,tof,tot = read_timepix_data(f)
        shot_avail = np.unique(shot)
        evt_filt = (shot >= 0 )# & (x > 146) & ( x < 158) & (y > 126) & (y < (136))# (shot < 10) #& (tot > 300) #(shot == shot_avail[2]) | (shot == shot_avail[1]) | (shot == shot_avail[0])

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

        label_time = time.time()

        labels = find_cluster(shot,x,y,tof,tot,epsilon=2,min_samples=5)
        label_time = time.time() - label_time

        moment_time = time.time()
        c_s,c_x,c_y,c_a,c_int,c_eig,c_vecs = cluster_properties(shot,x,y,tof,tot,labels)
        moment_time = time.time() - moment_time


        matrix = np.ndarray(shape=(256,256,),dtype=np.float)
        matrix[...]=0.0
        matrix[x,y] = tot
        
        # #matrix = np.ndarray(shape=(256,256,),dtype=np.float)



        plt.matshow(matrix,cmap='jet')
        fig = plt.gcf()
        ax = fig.gca()
        for idx in range(c_s.size):
            # fit = gaussian(c_tot[idx],c_x[idx],c_y[idx],c_wx[idx],c_wy[idx])
            # x_r = np.linspace(c_x[idx]-c_wx[idx]/2,c_x[idx]+c_wx[idx]/2,10)
            # y_r = np.linspace(c_y[idx]-c_wy[idx]/2,c_y[idx]+c_wy[idx]/2,10)
            # gridx,gridy = np.meshgrid(y_r,x_r)
            # print(x_r)
            # c_x[idx],c_y[idx],c_wx[idx],c_wy[idx]
            # plt.contour(gridx,gridy,fit(gridx,gridy), cmap=plt.cm.hot)
            # print(int(c_x[idx]),int(c_y[idx]))
            ax.add_artist(plt.Circle((c_y[idx],c_x[idx]),5,color='r',fill=False))
            
            # if idx ==0:
            #     break
        #ax = plt.gca()
        plt.show()

        num_triggers = np.unique(shot).size
        num_objects = np.unique(labels).size

        print('Time taken: Labelling: {} s Moments: {} s'.format(label_time,moment_time))
        print('Number of triggers {} , Avg label time: {} , number of objects: {} Avg moment time: {}'.format(num_triggers,label_time/num_triggers,num_objects,moment_time/num_objects))

        # cluster_shot,cluster_x,cluster_y,cluster_tof,cluster_tot,labels,new_tof = find_cluster(shot,x,y,tof,tot)

        # cluster_tof*=1E6
        # print(new_tof*1E6,tot)
        # # plt.hist2d(new_tof*1E6,tot,bins=100,cmap='hot',range=[[1.75,2],[0,4000]])
        # # plt.show()
        # # print('DISTANCE',dist)
        # # print('SHAPE',dist.shape)
        # # print(dist.max())
        # # print(tof_dist)
        # # print(tof_dist.shape)
        # # print(81920*(25./4096)*1E-9)
        # # quit()
        # # print(dist.max())
        # # print(np.mean(dist))
        
        # # # print(X.shape)
        # # # print(X)
        # # # print(labels)
        # # # print(labels.min(),labels.max())
        # # # n_clusters_ = len(set(labels)) - (1 if -1 in labels else 0)
        # # # print(n_clusters_)
        # # shot_avail = np.unique(shot)
        # # print(np.unique(labels))

        # fig = plt.figure()
        # ax = fig.add_subplot(221, projection='3d')
        # bx = fig.add_subplot(222, projection='3d')
        # cx = fig.add_subplot(223)
        # dx = fig.add_subplot(224)


        # # # tof_us = tof*1E6
        # # # tot_ns = tot.astype(np.float)
        # # # #evt_filt =   (tof_us > 1.75) & (tof_us < 2.1) 
        # # # # print(np.where(evt_filt))
        # tof_us = tof*1E6
        # new_tof_us = new_tof*1E6

        # tof_filt = (tof_us > 1.6) & (tof_us < 2.0)
        # new_tof_filt = (new_tof_us > 1.6) & (new_tof_us < 2.0)
        # p = ax.scatter(x[tof_filt], y[tof_filt], zs=tof_us[tof_filt], s=3, c=tot[tof_filt], depthshade=True, cmap="hot")
        # bx.scatter(x[new_tof_filt], y[new_tof_filt], zs=new_tof_us[new_tof_filt], s=3, c=tot[new_tof_filt], depthshade=True, cmap="hot")
        # cx.hist2d(tof_us[tof_filt],tot[tof_filt],bins=100,cmap='hot')
        # dx.hist2d(new_tof_us[new_tof_filt],tot[new_tof_filt],bins=100,cmap='hot')
        # ax.set_xlabel('x')
        # ax.set_ylabel('y')
        # ax.set_zlabel('tof')

        # bx.set_xlabel('x')
        # bx.set_ylabel('y')
        # bx.set_zlabel('tof')


        # cx.set_xlabel('TOF (us)')
        # cx.set_ylabel('TOT (ns)')

        # dx.set_xlabel('TOF (us)')
        # dx.set_ylabel('TOT (ns)')

        # #plt.colorbar(p)
        # plt.show()
        # plt.hist(new_tof*1E6,bins=500)
        # plt.show()

if __name__=="__main__":
    main()
