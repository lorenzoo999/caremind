# CareMind — Un chabot per supportarti nei momenti d'ansia

CareMind è un assistente digitale che offre supporto informativo, pratico ed empatico per la gestione dell'ansia. Basato su tecniche validate e su Retrieval-Augmented Generation (RAG), aiuta a rispondere a dubbi, suggerire esercizi utili e fornire indicazioni non cliniche ma affidabili.

👥 Per chi è pensato:

-Utenti finali: persone con sintomi ansiosi possono accedere a contenuti educativi e tecniche di gestione (respirazione, rilassamento, grounding), ricevendo risposte rassicuranti e feedback anonimo.
-Operatori sanitari: strumento di consultazione rapida per tecniche e linee guida essenziali, utile durante visite o colloqui di follow-up.
🧭 Obiettivo: fornire un primo livello di aiuto sicuro, rispettoso e personalizzato, senza sostituire il supporto specialistico.

📞 In caso di necessità: CareMind invita sempre a contattare professionisti o numeri di emergenza, al fine di ricevere un triage medico per situazioni critiche.

### Tecnologie utilizzate:

- huggingface_hub
- langchain
- langchain_community
- langchain_openai
- openai
- pymongo
- pypdf
- streamlit
- bcrypt
- faiss-cpu
- ragas
- cryptography



## ⚙️ Installazione (Terminale VS Code)

### 1. Clonare il repository

```bash
git clone https://github.com/lorenzoo999/caremind.git
```
### 2. Creazione ed attivazione di un ambiente virtuale Python

Assicurati di usare Python 3.11 per il corretto funzionamento dei driver MongoDB di Atlas

```bash
python3.11 -m venv .venv
source .venv/bin/activate  # (Linux/macOS)
.venv\Scripts\activate     # (Windows)
```

### 3. Installazione delle dipendenze

```bash
pip install -r requirements.txt
```

**NOTA**: durante l'installazione delle dipende si può incorrere in errori "Failed to build wheel for pyarrow / faiss-cpu"
In tal caso si consiglia di lanciare il seguente comando per aggiornare i tool di build di Python all'interno del proprio venv:

```bash
pip install --upgrade pip setuptools wheel
```


### 4. Configurazione delle variabili d'ambiente

Crea un file `.env` partendo da quello di esempio `.env.example` fornito nel repository:

```bash
cp .env.example .env  # Su macOS
copy .env.example .env  # Su Windows (cmd)
```

Compila i TOKEN/KEY richiesti: 
- OPENAI_API_KEY
- HF_TOKEN
- MONGO_DB_PASSWORD

### 5. 🎛️ Avvio del Chatbot (Streamlit)


```bash
streamlit run chatbot.py
```



## ☁️ Deploy su Streamlit Community Cloud

CareMind può essere eseguito anche direttamente online tramite Streamlit Cloud, senza bisogno di alcuna installazione locale.
E' possibile eseguire il chatbot al seguente link: https://caremind.streamlit.app



## Credenziali di Accesso
All'avvio dell'applicazione sarà possibile accedere a sezione per pazienti e per professionisti (operatori sanitari) che richiederanno delle rispettive credenziali di accesso valide:


### Credenziali di esempio Paziente

- **Email:** `stefano.diguida@gmail.com`  
  **Password:** `stefanodiguida`

### Credenziali di esempio Professionista

- **Email:** `simone.rossi@asl1.com`  
  **Password:** `PasswordSicura123`

