import re
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.database import KnowledgeBase, Document, FAQ, AgentKnowledgeBase
from app.schemas.knowledge_base import SearchRequest, SearchResult


class KnowledgeService:
    def __init__(self, db: Session):
        self.db = db
    
    def search_knowledge_base(self, search_request: SearchRequest) -> List[SearchResult]:
        """Search through knowledge bases for relevant information"""
        results = []
        
        # Get knowledge base IDs to search in
        kb_ids = search_request.knowledge_base_ids
        if not kb_ids:
            # If no specific KBs provided, search in all active ones
            kb_ids = [kb.id for kb in self.db.query(KnowledgeBase).filter(KnowledgeBase.is_active == True).all()]
        
        query_terms = self._tokenize_query(search_request.query.lower())
        
        if search_request.search_type in ["all", "documents"]:
            doc_results = self._search_documents(query_terms, kb_ids, search_request.limit)
            results.extend(doc_results)
        
        if search_request.search_type in ["all", "faqs"]:
            faq_results = self._search_faqs(query_terms, kb_ids, search_request.limit)
            results.extend(faq_results)
        
        # Sort by relevance score and limit results
        results.sort(key=lambda x: x.relevance_score or 0, reverse=True)
        return results[:search_request.limit]
    
    def _tokenize_query(self, query: str) -> List[str]:
        """Tokenize the search query into terms"""
        # Simple tokenization - split on whitespace and remove punctuation
        tokens = re.findall(r'\b\w+\b', query.lower())
        return [token for token in tokens if len(token) > 2]  # Filter out very short words
    
    def _search_documents(self, query_terms: List[str], kb_ids: List[int], limit: int) -> List[SearchResult]:
        """Search through documents"""
        results = []
        
        documents = self.db.query(Document).filter(
            Document.knowledge_base_id.in_(kb_ids),
            Document.is_active == True
        ).all()
        
        for doc in documents:
            score = self._calculate_relevance_score(query_terms, doc.title + " " + doc.content)
            if score > 0:
                kb = self.db.query(KnowledgeBase).filter(KnowledgeBase.id == doc.knowledge_base_id).first()
                results.append(SearchResult(
                    type="document",
                    id=doc.id,
                    title=doc.title,
                    content=doc.content[:500] + "..." if len(doc.content) > 500 else doc.content,
                    knowledge_base_id=doc.knowledge_base_id,
                    knowledge_base_name=kb.name if kb else "Unknown",
                    relevance_score=score,
                    metadata=doc.metadata
                ))
        
        return results
    
    def _search_faqs(self, query_terms: List[str], kb_ids: List[int], limit: int) -> List[SearchResult]:
        """Search through FAQs"""
        results = []
        
        faqs = self.db.query(FAQ).filter(
            FAQ.knowledge_base_id.in_(kb_ids),
            FAQ.is_active == True
        ).all()
        
        for faq in faqs:
            # Search in both question and answer
            search_text = faq.question + " " + faq.answer
            score = self._calculate_relevance_score(query_terms, search_text)
            if score > 0:
                kb = self.db.query(KnowledgeBase).filter(KnowledgeBase.id == faq.knowledge_base_id).first()
                results.append(SearchResult(
                    type="faq",
                    id=faq.id,
                    title=faq.question,
                    content=faq.answer,
                    knowledge_base_id=faq.knowledge_base_id,
                    knowledge_base_name=kb.name if kb else "Unknown",
                    relevance_score=score,
                    metadata={"category": faq.category, "tags": faq.tags}
                ))
        
        return results
    
    def _calculate_relevance_score(self, query_terms: List[str], text: str) -> float:
        """Calculate relevance score for a piece of text"""
        text_lower = text.lower()
        score = 0.0
        
        for term in query_terms:
            # Count occurrences of the term
            count = text_lower.count(term)
            if count > 0:
                # Basic scoring: more occurrences = higher score
                score += count * 0.1
                
                # Bonus for exact phrase matches
                if len(query_terms) > 1:
                    phrase = " ".join(query_terms)
                    phrase_count = text_lower.count(phrase)
                    score += phrase_count * 0.5
        
        return score
    
    def get_agent_knowledge_bases(self, agent_id: int) -> List[Dict[str, Any]]:
        """Get all knowledge bases assigned to an agent"""
        agent_kbs = self.db.query(AgentKnowledgeBase).filter(
            AgentKnowledgeBase.agent_id == agent_id,
            AgentKnowledgeBase.is_enabled == True
        ).join(KnowledgeBase).filter(
            KnowledgeBase.is_active == True
        ).order_by(AgentKnowledgeBase.priority.desc()).all()
        
        result = []
        for agent_kb in agent_kbs:
            kb_data = {
                "id": agent_kb.knowledge_base.id,
                "name": agent_kb.knowledge_base.name,
                "description": agent_kb.knowledge_base.description,
                "kb_type": agent_kb.knowledge_base.kb_type,
                "priority": agent_kb.priority,
                "documents_count": len(agent_kb.knowledge_base.documents),
                "faqs_count": len(agent_kb.knowledge_base.faqs)
            }
            result.append(kb_data)
        
        return result
    
    def get_knowledge_base_content(self, kb_id: int) -> Dict[str, Any]:
        """Get all content from a knowledge base"""
        kb = self.db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()
        if not kb:
            return None
        
        documents = self.db.query(Document).filter(
            Document.knowledge_base_id == kb_id,
            Document.is_active == True
        ).all()
        
        faqs = self.db.query(FAQ).filter(
            FAQ.knowledge_base_id == kb_id,
            FAQ.is_active == True
        ).all()
        
        return {
            "knowledge_base": {
                "id": kb.id,
                "name": kb.name,
                "description": kb.description,
                "kb_type": kb.kb_type
            },
            "documents": [
                {
                    "id": doc.id,
                    "title": doc.title,
                    "content": doc.content,
                    "file_type": doc.file_type
                }
                for doc in documents
            ],
            "faqs": [
                {
                    "id": faq.id,
                    "question": faq.question,
                    "answer": faq.answer,
                    "category": faq.category,
                    "tags": faq.tags
                }
                for faq in faqs
            ]
        }
    
    def build_agent_context(self, agent_id: int, query: str = None) -> str:
        """Build context string from agent's knowledge bases for use in agent instructions"""
        agent_kbs = self.get_agent_knowledge_bases(agent_id)
        if not agent_kbs:
            return ""
        
        context_parts = []
        
        for kb in agent_kbs:
            kb_content = self.get_knowledge_base_content(kb["id"])
            if not kb_content:
                continue
            
            # Add knowledge base header
            context_parts.append(f"\n## {kb['name']}")
            if kb["description"]:
                context_parts.append(f"Description: {kb['description']}")
            
            # Add relevant documents
            if kb_content["documents"]:
                context_parts.append("\n### Documents:")
                for doc in kb_content["documents"][:5]:  # Limit to 5 most recent
                    context_parts.append(f"- {doc['title']}: {doc['content'][:200]}...")
            
            # Add relevant FAQs
            if kb_content["faqs"]:
                context_parts.append("\n### FAQs:")
                for faq in kb_content["faqs"][:5]:  # Limit to 5 most recent
                    context_parts.append(f"Q: {faq['question']}")
                    context_parts.append(f"A: {faq['answer']}")
        
        return "\n".join(context_parts) 