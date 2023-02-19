from tqdm import tqdm

from pymepix.processing.rawfilesampler import RawFileSampler

class ProgressBar(tqdm):
    gui_bar_fun = None

    def update_to(self, progress):
        self.gui_bar_fun(self.n)
        return self.update(progress - self.n)


def run_post_processing(input_file_name, output_file, number_processes, timewalk_file, cent_timewalk_file, progress_callback,
                        clustering_args={}, dbscan_clustering=True, **kwargs):
    with ProgressBar(total=1.0, dynamic_ncols=True) as progress_bar:
        progress_bar.gui_bar_fun = progress_callback
        file_sampler = RawFileSampler(input_file_name, output_file, number_processes, timewalk_file, cent_timewalk_file,
                                      progress_bar.update_to, clustering_args, dbscan_clustering, **kwargs)
        file_sampler.run()
