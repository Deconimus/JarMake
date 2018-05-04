import os
import compositor


class MakeData:
	
	
	def __init__(self):
		
		self.projectPath = ""
		self.jarName = "app"
		self.outDir = "release"
		self.mainClass = ""
		self.srcDirs = None
		self.imports = []
		self.dynImports = []
		self.dynImportsExt = []
		self.extLibDir = "lib"
		self.packFiles = []
		self.targets = ["jar"]
		
	
	def loadFromData(self, projectPath, data):
		
		self.projectPath = projectPath
		self.jarName = data["jarName"] if "jarName" in data else self.jarName
		self.outDir = data["outDir"] if "outDir" in data else self.outDir
		self.mainClass = data["main"] if "main" in data else self.mainClass
		self.srcDirs = data["sourceDirs"] if "sourceDirs" in data else self.srcDirs
		self.imports = data["imports"] if "imports" in data else self.imports
		self.dynImports = data["dynImports"] if "dynImports" in data else self.dynImports
		self.dynImportsExt = data["dynImportsExt"] if "dynImportsExt" in data else self.dynImportsExt
		self.extLibDir = data["extLibDir"] if "extLibDir" in data else self.extLibDir
		self.packFiles = data["packFiles"] if "packFiles" in data else self.packFiles
		self.targets = data["target"] if "target" in data else self.targets
		self.targets = data["targets"] if "targets" in data else self.targets
		
		if isinstance(self.targets, str):
			self.targets = [self.targets]
		
		if self.srcDirs is None or len(self.srcDirs) <= 0:
			self.srcDirs = [self.projectPath+"/src"]
		
		if not self.jarName.lower().endswith(".jar"):
			self.jarName = self.jarName+".jar"
			
		compositor.completePaths(self.srcDirs, projectPath)
		compositor.completePaths(self.imports, projectPath)
		compositor.completePaths(self.dynImports, projectPath)
		compositor.completePaths(self.dynImportsExt, projectPath)
		self.extLibDir = compositor.completePath(self.extLibDir, projectPath)
		compositor.completePaths(self.packFiles, projectPath)
		self.outDir = compositor.completePath(self.outDir, projectPath)