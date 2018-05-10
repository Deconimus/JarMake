import os, shutil, zipfile, sys, subprocess, hashlib, platform, argparse
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
def make(makeFile, args):
	
	makeFile = makeFile.replace("\\", "/")
	projectPath = makeFile[:makeFile.rfind("/")]
	
	data = compositor.getBuildData(makeFile)
	
	if data is None or len(data) <= 0:
		return
	
	if args.outFile:
		args.outFile = args.outFile.replace("\\", "/")
		if "/" in args.outFile:
			data["outDir"] = args.outFile[:outFile.rfind("/")]
			data["jarName"] = args.outFile[outFile.rfind("/")+1:]
		else:
			data["jarName"] = args.outFile
			
	if args.outDirs: data["outDirs"] = args.outDirs
	if args.jarName: data["jarName"] = args.jarName
	if args.runScripts: data["runScripts"] = args.runScripts
	if args.targets: data["targets"] = args.targets
	if args.mainClass: data["mainClass"] = args.mainClass
	
	compositor.build(projectPath, data)
	

def compile(makeData, outdir):
	
	if not os.path.exists(outdir): os.makedirs(outdir)
	
	os.chdir(makeData.projectPath)
	
	if not outdir in makeData.imports:
		makeData.imports.append(outdir)
	
	timestamp = outdir+"/compile.timestamp"
	log = open(outdir+"/compile.log", "w+")
	
	srcPackages, srcFiles = getSources(makeData.srcDirs, makeData.projectPath, outdir, timestamp)
	srcStrings = buildSrcStrings(srcPackages, srcFiles)
	
	if not srcStrings:
		print(makeData.projectPath[makeData.projectPath.rfind("/")+1:]+" is up-to-date.")
		return
		
	print("Compiling "+makeData.projectPath[makeData.projectPath.rfind("/")+1:])
	
	log.write("Sources to compile:\n\n")
	for src in srcStrings:
		log.write(src+"\n")
	
	log.write("\nClasspaths:\n\n")
	for lst in makeData.imports, makeData.dynImports, makeData.dynImportsExt:
		for s in lst:
			log.write(s+"\n")
	
	log.flush()
	
	srcPath = ""
	clsPath = ""
	
	if makeData.srcDirs:
		srcPath = " -sourcepath "+pathList(makeData.srcDirs)
	
	if makeData.imports or makeData.dynImports or makeData.dynImportsExt:
		clsPath = " -cp "+pathList(makeData.imports, makeData.dynImports, makeData.dynImportsExt)
	
	cmdPrefix = "javac"
	
	cmdSuffix = clsPath+""+srcPath+" -d \""+outdir+"/\" -Xprefer:newer"
	
	if makeData.javacOptions:
		cmdSuffix += " " + " ".join(makeData.javacOptions)
	
	commands = buildCommands(cmdPrefix, cmdSuffix, srcStrings, cmdlimit)
	
	log.write("\nJavac commands:\n\n")
	
	for cmd in commands:
		
		os.system(cmd)
		
		log.write(cmd+"\n\n")
		
	log.flush()
	log.close()
	
	touch(timestamp)
	
	
def buildJar(makeData):
	
	tmp = makeData.projectPath+"/.jarMakeCache/tmp"
	
	if os.path.exists(tmp): shutil.rmtree(tmp)
	
	os.makedirs(tmp)
	
	copyClassFiles(makeData.imports, tmp)
	copyLibraries(makeData.dynImports, tmp)
	for outDir in makeData.outDirs:
		copyLibraries(makeData.dynImportsExt, outDir+"/"+makeData.extLibDir)
	
	if makeData.dynImportsExt:
		copyClassFiles([path+"/res/classloader"], tmp)
		
	for f in makeData.packFiles:
		if not os.path.exists(f):
			print("Warning: Couldn't find \""+f+"\"!")
			continue
		cpf(f, tmp+"/"+(f[f.rfind("/")+1:]))
	
	meta.writeManifest(makeData)
	
	outFile = makeData.projectPath+"/.jarMakeCache/build.jar"
	if os.path.exists(outFile): os.remove(outFile)
	
	os.chdir(tmp)
	os.system("jar cmf \""+makeData.projectPath+"/MANIFEST.MF\" \""+outFile+"\" *")
	
	os.chdir(makeData.projectPath)
	
	os.remove(makeData.projectPath+"/MANIFEST.MF")
	
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
			
			classPackageDir = binDir+"/"+dirName.replace("\\", "/")[len(srcDir)+1:]
			
			if len(sourcesToCompile) >= srcCount and srcCount > 0:
				
				packages.append(shortenName(dirName.replace("\\", "/")))
				
				if os.path.exists(classPackageDir):
					for f in os.listdir(classPackageDir):
						if not f.endswith(".class"): continue
						os.remove(f)
				
			elif sourcesToCompile:
				
				subClassFiles = []
				for f in os.listdir(classPackageDir):
					if f.endswith(".class") and "$" in f:
						subClassFiles.append(f)
				
				for src in sourcesToCompile:
					
					files.append(shortenName(src.replace("\\", "/")))
					
					prefix = src[src.rfind("/")+1:-5]+"$"
					
					i = 0
					while i < len(subClassFiles):
						if subClassFiles[i].startswith(prefix):
							os.remove(classPackageDir+"/"+subClassFiles[i])
							subClassFiles.pop(i)
						else:
							i += 1
					
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
	
	
def pathList(*paths):
	
	if not paths: return ""
	
	str = ""
	
	for pths in paths:
		for p in pths:
			
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
			

def parseArgs(args):
	
	parser = argparse.ArgumentParser()
	
	parser.add_argument("makeFile", type=str)
	parser.add_argument("--outFile", type=str)
	parser.add_argument("-dir", "--outDirs", type=str, nargs="+")
	parser.add_argument("-j", "--jarName", type=str)
	parser.add_argument("-t", "--targets", type=str, nargs="+")
	parser.add_argument("--runScripts", type=str, nargs="+")
	parser.add_argument("-m", "--mainClass", type=str)
	
	return parser.parse_args(args)


if __name__ == "__main__":
	
	args = parseArgs(sys.argv[1:])
	
	if not args.makeFile:
		print("No makefile specified.")
		quit()
	
	if not os.path.exists(args.makeFile):
		print("\""+args.makeFile+"\" not found.")
		quit()
	
	make(args.makeFile, args)