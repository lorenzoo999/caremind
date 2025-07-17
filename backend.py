#La libreria standard `os` fornisce funzioni per interagire con il sistema operativo
import os
#Importa il pacchetto ufficiale OpenAI per interagire direttamente con le API OpenAI
import openai
#Importa il wrapper `OpenAIEmbeddings` di LangChain per generare tramite API embedding vettoriali 
from langchain_openai import OpenAIEmbeddings
#Importa il wrapper `ChatOpenAI` di LangChain per istanziare tramite API modelli GPT di OpenAI (gpt-3.5-turbo)
from langchain_openai import ChatOpenAI
#Streamlit è una libreria Python per creare rapidamente applicazioni web interattive e data-driven. 
import streamlit as st
#PdfReader e PdfWriter: classi della libreria pypdf che consentono di leggere e manipolare file PDF
from pypdf import PdfWriter, PdfReader
#RecursiveCharacterTextSplitter è uno strumento per suddividere testi lunghi in segmenti più piccoli in modo ricorsivo, mantenendo la coerenza delle frasi. È utile per pre-processare testi per analisi successive.
from langchain.text_splitter import RecursiveCharacterTextSplitter
#FAISS (Facebook AI Similarity Search) è una libreria per la ricerca efficiente e il clustering di grandi collezioni di vettori. Viene utilizzata per eseguire ricerche di similarità su grandi dataset di embedding.
from langchain_community.vectorstores import FAISS
#ConversationalRetrievalChain è una catena di elaborazione che combina retrieval di informazioni e generazione di risposte in un contesto conversazionale, utile per chatbot e assistenti virtuali.
from langchain.chains import ConversationalRetrievalChain
#ConversationBufferWindowMemory è una struttura di memoria che memorizza le ultime k interazioni di una conversazione. È utile per mantenere il contesto durante una conversazione lunga, migliorando la coerenza delle risposte.
from langchain.memory import ConversationBufferWindowMemory
#Classi di LangChain per costruire prompt strutturati
from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate


#MongoClient è il client ufficiale per connettersi a un database MongoDB e interagire con le collections di database
from pymongo import MongoClient
#La classe `datetime` del modulo standard per gestire date e orari
from datetime import datetime
#InferenceClient è la libreria client che permette di eseguire inferenze su modelli ospitati su Hugging Face Hub
from huggingface_hub import InferenceClient
#`load_dotenv` carica automaticamente variabili di ambiente 
from dotenv import load_dotenv


#carica le variabili d'ambiente da .env
load_dotenv()  

openai.api_key = os.getenv("OPENAI_API_KEY")

hf_token = os.getenv("HF_TOKEN")

mongo_db_password = os.getenv("MONGO_DB_PASSWORD")




# --- Connessione MongoDB ---
uri = f"mongodb+srv://simodgapple:{mongo_db_password}@cluster0.xixh93i.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(uri)

try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)

# Seleziona il database e la collection
db = client["Project_db"]
logs_collection = db["sentiment_analysis_logs"]
feedbacks_collection = db["user_feedbacks"]



# --- hugging face HUB Inference Client---
if hf_token is None:
    raise ValueError("Devi impostare la variabile d'ambiente HF_TOKEN")

client = InferenceClient(provider="hf-inference", api_key=hf_token)



#funzione che unisce (merge) tutti i file PDF presenti in una cartella (anche nelle sottocartelle) in un unico PDF di output. 
def merge_pdfs(folder_path, output_path):
    writer = PdfWriter()

    for root, dirs, files in os.walk(folder_path):
        for file in files:
            if file.lower().endswith('.pdf'):
                file_path = os.path.join(root, file)
                reader = PdfReader(file_path)
                for page in reader.pages:
                    writer.add_page(page)

    with open(output_path, "wb") as f_out:
        writer.write(f_out)


#funzione che consente di leggere i pdf e ritornarne il contenuto testuale
def read_pdf(file):
    document = ""

    reader = PdfReader(file)
    for page in reader.pages:
        document += page.extract_text()

    return document



#funzione per realizzare il recursive character text splitter; 
def split_doc(document, chunk_size, chunk_overlap):

    splitter = RecursiveCharacterTextSplitter( 
        separators=["\n\n", "\n", ".", " "],  # dalla struttura maggiore al fallback
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )
    split = splitter.split_text(document)
    split = splitter.create_documents(split)

    return split



#funzione per genera embeddings dei chunk e salva in un Vector Store
def embedding_storing(split, create_new_vs, vector_store_name):


        #Viene usato un pretrained sentence transformer model per generare l'embedding;
        #In tal caso si sfruttano i modelli di Embedding offerti da OpenAI (senza specificare il modello di default si utilizza text-embedding-ada-002)
        instructor_embeddings = OpenAIEmbeddings()

        #Viene generato un vector_store tramite FAISS per realizzare la similarity search
        db = FAISS.from_documents(split, instructor_embeddings)

        #creazione di un nuovo vector_store salvato in locale
        if create_new_vs == True:
            # Save vectore_store
            db.save_local("vector_store/" + vector_store_name)
        else:
            #Altrimenti carica vector_store esistente
            load_db = FAISS.load_local(
                "vector_store/" + vector_store_name,
                instructor_embeddings,
                allow_dangerous_deserialization=True
            )
            # Merge del vector_store esistente con nuovi embeddings e salvataggio
            load_db.merge_from(db)
            load_db.save_local("vector_store/" + vector_store_name)
 
        
        
#funzione per inizializzare e preparare il RAG conversational model con una data configurazione
def prepare_rag_llm(vector_store, temperature, max_length):

    #istanzio nuovamente il modello di embedding precedente;
    instructor_embeddings = OpenAIEmbeddings()

    # carico il vector_store attraverso load_local della classe FAISS passando il file path del vector_store su cui lavorerà il RAG,
    #ed il modello di embedding
    loaded_db = FAISS.load_local(
        f"vector_store/{vector_store}", instructor_embeddings, allow_dangerous_deserialization=True
    )

    #istanzio l'LLM richiamando il modello di GPT-3.5-turbo attraverso la classe per l'integrazione 
    #di modelli OpenaAI, settando la temperature e la massima lungezza della risposta che viene data in output; 
    #L'API_KEY viene ottenuta direttamente a partire dalle variabili d'ambiente;
    #NOTA: TEMPERATURA = parametro di entropia che va da 0 a 1 e che determina quanto la risposta del chatbot sarà creativa (andando verso l'1), ovvero una risposta più o meno deterministica.
    llm = ChatOpenAI(
        model="gpt-3.5-turbo", 
        temperature= temperature, 
        max_tokens = max_length
    )

    #ConversationBufferWindowMemory: buffer di memoria per far sì che l’LLM generi risposte coerenti col contesto della conversazione
    #tenendo traccia delle ultime k interazioni
    memory = ConversationBufferWindowMemory(
        k=5, #recupera info a partire dalle ultime 5 interazioni;
        memory_key="chat_history", #variabile dove viene salvata la cronologia della conversazione
        output_key="answer", #variabile per specificare quale parte dell’output della chain deve essere usata come risposta
        return_messages=True, #restituire la cronologia come oggetti di tipo Message, non come semplice testo.
    )

    #Prompt di sistema per il chatbot finalizzato ai pazienti
    if vector_store == "GestioneAnsiaPazienti":
        system_message = SystemMessagePromptTemplate.from_template(
            "Sei un chatbot professionista della salute digitale che risponde in modo empatico, chiaro, "
            "basato su evidenze scientifiche, adatto a pazienti e caregiver. "
            "Rispondi basandoti sui seguenti documenti, altrimenti invita a consultare un medico: {context} "
            "Nel caso in cui individui segnali di crisi grave nel messaggio nel paziente, contente ad esempio keyword"
            "del tipo: 'suicidio', 'suicidarmi', 'voglio morire', 'mi uccido', 'suicidarmi', 'farla finita', 'non voglio vivere',"
            "'autolesionismo', 'uccidermi', 'farmi del male', 'mi ammazzo', o simili, dai la seguente risposta di default senza modificarla:"
            "Sembra che tu stia attraversando un momento molto difficile.\n\n"
            "Per favore, sappi che non sei solo: ti incoraggio a contattare subito un professionista "
            "o a chiamare il numero di emergenza del tuo paese (112 o 118 in Italia).\n\n"
            "Se hai pensieri di farti del male, contatta immediatamente un familiare, un amico fidato "
            "o un professionista della salute mentale.\n\n"
            "Ti fornisco la linea telefonica per il supporto in caso di crisi psicologica "
            "disponibile  24 ore su 24, sette giorni su sette, raggiungibile al numero verde: 800 101 800.\n\n "
            "Inoltre, per un accesso più facile alla rete Suicide Prevention Lifeline e alle relative risorse di crisi,"
            "contatta il numero nazionale: 988"
        )

    #Prompt di sistema per il chatbot finalizzato ai professionisti
    elif vector_store == "DocumentiProfessionisti": 
        system_message = SystemMessagePromptTemplate.from_template(
            "Sei un assistente virtuale specializzato in salute mentale e supporto psicologico "
            "per operatori sanitari. Fornisci risposte chiare, concise e basate sulle evidenze "
            "scientifiche più recenti, con riferimento a tecniche psicoeducative, linee guida "
            "e protocolli di intervento per la gestione di ansia, stress e stabilizzazione emotiva. "
            "Organizza le informazioni in modo conciso e facilmente consultabile. "
            "Se la domanda esula dalle risorse disponibili, invita l'utente a consultare "
            "un esperto qualificato. "
            "Rispondi basandoti sui seguenti documenti: {context}."
        )


    #prompt dell'utente
    human_message = HumanMessagePromptTemplate.from_template(
        "{question}"
    )

    #Prompt finale
    qa_prompt = ChatPromptTemplate.from_messages([system_message, human_message])

    #inizializzazione della question-answer conversational chain attraverso la chain ConversationalRetrievalChain fornita dal LangChain
    qa_conversation = ConversationalRetrievalChain.from_llm(
        llm=llm, #il modello LLM (GPT-3.5 Turbo) per generare le risposte
        chain_type="stuff", #Specifica la logica di combinazione: “stuff” indica che tutti i documenti recuperati vengono inseriti nel prompt così come sono.
        retriever=loaded_db.as_retriever(search_kwargs={"k": 3}), #retriever per cercare automaticamente i top 3 documenti più rilevanti e dunque simili semanticamente all’interno di un database vettoriale (FAISS).
        memory=memory, #memoria conversazionale che tiene traccia delle k interazioni precedenti tramite ConversationBufferWindowMemory
        return_source_documents=True, #Restituisce i documenti originali utilizzati
        combine_docs_chain_kwargs={"prompt": qa_prompt}  #Prompt personalizzato che guida la risposta
    )

    #alla fine viene ritornata la chain finale di question_answer
    return qa_conversation



#funzione per generare risposte alle query dell'utente utilizzando il modello conversazionale creato con ConversationalRetrievalChain
#question: la domanda dell’utente 
#conversation_key: chiave per recuperare l’oggetto qa_conversation salvato in st.session_state di Streamlit:
#streamlit: parametro di default settato a True. Se settato a False permette di ottenere la riposta direttamente senza coinvolgere Streamlit
def generate_answer(question, conversation_key, streamlit = True):
    answer = "Mi dispiace, sto avendo difficoltà a rispondere ora. Puoi riprovare tra poco?" #Risposta di Default in caso di errore
    
    if(streamlit == False):
        response = conversation_key({"question": question})
    else: 
        response = st.session_state[conversation_key]({"question": question}) #Viene processata la domanda attraverso il conversational mode
    answer = response.get("answer").split("Helpful Answer:")[-1].strip() #Viene estratta la risposta da response
    explanation = response.get("source_documents", [])
    doc_source = [d.page_content for d in explanation] #Vengono collezionati i documenti che hanno contribuito alla risposta;

    return answer, doc_source



#Analisi sentiment chatbotbot 
def analyze_and_store(question, answer, user_type="paziente"):
    try:
        bot_sentiment_result = client.text_classification(
            answer,
            model="neuraly/bert-base-italian-cased-sentiment"
        )
    except Exception as e:
        print(f"Errore API sentiment bot: {e}")
        bot_sentiment_result = [{"label": "NEUTRAL", "score": 0.0}]

    bot_sentiment = bot_sentiment_result[0]["label"].lower()
    bot_polarity = bot_sentiment_result[0]["score"]

    # Controllo empatia risposta bot
    # Se bot troppo negativo o poco empatico -> alert 
    bot_alert = False
    if bot_sentiment == "negative" and bot_polarity > 0.8:
        bot_alert = True
        print("⚠️ Alert: risposta bot non empatica o troppo negativa.")

    # Prepara record da salvare
    log_record = {
        "user_type": user_type,
        "question": question,
        "answer": answer,
        "bot_sentiment": bot_sentiment,
        "bot_polarity": bot_polarity,
        "bot_alert": bot_alert,
        "timestamp": datetime.now()
    }

    # Salvataggio su MongoDB
    logs_collection.insert_one(log_record)

    return log_record


