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
	
		txt += ("Rsrc-" if makeData.dynImports else "") + "Main-Class: "+makeData.mainClass.strip()+"\n";
		
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
		
		
def javaBinCmdString(makeData):
	
	cmd = "java -cp \"bin\""
	
	if makeData.extLibDir:
		cmd += os.pathsep + "\""+makeData.extLibDir+"/\"*"
		
	#for jar in extJars:
	#	cmd += os.pathsep + "\""+jar+"\""
		
	cmd += " " + mainClass


def writeBatchBinScript(makeData, outDir):
	
	outfile = getScriptPath(makeData, outDir, ".bat")
	
	txt = "@echo off\r\n"
	
	txt += javaBinCmdString(makeData)
	txt += " %*\r\n"
	
	writeFile(outfile, txt)
		
		
def writeShellBinScript(makeData, outDir):
	
	outfile = getScriptPath(makeData, outDir, ".sh")
	
	txt = "#!/bin/sh\n"
	
	txt += javaBinCmdString(makeData)
	txt += " $@\n"
	
	writeFile(outfile, txt)


def writePythonBinScript(makeData, outDir):
	
	outfile = getScriptPath(makeData, outDir, ".py")
	
	txt = "import os, sys\n\n"
	
	txt += "if __name__ == \"__main__\":\n"
	txt += "\t\n"
	txt += "\tos.system(\""
	txt += javaBinCmdString(makeData)
	txt += " \"+\" \".join(sys.argv)\n"
	

def getScriptPath(makeData, outDir, ext):
	
	outfile = outDir+"/"
	
	if makeData.jarName:
		outfile += makeData.jarName[:-4]
	else:
		outfile += makeData.projectPath[makeData.projectPath.rfind("/")+1:].lower()
		
	return outfile + ext