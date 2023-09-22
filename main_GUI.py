import tkinter as tk
from tkinter import ttk
import subprocess
import os
from RVE_envlop_gene_custom_inp_nodeset import main


def retrieve_values(material_frame):
    values = {}
    for label, entry in material_frame.entries.items():
        values[label] = entry.get()
    return values
def call_script_1():
    mat1_entries = []
    mat2_entries = []
    mat_def = {}

    for widget in frame_material1.winfo_children():
        if 'entry' in str(widget):
            mat1_entries.append(widget.get())
    for widget in frame_material2.winfo_children():
        if 'entry' in str(widget):
            mat2_entries.append(widget.get())

    Thickness = float(entry_Thickness.get())
    Density = float(entry_Density.get())
    dimension = combo_dimension.get()
    material_type1 = frame_material1.combo.get()
    material_type2 = frame_material2.combo.get()

    mat_def[material_type1+'1'] = mat1_entries
    mat_def[material_type2+'2'] = mat2_entries

    #cmd = f"python RVE-envlop-gene-custom-inp-nodeset.py {Thickness} {Density} {dimension} {mat_def}"
    main(Thickness,Density, dimension,mat_def)
    
    print('Done')
    #subprocess.run(cmd, shell=True)
def call_exit():
    app.shut()

def update_fields(frame_fields):

    selected = frame_fields.combo.get()
    row_offset = 2
    entry = []

    # Clear previous fields
    for widget in frame_fields.winfo_children():
        if 'entry' in str(widget):
            widget.destroy()
        if 'label' in str(widget):
            t = widget.cget("text")
            if 'Material' not in t:
                widget.destroy()
                
    frame_fields.entries = {}
    
    if selected == 'Elastic':
        
        ttk.Label(frame_fields, text="E:").grid(row=row_offset, column=0)
        entry.append(ttk.Entry(frame_fields,width=10).grid(row=1+row_offset, column=0))
        ttk.Label(frame_fields, text="v:").grid(row=row_offset, column=1)
        entry.append(ttk.Entry(frame_fields,width=10).grid(row=1+row_offset, column=1))
        frame_fields.entries[selected] = entry
    elif selected == 'Eng constant':
        ttk.Label(frame_fields, text="E1:").grid(row=row_offset, column=0)
        entry.append(ttk.Entry(frame_fields, width=10).grid(row=1+row_offset, column=0))
        ttk.Label(frame_fields, text="E2:").grid(row=row_offset, column=1)
        entry.append(ttk.Entry(frame_fields, width=10).grid(row=1+row_offset, column=1))
        ttk.Label(frame_fields, text="E3:").grid(row=row_offset, column=2)
        entry.append(ttk.Entry(frame_fields, width=10).grid(row=1+row_offset, column=2))
        ttk.Label(frame_fields, text="nu12:").grid(row=row_offset, column=3)
        entry.append(ttk.Entry(frame_fields, width=10).grid(row=1+row_offset, column=3))
        ttk.Label(frame_fields, text="nu13:").grid(row=row_offset, column=4)
        entry.append(ttk.Entry(frame_fields, width=10).grid(row=1+row_offset, column=4))
        ttk.Label(frame_fields, text="nu23:").grid(row=row_offset, column=5)
        entry.append(ttk.Entry(frame_fields, width=10).grid(row=1+row_offset, column=5))
        ttk.Label(frame_fields, text="G12:").grid(row=row_offset, column=6)
        entry.append(ttk.Entry(frame_fields, width=10).grid(row=1+row_offset, column=6))
        ttk.Label(frame_fields, text="G13:").grid(row=row_offset, column=7)
        entry.append(ttk.Entry(frame_fields, width=10).grid(row=1+row_offset, column=7))
        ttk.Label(frame_fields, text="G23:").grid(row=row_offset, column=8)
        entry.append(ttk.Entry(frame_fields, width=10).grid(row=1+row_offset, column=8))
        frame_fields.entries[selected] = entry
    elif selected == 'Orthotropic':
        ttk.Label(frame_fields, text="D1111:").grid(row=row_offset, column=0)
        entry.append(ttk.Entry(frame_fields, width=10).grid(row=1+row_offset, column=0))
        ttk.Label(frame_fields, text="D1122:").grid(row=row_offset, column=1)
        entry.append(ttk.Entry(frame_fields, width=10).grid(row=1+row_offset, column=1))
        ttk.Label(frame_fields, text="D2222:").grid(row=row_offset, column=2)
        entry.append(ttk.Entry(frame_fields, width=10).grid(row=1+row_offset, column=2))
        ttk.Label(frame_fields, text="D1133:").grid(row=row_offset, column=3)
        entry.append(ttk.Entry(frame_fields, width=10).grid(row=1+row_offset, column=3))
        ttk.Label(frame_fields, text="D2233:").grid(row=row_offset, column=4)
        entry.append(ttk.Entry(frame_fields, width=10).grid(row=1+row_offset, column=4))
        ttk.Label(frame_fields, text="D3333:").grid(row=row_offset, column=5)
        entry.append(ttk.Entry(frame_fields, width=10).grid(row=1+row_offset, column=5))
        ttk.Label(frame_fields, text="D1212:").grid(row=row_offset, column=6)
        entry.append(ttk.Entry(frame_fields, width=10).grid(row=1+row_offset, column=6))
        ttk.Label(frame_fields, text="D1313:").grid(row=row_offset, column=7)
        entry.append(ttk.Entry(frame_fields, width=10).grid(row=1+row_offset, column=7))
        ttk.Label(frame_fields, text="D2323:").grid(row=row_offset, column=8)
        entry.append(ttk.Entry(frame_fields, width=10).grid(row=1+row_offset, column=8))
        frame_fields.entries[selected] = entry

app = tk.Tk()
app.title("Homtools GUI")

# Script 1 GUI
label_intro = ttk.Label(app, text=r"Build an envelopped RVE suitable for homogeneization in Abaqus coupled with the Homtools plugin")
label_intro.grid(column=0, row=0)

label_Thickness = ttk.Label(app, text="Thickness :")
label_Thickness.grid(column=0, row=1)
entry_Thickness = ttk.Entry(app,textvariable='1.0')
entry_Thickness.grid(column=1, row=1)
entry_Thickness.insert(0, "1.0")

label_Density = ttk.Label(app, text="Mesh density:")
label_Density.grid(column=0, row=2)
entry_Density = ttk.Entry(app)
entry_Density.grid(column=1, row=2)
entry_Density.insert(0,"1.0")

label_dimension = ttk.Label(app, text="Dimension:")
label_dimension.grid(column=0, row=3)
combo_dimension = ttk.Combobox(app, values=["3D"])
combo_dimension.grid(column=1, row=3)
combo_dimension.set("3D")

btn_cancel = ttk.Button(app, text="Exit", command=app.destroy)
btn_cancel.grid(column=0, row=4)
btn_script1 = ttk.Button(app, text="Browse", command=call_script_1)
btn_script1.grid(column=1, row=4)

frame_main = ttk.Frame(app, padding="10")
frame_main.grid(row=5, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
frame_main.columnconfigure(0, weight=1)  # Allow column 0 to expand
frame_main.columnconfigure(1, weight=1)  # Allow column 1 to expand more

# First Material
options = ["Elastic", "Eng constant", "Orthotropic"]
# First Material
frame_material1 = ttk.Frame(frame_main)
ttk.Label(frame_material1, text="Material 1:").grid(row=0, column=0, sticky=tk.W)
frame_material1.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
frame_material1.combo = ttk.Combobox(frame_material1, values=options, width=10)
frame_material1.combo.grid(row=0, column=1)
frame_material1.combo.set(options[0])  # Setting a default value
frame_material1.combo.bind("<<ComboboxSelected>>", lambda event: update_fields(frame_material1))
update_fields(frame_material1)

# Second Material
frame_material2 = ttk.Frame(frame_main)
frame_material2.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
frame_material2.combo = ttk.Combobox(frame_material2, values=options, width=10)
frame_material2.combo.grid(row=0, column=1)
frame_material2.combo.set(options[0])  # Setting a default value
frame_material2.combo.bind("<<ComboboxSelected>>", lambda event: update_fields(frame_material2))
ttk.Label(frame_material2, text="Material 2:").grid(row=0, column=0, sticky=tk.W)
update_fields(frame_material2)

app.mainloop()