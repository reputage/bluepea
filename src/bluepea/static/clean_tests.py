import glob, os

for file in glob.glob("./tests/__javascript__/*.mod.js"):
    os.remove(file)
