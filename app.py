import streamlit as st
import zipfile
import re
from lxml import etree
import io

st.set_page_config(page_title="KMZ Renamer 1GB", page_icon="📍")

st.title("📍 KMZ Homepass Renamer")
st.info("Batas upload telah ditingkatkan menjadi 1GB.")

uploaded_file = st.file_uploader("Upload file KMZ Anda (Maks 1GB)", type=["kmz"])

if uploaded_file is not None:
    with st.spinner('Sedang memproses file besar, mohon tunggu...'):
        try:
            # Baca file KMZ
            with zipfile.ZipFile(uploaded_file, 'r') as kmz:
                kml_content = kmz.read('doc.kml')
                
                tree = etree.fromstring(kml_content)
                namespaces = {'kml': 'http://www.opengis.net/kml/2.2'}
                names = tree.xpath('//kml:name', namespaces=namespaces)
                
                log_updates = []
                count = 0
                
                for name in names:
                    if name.text and "No." in name.text:
                        old_name = name.text
                        new_name = re.sub(r'No\.\s*', '', old_name).strip()
                        name.text = new_name
                        log_updates.append(f"Berhasil: {old_name} ➜ {new_name}")
                        count += 1
                
                # Bungkus ulang file
                new_kml_content = etree.tostring(tree, pretty_print=True, xml_declaration=True, encoding='UTF-8')
                
                output_kmz = io.BytesIO()
                with zipfile.ZipFile(output_kmz, 'w', zipfile.ZIP_DEFLATED) as new_kmz:
                    new_kmz.writestr('doc.kml', new_kml_content)
                    # Copy file pendukung (gambar/ikon) jika ada
                    for item in kmz.infolist():
                        if item.filename != 'doc.kml':
                            new_kmz.writestr(item, kmz.read(item.filename))
                
                st.success(f"Selesai! {count} titik telah diubah.")
                
                # Tombol Download
                st.download_button(
                    label="📥 Unduh KMZ Hasil Rename",
                    data=output_kmz.getvalue(),
                    file_name=f"Renamed_{uploaded_file.name}",
                    mime="application/vnd.google-earth.kmz"
                )

                # Menampilkan Log untuk verifikasi keamanan data
                with st.expander("Lihat Rincian Perubahan (Log)"):
                    for log in log_updates[:100]: # Batasi 100 pertama agar tidak berat
                        st.text(log)
                    if len(log_updates) > 100:
                        st.text(f"... dan {len(log_updates) - 100} data lainnya.")

        except Exception as e:
            st.error(f"Terjadi kesalahan: {e}")