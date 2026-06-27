import multiprocessing
import sys

# PyInstaller 打包后 Windows 上必须调用，否则 multiprocessing/uvicorn 可能异常退出。
multiprocessing.freeze_support()
