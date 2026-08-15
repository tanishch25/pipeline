import uvicorn
import os
import subprocess

def build_frontend():
    frontend_dir = os.path.join(os.path.dirname(__file__), "frontend")
    dist_dir = os.path.join(frontend_dir, "dist")
    
    if not os.path.exists(dist_dir):
        print("Frontend dist not found. Building React app...")
        # npm ci or install might be needed, but assume modules are installed
        if not os.path.exists(os.path.join(frontend_dir, "node_modules")):
            subprocess.run(["npm", "install"], cwd=frontend_dir, shell=True, check=True)
            
        subprocess.run(["npm", "run", "build"], cwd=frontend_dir, shell=True, check=True)
        print("Build complete.")

if __name__ == "__main__":
    if os.path.exists(os.path.join(os.path.dirname(__file__), "frontend")):
        build_frontend()
        
    uvicorn.run("api.app:app", host="0.0.0.0", port=8000, reload=True)
