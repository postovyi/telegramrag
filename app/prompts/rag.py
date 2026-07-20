SYSTEM_PROMPT = """
You are an expert in the field of RAG (Retrieval-Augmented Generation) in the fields of Telegram.
You are given a query and a list of documents.
You need to retrieve the most relevant documents from the list of documents.
You may be given different strategies.
Pay attention to the language of the query and the documents.
"""

HYDE_PROMPT = """
Create a hypothetical document that is relevant to the query.
Imagine how the post you need would look like and try to generate it.

Query:\n
<<{query}>>
"""

SELF_RAG_PROMPT = """
Refine the query to be more specific and relevant to the document.
Make it more specific and relevant for RAG (Retrieval-Augmented Generation).

Query:\n
<<{query}>>
"""

OUTPUT_INSTRUCTIONS = """
Return the query suitable for RAG (Retrieval-Augmented Generation).
"""