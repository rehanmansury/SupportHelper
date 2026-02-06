from dataclasses import dataclass
from typing import Optional

from PIL import Image, ImageFilter, ImageOps
import pytesseract


@dataclass
class OCRPreprocessOptions:
    """Tunable, offline-safe preprocessing options for OCR.

    - upscale: 1.0 (no scale), 1.5, 2.0 ... Use >1.0 to help small/blurred text.
    - denoise_median: Median filter to reduce speckle noise prior to sharpening.
    - grayscale: Convert to grayscale (recommended before thresholding).
    - auto_contrast: Stretch histogram for global contrast.
    - equalize: Histogram equalization for adaptive contrast.
    - sharpen: Apply unsharp mask for crisper edges.
    - sharpen_percent: Unsharp mask strength (0-300 typical).
    - threshold: Fixed binarization using threshold_value.
    - threshold_value: 0-255 cutoff for fixed threshold.
    - strong_threshold: Otsu-like auto threshold after enhancements.
    """
    upscale: float = 1.0
    denoise_median: bool = False
    grayscale: bool = False
    auto_contrast: bool = False
    equalize: bool = False
    sharpen: bool = False
    sharpen_percent: int = 150
    threshold: bool = False
    threshold_value: int = 160
    strong_threshold: bool = False


def _otsu_threshold(gray: Image.Image) -> int:
    """Compute an Otsu-like threshold level for a grayscale image."""
    hist = gray.histogram()
    total = sum(hist)
    sumB = 0
    wB = 0
    maximum = 0
    sum1 = sum(i * hist[i] for i in range(256))
    level = 160  # fallback
    for i in range(256):
        wB += hist[i]
        if wB == 0:
            continue
        wF = total - wB
        if wF == 0:
            break
        sumB += i * hist[i]
        mB = sumB / wB
        mF = (sum1 - sumB) / wF
        between = wB * wF * (mB - mF) * (mB - mF)
        if between >= maximum:
            level = i
            maximum = between
    return int(level)


def preprocess_image(img: Image.Image, opt: Optional[OCRPreprocessOptions] = None) -> Image.Image:
    """Apply a robust chain of offline preprocessing operations to improve OCR.

    The pipeline is conservative by default and configurable via `opt`.
    """
    if opt is None:
        opt = OCRPreprocessOptions()

    out = img

    # 1) Upscale early to help small or slightly blurred text
    try:
        if opt.upscale and opt.upscale > 1.0:
            w, h = out.size
            out = out.resize((int(w * opt.upscale), int(h * opt.upscale)), Image.LANCZOS)
    except Exception:
        pass

    # 2) Denoise before sharpening/thresholding
    if opt.denoise_median:
        try:
            out = out.filter(ImageFilter.MedianFilter(size=3))
        except Exception:
            pass

    # 3) Convert to grayscale if requested or if later steps need it
    if opt.grayscale:
        out = out.convert('L')

    # 4) Global/adaptive contrast improvements
    if opt.auto_contrast:
        try:
            out = ImageOps.autocontrast(out)
        except Exception:
            pass
    if opt.equalize:
        try:
            out = ImageOps.equalize(out)
        except Exception:
            pass

    # 5) Sharpen edges using unsharp mask (good after denoise/contrast)
    if opt.sharpen:
        try:
            amt = max(0, min(300, int(opt.sharpen_percent)))
            out = out.filter(ImageFilter.UnsharpMask(radius=1.5, percent=amt, threshold=2))
        except Exception:
            pass

    # 6) Thresholding (fixed or strong/Otsu-like)
    if opt.threshold:
        gray = out.convert('L')
        thr = int(opt.threshold_value)
        out = gray.point(lambda p: 255 if p > thr else 0)

    if opt.strong_threshold:
        gray = out.convert('L')
        try:
            thr = _otsu_threshold(gray)
        except Exception:
            thr = 160
        out = gray.point(lambda p: 255 if p > thr else 0)

    return out


def ocr_image(img: Image.Image, lang: str = 'eng', opt: Optional[OCRPreprocessOptions] = None) -> str:
    """Run offline OCR using Tesseract with optional preprocessing.

    - Ensure Tesseract is locally installed.
    - The caller may set `pytesseract.pytesseract.tesseract_cmd` externally if needed.
    - `lang` supports combinations (e.g., 'eng+hin') if language data is installed locally.
    """
    pre = preprocess_image(img, opt)
    return pytesseract.image_to_string(pre, lang=lang)
