import os
import compositor


class MakeData:
	
	
	def __init__(self):
		
		self.projectPath = ""
		self.jarName = "app"
		self.outDirs = ["release"]
		self.mainClass = ""
		self.srcDirs = ["src"]
		self.imports = []
		self.dynImports = []
		self.dynImportsExt = []
		self.extLibDir = "lib"
		self.packFiles = []
		self.targets = ["jar"]
		self.runScripts = []
		self.javacOptions = []
		self.runOptions = []
		
	
	def loadFromData(self, projectPath, data):
		
		self.projectPath = projectPath.replace("\\", "/")
		self.jarName = data["jarName"] if "jarName" in data else self.jarName
		self.outDirs = data["outDir"] if "outDir" in data else self.outDirs
		self.outDirs = data["outDirs"] if "outDirs" in data else self.outDirs
		self.mainClass = data["main"] if "main" in data else self.mainClass
		self.mainClass = data["mainClass"] if "mainClass" in data else self.mainClass
		self.srcDirs = data["sourceDirs"] if "sourceDirs" in data else self.srcDirs
		self.imports = data["imports"] if "imports" in data else self.imports
		self.dynImports = data["dynImports"] if "dynImports" in data else self.dynImports
		self.dynImportsExt = data["dynImportsExt"] if "dynImportsExt" in data else self.dynImportsExt
		self.extLibDir = data["extLibDir"] if "extLibDir" in data else self.extLibDir
		self.packFiles = data["packFiles"] if "packFiles" in data else self.packFiles
		self.targets = data["target"] if "target" in data else self.targets
		self.targets = data["targets"] if "targets" in data else self.targets
		self.runScripts = data["runScripts"] if "runScripts" in data else self.runScripts
		self.runScripts = data["scripts"] if "scripts" in data else self.runScripts
		self.javacOptions = data["javacOptions"] if "javacOptions" in data else self.javacOptions
		self.runOptions = data["runOptions"] if "runOptions" in data else self.runOptions
		
		self.srcDirs = ensureList(self.srcDirs)
		self.imports = ensureList(self.imports)
		self.dynImports = ensureList(self.dynImports)
		self.dynImportsExt = ensureList(self.dynImportsExt)
		self.packFiles = ensureList(self.packFiles)
		self.targets = ensureList(self.targets)
		self.runScripts = ensureList(self.runScripts)
		self.outDirs = ensureList(self.outDirs)
		self.runOptions = ensureList(self.runOptions)
		self.javacOptions = ensureList(self.javacOptions)
		
		self.targets = [t.lower().strip() for t in self.targets]
		self.runScripts = [s.lower().strip() for s in self.runScripts]
		
		if not self.jarName.lower().endswith(".jar"):
			self.jarName = self.jarName+".jar"
			
		if ("bin" in self.targets or self.javacOptions) and self.mainClass and not self.runScripts:
			self.runScripts = ["py"]
			
		compositor.completePaths(self.srcDirs, projectPath)
		compositor.completePaths(self.imports, projectPath)
		compositor.completePaths(self.dynImports, projectPath)
		compositor.completePaths(self.dynImportsExt, projectPath)
		self.extLibDir = compositor.completePath(self.extLibDir, projectPath)
		compositor.completePaths(self.packFiles, projectPath)
		compositor.completePaths(self.outDirs, projectPath)
		
		expandWildcards(self.imports, self.dynImports, self.dynImportsExt, self.packFiles)
		
		
def expandWildcards(*paths):
	
	for pths in paths:
		
		i = 0
		while i < len(pths):
			
			p = pths[i]
			
			name = p[p.rfind("/")+1:]
			dir = p[:p.rfind("/")]
			
			ind = name.find("*")
			if ind < 0 or not os.path.isdir(dir):
				i += 1
				continue
			
			prefix = name[:ind]
			suffix = name[ind+1:]
			
			for file in os.listdir(dir):
				
				if file.startswith(prefix) and file.endswith(suffix):
					
					pths.append(dir+"/"+file)
					
			del pths[i]
			
			
def ensureList(lst):
	if not isinstance(lst, list):
		return [lst]
	return lst