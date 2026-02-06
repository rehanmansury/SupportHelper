import os
import sys
import subprocess

def main():
    """Master script to build and package SupportHelper"""
    
    print("🚀 SupportHelper Build and Package Tool")
    print("=" * 50)
    
    # Get paths
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    
    print(f"📁 Working directory: {current_dir}")
    print(f"📁 Source directory: {parent_dir}")
    
    while True:
        print("\n" + "=" * 50)
        print("Select an option:")
        print("1. Build EXE")
        print("2. Sign EXE (requires certificate)")
        print("3. Create Installer Package")
        print("4. Create GitHub Release")
        print("5. Build & Sign & Package (All)")
        print("6. Exit")
        print("=" * 50)
        
        choice = input("\nEnter choice (1-6): ").strip()
        
        if choice == '1':
            print("\n🔨 Building EXE...")
            subprocess.run([sys.executable, 'build_exe.py'], cwd=current_dir)
            
        elif choice == '2':
            print("\n🔐 Signing EXE...")
            subprocess.run([sys.executable, 'simple_sign.py'], cwd=current_dir)
            
        elif choice == '3':
            print("\n📦 Creating installer...")
            subprocess.run([sys.executable, 'create_installer.py'], cwd=current_dir)
            
        elif choice == '4':
            print("\n🚀 Creating release...")
            subprocess.run([sys.executable, 'create_release.py'], cwd=current_dir)
            
        elif choice == '5':
            print("\n🎯 Running complete process...")
            
            # Build
            print("\n[1/3] Building EXE...")
            result1 = subprocess.run([sys.executable, 'build_exe.py'], cwd=current_dir)
            
            if result1.returncode == 0:
                # Sign
                print("\n[2/3] Signing EXE...")
                result2 = subprocess.run([sys.executable, 'simple_sign.py'], cwd=current_dir)
                
                if result2.returncode == 0:
                    # Package
                    print("\n[3/3] Creating installer...")
                    subprocess.run([sys.executable, 'create_installer.py'], cwd=current_dir)
                else:
                    print("\n⚠️ Signing failed, but continuing...")
            else:
                print("\n❌ Build failed!")
            
        elif choice == '6':
            print("\n👋 Goodbye!")
            break
            
        else:
            print("\n❌ Invalid choice! Please try again.")
    
    # Show final output location
    dist_dir = os.path.join(current_dir, 'dist')
    if os.path.exists(dist_dir):
        print("\n📁 Output files in:")
        print(f"   {dist_dir}")
        print("\nAvailable packages:")
        for item in os.listdir(dist_dir):
            item_path = os.path.join(dist_dir, item)
            if os.path.isfile(item_path):
                size = os.path.getsize(item_path) / (1024*1024)
                print(f"   📦 {item} ({size:.1f} MB)")

if __name__ == "__main__":
    main()
