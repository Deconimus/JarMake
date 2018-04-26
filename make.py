import os, sys


path = os.path.dirname(os.path.abspath(__file__)).replace("\\", "/")


def main(outFile):
	
	if not os.path.exists(path+"/make.json"):
		print("\""+path+"/make.json\" not found.")
		return
	
	jarMake = ""
	
	for p in os.environ["PATH"].split(";"):
		
		if p.lower().endswith("jarmake"):
			jarMake = p+"/jarMake.py"
			
	if (not os.path.exists(jarMake)) and os.path.exists(path+"/jarMake/jarMake.py"):
		
		jarMake = path+"/jarMake/jarMake.py"
		
	if not os.path.exists(jarMake):
		
		print("jarMake not found.")
		return
		
	jarMake = jarMake.replace("\\", "/")
	
	os.system("python \""+jarMake+"\" \""+path.replace("\\", "/")+"/make.json\" "+outFile)
	
	
if __name__ == "__main__":
	
	outFile = ""
	if len(sys.argv) > 1:
		outFile = "\""+sys.argv[1]+"\""
	
	main(outFile)