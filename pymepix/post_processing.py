from pymepix.processing.rawfilesampler import RawFileSampler

def run_post_processing(input_file_name, output_file, number_processes, timewalk_file, cent_timewalk_file, progress_callback=None):
    file_sampler = RawFileSampler(input_file_name, output_file, number_processes, timewalk_file, cent_timewalk_file, progress_callback)
    file_sampler.run()