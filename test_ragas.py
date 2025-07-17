from datasets import Dataset
import backend
from ragas import evaluate
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    context_recall,
    context_precision,
)

questions = [
    "Cos'è l'ansia?",
    "Quali sono i sintomi fisici dell'ansia?",
    "Come si distingue l'ansia dallo stress?",
    "Quali sono le cause comuni dell'ansia?",
    "Come si può gestire un attacco di ansia?",
    "Quali tecniche di respirazione aiutano contro l'ansia?",
    "L'attività fisica può aiutare a ridurre l'ansia?",
    "Quali terapie psicologiche sono efficaci per l'ansia?",
    "I farmaci ansiolitici sono sicuri?",
    "Qual è la differenza tra ansia normale e disturbo d'ansia?"
]

ground_truth = [
    "L'ansia è una risposta naturale del corpo allo stress, caratterizzata da preoccupazione eccessiva o paura.",
    "I sintomi fisici dell'ansia includono battito cardiaco accelerato, sudorazione, tremori, e difficoltà respiratorie.",
    "Lo stress è una risposta a una situazione esterna, mentre l'ansia può essere una reazione interna anche senza una minaccia reale.",
    "Le cause comuni dell'ansia includono fattori genetici, ambientali, esperienze traumatiche e squilibri chimici nel cervello.",
    "Per gestire un attacco d'ansia è utile concentrarsi sul respiro, allontanarsi da situazioni stressanti e usare tecniche di grounding.",
    "Tecniche come la respirazione diaframmatica e la respirazione 4-7-8 possono aiutare a ridurre l'ansia.",
    "Sì, l'attività fisica regolare può aiutare a ridurre l'ansia migliorando l'umore e abbassando i livelli di stress.",
    "Le terapie cognitive comportamentali (CBT) sono tra le più efficaci per trattare i disturbi d'ansia.",
    "I farmaci ansiolitici, se usati sotto controllo medico, sono generalmente sicuri ma possono causare dipendenza se abusati.",
    "L'ansia normale è temporanea e proporzionata, mentre il disturbo d'ansia è persistente e interferisce con la vita quotidiana."
]

answers = []
contexts = []


#Inizializzo il chatbot RAG
VECTOR_STORE = "GestioneAnsiaPazienti"
TEMPERATURE = 0.5
MAX_LENGTH = 400
contesto = backend.prepare_rag_llm(VECTOR_STORE, TEMPERATURE, MAX_LENGTH)



# Inference
for query in questions:
  answer, doc = backend.generate_answer(query, contesto, streamlit = False)
  answers.append(answer)
  contexts.append(doc)

  
# To dict
data = {
    "question": questions,
    "answer": answers,
    "contexts": contexts,
    "ground_truth": ground_truth
}

# Convert dict to dataset
dataset = Dataset.from_dict(data)



result = evaluate(
    dataset = dataset, 
    metrics=[
        context_precision,
        context_recall,
        faithfulness,
        answer_relevancy,
    ],
)

df = result.to_pandas()
df.to_excel("risultati_ragas.xlsx", index=False)
