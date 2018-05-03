import os
from utils import *


def writeManifest(projectPath, dynamicIncludes, dynamicLinks, extLibDir, mainClass):
	
	txt = "Manifest-Version: 1.0\n"
	
	if len(dynamicIncludes) > 0:
		
		txt += "Rsrc-Class-Path: ./"
		for lib in dynamicIncludes:
			txt += " "+lib.replace("\\", "/").split("/")[-1]
		txt += "\n"
	
	txt += "Class-Path: ."
	for lib in dynamicLinks:
		txt += " \""+extLibDir+"/"+lib.replace("\\", "/").split("/")[-1]+"\""
	txt += "\n"
	
	if len(mainClass) > 0:
	
		txt += ("Rsrc-" if len(dynamicIncludes) > 0 else "") + "Main-Class: "+mainClass.strip()+"\n";
		
		if len(dynamicIncludes) > 0:
			
			txt += "Main-Class: org.eclipse.jdt.internal.jarinjarloader.JarRsrcLoader\n"
	
	writeFile(projectPath+"/MANIFEST.MF", txt)
		
		
def javaCmdString(scriptPath, mainClass, binDir, jarDir="", extJars=[]):
	
	cmd = "java -cp \""+binDir+"\""
	
	if jarDir:
		cmd += os.pathsep + "\""+jarDir+"/\"*"
		
	for jar in extJars:
		cmd += os.pathsep + "\""+jar+"\""
		
	cmd += " " + mainClass


def writeBatchScript(outfile, mainClass, binDir, jarDir, extJars):
	
	txt = "@echo off\r\n"
	
	txt += javaCmdString(outfile, mainClass, binDir, jarDir, extJars)
	txt += " %*\r\n"
	
	writeFile(outfile, txt)
		
		
def writeShellScript(outfile, mainClass, binDir, jarDir, extJars):
	
	txt = "#!/bin/sh\n"
	
	txt += javaCmdString(outfile, mainClass, binDir, jarDir, extJars)
	txt += " $@\n"
	
	writeFile(outfile, txt)


def writePythonScript(outfile, mainClass, binDir, jarDir, extJars):
	
	txt = "import os, sys\n\n"
	
	txt += "if __name__ == \"__main__\":\n"
	txt += "\t\n"
	txt += "\tos.system(\""
	txt += javaCmdString(outfile, mainClass, binDir, jarDir, extJars)
	txt += " \"+\" \".join(sys.argv)\n"
	
