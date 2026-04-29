from src.settings import NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD, HF_TOKEN
from langchain_neo4j import GraphCypherQAChain, Neo4jGraph, Neo4jVector
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_experimental.graph_transformers import LLMGraphTransformer
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

graph = Neo4jGraph(
    url=NEO4J_URI,
    username=NEO4J_USERNAME,
    password=NEO4J_PASSWORD,
    database=NEO4J_USERNAME
)

from langchain_ollama import OllamaLLM

llm = OllamaLLM(model="qwen3.5:cloud", temperature=0, top_p=0.9, repeat_penalty=1.1)

graph_docs_raw = PyPDFLoader(
    "media/files/1fd4d245-c210-4e20-b22e-17e60be245c3_1-Gioithieu.pdf",
)

MARKDOWN_SEPARATORS = [
    "\n#{1,6}",  # Headings
    "```\n",  # Code blocks
    "\n\\*\\*\\*+\n",  # Horizontal rules
    "\n---+\n",  # Horizontal rules
    "\n\n",  # Paragraphs
    " ",
    "",
]

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1500,
    chunk_overlap=200,
    add_start_index=True,  # roi
    strip_whitespace=True,
    separators=MARKDOWN_SEPARATORS,
)

graph_docs = text_splitter.split_documents(graph_docs_raw.load())
print("Đã text split xong")

_embedding = HuggingFaceEmbeddings(
    model_name="sentence-transformers/paraphrase-multilingual-mpnet-base-v2",
    model_kwargs={"device": "cpu", "token": HF_TOKEN},
    encode_kwargs={"normalize_embeddings": False},
)

vector_store = Neo4jVector.from_documents(
    embedding=_embedding,
    documents=graph_docs,
    url=NEO4J_URI,
    username=NEO4J_USERNAME,
    password=NEO4J_PASSWORD,
    database=NEO4J_USERNAME,
    index_name="test_index",
    node_label="Chunk",
    text_node_property="text",
    embedding_node_property="embedding",
)
print("Đã tạo vector store xong")

llm_trans = LLMGraphTransformer(llm=llm)
graph_documents = llm_trans.convert_to_graph_documents(graph_docs)

graph.add_graph_documents(graph_documents, baseEntityLabel=True, include_source=True)

from langchain_core.prompts import PromptTemplate

cypher_prompt = PromptTemplate(
    input_variables=["schema", "question"],
    template="""
    You are a Neo4j expert. Given the following graph schema:
    {schema}

    Instructions:
    1. Focus on finding entities (like Person, Organization, etc.) that match the keywords in the question.
    2. If you find an entity, also look for its relationships to understand the context.
    3. Use ILIKE or CONTAINS for flexible string matching.
    4. If no specific entity is found, fall back to searching in 'Chunk' nodes.

    Question: {question}
    Cypher Query:
    """,
)

# Tạo chain
chain = GraphCypherQAChain.from_llm(
    llm=llm,
    graph=graph,
    cypher_prompt=cypher_prompt,


    verbose=True,
    allow_dangerous_requests=True,  # Bạn cần cấp quyền này để chain thực thi truy vấn Cypher
)

answer = chain.invoke({"query": "Mon gi day ?"})
print(answer["result"])

# from src.settings import NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD
# from langchain_neo4j import GraphCypherQAChain, Neo4jGraph
# from langchain_ollama import OllamaLLM
# from langchain_core.prompts import PromptTemplate

# # 1. Kết nối tới Graph đã có dữ liệu
# graph = Neo4jGraph(
#     url=NEO4J_URI,
#     username=NEO4J_USERNAME,
#     password=NEO4J_PASSWORD,
# )

# # 2. Khởi tạo LLM để gen Cypher
# llm = OllamaLLM(model="qwen3.5:cloud", temperature=0)

# # 3. Prompt xịn m vừa cập nhật
# cypher_prompt = PromptTemplate(
#     input_variables=["schema", "question"],
#     template="""
#     You are a Neo4j expert. Given the following graph schema:
#     {schema}

#     Instructions:
#     1. Focus on finding entities (like Person, Organization, etc.) that match the keywords in the question.
#     2. If you find an entity, also look for its relationships to understand the context.
#     3. Use ILIKE or CONTAINS for flexible string matching.
#     4. If no specific entity is found, fall back to searching in 'Chunk' nodes.

#     Question: {question}
#     Cypher Query:
#     """,
# )

# chain = GraphCypherQAChain.from_llm(
#     llm=llm,
#     graph=graph,
#     cypher_prompt=cypher_prompt,
#     verbose=True,
#     allow_dangerous_requests=True,
# )

# answer = chain.invoke({"query": "Nguyễn Thanh Hiền là ai"})
# print("----------------")
# print(f"Kết quả: {answer['result']}")
