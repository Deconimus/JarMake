class MultiOutWrapper:
	
	
	def __init__(self, *outputs):
		
		self.outputs = outputs
		
		
	def write(self, val):
		
		for out in self.outputs:
			out.write(val)
			
			
	def flush(self):
		
		for out in self.outputs:
			out.flush()
			
			
	def close(self):
		
		for out in self.outputs:
			out.close()
			
			
	def fileno(self):
		
		for out in self.outputs:
			val = -1
			
			try: val = out.fileno()
			except: continue
			
			return val
			
		return 1
	