from dataclasses import dataclass

from api.common.domain.entities import ParentDocument
from api.common.exceptions import IndexNotReadyError
from api.modules.rag.entities import RAGResponse
from api.modules.rag.exceptions import EmptyQuestionError
from api.modules.rag.ports import LLMPort, VectorSearchPort
from api.modules.rag.prompts import SYSTEM_PROMPT, build_context, build_user_prompt


@dataclass
class AskQuestionUseCase:
    vector_store: VectorSearchPort
    llm: LLMPort
    retrieval_k: int = 5

    def execute(self, question: str) -> RAGResponse:
        if not question or not question.strip():
            raise EmptyQuestionError()
        if not self.vector_store.is_ready:
            raise IndexNotReadyError()

        parent_docs = [
            ParentDocument(uid=uid, text=text)
            for uid, text in self.vector_store.search_parent_docs(question, k=self.retrieval_k)
        ]

        if not parent_docs:
            return RAGResponse(
                question=question,
                answer="Je n'ai trouvé aucun événement pertinent pour votre question.",
                sources=[],
            )

        context = build_context(parent_docs)
        user_prompt = build_user_prompt(question, context)
        answer = self.llm.invoke(SYSTEM_PROMPT, user_prompt)

        return RAGResponse(question=question, answer=answer, sources=parent_docs)
