"""Flag detached faint ink for review; this does not certify an image as clean.

Run with image filenames, or --self-test. Requires Pillow and NumPy.
Never modify or publish the diagnostic pixels as a replacement diagram.
"""
import json
import sys

import numpy as np
from PIL import Image, ImageFilter


def faint_ink(image):
    image = image.convert('RGBA')
    pixels = np.asarray(image, dtype=np.float32)
    # Alpha alone misses opaque, almost-white marks in transparent images.
    rgb = 255 + (pixels[:, :, :3] - 255) * (pixels[:, :, 3:] / 255)
    ink = np.ceil(np.max(255 - rgb, axis=2)).clip(0, 255).astype('uint8')
    strong = Image.fromarray((ink >= 55).astype('uint8') * 255)
    strong = strong.resize((max(1, (image.width + 3) // 4), max(1, (image.height + 3) // 4)), Image.Resampling.BOX)
    strong = strong.point(lambda v: 255 if v else 0).filter(ImageFilter.MaxFilter(5)).resize(image.size, Image.Resampling.NEAREST)
    weak = (ink > 0) & (ink < 55) & (np.asarray(strong) == 0)
    ys, xs = np.nonzero(weak)
    if len(xs) >= 14 and len(set(xs // 5)) >= 6:
        return [len(xs), int(xs.max() - xs.min()), int(ys.max() - ys.min())]
    return None


if __name__ == '__main__':
    if sys.argv[1:] == ['--self-test']:
        image = Image.new('RGBA', (100, 50), (255, 255, 255, 0))
        assert faint_ink(image) is None
        image.paste((0, 0, 0, 255), (20, 20, 70, 25))
        assert faint_ink(image) is None
        image.paste((252, 252, 252, 255), (5, 40, 90, 43))
        assert faint_ink(image), 'Opaque near-white mark must not disappear into alpha'
        image.paste((0, 0, 0, 3), (5, 40, 90, 43))
        assert faint_ink(image), 'Nearly transparent black mark must also be detected'
        print('Faint-ink regression checks passed')
    else:
        for filename in sys.argv[1:]:
            with Image.open(filename) as image:
                result = faint_ink(image)
            if result:
                print(json.dumps({'file': filename, 'faintInk': result}))
