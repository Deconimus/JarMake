import os
from utils import *


def writeManifest(makeData):
	
	extLibDir = makeData.outDir+"/"+makeData.extLibDir
	
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
		
		
def javaCmdString(scriptPath, mainClass, binDir, libDir="", extJars=[]):
	
	cmd = "java -cp \""+binDir+"\""
	
	if jarDir:
		cmd += os.pathsep + "\""+libDir+"/\"*"
		
	for jar in extJars:
		cmd += os.pathsep + "\""+jar+"\""
		
	cmd += " " + mainClass


def writeBatchScript(outfile, mainClass, binDir, libDir, extJars):
	
	txt = "@echo off\r\n"
	
	txt += javaCmdString(outfile, mainClass, binDir, libDir, extJars)
	txt += " %*\r\n"
	
	writeFile(outfile, txt)
		
		
def writeShellScript(outfile, mainClass, binDir, libDir, extJars):
	
	txt = "#!/bin/sh\n"
	
	txt += javaCmdString(outfile, mainClass, binDir, libDir, extJars)
	txt += " $@\n"
	
	writeFile(outfile, txt)


def writePythonScript(outfile, mainClass, binDir, libDir, extJars):
	
	txt = "import os, sys\n\n"
	
	txt += "if __name__ == \"__main__\":\n"
	txt += "\t\n"
	txt += "\tos.system(\""
	txt += javaCmdString(outfile, mainClass, binDir, libDir, extJars)
	txt += " \"+\" \".join(sys.argv)\n"
	
