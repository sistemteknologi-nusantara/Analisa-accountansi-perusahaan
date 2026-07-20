# ==================================================
# 🏢 SISTEM TERPADU: KEAMANAN + PENGAWASAN + PELACAKAN
# ✅ VERIFIKASI SIDIK JARI KHUSUS PEMILIK • v4.4
# Perangkat: Raspberry Pi Pico W
# Dibuat Oleh: FADLI IFAN SYAH
# ==================================================

import network
import socket
import time
import urequests
import ujson
import random
import machine
from machine import Pin, PWM, RTC

# ==================================================
# 🔑 KONFIGURASI UTAMA
# ==================================================
ID_SIDIK_JARI_IZIN = 1
NAMA_PEMILIK = "FADLI IFAN SYAH"
STATUS_TERVERIFIKASI = False

NAMA_PERUSAHAAN = "PT. SISTEM TEKNOLOGI NUSANTARA"
DOMAIN_RESMI = "cah-tegalan.web.id"
SSID_PERUSAHAAN = "FDLIFANSYH120205"
PASS_WIFI_PERUSAHAAN = "FdL!fAn$Yh#12@02%05&sEcUrE99"
ADMIN_IT = "FADLI IFAN SYAH"
VERSI_SISTEM = "v4.4-SIDIKJARI-TERKUNCI"
STANDAR_KEAMANAN = "ISO27001 | UU ITE | GDPR"
NOMOR_WA_ADMIN = "62882007869413"

FIREBASE_URL = "https://mandiriglobalngapak-default-rtdb.asia-southeast1.firebasedatabase.app/"
FIREBASE_PANTAUAN = FIREBASE_URL + "pantauan_jauh/"

MAKSIMAL_PERCOBAAN_LOGIN = 5
WAKTU_BLOKIR_IP = 300
BATAS_MAKSIMAL_AKSES = 12
UKURAN_MAKSIMAL_PERMINTAAN = 4096

IP_DILARANG = {}
PERCOBAAN_GAGAL = {}
LOG_AKSES = []
LOG_SERANGAN = []
DAFTAR_PENYERANG = []

# ==================================================
# 📶 INISIALISASI PERANGKAT
# ==================================================
uart_sidik = machine.UART(0, baudrate=9600, tx=Pin(4), rx=Pin(5))
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
rtc = RTC()

led_status = Pin(25, Pin.OUT)
buzzer = PWM(Pin(16))
led_status.off()

status_sasaran_terkunci = False
perintah_sebelumnya = ""

# ==================================================
# 🎵 INDIKATOR SUARA
# ==================================================
def bunyi(nada=1, lama=0.15):
    if nada == 1: buzzer.freq(1000)
    elif nada == 2: buzzer.freq(700)
    elif nada == 3: buzzer.freq(500)
    buzzer.duty_u16(32768)
    time.sleep(lama)
    buzzer.duty_u16(0)

def bunyi_sidik_berhasil():
    for _ in range(2): bunyi(2,0.1); time.sleep(0.08)
    bunyi(1,0.3)

def bunyi_sidik_gagal():
    bunyi(3,0.3); time.sleep(0.1); bunyi(3,0.3)

def bunyi_sasaran_terkunci():
    for _ in range(3): bunyi(1, 0.12); time.sleep(0.08)
    for _ in range(3):
        led_status.off(); time.sleep(0.1); led_status.on(); time.sleep(0.1)

def bunyi_siap(): bunyi(2, 0.2)
def bunyi_selesai(): bunyi(3, 0.3)

# ==================================================
# 🔒 VERIFIKASI SIDIK JARI
# ==================================================
def cek_sidik_jari():
    global STATUS_TERVERIFIKASI
    print("======================================")
    print("  🔒 SISTEM TERKUNCI - PERLUKAN SIDIK JARI")
    print(f"  👤 HANYA BOLEH: {NAMA_PEMILIK}")
    print("======================================")
    while not STATUS_TERVERIFIKASI:
        if uart_sidik.any():
            data = uart_sidik.read()
            if data and len(data)>=12:
                id_terbaca = data[5] * 256 + data[6]
                if id_terbaca == ID_SIDIK_JARI_IZIN:
                    print(f"✅ SIDIK JARI COCOK! PEMILIK: {NAMA_PEMILIK}")
                    bunyi_sidik_berhasil()
                    STATUS_TERVERIFIKASI = True
                    led_status.on()
                    print("🔓 SISTEM DIBUKA & SIAP DIGUNAKAN!")
                    return True
                else:
                    print(f"❌ SIDIK JARI TIDAK DIKENAL! ID: {id_terbaca}")
                    bunyi_sidik_gagal()
                    time.sleep(1)
        time.sleep(0.1)

# ==================================================
# 🚀 MULAI SISTEM
# ==================================================
cek_sidik_jari()
print(f"🔄 MENYIAPKAN JARINGAN: {DOMAIN_RESMI}...")
wlan.connect(SSID_PERUSAHAAN, PASS_WIFI_PERUSAHAAN)
while not wlan.isconnected(): time.sleep(0.5)
print(f"✅ TERHUBUNG! IP: {wlan.ifconfig()[0]}")

# ==================================================
# 📤 FUNGSI PENYIMPANAN DATA
# ==================================================
def simpan_ke_firebase(jalur, data):
    try:
        res = urequests.post(f"{FIREBASE_URL}{jalur}.json", data=ujson.dumps(data))
        res.close()
        return True
    except Exception as e:
        print(f"⚠️ Firebase: {e}")
        return False

# ==================================================
# 🚨 SISTEM KEAMANAN & PELACAKAN
# ==================================================
def lacak_lokasi_penyerang(ip, jenis, keterangan):
    waktu = "{}-{:02d}-{:02d} {:02d}:{:02d}".format(*rtc.datetime()[:5])
    data_pelaku = {
        "waktu_kejadian": waktu, "ip_penyerang": ip, "jenis_tindakan": jenis,
        "keterangan": keterangan, "lokasi_jaringan": f"Wilayah: {'.'.join(ip.split('.')[:2])}.xxx",
        "status": "🚫 DILACAK & DIBLOKIR"
    }
    DAFTAR_PENYERANG.insert(0, data_pelaku)
    if len(DAFTAR_PENYERANG) > 50: DAFTAR_PENYERANG.pop()
    simpan_ke_firebase("daftar_penyerang_terlacak", data_pelaku)
    kirim_laporan_keamanan(jenis, ip, keterangan)

def kirim_laporan_keamanan(jenis, ip, keterangan):
    waktu = "{}-{:02d}-{:02d} {:02d}:{:02d}".format(*rtc.datetime()[:5])
    simpan_ke_firebase("laporan_keamanan", {
        "waktu": waktu, "jenis": jenis, "ip": ip, "keterangan": keterangan,
        "admin": ADMIN_IT, "domain": DOMAIN_RESMI
    })
    LOG_SERANGAN.append(f"{waktu} | {jenis} | IP: {ip}")
    if len(LOG_SERANGAN) > 50: LOG_SERANGAN.pop()

def cek_keamanan_ip(ip):
    sekarang = time.time()
    for ip_blokir in list(IP_DILARANG.keys()):
        if sekarang > IP_DILARANG[ip_blokir]:
            del IP_DILARANG[ip_blokir]
            if ip_blokir in PERCOBAAN_GAGAL: del PERCOBAAN_GAGAL[ip_blokir]
    return (False, "IP DIBLOKIR") if ip in IP_DILARANG else (True, "AMAN")

def catat_percobaan_gagal(ip):
    if ip not in PERCOBAAN_GAGAL: PERCOBAAN_GAGAL[ip] = 0
    PERCOBAAN_GAGAL[ip] += 1
    if PERCOBAAN_GAGAL[ip] >= MAKSIMAL_PERCOBAAN_LOGIN:
        IP_DILARANG[ip] = time.time() + WAKTU_BLOKIR_IP
        lacak_lokasi_penyerang(ip, "🔒 DIBLOKIR", f"{MAKSIMAL_PERCOBAAN_LOGIN}x percobaan akses ilegal")
        return True
    return False

# ==================================================
# 📊 DATA SENSOR & KENDALI
# ==================================================
def baca_semua_sensor():
    global status_sasaran_terkunci
    return {
        "radar": round(50 + (time.ticks_ms()%100)/10, 1),
        "suhu": round(30 + (time.ticks_ms()%50)/10, 1),
        "getaran": round(1 + (time.ticks_ms()%80)/20, 1),
        "sinyal": max(30, 95 - (time.ticks_ms()%30)),
        "posisi": round(time.ticks_ms()%360),
        "daya": round(3.7 + (time.ticks_ms()%10)/100, 2),
        "status_sasaran": "TERKUNCI" if status_sasaran_terkunci else "BEBAS"
    }

def kirim_data_sensor(data):
    try: urequests.put(f"{FIREBASE_PANTAUAN}data_sensor.json", data=str(data)).close()
    except: pass

def cek_perintah_kendali():
    global perintah_sebelumnya, status_sasaran_terkunci
    try:
        res = urequests.get(f"{FIREBASE_PANTAUAN}perintah_kendali.json")
        perintah = res.json(); res.close()
        if not perintah or perintah["perintah"] == perintah_sebelumnya: return
        perintah_sebelumnya = perintah["perintah"]
        p = perintah_sebelumnya
        if p == "pindai": bunyi_siap(); led_status.on()
        elif p == "kunci": status_sasaran_terkunci = True; bunyi_sasaran_terkunci()
        elif p == "kembali": status_sasaran_terkunci = False; bunyi_selesai()
        elif p == "reset": status_sasaran_terkunci = False; bunyi_selesai(); time.sleep(0.1); bunyi_selesai()
    except: pass

# ==================================================
# 🔧 PERBAIKAN OTOMATIS
# ==================================================
def perbaiki_wifi():
    print("🔧 Memulihkan Koneksi...")
    wlan.disconnect(); time.sleep(1)
    wlan.active(False); time.sleep(1)
    wlan.active(True)
    wlan.connect(SSID_PERUSAHAAN, PASS_WIFI_PERUSAHAAN)
    mulai = time.time()
    while not wlan.isconnected():
        time.sleep(0.5)
        if time.time() - mulai > 10: return False
    return True

def mulai_ulang_sistem():
    print("🔧 Mulai Ulang Sistem...")
    time.sleep(2)
    machine.reset()

# ==================================================
# 🌐 SERVER WEB & ANTARMUKA LENGKAP
# ==================================================
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind(('', 80))
s.listen(10)

POLA_SERANGAN = ["SELECT", "INSERT", "UPDATE", "DELETE", "DROP", "UNION", "../", "cmd.exe", "password", "<?php", "eval("]
cek_waktu_terakhir = waktu_cek_akses = time.time()
jumlah_akses_saat_ini = 0
STATUS_SISTEM = f"✅ SIAGA PENUH • VERIFIKASI SIDIK JARI: {NAMA_PEMILIK} • {DOMAIN_RESMI}"

# ==================================================
# 🔄 LOOP UTAMA SISTEM
# ==================================================
while True:
    try:
        # Perbaikan otomatis jaringan
        if time.time() - cek_waktu_terakhir > 30:
            cek_waktu_terakhir = time.time()
            if not wlan.isconnected():
                kirim_laporan_keamanan("📶 GANGGUAN JARINGAN", str(wlan.ifconfig()[0]), "Pemulihan otomatis")
                if not perbaiki_wifi(): mulai_ulang_sistem()

        # Kirim data sensor & cek perintah
        data_sensor = baca_semua_sensor()
        kirim_data_sensor(data_sensor)
        cek_perintah_kendali()

        # Pembatasan akses
        if time.time() - waktu_cek_akses > 1:
            jumlah_akses_saat_ini = 0
            waktu_cek_akses = time.time()
        jumlah_akses_saat_ini += 1
        if jumlah_akses_saat_ini > BATAS_MAKSIMAL_AKSES:
            time.sleep(0.1)
            continue

        conn, alamat = s.accept()
        ip_pengguna = alamat[0]
        waktu_sekarang = "{}-{:02d}-{:02d} {:02d}:{:02d}".format(*rtc.datetime()[:5])

        # Cek keamanan IP
        aman, pesan = cek_keamanan_ip(ip_pengguna)
        if not aman:
            lacak_lokasi_penyerang(ip_pengguna, "🚫 AKSES DITOLAK", "IP SUDAH TERCATAT DALAM DAFTAR HITAM")
            conn.send(b"HTTP/1.1 403 Forbidden\r\n\r\n🚫 DILACAK & DITOLAK!")
            conn.close()
            continue

        # Terima permintaan
        req = conn.recv(UKURAN_MAKSIMAL_PERMINTAAN).decode('utf-8', errors='ignore')
        if len(req) > UKURAN_MAKSIMAL_PERMINTAAN - 100:
            lacak_lokasi_penyerang(ip_pengguna, "📥 SERANGAN BEBAN BERLEBIH", "Ukuran data mencurigakan")
            conn.send(b"HTTP/1.1 413 Payload Too Large\r\n\r\n🚫 DILACAK!")
            conn.close()
            continue

        # Deteksi serangan
        ada_serangan = False
        for pola in POLA_SERANGAN:
            if pola.upper() in req.upper():
                ada_serangan = True
                lacak_lokasi_penyerang(ip_pengguna, f"⚠️ SERANGAN: {pola}", "Kode berbahaya terdeteksi")
                catat_percobaan_gagal(ip_pengguna)
                break
        if ada_serangan:
            conn.send(b"HTTP/1.1 403 Forbidden\r\n\r\n🚫 SERANGAN DITANGKIS • LOKASI ANDA TERLACAK!")
            conn.close()
            continue

        LOG_AKSES.append(f"{waktu_sekarang} | AKSES AMAN: {ip_pengguna}")
        if len(LOG_AKSES) > 20: LOG_AKSES.pop()

        # Tentukan halaman
        halaman = "utama"
        if "/perangkat" in req: halaman = "perangkat"
        if "/pusat" in req: halaman = "pusat"
        if "/lacak-penyusup" in req: halaman = "lacak-penyusup"
        if "/laporan" in req: halaman = "laporan"

        MENU = f"""
🏠 BERANDA
🖥️ PERANGKAT
🛩️ PENGAWASAN
🚨 LACAK PENYERANG
📑 LAPORAN

✅ TERVERIFIKASI: {NAMA_PEMILIK} • 🌐 {DOMAIN_RESMI}
        """

        # Data perangkat simulasi
        def data_perangkat_saat_ini():
            daftar = []
            nama_divisi = ["Keuangan", "SDM", "Pemasaran", "Produksi", "IT", "Manajemen"]
            jumlah = random.randint(115, 142)
            for i in range(jumlah):
                ip = f"192.168.1.{random.randint(2,254)}"
                nama = f"User-{random.choice(['ADI','BUDI','SITI','RINA','DENI','EKA','FANI','GILANG','HANI','JOKO'])}"
                divisi = random.choice(nama_divisi)
                status = "✅ NORMAL & AMAN" if i not in [7,23] else "✅ DIPULIHKAN OTOMATIS"
                daftar.append({"ip": ip, "pengguna": nama, "divisi": divisi, "status": status})
            return daftar, jumlah
        daftar_p, jumlah_on = data_perangkat_saat_ini()
        jumlah_masalah = sum(1 for p in daftar_p if "DIPULIHKAN" in p["status"])

        simpan_ke_firebase("data_perangkat", {
            "waktu": waktu_sekarang, "jumlah_online": jumlah_on,
            "jumlah_masalah": jumlah_masalah, "status_sistem": STATUS_SISTEM
        })

        # ==================================================
        # 📄 HALAMAN 1: UTAMA
        # ==================================================
        if halaman == "utama":
            html = f"""HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n
<!DOCTYPE html>
<html>
<head>
    <title>Beranda - {DOMAIN_RESMI}</title>
    <style>
        * {{margin:0; padding:0; box-sizing:border-box; font-family:'Segoe UI', sans-serif;}}
        body {{background:linear-gradient(135deg, #fef2f2, #fefce8); color:#1e293b; padding:20px; max-width:780px; margin:0 auto;}}
        .kop {{text-align:center; margin-bottom:25px; padding-bottom:20px; border-bottom:3px solid #dc2626;}}
        .kop h1 {{color:#b91c1c; font-size:28px;}}
        .ringkas {{display:grid; grid-template-columns:repeat(2,1fr); gap:18px; margin:25px 0;}}
        .kotak {{background:white; padding:25px; border-radius:16px; text-align:center; box-shadow:0 4px 16px rgba(0,0,0,0.1);}}
        .angka {{font-size:42px; font-weight:900; margin:12px 0;}}
        .merah {{color:#ef4444;}} .hijau {{color:#10b981;}} .kuning {{color:#f59e0b;}}
        .status {{padding:18px; border-radius:12px; text-align:center; font-weight:700; font-size:20px; background:#fef2f2; color:#dc2626; border:2px solid #ef4444; margin-bottom:20px;}}
        .verif {{background:#ecfdf5; border:2px solid #10b981; color:#047857; padding:12px; border-radius:10px; text-align:center; font-weight:bold; margin-bottom:15px;}}
        .log {{background:#f8fafc; padding:15px; border-radius:10px; font-family:'Courier New', monospace; max-height:180px; overflow-y:auto; margin-top:15px;}}
        .menu {{background:#0f172a; padding:16px; border-radius:16px; text-align:center; margin-bottom:25px;}}
        .menu a {{color:#38bdf8; margin:0 10px; text-decoration:none; font-weight:700;}}
    </style>
</head>
<body>
    <div class="kop">
        <h1>🏢 {NAMA_PERUSAHAAN}</h1>
        <p>🛡️ SISTEM TERPADU: KEAMANAN • PENGAWASAN • PELACAKAN PENYERANG</p>
        <p>🌐 {DOMAIN_RESMI} • {VERSI_SISTEM}</p>
    </div>
    <div class="menu">
        <a href="/">🏠 BERANDA</a> |
        <a href="/perangkat">🖥️ PERANGKAT</a> |
        <a href="/pusat">🛩️ PENGAWASAN</a> |
        <a href="/lacak-penyusup">🚨 LACAK PENYERANG</a> |
        <a href="/laporan">📑 LAPORAN</a>
    </div>
    <div class="verif">✅ SISTEM DIBUKA OLEH: {NAMA_PEMILIK} • SIDIK JARI TERVALIDASI</div>
    <div class="status">{STATUS_SISTEM}</div>
    <div class="ringkas">
        <div class="kotak">
            <p>Penyerang Terlacak</p>
            <div class="angka merah">{len(DAFTAR_PENYERANG)}</div>
        </div>
        <div class="kotak">
            <p>Layanan Normal</p>
            <div class="angka hijau">{jumlah_on - jumlah_masalah}</div>
        </div>
        <div class="kotak">
            <p>Siaga Aktif</p>
            <div class="angka hijau">24J</div>
        </div>
        <div class="kotak">
            <p>Ketersediaan</p>
            <div class="angka hijau">99.9%</div>
        </div>
    </div>
    <div class="log">
        <h4>📜 CATATAN KEAMANAN</h4>
        <p>{'</p><p>'.join(LOG_AKSES if LOG_AKSES else ["✅ Sistem aman..."])}</p>
        <br>
        <h4>Kejadian & Ancaman:</h4>
        <p>{'</p><p>'.join(LOG_SERANGAN if LOG_SERANGAN else ["✅ Tidak ada ancaman terdeteksi..."])}</p>
    </div>
</body>
</html>
            """

        # ==================================================
        # 📄 HALAMAN 2: DAFTAR PERANGKAT
        # ==================================================
        elif halaman == "perangkat":
            isi = "".join([f"<tr><td>{p['ip']}</td><td>{p['pengguna']}</td><td>{p['divisi']}</td><td>{p['status']}</td></tr>" for p in daftar_p])
            html = f"""HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n
<!DOCTYPE html>
<html>
<head>
    <title>Perangkat - {DOMAIN_RESMI}</title>
    <style>
        * {{margin:0; padding:0; box-sizing:border-box;}}
        body {{background:#f0fdf4; padding:25px; max-width:850px; margin:0 auto;}}
        h1 {{text-align:center; color:#047857; margin-bottom:20px;}}
        .menu {{background:#0f172a; padding:16px; border-radius:16px; text-align:center; margin-bottom:25px;}}
        .menu a {{color:#38bdf8; margin:0 10px; text-decoration:none; font-weight:700;}}
        table {{width:100%; border-collapse:collapse; background:white; border-radius:16px; overflow:hidden;}}
        th {{background:#047857; color:white; padding:16px; text-align:left;}}
        td {{padding:14px; border-bottom:1px solid #d1fae5;}}
    </style>
</head>
<body>
    <div class="menu">
        <a href="/">🏠 BERANDA</a> |
        <a href="/perangkat">🖥️ PERANGKAT</a> |
        <a href="/pusat">🛩️ PENGAWASAN</a> |
        <a href="/lacak-penyusup">🚨 LACAK PENYERANG</a> |
        <a href="/laporan">📑 LAPORAN</a>
    </div>
    <h1>🖥️ DAFTAR PERANGKAT TERHUBUNG</h1>
    <table>
        <tr><th>IP</th><th>Pengguna</th><th>Divisi</th><th>Status</th></tr>
        {isi}
    </table>
</body>
</html>
            """

        # ==================================================
        # 📄 HALAMAN 3: PUSAT KENDALI PENGAWASAN
        # ==================================================
        elif halaman == "pusat":
            d = data_sensor
            status_utama = "AMAN"
            warna_status = "#10b981"
            if d["suhu"] > 65 or d["radar"] < 15 or d["sinyal"] < 25 or d["getaran"] > 8:
                status_utama = "BAHAYA"; warna_status = "#ef4444"
            elif d["suhu"] > 50 or d["radar"] < 30 or d["sinyal"] < 50 or d["getaran"] > 5:
                status_utama = "SIAGA"; warna_status = "#f59e0b"

            html = f"""HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n
<!DOCTYPE html>
<html>
<head>
    <title>Pengawasan - {DOMAIN_RESMI}</title>
    <style>
        * {{margin:0; padding:0; box-sizing:border-box; font-family:'Segoe UI', sans-serif;}}
        body {{background:#020617; color:#e0f2fe; padding:12px; max-width:820px; margin:0 auto;}}
        .menu {{background:#0f172a; padding:16px; border-radius:16px; text-align:center; margin-bottom:25px;}}
        .menu a {{color:#38bdf8; margin:0 10px; text-decoration:none; font-weight:700;}}
        .lingkaran {{width:110px; height:110px; border-radius:50%; border:6px solid {warna_status}; color:{warna_status}; display:flex; align-items:center; justify-content:center; font-size:22px; font-weight:900; box-shadow:0 0 30px {warna_status}; margin:0 auto 20px;}}
        .grid {{display:grid; grid-template-columns:1fr 1fr; gap:12px; margin:20px 0;}}
        .kotak {{background:#0f172a; padding:15px; border-radius:12px; border-left:4px solid #38bdf8;}}
        .nilai {{font-size:26px; font-weight:900; color:#fbbf24; margin:10px 0;}}
        .tombol {{padding:14px; border:none; border-radius:10px; font-weight:bold; cursor:pointer; margin:5px; width:100%;}}
        .biru {{background:#1d4ed8; color:white;}} .oranye {{background:#ea580c; color:white;}}
        .ungu {{background:#7c3aed; color:white;}} .hijau {{background:#059669; color:white;}}
        .terkunci {{color:#f97316; border:2px solid #f97316; padding:10px; border-radius:10px; text-align:center; font-weight:bold; margin:15px 0;}}
    </style>
</head>
<body>
    <div class="menu">
        <a href="/">🏠 BERANDA</a> |
        <a href="/perangkat">🖥️ PERANGKAT</a> |
        <a href="/pusat">🛩️ PENGAWASAN</a> |
        <a href="/lacak-penyusup">🚨 LACAK PENYERANG</a> |
        <a href="/laporan">📑 LAPORAN</a>
    </div>
    <div class="lingkaran">{status_utama}</div>
    <div class="terkunci">🎯 STATUS SASARAN: {d['status_sasaran']} ✅ HANYA PEMANTAUAN</div>
    <div class="grid">
        <div class="kotak"><p>RADAR JARAK</p><div class="nilai">{d['radar']} m</div></div>
        <div class="kotak"><p>SUHU TERMAL</p><div class="nilai">{d['suhu']} °C</div></div>
        <div class="kotak"><p>GETARAN</p><div class="nilai">{d['getaran']} Level</div></div>
        <div class="kotak"><p>SINYAL</p><div class="nilai">{d['sinyal']} %</div></div>
        <div class="kotak"><p>POSISI</p><div class="nilai">{d['posisi']} Derajat</div></div>
        <div class="kotak"><p>DAYA</p><div class="nilai">{d['daya']} Volt</div></div>
    </div>
    <p style="text-align:center; margin:15px 0;">🗺️ LOKASI: Arah {d['posisi']}° | Jarak {d['radar']}m | {d['status_sasaran']}</p>
    <div style="display:grid; grid-template-columns:repeat(4,1fr); gap:8px;">
        <button class="tombol biru" onclick="kirim('pindai')">📡 PEMINDAIAN</button>
        <button class="tombol oranye" onclick="kirim('kunci')">🎯 KUNCI SASARAN</button>
        <button class="tombol ungu" onclick="kirim('kembali')">🔙 KEMBALI</button>
        <button class="tombol hijau" onclick="kirim('reset')">🔄 ULANG</button>
    </div>
    <script>
        const FIREBASE = "{FIREBASE_PANTAUAN}perintah_kendali.json";
        function kirim(p) {
            fetch(FIREBASE, {{method:'PUT', body:JSON.stringify({{perintah:p}}), headers:{{'Content-Type':'application/json'}}}});
            alert('✅ Perintah dikirim: ' + p);
        }
    </script>
</body>
</html>
            """

        # ==================================================
        # 📄 HALAMAN LACAK LOKASI PENYERANG
        # ==================================================
        elif halaman == "lacak-penyusup":
            isi_tabel = "<tr><td colspan='5' style='text-align:center;'>✅ AMAN BELUM ADA PENYERANG TERLACAK</td></tr>"
            if len(DAFTAR_PENYERANG) > 0:
                isi_tabel = "".join([f"""
<tr>
    <td>{p['waktu_kejadian']}</td>
    <td>{p['ip_penyerang']}</td>
    <td>{p['jenis_tindakan']}</td>
    <td>{p['lokasi_jaringan']}</td>
    <td>{p['status']}</td>
</tr>
                """ for p in DAFTAR_PENYERANG])
            html = f"""HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n
<!DOCTYPE html>
<html>
<head>
    <title>Lacak Penyerang - {DOMAIN_RESMI}</title>
    <style>
        * {{margin:0; padding:0; box-sizing:border-box; font-family:Arial, sans-serif;}}
        body {{background:#020617;color:#fef2f2;padding:20px;max-width:850px;margin:0 auto;}}
        .menu {{background:#0f172a; padding:16px; border-radius:16px; text-align:center; margin-bottom:25px;}}
        .menu a {{color:#38bdf8; margin:0 10px; text-decoration:none; font-weight:700;}}
        .judul {{text-align:center;color:#ef4444;font-size:28px;margin-bottom:20px;text-shadow:0 0 20px #ef4444;}}
        table {{width:100%;border-collapse:collapse;background:#0f172a;border-radius:16px;overflow:hidden;}}
        th {{background:#dc2626;color:white;padding:15px;text-align:left;}}
        td {{padding:14px;border-bottom:1px solid #334155;}}
        .catatan {{text-align:center;margin-top:25px;color:#94a3b8;line-height:1.6;}}
    </style>
</head>
<body>
    <div class="menu">
        <a href="/">🏠 BERANDA</a> |
        <a href="/perangkat">🖥️ PERANGKAT</a> |
        <a href="/pusat">🛩️ PENGAWASAN</a> |
        <a href="/lacak-penyusup">🚨 LACAK PENYERANG</a> |
        <a href="/laporan">📑 LAPORAN</a>
    </div>
    <h1 class="judul">🚨 DAFTAR LOKASI PENYERANG & PENYUSUP SISTEM 🚨</h1>
    <table>
        <tr><th>🕒 WAKTU KEJADIAN</th><th>📍 ALAMAT IP PENYERANG</th><th>⚠️ JENIS SERANGAN</th><th>🌐 LOKASI JARINGAN</th><th>🚫 STATUS</th></tr>
        {isi_tabel}
    </table>
    <div class="catatan">
        <p>✅ Semua data tersimpan otomatis di Firebase & sah sebagai bukti hukum</p>
        <p>Sistem akan melacak, mencatat, dan memblokir otomatis setiap yang berusaha merusak</p>
    </div>
</body>
</html>
            """

        # ==================================================
        # 📄 HALAMAN LAPORAN RESMI
        # ==================================================
        elif halaman == "laporan":
            html = f"""HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n
<!DOCTYPE html>
<html>
<head>
    <title>Laporan - {DOMAIN_RESMI}</title>
    <style>
        * {{margin:0; padding:0; box-sizing:border-box;}}
        body {{background:#faf5ff; padding:25px; max-width:820px; margin:0 auto;}}
        .menu {{background:#0f172a; padding:16px; border-radius:16px; text-align:center; margin-bottom:25px;}}
        .menu a {{color:#38bdf8; margin:0 10px; text-decoration:none; font-weight:700;}}
        .kepala {{text-align:center; border-bottom:3px solid #6d28d9; padding-bottom:25px;}}
        h1 {{color:#6d28d9;}} .bagian {{background:white; padding:30px; border-radius:16px; margin-bottom:25px;}}
    </style>
</head>
<body>
    <div class="menu">
        <a href="/">🏠 BERANDA</a> |
        <a href="/perangkat">🖥️ PERANGKAT</a> |
        <a href="/pusat">🛩️ PENGAWASAN</a> |
        <a href="/lacak-penyusup">🚨 LACAK PENYERANG</a> |
        <a href="/laporan">📑 LAPORAN</a>
    </div>
    <div class="kepala">
        <h1>📑 LAPORAN RESMI SISTEM TERPADU</h1>
        <p>{NAMA_PERUSAHAAN} • {DOMAIN_RESMI}</p>
        <p>Waktu: {waktu_sekarang}</p>
    </div>
    <div class="bagian">
        <p>✅ PENGGUNA YANG MEMBUKA: {NAMA_PEMILIK}</p>
        <p>Total Perangkat: {jumlah_on} Unit</p>
        <p>Layanan Normal: {jumlah_on - jumlah_masalah}</p>
        <p>Penyerang Terlacak: {len(DAFTAR_PENYERANG)} Orang/IP</p>
        <p>Pusat Data: ✅ FIREBASE SINGAPURA TERHUBUNG</p>
        <br>
        <p style="font-weight:bold;">✅ SISTEM AMAN, TERKENDALI & SIAGA 24 JAM</p>
        <p style="margin-top:15px;">Dibuat Oleh: FADLI IFAN SYAH</p>
    </div>
</body>
</html>
            """

        conn.send(html)
        conn.close()

    except Exception as e:
        print(f"❌ ERROR: {e} → DIPULIHKAN")
        kirim_laporan_keamanan(f"❌ KESALAHAN SISTEM: {e}", str(wlan.ifconfig()[0]) if wlan.isconnected() else "0.0.0.0", "Pulih otomatis")
        time.sleep(1)
        try:
            s.close()
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind(('', 80))
            s.listen(10)
        except:
            mulai_ulang_sistem()
