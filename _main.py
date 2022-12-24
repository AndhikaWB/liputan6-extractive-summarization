# Tkinter tidak support auto scaling secara otomatis (Linux)
# Window program mungkin akan terlihat kecil pada layar resolusi 2K+

from pathlib import Path
from tkinter import Tk, Canvas, Entry, Text, Button, PhotoImage, filedialog
from nlp import NLP

OUTPUT_PATH = Path(__file__).parent
ASSETS_PATH = OUTPUT_PATH / Path("./assets")

def relative_to_assets(path: str) -> Path:
    return ASSETS_PATH / Path(path)

window = Tk()
window.geometry("800x620")
window.configure(bg = "#FFFFFF")
# Tidak berfungsi bila font merupakan bitmap
# window.tk.call('tk', 'scaling', 2.0)

canvas = Canvas(
    window,
    bg = "#FFFFFF",
    height = 620,
    width = 800,
    bd = 0,
    highlightthickness = 0,
    relief = "ridge"
)

canvas.place(x = 0, y = 0)
image_image_1 = PhotoImage(
    file=relative_to_assets("image_1.png"))
image_1 = canvas.create_image(
    535.0,
    45.0,
    image=image_image_1
)

def get_evaluation():
    file_or_url = entry_1.get()
    max_sentences = entry_3.get()
    human_summarization = entry_5.get("1.0","end-1c")
    kmeans_summarization = entry_6.get("1.0","end-1c")

    try: max_sentences = int(max_sentences)
    except ValueError: pass
    
    entry_2.delete(1.0, "end")
    if not isinstance(max_sentences, int):
        entry_2.insert("end", "Jumlah kalimat maksimal harus berupa angka bulat!\n")
        return
    if isinstance(max_sentences, int) and max_sentences < 1:
        entry_2.insert("end", "Jumlah kalimat maksimal harus lebih dari 0!\n")
        return

    if kmeans_summarization and human_summarization:
        kmeans_summarization_list = NLP.sentence_segmentation(kmeans_summarization)
        human_summarization_list = NLP.sentence_segmentation(human_summarization)
        full_document = NLP.sentence_segmentation(NLP.get_text_auto(file_or_url))
        if file_or_url and not full_document: file_or_url = ""

        kmeans_summarization = NLP.sentence_preprocess(kmeans_summarization)
        human_summarization = NLP.sentence_preprocess(human_summarization)

        # Sesuaikan banyak kalimat untuk dibandingkan (ambil yang paling sedikit)
        if (len(kmeans_summarization) > len(human_summarization)):
            entry_2.insert("end", f'Hanya membandingkan {len(human_summarization)} kalimat pertama...\n')
        elif (len(kmeans_summarization) < len(human_summarization)):
            entry_2.insert("end", f'Hanya membandingkan {len(kmeans_summarization)} kalimat pertama...\n')
        else:
            entry_2.insert("end", 'Membandingkan seluruh kalimat...\n')
        
        kmeans_summarization = " ".join(kmeans_summarization)
        human_summarization = " ".join(human_summarization)

        entry_2.insert("end", "Mendapatkan hasil evaluasi ROUGE...\n")
        rouge = NLP.get_rouge_score(kmeans_summarization, human_summarization)

        for i, val in enumerate(rouge.values()):
          entry_2.insert("end", f'{["ROUGE 1-gram","ROUGE 2-gram","ROUGE LCS"][i]}: ')
          entry_2.insert("end", f'{round(val["r"], 5)} (r), {round(val["p"], 5)} (p), {round(val["f"], 5)} (f)\n')
        
        NLP.import_file(full_document, human_summarization_list, kmeans_summarization_list, file_or_url)
    else:
        entry_2.insert("end", "Hasil ringkasan (mesin dan pembanding) tidak boleh kosong!\n")

button_image_1 = PhotoImage(
    file=relative_to_assets("button_1.png"))
button_1 = Button(
    image=button_image_1,
    borderwidth=0,
    highlightthickness=0,
    command=get_evaluation,
    relief="flat"
)
button_1.place(
    x=520.0,
    y=546.0,
    width=160.0,
    height=37.0
)

canvas.create_rectangle(
    0.0,
    0.0,
    400.0,
    620.0,
    fill="#009688",
    outline="")

image_image_2 = PhotoImage(
    file=relative_to_assets("image_2.png"))
image_2 = canvas.create_image(
    200.0,
    136.0,
    image=image_image_2
)

entry_image_1 = PhotoImage(
    file=relative_to_assets("entry_1.png"))
entry_bg_1 = canvas.create_image(
    180.0,
    243.0,
    image=entry_image_1
)
entry_1 = Entry(
    bd=0,
    bg="#F4F6F8",
    fg="#000716",
    highlightthickness=0
)
entry_1.place(
    x=44.0,
    y=227.0,
    width=272.0,
    height=30.0
)

entry_image_2 = PhotoImage(
    file=relative_to_assets("entry_2.png"))
entry_bg_2 = canvas.create_image(
    200.0,
    519.0,
    image=entry_image_2
)
entry_2 = Text(
    bd=0,
    bg="#F4F6F8",
    fg="#000716",
    highlightthickness=0
)
entry_2.place(
    x=44.0,
    y=455.0,
    width=312.0,
    height=126.0
)

image_image_3 = PhotoImage(
    file=relative_to_assets("image_3.png"))
image_3 = canvas.create_image(
    148.0,
    205.0,
    image=image_image_3
)

def choose_file():
    # Tampilkan dialog untuk memilih gambar
    file = filedialog.askopenfilename(
        filetypes = [
            ("TXT files", "*.txt"),
            ("CSV (tab separated) files", "*.csv"),
            ("HTML files", "*.html"),
            ("All files", "*.*")
        ]
    )

    if file:
        # Hapus entry dan tambahkan kembali path ke file
        entry_1.delete(0, "end")
        entry_1.insert("end", file)

button_image_2 = PhotoImage(
    file=relative_to_assets("button_2.png"))
button_2 = Button(
    image=button_image_2,
    borderwidth=0,
    highlightthickness=0,
    command=choose_file,
    relief="flat"
)
button_2.place(
    x=332.0,
    y=227.0,
    width=32.0,
    height=32.0
)

image_image_4 = PhotoImage(
    file=relative_to_assets("image_4.png"))
image_4 = canvas.create_image(
    97.0,
    284.0,
    image=image_image_4
)

entry_image_3 = PhotoImage(
    file=relative_to_assets("entry_3.png"))
entry_bg_3 = canvas.create_image(
    116.0,
    322.0,
    image=entry_image_3
)
entry_3 = Entry(
    bd=0,
    bg="#F4F6F8",
    fg="#000716",
    highlightthickness=0
)
entry_3.place(
    x=44.0,
    y=306.0,
    width=144.0,
    height=30.0
)

entry_image_4 = PhotoImage(
    file=relative_to_assets("entry_4.png"))
entry_bg_4 = canvas.create_image(
    284.0,
    322.0,
    image=entry_image_4
)
entry_4 = Entry(
    bd=0,
    bg="#F4F6F8",
    fg="#000716",
    highlightthickness=0
)
entry_4.place(
    x=212.0,
    y=306.0,
    width=144.0,
    height=30.0
)

image_image_5 = PhotoImage(
    file=relative_to_assets("image_5.png"))
image_5 = canvas.create_image(
    271.0,
    284.0,
    image=image_image_5
)

image_image_6 = PhotoImage(
    file=relative_to_assets("image_6.png"))
image_6 = canvas.create_image(
    101.0,
    433.0,
    image=image_image_6
)

entry_image_5 = PhotoImage(
    file=relative_to_assets("entry_5.png"))
entry_bg_5 = canvas.create_image(
    600.0,
    171.0,
    image=entry_image_5
)
entry_5 = Text(
    bd=0,
    bg="#F4F6F8",
    fg="#000716",
    highlightthickness=0
)
entry_5.place(
    x=444.0,
    y=67.0,
    width=312.0,
    height=206.0
)

image_image_7 = PhotoImage(
    file=relative_to_assets("image_7.png"))
image_7 = canvas.create_image(
    200.0,
    68.0,
    image=image_image_7
)

def process_summarization():
    file_or_url = entry_1.get()
    max_sentences = entry_3.get()
    max_clusters = entry_4.get()

    try:
        max_sentences = int(max_sentences)
        max_clusters = int(max_clusters)
    except ValueError:
        pass
    
    entry_2.delete(1.0, "end")
    if not isinstance(max_sentences, int):
        entry_2.insert("end", "Jumlah kalimat maksimal harus berupa angka bulat!\n")
        return
    if not isinstance(max_clusters, int):
        entry_2.insert("end", "Jumlah cluster maksimal harus berupa angka bulat!\n")
        return
    if isinstance(max_sentences, int) and max_sentences < 1:
        entry_2.insert("end", "Jumlah kalimat maksimal harus lebih dari 0!\n")
        return
    if isinstance(max_clusters, int) and max_clusters < 2:
        entry_2.insert("end", "Jumlah cluster maksimal harus lebih dari 1!\n")
        return
    
    entry_2.insert("end", "Mencoba mendapatkan teks dari file atau URL...\n")
    text_content = NLP.get_text_auto(file_or_url)
    if not text_content:
        entry_2.insert("end", "Gagal mendapatkan teks dari file atau URL!\n")
        return
    
    entry_2.insert("end", "Memisahkan paragraf menjadi kalimat...\n")
    sentence_list = NLP.sentence_segmentation(text_content)
    if len(sentence_list) < 2:
        entry_2.insert("end", "Jumlah kalimat yang ada terlalu sedikit!\n")
        return
    
    entry_2.insert("end", "Melakukan preprocessing pada kalimat...\n")
    sentence_list_preprocess = NLP.sentence_preprocess(text_content)

    entry_2.insert("end", "Mendapatkan matrix TF-IDF...\n")
    tfidf_matrix = NLP.get_tfidf(sentence_list_preprocess)

    entry_2.insert("end", "Mencoba menemukan jumlah cluster terbaik...\n")
    knee_cluster_index = NLP.find_elbow_location(tfidf_matrix, max_clusters)

    if knee_cluster_index:
        entry_2.insert("end", f"Cluster terbaik berada pada K = {knee_cluster_index}!\n")
    else:
        knee_cluster_index = 2
        entry_2.insert("end", "Tidak menemukan cluster terbaik, default ke K = 2!\n")
    
    entry_2.insert("end", "Mendapatkan kelas cluster dari tiap kalimat...\n")
    cluster_label = NLP.kmeans_cluster_from_elbow(tfidf_matrix, knee_cluster_index)

    entry_2.insert("end", "Mendapatkan hasil ringkasan dari K-means...\n")
    text_summarization_kmeans = NLP.get_kmeans_summarization_result(tfidf_matrix, cluster_label, sentence_list, max_sentences)
    entry_5.delete(1.0, "end")
    entry_5.insert("end", text_summarization_kmeans)

    entry_6.delete(1.0, "end")
    text_summarization_human = NLP.get_reference_summary(file_or_url, max_sentences)

    if not text_summarization_human:
        entry_2.insert("end", "Gagal mendapatkan ringkasan pembanding secara otomatis!\n")
        entry_2.insert("end", "Masukkan ringkasan pembanding secara manual bila ingin mengevaluasi hasil...\n")
    else:
        entry_6.insert("end", text_summarization_human)

button_image_3 = PhotoImage(
    file=relative_to_assets("button_3.png"))
button_3 = Button(
    image=button_image_3,
    borderwidth=0,
    highlightthickness=0,
    command=process_summarization,
    relief="flat"
)
button_3.place(
    x=113.0,
    y=354.0,
    width=178.0,
    height=37.0
)

image_image_8 = PhotoImage(
    file=relative_to_assets("image_8.png"))
image_8 = canvas.create_image(
    561.0,
    300.0,
    image=image_image_8
)

entry_image_6 = PhotoImage(
    file=relative_to_assets("entry_6.png"))
entry_bg_6 = canvas.create_image(
    600.0,
    426.0,
    image=entry_image_6
)
entry_6 = Text(
    bd=0,
    bg="#F4F6F8",
    fg="#000716",
    highlightthickness=0
)
entry_6.place(
    x=444.0,
    y=322.0,
    width=312.0,
    height=206.0
)
window.resizable(False, False)
window.mainloop()
