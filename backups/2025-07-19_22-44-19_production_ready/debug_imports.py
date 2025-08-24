#!/usr/bin/env python3
"""
Debug script to trace all import attempts and identify missing modules
"""
import sys
import traceback
from importlib.abc import MetaPathFinder, Loader
from importlib.machinery import ModuleSpec

class ImportTracer:
    def __init__(self):
        self.missing_modules = set()
        self.import_attempts = []
    
    def find_spec(self, fullname, path, target=None):
        try:
            # Try to find the module normally
            for finder in sys.meta_path:
                if finder != self:
                    spec = finder.find_spec(fullname, path, target)
                    if spec is not None:
                        return spec
            
            # If we get here, the module wasn't found
            self.missing_modules.add(fullname)
            self.import_attempts.append(fullname)
            return None
            
        except Exception as e:
            self.missing_modules.add(fullname)
            self.import_attempts.append(f"{fullname} (error: {e})")
            return None

def main():
    tracer = ImportTracer()
    sys.meta_path.insert(0, tracer)
    
    try:
        # Try to import the main app
        from app import main
        print("✅ App imported successfully!")
    except Exception as e:
        print(f"❌ Import failed: {e}")
        print("\n📋 Missing modules:")
        for module in sorted(tracer.missing_modules):
            print(f"  - {module}")
        
        print(f"\n📊 Total missing modules: {len(tracer.missing_modules)}")
        print(f"📊 Total import attempts: {len(tracer.import_attempts)}")

if __name__ == "__main__":
    main() 