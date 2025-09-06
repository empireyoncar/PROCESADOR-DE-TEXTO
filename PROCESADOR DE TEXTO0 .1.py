# main.py
import os
import tkinter as tk
from tkinter import scrolledtext, filedialog
import PyPDF2
import docx
from openai import OpenAI
import threading
import time

# ---------------------------
# Configura tu API Key
client = OpenAI(api_key="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")
# ---------------------------

CONFIG_FILE = "last_folder.txt"

# ---------------------------
# Funciones de carpeta
def guardar_ultima_carpeta(folder):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        f.write(folder)

def cargar_ultima_carpeta():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            folder = f.read().strip()
            if os.path.exists(folder):
                return folder
    return os.path.expanduser("~")  # Carpeta por defecto si no hay historial

# ---------------------------
# Función para cargar documentos
def cargar_documentos(folder):
    docs = {}
    if not os.path.exists(folder):
        os.makedirs(folder)
    for filename in os.listdir(folder):
        path = os.path.join(folder, filename)
        try:
            if filename.endswith(".txt"):
                with open(path, "r", encoding="utf-8") as f:
                    docs[filename] = f.read()
            elif filename.endswith(".pdf"):
                texto = ""
                pdf = PyPDF2.PdfReader(path)
                for page in pdf.pages:
                    texto += page.extract_text() or ""
                docs[filename] = texto
            elif filename.endswith(".docx"):
                doc = docx.Document(path)
                texto = "\n".join([p.text for p in doc.paragraphs])
                docs[filename] = texto
        except Exception as e:
            print(f"Error cargando {filename}: {e}")
    return docs

# ---------------------------
# Función para seleccionar carpeta
def seleccionar_carpeta():
    folder = filedialog.askdirectory()
    if folder:
        guardar_ultima_carpeta(folder)
        carpeta_var.set(folder)
        actualizar_archivos(folder)

# ---------------------------
# Función para actualizar archivos
def actualizar_archivos(folder):
    global documentos, archivos_list
    documentos = cargar_documentos(folder)
    archivos_list = list(documentos.keys())
    # Actualizar OptionMenu
    menu = archivo_menu["menu"]
    menu.delete(0, "end")
    for archivo in archivos_list:
        menu.add_command(label=archivo, command=lambda value=archivo: archivo_var.set(value))
    if archivos_list:
        archivo_var.set(archivos_list[0])
    else:
        archivo_var.set("")

# ---------------------------
# Función para actualizar continuamente (auto-refresh)
def auto_actualizar():
    previous_files = set()
    while True:
        current_files = set(os.listdir(carpeta_var.get()))
        if current_files != previous_files:
            actualizar_archivos(carpeta_var.get())
            previous_files = current_files
        time.sleep(2)  # revisar cada 2 segundos

# ---------------------------
# Función para preguntar a la IA
def preguntar_ia():
    try:
        pregunta = pregunta_entry.get().strip()
        archivo = archivo_var.get()
        if not archivo or archivo not in documentos:
            resultado_text.delete(1.0, tk.END)
            resultado_text.insert(tk.END, "⚠️ No has seleccionado un archivo válido.")
            return
        if not pregunta:
            resultado_text.delete(1.0, tk.END)
            resultado_text.insert(tk.END, "⚠️ Escribe una pregunta primero.")
            return

        contenido = documentos[archivo]
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Eres un asistente experto en los documentos proporcionados."},
                {"role": "user", "content": f"Documento:\n{contenido}\n\nPregunta: {pregunta}"}
            ]
        )
        respuesta = response.choices[0].message.content
        resultado_text.delete(1.0, tk.END)
        resultado_text.insert(tk.END, respuesta)
    except Exception as e:
        resultado_text.delete(1.0, tk.END)
        resultado_text.insert(tk.END, f"⚠️ Ocurrió un error:\n{e}")

# ---------------------------
# Configuración inicial
ultima_carpeta = cargar_ultima_carpeta()
documentos = cargar_documentos(ultima_carpeta)
archivos_list = list(documentos.keys())

# ---------------------------
# Crear GUI
root = tk.Tk()
root.title("📑 Procesador de Notas IA")

# Seleccionar carpeta
carpeta_var = tk.StringVar(value=ultima_carpeta)
seleccionar_btn = tk.Button(root, text="📂 Seleccionar carpeta", command=seleccionar_carpeta)
seleccionar_btn.pack(pady=5)

# Mostrar carpeta seleccionada
carpeta_label = tk.Label(root, textvariable=carpeta_var, fg="blue")
carpeta_label.pack(pady=5)

# Selección de archivo
archivo_var = tk.StringVar()
if archivos_list:
    archivo_var.set(archivos_list[0])
    archivo_menu = tk.OptionMenu(root, archivo_var, *archivos_list)
else:
    archivo_var.set("")  # Valor inicial vacío
    archivo_menu = tk.OptionMenu(root, archivo_var, "")  # Opción vacía para que no falle
archivo_menu.pack(pady=5)


# Entrada de pregunta
pregunta_entry = tk.Entry(root, width=80)
pregunta_entry.pack(pady=5)

# Botón preguntar
preguntar_btn = tk.Button(root, text="❓ Preguntar", command=preguntar_ia)
preguntar_btn.pack(pady=5)

# Caja de mensajes
mensaje_label = tk.Label(root, text="Mensajes:")
mensaje_label.pack()
resultado_text = scrolledtext.ScrolledText(root, width=100, height=20)
resultado_text.pack(pady=5)

# ---------------------------
# Hilo de auto-actualización
threading.Thread(target=auto_actualizar, daemon=True).start()

root.mainloop()
