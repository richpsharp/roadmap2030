import logging
import sys
from ecoshard import taskgraph
import os
import geopandas as gpd
from ecoshard import geoprocessing

logging.basicConfig(
    level=logging.DEBUG,
    stream=sys.stdout,
    format=(
        '%(asctime)s (%(relativeCreated)d) %(levelname)s %(name)s'
        ' [%(pathname)s.%(funcName)s:%(lineno)d] %(message)s'))
LOGGER = logging.getLogger(__name__)
logging.getLogger('matplotlib.font_manager').setLevel(logging.ERROR)
logging.getLogger('PIL').setLevel(logging.ERROR)
logging.getLogger('ecoshard.taskgraph').setLevel(logging.INFO)
logging.getLogger('fiona').setLevel(logging.WARN)


BASE_RASTER_LOOKUP = {
    'sed_export_marine': r"D:\repositories\roadmap2030\data\ndv_0.0_sed_export_marineESA_2020-1992_change_md5_0ab0cf.tif",
    'cv_habitat_value_mar': r"D:\repositories\roadmap2030\data\ndv_0.0_cv_habitat_value_marESA2020-1992_change_md5_1643a7.tif",
    'n_export_marine': r"D:\repositories\roadmap2030\data\ndv_0.0_n_export_marineESA_2020-1992_change_val_md5_18a2b3.tif",
    'realized_pollination_on_ag_mar': r"D:\repositories\roadmap2030\data\ndv_0.0_realized_pollination_on_ag_marESA_2020-1992_fullchange_md5_8e63e2.tif",
    'sed_deposition_marine': r"D:\repositories\roadmap2030\data\ndv_0.0_sed_deposition_marineESA_2020-1992_change_md5_d23c49.tif",
}


VECTOR_PATH_LOOKUP = {
    'non-arpa': r"D:\repositories\roadmap2030\data\Non-ARPA\non-ARPA.shp",
    'arpa': r"D:\repositories\roadmap2030\data\arpa\ucs_ARPA.shp"
}

OUTPUT_DIR = './results'
CLIPPED_DIR = os.path.join(OUTPUT_DIR, 'clipped')
for dirpath in [OUTPUT_DIR, CLIPPED_DIR]:
    os.makedirs(dirpath, exist_ok=True)


def create_subset(gdf, name, target_vector_path):
    LOGGER.info(f'creating subset of {name}')
    subset_gdf = gdf[gdf["Name"] == name]
    subset_gdf.to_file(target_vector_path, driver="GPKG")
    LOGGER.info(f'done with subset of {name}')


def clip_raster(base_raster_path, summary_vector_path, temp_clip_path):
    base_raster_info = geoprocessing.get_raster_info(base_raster_path)
    summary_vector_info = geoprocessing.get_vector_info(summary_vector_path)
    target_pixel_size = base_raster_info['pixel_size']
    base_vector_bb = summary_vector_info['bounding_box']

    target_bb = geoprocessing.transform_bounding_box(
        base_vector_bb, summary_vector_info['projection_wkt'],
        base_raster_info['projection_wkt'])

    geoprocessing.warp_raster(
        base_raster_path, target_pixel_size, temp_clip_path,
        'near', target_bb=target_bb, vector_mask_options={
            'mask_vector_path': summary_vector_path,
            'all_touched': True})


def main():
    """Entry point."""
    print(os.cpu_count())
    task_graph = taskgraph.TaskGraph(OUTPUT_DIR, os.cpu_count(), reporting_interval=10.0)
    for vector_id, vector_path in VECTOR_PATH_LOOKUP.items():
        LOGGER.info(f'processing {vector_id}')
        for raster_basename, raster_path in BASE_RASTER_LOOKUP.items():
            LOGGER.info(f'clipping {raster_basename} to {vector_id}')
            clipped_raster_path = os.path.join(
                CLIPPED_DIR, f'{vector_id}_{raster_basename}.tif')
            clipped_task = task_graph.add_task(
                func=clip_raster,
                args=(raster_path, vector_path, clipped_raster_path),
                ignore_path_list=[vector_path],
                target_path_list=[clipped_raster_path],
                task_name=f'clipping {raster_path} to {vector_path}')

    task_graph.join()
    print('all done!')


if __name__ == '__main__':
    main()
