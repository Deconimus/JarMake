import os, shutil, json, hashlib, zipfile
import jarMake, meta
from utils import *
from makeData import MakeData


path = os.path.dirname(os.path.abspath(__file__)).replace("\\", "/")

compiled_dependencies = set([])


def build(projectPath, data):
	
	projectPath = projectPath.replace("\\", "/")
	
	makeData = processMakeData(projectPath, data)
	
	for outDir in makeData.outDirs:
		if not os.path.exists(outDir): os.makedirs(outDir)
	
	binPath = makeData.projectPath.replace("\\", "/")+"/.jarMakeCache/bin"
	
	if not binPath in makeData.imports: makeData.imports.append(binPath)
	
	for target in makeData.targets:
		
		if target == "jar":
			buildJarTarget(makeData, data, binPath)
			
		elif target == "bin":
			buildBinTarget(makeData, binPath)
			
		elif target == "compile":
			buildCompileTarget(makeData, binPath)
			
	writeBuildImportsJson(makeData)
			
	print("All targets are done.")
	
	
def buildJarTarget(makeData, data, binPath):
	
	if not checkUpToDate(makeData.projectPath, makeData):
		
		jarMake.compile(makeData, binPath)
		
		print("Making "+makeData.jarName)
		
		jarMake.buildJar(makeData)
		
		jarShrink = None
		jarShrinkKeep = []
		
		if "jarShrink" in data and "path" in data["jarShrink"]:
			
			jarShrink = data["jarShrink"]["path"]
			
			if not os.path.exists(jarShrink):
				print("\""+jarShrink+"\" not found.")
				jarShrink = None
			
			if "keep" in data["jarShrink"]:
				
				jarShrinkKeep = data["jarShrink"]["keep"]
				
		if jarShrink:
			
			jp = "\""+makeData.projectPath+"/.jarMakeCache/build.jar"+"\""
			
			ks = ""
			for k in jarShrinkKeep:
				ks = ks+" -k \""+k+"\""
				
			jarShrinkTmp = makeData.projectPath+"/.jarMakeCache/jarShrink_tmp"
			
			print("Shrinking "+makeData.jarName)
			
			os.system("java -jar \""+jarShrink+"\" "+jp+" -out "+jp+" -t \""+jarShrinkTmp+"\" -n "+ks)
			
			shutil.rmtree(jarShrinkTmp)
			
	else:
		
		print(makeData.jarName+" is up-to-date.")
		
	
	for outDir in makeData.outDirs:
		cpf(makeData.projectPath+"/.jarMakeCache/build.jar", outDir+"/"+makeData.jarName, True)
		
	if makeData.runScripts:
		
		print("Writing runscripts.")
		
		for outDir in makeData.outDirs:
			for scriptType in makeData.runScripts:
				meta.writeScript(makeData, outDir, "jar", scriptType)
	
	if makeData.copyFiles:
		
		print("Copying files into output directories.")
		
		for outDir in makeData.outDirs:
			copyFilesToTarget(makeData, outDir)
	
	
def buildBinTarget(makeData, binPath):
	
	jarMake.compile(makeData, binPath)
		
	for outDir in makeData.outDirs:
		
		outBinPath = outDir.replace("\\", "/")+"/bin"
		
		if not outBinPath == binPath:
			
			if os.path.exists(outBinPath): shutil.rmtree(outBinPath)
			os.makedirs(outBinPath)
			
			copyDir(binPath, outBinPath)
			
			timestamp = outBinPath+"/compile.timestamp"
			compilelog = outBinPath+"/compile.log"
			if os.path.exists(timestamp): os.remove(timestamp)
			if os.path.exists(compilelog): os.remove(compilelog)
			
		for scriptType in makeData.runScripts:
			
			meta.writeScript(makeData, outDir, "bin", scriptType)
			
		copyFilesToTarget(makeData, outDir)
			
				
def buildCompileTarget(makeData, binPath):
	
	jarMake.compile(makeData, binPath)
	
	
def processMakeData(projectPath, data):
	
	cacheDir = projectPath+"/.jarMakeCache"
	
	if not os.path.exists(cacheDir):
		
		os.makedirs(cacheDir)
		
		if os.path.exists(projectPath+"/.gitignore"):
			meta.addGitignoreEntry(projectPath+"/.gitignore", cacheDir)
	
	makeData = MakeData()
	makeData.loadFromData(projectPath, data)
	
	checkForProjects(makeData.imports, makeData.dynImports, makeData.dynImportsExt, makeData.srcDirs)
	checkForProjectsDyn(makeData.dynImports)
	checkForProjectsDyn(makeData.dynImportsExt)
	
	return makeData
	
	
def copyFilesToTarget(makeData, outDir):
	
	for i in range(0, len(makeData.copyFiles), 2):
		
		src = makeData.copyFiles[i]
		dst = outDir+"/"+makeData.copyFiles[i+1]
		
		parent = os.path.abspath(os.path.dirname(dst))
		
		if not os.path.exists(parent): os.makedirs(parent)
		
		if os.path.exists(dst) and os.path.getmtime(dst) >= os.path.getmtime(src):
			continue
		
		cpf(src, dst)
	
	
def completePaths(paths, projectPath):
	
	for i in range(0, len(paths)):
		
		paths[i] = completePath(paths[i], projectPath)
			
			
def completePath(p, projectPath):
	
	p = p.replace("\\", "/")
	
	if not is_absolute(p):
		
		p = projectPath+"/"+p
		
	ind = p.find("/../")
	while ind >= 0:
		left = p[:ind]
		right = p[ind+4:]
		left = left[:left.rindex("/")]
		p = left + "/" + right
		ind = p.find("/../")
		
	return p
	
	
def isProject(path):
	return path.endswith(".json") or os.path.exists(path+"/make.json")
	

def checkForProjectsDyn(imports):
	
	checkForProjects(imports, None, None, None, dynamic=True)


def checkForProjects(imports, dynImports, dynImportsExt, srcDirs, dynamic=False):
	
	i = 0
	while i < len(imports):
		
		project = imports[i]
		
		if isProject(imports[i]):
			
			project = project.replace("\\", "/")
			
			makeFile = project+"/"+"make.json"
			
			if project.endswith(".json"):
				makeFile = project
				project = project[:project.rfind("/")]
			
			data = getBuildData(makeFile)
			
			if not data is None:
				
				if dynamic:
					
					imports[i] = buildDependency(project, data)
					
				else:
					
					complete = lambda p: completePath(p, project)
						
					appendElementsFromMap(data, imports, "imports", proc=complete)
					appendElementsFromMap(data, dynImports, "dynImports", proc=complete)
					appendElementsFromMap(data, dynImportsExt, "dynImportsExt", proc=complete)
					
					binPath = project+"/.jarMakeCache/bin"
					
					compileDependency(project, data, binPath)
					
					if not binPath in imports:
						imports.append(binPath)
					
					imports[i] = None
					
			else:
				
				imports[i] = None
				
		if imports[i] is None or not os.path.exists(imports[i]):
			
			del imports[i]
			i = i-1
			
		i = i+1
	
	
def getBuildData(makeFile):
	
	with open(makeFile) as f:
		data = json.load(f)
		
	if data is None or len(data) <= 0:
		print("\""+makeFile+"\" is corrupted.")
		return None
		
	return data
	
	
def buildDependency(project, data):
	
	data["outDir"] = path+"/tmp_libs"
	data["targets"] = ["jar"]
	
	if not "jarName" in data:
		data["jarName"] = project.replace("\\", "/").split("/")[-1]
		
	build(project, data)
	
	libPath = path+"/tmp_libs"+data["jarName"]
	
	if not libPath.lower().endswith(".jar"):
		libPath = libPath+".jar"
		
	if not os.path.exists(libPath):
		
		return None
	
	return libPath
	
	
def compileDependency(projectPath, data, binPath):
	
	global compiled_dependencies
	
	projectPath = projectPath.replace("\\", "/")
	
	if not projectPath in compiled_dependencies:
		
		compiled_dependencies.add(projectPath)
	
		makeData = processMakeData(projectPath, data)
		
		jarMake.compile(makeData, binPath)
	
	
def checkUpToDate(projectPath, makeData):
	
	if not os.path.exists(projectPath+"/.jarMakeCache/build.jar"):
		return False
		
	buildTime = os.path.getmtime(projectPath+"/.jarMakeCache/build.jar")
	
	if os.path.getmtime(projectPath+"/make.json") > buildTime:
		return False
	
	for srcDir in makeData.srcDirs:
		for dirName, subdirList, fileList in os.walk(srcDir):
			
			if os.path.getmtime(dirName) > buildTime:
				return False
			
			for f in fileList:
				
				if not f.lower().endswith(".java"):
					continue
					
				if os.path.getmtime(dirName+"/"+f) > buildTime:
					return False
	
	for files in makeData.imports, makeData.dynImports, makeData.dynImportsExt:			
		for file in files:
			if os.path.isdir(file) or not os.path.exists(file): continue
			if os.path.getmtime(file) >= buildTime: return False
	
	# due to wildcards, it is possible for the imports to change while the makefile doesn't:
	
	buildImportsFile = makeData.projectPath+"/.jarMakeCache/buildImports.json"
	if not os.path.exists(buildImportsFile): return False
		
	with open(buildImportsFile) as f:
		buildImportsData = json.load(f)
		
	if not makeData.imports == buildImportsData["imports"] or \
	   not makeData.dynImports == buildImportsData["dynImports"] or \
	   not makeData.dynImportsExt == buildImportsData["dynImportsExt"] or \
	   not makeData.packFiles == buildImportsData["packFiles"]:
	   
	   return False
	
	return True
	
	
def writeBuildImportsJson(makeData):
	
	data = {}
	data["imports"] = makeData.imports
	data["dynImports"] = makeData.dynImports
	data["dynImportsExt"] = makeData.dynImportsExt
	data["packFiles"] = makeData.packFiles
	
	with open(makeData.projectPath+"/.jarMakeCache/buildImports.json", "w+") as f:
		json.dump(data, f, indent=4)
		
		
def appendElementsFromMap(m, l, key, proc=None):
	
	if key in m:
		for e in m[key]:
			if not proc is None and not e is None:
				e = proc(e)
				
			if not e in l:
				l.append(e)
				
				
def cleanup():
	
	removeTmpLibs()

				
def removeTmpLibs():
	
	if os.path.exists(path+"/tmp_libs"):
		
		shutil.rmtree(path+"/tmp_libs")
		
		