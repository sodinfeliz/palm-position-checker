from __future__ import absolute_import

import cv2
import numpy as np
import shutil
from pathlib import Path 
from progress.bar import Bar
from skimage.util.shape import view_as_windows


def _split_image(img,
                 crop_size,
                 overlap=0.0,
                 out_format='',
                 out_folder_name='',
                 out_dir_path=Path.cwd(),
                 prefix='_'):

    assert out_format in ['tif', 'png']
    assert (0 <= overlap < 1), 'Overlap range must in [0, 1).'
    if not all(l >= crop_size for l in img.shape[:2]):
        raise AttributeError(f'Dimension size must greater than crop size {crop_size}')

    # re-build directory
    path = Path(out_dir_path).joinpath(out_folder_name)
    shutil.rmtree(path, ignore_errors=True)
    path.mkdir(parents=True, exist_ok=True)

    stride = int(crop_size * (1 - overlap))
    crop_block = (crop_size,)*2 + ((img.shape[-1],) if img.ndim == 3 else tuple())
    im_tiles = view_as_windows(img, crop_block, stride)
    im_tiles = im_tiles.reshape(-1, *crop_block)

    with Bar('Processing', fill='>', max=len(im_tiles), suffix='%(percent).1f%% - %(eta)ds') as bar:
        for idx, tile in enumerate(im_tiles):
            out_path = path.joinpath(f'{prefix}{idx}.{out_format}')
            cv2.imwrite(str(out_path), tile)
            bar.next()
    

def _coverage_filter(path: Path, ratio_lower=None, ratio_upper=None):
    """ Removing the mask image with coverage less than 'ratio_lower' """
    def coverage_ratio(img):
        if np.amax(img) == 0:
            return 0

        area = img.shape[0] * img.shape[1]
        ratio = np.count_nonzero(img)/area
        return ratio

    for p in Path(path).glob('*.png'):
        gray_im = cv2.imread(str(p), 0)
        r = coverage_ratio(gray_im)
        if ratio_lower is not None and r < ratio_lower:
            p.unlink()
        elif ratio_upper is not None and r > ratio_upper:
            p.unlink()


def _correspond_filter(image_folder: Path, label_folder: Path):
    for path in image_folder.glob('*.tif'):
        if not label_folder.joinpath(f'{path.stem}.png').exists():
            path.unlink()


def save_train_data(im_path: Path, label_path: Path, crop_size, ratio, filename=None):
    prefix = im_path.stem[:-5] if filename is None else filename
    data_dir = im_path.parent

    im = cv2.imread(str(im_path))
    label_im_vision = cv2.imread(str(label_path), 0)
    label_im = label_im_vision.astype('float') / 255.

    # splitting the image into subtiles by 'crop_size' and 'ratio'
    _split_image(im, crop_size=crop_size, overlap=ratio, out_format='tif',
                out_folder_name='images', out_dir_path=data_dir, prefix=f'{prefix}_')
    _split_image(label_im, crop_size=crop_size, overlap=ratio, out_format='png',
                out_folder_name='labels', out_dir_path=data_dir, prefix=f'{prefix}_')
    _split_image(label_im_vision, crop_size=crop_size, overlap=ratio, out_format='png',
                out_folder_name='labels_vision', out_dir_path=data_dir, prefix=f'{prefix}_')

    # removing the image by their coverage
    _coverage_filter(data_dir.joinpath('labels'), ratio_lower=0.02, ratio_upper=1)
    _coverage_filter(data_dir.joinpath('labels_vision'), ratio_lower=0.02, ratio_upper=1)
    _correspond_filter(data_dir.joinpath('images'), data_dir.joinpath('labels'))

