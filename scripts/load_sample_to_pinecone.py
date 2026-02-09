"""샘플 데이터를 Pinecone에 로드 (OpenAI API 절약)"""
from rag.pinecone_client import get_pinecone_client
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_sample_documents():
    """샘플 규제 문서 데이터 (API 사용 최소화)"""

    # 실제 규제 가이드라인 샘플
    sample_docs = [
        {
            "text": """
Allergenicity Assessment

The assessment of potential allergenicity should focus on:
1. Source of the genetic material
2. Amino acid sequence homology to known allergens
3. Serum screening with sera from individuals allergic to the source
4. Targeted serum screening (where appropriate)

If the introduced protein(s) is derived from a known allergenic source, additional targeted serum screening should be performed.
            """.strip(),
            "source": "Codex Guideline Section 4.2.pdf",
            "page": 12
        },
        {
            "text": """
Substantial Equivalence

The concept of substantial equivalence is a key step in the safety assessment process. The principle establishes the conventional food or food component as a comparator for the safety assessment of the GM food.

The comparison should include:
- Key nutrients
- Anti-nutrients
- Natural toxicants
- Allergens
            """.strip(),
            "source": "Codex Guideline Section 3.1.pdf",
            "page": 8
        },
        {
            "text": """
Toxicological Assessment

Where the novel food or food ingredient contains or consists of a GMO, the safety assessment should consider:
- Potential toxicity of the newly expressed proteins
- Potential unintended effects
- Allergenicity
- Nutritional impact

90-day feeding studies in rodents are generally recommended for initial safety assessment.
            """.strip(),
            "source": "EFSA Guidance on Novel Foods.pdf",
            "page": 24
        },
        {
            "text": """
Post-Market Monitoring

FDA may recommend post-market surveillance when:
- The novel food represents a significant dietary change
- There are unresolved safety questions
- Long-term effects need to be monitored

Developers should establish monitoring systems to detect any unexpected adverse effects.
            """.strip(),
            "source": "FDA Guidance for Industry.pdf",
            "page": 45
        },
        {
            "text": """
Gene Editing Technologies

For NGT products developed using site-directed nucleases (SDN):
- SDN-1: No foreign DNA introduced, may not require extensive safety assessment
- SDN-2: Small targeted changes, case-by-case evaluation
- SDN-3: Insertion of genetic material, similar to conventional GMO assessment

The absence of foreign DNA in SDN-1 products may support a streamlined regulatory approach.
            """.strip(),
            "source": "EU NGT Regulation 2025.pdf",
            "page": 15
        }
    ]

    try:
        client = get_pinecone_client()
        logger.info("⬆️ 샘플 문서 업로드 중... (5개)")

        client.upsert_documents(sample_docs)

        logger.info("✅ 완료!")
        logger.info(f"📊 5개 샘플 문서가 Pinecone에 저장되었습니다")
        logger.info("")
        logger.info("🧪 테스트 쿼리:")
        logger.info('  python -c "from tools.rag_search import rag_search_tool; print(rag_search_tool.invoke({\'query\': \'allergen assessment\'}))"')

    except Exception as e:
        logger.error(f"❌ 업로드 실패: {e}")


if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("Sample Data to Pinecone Loader")
    logger.info("=" * 60)
    load_sample_documents()
