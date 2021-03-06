"""
Unit test for DataLoader.Loader
"""
#  Copyright (c): Wenyi Tang 2017-2019.
#  Author: Wenyi Tang
#  Email: wenyi.tang@intel.com
#  Update Date: 2019/4/3 下午8:28

import os

if not os.getcwd().endswith('UTest'):
  os.chdir('UTest')
from VSR.DataLoader.Loader import *
from VSR.DataLoader.Dataset import *
from VSR.Util.ImageProcess import *
from VSR.Framework.Callbacks import _viz_flow

DATASETS = load_datasets('./data/fake_datasets.yml')


def test_basicloader_iter():
  dut = DATASETS['NORMAL']
  config = Config(batch=16, scale=4, depth=1, steps_per_epoch=200,
                  convert_to='RGB', crop='random')
  config.patch_size = 48
  r = BasicLoader(dut, 'train', config, True)
  it = r.make_one_shot_iterator('8GB')
  for hr, lr, name, _ in it:
    print(name, flush=True)
  it = r.make_one_shot_iterator('8GB')
  for hr, lr, name, _ in it:
    print(name, flush=True)


def test_quickloader_iter():
  dut = DATASETS['NORMAL']
  config = Config(batch=16, scale=4, depth=1, steps_per_epoch=200,
                  convert_to='RGB', crop='random')
  config.patch_size = 48
  r = QuickLoader(dut, 'train', config, True, n_threads=8)
  it = r.make_one_shot_iterator('8GB')
  for hr, lr, name, _ in it:
    print(name, flush=True)
  it = r.make_one_shot_iterator('8GB')
  for hr, lr, name, _ in it:
    print(name, flush=True)


def test_read_flow():
  dut = DATASETS['FLOW']
  config = Config(batch=8, scale=1, depth=2, patch_size=256,
                  steps_per_epoch=100, convert_to='RGB', crop='random')
  loader = QuickLoader(dut, 'train', config, True, n_threads=8)
  r = loader.make_one_shot_iterator('1GB', shuffle=True)
  loader.prefetch('1GB')
  list(r)
  r = loader.make_one_shot_iterator('8GB', shuffle=True)
  img, flow, name, _ = list(r)[0]

  ref0 = img[0, 0, ...]
  ref1 = img[0, 1, ...]
  u = flow[0, 0, ..., 0]
  v = flow[0, 0, ..., 1]
  # array_to_img(ref0, 'RGB').show()
  # array_to_img(ref1, 'RGB').show()
  # array_to_img(_viz_flow(u, v), 'RGB').show()


def test_read_pair():
  dut = DATASETS['PAIR']
  config = Config(batch=4, scale=1, depth=1, patch_size=64,
                  steps_per_epoch=10, convert_to='RGB', crop='random')
  loader = QuickLoader(dut, 'train', config, True, n_threads=8)
  r = loader.make_one_shot_iterator('1GB', shuffle=True)
  loader.prefetch('1GB')
  list(r)
  r = loader.make_one_shot_iterator('8GB', shuffle=True)
  for hr, pair, name, _ in r:
    assert np.all(hr == pair)


def test_cifar_loader():
  from tqdm import tqdm
  dut = DATASETS['NUMPY']
  config = Config(batch=8, scale=4, depth=1, patch_size=32,
                  steps_per_epoch=100, convert_to='RGB')
  loader = BasicLoader(dut, 'train', config, False)
  r = loader.make_one_shot_iterator()
  list(tqdm(r))


def test_crop_center():
  dut = DATASETS['NORMAL']
  config = Config(batch=1, scale=1, depth=1, patch_size=32, crop='center')
  np.random.seed(1)
  loader = QuickLoader(dut, 'test', config, False, n_threads=8)
  ref = QuickLoader(dut, 'test', config, False, n_threads=8, crop='not')
  for t, r in zip(loader.make_one_shot_iterator(),
                  ref.make_one_shot_iterator()):
    h, w = r[0].shape[1:3]
    ph, pw = t[0].shape[1:3]
    center = r[0][:, (h - ph) // 2:(h - ph) // 2 + ph,
             (w - pw) // 2:(w - pw) // 2 + pw, :]
    assert np.all(t[0] == center)


def test_crop_stride():
  dut = DATASETS['NORMAL']
  config = Config(batch=1, scale=1, depth=1, patch_size=32, crop='stride',
                  steps_per_epoch=999)
  np.random.seed(1)
  loader = QuickLoader(dut, 'test', config, False, n_threads=8)
  ref = QuickLoader(dut, 'test', config, False, n_threads=8, crop='not')
  ref = list(ref.make_one_shot_iterator())[0][0]
  patches = [t[0] for t in loader.make_one_shot_iterator()]
  patches = np.concatenate(patches)
  shape = patches.shape
  rows = ref.shape[1] // 32
  cols = ref.shape[2] // 32
  assert rows * cols == shape[0]
  re = patches.reshape([rows, cols, *shape[1:]])
  re = re.transpose([0, 2, 1, 3, 4])
  re = re.reshape([shape[1] * rows, shape[2] * cols, shape[3]])
  assert np.all(ref[0, :re.shape[0], :re.shape[1], :] == re)


def test_video_raw():
  dut = DATASETS['RAW']
  config = Config(batch=1, scale=2, depth=3, patch_size=32)
  ld1 = QuickLoader(dut, 'train', config)
  ld2 = QuickLoader(dut, 'val', config)
  ld3 = QuickLoader(dut, 'test', config)
  assert list(ld1.make_one_shot_iterator()) != []
  assert list(ld2.make_one_shot_iterator()) != []
  assert list(ld3.make_one_shot_iterator()) != []


def test_video_pair():
  dut = DATASETS['VIDEOPAIR']
  config = Config(batch=1, scale=2, depth=3, patch_size=32)
  ld1 = QuickLoader(dut, 'train', config)
  ld2 = QuickLoader(dut, 'val', config)
  ld3 = QuickLoader(dut, 'test', config)
  assert list(ld1.make_one_shot_iterator()) != []
  assert list(ld2.make_one_shot_iterator()) != []
  assert list(ld3.make_one_shot_iterator()) != []


def test_seq_loader():
  dut = DATASETS['NORMAL']
  config = Config(batch=1, scale=4, depth=1, convert_to='RGB', crop='random')
  config.patch_size = 48
  ld = SequentialLoader(dut, 'train', config, split=7)
  assert len(list(ld.make_one_shot_iterator())) == 7
