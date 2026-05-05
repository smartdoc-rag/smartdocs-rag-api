from typing import Optional, List, Tuple, Dict, Any
from langchain_core.documents import Document
from langchain_core.prompts import PromptTemplate
from src.core.rag.llm_model import LLMModel
from src.core.rag.prompt import PROMPT_VI, PROMPT_EN, _is_vietnamese

# Optional imports for Neo4j
try:
    from langchain_neo4j import GraphCypherQAChain

    GRAPHCYPHER_AVAILABLE = True
except ImportError:
    try:
        from langchain_classic import GraphCypherQAChain

        GRAPHCYPHER_AVAILABLE = True
    except ImportError:
        GRAPHCYPHER_AVAILABLE = False
        GraphCypherQAChain = None  # type: ignore

try:
    from src.core.rag.neo4j import neo4j_connect

    NEO4J_CONNECT_AVAILABLE = True
except ImportError:
    NEO4J_CONNECT_AVAILABLE = False
    neo4j_connect = None  # type: ignore


class GraphRAGService:
    def __init__(self):
        self.llm = LLMModel().get_openai()
        self.graph = None
        self.graph_error = None
        self.neo4j_available = GRAPHCYPHER_AVAILABLE and NEO4J_CONNECT_AVAILABLE

        if not self.neo4j_available:
            import logging

            logging.getLogger(__name__).warning(
                "Neo4j dependencies not available. GraphRAG will be disabled."
            )
            return

        try:
            self.graph = neo4j_connect()
        except Exception as e:
            self.graph_error = str(e)
            import logging

            logging.getLogger(__name__).warning(f"Failed to connect to Neo4j: {e}")

    @staticmethod
    def _fix_file_id_in_cypher(cypher: str) -> str:
        """Post-process Cypher to ensure file_id values are quoted as strings.

        LLM thường sinh file_id IN [34, 35] thay vì file_id IN ["34", "35"]
        dù prompt đã hướng dẫn, vì Neo4j lưu file_id dạng STRING.
        """
        import re
        # file_id IN [34, 35] -> file_id IN ["34", "35"]
        cypher = re.sub(
            r'(file_id\s+IN\s*)\[(\d+(?:\s*,\s*\d+)*)\]',
            lambda m: m.group(1) + '["' + '", "'.join(x.strip() for x in m.group(2).split(',')) + '"]',
            cypher,
        )
        # file_id = 34 -> file_id = "34"  (chỉ khi vế phải là số nguyên, không phải biểu thức)
        cypher = re.sub(
            r'(file_id\s*=\s*)(\d+)\b',
            lambda m: m.group(1) + '"' + m.group(2) + '"',
            cypher,
        )
        return cypher

    def _extract_citations_from_result(
        self, chain_result: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """Trích xuất citations từ kết quả của GraphCypherQAChain.
        Hỗ trợ nhiều dạng record: node object, dict, và chuỗi scalar từ RETURN p.id...
        """
        citations = []
        context = []

        intermediate = chain_result.get("intermediate_steps", [])
        if len(intermediate) >= 2 and isinstance(intermediate[1], dict):
            context = intermediate[1].get("context", [])
        if not context:
            for step in intermediate:
                if isinstance(step, dict) and "context" in step:
                    context = step["context"]
                    break

        for record in context:
            if not isinstance(record, dict):
                continue

            # Bước 1: Parse record thành dict chuẩn bằng cách loại bỏ prefix alias
            parsed = {}
            alias_type = None  # để suy loại thực thể
            for k, v in record.items():
                if isinstance(v, str) and "." in k:
                    # Key dạng "p.id" -> tách thành base_key "id"
                    prefix, base_key = k.split(".", 1)
                    parsed[base_key] = v
                    # Thử nhận diện loại thực thể từ prefix
                    if prefix.lower() in ["p", "person"]:
                        alias_type = "Person"
                    elif prefix.lower() in ["o", "org", "organization"]:
                        alias_type = "Organization"
                    elif prefix.lower() in ["t", "tech", "technology"]:
                        alias_type = "Technology"
                    # ... có thể mở rộng thêm
                else:
                    parsed[k] = v

            # Bước 2: Lấy id, name, type, file_id
            node_id = (
                parsed.get("id") or parsed.get("document_id") or parsed.get("d.id")
            )  # dạng alias d.id có thể đã được parse
            name = (
                parsed.get("name")
                or parsed.get("file_name")
                or parsed.get("title")
                or parsed.get("d.title")
            )
            file_id = parsed.get("file_id") or parsed.get("d.file_id") or None
            entity_type = parsed.get("type") or alias_type or "Node"

            # Nếu node_id quá dài (>200), đó là chunk text bị LLM alias
            # thành id (vd: RETURN c.text AS id). Không dùng làm id citation.
            if isinstance(node_id, str) and len(node_id) > 200:
                if not name:
                    name = node_id[:500]  # Dùng text làm name
                node_id = node_id[:200]  # Rút gọn id

            # Nếu record chứa trực tiếp một node object (có .id và .labels)
            if len(record) == 1:
                only_value = list(record.values())[0]
                if hasattr(only_value, "id") and hasattr(only_value, "labels"):
                    node_id = str(only_value.id)
                    name = only_value.get(
                        "file_name", only_value.get("title", only_value.get("name", ""))
                    ) or str(only_value)
                    entity_type = (
                        list(only_value.labels)[0] if only_value.labels else "Node"
                    )
                    file_id = only_value.get("file_id", None)
                elif isinstance(only_value, dict):
                    # nested dict: lấy từ dict con
                    node_id = only_value.get("id") or only_value.get("document_id")
                    name = (
                        only_value.get("name")
                        or only_value.get("file_name")
                        or only_value.get("title")
                    )
                    if not name and node_id:
                        name = str(node_id)
                    file_id = only_value.get("file_id", None)
                    entity_type = only_value.get("type", "Document")
                elif isinstance(only_value, str):
                    # Giá trị chuỗi đơn (scalar) – dùng luôn làm id và name
                    node_id = only_value
                    name = only_value
                    entity_type = alias_type or "Node"

            # Bước 3: Fallback fuzzy — khi LLM dùng alias tùy ý (vd: ProjectId, RelatedEntityId...)
            # mà không theo convention `AS id, 'Type' AS type`.
            if not node_id or entity_type == "Node":
                id_keys = []
                name_keys = []
                type_keys = []
                file_keys = []
                for k in parsed:
                    kl = k.lower()
                    if kl == "file_id" or "fileid" in kl:
                        file_keys.append(k)
                    elif kl == "id" or kl.endswith("id") or "entityid" in kl or "relatedid" in kl:
                        id_keys.append(k)
                    elif "name" in kl or "title" in kl or kl == "project":
                        name_keys.append(k)
                    elif "type" in kl or "label" in kl:
                        type_keys.append(k)

                if not node_id:
                    for k in id_keys:
                        v = parsed.get(k)
                        if v and isinstance(v, str):
                            node_id = v
                            break

                if not name:
                    for k in name_keys:
                        v = parsed.get(k)
                        if v and isinstance(v, str):
                            name = v
                            break
                    if not name and node_id:
                        name = node_id

                if entity_type == "Node":
                    for k in type_keys:
                        v = parsed.get(k)
                        if v and isinstance(v, str) and v != "__Entity__":
                            entity_type = v
                            break

                if not file_id:
                    for k in file_keys:
                        v = parsed.get(k)
                        if v and isinstance(v, str):
                            file_id = v
                            break

            # Nếu vẫn chưa có name nhưng có id, gán name = id
            if not name and node_id:
                name = str(node_id)
            elif not name:
                name = "Unknown"

            # Bỏ qua nếu không có id
            if not node_id:
                continue

            citations.append(
                {
                    "id": node_id,
                    "name": name,
                    "type": entity_type,
                    "file_id": file_id,
                }
            )

        # Loại bỏ trùng lặp dựa trên id
        seen = set()
        unique = []
        for cit in citations:
            cid = cit.get("id")
            if cid and cid not in seen:
                seen.add(cid)
                unique.append(cit)
            elif not cid:
                unique.append(cit)
        return unique

    def _get_cypher_prompt(
        self, selected_file_ids=None, conversation_id=None
    ) -> PromptTemplate:
        file_filter = ""
        conv_filter = ""
        if selected_file_ids:
            file_ids_quoted = ", ".join([f'"{fid}"' for fid in selected_file_ids])
            file_filter = (
                f"\nCRITICAL: file_id is stored as STRING in Neo4j. Only query nodes with file_id IN [{file_ids_quoted}]."
                f"\n   - For Chunk nodes: WHERE c.file_id IN [{file_ids_quoted}]"
                f"\n   - For Document nodes: WHERE d.file_id IN [{file_ids_quoted}]"
                f"\n   - For entities: ensure connected Document/Chunk has file_id IN [{file_ids_quoted}]"
                f"\n   - REMINDER: file_name usually has extension like '.docx', '.pdf'. NEVER use exact match with `=` or `toLower(x) = '...'`; ALWAYS use `CONTAINS` for file_name."
            )

        if conversation_id is not None:
            conv_filter = f"\nCRITICAL: All nodes MUST have conversation_id = {conversation_id}. For Chunk: WHERE c.conversation_id = {conversation_id}. For Document: WHERE d.conversation_id = {conversation_id}."

        # Các ví dụ mẫu (few‑shot) được nhúng trực tiếp
        examples = """
Examples of how to answer questions using the graph:

Question: "CV nói về ai?"
Cypher: MATCH (d:Document)-[:MENTIONS]->(p:Person)
        WHERE toLower(d.file_name) CONTAINS 'cv' OR toLower(d.title) CONTAINS 'cv'
        RETURN p.id AS id, 'Person' AS type

Question: "Ai là tác giả của tài liệu này?" (when referring to a specific document)
Cypher: MATCH (d:Document)-[:HAS_AUTHOR]->(p:Person)
        WHERE toLower(d.file_name) CONTAINS 'tai_lieu_x'
        RETURN p.id AS id, 'Person' AS type

Question: "What technologies are mentioned in the architecture document?"
Cypher: MATCH (d:Document)-[:MENTIONS]->(t:Technology)
        WHERE toLower(d.file_name) CONTAINS 'architecture'
        RETURN t.id AS id, 'Technology' AS type

Question: "Which organization uses React?"
Cypher: MATCH (o:Organization)-[:RELY_ON]->(t:Technology)
        WHERE toLower(t.name) = 'react'
        RETURN o.id AS id, 'Organization' AS type

Question: "List all people with Python skill"
Cypher: MATCH (p:Person)-[:HAS_SKILL]->(s:Skill)
        WHERE toLower(s.name) = 'python'
        RETURN p.id AS id, 'Person' AS type

Always use aliases in RETURN: `RETURN x.property AS id, 'EntityType' AS type`.
When the question asks about "who", "ai", "tác giả", "author", you MUST search for Person nodes via MENTIONS or HAS_AUTHOR relationships.
If you need a name but the node only has an id, use that id as the name.
When returning chunk text, use `c.id AS id, c.text AS text` — NEVER alias chunk text as `id` because it is too long.
"""

        template = (
            "Task: Generate Cypher statement to query a graph database.\n"
            "Instructions:\n"
            "Use only the provided relationship types and properties in the schema.\n"
            "Do not use any other relationship types or properties that are not provided.\n"
            "Schema:\n"
            "{schema}\n"
            "Note: Do not include any explanations or apologies in your responses.\n"
            "Do not include any text except the generated Cypher statement.\n"
            "For text matching use CONTAINS or toLower(), NOT ILIKE.\n"
            "If no specific entity is found, fall back to searching Chunk nodes."
            + conv_filter
            + file_filter
            + "\n\n"
            + examples
            + "\nThe question is:\n{question}"
        )

        return PromptTemplate(input_variables=["schema", "question"], template=template)

    def _create_chain(self, selected_file_ids=None, conversation_id=None):
        if not self.neo4j_available or self.graph is None or GraphCypherQAChain is None:
            raise ValueError(
                "Neo4j graph not available. Cannot create GraphCypherQAChain."
            )
        cypher_prompt = self._get_cypher_prompt(selected_file_ids, conversation_id)
        chain = GraphCypherQAChain.from_llm(
            llm=self.llm,
            graph=self.graph,
            cypher_prompt=cypher_prompt,
            verbose=True,
            allow_dangerous_requests=True,
            return_intermediate_steps=True,
            post_cypher_callback=self._fix_file_id_in_cypher,
        )
        return chain

    # Các phương thức còn lại giữ nguyên hoàn toàn
    def chat_flow(
        self,
        user_input: str,
        context_docs: Optional[List[Document]] = None,
        chat_history: Optional[List[Tuple[str, str]]] = None,
        selected_file_ids: Optional[List[int]] = None,
        conversation_id=None,
    ) -> Dict[str, Any]:
        if not self.neo4j_available or self.graph is None:
            from src.services.rag.rag_service import RAGService

            rag = RAGService()
            answer = rag.chat_flow(
                user_input, context_docs=context_docs, chat_history=chat_history
            )
            return {"answer": answer, "citations": []}

        if context_docs:
            from src.services.rag.rag_service import RAGService

            rag = RAGService()
            answer = rag.chat_flow(
                user_input, context_docs=context_docs, chat_history=chat_history
            )
            return {"answer": answer, "citations": []}

        answer, citations = self.query_graph(
            user_input, selected_file_ids, conversation_id
        )

        # Fallback: nếu GraphRAG không trả về kết quả (lỗi Cypher, empty, etc.)
        if not answer:
            import logging
            logging.getLogger(__name__).warning(
                "[GraphRAG] No result from graph query, falling back to vector RAG"
            )
            from src.services.rag.rag_service import RAGService
            rag = RAGService()
            answer = rag.chat_flow(
                user_input, context_docs=None, chat_history=chat_history
            )
            return {"answer": answer, "citations": []}

        if selected_file_ids:
            str_selected = [str(fid) for fid in selected_file_ids]
            filtered_citations = []
            for cit in citations:
                if cit.get("file_id") and str(cit["file_id"]) in str_selected:
                    filtered_citations.append(cit)
                else:
                    filtered_citations.append(cit)  # hoặc bỏ qua tùy ý
            citations = filtered_citations

        citations_output = [
            {"id": c["id"], "name": c["name"], "type": c["type"]} for c in citations
        ]
        return {"answer": answer, "citations": citations_output}

    def query_graph(
        self, question: str, selected_file_ids=None, conversation_id=None
    ) -> Tuple[str, List[Dict]]:
        import logging

        logger = logging.getLogger(__name__)

        try:
            logger.warning(f"[GraphRAG] Graph schema: {self.graph.schema}")
        except Exception as se:
            logger.warning(f"[GraphRAG] Could not get schema: {se}")

        chain = self._create_chain(selected_file_ids, conversation_id)
        try:
            result = chain.invoke({"query": question})
        except Exception as e:
            logger.warning(f"[GraphRAG] Cypher execution failed: {e}")
            return "", []

        logger.warning(
            f"[GraphRAG] intermediate_steps count: {len(result.get('intermediate_steps', []))}"
        )
        for i, step in enumerate(result.get("intermediate_steps", [])):
            logger.warning(
                f"[GraphRAG] step[{i}] keys: {list(step.keys()) if isinstance(step, dict) else type(step)}"
            )
            if isinstance(step, dict) and "query" in step:
                logger.warning(f"[GraphRAG] generated cypher: {step['query']}")
            if isinstance(step, dict) and "context" in step:
                ctx = step["context"]
                logger.warning(f"[GraphRAG] context len: {len(ctx) if ctx else 0}")
                if ctx:
                    for ci, c in enumerate(ctx):
                        logger.warning(f"[GraphRAG] context[{ci}]: {c}")

        answer = result.get("result", "")
        citations = self._extract_citations_from_result(result)
        return answer, citations

    def hybrid_search(
        self,
        question: str,
        vector_docs: List[Document],
        chat_history: Optional[List[Tuple[str, str]]] = None,
        selected_file_ids: Optional[List[int]] = None,
    ) -> str:
        if not self.neo4j_available or self.graph is None:
            from src.services.rag.rag_service import RAGService

            rag = RAGService()
            return rag.chat_flow(
                question, context_docs=vector_docs, chat_history=chat_history
            )

        graph_answer = self.query_graph(question, selected_file_ids)
        if not graph_answer or "I don't know" in graph_answer.lower():
            from src.services.rag.rag_service import RAGService

            rag = RAGService()
            return rag.chat_flow(
                question, context_docs=vector_docs, chat_history=chat_history
            )
        return graph_answer

    def rewrite_query(
        self, original_query: str, chat_history: List[Tuple[str, str]] = None
    ) -> str:
        from src.services.rag.rag_service import RAGService

        rag = RAGService()
        return rag.rewrite_query(original_query, chat_history)

    def evaluate_answer(self, question: str, answer: str, context: str) -> dict:
        from src.services.rag.rag_service import RAGService

        rag = RAGService()
        return rag.evaluate_answer(question, answer, context)

    def needs_more_info(self, question: str, answer: str, confidence: int) -> bool:
        from src.services.rag.rag_service import RAGService

        rag = RAGService()
        return rag.needs_more_info(question, answer, confidence)
