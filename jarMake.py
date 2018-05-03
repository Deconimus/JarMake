import os, shutil, zipfile, sys, subprocess, hashlib, platform
import compositor, meta
from utils import *

win = sys.platform.startswith("win")
linux = sys.platform.startswith("linux")
mac = sys.platform.startswith("darwin")

cmdlimit = 0

if win:
	import win32api
	if platform.architecture()[0].startswith("64"):
		cmdlimit = 8191
	else:
		cmdlimit = 2047
else:
	cmdlimit = os.sysconf("SC_ARG_MAX")

path = os.path.dirname(os.path.abspath(__file__)).replace("\\", "/")


# root function
def make(makeFile, outFile=""):
	
	makeFile = makeFile.replace("\\", "/")
	projectPath = makeFile[:makeFile.rfind("/")]
	
	data = compositor.getBuildData(makeFile)
	
	if data is None or len(data) <= 0:
		return
	
	if len(outFile) > 0:
		
		if "/" in outFile:
			data["outDir"] = outFile[:outFile.rfind("/")]
			data["jarName"] = outFile[outFile.rfind("/")+1:]
		else:
			data["jarName"] = outFile
	
	compositor.build(projectPath, data)
	

def compile(projectPath, srcDirs, classPaths, dynamicIncludes, dynamicLinks, outdir):
	
	if not os.path.exists(outdir): os.makedirs(outdir)
	
	os.chdir(projectPath)
	
	classPaths.append(outdir)
	
	timestamp = outdir+"/compile.timestamp"
	
	srcPackages, srcFiles = getSources(srcDirs, projectPath, outdir, timestamp)
	srcStrings = buildSrcStrings(srcPackages, srcFiles)
	
	if not srcStrings:
		print(projectPath[projectPath.rfind("/")+1:]+" is up-to-date.")
		return
		
	print("Compiling "+projectPath[projectPath.rfind("/")+1:])
	
	srcPath = " -sourcepath "+pathList(srcDirs) if len(srcDirs) > 0 else ""
	clsPath = " -cp "+pathList(classPaths+dynamicIncludes+dynamicLinks) if len(classPaths) > 0 else ""
	
	cmdPrefix = "javac"
	cmdSuffix = clsPath+""+srcPath+" -d \""+outdir+"/\" -Xprefer:newer"
	
	commands = buildCommands(cmdPrefix, cmdSuffix, srcStrings, cmdlimit)
	
	for cmd in commands:
		
		os.system(cmd)
	
	touch(timestamp)
	
	
	
def buildJar(projectPath, mainClass, classPaths, dynamicIncludes,
			 dynamicLinks, extLibDir, packFiles):
	
	tmp = projectPath+"/.jarMakeCache/tmp"
	
	if os.path.exists(tmp): shutil.rmtree(tmp)
	
	os.makedirs(tmp)
	
	copyClassFiles(classPaths, tmp)
	copyLibraries(dynamicIncludes, tmp)
	copyLibraries(dynamicLinks, extLibDir)
	
	if len(dynamicIncludes) > 0:
		copyClassFiles([path+"/res/classloader"], tmp)
		
	for f in packFiles:
		cpf(f, tmp+"/"+(f[f.rfind("/")+1:]))
	
	meta.writeManifest(projectPath, dynamicIncludes, dynamicLinks, extLibDir, mainClass)
	
	outFile = projectPath+"/.jarMakeCache/build.jar"
	if os.path.exists(outFile): os.remove(outFile)
	
	os.chdir(tmp)
	os.system("jar cmf \""+projectPath+"/MANIFEST.MF\" \""+outFile+"\" *")
	
	os.chdir(projectPath)
	
	os.remove(projectPath+"/MANIFEST.MF")
	
	shutil.rmtree(tmp)
	
	
def getSources(srcDirs, projectPath, binDir, timestamp):
	
	packages = []
	files = []
	
	lastCompile = os.path.getmtime(timestamp) if os.path.exists(timestamp) else -1
	
	for srcDir in srcDirs:
		
		if srcDir.endswith("/") or srcDir.endswith("\\"):
			srcDir = srcDir[:-1]
		
		for dirName, subdirList, fileList in os.walk(srcDir):
			
			srcCount = 0
			sourcesToCompile = []
			
			for f in fileList:
				if (f.lower().endswith(".java")):
					
					srcCount += 1
					
					sourceFile = dirName+"/"+f
					classFile = binDir+"/"+sourceFile[len(srcDir)+1:-5]+".class"
					
					if not os.path.exists(classFile) or \
					   os.path.getmtime(sourceFile) >= \
					   (lastCompile if lastCompile > 0 else os.path.getmtime(classFile)):
						
						sourcesToCompile.append(sourceFile)
			
			shortenName = lambda s: s if not s.startswith(projectPath) else s[len(projectPath)+1:]
			
			if len(sourcesToCompile) >= srcCount and srcCount > 0:
				
				packages.append(shortenName(dirName.replace("\\", "/")))
			
			else:
				
				for src in sourcesToCompile:
					
					files.append(shortenName(src.replace("\\", "/")))
			
	return packages, files
	
	
def buildCommands(prefix, suffix, sources, cmdlimit):
	
	cmds = []
	
	cmd = prefix
	
	for src in sources:
		
		if len(cmd+" "+src+suffix) > cmdlimit:
			
			cmds.append(cmd+suffix)
			cmd = prefix
			
		cmd = cmd + " " + src
		
	if len(cmd) > len(prefix):
		cmds.append(cmd+suffix)
		
	return cmds
		
	
def buildSrcStrings(packages, files):
	
	srcStrings = []
	
	for p in packages:
		
		srcStrings.append("\""+p+"/\"*.java")
		
	for f in files:
		
		srcStrings.append("\""+f+"\"")
		
	return srcStrings
	
	
def pathList(paths):
	
	if len(paths) <= 0:
		return ""
	
	str = ""
	
	for p in paths:
		
		str = str+"\""+p
		
		if not p.lower().endswith(".jar"):
			str = str+"/"
			
		str = str+"\""+os.pathsep
		
	return str[:-1]
	
	
def copyClassFiles(paths, tmp):
	
	for d in paths:
		
		if d.lower().endswith(".jar"):
			
			with zipfile.ZipFile(d, "r") as jar:
				
				for entry in jar.infolist():
					
					if entry.filename.endswith("/") or entry.filename.endswith("MANIFEST.MF"):
						continue
						
					outFile = (tmp+"/"+entry.filename)
					outDir = outFile[:outFile.rindex("/")]
						
					if not os.path.exists(outDir):
						os.makedirs(outDir)
						
					jar.extract(entry, path=tmp)
			
		else:
			
			copyDir(d, tmp)
			
	
def copyLibraries(paths, parent):
	
	if len(paths) > 0 and not parent is None and not os.path.exists(parent):
		os.makedirs(parent)
	
	for f in paths:
		
		if f.lower().endswith(".jar"):
			
			cpf(f, parent+"/"+f.replace("\\", "/").split("/")[-1])
			
			
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
	
	
if __name__ == "__main__":
	
	if len(sys.argv) < 2:
		print("No Makefile specified.")
		quit()
	
	makeFile = sys.argv[1]
	
	if not os.path.exists(makeFile):
		print("\""+makeFile+"\" not found.")
		quit()
	
	outFile = ""
	
	if len(sys.argv) >= 3:
		outFile = sys.argv[2].replace("\\", "/")
		
	make(makeFile, outFile)