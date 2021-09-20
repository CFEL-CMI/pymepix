from tqdm import tqdm

from pymepix.processing.rawfilesampler import RawFileSampler

class ProgressBar(tqdm):

    def update_to(self, progress):
        return self.update(progress - self.n)


def run_post_processing(input_file_name, output_file, number_processes, timewalk_file, cent_timewalk_file):
    with ProgressBar(total=1.0, dynamic_ncols=True) as progress_bar:
        file_sampler = RawFileSampler(input_file_name, output_file, number_processes, timewalk_file, cent_timewalk_file, progress_bar.update_to)
        file_sampler.run()