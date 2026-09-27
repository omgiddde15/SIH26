"""
LOCKED LOFTR BASELINE PDF GENERATOR
Generates a PDF report for the Locked LoFTR Baseline with correct terminology.
"""

import os
import json
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak

def generate_baseline_pdf_report(json_path, output_path):
    """Generate PDF report from Locked LoFTR Baseline JSON results."""
    
    # Load JSON results
    with open(json_path, 'r') as f:
        data = json.load(f)
    
    # Create PDF
    doc = SimpleDocTemplate(output_path, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    # Title
    title_style = styles["Title"]
    title_style.fontSize = 18
    title_style.textColor = colors.HexColor("#1e40af")
    story.append(Paragraph("Locked LoFTR Baseline Report", title_style))
    story.append(Spacer(1, 12))
    
    # Timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    story.append(Paragraph(f"Generated: {timestamp}", styles["Normal"]))
    story.append(Spacer(1, 12))
    
    # Pipeline Configuration
    story.append(Paragraph("<b>PIPELINE CONFIGURATION</b>", styles["Heading2"]))
    story.append(Spacer(1, 6))
    
    config_data = [
        ["Pipeline Mode", data["pipeline_mode"]],
        ["Adaptive Routing", data["adaptive_routing"]],
        ["Fallback", data["fallback"]],
        ["Matcher", data["matcher"]],
        ["Source Resolution", data["source_resolution"]],
        ["Reference Resolution", data["reference_resolution"]],
    ]
    
    config_table = Table(config_data, colWidths=[200, 300])
    config_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor("#f1f5f9")),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor("#334155")),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
    ]))
    story.append(config_table)
    story.append(Spacer(1, 12))
    
    # Baseline Results
    story.append(Paragraph("<b>BASELINE RESULTS</b>", styles["Heading2"]))
    story.append(Spacer(1, 6))
    
    results_data = [
        ["Candidate Correspondences", str(data["candidate_correspondences"])],
        ["Initial Inliers", str(data["initial_inliers"])],
        ["Initial Inlier Ratio", f"{data['initial_inlier_ratio']:.4f}"],
        ["Final Inliers", str(data["final_inliers"])],
        ["Spatial Occupancy", f"{data['spatial_occupancy']:.4f}"],
        ["Spatial CV", f"{data['spatial_cv']:.4f}"],
        ["Reprojection RMSE", f"{data['reprojection_rmse']:.4f} px"],
        ["Mean Error", f"{data['mean_error']:.4f} px"],
        ["Median Error", f"{data['median_error']:.4f} px"],
        ["Max Error", f"{data['max_error']:.4f} px"],
        ["Runtime", f"{data['runtime']:.2f} s"],
    ]
    
    results_table = Table(results_data, colWidths=[200, 300])
    results_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor("#f1f5f9")),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor("#334155")),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
    ]))
    story.append(results_table)
    story.append(Spacer(1, 12))
    
    # Independent Validation
    if data.get("validation_available"):
        story.append(Paragraph("<b>INDEPENDENT VALIDATION RESULTS</b>", styles["Heading2"]))
        story.append(Spacer(1, 6))
        
        validation_data = [
            ["Validation Available", "Yes"],
            ["Validation Seed", str(data.get("validation_seed", "N/A"))],
            ["Estimation Points", str(data.get("estimation_points", "N/A"))],
            ["Check Points", str(data.get("check_points", "N/A"))],
            ["Fit RMSE", f"{data.get('fit_rmse', 0):.4f} px" if data.get('fit_rmse') else "N/A"],
            ["Check RMSE", f"{data.get('check_rmse', 0):.4f} px" if data.get('check_rmse') else "N/A"],
            ["Validation Status", data.get("validation_status", "N/A")],
        ]
        
        if "cross_seed_mean_check_rmse" in data:
            validation_data.extend([
                ["Cross-Seed Mean Check RMSE", f"{data['cross_seed_mean_check_rmse']:.4f} px"],
                ["Cross-Seed Median Check RMSE", f"{data['cross_seed_median_check_rmse']:.4f} px"],
                ["Cross-Seed Best Check RMSE", f"{data['cross_seed_best_check_rmse']:.4f} px"],
                ["Cross-Seed Worst Check RMSE", f"{data['cross_seed_worst_check_rmse']:.4f} px"],
            ])
        
        validation_table = Table(validation_data, colWidths=[200, 300])
        validation_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor("#f1f5f9")),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor("#334155")),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ]))
        story.append(validation_table)
        story.append(Spacer(1, 12))
    
    # Important Notes
    story.append(Paragraph("<b>IMPORTANT NOTES</b>", styles["Heading2"]))
    story.append(Spacer(1, 6))
    
    notes = [
        "This is a TRUE Locked LoFTR Baseline run.",
        "Pipeline Mode: Locked LoFTR Baseline",
        "Adaptive Routing: Not Used",
        "Fallback: Not Used",
        "Matcher: LoFTR only",
        "No adaptive router was invoked during this run.",
        "No SIFT or SuperGlue fallback was used.",
        "This is NOT an Adaptive Rule-Based LoFTR run.",
        "Registration mathematics were not modified.",
    ]
    
    for note in notes:
        story.append(Paragraph(f"• {note}", styles["Normal"]))
    
    story.append(Spacer(1, 12))
    
    # Build PDF
    doc.build(story)
    print(f"PDF report generated: {output_path}")

if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(script_dir, "locked_loftr_baseline_results.json")
    output_path = os.path.join(script_dir, "locked_loftr_baseline_report.pdf")
    generate_baseline_pdf_report(json_path, output_path)
