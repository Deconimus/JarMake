import os, shutil, zipfile, sys, subprocess, hashlib
import compositor

win = sys.platform.startswith("win")
linux = sys.platform.startswith("linux")
mac = sys.platform.startswith("darwin")

if win:
	import win32api


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
	
	packages = getPackages(srcDirs, projectPath, outdir)
	
	if len(packages) <= 0:
		print(projectPath[projectPath.rfind("/")+1:]+" is up-to-date.")
		return
		
	print("Compiling "+projectPath[projectPath.rfind("/")+1:])
	
	srcList = sourceListString(packages)
	srcPath = " -sourcepath "+pathList(srcDirs) if len(srcDirs) > 0 else ""
	clsPath = " -cp "+pathList(classPaths+dynamicIncludes+dynamicLinks) if len(classPaths) > 0 else ""
	
	if len(srcDirs) > 0:
		
		os.system("javac "+srcList+""+clsPath+""+srcPath+" -d \""+outdir+"/\" -Xprefer:newer")
	
	
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
	
	createManifest(projectPath, dynamicIncludes, dynamicLinks, extLibDir, mainClass)
	
	outFile = projectPath+"/.jarMakeCache/build.jar"
	if os.path.exists(outFile): os.remove(outFile)
	
	os.chdir(tmp)
	os.system("jar cmf \""+projectPath+"/MANIFEST.MF\" \""+outFile+"\" *")
	
	os.chdir(projectPath)
	
	os.remove(projectPath+"/MANIFEST.MF")
	
	shutil.rmtree(tmp)
	
	
def getPackages(srcDirs, projectPath, binDir, filter=True):
	
	files = []
	
	for srcDir in srcDirs:
		
		if srcDir.endswith("/") or srcDir.endswith("\\"):
			srcDir = srcDir[:-1]
		
		for dirName, subdirList, fileList in os.walk(srcDir):
			
			isPackage = False
			packageCompiled = True
			
			for f in fileList:
				if (f.lower().endswith(".java")):
					
					isPackage = True
					if not filter: break
					
					file = dirName+"/"+f
					
					classFile = binDir+"/"+file[len(srcDir)+1:-5]+".class"
					
					if not os.path.exists(classFile) or \
					   os.path.getmtime(file) >= os.path.getmtime(classFile):
					   
						packageCompiled = False
						break
					
				
			if isPackage and (not packageCompiled or not filter):
			
				name = dirName.replace("\\", "/")
						
				if name.startswith(projectPath):
					name = name[len(projectPath)+1:]
					
				files.append(name)
				
	return files
	
	
def sourceListString(sourceFiles):
	
	str = ""
	
	for f in sourceFiles:
		
		str = str+"\""+f+"/\"*.java "
		
	return str.strip()
	
	
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
	
	
def cpf(src, dst, replace=True):
	
	if win:
		
		win32api.CopyFile(src, dst, 0 if replace else 1)
		
	else:
		
		shutil.copy(src, dst)
	
	
def createManifest(projectPath, dynamicIncludes, dynamicLinks, extLibDir, mainClass):
	
	txt = "Manifest-Version: 1.0\n"
	
	if len(dynamicIncludes) > 0:
		
		txt = txt+"Rsrc-Class-Path: ./"
		for lib in dynamicIncludes:
			txt = txt+" "+lib.replace("\\", "/").split("/")[-1]
		txt = txt+"\n"
	
	txt = txt + "Class-Path: ."
	for lib in dynamicLinks:
		txt = txt+" \""+extLibDir+"/"+lib.replace("\\", "/").split("/")[-1]+"\""
	txt = txt + "\n"
	
	if len(mainClass) > 0:
	
		txt = txt + ("Rsrc-" if len(dynamicIncludes) > 0 else "") + "Main-Class: "+mainClass.strip()+"\n";
		
		if len(dynamicIncludes) > 0:
			
			txt = txt + "Main-Class: org.eclipse.jdt.internal.jarinjarloader.JarRsrcLoader\n"
	
	with open(projectPath+"/MANIFEST.MF", "w+") as f:
		
		f.write(txt)
		
		
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