import os
from utils import *


def writeManifest(makeData):
	
	extLibDir = makeData.extLibDir
	
	txt = "Manifest-Version: 1.0\n"
	
	if makeData.dynImports:
		
		txt += "Rsrc-Class-Path: ./"
		for lib in makeData.dynImports:
			txt += " "+lib.replace("\\", "/").split("/")[-1]
		txt += "\n"
	
	txt += "Class-Path: ."
	for lib in makeData.dynImportsExt:
		txt += " \""+extLibDir+"/"+lib.replace("\\", "/").split("/")[-1]+"\""
	txt += "\n"
	
	if makeData.mainClass:
	
		txt += ("Rsrc-" if makeData.dynImports else "")+"Main-Class: "+makeData.mainClass.strip()+"\n";
		
		if makeData.dynImports:
			
			txt += "Main-Class: org.eclipse.jdt.internal.jarinjarloader.JarRsrcLoader\n"
	
	writeFile(makeData.projectPath+"/MANIFEST.MF", txt)
	
	
def addGitignoreEntry(gitignore, entry):
	
	entry = entry.replace("\\", "/")
	gitignore = gitignore.replace("\\", "/")
	
	if os.path.isdir(entry) and not entry.endswith("/"):
		entry = entry+"/"
		
	if entry.startswith(gitignore[:gitignore.rfind("/")]):
		entry = entry[gitignore.rfind("/")+1:]
	
	with open(gitignore, "r") as f:
		content = f.read()
		
	for line in content.split("\n"):
		if line.strip() == entry: return
		
	with open(gitignore, "a") as f:
		if not content.endswith("\n"): f.write("\n")
		f.write(entry+"\n")
		
		
def javaCmdString(makeData, target):
	
	cmd = "java"
	
	if makeData.runOptions:
		cmd += " "
		cmd += " ".join(makeData.runOptions)
	
	if target == "bin":
	
		cmd += " -cp \"bin\""
		
		if makeData.extLibDir:
			cmd += os.pathsep + "\""+makeData.extLibDir+"/\"*"
			
		#for jar in extJars:
		#	cmd += os.pathsep + "\""+jar+"\""
		
		cmd += " " + makeData.mainClass
	
	elif target == "jar":
	
		cmd += " -jar "
			
		if " " in makeData.jarName:
			cmd += "\""+makeData.jarName+"\""
		else:
			cmd += makeData.jarName
	
	return cmd


def writeScript(makeData, outDir, target, scriptType):
	
	if scriptType.startswith("py"):
		writePythonScript(makeData, outDir, target)
		
	elif scriptType.startswith("bat"):
		writeBatchScript(makeData, outDir, target)
		
	elif scriptType.startswith("sh"):
		writeShellScript(makeData, outDir, target)


def writeBatchScript(makeData, outDir, target):
	
	outfile = getScriptPath(makeData, outDir, ".bat")
	
	txt = "@echo off\r\n"
	
	txt += javaCmdString(makeData, target)
	txt += " %*\r\n"
	
	writeFile(outfile, txt)
		
		
def writeShellScript(makeData, outDir, target):
	
	outfile = getScriptPath(makeData, outDir, ".sh")
	
	txt = "#!/bin/sh\n"
	
	txt += javaCmdString(makeData, target)
	txt += " $@\n"
	
	writeFile(outfile, txt)


def writePythonScript(makeData, outDir, target):
	
	outfile = getScriptPath(makeData, outDir, ".py")
	
	txt = "import os, sys\n\n"
	
	txt += "if __name__ == \"__main__\":\n"
	txt += "\t\n"
	txt += "\targstr = \" \".join(sys.argv[1:])\n"
	txt += "\t\n"
	txt += "\tos.system(\""
	txt += javaCmdString(makeData, target).replace("\"", "\\\"")
	txt += " \"+argstr)\n"
	txt += "\t\n"
	
	writeFile(outfile, txt)
	

def getScriptPath(makeData, outDir, ext):
	
	outfile = outDir+"/"
	
	if makeData.jarName:
		outfile += makeData.jarName[:-4]
	else:
		outfile += makeData.projectPath[makeData.projectPath.rfind("/")+1:].lower()
		
	return outfile + ext