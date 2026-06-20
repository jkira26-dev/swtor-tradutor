import sys
import os

ilspy_dir = os.path.abspath('ilspycmd')
sys.path.append(ilspy_dir)

import clr
clr.AddReference(os.path.join(ilspy_dir, 'ICSharpCode.Decompiler.dll'))

try:
    from ICSharpCode.Decompiler.CSharp import CSharpDecompiler
    from ICSharpCode.Decompiler import DecompilerSettings
except Exception as e:
    print(f"Error importing from ICSharpCode.Decompiler: {e}")
    sys.exit(1)
print("Decompiling to single file...")
decompiler = CSharpDecompiler("SWToR_RUS.exe", DecompilerSettings())
syntax_tree = decompiler.DecompileWholeModuleAsSingleFile()
print("Writing to file...")
with open("decompiled.cs", "w", encoding="utf-8") as f:
    f.write(syntax_tree.ToString())
print("Decompilation complete!")
