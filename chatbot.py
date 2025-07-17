import datetime
import streamlit as st
import os
import backend
import time
from pymongo import MongoClient
import bcrypt

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

mongo_db_password = os.getenv("MONGO_DB_PASSWORD")

# --- Connessione MongoDB ---
uri = f"mongodb+srv://simodgapple:{mongo_db_password}@cluster0.xixh93i.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(uri)

try:
    client.admin.command('ping')
    print("Connessione a MongoDB avvenuta con successo!")
except Exception as e:
    print(e)


# Selezione del database MongoDB 
db = client["Project_db"]
# Selezione delle collections
professionisti_collection = db["professionisti"]
pazienti_collection = db["pazienti"]  
user_sessions_collection = db["user_sessions_logs"]  



#main dell'app Streamlit
def main():

    #Generazione degli embeddings e creazione di un nuovo vector_store salvato in locale (se non esistente)
    document_embedding()

    #barra laterale per navigare tra le pagine
    st.sidebar.title("Navigazione")
    page = st.sidebar.radio(
        "Vai a:",
        [ "Chi Siamo", "Accesso Paziente", "Accesso Professionista"]
    )

    if page == "Chi Siamo":
        display_chi_siamo_page()
    elif page == "Accesso Professionista":
        display_professionista_page()
    elif page == "Accesso Paziente":
        display_paziente_page()


#Funzione per caricare un file CSS locale e lo applica allo stile dell'app Streamlit
def load_css(file_name):
    with open(file_name) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)



# Pagina di accesso dedicata all'utente finale
def display_paziente_page():

    #Configurazione della pagina con titolo e icona
    st.set_page_config(
        page_title="Accesso Paziente",
        page_icon="😊",
        layout="centered"
    )

    # Inizializza lo stato di login per pazienti se non presente
    if "logged_in_patient" not in st.session_state:
        st.session_state.logged_in_patient = False


    #Definizione della dialog di feedback con form
    @st.dialog("Feedback Logout")
    def logout_feedback_dialog():
        st.write("Prima di uscire, come valuti la tua esperienza?")

        with st.form("feedback_form"):
            feedback = st.radio("Feedback", ["Positivo", "Negativo"])
            submit = st.form_submit_button("Invia Feedback")
        
        if submit:

            # Salvataggio del feedback nella session state 
            st.session_state["logout_feedback"] = feedback

            # Log della sessione 
            end_time = datetime.datetime.now()
            duration = round((end_time - st.session_state.start_time).total_seconds() / 60, 1)

            # Creazione di un dizionario con i dati della sessione
            interaction_log = {
                "start_time": st.session_state.start_time,
                "end_time": end_time,
                "chat_history": st.session_state.get("paziente_history", []),
                "durata_minuti": duration,
                "conteggio_domande": st.session_state.question_count,
                "feedback": feedback 
            }

            #Salvataggio del log della sessione nella collection
            user_sessions_collection.insert_one(interaction_log)

            st.success("Sessione terminata! Grazie per averci utilizzato.")

            st.session_state.logged_in_patient = False
            
            # Pulizia della session state legata alla chat paziente
            for key in [
                "paziente_conversation",
                "paziente_history",
                "paziente_source",
                "patient_email",
                "question_count",
                "start_time",
                "logout_feedback"
            ]:
                if key in st.session_state:
                    del st.session_state[key]

            #Ricarica l’app per tornare alla pagina di accesso del paziente
            st.rerun()

    #Se l'utente NON è loggato viene mostrato form di login
    if not st.session_state.logged_in_patient:
        st.title("Accesso Paziente")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")

        #Bottone per inviare i dati di accesso
        if st.button("Accedi"):
            #Verifica che i campi non siano vuoti
            if not email or not password:
                st.warning("Inserisci email e password.")
            else:
                #Si cerca l'utente nelle collection a partire dall'email
                user = pazienti_collection.find_one({"email": email})
                #se l'utente esiste e se la password è corretta (hashing bcrypt):
                if user and bcrypt.checkpw(password.encode(), user["password_hash"].encode()):
                    st.success("Accesso effettuato con successo!")
                    st.session_state.logged_in_patient = True
                    st.session_state.patient_email = email
                    st.rerun()
                else:
                    st.error("Credenziali non valide.")
    else:
        #Recupera nome e cognome del paziente da mostrare nella pagina
        user = pazienti_collection.find_one({"email": st.session_state.patient_email})
        nome = user.get("nome", "Nome")
        cognome = user.get("cognome", "Cognome")

        col1, col2 = st.columns([5, 2])
        with col1:
            st.subheader(f"User: {nome} {cognome}")
        with col2:
            container_2 = st.container()
            with container_2:
            # Iniettiamo il CSS dentro il container
                st.markdown("""
                    <style>
                    .stButton>button {
                        background-color: #c65611;
                        color: white;
                        position:absolute;
                        right: 0px;
                        top: -7px;
                    }
                    </style>
                """, unsafe_allow_html=True)
                #Bottone di Logout che chiama la funzione del dialog per il feedback con on_click
                st.button("Logout", on_click=logout_feedback_dialog)
                  

        # Avvio della pagina del chatbot passando chiavi di sessione specifiche per paziente
        display_chatbot_page(
            vector_store_name="GestioneAnsiaPazienti",
            conversation_key="paziente_conversation",
            history_key="paziente_history",
            source_key="paziente_source"
        )



# Pagina di accesso dedicata ai prefessionisti (operatori sanitari)
def display_professionista_page():
    #Configura la pagina Streamlit con titolo, icona e layout centrato
    st.set_page_config(
        page_title="Accesso Professionista",
        page_icon="👨‍⚕️",
        layout="centered"
    )

    # Inizializza lo stato di login per professionisti se non presente
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False

    # Se l'utente non è loggato si mostra form di login
    if not st.session_state.logged_in:
        st.title("Accesso Professionista")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        #Bottone per inviare i dati di accesso
        if st.button("Accedi"):
            #Verifica che i campi non siano vuoti
            if not email or not password:
                st.warning("Inserisci email e password.")
            else:
                #Si cerca il professionista nella collection a partire dall'email
                user = professionisti_collection.find_one({"email": email})
                #se il professionista esiste e se la password è corretta (hashing bcrypt):
                if user and bcrypt.checkpw(password.encode(), user["password_hash"].encode()):
                    st.success("Accesso effettuato con successo!")
                    st.session_state.logged_in = True
                    st.session_state.user_email = email
                    st.rerun()
                else:
                    st.error("Credenziali non valide.")
    else:
        # Recupera nome e cognome del professionista
        user = professionisti_collection.find_one({"email": st.session_state.user_email})
        nome = user.get("nome", "Nome")
        cognome = user.get("cognome", "Cognome")

        # Titolo area riservata
        st.title("Area Riservata ai Professionisti")

        # Riga con nome/cognome e logout
        col1, col2, col3 = st.columns([2, 1, 3])
        with col1:
            st.subheader(f"👨‍⚕️: {nome} {cognome}")
        with col2:
            st.markdown(
                """
                <style>
                div.stButton > button {
                    margin-top: -5px !important;
                }
                </style>
                """,
                unsafe_allow_html=True
            )
            #Bottone per il Logout del professionista
            if st.button("Logout"):
                st.session_state.logged_in = False

                # Elenco di tutte le chiavi da rimuovere dalla sessione del professionista
                keys_to_delete = [
                    "professionista_conversation",
                    "professionista_history",
                    "professionista_source",
                    "user_email"
                ]
                #Pulizia del session state
                for key in keys_to_delete:
                    if key in st.session_state:
                        del st.session_state[key]
                
                #Ricarica l’app per tornare alla pagina di accesso del professionista
                st.rerun()


    

        # Mostra all'utente professionista un radio button per scegliere cosa fare:
        # - Interagire con il chatbot
        # - Aggiornare la base di conoscenza del chatbot con nuovi documenti PDF
        action = st.radio(
            "Cosa vuoi fare?",
            ["Interagisci con Chatbot", "Aggiorna la Base di Conoscenza"],
            index=0
        )

        # Se l'utente sceglie di interagire con il chatbot
        if action == "Interagisci con Chatbot":
            # Verifica se esiste già il vector store dei documenti dei professionisti
            if os.path.exists("vector_store/DocumentiProfessionisti"):
                # Avvio della pagina del chatbot passando chiavi di sessione specifiche per professionista
                display_chatbot_page(
                    vector_store_name="DocumentiProfessionisti",
                    conversation_key="professionista_conversation",
                    history_key="professionista_history",
                    source_key="professionista_source"
                )
            else:
                #Si avvisa che il vector store deve essere prima creato
                st.info("Il vector store non è ancora stato creato. Carica i documenti in 'Aggiorna la Base di Conoscenza' prima di usare il chatbot.")
        # Se l'utente sceglie di aggiornare il vector store
        elif action == "Aggiorna la Base di Conoscenza":
            st.write("Carica i tuoi documenti PDF per aggiornare la Base di Conoscenza per i professionisti.")

            # Componente che permette di caricare uno o più file PDF per aggiornare il vector store dei professionisti con i nuovi chunk embeddizzati
            uploaded_files = st.file_uploader(
                "Carica uno o più file PDF",
                accept_multiple_files=True,
                type=['pdf']
            )

            # Se il professionista ha caricato uno o più PDF
            if uploaded_files:
                #Cartella dove salvare i PDF caricati
                save_path = "PDFs/FolderPdfProfessionisti"
                os.makedirs(save_path, exist_ok=True)

                #Salva ogni PDF caricato nella cartella indicata
                for uploaded_file in uploaded_files:
                    file_path = os.path.join(save_path, uploaded_file.name)
                    with open(file_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                st.success("PDF caricati correttamente.")

                #Mostra il pulsante per avviare la creazione o l'aggiornamento del vector store
                if st.button("Crea/aggiorna Base di Conoscenza"):
                    with st.spinner("Elaborazione documenti e aggiornamento..."):
                        output_pdf = "PDFs/merged_Professionisti.pdf"
                        backend.merge_pdfs(save_path, output_pdf)

                        combined_content = backend.read_pdf(output_pdf)
                        chunks = backend.split_doc(combined_content, 1500, 300)

                        vector_store_path = "vector_store/DocumentiProfessionisti"

                        #Se il vector store non esiste, lo crea
                        # Altrimenti lo aggiorna unendo i nuovi embeddings
                        if not os.path.exists(vector_store_path):
                            backend.embedding_storing(chunks, True, "DocumentiProfessionisti")
                        else:
                            backend.embedding_storing(chunks, False, "DocumentiProfessionisti")

                        st.success("Base di Conoscenza creata/aggiornata correttamente!")


# Pagina "Chi Siamo" sintetica per il chatbot CareMind
def display_chi_siamo_page():
    st.set_page_config(
        page_title="Chi Siamo",
        page_icon="ℹ️",
        layout="centered"
    )
    st.title("Chi Siamo")

    st.write("""
    **CareMind** è un assistente digitale che offre supporto informativo, pratico ed empatico 
    per la gestione dell'ansia. Basato su tecniche validate e su Retrieval-Augmented Generation (RAG),
    aiuta a rispondere a dubbi, suggerire esercizi utili e fornire indicazioni non cliniche ma affidabili.

    👥 **Per chi è pensato:**
    - **Utenti finali:** persone con sintomi ansiosi possono accedere a contenuti educativi e tecniche 
      di gestione (respirazione, rilassamento, grounding), ricevendo risposte rassicuranti e feedback 
      anonimo.
    - **Operatori sanitari:** strumento di consultazione rapida per tecniche e linee guida essenziali, 
      utile durante visite o colloqui di follow-up.

    🧭 **Obiettivo:**
    fornire un primo livello di aiuto sicuro, rispettoso e personalizzato, senza sostituire 
    il supporto specialistico.

    📞 **In caso di necessità:**
    CareMind invita sempre a contattare professionisti o numeri di emergenza, al fine di ricevere un triage medico per situazioni critiche.
    """)



#Definisce una funzione per mostrare la pagina del chatbot, istanziado il modello conversazionale tramite
#catena di question-answer (QA) conversazionale basata su RAG 
def display_chatbot_page(vector_store_name, conversation_key, history_key, source_key):

    #file CSS per applicare un tema personalizzato.
    coffee_theme_css = 'coffee_theme.css'

    #Salva il tema nella sessione Streamlit
    if 'theme' not in st.session_state:
        st.session_state.theme = coffee_theme_css

    #pplica il tema custom alla pagina.
    load_css(st.session_state.theme)



    #URL delle icone
    user = "https://raw.githubusercontent.com/simo26/icone/main/user-286-3.png"                        
    icon = "https://raw.githubusercontent.com/simo26/icone/main/calm.png"


    #Layout e logica specifica per i pazienti.
    if vector_store_name == "GestioneAnsiaPazienti":

        # Traccia inizio sessione il user session log
        if 'start_time' not in st.session_state:
            st.session_state.start_time = datetime.datetime.now()
            st.session_state.question_count = 0

        st.markdown(f"""<h1 style='text-align:center; color: #51b5c7; margin-left: 65px;' class='stTitle'> 
        CareMind <img src="{icon}" alt="logo" style="width:85px; position: relative; bottom: 22px;">
        </h1>""", unsafe_allow_html=True)


        st.markdown("""
        <div style='text-align: center; margin-top: -20px;'>
            <p class="customHdr" style='font-family: "Roboto", sans-serif; font-size: 1.2em;'>
            Il Tuo Anti-Stress Digitale, Sempre a Disposizione!
            </p>
        </div>
        """, unsafe_allow_html=True)

    else:
         st.markdown(f"""
        <div style='text-align: center; margin-top: 0px;'>
            <p class="customHdr" style='font-family: "Roboto", sans-serif; font-size: 1.6em;'>
            Ottieni informazioni sui documenti <img src="{icon}" alt="logo" style="width:55px; position: relative; bottom: 15px;">
            </p>
        </div>
        """, unsafe_allow_html=True)


    #Inizializza la sessione per la ConversationalRetrievalChain non esiste.
    if conversation_key not in st.session_state:
        st.session_state[conversation_key] = None

    #Parametri per instanziare il modello chatgpt-3.5-turbo
    VECTOR_STORE = vector_store_name
    TEMPERATURE = 0.5
    MAX_LENGTH = 520


    #Prepara la catena RAG (ConversationalRetrievalChain) e la salva in sessione
    st.session_state[conversation_key] = backend.prepare_rag_llm(
        VECTOR_STORE, TEMPERATURE, MAX_LENGTH
    )

    #Inizializza la cronologia della chat se non esiste.
    if history_key not in st.session_state:
        st.session_state[history_key] = []

    #Inizializza la lista delle fonti dei documenti se non esiste.
    if source_key not in st.session_state:
        st.session_state[source_key] = []

    #Visualizza tutti i messaggi precedenti con l'avatar corretto (utente o chatbot).
    for message in st.session_state[history_key]:
        display_message(message["role"], message["content"], user if message["role"] == "user" else icon)

    # Se l'utente inserisce una nuova domanda nella chat
    if question := st.chat_input("Fammi una domanda"):

        #Conta le domande se la sessione è per pazienti.
        if vector_store_name == "GestioneAnsiaPazienti":
            st.session_state.question_count += 1

        #Aggiunta della domanda alla cronologia e mostra domanda dell'utente
        st.session_state[history_key].append({"role": "user", "content": question})
        display_message("user", question, user)

        #Chiamata alla funzione di backend per generare la risposta ed i 3 top documenti semanticamente simili mediante la question-answer chain precedemente istanziata.
        answer, doc_source = backend.generate_answer(question, conversation_key)


        #Mostra la risposta del chatbot con effetto "typing"
        message_placeholder = st.empty()
        partial_answer = ""
        for char in answer:
            partial_answer += char
            message_placeholder.markdown(f""" 
                <div class="assistant-message">
                    <img src="{icon}" class="avatar">
                    <div class="chat-bubble assistant-bubble">
                        {partial_answer.strip()}
                    </div>
                </div>
            """, unsafe_allow_html=True)
            time.sleep(0.02)
        #Aggiungta della risposta alla cronologia e salvataggio dei documenti di origine nella session state
        st.session_state[history_key].append({"role": "assistant", "content": answer})
        st.session_state[source_key].append({"question": question, "answer": answer, "document": doc_source})

        #Nel caso di sessione per i pazienti: salvataggio del log di sentiment analysis.
        if vector_store_name == "GestioneAnsiaPazienti":

            #Salvataggio delle analisi sentiment delle risposte del chatbot su collection MongoDB
            log_record = backend.analyze_and_store(
                question,
                answer,
                user_type="paziente"
            )

            print("Log salvato:", log_record)



#Mostra messaggi della conversazione con stile a fumetto e avatar
def display_message(role, content, avatar_url):
    # Determina classi CSS in base al ruolo
    message_class = "user-message" if role == "user" else "assistant-message"
    bubble_class = "user-bubble" if role == "user" else "assistant-bubble"
    # Messaggio utente: testo + avatar a destra
    if role == "user":
        st.markdown(f"""         
            <div class="{message_class}">
                <div class="chat-bubble {bubble_class}">
                    {content}
                </div>
                <img src="{avatar_url}" class="avatar">
            </div>
        """, unsafe_allow_html=True)
    # Messaggio assistente: avatar a sinistra + testo
    else:
        st.markdown(f"""
            <div class="{message_class}">
                <img src="{avatar_url}" class="avatar">
                <div class="stChatMessage {bubble_class}">
                    {content}
                </div>
            </div>
        """, unsafe_allow_html=True)




# Funzione che controlla se esiste già il vector_store locale "GestioneAnsiaPazienti".
# Se non esiste, unisce tutti i PDF nella cartella, li legge e li spezza in chunk.
# Poi genera gli embeddings e crea un nuovo vector_store salvato in locale.
def document_embedding():
    if not os.path.exists("vector_store/GestioneAnsiaPazienti"):

        print("vector_store/GestioneAnsiaPazienti assente. Generazione in corso.")

        input_path = "PDFs/FolderPdfGestioneAnsiaPazienti"
        output_path = "PDFs/merged_PdfGestioneAnsiaPazienti.pdf"
        backend.merge_pdfs(input_path, output_path)
        combined_content = backend.read_pdf(output_path)
        split = backend.split_doc(combined_content, 1500, 300)
        backend.embedding_storing(split, True, "GestioneAnsiaPazienti")



if __name__ == "__main__":
    main()

