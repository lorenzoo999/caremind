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
git clone https://github.com/simo26/voice2care.git
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

⚠️ Nota importante:
Il pacchetto av (richiesto per il modello di faster-whisper) necessita di:

- FFmpeg installato sul sistema
- Strumenti di sviluppo: pkg-config, build-essential, Cython, gcc, ecc.

macOS:

```bash
brew install ffmpeg
brew install pkg-config
pip install cython
```

Windows:

- 1.Scarica FFmpeg e aggiungilo al PATH.
- 2.Installa il compilatore Visual C++ tramite Build Tools for Visual Studio
- 3.Installa Cython:

```bash
pip install cython
```

### 4. Configurazione delle variabili d'ambiente

Crea un file `.env` partendo da quello di esempio `.env.example` fornito nel repository:

```bash
cp .env.example .env  # Su macOS
copy .env.example .env  # Su Windows (cmd)
```

Compila i valori mancanti: 
- HF_TOKEN: https://huggingface.co
- API_KEY_GEMINI: https://aistudio.google.com
- CHAT_ID: l'id della tua chat ottenibile inviando un messaggio al bot @CodiceRossoBot; successivamente estrapola "id" della chat da: https://api.telegram.org/bot7935276594:AAHNX091qdRxR4W9kYyqi7G8H_Y_5f5ADsE/getUpdates
- DB_PASSWORD: Fornita all'interno dello stesso file di esempio

### 5. Configurazione Redis

Per abilitare l'utilizzo di Redis:

#### Windows
- 1.Installa Redis localmente:

```bash
wsl --install
```
Questo installerà Ubuntu su WSL2 e riavvierà il computer. 
Dopo il riavvio, segui la configurazione iniziale (nome utente e password).

- 2.Apri Ubuntu (WSL) e aggiorna i pacchetti
  
```bash
sudo apt udapte
sudo apt install redis-server
```

- 3.Avvia Redis

 ```bash
sudo service redis-server start
```

- 3.Verifica che Redis sia attivo

 ```bash
redis-cli ping
```

Risposta attesa: PONG

- 4.Eseguire il file alert_subscriber.py

#### MacOS

- 1.Installa Redis tramite Homebrew
  
 ```bash
brew install redis
```

- 2.Avvia Redis
  
 ```bash
redis-server
```

- 3.Verifica che Redis sia attivo
  
 ```bash
redis-cli ping
```
Risposta attesa: PONG

- 4.Eseguire il file alert_subscriber.py

### 6. ⚙️ Avvio del Backend

Il backend FastAPI può essere eseguito in due modalità, a seconda delle risorse disponibili e della preferenza per modelli remoti o locali:

🔁 **Opzione 1 — API Hugging Face (whisper-large-v3-turbo)**  
Questa modalità sfrutta le API degl'Inference Provider di Hugging Face, ideale per ambienti leggeri.
Usa questa modalità se vuoi evitare l’uso locale di modelli pesanti.

```bash
uvicorn backend.main_whisper_api:app --reload
```

**NOTA: whisper-large-v3-turbo via API non supporta la trascrizione di audio in formato .m4a!**

⚡ **Opzione 2 — Faster-Whisper "medium" (modello locale)**
Questa modalità utilizza Faster-Whisper in esecuzione locale per la trascrizione, sfruttando la potenza della GPU (se disponibile).

```bash
uvicorn backend.main_whisper_model:app --reload
```

Verifica che torch.cuda.is_available() sia True per sfruttare la GPU.

### 7. 🎛️ Avvio del Frontend (Streamlit)

Lancia l’interfaccia utente:

```bash
streamlit run app.py
```


All'avvio della dashboard verranno richieste le credenziali di accesso dell'operatore sanitario (medico) che desidera interagire con l'applicativo:

<img width="600" alt="Screenshot della schermata di login" src="https://github.com/user-attachments/assets/3cd851fe-81e9-4724-8b07-c6257f0d8ce3" />

### Credenziali di esempio

Puoi utilizzare le seguenti credenziali per effettuare l'accesso:

- **Email:** `marco.verdi@asl.it`  
  **Password:** `Sicura456`

- **Email:** `giulia.bianchi@asl.it`  
  **Password:** `PasswordMedico123`

