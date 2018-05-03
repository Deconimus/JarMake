import os, shutil, sys

win = sys.platform.startswith("win")

if win:
	import win32api


def touch(file):
	
	with open(file, "a"):
		os.utime(file, None)
		
		
def cpf(src, dst, replace=True):
	
	if win:
		
		win32api.CopyFile(src, dst, 0 if replace else 1)
		
	else:
		
		shutil.copy(src, dst)