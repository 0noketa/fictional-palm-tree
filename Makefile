# win10 store app
PY_INCLUDE=C:\PROGRA~1\WindowsApps\PythonSoftwareFoundation.Python.3.9_3.9.496.0_x64__qbz5n2kfra8p0\include
PY_LIBS=C:\PROGRA~1\WindowsApps\PythonSoftwareFoundation.Python.3.9_3.9.496.0_x64__qbz5n2kfra8p0\libs
CC_PFX=cl /Fe
CC_SFX= /O1 /favor:INTEL64 /LD /I$(PY_INCLUDE) /link /libpath:$(PY_LIBS) python3.lib
RM = del

brainfuck_interpreter.pyd: brainfuck_interpreter.c
	$(CC_PFX)brainfuck_interpreter.pyd brainfuck_interpreter.c $(CC_SFX)
brainfuck_interpreter.c:
	cython -3 brainfuck_interpreter.py

repmac.pyd: repmac.c
	$(CC_PFX)repmac.pyd repmac.c $(CC_SFX)
repmac.c:
	cython -3 repmac.py

pfch.pyd: pfch.c
	$(CC_PFX)pfch.pyd pfch.c $(CC_SFX)
pfch.c:
	cython -3 pfch.py

pych.pyd: pych.c
	$(CC_PFX)pych.pyd pych.c $(CC_SFX)
pych.c:
	cython -3 pych.py

clean:
	$(RM) *.pyd
	$(RM) *.c 
	$(RM) *.lib 
	$(RM) *.obj
