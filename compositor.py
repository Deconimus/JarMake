import os, shutil, json, hashlib, zipfile
import jarMake


path = os.path.dirname(os.path.abspath(__file__)).replace("\\", "/")


def build(projectPath, data):
	
	projectPath = projectPath.replace("\\", "/")
	
	jarName, outDir, mainClass, srcDirs, imports, dynImports, dynImportsExt, \
		extLibDir, packFiles = processBuildData(projectPath, data)
	
	if not checkUpToDate(projectPath, srcDirs):
		
		binPath = projectPath+"/.jarMakeCache/bin"
		
		jarMake.compile(projectPath, srcDirs, imports, dynImports, dynImportsExt, binPath)
		
		if not binPath in imports: imports.append(binPath)
		
		print("Making "+jarName)
		
		jarMake.buildJar(projectPath, mainClass, imports, dynImports, dynImportsExt,
						 outDir+"/"+extLibDir, packFiles)
		
		jarShrink = None
		jarShrinkKeep = []
		
		if "jarShrink" in data and "path" in data["jarShrink"]:
			
			jarShrink = data["jarShrink"]["path"]
			
			if not os.path.exists(jarShrink):
				print("\""+jarShrink+"\" not found.")
				jarShrink = None
			
			if "keep" in data["jarShrink"]:
				
				jarShrinkKeep = data["jarShrink"]["keep"]
				
		if not jarShrink is None:
			
			jp = "\""+projectPath+"/.jarMakeCache/build.jar"+"\""
			
			ks = ""
			for k in jarShrinkKeep:
				ks = ks+" -k \""+k+"\""
				
			jarShrinkTmp = projectPath+"/.jarMakeCache/jarShrink_tmp"
			
			print("Shrinking "+jarName)
			
			os.system("java -jar \""+jarShrink+"\" "+jp+" -out "+jp+" -t \""+jarShrinkTmp+"\" -n "+ks)
			
			shutil.rmtree(jarShrinkTmp)
			
	else:
		
		print(jarName+" is up-to-date.")
		
		
	jarMake.cpf(projectPath+"/.jarMakeCache/build.jar", outDir+"/"+jarName, True)
		
	print("All targets are done.")
	
	
def processBuildData(projectPath, data):
	
	if not os.path.exists(projectPath+"/.jarMakeCache"):
		os.mkdir(projectPath+"/.jarMakeCache")
	
	jarName = data["jarName"] if "jarName" in data else "app"
	outDir = data["outDir"] if "outDir" in data else ""
	mainClass = data["main"] if "main" in data else ""
	srcDirs = data["sourceDirs"] if "sourceDirs" in data else None
	imports = data["imports"] if "imports" in data else []
	dynImports = data["dynImports"] if "dynImports" in data else []
	dynImportsExt = data["dynImportsExt"] if "dynImportsExt" in data else []
	extLibDir = data["extLibDir"] if "extLibDir" in data else "lib"
	packFiles = data["packFiles"] if "packFiles" in data else []
	
	if srcDirs is None or len(srcDirs) <= 0:
		srcDirs = [projectPath+"/src"]
	
	if not jarName.lower().endswith(".jar"):
		jarName = jarName+".jar"
		
	completePaths(srcDirs, projectPath)
	completePaths(imports, projectPath)
	completePaths(dynImports, projectPath)
	completePaths(dynImportsExt, projectPath)
	extLibDir = completePath(extLibDir, projectPath)
	completePaths(packFiles, projectPath)
	outDir = completePath(outDir, projectPath)
	
	checkForProjects(imports, dynImports, dynImportsExt, srcDirs)
	checkForProjectsDyn(dynImports)
	checkForProjectsDyn(dynImportsExt)
	
	return jarName, outDir, mainClass, srcDirs, imports, dynImports, dynImportsExt, \
			extLibDir, packFiles
	
	
def completePaths(paths, projectPath):
	
	for i in range(0, len(paths)):
		
		paths[i] = completePath(paths[i], projectPath)
			
			
def completePath(p, projectPath):
	
	p = p.replace("\\", "/")
	
	if not p.startswith("/") and not (len(p) > 1 and p[1] == ":"):
		
		return projectPath+"/"+p
		
	return p
	
	
def isProject(directory):
	return os.path.exists(directory+"/make.json") or directory.endswith("/make.json")
	

def checkForProjectsDyn(imports):
	
	checkForProjects(imports, None, None, None, dynamic=True)


def checkForProjects(imports, dynImports, dynImportsExt, srcDirs, dynamic=False):
	
	i = 0
	while i < len(imports):
		
		project = imports[i]
		
		if isProject(imports[i]):
			
			project = project.replace("\\", "/")
			
			if project.endswith("/make.json"):
				project = project[:project.rindex("/")]
			
			makeFile = project+"/"+"make.json"
			
			data = getBuildData(makeFile)
			
			if not data is None:
				
				if dynamic:
					
					imports[i] = buildDependency(project, data)
					
				else:
					
					#if not "srcDirs" in data:
					#	data["srcDirs"] = [project+"/src"]
					
					complete = lambda p: completePath(p, project)
						
					appendElementsFromMap(data, imports, "imports", proc=complete)
					appendElementsFromMap(data, dynImports, "dynImports", proc=complete)
					appendElementsFromMap(data, dynImportsExt, "dynImportsExt", proc=complete)
					#appendElementsFromMap(data, srcDirs, "srcDirs", proc=complete)
					
					binPath = project+"/.jarMakeCache/bin"
					
					compileDependency(project, data, binPath)
					
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
	
	projectPath = projectPath.replace("\\", "/")
	
	jarName, outDir, mainClass, srcDirs, imports, dynImports, dynImportsExt, \
		extLibDir, packFiles = processBuildData(projectPath, data)
	
	jarMake.compile(projectPath, srcDirs, imports, dynImports, dynImportsExt, binPath)
	
	
def checkUpToDate(projectPath, srcDirs):
	
	if not os.path.exists(projectPath+"/.jarMakeCache/build.jar"):
		return False
		
	buildTime = os.path.getmtime(projectPath+"/.jarMakeCache/build.jar")
	
	if os.path.getmtime(projectPath+"/make.json") > buildTime:
		return False
	
	for srcDir in srcDirs:
		for dirName, subdirList, fileList in os.walk(srcDir):
			
			if os.path.getmtime(dirName) > buildTime:
				return False
			
			for f in fileList:
				
				if not f.lower().endswith(".java"):
					continue
					
				if os.path.getmtime(dirName+"/"+f) > buildTime:
					return False
	
	return True
	
	
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
		
		