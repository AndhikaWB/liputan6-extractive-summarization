from math import ceil
from bs4 import BeautifulSoup
from pathlib import Path
from spacy.lang.id import Indonesian
from spacy.symbols import ORTH
from copy import deepcopy
from Sastrawi.Stemmer.StemmerFactory import StemmerFactory
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from kneed import KneeLocator
from rouge import Rouge

import requests
import csv
import re
import unicodedata
import warnings
import json

class NLP:
  @staticmethod
  def get_text_auto(file_or_url):
    # Cek apakah input merupakan sebuah file
    if Path(file_or_url).is_file(): is_file = True
    else: is_file = False

    # Bila berupa file
    if is_file:
      # Cek tipe/ekstensi file
      file_ext = Path(file_or_url).suffix

      # Bila tipe file didukung
      if file_ext in ('.txt', '.html'):
        # Baca isi dari file sebagai plain teks
        file = open(file_or_url, 'r')
        text_content = file.read()
        file.close()

        # Parse HTML dahulu bila bukan plain teks
        if file_ext == '.html':
          text_content = NLP.get_text_from_url(text_content, True)
      # Bila tipe file tidak didukung
      else:
        print('Format file tidak didukung!')
        text_content = ''
    # Bila berupa URL
    else:
      text_content = NLP.get_text_from_url(file_or_url)

    # Berikan isi teks dari file atau URL
    return text_content
  
  @staticmethod
  def get_text_from_url(url_content, from_file = False):
    if not from_file:
      try:
        # Dapatkan konten HTML dari URL
        url_content = requests.get(url_content, headers = {
          'User-Agent': 'Mozilla/5.0 (Linux; Android 13) Chrome/107.0',
          'Save-Data': 'on'
        }).content
      except: return ''
    else:
      # Data sudah dalam bentuk HTML
      pass

    # Objek bantuan untuk fungsi filter tag HTML dll
    soup = BeautifulSoup(url_content, 'html.parser')
    
    # Teks sampah pada beberapa situs (detik.com, liputan6.com, dll)
    # TODO: Gunakan filter adblock sebagai alternatif
    text_noise = (
      'ADVERTISEMENT',
      'SCROLL TO RESUME CONTENT',
      'SCROLL TO CONTINUE WITH CONTENT',
      'Advertisement',
      'liputan6'
    )
    strong_text_noise = (
      'lihat',
      'simak',
      'baca',
      'tonton',
      '(',
      '[',
      '*'
    )

    try:
      # Hilangkan informasi nama situs, tanggal, dan penulis dari liputan6.com
      soup.find('div', class_='read-page--header--author__wrapper').decompose()
      soup.find('div', class_='navbar--top--logo__site-title').decompose()
    except AttributeError: pass

    def text_scraping(soup, text_tag, tag_class = None):
      # Isi teks mula-mula (kosong)
      text_content = ''

      for paragraph in soup.find_all(text_tag, class_ = tag_class):
        # Hapus superscript (referensi Wikipedia) dari teks
        for p in paragraph.select('sup'): p.extract()
        # Hapus teks promosi dari beberapa situs (detik.com, liputan6.com, dll)
        for p in paragraph.select('strong'):
          temp_text = p.get_text().lower().strip()
          if temp_text.startswith(strong_text_noise): p.extract()
        # Hapus whitespace sesudah dan sebelum teks
        temp_text = paragraph.get_text().strip()
        # Filter kata sampah (bukan stop word)
        if temp_text not in text_noise:
          text_content += temp_text + ' '
        
      return text_content

    text_content = text_scraping(soup, 'p').strip()
    # Jika tag tidak menggunakan <p> (pada beberapa berita liputan6.com)
    if not text_content:
      text_content = text_scraping(soup, 'div', 'article-content-body__item-page').strip()

    # Hilangkan spasi beruntun dan baris baru
    text_content = re.sub('\s+', ' ', text_content)
    
    # Berikan isi teks
    return text_content
  
  @staticmethod
  def sentence_segmentation(text):
    nlp = Indonesian()
    nlp.add_pipe('sentencizer')

    # Jangan anggap kasus berikut sebagai akhir kalimat
    nlp.tokenizer.add_special_case("Ir.", [{ORTH: "Ir."}])
    nlp.tokenizer.add_special_case("Mr.", [{ORTH: "Mr."}])
    nlp.tokenizer.add_special_case("PT.", [{ORTH: "PT."}])

    # Muat teks ke dalam pipeline
    doc = nlp(text)

    # Simpan hasil tokenisasi kalimat ke dalam list kalimat
    sentence_list = [ str(sentence) for sentence in doc.sents ]

    # Workaround kesalahan pengutipan pada tokenizer Indonesia
    for i, sentence in enumerate(sentence_list):
      # Kalimat diakhiri dengan titik dan kutip
      if sentence.endswith('. "'):
        sentence_list[i] = sentence_list[i][:-2]
        sentence_list[i+1] = '"' + sentence_list[i+1]
      # Kalimat diakhiri dengan titik, kutip, dan kurung
      elif sentence.endswith('. "('):
        sentence_list[i] = sentence_list[i][:-3]
        sentence_list[i+1] = '"(' + sentence_list[i+1]
    
    return sentence_list
  
  @staticmethod
  def sentence_clean_regex(sentence_list):
    # sentence_list = deepcopy(sentence_list)

    for i, sentence in enumerate(sentence_list):
      # Hilangkan semua karakter non-ASCII (UNICODE, dll)
      # sentence = re.sub(r'[^\x00-\x7f]','', sentence)
      # sentence = sentence.encode('ascii', 'ignore').decode()
      sentence = unicodedata.normalize('NFKC', sentence)

      # Hilangkan URL
      sentence = re.sub(r'http[s]?://\S+', '', sentence)
      # Hilangkan tag/mention
      sentence = re.sub(r'@\S+', '', sentence)
      # Hilangkan hashtag
      sentence = re.sub(r'#\S+', '', sentence)

      # Ubah semua tab dan baris baru menjadi spasi
      sentence = re.sub(r'\t|\n|\r', ' ', sentence)

      # Hilangkan semua kata yang hanya terdiri dari non-alphabet
      # https://stackoverflow.com/questions/72318334
      sentence = re.sub(r'(?<!\S)[^A-Za-z]+(?!\S)', '', sentence)

      # Hilangkan semua karakter spesial yang tidak berada di antara alphanumerik
      # https://stackoverflow.com/questions/61049643
      sentence = re.sub(r'(?<!\w)\W+|\W+(?!\w)', ' ', sentence)

      # Hilangkan whitespace beruntun (lebih dari satu)
      sentence = re.sub(r'\s\s+', ' ', sentence)

      # Hilangkan trailing/leading whitespace
      sentence = sentence.strip()

      # Ganti isi kalimat saat ini dengan isi variabel sementara
      sentence_list[i] = sentence
    
    return sentence_list
  
  @staticmethod
  def sentence_stopwords_removal(sentence_list):
    # sentence_list = deepcopy(sentence_list)

    nlp = Indonesian()
    # Tambah stopwords baru (bila ada)
    # nlp.Defaults.stop_words.add("kata_sampah")

    for i, sentence in enumerate(sentence_list):
      # Tokenisasi kalimat (menjadi per kata)
      tokens = nlp.tokenizer(sentence)
      # Kosongkan kalimat saat ini
      sentence_list[i] = ''
      # Tambah token ke kalimat bila bukan stopword
      # Sertakan juga pemisah antar kata (spasi)
      for token in tokens:
        if not token.is_stop:
          sentence_list[i] += token.text + token.whitespace_

    return sentence_list
  
  @staticmethod
  def sentence_stemming(sentence_list):
    # sentence_list = deepcopy(sentence_list)

    stemmer = StemmerFactory().create_stemmer()
    for i, sentence in enumerate(sentence_list):
      sentence_list[i] = stemmer.stem(sentence)
    
    return sentence_list
  
  @staticmethod
  def sentence_preprocess(text_content):
    sentence_list = NLP.sentence_segmentation(text_content)
    sentence_list = NLP.sentence_clean_regex(sentence_list)
    sentence_list = NLP.sentence_stopwords_removal(sentence_list)
    sentence_list = NLP.sentence_stemming(sentence_list)

    return sentence_list
  
  @staticmethod
  def get_tfidf(sentence_list):
    tfidf = TfidfVectorizer()
    tfidf_matrix = tfidf.fit_transform(sentence_list)
    return tfidf_matrix
  
  @staticmethod
  def find_elbow_location(tfidf_matrix, max_clusters):
    # Dapatkan banyaknya kalimat
    num_sentences = tfidf_matrix.shape[0]
    if max_clusters > num_sentences:
      max_clusters = num_sentences - 1

    wcss = []

    if max_clusters > 2:
      for i in range(2, max_clusters + 1):
        # Proses K-means berulang-ulang sampai jumlah kluster tertentu
        kmeans = KMeans(n_clusters = i, random_state = 66)
        # Prediksi kluster tiap kalimat pada dokumen
        kmeans.fit_predict(tfidf_matrix)
        # Tambahkan WCSS untuk jumlah K saat ini
        wcss.append(kmeans.inertia_)
    else:
      # Proses K-means hanya untuk K = 2 (paling minimum)
      kmeans = KMeans(n_clusters = 2, random_state = 66)
      # Prediksi kluster tiap kalimat pada dokumen
      kmeans.fit_predict(tfidf_matrix)
      # Tambahkan WCSS untuk jumlah K saat ini
      wcss.append(kmeans.inertia_)

    # Tampilkan nilai WCSS
    # for i, s in enumerate(wcss):
    #   print(f'Nilai WCSS K = {i+2}: {s}')

    # Hilangkan warning bila tidak terdapat siku/lutut
    warnings.filterwarnings("ignore")

    # Dapatkan indeks kluster yang terletak di siku/lutut
    if max_clusters > 2:
      knee_cluster_index = KneeLocator(
        range(2, max_clusters + 1), wcss,
        curve = 'convex', direction = 'decreasing'
      ).knee # Akan return None bila tidak ada siku/lutut
    else:
      # print("Tidak memungkinkan menggunakan jumlah K > 2...")
      knee_cluster_index = 2

    # Jika tidak ditemukan siku/lutut
    # if knee_cluster_index == None:
      # print('Siku/lutut tidak ditemukan! Set ke K = 2...')
      # knee_cluster_index = 2

    # print(f'Siku/lutut terletak pada K = {knee_cluster_index}')

    return knee_cluster_index
  
  @staticmethod
  def kmeans_cluster_from_elbow(tfidf_matrix, knee_cluster_index):
    # Jalankan kembali K-means dengan nilai K terbaik
    kmeans = KMeans(knee_cluster_index, random_state = 66)
    kmeans.fit_predict(tfidf_matrix)

    # List keanggotaan cluster untuk tiap kalimat
    cluster_label = kmeans.labels_
    # print(f'Label kluster tiap kalimat: {cluster_label}')
    return cluster_label
  
  @staticmethod
  def get_kmeans_summarization_result(tfidf_matrix, cluster_label, sentence_list, max_summary_sentences):
    # Dapatkan nilai rata-rata TF-IDF per kata dalam suatu kalimat
    # Lalu, anggap nilai tersebut sebagai nilai TF-IDF kalimat
    # Nilai nol pada list/array akan dihilangkan sebelum dirata-rata
    sentence_relevancy = [ sum(t) / len(t) for t in tfidf_matrix.toarray() ]

    # for i, r in enumerate(sentence_relevancy):
    #   print(f'Nilai TF-IDF (relevansi) S{i+1}: {r}')  

    # Nilai TF-IDF mula-mula tiap kluster adalah nol
    cluster_relevancy = [ 0 for _ in set(cluster_label) ]

    for i, label in enumerate(set(cluster_label)):
      temp_cluster_members = 0
      for j, sentence in enumerate(sentence_list):
        if cluster_label[j] == label:
          # Totalkan nilai TF-IDF per kalimat menjadi nilai TF-IDF kluster
          cluster_relevancy[i] += sentence_relevancy[j]
          # Hitung jumlah kalimat dalam kluster yang sama
          temp_cluster_members += 1
      # Rata-ratakan nilai TF-IDF kluster (dibagi dengan jumlah kalimat)
      # Untuk mengurangi skew ke kluster dengan kalimat panjang
      cluster_relevancy[i] /= temp_cluster_members

    # for i, r in enumerate(cluster_relevancy):
    #   print(f'Nilai TF-IDF (relevansi) K{i}: {r}')

    # Simpan nomor kluster yang paling relevan
    most_relevant_cluster = cluster_relevancy.index(max(cluster_relevancy))
    # print(f'Kluster paling relevan: K{most_relevant_cluster}')
    # Simpan jumlah kalimat dari kluster yang paling relevan
    top_cluster_members = 0

    # Set jumlah kalimat maksimal untuk hasil ringkasan
    if max_summary_sentences < 1 or not isinstance(max_summary_sentences, int):
      max_summary_sentences = 5

    # Teks gabungan hasil summarization
    text_summarization_kmeans = ""

    # Tampilkan kluster paling baik
    for i, sentence in enumerate(sentence_list):
      if top_cluster_members == max_summary_sentences: break
      if cluster_label[i] == most_relevant_cluster:
        text_summarization_kmeans += sentence + " "
        # print(f'[{i+1}] {sentence}')
        top_cluster_members += 1  

    return text_summarization_kmeans

  @staticmethod
  def get_reference_summary(url, max_summary_sentences):
    # Hasil ringkasan mula-mula
    summary_sentence = ""

    # Jika situs berasal dari liputan6.com
    if url.startswith('https://www.liputan6.com/news/read/'):
      # Dapatkan ID berita dari URL
      news_id = url.split('/')[5]

      # Buka file JSON
      try:
        with open(f'./dataset/{news_id}.json') as json_file:
          data = json.load(json_file)

          for i, sentence in enumerate(data["clean_article"]):
            # Jika urutan kalimat saat ini merupakan ringkasan
            if i in data["extractive_summary"]:
              for word in sentence:
                if word.isalnum(): summary_sentence += ' ' + word
                else: summary_sentence += word
      except Exception: pass

    # Jika hasil kosong atau situs bukan berasal dari liputan6.com
    if not summary_sentence:
      api_url = "https://api.smmry.com"
      query_string = {
        # Request API key: https://smmry.com/api
        "SM_API_KEY": "XXXXXXXXXX",
        "SM_LENGTH": max_summary_sentences
      }

      if not Path(url).is_file():
        query_string["SM_URL"] = url
        response = requests.request("GET", api_url, params = query_string)
      else:
        form_data = { "sm_api_input": NLP.get_text_auto(url) }
        response = requests.request("POST", api_url, params = query_string, data = form_data)

      try: summary_sentence = response.json()["sm_api_content"]
      except Exception: pass

    return summary_sentence.strip()

  @staticmethod
  def get_rouge_score(machine_summary, human_summary):
    # machine_summary = NLP.sentence_preprocess(machine_summary)
    # human_summary = NLP.sentence_preprocess(human_summary)

    # Sesuaikan banyak kalimat untuk dibandingkan (ambil yang paling sedikit)
    if (len(machine_summary) > len(human_summary)):
      machine_summary = machine_summary[:len(human_summary)]
      # print(f'Hanya membandingkan {len(human_summary)} kalimat pertama...')
    elif (len(machine_summary) < len(human_summary)):
      human_summary = human_summary[:len(machine_summary)]
      # print(f'Hanya membandingkan {len(machine_summary)} kalimat pertama...')
    else:
      # print('Membandingkan seluruh kalimat...')
      pass

    machine_summary = '. '.join(machine_summary)
    human_summary = '. '.join(human_summary)

    # Hitung skor ROUGE antara teks rangkuman mesin dengan pembanding
    rouge = Rouge().get_scores(machine_summary, human_summary)[0]

    # Tampilkan hasilnya dalam bentuk recall, precision, dan skor F1
    # for i, val in enumerate(rouge.values()):
    #   print(['ROUGE 1-gram','ROUGE 2-gram','ROUGE LCS'][i], end = ": ")
    #   print(f'{round(val["r"], 5)} (r), {round(val["p"], 5)} (p), {round(val["f"], 5)} (f)')

    return rouge
  
  @staticmethod
  def import_file(document, human_summary, machine_summary, file_or_url = "", file_output = ""):
    # Path file output secara default
    if not file_output:
      file_output = "output/log.csv"

    # Jika file belum ada atau kosong
    if not Path(file_output).is_file() or Path(file_output).stat().st_size == 0:
      with open(file_output, 'w') as fw:
        writer = csv.writer(fw, delimiter = ';')
        # Buat header baru bila belum ada file
        writer.writerow(['file_or_url', 'full_document', 'human_summary', 'machine_summary'])
    
    with open(file_output, 'r+') as frw:
      reader = csv.reader(frw, delimiter = ';')
      # Simpan list baris yang tidak memiliki file/URL yang sama dengan parameter
      rows = [row for row in reader if row[0] != file_or_url]
      # Tambahkan baris baru di akhir berdasarkan parameter saat ini
      rows.append([file_or_url, document, human_summary, machine_summary])

      # Reset posisi dan isi file
      frw.seek(0)
      frw.truncate()

      # Tulis kembali file tanpa duplikat yang sama di awal (dari baris terakhir)
      writer = csv.writer(frw, delimiter = ';')
      writer.writerows(rows)