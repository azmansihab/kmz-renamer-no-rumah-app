import streamlit as st
import zipfile
import re
from lxml import etree
import io

st.set_page_config(page_title="KMZ Renamer Pro", page_icon="📍")

st.title("📍 KMZ Homepass Renamer")
st.markdown("---")

uploaded_file = st.file_uploader("Upload file KMZ Anda (Maks 1GB)", type=["kmz"])

if uploaded_file is not None:
    with st.spinner('Sedang memproses...'):
        try:
            # Membaca KMZ
            input_kmz = zipfile.ZipFile(uploaded_file, 'r')
            
            # 1. Cari file KML di dalam KMZ (tidak harus doc.kml)
            kml_filename = next((f for f in input_kmz.namelist() if f.endswith('.kml')), None)
            
            if not kml_filename:
                st.error("Tidak ditemukan file KML di dalam paket KMZ ini.")
            else:
                kml_content = input_kmz.read(kml_filename)
                
                # 2. Parsing dengan recover=True untuk menghindari error struktur XML
                parser = etree.XMLParser(recover=True, remove_blank_text=True)
                tree = etree.fromstring(kml_content, parser=parser)
                
                # 3. Gunakan xpath yang lebih fleksibel terhadap Namespace
                # Ini akan mencari semua tag <name> tanpa peduli prefix kml: nya
                names = tree.xpath('//*[local-name()="name"]')
                
                log_updates = []
                count = 0
                
                for name in names:
                    if name.text:
                        # Pola Regex yang lebih kuat: cari "No." atau "No " (case insensitive)
                        # Menghapus "No." diikuti spasi atau angka
                        if re.search(r'No\.\s*|No\s+', name.text, re.IGNORECASE):
                            old_name = name.text
                            # Menghapus kata "No." atau "No" dan menyisakan sisa stringnya
                            new_name = re.sub(r'(?i)No\.\s*|No\s+', '', old_name).strip()
                            name.text = new_name
                            log_updates.append(f"Ubah: {old_name} ➜ {new_name}")
                            count += 1
                
                if count == 0:
                    st.warning("File terbaca, tetapi tidak ditemukan label dengan format 'No.' di dalamnya.")
                    # Debug: Tampilkan 5 nama pertama yang ditemukan untuk pengecekan
                    st.write("Contoh label yang ditemukan di file Anda:")
                    for n in names[:5]:
                        st.code(n.text)
                else:
                    # 4. Bungkus ulang ke KMZ baru
                    new_kml_content = etree.tostring(tree, pretty_print=True, xml_declaration=True, encoding='UTF-8')
                    
                    output_kmz = io.BytesIO()
                    with zipfile.ZipFile(output_kmz, 'w', zipfile.ZIP_DEFLATED) as new_zip:
                        # Masukkan KML yang sudah di-rename
                        new_zip.writestr(kml_filename, new_kml_content)
                        
                        # Copy semua file lain (gambar, icon, folder) agar KMZ tidak rusak
                        for item in input_kmz.infolist():
                            if item.filename != kml_filename:
                                new_zip.writestr(item, input_kmz.read(item.filename))
                    
                    st.success(f"Berhasil merename {count} titik!")
                    
                    st.download_button(
                        label="📥 Unduh Hasil Rename",
                        data=output_kmz.getvalue(),
                        file_name=f"Fixed_{uploaded_file.name}",
                        mime="application/vnd.google-earth.kmz"
                    )
                    
                    with st.expander("Lihat Log Perubahan"):
                        for log in log_updates[:50]:
                            st.text(log)

            input_kmz.close()

        except Exception as e:
            st.error(f"Terjadi kesalahan sistem: {e}")