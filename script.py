# ===== SOAP SERVER (menggunakan Flask + lxml) =====
from flask import Flask, request, Response
import xml.etree.ElementTree as ET
from xml.dom import minidom
import json

app = Flask(__name__)

# Simulasi database mahasiswa
mahasiswa_db = {
    "12345": {"nim": "12345", "nama": "Ahmad Rizki", "jurusan": "Teknik Informatika", "ipk": "3.75"},
    "67890": {"nim": "67890", "nama": "Siti Nurhaliza", "jurusan": "Sistem Informasi", "ipk": "3.85"},
    "11111": {"nim": "11111", "nama": "Budi Santoso", "jurusan": "Teknik Komputer", "ipk": "3.60"}
}

def create_soap_response(data, operation):
    """Membuat response SOAP XML"""
    soap_env = ET.Element("soap:Envelope")
    soap_env.set("xmlns:soap", "http://schemas.xmlsoap.org/soap/envelope/")
    soap_env.set("xmlns:mhs", "http://mahasiswa.service/")
    
    soap_body = ET.SubElement(soap_env, "soap:Body")
    
    if operation == "get_mahasiswa":
        response = ET.SubElement(soap_body, "mhs:getMahasiswaResponse")
        if data:
            mahasiswa = ET.SubElement(response, "mahasiswa")
            ET.SubElement(mahasiswa, "nim").text = data["nim"]
            ET.SubElement(mahasiswa, "nama").text = data["nama"]
            ET.SubElement(mahasiswa, "jurusan").text = data["jurusan"]
            ET.SubElement(mahasiswa, "ipk").text = data["ipk"]
        else:
            ET.SubElement(response, "message").text = "Data tidak ditemukan"
    
    elif operation == "tambah_mahasiswa":
        response = ET.SubElement(soap_body, "mhs:tambahMahasiswaResponse")
        ET.SubElement(response, "message").text = data
    
    # Format XML dengan indentasi
    xml_str = ET.tostring(soap_env, encoding='unicode')
    dom = minidom.parseString(xml_str)
    return dom.toprettyxml(indent="  ")

def parse_soap_request(xml_data):
    """Parse SOAP request XML"""
    try:
        root = ET.fromstring(xml_data)
        
        # Namespace untuk SOAP
        ns = {
            'soap': 'http://schemas.xmlsoap.org/soap/envelope/',
            'mhs': 'http://mahasiswa.service/'
        }
        
        body = root.find('.//soap:Body', ns)
        
        # Cek operasi yang diminta
        if body.find('.//mhs:getMahasiswa', ns) is not None:
            nim_elem = body.find('.//nim')
            nim = nim_elem.text if nim_elem is not None else ""
            return "get_mahasiswa", {"nim": nim}
        
        elif body.find('.//mhs:tambahMahasiswa', ns) is not None:
            mahasiswa_elem = body.find('.//mahasiswa')
            if mahasiswa_elem is not None:
                nim = mahasiswa_elem.find('nim').text
                nama = mahasiswa_elem.find('nama').text
                jurusan = mahasiswa_elem.find('jurusan').text
                ipk = mahasiswa_elem.find('ipk').text
                return "tambah_mahasiswa", {"nim": nim, "nama": nama, "jurusan": jurusan, "ipk": ipk}
        
        return None, None
    except Exception as e:
        print(f"Error parsing SOAP request: {e}")
        return None, None

@app.route('/mahasiswa', methods=['POST'])
def soap_service():
    """Endpoint SOAP service"""
    try:
        xml_data = request.data.decode('utf-8')
        operation, params = parse_soap_request(xml_data)
        
        if operation == "get_mahasiswa":
            nim = params["nim"]
            mahasiswa = mahasiswa_db.get(nim)
            response_xml = create_soap_response(mahasiswa, operation)
            
        elif operation == "tambah_mahasiswa":
            nim = params["nim"]
            mahasiswa_db[nim] = params
            message = f"Mahasiswa {params['nama']} dengan NIM {nim} berhasil ditambahkan"
            response_xml = create_soap_response(message, operation)
            
        else:
            response_xml = create_soap_response("Operasi tidak dikenal", "error")
        
        return Response(response_xml, mimetype='text/xml')
    
    except Exception as e:
        error_response = create_soap_response(f"Error: {str(e)}", "error")
        return Response(error_response, mimetype='text/xml')

@app.route('/wsdl')
def wsdl():
    """Endpoint untuk WSDL"""
    wsdl_content = """<?xml version="1.0" encoding="UTF-8"?>
<definitions xmlns="http://schemas.xmlsoap.org/wsdl/"
             xmlns:soap="http://schemas.xmlsoap.org/wsdl/soap/"
             xmlns:tns="http://mahasiswa.service/"
             targetNamespace="http://mahasiswa.service/">
    
    <types>
        <schema xmlns="http://www.w3.org/2001/XMLSchema"
                targetNamespace="http://mahasiswa.service/">
            <element name="getMahasiswa">
                <complexType>
                    <sequence>
                        <element name="nim" type="string"/>
                    </sequence>
                </complexType>
            </element>
            <element name="tambahMahasiswa">
                <complexType>
                    <sequence>
                        <element name="mahasiswa">
                            <complexType>
                                <sequence>
                                    <element name="nim" type="string"/>
                                    <element name="nama" type="string"/>
                                    <element name="jurusan" type="string"/>
                                    <element name="ipk" type="string"/>
                                </sequence>
                            </complexType>
                        </element>
                    </sequence>
                </complexType>
            </element>
        </schema>
    </types>
    
    <message name="getMahasiswaRequest">
        <part name="parameters" element="tns:getMahasiswa"/>
    </message>
    
    <message name="tambahMahasiswaRequest">
        <part name="parameters" element="tns:tambahMahasiswa"/>
    </message>
    
    <portType name="MahasiswaPortType">
        <operation name="getMahasiswa">
            <input message="tns:getMahasiswaRequest"/>
        </operation>
        <operation name="tambahMahasiswa">
            <input message="tns:tambahMahasiswaRequest"/>
        </operation>
    </portType>
    
    <binding name="MahasiswaBinding" type="tns:MahasiswaPortType">
        <soap:binding style="document" transport="http://schemas.xmlsoap.org/soap/http"/>
        <operation name="getMahasiswa">
            <soap:operation soapAction="getMahasiswa"/>
            <input><soap:body use="literal"/></input>
        </operation>
        <operation name="tambahMahasiswa">
            <soap:operation soapAction="tambahMahasiswa"/>
            <input><soap:body use="literal"/></input>
        </operation>
    </binding>
    
    <service name="MahasiswaService">
        <port name="MahasiswaPort" binding="tns:MahasiswaBinding">
            <soap:address location="http://localhost:5000/mahasiswa"/>
        </port>
    </service>
</definitions>"""
    return Response(wsdl_content, mimetype='text/xml')

# ===== SOAP CLIENT (menggunakan requests) =====
import requests

class SOAPClient:
    def __init__(self, service_url):
        self.service_url = service_url
    
    def get_mahasiswa(self, nim):
        """Mengambil data mahasiswa"""
        soap_request = f"""<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"
               xmlns:mhs="http://mahasiswa.service/">
    <soap:Body>
        <mhs:getMahasiswa>
            <nim>{nim}</nim>
        </mhs:getMahasiswa>
    </soap:Body>
</soap:Envelope>"""
        
        headers = {
            'Content-Type': 'text/xml; charset=utf-8',
            'SOAPAction': 'getMahasiswa'
        }
        
        try:
            response = requests.post(self.service_url, data=soap_request, headers=headers)
            return self._parse_response(response.text)
        except Exception as e:
            print(f"Error: {e}")
            return None
    
    def tambah_mahasiswa(self, nim, nama, jurusan, ipk):
        """Menambah mahasiswa baru"""
        soap_request = f"""<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"
               xmlns:mhs="http://mahasiswa.service/">
    <soap:Body>
        <mhs:tambahMahasiswa>
            <mahasiswa>
                <nim>{nim}</nim>
                <nama>{nama}</nama>
                <jurusan>{jurusan}</jurusan>
                <ipk>{ipk}</ipk>
            </mahasiswa>
        </mhs:tambahMahasiswa>
    </soap:Body>
</soap:Envelope>"""
        
        headers = {
            'Content-Type': 'text/xml; charset=utf-8',
            'SOAPAction': 'tambahMahasiswa'
        }
        
        try:
            response = requests.post(self.service_url, data=soap_request, headers=headers)
            return self._parse_response(response.text)
        except Exception as e:
            print(f"Error: {e}")
            return None
    
    def _parse_response(self, xml_response):
        """Parse response XML"""
        try:
            root = ET.fromstring(xml_response)
            
            # Cari mahasiswa data
            mahasiswa = root.find('.//mahasiswa')
            if mahasiswa is not None:
                return {
                    'nim': mahasiswa.find('nim').text,
                    'nama': mahasiswa.find('nama').text,
                    'jurusan': mahasiswa.find('jurusan').text,
                    'ipk': mahasiswa.find('ipk').text
                }
            
            # Cari message
            message = root.find('.//message')
            if message is not None:
                return {'message': message.text}
            
            return None
        except Exception as e:
            print(f"Error parsing response: {e}")
            return None

# ===== XML PROCESSING =====
class XMLProcessor:
    def __init__(self):
        self.data_file = "mahasiswa.xml"
    
    def create_xml_file(self):
        """Membuat file XML dengan data mahasiswa"""
        root = ET.Element("mahasiswa_list")
        
        # Data sample mahasiswa
        mahasiswa_data = [
            {"nim": "12345", "nama": "Ahmad Rizki", "jurusan": "Teknik Informatika", "ipk": "3.75"},
            {"nim": "67890", "nama": "Siti Nurhaliza", "jurusan": "Sistem Informasi", "ipk": "3.85"},
            {"nim": "11111", "nama": "Budi Santoso", "jurusan": "Teknik Komputer", "ipk": "3.60"}
        ]
        
        for mhs in mahasiswa_data:
            mahasiswa = ET.SubElement(root, "mahasiswa")
            ET.SubElement(mahasiswa, "nim").text = mhs["nim"]
            ET.SubElement(mahasiswa, "nama").text = mhs["nama"]
            ET.SubElement(mahasiswa, "jurusan").text = mhs["jurusan"]
            ET.SubElement(mahasiswa, "ipk").text = mhs["ipk"]
        
        # Format XML dengan indentasi
        xml_str = ET.tostring(root, encoding='unicode')
        dom = minidom.parseString(xml_str)
        with open(self.data_file, 'w', encoding='utf-8') as f:
            f.write(dom.toprettyxml(indent="  "))
        
        print(f"File XML berhasil dibuat: {self.data_file}")
    
    def read_xml_file(self):
        """Membaca dan menampilkan data dari file XML"""
        try:
            tree = ET.parse(self.data_file)
            root = tree.getroot()
            
            print("Data Mahasiswa dari XML:")
            print("-" * 50)
            
            for mahasiswa in root.findall("mahasiswa"):
                nim = mahasiswa.find("nim").text
                nama = mahasiswa.find("nama").text
                jurusan = mahasiswa.find("jurusan").text
                ipk = mahasiswa.find("ipk").text
                
                print(f"NIM: {nim}")
                print(f"Nama: {nama}")
                print(f"Jurusan: {jurusan}")
                print(f"IPK: {ipk}")
                print("-" * 30)
                
        except FileNotFoundError:
            print(f"File {self.data_file} tidak ditemukan")
        except ET.ParseError as e:
            print(f"Error parsing XML file: {e}")
    
    def add_mahasiswa_to_xml(self, nim, nama, jurusan, ipk):
        """Menambah mahasiswa baru ke file XML"""
        try:
            tree = ET.parse(self.data_file)
            root = tree.getroot()
        except FileNotFoundError:
            # Buat file baru jika tidak ada
            root = ET.Element("mahasiswa_list")
        
        # Tambah mahasiswa baru
        mahasiswa = ET.SubElement(root, "mahasiswa")
        ET.SubElement(mahasiswa, "nim").text = nim
        ET.SubElement(mahasiswa, "nama").text = nama
        ET.SubElement(mahasiswa, "jurusan").text = jurusan
        ET.SubElement(mahasiswa, "ipk").text = ipk
        
        # Format dan simpan
        xml_str = ET.tostring(root, encoding='unicode')
        dom = minidom.parseString(xml_str)
        with open(self.data_file, 'w', encoding='utf-8') as f:
            f.write(dom.toprettyxml(indent="  "))
        
        print(f"Mahasiswa {nama} berhasil ditambahkan ke XML")
    
    def search_mahasiswa_by_nim(self, nim):
        """Mencari mahasiswa berdasarkan NIM"""
        try:
            tree = ET.parse(self.data_file)
            root = tree.getroot()
            
            for mahasiswa in root.findall("mahasiswa"):
                if mahasiswa.find("nim").text == nim:
                    return {
                        'nim': mahasiswa.find("nim").text,
                        'nama': mahasiswa.find("nama").text,
                        'jurusan': mahasiswa.find("jurusan").text,
                        'ipk': mahasiswa.find("ipk").text
                    }
            return None
        except FileNotFoundError:
            print(f"File {self.data_file} tidak ditemukan")
            return None
    
    def update_mahasiswa_ipk(self, nim, ipk_baru):
        """Update IPK mahasiswa"""
        try:
            tree = ET.parse(self.data_file)
            root = tree.getroot()
            
            for mahasiswa in root.findall("mahasiswa"):
                if mahasiswa.find("nim").text == nim:
                    mahasiswa.find("ipk").text = ipk_baru
                    
                    # Simpan perubahan
                    xml_str = ET.tostring(root, encoding='unicode')
                    dom = minidom.parseString(xml_str)
                    with open(self.data_file, 'w', encoding='utf-8') as f:
                        f.write(dom.toprettyxml(indent="  "))
                    
                    print(f"IPK mahasiswa NIM {nim} berhasil diupdate menjadi {ipk_baru}")
                    return True
            
            print(f"Mahasiswa dengan NIM {nim} tidak ditemukan")
            return False
            
        except FileNotFoundError:
            print(f"File {self.data_file} tidak ditemukan")
            return False

# ===== CONTOH PENGGUNAAN =====
def demo_xml():
    """Demo penggunaan XML"""
    print("=== DEMO XML PROCESSING ===")
    xml_processor = XMLProcessor()
    
    # Buat file XML
    xml_processor.create_xml_file()
    
    # Baca file XML
    xml_processor.read_xml_file()
    
    # Tambah mahasiswa baru
    print("\nMenambah mahasiswa baru...")
    xml_processor.add_mahasiswa_to_xml("99999", "Andi Wijaya", "Teknik Elektro", "3.90")
    
    # Cari mahasiswa
    print("\nMencari mahasiswa dengan NIM 12345...")
    result = xml_processor.search_mahasiswa_by_nim("12345")
    if result:
        print(f"Ditemukan: {result['nama']} - {result['jurusan']}")
    
    # Update IPK
    print("\nUpdate IPK mahasiswa...")
    xml_processor.update_mahasiswa_ipk("12345", "3.80")
    
    # Baca ulang file XML
    print("\nData setelah update:")
    xml_processor.read_xml_file()

def demo_soap_client():
    """Demo penggunaan SOAP client"""
    print("=== DEMO SOAP CLIENT ===")
    
    service_url = "http://localhost:5000/mahasiswa"
    client = SOAPClient(service_url)
    
    try:
        # Ambil data mahasiswa
        print("Mengambil data mahasiswa dengan NIM 12345:")
        result = client.get_mahasiswa("12345")
        if result and 'nim' in result:
            print(f"NIM: {result['nim']}")
            print(f"Nama: {result['nama']}")
            print(f"Jurusan: {result['jurusan']}")
            print(f"IPK: {result['ipk']}")
        elif result:
            print(result['message'])
        
        # Tambah mahasiswa baru
        print("\nMenambah mahasiswa baru:")
        result = client.tambah_mahasiswa("88888", "Dewi Sartika", "Teknik Sipil", "3.70")
        if result:
            print(result['message'])
        
        # Coba ambil mahasiswa yang baru ditambahkan
        print("\nMengambil data mahasiswa yang baru ditambahkan:")
        result = client.get_mahasiswa("88888")
        if result and 'nim' in result:
            print(f"NIM: {result['nim']}")
            print(f"Nama: {result['nama']}")
            print(f"Jurusan: {result['jurusan']}")
            print(f"IPK: {result['ipk']}")
        
    except Exception as e:
        print(f"Error koneksi ke SOAP server: {e}")
        print("Pastikan server SOAP sudah berjalan dengan menjalankan:")
        print("python script.py server")

def start_server():
    """Menjalankan SOAP server"""
    print("SOAP Server berjalan di http://localhost:5000/mahasiswa")
    print("WSDL tersedia di http://localhost:5000/wsdl")
    app.run(debug=True, port=5000)

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "server":
            # Jalankan server SOAP
            start_server()
        elif sys.argv[1] == "client":
            # Jalankan demo client
            demo_soap_client()
        elif sys.argv[1] == "xml":
            # Jalankan demo XML
            demo_xml()
    else:
        print("Pilih mode:")
        print("python script.py server   # Jalankan SOAP server")
        print("python script.py client   # Demo SOAP client")
        print("python script.py xml      # Demo XML processing")
        
        # Jalankan demo XML sebagai default
        print("\n" + "="*50)
        print("Menjalankan demo XML...")
        demo_xml()
        print("\n" + "="*50)
        print("Untuk menjalankan demo SOAP:")
        print("1. Jalankan server: python script.py server")
        print("2. Di terminal lain: python script.py client")