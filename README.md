# sic_asm

An ultra-simple, barebones assembler for the SIC machine

# USAGE

```
$ ./sic_asm sample_program
$ cat intermediate.txt  # intermediate file
$ cat out.txt  # object code
```

OR...

```Cython
from sic_asm import SicAsm
m = SicAsm()
m.assemble(source_input_file, object_output_file)
```
