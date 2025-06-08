Penjelasan Model:
Model 3D yang saya buat adalah sebuah robot sederhana yang berada di atas sebuah meja, model ini menggunakan beberapa bangun yang terdiri dari beberapa bagian seperti:

1. Kubus -> untuk meja, badan robot, dan lengan robot. (Translasi, skala)
2. Silinder -> untuk kaki" meja dan leher tobot (Translasi, skala)
3. Bola -> untuk kepala robot, mata, tangan (Translasi, skala)
4. Kerucut -> untuk anthena diatas kepala robot (Translasi, skala)

🪑 Meja
Top Table (Cube):
Translasi: ditempatkan di ketinggian z = 1
Skala: panjang 6, lebar 3, tebal 0.3
4 Kaki Meja (Cylinder):
Translasi: ke 4 sudut meja
Skala: tinggi 1, radius 0.2

🤖 Robot
Badan (Cube):
Skala: [1, 0.6, 1]
Translasi: diletakkan di atas meja
Leher (Cylinder):
Skala: tinggi 0.2, radius 0.1
Kepala (Sphere):
Translasi: di atas leher
Radius: 0.3
Mata (2 Sphere kecil):
Translasi: posisi simetris di depan kepala
Radius: 0.05
Antena (Cone):
Translasi: atas kepala
Skala: tinggi 0.3, radius 0.05
Tangan (Cube + Sphere):
Lengan (Cube): translasi ke sisi badan
Tangan (Sphere): translasi ujung lengan, radius 0.075

▶️ Cara Menjalankan Program di vscode
Di Komputer Lokal (Python):
1. Pastikan Python sudah terinstall.
2. Install library plotly dan numpy:
    pip install plotly -> perintah 1 
    pip install numpy -> perintah 2
Jalankan program dengan mengetikkan perintah berikut di terminal atau command prompt

3. Jalankan file main.py:
    python main.py

Scene Root
├── Meja
│   ├── Top Table
│   ├── Kaki 1–4
└── Robot
    ├── Badan
    ├── Leher
    ├── Kepala
    │   ├── Mata kiri
    │   ├── Mata kanan
    │   └── Antena
    └── Tangan kiri & kanan
