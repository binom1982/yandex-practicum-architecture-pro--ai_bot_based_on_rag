from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings

# Загрузка индекса и модели
embeddings = HuggingFaceEmbeddings(
    #model_name="sentence-transformers/all-MiniLM-L6-v2"
    model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)
vectorstore = FAISS.load_local(
    "faiss_index", embeddings, allow_dangerous_deserialization=True
)

# Тестовый запрос
#query =  "What powers the HyperRelay technology?" #"Что питает технологию HyperRelay?"
query =  "Что питает технологию HyperRelay?"
results = vectorstore.similarity_search(query, k=3)

print(f"🔍 Запрос: {query}\n")
for i, doc in enumerate(results, 1):
    print(f"[{i}] Источник: {doc.metadata['source']}")
    print(f"    Текст: {doc.page_content[:200]}...\n")