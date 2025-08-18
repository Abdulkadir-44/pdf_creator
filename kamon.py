# test_runner.py (yeni dosya oluştur)
from logic.pdf_generator import PDFCreator  # senin pdf sınıfın
from test import PDFTestSuite

def run_tests():
    pdf_creator = PDFCreator()
    soru_klasoru = "C:\\Users\\abdul\\Desktop\\Soru-Havuzu\\Unite-1\\Karbonhidrat\\Test\\Kolay"  # senin soru klasörün
    
    test_suite = PDFTestSuite(pdf_creator, soru_klasoru)
    test_suite.run_all_tests()

if __name__ == "__main__":
    run_tests()

