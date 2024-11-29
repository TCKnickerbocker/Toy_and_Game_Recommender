clean:
	# Remove all log files in ./logs directory
	rm -f ./logs/*
	
	# Remove __pycache__ directories in the current directory and its subdirectories
	find . -type d -name "__pycache__" -exec rm -rf {} +
