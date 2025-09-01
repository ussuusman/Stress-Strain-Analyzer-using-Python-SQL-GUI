

import sqlite3

import matplotlib.pyplot as plt

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import datetime



# create database
conn = sqlite3.connect("mechanical.db")
cursor = conn.cursor()

# create table
cursor.execute("""
CREATE TABLE IF NOT EXISTS materials (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    youngs_modulus REAL,
    yield_strength REAL
)
""")

# insert some materials
cursor.execute("SELECT COUNT(*) FROM materials")
if cursor.fetchone()[0] == 0:
    cursor.executemany("""
    INSERT INTO materials (name, youngs_modulus, yield_strength) VALUES (?, ?, ?)
    """, [
        ("Steel", 210000, 250),
        ("Aluminum", 70000, 150),
        ("Brass", 100000, 200)
    ])


conn.commit()
conn.close()
print("Database created successfully!")



import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox

# function to fetch material names from DB
def get_materials():
    conn = sqlite3.connect("mechanical.db")
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM materials")
    data = [row[0] for row in cursor.fetchall()]
    conn.close()
    return data

# function to calculate stress/strain
def analyze(load, area, material):
    conn = sqlite3.connect("mechanical.db")
    cursor = conn.cursor()
    cursor.execute("SELECT youngs_modulus, yield_strength FROM materials WHERE name=?", (material,))
    youngs_modulus, yield_strength = cursor.fetchone()
    conn.close()
    
    stress = load / area      # N/mm² (MPa)
    strain = stress / youngs_modulus
    fos = yield_strength / stress
    return stress, strain, fos
def plot_graph(stress, strain, youngs_modulus, yield_strength):
    # Elastic limit strain = yield_strength / youngs_modulus
    elastic_strain = yield_strength / youngs_modulus

    # Elastic region (0 → yield)
    elastic_strains = [0, elastic_strain]
    elastic_stresses = [0, yield_strength]

    # Plastic region (approximate: strain from yield → 2x yield strain, stress stays near yield)
    plastic_strains = [elastic_strain, elastic_strain * 2]
    plastic_stresses = [yield_strength, yield_strength * 0.9]  # drop slightly to simulate necking

    plt.figure(figsize=(6,4))
    plt.plot(elastic_strains, elastic_stresses, label="Elastic Region", color="blue", linewidth=2)
    plt.plot(plastic_strains, plastic_stresses, label="Plastic Region", color="orange", linewidth=2)

    # Add actual point from user input
    plt.scatter([strain], [stress], color="red", zorder=5, label="Calculated Point")

    plt.axhline(y=yield_strength, color="green", linestyle="--", label="Yield Strength")
    plt.xlabel("Strain")
    plt.ylabel("Stress (MPa)")
    plt.title("Stress-Strain Curve")
    plt.legend()
    plt.grid(True)
    plt.show()


# GUI action
def calculate():
    try:
        load = float(load_entry.get())
        area = float(area_entry.get())
        material = material_combo.get()

        conn = sqlite3.connect("mechanical.db")
        cursor = conn.cursor()
        cursor.execute("SELECT youngs_modulus, yield_strength FROM materials WHERE name=?", (material,))
        youngs_modulus, yield_strength = cursor.fetchone()
        conn.close()

        stress, strain, fos = analyze(load, area, material)

        messagebox.showinfo("Results", f"Stress: {stress:.2f} MPa\nStrain: {strain:.6f}\nFactor of Safety: {fos:.2f}")

        # Call graph function
        plot_graph(stress, strain, youngs_modulus, yield_strength)
        
        # Call export function
        export_report(stress, strain, fos, material, yield_strength, youngs_modulus)


    except Exception as e:
        messagebox.showerror("Error", str(e))
def export_report(stress, strain, fos, material, yield_strength, youngs_modulus):
    filename = f"StressStrain_Report_{material}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"

    c = canvas.Canvas(filename, pagesize=letter)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(200, 750, "Stress & Strain Analysis Report")

    c.setFont("Helvetica", 12)
    c.drawString(50, 700, f"Date: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    c.drawString(50, 670, f"Material: {material}")
    c.drawString(50, 650, f"Young's Modulus: {youngs_modulus} MPa")
    c.drawString(50, 630, f"Yield Strength: {yield_strength} MPa")
    c.drawString(50, 610, f"Applied Stress: {stress:.2f} MPa")
    c.drawString(50, 590, f"Calculated Strain: {strain:.6f}")
    c.drawString(50, 570, f"Factor of Safety: {fos:.2f}")

    c.setFont("Helvetica-Oblique", 10)
    c.drawString(50, 540, "Generated using Python, SQLite, Tkinter, Matplotlib, and ReportLab")

    c.save()
    messagebox.showinfo("Export", f"Report saved as {filename}")



# GUI setup
root = tk.Tk()
root.title("Stress & Strain Analyzer")

tk.Label(root, text="Load (N):").grid(row=0, column=0, padx=5, pady=5)
load_entry = tk.Entry(root)
load_entry.grid(row=0, column=1)

tk.Label(root, text="Area (mm²):").grid(row=1, column=0, padx=5, pady=5)
area_entry = tk.Entry(root)
area_entry.grid(row=1, column=1)

tk.Label(root, text="Material:").grid(row=2, column=0, padx=5, pady=5)
material_combo = ttk.Combobox(root, values=get_materials())
material_combo.grid(row=2, column=1)

tk.Button(root, text="Calculate", command=calculate).grid(row=3, column=0, columnspan=2, pady=10)

root.mainloop()











