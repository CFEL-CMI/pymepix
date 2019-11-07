##############################################################################
##
# This file is part of Pymepix
#
# https://arxiv.org/abs/1905.07999
#
#
# Pymepix is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Pymepix is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with Pymepix.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import numpy as np


def compute_timewalk(tof, tot, region):
    from scipy.optimize import curve_fit
    from scipy.stats import norm

    # Filter for the calibration region we are looking at
    region_filter = (tof >= region[0]) & (tof <= region[1])
    tof_region = tof[region_filter] * 1E9
    tot_region = tot[region_filter]

    # Find maximum tot
    percent_vals = len(tof_region) // 100
    # Find maximum tot
    # max_tot_index = np.argmax(tot_region)
    center_tof = np.mean(tof_region[np.argsort(-tot_region)[0:percent_vals]])
    print(center_tof)

    # This is our 'correct' TOF
    # center_tof = tof_region[max_tot_index]
    # Compute the time difference
    time_diff = tof_region - center_tof

    time_walk_bin = int((np.max(tof_region) - np.min(tof_region)) / 1.562)
    tot_bins = int(np.max(tot_region) - np.min(tot_region)) / 25
    print(time_walk_bin, tot_bins)
    # Sample on a 2d histogram
    time_hist, tot_bins, time_bins = np.histogram2d(tot_region, time_diff, bins=[tot_bins, time_walk_bin])
    bin_edges = time_bins
    bin_centres = (bin_edges[:-1] + bin_edges[1:]) / 2
    last_mean = 99999
    tot_points = []
    time_walk_points = []

    total_bins = time_hist.shape[0]
    print(total_bins)
    # print(bin_centres)
    # For each bin
    for b in range(0, total_bins):
        # print(b)
        current_tot = time_hist[b]

        #         plt.plot(bin_centres,current_tot)
        #         plt.show()
        #         center_guess = np.sum(current_tot*bin_centres)/np.sum(current_tot)
        #         sigma_guess = np.sqrt(np.sum(current_tot*np.square(bin_centres - center_guess))/(np.sum(current_tot)-1))

        #         print(center_guess,sigma_guess)
        #         if b==4:
        #             return
        #         continue
        # # Define model function to be used to fit to the data above:
        def gauss(x, *p):
            A, mu, sigma = p
            return A * np.exp(-(x - mu) ** 2 / (2. * sigma ** 2))

        # Fit sampled tot region with gaussian

        A_guess = np.max(current_tot)
        center_guess = np.sum(current_tot * bin_centres) / np.sum(current_tot)
        sigma_guess = np.sqrt(np.sum(current_tot * np.square(bin_centres - center_guess)) / (np.sum(current_tot) - 1))
        # print('CENTER ',center_guess)
        # print('SIGMA ',sigma_guess)
        # # p0 is the initial guess for the fitting coefficients (A, mu and sigma above)
        p0 = [np.max(current_tot), center_guess, sigma_guess]
        # print(p0)
        try:

            coeff, var_matrix = curve_fit(gauss, bin_centres, current_tot, p0=p0)
        except:
            print("Counldn't do it")
            continue
        print(tot_bins[b], coeff[1])
        if np.isnan(coeff[2]):
            continue
        if (coeff[1] < 1.525):
            break
        # print(coeff[1],coeff[2])
        #         if(coeff[1]>last_mean):
        #             continue
        #         last_mean = coeff[1]
        # # Get the fitted curve
        # hist_fit = gauss(bin_centres, *coeff)

        #         test = np.sum(current_tot)
        #         if(test <=0):
        #             continue
        #         mean = np.sum(current_tot*bin_centres)/np.sum(current_tot)
        #         if(mean < 0):
        #             break

        #         #Mean (coeff[1]) is the timewalk
        #         time_walk_points.append(mean)
        time_walk_points.append(coeff[1])
        tot_points.append(tot_bins[b])
        # print(tot_points)
        # no point correcting further than this since its below 1.5625 ns

    return np.array(tot_points), np.array(time_walk_points)


def compute_timewalk_lookup(tof, tot, region):
    from scipy import interpolate
    tot_points, time_walk_points = compute_timewalk(tof, tot, region)
    tot_lookup_table = np.zeros(0x3FF, dtype=np.float32)
    tot_lookup_table[tot_points.astype(int) // 25] = time_walk_points[...]
    f = interpolate.interp1d(np.array(tot_points), np.array(time_walk_points))
    for x in range(0x3FF):
        try:
            val = f((x + 1) * 25)
            tot_lookup_table[x] = val
        except:
            pass
    return tot_lookup_table * 1E-9
