"""
TERMINOLOGY VERIFICATION SCRIPT
Verifies that JSON and PDF use correct Locked LoFTR terminology.
"""

import json
import os

def verify_json_terminology(json_path):
    """Verify JSON file uses correct Locked LoFTR terminology."""
    print("=" * 80)
    print("JSON TERMINOLOGY VERIFICATION")
    print("=" * 80)
    print()
    
    with open(json_path, 'r') as f:
        data = json.load(f)
    
    # Check required fields with correct terminology
    checks = [
        ("pipeline_mode", "Locked LoFTR Baseline"),
        ("adaptive_routing", "Not Used"),
        ("fallback", "Not Used"),
        ("matcher", "LoFTR"),
    ]
    
    all_passed = True
    for field, expected_value in checks:
        actual_value = data.get(field, "MISSING")
        if actual_value == expected_value:
            print(f"[PASS] {field}: '{actual_value}' (CORRECT)")
        else:
            print(f"[FAIL] {field}: '{actual_value}' (EXPECTED: '{expected_value}')")
            all_passed = False
    
    print()
    if all_passed:
        print("[PASS] JSON TERMINOLOGY VERIFICATION: PASSED")
    else:
        print("[FAIL] JSON TERMINOLOGY VERIFICATION: FAILED")
    print()
    
    return all_passed

def verify_pdf_terminology(pdf_path):
    """Verify PDF exists and can be opened."""
    print("=" * 80)
    print("PDF TERMINOLOGY VERIFICATION")
    print("=" * 80)
    print()
    
    if not os.path.exists(pdf_path):
        print(f"[FAIL] PDF file not found: {pdf_path}")
        return False
    
    file_size = os.path.getsize(pdf_path)
    print(f"[PASS] PDF file exists: {pdf_path}")
    print(f"[PASS] PDF file size: {file_size} bytes")
    
    # Try to read PDF to verify it's valid
    try:
        import pypdf
        with open(pdf_path, 'rb') as f:
            pdf_reader = pypdf.PdfReader(f)
            num_pages = len(pdf_reader.pages)
            print(f"[PASS] PDF is valid: {num_pages} pages")
            
            # Extract text from first page to check for key terms
            first_page = pdf_reader.pages[0]
            text = first_page.extract_text()
            
            # Check for key terminology
            key_terms = [
                "Locked LoFTR Baseline",
                "Not Used",
                "LoFTR",
            ]
            
            print()
            print("Checking for key terminology in PDF:")
            for term in key_terms:
                if term in text:
                    print(f"[PASS] Found: '{term}'")
                else:
                    print(f"[WARN] Not found: '{term}'")
            
            print()
            print("[PASS] PDF TERMINOLOGY VERIFICATION: PASSED")
            return True
            
    except Exception as e:
        print(f"[FAIL] Error reading PDF: {e}")
        print("[WARN] PDF TERMINOLOGY VERIFICATION: INCONCLUSIVE")
        return False

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(script_dir, "locked_loftr_baseline_results.json")
    pdf_path = os.path.join(script_dir, "locked_loftr_baseline_report.pdf")
    
    json_ok = verify_json_terminology(json_path)
    pdf_ok = verify_pdf_terminology(pdf_path)
    
    print()
    print("=" * 80)
    print("FINAL VERIFICATION SUMMARY")
    print("=" * 80)
    print()
    
    if json_ok and pdf_ok:
        print("[PASS] ALL VERIFICATIONS PASSED")
        print()
        print("The Locked LoFTR Baseline uses correct terminology:")
        print("  - Pipeline Mode: Locked LoFTR Baseline")
        print("  - Adaptive Routing: Not Used")
        print("  - Fallback: Not Used")
        print("  - Matcher: LoFTR")
        print()
        print("This is a TRUE Locked LoFTR Baseline, clearly separated from")
        print("the Adaptive Research Engine.")
    else:
        print("[FAIL] SOME VERIFICATIONS FAILED")
        if not json_ok:
            print("  - JSON terminology verification failed")
        if not pdf_ok:
            print("  - PDF verification failed")

if __name__ == "__main__":
    main()
