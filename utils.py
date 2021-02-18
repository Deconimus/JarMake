import os, shutil, sys, subprocess, io, collections

win = sys.platform.startswith("win")
linux = sys.platform.startswith("linux")
mac = sys.platform.startswith("darwin")

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
		
		
def copyDir(src, dst):
	
	src = os.path.abspath(src) if os.path.exists(src) else src
	dst = os.path.abspath(dst) if os.path.exists(dst) else dst
	
	src = src.strip().replace("\\", "/")
	dst = dst.strip().replace("\\", "/")
	
	if src[-1] == "/": src = src[:-1]
	if dst[-1] == "/": dst = dst[:-1]
	
	#if win:
		
		# won't close after completion...
		
		#cmd = ["xcopy", src, dst, "/s", "/y"]
		#subprocess.call(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		
	if linux or mac:
		
		cmd = ["cp", "-R", "-f", src, dst]
		subprocess.call(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		
	else:
		
		srcFiles, dstFiles, dstDirs = copyListFiles(src, dst)
		
		for d in dstDirs:
			if not os.path.exists(d): os.makedirs(d)
		
		for i in range(0, len(srcFiles)):
				
			cpf(srcFiles[i], dstFiles[i], True)
			
			
def copyListFiles(src, dst):
	
	srcFiles = []
	dstFiles = []
	dstDirs = []
	
	for dirName, subdirList, fileList, in os.walk(src):
		
		d = dirName.replace("\\", "/")
		dd = (dst+dirName[len(src):]).replace("\\", "/")
		
		dstDirs.append(dd)
		
		for f in fileList:
			
			srcFiles.append(d+"/"+f)
			dstFiles.append(dd+"/"+f)
			
	return srcFiles, dstFiles, dstDirs
		
		
def writeFile(filepath, text):
	
	dir = os.path.dirname(filepath)
	if not os.path.exists(dir): os.makedirs(dir)
	
	with open(filepath, "w+") as f:
		
		f.write(text)
		
		
def is_absolute(path):
	
	if not path or not isinstance(path, str) or len(path) < 3:
		return False
	
	if path[0] == "/" or path[1] == ":" or path[0] == "\\" or ":" in path:
		return True
		
	return False
	
		
class StringIOFix(io.StringIO):

	def __init__(self, initial_value="", newline="\n"):
		super(StringIOFix, self).__init__(initial_value, newline)
		
	def fileno(self):
		return 1
		

class CaseInsensitiveDict(collections.Mapping):
	def __init__(self, d):
		self._d = d
		self._s = dict((k.lower(), k) for k in d)
	def __contains__(self, k):
		return k.lower() in self._s
	def __len__(self):
		return len(self._s)
	def __iter__(self):
		return iter(self._s)
	def __getitem__(self, k):
		return self._d[self._s[k.lower()]]
	def actual_key_case(self, k):
		return self._s.get(k.lower())