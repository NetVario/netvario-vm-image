import os
import subprocess
import shutil
import tarfile

# Konfiguration
kernel_version = "5.10"  # Beispielversion, kann angepasst werden
program_path = "/path/to/dein_programm"  # Pfad zu deinem vorab kompilierten Programm
modules_dir = "modules"  # Verzeichnis mit .tar.gz-Dateien
rootfs_size_mb = 16
output_image = "rootfs.img"
output_kernel = "zImage"
config_file = "kernel.config"  # Pfad zur vorkonfigurierten .config-Datei

# 1. Kernel herunterladen und kompilieren
def download_and_compile_kernel():
    os.makedirs("linux", exist_ok=True)
    os.chdir("linux")
    subprocess.run(["wget", f"https://cdn.kernel.org/pub/linux/kernel/v{kernel_version[0]}.x/linux-{kernel_version}.tar.xz"])
    subprocess.run(["tar", "-xf", f"linux-{kernel_version}.tar.xz"])
    os.chdir(f"linux-{kernel_version}")

    # Vorkonfigurierte .config-Datei verwenden
    if os.path.exists(f"../{config_file}"):
        shutil.copy(f"../{config_file}", ".config")  # Kopiere die config-Datei
    else:
        raise FileNotFoundError(f"{config_file} wurde nicht gefunden.")

    subprocess.run(["make", "ARCH=arm", "CROSS_COMPILE=arm-linux-gnueabi-", "-j$(nproc)"])
    shutil.move(f"arch/arm/boot/zImage", f"../{output_kernel}")
    os.chdir("../..")

# 2. Minimalistisches Root-Dateisystem erstellen
def create_root_filesystem():
    os.makedirs("rootfs/bin", exist_ok=True)
    os.makedirs("rootfs/sbin", exist_ok=True)
    os.makedirs("rootfs/etc", exist_ok=True)
    os.makedirs("rootfs/dev", exist_ok=True)
    os.makedirs("rootfs/proc", exist_ok=True)
    os.makedirs("rootfs/sys", exist_ok=True)

    # Kopiere dein Programm
    shutil.copy(program_path, "rootfs/bin/dein_programm")

    # Init-Skript erstellen
    with open("rootfs/init", "w") as f:
        f.write("#!/bin/sh\n")
        f.write("/bin/dein_programm &\n")
        f.write("exec tor\n")
    os.chmod("rootfs/init", 0o755)

# 3. Module entpacken und installieren
def install_modules():
    for filename in os.listdir(modules_dir):
        if filename.endswith(".tar.gz"):
            module_path = os.path.join(modules_dir, filename)
            with tarfile.open(module_path, "r:gz") as tar:
                tar.extractall("rootfs")  # Entpacke ins Root-Dateisystem
            print(f"Modul {filename} installiert.")

# 4. Root-Dateisystem als Image erstellen
def create_rootfs_image():
    # Image erstellen
    subprocess.run(["dd", "if=/dev/zero", f"of={output_image}", "bs=1M", f"count={rootfs_size_mb}"])
    subprocess.run(["mkfs.ext2", output_image])
    os.makedirs("/mnt/rootfs", exist_ok=True)
    
    # Mount-Operation
    subprocess.run(["sudo", "mount", "-o", "loop", output_image, "/mnt/rootfs"])
    shutil.copytree("rootfs", "/mnt/rootfs", dirs_exist_ok=True)
    subprocess.run(["sudo", "umount", "/mnt/rootfs"])

# 5. Hauptfunktion
def main():
    download_and_compile_kernel()
    create_root_filesystem()
    install_modules()
    create_rootfs_image()
    print("Build abgeschlossen!")

if __name__ == "__main__":
    main()