from langchain_community.document_loaders import PyPDFLoader
loader = PyPDFLoader("media/files/1fd4d245-c210-4e20-b22e-17e60be245c3_1-Gioithieu.pdf")
docs = loader.load()
print(len(docs))
print(docs[0].page_content[:200])