"""PDF 문서를 Pinecone에 로드"""
import PyPDF2
from pathlib import Path
from typing import List, Dict
from rag.pinecone_client import get_pinecone_client
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def extract_text_from_pdf(pdf_path: Path) -> List[Dict]:
    """PDF에서 텍스트 추출 및 청크 분할"""
    documents = []

    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)

            for page_num, page in enumerate(reader.pages, start=1):
                text = page.extract_text()

                # 청크로 분할 (1000자씩)
                chunk_size = 1000
                for i in range(0, len(text), chunk_size):
                    chunk = text[i:i + chunk_size]

                    if len(chunk.strip()) > 50:  # 너무 짧은 청크 제외
                        documents.append({
                            "text": chunk,
                            "source": pdf_path.name,
                            "page": page_num
                        })

        logger.info(f"📄 {pdf_path.name}: {len(documents)}개 청크 추출")
        return documents

    except Exception as e:
        logger.error(f"❌ {pdf_path.name} 처리 실패: {e}")
        return []


def load_pdfs_to_pinecone(pdf_dir: str = "data/regulatory"):
    """모든 PDF를 Pinecone에 로드"""
    pdf_path = Path(pdf_dir)

    if not pdf_path.exists():
        logger.error(f"❌ 디렉토리 없음: {pdf_dir}")
        logger.info(f"💡 디렉토리 생성 후 PDF 파일을 배치하세요")
        return

    # Pinecone 클라이언트
    try:
        client = get_pinecone_client()
    except Exception as e:
        logger.error(f"❌ Pinecone 연결 실패: {e}")
        logger.info(f"💡 .env 파일의 PINECONE_API_KEY를 확인하세요")
        return

    # 모든 PDF 파일 처리
    pdf_files = list(pdf_path.glob("*.pdf"))

    if not pdf_files:
        logger.warning(f"⚠️ {pdf_dir}에 PDF 파일이 없습니다")
        logger.info(f"💡 Codex, FDA 가이드라인 PDF를 {pdf_dir}에 배치하세요")
        return

    logger.info(f"📚 {len(pdf_files)}개 PDF 파일 발견")

    all_documents = []
    for pdf_file in pdf_files:
        docs = extract_text_from_pdf(pdf_file)
        all_documents.extend(docs)

    if not all_documents:
        logger.error("❌ 추출된 문서가 없습니다")
        return

    # Pinecone에 업로드
    logger.info(f"⬆️ Pinecone에 업로드 중... (총 {len(all_documents)}개 청크)")
    try:
        client.upsert_documents(all_documents)
        logger.info("✅ 완료!")
        logger.info(f"📊 총 {len(all_documents)}개 청크가 Pinecone에 저장되었습니다")
    except Exception as e:
        logger.error(f"❌ 업로드 실패: {e}")
        logger.info(f"💡 Pinecone 인덱스가 생성되었는지 확인하세요")
        from config import settings
        logger.info(f"   https://app.pinecone.io → Indexes → {settings.PINECONE_INDEX_NAME}")


if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("PDF to Pinecone Loader")
    logger.info("=" * 60)
    load_pdfs_to_pinecone()
